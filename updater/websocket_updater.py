import asyncio
import json
import random
import ssl
import time
import traceback
from datetime import datetime, timezone

import aiohttp
import certifi

from api.disney_api import (build_live_updates, fetch_park_live_data, get_down_time, parse_forecast,
                            parse_queue_wait, parse_showtimes, update_parks_operating_status)
from updater.data_updater import merge_live_data
from updater.shared import (note_live_feed_down, note_live_feed_frame, note_live_feed_synced,
                            note_network_result, parks_data_lock)
from utils import debug

# The only address ThemeParks.wiki supports (ws. is a hosting hostname).
WS_URL = "wss://api.themeparks.wiki/v1/live"
# The frame shape _apply_live_update parses ({"event": ...}). No subprotocol gets it today, but the
# default is moving to "preview", and "legacy" stays selected after it does.
WS_SUBPROTOCOLS = ("legacy",)
# The entity types we display. A destination subscription takes one entityTypeFilter
# (a list or "A,B" is rejected), so each destination gets one subscription per type.
# Unfiltered, restaurants were two thirds of the messages. Each uses one of the
# key's 15 subscriptions (the welcome frame's subscriptionsLimit).
WS_ENTITY_TYPES = ("ATTRACTION", "SHOW")
_RECONNECT_DELAY_INITIAL = 5
_RECONNECT_DELAY_MAX = 60
_WS_HEARTBEAT_SECS = 30
_WS_RECEIVE_TIMEOUT_SECS = 120
_WS_CLOSE_TIMEOUT_SECS = 10  # aiohttp's own default, which a ClientWSTimeout given only ws_receive drops
_STABLE_CONNECTION_SECS = 60


def _next_delay(current_delay, connection_duration):
    """Reset backoff only after a stable connection; otherwise keep doubling so a
    connect-then-immediately-die loop can't hammer the server every 5s."""
    if connection_duration is not None and connection_duration >= _STABLE_CONNECTION_SECS:
        return _RECONNECT_DELAY_INITIAL
    return min(max(current_delay, _RECONNECT_DELAY_INITIAL) * 2, _RECONNECT_DELAY_MAX)

_WATCHDOG_INTERVAL_SECS = 300


class _WsStats:
    """Per-connection message counter for the watchdog's health window."""

    def __init__(self):
        self.msg_count = 0
        self.window_started = time.monotonic()

    def note_message(self):
        self.msg_count += 1

    def snapshot_and_reset(self):
        elapsed = time.monotonic() - self.window_started
        count = self.msg_count
        self.msg_count = 0
        self.window_started = time.monotonic()
        return count, elapsed


def _should_force_reconnect(msg_count, parks_data):
    """Silence is only suspicious while something is open and should be streaming."""
    if msg_count > 0:
        return False
    return any(p.get("operating") for p in parks_data)


async def _watchdog(ws, stats, parks_data):
    """Log a periodic health summary and force a reconnect if the connection is
    alive at the protocol level but no data flows while parks are operating."""
    while True:
        await asyncio.sleep(_WATCHDOG_INTERVAL_SECS)
        count, elapsed = stats.snapshot_and_reset()
        debug.info(f"WS heartbeat: {count} messages received in last {int(elapsed)}s")
        if _should_force_reconnect(count, parks_data):
            debug.warning("WS watchdog: no messages while parks operating — forcing reconnect.")
            await ws.close()
            return


