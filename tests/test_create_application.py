
"""
Integration test for creating a scholarship application.

Run from the project root using:
    python tests/test_create_application.py

This test creates a test applicant first and then uses the returned
applicant ID to create a scholarship application.
"""

from uuid import uuid4

from app.repositories.applicant_repository import ApplicantRepository
from app.repositories.application_repository import ApplicationRepository


def test_create_application():
    unique_email = f"app.test.{uuid4().hex[:10]}@example.com"

    try:
        # Step 1: Create a test applicant.
        applicant_id = ApplicantRepository.create(
            first_name="Application",
            middle_name="Test",
            last_name="Applicant",
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

        print("Test applicant created successfully!")
        print("Applicant ID:", applicant_id)

        # Step 2: Verify that the applicant is active.
        applicant = ApplicantRepository.get_by_id(applicant_id)

        if applicant is None:
            raise RuntimeError(
                f"Applicant ID {applicant_id} was not found "
                "or is archived."
            )

        # Step 3: Create the scholarship application.
        application_id = ApplicationRepository.create(
            applicant_id=applicant_id,
            scholarship_program="Test Scholarship",
            scholarship_year=2027,
            academic_average=95.50,
            monthly_income=12000.00,
            household=5,
            children_count=2,
            senior_count=1,
            pwd_count=0,
            mswdo_poverty_eligible=True,
            solo_parent=False,
            dependent=True,

            # Exam results:
            # 17 correct answers out of 20 = 85%.
            exam_raw_score=17,
            exam_total_items=20,
            exam_score=85.00,
            exam_passed=True,

            four_ps_beneficiary=False,
            spes_beneficiary=False,
            scholars_in_family=1,
            residency="Santa Cruz, Laguna",
            previous_scholarship=False,
        )

        print("\nApplication created successfully!")
        print("Application ID:", application_id)

        # Step 4: Retrieve the saved application.
        application = ApplicationRepository.get_by_id(application_id)

        if application is None:
            raise AssertionError(
                f"Application ID {application_id} was not found "
                "after creation."
            )

        print("Program:", application["scholarship_program"])
        print("Year:", application["scholarship_year"])
        print("Status:", application["status"])
        print("\nTEST PASSED!")

        return application_id

    except Exception as error:
        print("\nApplication creation test FAILED:", error)
        raise


if __name__ == "__main__":
    test_create_application()
