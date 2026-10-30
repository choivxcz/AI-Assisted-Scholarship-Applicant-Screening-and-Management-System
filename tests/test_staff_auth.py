"""Staff authentication regressions; all account/database interactions are mocked."""
import hashlib
import unittest
from unittest.mock import Mock, patch

from argon2 import PasswordHasher
from app.ui.desktop import staff_auth as auth
from app.ui.desktop import configure_staff


class StaffAuthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hasher = PasswordHasher(time_cost=1, memory_cost=1024, parallelism=1)
        cls.password = 'Test-only-Password123!'
        cls.password_hash = cls.hasher.hash(cls.password)

    def setUp(self):
        with auth._lock:
            auth._sessions.clear()
            auth._attempts.clear()
            auth._global_attempts.clear()
        self.row = dict(user_id=7, username='official', first_name='Test', last_name='Official', role='LYDO_OFFICIAL', is_active=1, password_hash=self.password_hash)
        self.hasher_patch = patch.object(auth, 'PASSWORD_HASHER', self.hasher)
        self.hasher_patch.start()
        self.read_patch = patch.object(auth, '_read_user', side_effect=lambda *args: dict(self.row) if self.row else None)
        self.read = self.read_patch.start()
        self.addCleanup(self.hasher_patch.stop)
        self.addCleanup(self.read_patch.stop)

    def login(self):
        result = auth.authenticate('official', self.password)
        return result, {'Authorization': 'Bearer ' + result['token']}

    def assert_access_error(self, status, fn, *args):
        with self.assertRaises(auth.AccessError) as caught:
            fn(*args)
        self.assertEqual(caught.exception.status, status)
        return str(caught.exception)

    def test_both_roles_receive_equal_verified_workspace_identity(self):
        for role in ('ADMIN', 'LYDO_OFFICIAL'):
            with self.subTest(role=role):
                self.row['role'] = role
                result, headers = self.login()
                actor = auth.require_user(headers)
                self.assertEqual(actor['role'], role)
                self.assertEqual(actor['user_id'], 7)
                self.assertEqual(actor['display_name'], 'Test Official')
                self.assertNotIn('password_hash', actor)
                self.assertNotIn(result['token'], auth._sessions)
                digest = hashlib.sha256(result['token'].encode()).hexdigest()
                self.assertIn(digest, auth._sessions)

    def test_wrong_password_missing_disabled_and_unknown_role_share_generic_error(self):
        wrong = self.assert_access_error(401, auth.authenticate, 'official', 'wrong')
        self.row['is_active'] = 0
        disabled = self.assert_access_error(401, auth.authenticate, 'official', self.password)
        self.row.update(is_active=1, role='OTHER')
        role = self.assert_access_error(401, auth.authenticate, 'official', self.password)
        self.row = None
        missing = self.assert_access_error(401, auth.authenticate, 'official', self.password)
        self.assertEqual({wrong, disabled, role, missing}, {'Invalid username or password.'})
        self.assertFalse(auth._sessions)

    def test_client_cannot_replace_verified_identity_or_role(self):
        result, headers = self.login()
        result['user']['role'] = 'ADMIN'
        result['user']['user_id'] = 999
        headers['X-User-Id'] = '999'
        headers['X-Role'] = 'ADMIN'
        actor = auth.require_user(headers)
        self.assertEqual(actor['role'], 'LYDO_OFFICIAL')
        self.assertEqual(actor['user_id'], 7)

    def test_missing_forged_and_malformed_tokens_are_rejected_without_database_access(self):
        for headers in ({}, {'Authorization': 'Bearer forged'}, {'Authorization': 'Basic abc'}, {'Authorization': 'Bearer bad token'}, {'Authorization': 'Bearer '}):
            with self.subTest(headers=headers):
                self.assert_access_error(401, auth.require_user, headers)
        self.read.assert_not_called()

    def test_logout_revokes_session(self):
        _, headers = self.login()
        auth.logout(headers)
        self.assert_access_error(401, auth.require_user, headers)
        auth.logout(headers)  # idempotent

    def test_expired_session_is_removed(self):
        with patch.object(auth.time, 'monotonic', return_value=100):
            result, headers = self.login()
        digest = hashlib.sha256(result['token'].encode()).hexdigest()
        self.assertEqual(auth._sessions[digest]['expires_at'], 100 + auth.SESSION_SECONDS)
        with patch.object(auth.time, 'monotonic', return_value=100 + auth.SESSION_SECONDS):
            self.assert_access_error(401, auth.require_user, headers)
        self.assertNotIn(digest, auth._sessions)

    def test_password_reset_disabled_account_or_removed_role_revokes_session(self):
        for change in ({'password_hash': self.hasher.hash('Replacement-Password123!')}, {'is_active': 0}, {'role': 'UNKNOWN'}, {'user_id': 999}):
            with self.subTest(change=change):
                original = dict(self.row)
                result, headers = self.login()
                self.row.update(change)
                self.assert_access_error(401, auth.require_user, headers)
                digest = hashlib.sha256(result['token'].encode()).hexdigest()
                self.assertNotIn(digest, auth._sessions)
                self.row = original

    def test_supported_role_change_is_rechecked_from_database(self):
        _, headers = self.login()
        self.row['role'] = 'ADMIN'
        self.assertEqual(auth.require_user(headers)['role'], 'ADMIN')

    def test_attempt_limit_is_case_insensitive_and_expires(self):
        with patch.object(auth.time, 'monotonic', return_value=100):
            for _ in range(auth.MAX_ATTEMPTS_PER_USER):
                self.assert_access_error(401, auth.authenticate, 'Official', 'wrong')
            self.assert_access_error(429, auth.authenticate, 'OFFICIAL', self.password)
        with patch.object(auth.time, 'monotonic', return_value=100 + auth.RATE_WINDOW_SECONDS):
            self.assertIn('token', auth.authenticate('official', self.password))

    def test_global_attempt_limit_and_bounded_username_map(self):
        with patch.object(auth, 'MAX_ATTEMPTS_GLOBAL', 2):
            auth._reserve_attempt('first', 100)
            auth._reserve_attempt('second', 100)
            self.assert_access_error(429, auth._reserve_attempt, 'third', 100)
        auth._attempts.clear()
        auth._global_attempts.clear()
        with patch.object(auth, 'MAX_TRACKED_USERNAMES', 1):
            auth._reserve_attempt('first', 100)
            self.assert_access_error(429, auth._reserve_attempt, 'second', 100)
            self.assertEqual(len(auth._attempts), 1)

    def test_invalid_login_input_is_rejected_before_storage_access(self):
        for username, password in ((None, self.password), ('', self.password), ('a' * 51, self.password), ('official', None), ('official', 'x' * 1025)):
            with self.subTest(username=username):
                self.assert_access_error(400, auth.authenticate, username, password)
        self.read.assert_not_called()

    def test_account_storage_failure_does_not_expose_database_secrets(self):
        with patch.object(auth, 'get_connection', side_effect=RuntimeError('secret database details')):
            self.read_patch.stop()
            message = self.assert_access_error(503, auth._read_user, 'username', 'official')
        self.assertNotIn('secret', message)

    def test_cli_rejects_weak_password_and_role_before_database_access(self):
        with patch.object(configure_staff, 'get_connection') as connection:
            for password in ('short', 'longbutalllowercase', 'NoNumberOrSymbolHere'):
                with self.subTest(password=password), self.assertRaises(ValueError):
                    configure_staff.configure_account('staff', 'Test', 'Official', 'LYDO_OFFICIAL', password)
            with self.assertRaises(ValueError):
                configure_staff.configure_account('staff', 'Test', 'Official', 'OTHER', self.password)
            connection.assert_not_called()


if __name__ == '__main__':
    unittest.main()
