"""Local workspace regression tests; no database or model writes."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("desktop_bridge", Path(__file__).resolve().parents[1] / "app/ui/desktop/bridge_server.py")
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)

class BridgeSafetyTests(unittest.TestCase):
    def request(self, method, path, body):
        handler = bridge.Handler.__new__(bridge.Handler)
        handler.path = path
        handler._body = lambda: body
        handler._send = lambda status, data: (status, data)
        return getattr(handler, "do_" + method)()

    def test_local_decisions_use_existing_repository_without_staff_login(self):
        with patch.object(bridge.ScholarshipDecisionRepository, "save", return_value=7) as save:
            status, data = self.request("POST", "/api/decisions", {"application_id": 1, "decision": "APPROVED", "reason": "test"})
            self.assertEqual(status, 201)
            self.assertEqual(data["decision_id"], 7)
            save.assert_called_once()

    def test_workspace_read_does_not_require_login(self):
        with patch.object(bridge.ApplicantRepository, "get_all", return_value=[]) as read:
            handler = bridge.Handler.__new__(bridge.Handler)
            handler.path = "/api/applicants"
            handler._send = lambda status, data: (status, data)
            status, _ = handler.do_GET()
            self.assertEqual(status, 200)
            read.assert_called_once()

    def test_final_status_cannot_bypass_decision_authorization(self):
        for final_status in ("APPROVED", "REJECTED", "WAITLISTED"):
            with self.subTest(final_status=final_status), patch.object(bridge.ApplicationRepository, "get_by_id", return_value={"status": "RECOMMENDED"}), patch.object(bridge.ApplicationRepository, "update") as update:
                status, _ = self.request("PUT", "/api/applications/1", {"status": final_status})
                self.assertEqual(status, 403)
                update.assert_not_called()

    def test_registration_cannot_create_an_official_award(self):
        with patch.object(bridge.ApplicationService, "register_applicant_with_application") as register:
            status, _ = self.request("POST", "/api/register", {"application": {"status": "APPROVED"}})
            self.assertEqual(status, 403)
            register.assert_not_called()

    def test_account_requests_do_not_simulate_success(self):
        for endpoint in ("login", "requests"):
            status, data = self.request("POST", "/api/auth/" + endpoint, {"role": "ADMINISTRATOR"})
            self.assertEqual(status, 503)
            self.assertIn("No account or request", data["error"])

    def test_screening_does_not_change_application_status(self):
        service = unittest.mock.Mock()
        service.screen_application.return_value = {"predicted_class": "Needs Official Review"}
        with patch.object(bridge.ApplicationRepository, "get_by_id", return_value={}), patch.object(bridge.ApplicationRepository, "update") as update:
            status, _ = self.request("POST", "/api/screening", {"application_id": 1})
            self.assertEqual(status, 404)
            update.assert_not_called()
        with patch.object(bridge.ApplicationRepository, "get_by_id", return_value={"application_id": 1}), patch.object(bridge, "application_screening_inputs", return_value={}), patch.object(bridge, "read_screening_service", return_value=service), patch.object(bridge.ApplicationRepository, "update") as update:
            status, _ = self.request("POST", "/api/screening", {"application_id": 1})
            self.assertEqual(status, 201)
            update.assert_not_called()

if __name__ == "__main__":
    unittest.main()
