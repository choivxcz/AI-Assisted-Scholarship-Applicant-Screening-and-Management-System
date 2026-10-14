
from app.services.screening_persistence_service import (
    ScreeningPersistenceService,
)


def main():
    print("Initializing saved-model screening service...")

    service = ScreeningPersistenceService()

    print(f"Model version: {service.artifact['model_version']}")
    print(f"Database model version ID: {service.model_version_id}")

    application_id = int(
        input(
            "\nEnter an EXISTING application_id to test screening: "
        ).strip()
    )

    sample_applicant = {
        "average": 90,
        "income": 12000,
        "household": 5,
        "children": 2,
        "seniors": 1,
        "pwds": 0,
        "dependents": 2,
        "solo": 0,
        "exam_score": 45,
        "exam_total": 50,
        "exam_passed": 1,
        "fourps": 0,
        "spes": 0,
        "scholars": 0,
    }

    result = service.screen_application(
        application_id=application_id,
        applicant_data=sample_applicant,
        screened_by=None,
    )

    print("\nScreening saved successfully.")

    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
