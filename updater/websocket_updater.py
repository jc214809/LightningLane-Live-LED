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
                update_parks_operating_status([park])
            return


async def _ws_loop(api_key, parks_data):
    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    delay = _RECONNECT_DELAY_INITIAL
    is_reconnect = False

    while True:
        try:
            headers = {"X-API-Key": api_key}
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(WS_URL, headers=headers, ssl=ssl_ctx) as ws:
                    if is_reconnect:
                        debug.info("WebSocket reconnected — refreshing live data via REST.")
                        for park in parks_data:
                            if park.get("attractions"):
                                new_live_data = await fetch_live_data(park["attractions"])
                                park["attractions"] = merge_live_data(park["attractions"], new_live_data)
                        updated = update_parks_operating_status(list(parks_data))
                        parks_data[:] = updated
                        debug.info("REST refresh after reconnect complete.")
                    else:
                        debug.info("WebSocket connected to ThemeParks.wiki")
                    delay = _RECONNECT_DELAY_INITIAL
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
                        elif msg.type in (aiohttp.WSMsgType.ERROR, aiohttp.WSMsgType.CLOSED):
                            debug.warning(f"WebSocket closed/error: {ws.exception()}")
                            break

        except Exception as e:
            debug.error(f"WebSocket error: {e}\n{traceback.format_exc()}")

        _log_ws_heartbeat(force=True)
        debug.info(f"WebSocket disconnected; reconnecting in {delay}s")
        await asyncio.sleep(delay)
        delay = min(delay * 2, _RECONNECT_DELAY_MAX)


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
