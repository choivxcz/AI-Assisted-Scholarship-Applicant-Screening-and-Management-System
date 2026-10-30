"""Dashboard read-model checks without database access or writes."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "dashboard_bridge", Path(__file__).resolve().parents[1] / "app/ui/desktop/bridge_server.py"
)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


class DashboardTests(unittest.TestCase):
    def dashboard(self, applications=None, interviews=None, decisions=None):
        with (
            patch.object(bridge.ApplicantRepository, "get_all", return_value=[]),
            patch.object(bridge.ApplicationRepository, "get_all", return_value=applications or []),
            patch.object(bridge.InterviewRepository, "get_all", return_value=interviews or []),
            patch.object(bridge.InterviewRepository, "get_upcoming", return_value=[]),
            patch.object(bridge.ScholarshipDecisionRepository, "get_all", return_value=decisions or []),
        ):
            return bridge.dashboard_data()

    def test_empty_database_has_no_generated_activity_or_totals(self):
        result = self.dashboard()
        self.assertEqual(result["recentActivity"], [])
        self.assertEqual(result["recentApplications"], [])
        self.assertEqual(result["statusCounts"], {})
        self.assertTrue(all(value == 0 for value in result["stats"].values()))

    def test_activity_is_chronological_and_uses_record_dates(self):
        result = self.dashboard(
            applications=[{"application_id": 1, "applicant_id": 1, "status": "INTERVIEWED", "created_at": "2026-10-20T10:00:00", "submitted_at": "2026-10-21T10:00:00"}],
            interviews=[{"interview_id": 2, "application_id": 1, "status": "COMPLETED", "application_status": "INTERVIEWED", "created_at": "2026-10-22T10:00:00", "updated_at": "2026-10-24T10:00:00", "scheduled_at": "2026-10-23T10:00:00", "result": "PASSED"}],
            decisions=[{"decision_id": 3, "application_id": 1, "decision": "APPROVED", "decided_at": "2026-10-25T10:00:00"}],
        )
        events = result["recentActivity"]
        self.assertEqual([event["type"] for event in events], ["decision", "interview", "application"])
        self.assertEqual(events[1]["at"], "2026-10-24T10:00:00")
        self.assertEqual(events[2]["at"], "2026-10-21T10:00:00")
        self.assertEqual(result["stats"]["awaitingDecision"], 1)
        self.assertEqual(result["stats"]["approved"], 1)
        self.assertEqual(result["stats"]["applications"], 1)


if __name__ == "__main__":
    unittest.main()
