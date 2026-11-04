"""
The WebSocket thread's entry point: runs the protocol config.json picks (utils/config.py's
websocket_protocol) until the process exits. The protocols are in ws_legacy.py and ws_preview.py.
"""
import asyncio
import time

from updater.ws_legacy import _ws_loop
from updater.ws_preview import _preview_ws_loop


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
