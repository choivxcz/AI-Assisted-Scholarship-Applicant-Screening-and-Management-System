
from app.repositories.applicant_repository import ApplicantRepository
from datetime import date


def test_create_applicant():
    applicant_id = ApplicantRepository.create(
        first_name="Juan",
        middle_name="Santos",
        last_name="Dela Cruz",
        birth_date=date(2005, 5, 15),
        sex="MALE",
        email=None,
        phone=None,
        house_no_street="123 Sample Street",
        barangay="Poblacion",
        municipality="Santa Cruz",
        province="Laguna",
    )

    print(f"Applicant created successfully! ID: {applicant_id}")


if __name__ == "__main__":
    test_create_applicant()
