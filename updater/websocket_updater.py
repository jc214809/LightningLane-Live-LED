import asyncio
import json
import ssl
import time
import traceback
from datetime import datetime, timezone

import aiohttp
import certifi

from api.disney_api import fetch_live_data, get_down_time, update_parks_operating_status
from updater.data_updater import merge_live_data
from utils import debug

WS_URL = "wss://ws.themeparks.wiki/v1/live"
_RECONNECT_DELAY_INITIAL = 5
_RECONNECT_DELAY_MAX = 60
_WS_HEARTBEAT_SECS = 30
_WS_RECEIVE_TIMEOUT_SECS = 120
_STABLE_CONNECTION_SECS = 60


def _next_delay(current_delay, connection_duration):
    """Reset backoff only after a stable connection; otherwise keep doubling so a
    connect-then-immediately-die loop can't hammer the server every 5s."""
    if connection_duration is not None and connection_duration >= _STABLE_CONNECTION_SECS:
        return _RECONNECT_DELAY_INITIAL
    return min(max(current_delay, _RECONNECT_DELAY_INITIAL) * 2, _RECONNECT_DELAY_MAX)

# Rolling message counter for heartbeat diagnostics
_ws_msg_count = 0
_ws_last_heartbeat = None


def _log_ws_heartbeat(force=False):
    """Log a periodic WS health summary every 5 minutes."""
    global _ws_msg_count, _ws_last_heartbeat
    now = datetime.now(timezone.utc)
    if _ws_last_heartbeat is None:
        _ws_last_heartbeat = now
    elapsed = (now - _ws_last_heartbeat).total_seconds()
    if force or elapsed >= 300:
        debug.info(
            f"WS heartbeat: {_ws_msg_count} messages received in last "
            f"{int(elapsed)}s (since {_ws_last_heartbeat.strftime('%H:%M:%S')} UTC)"
        )
        _ws_msg_count = 0
        _ws_last_heartbeat = now


def _apply_live_update(data, parks_data):
    """Apply a single WebSocket live-data event to the shared parks_data list."""
    global _ws_msg_count
    _ws_msg_count += 1
    event = data.get("event")
    debug.log(f"WS message: {data}")

    if event == "subscribed":
        debug.info(f"WebSocket subscribed to: {data.get('name') or data.get('entityId')}")
        return

    if event != "livedata":
        return

    entity_type = data.get("entityType")
    if entity_type not in ("ATTRACTION", "SHOW"):
        return

    entity_id = data.get("entityId")
    live = data.get("data") or {}
    status = live.get("status")
    last_updated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for park in parks_data:
        for attr in park.get("attractions", []):
            if attr.get("id") != entity_id:
                continue

            prev_status = attr.get("status")
            attr["status"] = status
            attr["lastUpdatedTs"] = last_updated

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
                queue = live.get("queue", {})
                standby = queue.get("STANDBY", {}).get("waitTime")
                if standby is not None:
                    attr["waitTime"] = standby
                else:
                    bg = queue.get("BOARDING_GROUP", {})
                    start = bg.get("currentGroupStart")
                    end = bg.get("currentGroupEnd")
                    if start is not None and end is not None:
                        attr["waitTime"] = f"Groups {start}-{end}"
                    elif start is not None:
                        attr["waitTime"] = f"Group {start}+"
                    else:
                        attr["waitTime"] = None

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
            headers = {"X-API-Key": api_key}
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(
                    WS_URL,
                    headers=headers,
                    ssl=ssl_ctx,
                    heartbeat=_WS_HEARTBEAT_SECS,
                    receive_timeout=_WS_RECEIVE_TIMEOUT_SECS,
                ) as ws:
                    connected_at = time.monotonic()
                    if is_reconnect:
                        debug.info("WebSocket reconnected — refreshing live data via REST.")
                        for park in parks_data:
                            if park.get("attractions"):
                                new_live_data = await fetch_live_data(park["attractions"])
                                park["attractions"] = merge_live_data(park["attractions"], new_live_data)
                        updated = update_parks_operating_status(list(parks_data), fetch_schedules=False)
                        parks_data[:] = updated
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
                        await ws.send_json({
                            "event": "subscribe",
                            "entityId": dest_id,
                        })
                    debug.info(f"Subscribed to destinations: {destination_ids}")

                    async for msg in ws:
                        _log_ws_heartbeat()
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            debug.log(f"WS raw: {msg.data}")
                            try:
                                _apply_live_update(json.loads(msg.data), parks_data)
                            except json.JSONDecodeError:
                                debug.warning(f"Non-JSON WS message: {msg.data}")
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            debug.warning(f"WebSocket error message: {ws.exception()}")
                            break

                    # aiohttp ends the async-for on close rather than yielding
                    # a CLOSED message; surface why the connection ended.
                    debug.warning(
                        f"WebSocket receive loop ended: close_code={ws.close_code}, "
                        f"exception={ws.exception()}"
                    )

        except Exception as e:
            debug.error(f"WebSocket error: {e}\n{traceback.format_exc()}")

        _log_ws_heartbeat(force=True)
        duration = (time.monotonic() - connected_at) if connected_at is not None else None
        delay = _next_delay(delay, duration)
        debug.info(f"WebSocket disconnected; reconnecting in {delay}s")
        await asyncio.sleep(delay)


def websocket_live_updater(api_key, parks_data):
    """
    Background thread entry point. Waits for parks_data to be populated, then
    maintains a persistent WebSocket connection for real-time attraction updates.
    Falls back gracefully if the connection cannot be established.
    """
    while not parks_data:
        time.sleep(1)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_ws_loop(api_key, parks_data))
    finally:
        loop.close()
