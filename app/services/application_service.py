
from app.repositories.application_repository import ApplicationRepository


class ApplicationService:
    ALLOWED_TRANSITIONS = {
        "DRAFT": {"SUBMITTED", "WITHDRAWN"},
        "SUBMITTED": {"UNDER_REVIEW", "WITHDRAWN"},
        "UNDER_REVIEW": {
            "FOR_INTERVIEW",
            "REJECTED",
            "WAITLISTED",
            "WITHDRAWN",
        },
        "FOR_INTERVIEW": {"INTERVIEWED", "WITHDRAWN"},
        "INTERVIEWED": {
            "RECOMMENDED",
            "REJECTED",
            "WAITLISTED",
            "WITHDRAWN",
        },
        "RECOMMENDED": {"APPROVED", "REJECTED", "WAITLISTED"},
        "WAITLISTED": {"APPROVED", "REJECTED", "WITHDRAWN"},
        "APPROVED": set(),
        "REJECTED": set(),
        "WITHDRAWN": set(),
    }

    @staticmethod
    def change_status(application_id, new_status):
        if not isinstance(new_status, str):
            raise ValueError("New status must be a string.")

        new_status = new_status.strip().upper()

        if new_status not in ApplicationRepository.ALLOWED_STATUSES:
            raise ValueError(f"Invalid application status: {new_status}")

        application = ApplicationRepository.get_by_id(application_id)

        if application is None:
            return False

        current_status = application["status"]

        if new_status == current_status:
            return True

        allowed = ApplicationService.ALLOWED_TRANSITIONS.get(
            current_status, set()
        )

        if new_status not in allowed:
            raise ValueError(
                f"Cannot change application status from "
                f"{current_status} to {new_status}."
            )

        return ApplicationRepository.update(
            application_id,
            status=new_status,
        )
