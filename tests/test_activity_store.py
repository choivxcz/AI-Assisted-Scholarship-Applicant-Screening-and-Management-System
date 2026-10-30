"""Activity persistence checks using mocked database connections only."""
import json
import unittest
from unittest.mock import Mock, patch

from app.ui.desktop import activity_store


class ActivityStoreTests(unittest.TestCase):
    actor = {"user_id": 7, "username": "lydo.mika", "display_name": "Mika Reyes", "role": "LYDO_OFFICIAL"}

    def connection(self):
        connection = Mock()
        connection.cursor.return_value.lastrowid = 45
        connection.cursor.return_value.rowcount = 1
        return connection

    def test_begin_commits_verified_actor_and_drops_credentials_and_raw_values(self):
        connection = self.connection()
        supplied = {
            "actor": {"user_id": 999, "role": "ADMIN"}, "outcome": "SUCCEEDED",
            "password": "do-not-save", "token": "do-not-save", "raw_form": {"email": "private@example.com"},
            "fields": ["status", "email", "password", "token", "api_secret", "email"],
            "previous_status": "draft", "new_status": "for_interview", "application_id": 21,
            "result": "do not save arbitrary input",
        }
        with patch.object(activity_store, "get_connection", return_value=connection):
            self.assertEqual(activity_store.begin_activity(self.actor, "CHANGE_STATUS", "application", 21, supplied), 45)
        sql, params = connection.cursor.return_value.execute.call_args.args
        self.assertIn("VALUES (%s, %s, %s, %s)", sql)
        self.assertEqual(params[:3], ("CHANGE_STATUS", "application", 21))
        payload = json.loads(params[3])
        self.assertEqual(payload["actor"], self.actor)
        self.assertEqual(payload["outcome"], "STARTED")
        self.assertEqual(payload["fields"], ["email", "status"])
        self.assertEqual(payload["new_status"], "FOR_INTERVIEW")
        self.assertNotIn("do-not-save", params[3])
        self.assertNotIn("private@example.com", params[3])
        self.assertNotIn("result", payload)
        connection.commit.assert_called_once()
        connection.rollback.assert_not_called()
        connection.close.assert_called_once()

    def test_begin_failure_rolls_back_and_does_not_return_success(self):
        connection = self.connection()
        connection.cursor.return_value.execute.side_effect = RuntimeError("Audit storage unavailable")
        with patch.object(activity_store, "get_connection", return_value=connection):
            with self.assertRaisesRegex(RuntimeError, "Audit storage unavailable"):
                activity_store.begin_activity(self.actor, "SCREEN", "application", 21)
        connection.commit.assert_not_called()
        connection.rollback.assert_called_once()
        connection.close.assert_called_once()

    def test_begin_requires_verified_staff_role_and_id(self):
        for actor in ({}, {**self.actor, "role": "GUEST"}, {**self.actor, "user_id": True}, {**self.actor, "user_id": 0}):
            with self.subTest(actor=actor), patch.object(activity_store, "get_connection") as connect:
                with self.assertRaises(ValueError):
                    activity_store.begin_activity(actor, "SCREEN", "application")
                connect.assert_not_called()

    def test_finish_updates_outcome_without_replacing_actor(self):
        for success, outcome, status in ((True, "SUCCEEDED", 201), (False, "FAILED", 400)):
            with self.subTest(success=success):
                connection = self.connection()
                with patch.object(activity_store, "get_connection", return_value=connection):
                    activity_store.finish_activity(45, success, entity_id=21, http_status=status)
                sql, params = connection.cursor.return_value.execute.call_args.args
                self.assertIn("JSON_SET(details", sql)
                self.assertNotIn("$.actor", sql)
                self.assertIn("= 'STARTED'", sql)
                self.assertEqual(params[:2], (outcome, status))
                self.assertEqual(params[-2:], (21, 45))
                connection.commit.assert_called_once()

    def test_finish_failure_preserves_previously_committed_started_record(self):
        connection = self.connection()
        connection.cursor.return_value.execute.side_effect = RuntimeError("Temporary database outage")
        with patch.object(activity_store, "get_connection", return_value=connection):
            with self.assertRaises(RuntimeError):
                activity_store.finish_activity(45, True)
        connection.commit.assert_not_called()
        connection.rollback.assert_called_once()

    def test_finish_missing_or_finalized_record_does_not_claim_success(self):
        connection = self.connection()
        connection.cursor.return_value.rowcount = 0
        with patch.object(activity_store, "get_connection", return_value=connection):
            with self.assertRaisesRegex(RuntimeError, "already finalized"):
                activity_store.finish_activity(45, True)
        connection.commit.assert_not_called()
        connection.rollback.assert_called_once()

    def test_list_decodes_real_rows_and_does_not_invent_legacy_identity(self):
        connection = self.connection()
        connection.cursor.return_value.fetchall.return_value = [
            {"audit_id": 45, "details": json.dumps({"actor": self.actor, "outcome": "SUCCEEDED"})},
            {"audit_id": 44, "details": {"operation": "legacy"}},
            {"audit_id": 43, "details": None},
            {"audit_id": 42, "details": "invalid json"},
        ]
        with patch.object(activity_store, "get_connection", return_value=connection):
            rows = activity_store.list_activity(100)
        self.assertEqual(rows[0]["details"]["actor"], self.actor)
        for row in rows[1:]:
            self.assertNotIn("actor", row["details"])
        sql, params = connection.cursor.return_value.execute.call_args.args
        self.assertIn("ORDER BY created_at DESC, audit_id DESC LIMIT %s", sql)
        self.assertEqual(params, (100,))
        connection.close.assert_called_once()

    def test_limit_validation_precedes_database_access(self):
        for limit in (0, -1, 1001, "250", "1; DROP TABLE users", True, None):
            with self.subTest(limit=limit), patch.object(activity_store, "get_connection") as connect:
                with self.assertRaises(ValueError):
                    activity_store.list_activity(limit)
                connect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
