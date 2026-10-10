
from app.repositories.application_repository import ApplicationRepository


def test_update_application():
    application_id = 1

    application = ApplicationRepository.get_by_id(application_id)

    if application is None:
        print(f"Application ID {application_id} was not found.")
        return

    print("Before update:", application["status"])

    updated = ApplicationRepository.update(
        application_id,
        status="UNDER_REVIEW",
    )

    application_after = ApplicationRepository.get_by_id(application_id)

    print("Update operation returned:", updated)

    if application_after:
        print("After update:", application_after["status"])


if __name__ == "__main__":
    test_update_application()