def _apply_live_update(data, parks_data):
    """Apply a single WebSocket live-data event to the shared parks_data list."""
    event = data.get("event")
    debug.log(f"WS message: {data}")

    if event == "subscribed":
        debug.info(f"WebSocket subscribed to: {data.get('name') or data.get('entityId')}"
                   f" ({data.get('entityTypeFilter', 'all')})")
        return

    if event == "error":
        debug.warning(f"WebSocket server error: {data.get('message') or data}")
        return

    if event != "livedata":
        return

    entity_type = data.get("entityType")
    if entity_type not in ("ATTRACTION", "SHOW"):
        return

    entity_id = data.get("entityId")
    live = data.get("data") or {}
    status = live.get("status")
    # The feed sends no lastUpdated (REST does), so the receive time stamps the update:
    # it's seconds behind the change. down_since takes it from the first DOWN message.
    last_updated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    with parks_data_lock:
        for park in parks_data:
            for attr in park.get("attractions", []):
                if attr.get("id") != entity_id:
                    continue

                prev_status = attr.get("status")
                attr["status"] = status
                attr["lastUpdatedTs"] = last_updated
                attr["updateSource"] = "websocket"  # only "livedata" events get here
                if live.get("forecast"):
                    attr["forecast"] = parse_forecast(live["forecast"])
                if "showtimes" in live:
                    attr["showtimes"] = parse_showtimes(live["showtimes"])

                if status == "DOWN":
                    if not attr.get("down_since"):
                        attr["down_since"] = last_updated
                        debug.info(f"DOWN (WS): {attr['name']} ({park['name']}) — down_since set to {last_updated}")
                    down_time = get_down_time(attr["down_since"])
                    attr["waitTime"] = f"Down {down_time}" if down_time is not None else "Down"
                elif status in ("CLOSED", "REFURBISHMENT"):
                    attr["down_since"] = ""
                else:
                    attr["down_since"] = ""
                    attr["waitTime"] = parse_queue_wait(live.get("queue") or {})

                if prev_status != status:
                    debug.info(
                        f"WS update: {attr['name']} ({park['name']}) "
                        f"{prev_status} → {status}, wait={attr.get('waitTime')}"
                    )
                    # fetch_schedules=False: we're on the WS event loop — schedule
                    # fetching is blocking HTTP and is deferred to the REST thread.
                    update_parks_operating_status([park], fetch_schedules=False)
                return


def has_api_key(api_key):
    """True for a real ThemeParks key. The WebSocket needs one: without it the
    server accepts the handshake, then closes with 3000 "Authentication timeout"."""
    return isinstance(api_key, str) and bool(api_key.strip()) and not api_key.startswith("<")


def websocket_settings(config):
    """(use_websocket, api_key) from config.json's "websocket" section:
    {"enabled": true, "api_key": "..."}. Runs only when enabled with a real key.
    A config without the section falls back to the old top-level themeparks_api_key."""
    section = config.get("websocket")
    if section is None:
        api_key = config.get("themeparks_api_key")
        if has_api_key(api_key):
            debug.info('Using the top-level "themeparks_api_key"; move it to "websocket": {"api_key": ...} in config.json.')
        return has_api_key(api_key), api_key
    if not isinstance(section, dict):
        debug.warning('config.json "websocket" should be {"enabled": true, "api_key": "..."}; using REST polling only.')
        return False, None

    enabled = section.get("enabled", True)
    api_key = section.get("api_key")
    if not isinstance(enabled, bool):
        debug.warning(f'config.json "websocket.enabled" should be true or false, not {enabled!r}; using REST polling only.')
        return False, api_key
    if not enabled:
        return False, api_key
    if not has_api_key(api_key):
        debug.warning('config.json "websocket.enabled" is true but "websocket.api_key" is not set; using REST polling only.')
        return False, api_key
    return True, api_key


