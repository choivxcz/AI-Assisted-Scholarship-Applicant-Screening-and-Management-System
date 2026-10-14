
import json

from app.repositories.model_version_repository import (
    ModelVersionRepository,
)
from app.repositories.screening_result_repository import (
    ScreeningResultRepository,
)
from app.services.ml_screening_service import (
    MODEL_PATH,
    evaluate_applicant,
    load_saved_model,
)


class ScreeningPersistenceService:
    """Run ML screening and save its result in MySQL."""

    def __init__(self):
        self.model, self.artifact = load_saved_model()

        self.model_version_id = (
            ModelVersionRepository.register_model(
                self.artifact,
                MODEL_PATH,
            )
        )

    def screen_application(
        self,
        application_id,
        applicant_data,
        screened_by=None,
    ):
        """
        Evaluate an applicant and save the screening result.

        application_id:
            Existing applications.application_id.

        applicant_data:
            Dictionary accepted by evaluate_applicant().

        screened_by:
            Existing users.user_id, or None if staff login
            has not been implemented.
        """

        result = evaluate_applicant(
            self.model,
            applicant_data,
        )

        # The current ML service returns the probability of
        # the QUALIFIED class as a percentage. Store it as
        # a 0-to-1 decimal in confidence_score.
        confidence_score = (
            result["model_probability_percent"] / 100.0
        )

        explanation = json.dumps(
            {
                "model_version": self.artifact["model_version"],
                "model_prediction": result["model_prediction"],
                "model_probability_percent": (
                    result["model_probability_percent"]
                ),
                "exam_percentage": result["exam_percentage"],
                "exam_passed": result["exam_passed"],
                "mswd_threshold": result["mswd_threshold"],
                "mswd_eligible": result["mswd_eligible"],
                "reasons": result["reasons"],
                "requires_human_review": True,
                "note": (
                    "Advisory screening result only. "
                    "This is not an official scholarship decision."
                ),
            },
            ensure_ascii=False,
        )

        screening_id = ScreeningResultRepository.create(
            application_id=application_id,
            model_version_id=self.model_version_id,
            predicted_class=result["predicted_class"],
            confidence_score=confidence_score,
            explanation=explanation,
            screened_by=screened_by,
        )

        return {
            "screening_id": screening_id,
            "application_id": application_id,
            "model_version_id": self.model_version_id,
            **result,
        }
