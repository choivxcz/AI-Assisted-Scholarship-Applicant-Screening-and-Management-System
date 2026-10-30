"""Partial updates must preserve stored application fields; no database writes."""
import unittest
from unittest.mock import Mock, patch
from app.repositories.application_repository import ApplicationRepository
from app.services.application_service import ApplicationService

class ApplicationPartialUpdateTests(unittest.TestCase):
    def test_status_update_only_writes_status(self):
        connection = Mock()
        cursor = connection.cursor.return_value
        cursor.rowcount = 1
        with patch('app.repositories.application_repository.get_connection', return_value=connection), patch.object(ApplicationRepository, 'get_by_id', return_value={'status': 'UNDER_REVIEW'}):
            self.assertTrue(ApplicationService.change_status(42, 'FOR_INTERVIEW'))
        sql, params = cursor.execute.call_args.args
        self.assertIn('`status` = %s', sql)
        self.assertNotIn('scholarship_program', sql)
        self.assertEqual(params, ('FOR_INTERVIEW', 42))
        connection.commit.assert_called_once()

    def test_create_still_requires_program(self):
        with self.assertRaisesRegex(ValueError, 'Scholarship program is required'):
            ApplicationRepository._validate_application({'status': 'DRAFT'})

    def test_partial_updates_still_validate_supplied_fields(self):
        for fields in ({'scholarship_program': ''}, {'academic_average': 101}, {'monthly_income': -1}, {'scholarship_year': 1999}, {'status': 'INVALID'}):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                ApplicationRepository._validate_application(fields, partial=True)

    def test_invalid_transition_does_not_write(self):
        with patch.object(ApplicationRepository, 'get_by_id', return_value={'status': 'APPROVED'}), patch.object(ApplicationRepository, 'update') as update:
            with self.assertRaises(ValueError):
                ApplicationService.change_status(42, 'FOR_INTERVIEW')
            update.assert_not_called()

if __name__ == '__main__':
    unittest.main()
