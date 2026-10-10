
from app.repositories.application_repository import ApplicationRepository


def test_search_application():
    keyword = "Test Scholarship"

    results = ApplicationRepository.search(keyword)

    print(f"\nSearch keyword: {keyword}")
    print(f"Results found: {len(results)}")

    for application in results:
        print(
            f"Application ID: {application['application_id']} | "
            f"Applicant ID: {application['applicant_id']} | "
            f"Program: {application['scholarship_program']} | "
            f"Year: {application['scholarship_year']} | "
            f"Status: {application['status']}"
        )


if __name__ == "__main__":
    test_search_application()
