
from app.repositories.applicant_repository import ApplicantRepository


def test_update_applicant():
    # Update an existing fictional test applicant.
    applicant_id = 1

    applicant = ApplicantRepository.get_by_id(applicant_id)

    if applicant is None:
        print(f"Applicant ID {applicant_id} was not found.")
        return

    print("Before update:", applicant["phone"])

    updated = ApplicantRepository.update(
        applicant_id,
        phone="09171234567",
    )

    applicant_after = ApplicantRepository.get_by_id(applicant_id)

    print("Update operation returned:", updated)
    print("After update:", applicant_after["phone"])


if __name__ == "__main__":
    test_update_applicant()