async def _ws_loop(api_key, parks_data):
    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    delay = _RECONNECT_DELAY_INITIAL
    is_reconnect = False

    while True:
        connected_at = None
        try:
            headers = {"X-API-Key": api_key.strip()}
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(
                    WS_URL,
                    protocols=WS_SUBPROTOCOLS,
                    headers=headers,
                    ssl=ssl_ctx,
                    heartbeat=_WS_HEARTBEAT_SECS,
                    # receive_timeout= is deprecated (aiohttp 3.14 warns); this is its replacement.
                    timeout=aiohttp.ClientWSTimeout(
                        ws_receive=_WS_RECEIVE_TIMEOUT_SECS, ws_close=_WS_CLOSE_TIMEOUT_SECS),
                ) as ws:
                    connected_at = time.monotonic()
                    if is_reconnect:
                        debug.info("WebSocket reconnected — refreshing live data via REST.")
                        for park in parks_data:
                            if park.get("attractions"):
                                new_live_data = await fetch_park_live_data(park)
                                if new_live_data is None:
                                    park["live_data_stale"] = True
                                    debug.warning(
                                        f"Live data refresh failed for {park.get('name')} after reconnect; "
                                        "keeping existing data."
                                    )
                                else:
                                    with parks_data_lock:
                                        park["live_data_stale"] = False
                                        merge_live_data(park["attractions"], new_live_data)
                        update_parks_operating_status(list(parks_data), fetch_schedules=False)
                        debug.info("REST refresh after reconnect complete.")
                    else:
                        debug.info("WebSocket connected to ThemeParks.wiki")
                    is_reconnect = True

                    destination_ids = list({
                        p["destination_id"] for p in parks_data
                        if p.get("destination_id")
                    })
                    if not destination_ids:
                        debug.warning("No destination IDs in parks_data; will retry")
                        break

                    for dest_id in destination_ids:
                        for entity_type in WS_ENTITY_TYPES:
                            await ws.send_json({
                                "event": "subscribe",
                                "entityId": dest_id,
                                "entityTypeFilter": entity_type,
                            })
                    debug.info(f"Subscribed to destinations: {destination_ids}")

                    stats = _WsStats()
                    watchdog = asyncio.create_task(_watchdog(ws, stats, parks_data))
                    try:
                        async for msg in ws:
                            stats.note_message()
                            note_network_result(True)
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                debug.log(f"WS raw: {msg.data}")
                                try:
                                    _apply_live_update(json.loads(msg.data), parks_data)
                                except json.JSONDecodeError:
                                    debug.warning(f"Non-JSON WS message: {msg.data}")
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                debug.warning(f"WebSocket error message: {ws.exception()}")
                                break
                    finally:
                        # Without this, every reconnect leaks a watchdog task
                        # holding a reference to a dead connection.
                        watchdog.cancel()

                    # aiohttp ends the async-for on close rather than yielding
                    # a CLOSED message; surface why the connection ended.
                    debug.warning(
                        f"WebSocket receive loop ended: close_code={ws.close_code}, "
                        f"exception={ws.exception()}"
                    )

        except Exception as e:
            debug.error(f"WebSocket error: {e}\n{traceback.format_exc()}")
            # A connect that fails at the socket level (DNS, refused, timeout — aiohttp's
            # connector errors are OSErrors) means no internet; a server rejection doesn't.
            if connected_at is None and isinstance(e, OSError):
                note_network_result(False)

        duration = (time.monotonic() - connected_at) if connected_at is not None else None
        delay = _next_delay(delay, duration)
        debug.info(f"WebSocket disconnected; reconnecting in {delay}s")
        await asyncio.sleep(delay)


# --- The preview protocol (config.json "websocket": {"protocol": "preview"}) ---
# Frames are {"type", "channel", "subscriptionId", "seq", "cursor", "ts", "data"}. A subscription
# starts with a snapshot of every ride, and its updates carry the ride's real lastUpdated. Each
# frame's cursor is saved, so a reconnect subscribes "since" it and gets what it missed replayed.
# Spec: https://www.themeparks.wiki/api/websockets (not under ThemeParks.wiki's SLA while in preview).

WS_PROTOCOLS = ("legacy", "preview")
WS_PREVIEW_SUBPROTOCOLS = ("preview",)
# The server pings an idle connection about every 30s (gaps can near 60s); 90s of nothing is dead.
_PREVIEW_RECEIVE_TIMEOUT_SECS = 90
# Close codes that retrying soon won't fix. 4029 is the key's connection cap: each board (and
# an emulator run) holds one, so waiting lets this board run on REST instead of hammering.
_REFUSED_CLOSE_CODES = {
    3000: "authentication failed (check websocket.api_key)",
    3001: "credentials were sent in the URL",
    3003: "the key's plan doesn't allow this",
    4029: "the key's connection limit is reached (other boards or an emulator are using it)",
}
_REFUSED_RETRY_SECS = 600
# Waits before re-sending a subscribe the server refused as retryable; then the next reconnect tries.
_SUBSCRIBE_RETRY_SECS = (2, 5, 15, 30)
_CURSOR_FRAME_TYPES = ("snapshot", "update", "resumed", "ping")


def websocket_protocol(config):
    """config.json's "websocket.protocol": "legacy" (the default) or "preview"."""
    section = config.get("websocket")
    protocol = section.get("protocol", "legacy") if isinstance(section, dict) else "legacy"
    if protocol not in WS_PROTOCOLS:
        debug.warning(f'config.json "websocket.protocol" should be "legacy" or "preview", not {protocol!r}; using "legacy".')
        return "legacy"
    return protocol


