from unittest.mock import patch

import pytest


@pytest.mark.parametrize("protocol, loop_name", [("preview", "_preview_ws_loop"), ("legacy", "_ws_loop")])
def test_websocket_live_updater_runs_the_configured_protocol(protocol, loop_name):
    from updater import websocket_updater
    ran = []

    async def fake_loop(api_key, parks):
        ran.append((loop_name, api_key))

    with patch.object(websocket_updater, loop_name, fake_loop):
        websocket_updater.websocket_live_updater("real-key", [{"id": "mk"}], protocol)
    assert ran == [(loop_name, "real-key")]
