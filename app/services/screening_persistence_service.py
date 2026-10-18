
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

        result = evaluate_applicant(
            self.model,
            applicant_data,
        )
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
