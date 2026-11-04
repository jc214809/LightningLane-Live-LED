"""
The legacy protocol (the default): {"event": "livedata", ...} frames, one per ride change,
with no lastUpdated. A reconnect refetches every park over REST to catch what it missed.
"""
import asyncio
import json
import ssl
import time
import traceback
from datetime import datetime, timezone

import aiohttp
import certifi

from api.disney_api import fetch_park_live_data, get_down_time, parse_forecast, parse_queue_wait, parse_showtimes
from parks.operating import update_parks_operating_status
from updater.data_updater import merge_live_data
from updater.shared import note_network_result, parks_data_lock
from updater.ws_common import (WS_ENTITY_TYPES, WS_URL, _RECONNECT_DELAY_INITIAL, _WS_CLOSE_TIMEOUT_SECS, _WsStats,
                               _next_delay, _watchdog)
from utils import debug

# The frame shape _apply_live_update parses ({"event": ...}). No subprotocol gets it today, but the
# default is moving to "preview", and "legacy" stays selected after it does.
WS_SUBPROTOCOLS = ("legacy",)
_WS_HEARTBEAT_SECS = 30
_WS_RECEIVE_TIMEOUT_SECS = 120


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
