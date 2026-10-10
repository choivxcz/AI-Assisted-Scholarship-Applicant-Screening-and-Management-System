
from app.repositories.applicant_repository import ApplicantRepository


def test_archive_applicant():
    # Use a fictional test record, not a real applicant.
    applicant_id = 4

    applicant = ApplicantRepository.get_by_id(applicant_id)

    if applicant is None:
        print(f"Active applicant ID {applicant_id} was not found.")
        return

    archived = ApplicantRepository.archive(applicant_id)

    print("Archive operation returned:", archived)

    active_applicant = ApplicantRepository.get_by_id(applicant_id)
    archived_applicant = ApplicantRepository.get_by_id(
        applicant_id,
        include_archived=True,
    )

    print("Visible among active applicants:", active_applicant is not None)
    print(
        "Still stored in database:",
        archived_applicant is not None,
    )


if __name__ == "__main__":
    test_archive_applicant()
