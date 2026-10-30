"""Response transport regressions; no database or model access."""
import importlib.util
import io
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location(
    "transport_bridge", Path(__file__).resolve().parents[1] / "app/ui/desktop/bridge_server.py"
)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


class BridgeTransportTests(unittest.TestCase):
    def handler(self):
        handler = bridge.Handler.__new__(bridge.Handler)
        handler.headers = {}
        handler.send_response = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()
        handler.wfile = io.BytesIO()
        handler.close_connection = False
        return handler

    def test_disconnect_during_headers_or_body_does_not_retry_response(self):
        for failure in (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            for phase in ("headers", "body"):
                with self.subTest(failure=failure.__name__, phase=phase):
                    handler = self.handler()
                    handler.path = "/api/health"
                    handler._error = Mock(side_effect=AssertionError("Must not send a second response"))
                    if phase == "headers":
                        handler.end_headers.side_effect = failure("Client disconnected")
                    else:
                        handler.wfile = Mock()
                        handler.wfile.write.side_effect = failure("Client disconnected")
                    handler.do_GET()
                    self.assertTrue(handler.close_connection)
                    handler.send_response.assert_called_once_with(200)
                    handler._error.assert_not_called()

    def test_successful_response_still_has_json_body_and_cors(self):
        handler = self.handler()
        origin = next(iter(bridge.ALLOWED_ORIGINS))
        handler.headers = {"Origin": origin}
        handler._send(200, {"ok": True})
        self.assertEqual(handler.wfile.getvalue(), b'{"ok": true}')
        handler.send_header.assert_any_call("Content-Length", "12")
        handler.send_header.assert_any_call("Access-Control-Allow-Origin", origin)
        self.assertFalse(handler.close_connection)

    def test_desktop_and_development_origins_can_read_health(self):
        for origin in ("http://127.0.0.1:1420", "http://localhost:1420", "http://tauri.localhost", "https://tauri.localhost"):
            with self.subTest(origin=origin):
                handler = self.handler()
                handler.path = "/api/health"
                handler.headers = {"Origin": origin}
                handler.do_GET()
                handler.send_header.assert_any_call("Access-Control-Allow-Origin", origin)
                self.assertEqual(handler.wfile.getvalue(), b'{"ok": true, "service": "Iskolar local bridge"}')

    def test_untrusted_browser_origins_are_not_granted_cors(self):
        handler = self.handler()
        handler.headers = {"Origin": "https://untrusted.example"}
        with patch("builtins.print"):
            handler._send(200, {"ok": True})
        self.assertFalse(any(call.args[0] == "Access-Control-Allow-Origin" for call in handler.send_header.call_args_list))

    def test_unrelated_write_errors_remain_visible(self):
        handler = self.handler()
        handler.wfile = Mock()
        handler.wfile.write.side_effect = OSError("Unexpected transport error")
        with self.assertRaisesRegex(OSError, "Unexpected transport error"):
            handler._send(200, {"ok": True})


if __name__ == "__main__":
    unittest.main()
