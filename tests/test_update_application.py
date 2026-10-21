
"""
Integration test for updating a scholarship application.

Run from the project root:
    python tests/test_update_application.py

Creates a test applicant and application, changes the application status,
and verifies that the new status was saved.
"""

from uuid import uuid4

from app.repositories.applicant_repository import ApplicantRepository
from app.repositories.application_repository import ApplicationRepository


def test_update_application():
    unique_email = f"update.test.{uuid4().hex[:10]}@example.com"

    try:
        # Step 1: Create a test applicant.
        applicant_id = ApplicantRepository.create(
            first_name="Update",
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

        print("Test applicant created. ID:", applicant_id)

        # Step 2: Create a test application.
        application_id = ApplicationRepository.create(
            applicant_id=applicant_id,
            scholarship_program="Update Test Scholarship",
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

        print("Test application created. ID:", application_id)

        # Step 3: Confirm the initial status.
        application_before = ApplicationRepository.get_by_id(application_id)

        if application_before is None:
            raise AssertionError(
                f"Application {application_id} could not be retrieved."
            )

        print("Before update:", application_before["status"])

        # Step 4: Change the status.
        target_status = "UNDER_REVIEW"

        updated = ApplicationRepository.update(
            application_id,
            status=target_status,
        )

        print("Update operation returned:", updated)

        # Step 5: Retrieve the application again.
        application_after = ApplicationRepository.get_by_id(application_id)

        if application_after is None:
            raise AssertionError(
                f"Application {application_id} could not be retrieved "
                "after the update."
            )

        print("After update:", application_after["status"])

        # Step 6: Verify the persisted status.
        if application_after["status"] != target_status:
            raise AssertionError(
                f"Expected status {target_status}, "
                f"but found {application_after['status']}."
            )

        print("\nTEST PASSED: Application status was saved correctly!")

        return application_id

    except Exception as error:
        print("\nApplication update test FAILED:", error)
        raise


if __name__ == "__main__":
    test_update_application()
