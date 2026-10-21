
import hashlib
import json

from app.repositories.model_version_repository import ModelVersionRepository
from app.repositories.screening_result_repository import ScreeningResultRepository
from app.services.ml_screening_service import (
    MODEL_PATH,
    evaluate_applicant,
    load_saved_model,
)


PERSISTED_PREDICTIONS = {
    "Proceed To Interview": "PROCEED_TO_INTERVIEW",
    "Needs Official Review": "NEEDS_OFFICIAL_REVIEW",
}


class ScreeningPersistenceService:
    def __init__(self):
        self.model, self.artifact = load_saved_model()

        self.model_version_id = ModelVersionRepository.register_model(
            self.artifact,
            MODEL_PATH,
        )

    def create_input_fingerprint(self, applicant_data):
        """
        Generate a deterministic fingerprint for the effective screening inputs
        and the currently registered model version.

        Identical inputs and model versions produce identical fingerprints.
        Changes to screening inputs or the model version produce a new
        fingerprint.
        """
        exam_score = int(float(applicant_data["exam_score"]))
        exam_total = int(float(applicant_data["exam_total"]))

        # The screening service derives exam_passed from the exam score
        # and total, so fingerprint the derived value actually used.
        effective_inputs = {
            "average": float(applicant_data["average"]),
            "income": float(applicant_data["income"]),
            "household": int(applicant_data["household"]),
            "children": int(applicant_data["children"]),
            "seniors": int(applicant_data["seniors"]),
            "pwds": int(applicant_data["pwds"]),
            "dependents": int(applicant_data["dependents"]),
            "solo": int(bool(applicant_data["solo"])),
            "exam_score": exam_score,
            "exam_total": exam_total,
            "exam_passed": int(exam_score >= 0.8 * exam_total),
            "fourps": int(bool(applicant_data["fourps"])),
            "spes": int(bool(applicant_data["spes"])),
            "scholars": int(applicant_data["scholars"]),
        }

        fingerprint_payload = {
            "model_version_id": int(self.model_version_id),
            "model_version": str(self.artifact["model_version"]),
            "inputs": effective_inputs,
        }

        canonical_json = json.dumps(
            fingerprint_payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        return hashlib.sha256(
            canonical_json.encode("utf-8")
        ).hexdigest()

    def screen_application(
        self,
        application_id,
        applicant_data,
        screened_by=None,
    ):
        result = evaluate_applicant(self.model, applicant_data)

        fingerprint = self.create_input_fingerprint(applicant_data)

        confidence_score = result["model_probability_percent"] / 100.0

        explanation = json.dumps(
            {
                "model_version": self.artifact["model_version"],
                "model_prediction": result["model_prediction"],
                "model_probability_percent": result[
                    "model_probability_percent"
                ],
                "exam_percentage": result["exam_percentage"],
                "exam_passed": result["exam_passed"],
                "mswd_threshold": result["mswd_threshold"],
                "mswd_eligible": result["mswd_eligible"],
                "reasons": result["reasons"],
                "screening_input_fingerprint": fingerprint,
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
            predicted_class=PERSISTED_PREDICTIONS[
                result["predicted_class"]
            ],
            confidence_score=confidence_score,
            explanation=explanation,
            screened_by=screened_by,
        )

        return {
            "screening_id": screening_id,
            "application_id": application_id,
            "model_version_id": self.model_version_id,
            "screening_input_fingerprint": fingerprint,
            **result,
        }
