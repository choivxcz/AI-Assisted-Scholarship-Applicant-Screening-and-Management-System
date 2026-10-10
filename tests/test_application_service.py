
from app.repositories.application_repository import ApplicationRepository
from app.services.application_service import ApplicationService


def test_application_service():
    application_id = 1

    application = ApplicationRepository.get_by_id(application_id)

    if application is None:
        print(f"Application ID {application_id} was not found.")
        return

    current_status = application["status"]
    print("Current status:", current_status)

    # First verify that an invalid transition is rejected.
    try:
        ApplicationService.change_status(
            application_id,
            "APPROVED",
        )
        print("Unexpected: direct approval was allowed.")
    except ValueError as error:
        print("Invalid transition correctly rejected:", error)

    # Then try a valid transition from the current status.
    if current_status == "UNDER_REVIEW":
        new_status = "FOR_INTERVIEW"
    elif current_status == "DRAFT":
        new_status = "SUBMITTED"
    elif current_status == "SUBMITTED":
        new_status = "UNDER_REVIEW"
    else:
        print(
            "No automatic test transition configured for this status."
        )
        return

    changed = ApplicationService.change_status(
        application_id,
        new_status,
    )

    updated_application = ApplicationRepository.get_by_id(application_id)

    print("Status change successful:", changed)
    print("New status:", updated_application["status"])


if __name__ == "__main__":
    test_application_service()
