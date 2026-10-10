
from app.repositories.applicant_repository import ApplicantRepository


def test_search_applicant():
    keyword = "Juan"

    results = ApplicantRepository.search(keyword)

    print(f"\nSearch keyword: {keyword}")
    print(f"Results found: {len(results)}")

    for applicant in results:
        print(
            f"ID: {applicant['applicant_id']} | "
            f"Name: {applicant['first_name']} "
            f"{applicant['last_name']} | "
            f"Barangay: {applicant['barangay']}"
        )


if __name__ == "__main__":
    test_search_applicant()