class _PreviewFeed:
    """
    The preview protocol's state. The cursor outlives a connection (it's what a reconnect
    resumes from); the subscribe frames and their retries belong to one connection.
    handle() applies a frame and returns the frames to send back, as (delay_s, frame) pairs.
    """

    def __init__(self, parks_data):
        self.parks_data = parks_data
        self.cursor = None
        self.stats = _WsStats()  # counts updates only, for the watchdog: pings prove nothing about the feed
        self.frames = {}
        self.pending = set()
        self.retries = {}

    def subscribe_frames(self, max_subscriptions=None):
        """One subscribe per destination and displayed entity type, resuming from the cursor
        (since wins over snapshot when the server still has it). If the key allows fewer
        subscriptions than that, one unfiltered subscription per destination instead."""
        dests = sorted({p["destination_id"] for p in self.parks_data if p.get("destination_id")})
        filters = WS_ENTITY_TYPES
        if isinstance(max_subscriptions, int) and len(dests) * len(filters) > max_subscriptions:
            debug.warning(f"WebSocket key allows {max_subscriptions} subscriptions; subscribing to everything "
                          "unfiltered (restaurants too) instead of one per entity type.")
            filters = (None,)
        frames = [{"type": "subscribe", "channel": dest, "filter": entity_filter, "snapshot": True,
                   "since": self.cursor, "reqId": f"{dest}:{entity_filter or 'all'}"}
                  for dest in dests for entity_filter in filters]
        self.frames = {frame["reqId"]: frame for frame in frames}
        self.pending = set(self.frames)
        self.retries = {}
        return frames

    def handle(self, frame):
        kind = frame.get("type")
        data = frame.get("data")
        debug.log(f"WS frame: {kind}")
        replies = []

        if kind == "welcome":
            limits = (data or {}).get("limits") or {}
            debug.info(f"WebSocket connected to ThemeParks.wiki (preview); key limits: {limits}")
            frames = self.subscribe_frames(limits.get("maxSubscriptions"))
            if not frames:
                debug.warning("No destination IDs in parks_data; nothing to subscribe to.")
            debug.info(("Resuming" if self.cursor else "Subscribing with a snapshot") + f": {sorted(self.frames)}")
            replies = [(0, f) for f in frames]
        elif kind == "subscribed":
            data = data or {}
            self.pending.discard(data.get("reqId"))
            debug.info(f"WebSocket subscribed to: {data.get('name') or data.get('entityId')}"
                       f" ({data.get('filter') or 'all'})")
        elif kind == "snapshot":
            entries = [e for e in data if isinstance(e, dict)] if isinstance(data, list) else []
            self._apply(entries, from_snapshot=True)
            if frame.get("final", True):
                debug.info(f"WebSocket snapshot: {frame.get('total') or len(entries)} entities")
                note_live_feed_synced()
        elif kind == "update":
            if isinstance(data, dict):
                self.stats.note_message()
                self._apply([data])
        elif kind == "resumed":
            debug.info("WebSocket resumed: caught up on the updates missed while disconnected.")
            note_live_feed_synced()
        elif kind == "ping":
            replies = [(0, {"type": "pong"})]
        elif kind == "error":
            replies = self._error(data if isinstance(data, dict) else {"message": data})
        # Anything else (unsubscribed, a type added later) is ignored: the protocol asks for tolerant readers.

        # Saved only once the frame is applied; a ping's cursor covers every channel, which
        # keeps a quiet channel's resume point from expiring overnight.
        if kind in _CURSOR_FRAME_TYPES and frame.get("cursor"):
            self.cursor = frame["cursor"]
        return replies

    def _error(self, data):
        req_id, message = data.get("reqId"), data.get("message") or data
        debug.warning(f"WebSocket server error: {message} (code {data.get('code')}, "
                      f"retryable {data.get('retryable')}, request {req_id})")
        frame = self.frames.get(req_id)
        if frame is None:
            return []
        if "resume incomplete" in str(message).lower():
            # The one case the spec names by message: the replay broke off; start that channel over.
            self.cursor = None
            return [(0, dict(frame, since=None, snapshot=True))]
        if req_id in self.pending and data.get("retryable"):
            attempt = self.retries[req_id] = self.retries.get(req_id, 0) + 1
            if attempt <= len(_SUBSCRIBE_RETRY_SECS):
                return [(_SUBSCRIBE_RETRY_SECS[attempt - 1], frame)]
            debug.warning(f"Giving up on subscription {req_id} until the next reconnect.")
        # Not retryable: before the ack it's refused for good; after it (a failed backfill)
        # the server sends that channel a fresh snapshot on its own.
        return []

    def _apply(self, entries, from_snapshot=False):
        """Merge REST-shaped live entries into their parks, through the same path as the REST
        poll. Operating status is rechecked for a park when a ride's status changed (and for
        every park after a snapshot)."""
        park_of = {e.get("id"): e.get("parkId") for e in entries}
        updates = build_live_updates(entries)
        for update in updates:
            update["updateSource"] = "websocket"
        with parks_data_lock:
            for park in self.parks_data:
                mine = [u for u in updates if park_of.get(u["id"]) == park.get("id")]
                if not mine:
                    continue
                by_id = {a.get("id"): a for a in park.get("attractions", [])}
                before = {u["id"]: by_id[u["id"]].get("status") for u in mine if u["id"] in by_id}
                merge_live_data(park["attractions"], mine)
                park["live_data_stale"] = False
                changed = [by_id[i] for i, status in before.items() if by_id[i].get("status") != status]
                if not from_snapshot:  # a snapshot's changes would be every ride at startup
                    for attr in changed:
                        debug.info(f"WS update: {attr['name']} ({park['name']}) {before[attr['id']]} → "
                                   f"{attr.get('status')}, wait={attr.get('waitTime')}")
                if changed or from_snapshot:
                    # fetch_schedules=False: blocking HTTP stays on the REST thread.
                    update_parks_operating_status([park], fetch_schedules=False)


