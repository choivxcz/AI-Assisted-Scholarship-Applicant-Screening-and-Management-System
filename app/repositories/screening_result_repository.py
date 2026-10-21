
import json

from database.connection import get_connection


ALLOWED_PREDICTIONS = {
    "PROCEED_TO_INTERVIEW",
    "NEEDS_OFFICIAL_REVIEW",
    "REJECTED",
}


class ScreeningResultRepository:
    """Database operations for applicant screening results."""

    @staticmethod
    def create(
        application_id,
        model_version_id,
        predicted_class,
        confidence_score,
        explanation,
        screened_by=None,
    ):
        """Save a new screening result."""

        if not isinstance(application_id, int) or application_id <= 0:
            raise ValueError("A valid application ID is required.")

        if not isinstance(model_version_id, int) or model_version_id <= 0:
            raise ValueError("A valid model version ID is required.")

        if predicted_class not in ALLOWED_PREDICTIONS:
            raise ValueError(
                f"Unsupported screening class: {predicted_class}"
            )

        if confidence_score is not None:
            confidence_score = float(confidence_score)

            if not 0 <= confidence_score <= 1:
                raise ValueError(
                    "Confidence score must be between 0 and 1."
                )

        if screened_by is not None and (
            not isinstance(screened_by, int) or screened_by <= 0
        ):
            raise ValueError(
                "screened_by must be a valid user ID or None."
            )

        connection = get_connection()
        cursor = None

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO screening_results (
                    application_id,
                    model_version_id,
                    predicted_class,
                    confidence_score,
                    explanation,
                    screened_by
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    application_id,
                    model_version_id,
                    predicted_class,
                    confidence_score,
                    explanation,
                    screened_by,
                ),
            )

            screening_id = cursor.lastrowid
            connection.commit()

            return screening_id

        except Exception:
            connection.rollback()
            raise

        finally:
            if cursor is not None:
                cursor.close()

            connection.close()

    @staticmethod
    def get_latest_for_applications(application_ids):
        """
        Return the latest screening result for each requested application.

        The screening input fingerprint is extracted from the existing
        explanation JSON. Older screening records without a fingerprint
        return None, allowing the screening service to establish a baseline.
        """

        ids = [int(value) for value in application_ids]

        if not ids:
            return {}

        placeholders = ", ".join(["%s"] * len(ids))

        query = f"""
            SELECT
                sr.screening_id,
                sr.application_id,
                sr.model_version_id,
                sr.predicted_class,
                sr.confidence_score,
                sr.explanation,
                sr.screened_by,
                sr.screened_at,
                mv.version_name
            FROM screening_results AS sr
            JOIN (
                SELECT
                    application_id,
                    MAX(screening_id) AS latest_screening_id
                FROM screening_results
                WHERE application_id IN ({placeholders})
                GROUP BY application_id
            ) AS latest
                ON latest.latest_screening_id = sr.screening_id
            JOIN model_versions AS mv
                ON mv.model_version_id = sr.model_version_id
        """

        connection = get_connection()
        cursor = None

        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, tuple(ids))

            rows = cursor.fetchall()
            results = {}

            for row in rows:
                explanation = row.get("explanation")
                parsed = {}

                if explanation:
                    try:
                        if isinstance(explanation, dict):
                            parsed = explanation
                        else:
                            parsed = json.loads(explanation)

                        if not isinstance(parsed, dict):
                            parsed = {}

                    except (TypeError, ValueError):
                        parsed = {"note": str(explanation)}

                probability = row.get("confidence_score")

                row["confidence_score"] = (
                    float(probability)
                    if probability is not None
                    else None
                )

                row["model_probability_percent"] = (
                    float(probability) * 100
                    if probability is not None
                    else None
                )

                row["model_prediction"] = parsed.get(
                    "model_prediction",
                    "Not available",
                )

                row["reasons"] = parsed.get("reasons", [])

                row["exam_percentage"] = parsed.get(
                    "exam_percentage"
                )

                row["exam_passed"] = parsed.get("exam_passed")

                row["mswd_threshold"] = parsed.get(
                    "mswd_threshold"
                )

                row["mswd_eligible"] = parsed.get(
                    "mswd_eligible"
                )

                # NEW: Retrieve the fingerprint stored in explanation JSON.
                # Legacy records won't have this field, so their value is None.
                row["screening_input_fingerprint"] = parsed.get(
                    "screening_input_fingerprint"
                )

                row["screened_at"] = str(
                    row.get("screened_at") or ""
                )

                results[int(row["application_id"])] = row

            return results

        finally:
            if cursor is not None:
                cursor.close()

            connection.close()
