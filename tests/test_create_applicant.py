"""
Test creating an applicant through ApplicantRepository.

Run from the project root:
    & "C:\\python314\\python.exe" tests/test_create_applicant.py
"""

from uuid import uuid4

from app.repositories.applicant_repository import ApplicantRepository


def test_create_applicant():
    unique_email = f"juan.test.{uuid4().hex[:10]}@example.com"

    applicant_id = ApplicantRepository.create(
        first_name="Juan",
        middle_name="Test",
        last_name="Dela Cruz",
        suffix=None,
        birth_date="2005-01-15",
        sex="MALE",
        email=unique_email,
        phone="09171234567",
        house_no_street="123 Test Street",
        barangay="Poblacion",
        municipality="Santa Cruz",
        province="Laguna",
    )

    if not applicant_id:
        raise AssertionError("ApplicantRepository.create() did not return an applicant ID.")

    created = ApplicantRepository.get_by_id(applicant_id)
    if not created:
        raise AssertionError(f"Applicant {applicant_id} was not found after creation.")

    if created.get("email") != unique_email:
        raise AssertionError("The saved email does not match the email used in the test.")

    print("Applicant created successfully!")
    print(f"Applicant ID: {applicant_id}")
    print(f"Test email: {unique_email}")
    return applicant_id


if __name__ == "__main__":
    test_create_applicant()