async def _send_later(ws, delay_s, frame):
    await asyncio.sleep(delay_s)
    if not ws.closed:
        await ws.send_json(frame)


async def _preview_ws_loop(api_key, parks_data):
    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    feed = _PreviewFeed(parks_data)
    delay = _RECONNECT_DELAY_INITIAL

    while True:
        connected_at = None
        refused = None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(
                    WS_URL,
                    protocols=WS_PREVIEW_SUBPROTOCOLS,
                    headers={"X-API-Key": api_key.strip()},
                    ssl=ssl_ctx,
                    timeout=aiohttp.ClientWSTimeout(
                        ws_receive=_PREVIEW_RECEIVE_TIMEOUT_SECS, ws_close=_WS_CLOSE_TIMEOUT_SECS),
                ) as ws:
                    connected_at = time.monotonic()
                    feed.stats = _WsStats()
                    watchdog = asyncio.create_task(_watchdog(ws, feed.stats, parks_data))
                    delayed = set()
                    try:
                        async for msg in ws:
                            note_network_result(True)
                            note_live_feed_frame()
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                try:
                                    frame = json.loads(msg.data)
                                except json.JSONDecodeError:
                                    debug.warning(f"Non-JSON WS message: {msg.data}")
                                    continue
                                if not isinstance(frame, dict):
                                    continue
                                for delay_s, reply in feed.handle(frame):
                                    if delay_s:
                                        task = asyncio.create_task(_send_later(ws, delay_s, reply))
                                        delayed.add(task)
                                        task.add_done_callback(delayed.discard)
                                    else:
                                        await ws.send_json(reply)
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                debug.warning(f"WebSocket error message: {ws.exception()}")
                                break
                    finally:
                        watchdog.cancel()
                        for task in delayed:
                            task.cancel()
                        note_live_feed_down()

                    refused = _REFUSED_CLOSE_CODES.get(ws.close_code)
                    debug.warning(f"WebSocket receive loop ended: close_code={ws.close_code}, "
                                  f"exception={ws.exception()}")

        except asyncio.TimeoutError:
            debug.warning(f"WebSocket silent for {_PREVIEW_RECEIVE_TIMEOUT_SECS}s; reconnecting.")
        except Exception as e:
            debug.error(f"WebSocket error: {e}\n{traceback.format_exc()}")
            if connected_at is None and isinstance(e, OSError):
                note_network_result(False)

        if refused:
            delay = _REFUSED_RETRY_SECS
            debug.warning(f"WebSocket refused: {refused}. Retrying in {delay // 60} min; REST polls meanwhile.")
        else:
            duration = (time.monotonic() - connected_at) if connected_at is not None else None
            delay = _next_delay(delay, duration)
            debug.info(f"WebSocket disconnected; reconnecting in about {delay}s"
                       + (" (resuming from the last cursor)" if feed.cursor else ""))
        # Jitter, so boards dropped together don't all reconnect in the same second.
        await asyncio.sleep(delay * random.uniform(1.0, 1.5))


def websocket_live_updater(api_key, parks_data, protocol="legacy"):
    """
    Background thread entry point. Waits for parks_data to be populated, then
    maintains a persistent WebSocket connection for real-time attraction updates
    over the given protocol ("legacy" or "preview"). Falls back gracefully if the
    connection cannot be established.
    """
    while not parks_data:
        time.sleep(1)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    run = _preview_ws_loop if protocol == "preview" else _ws_loop
    try:
        loop.run_until_complete(run(api_key, parks_data))
    finally:
        loop.close()
