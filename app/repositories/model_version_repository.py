
import json
from datetime import datetime
from pathlib import Path

from database.connection import get_connection


class ModelVersionRepository:
    """Database operations for saved ML model versions."""

    @staticmethod
    def register_model(artifact, artifact_path):
        required_metadata = {
            "model_version",
            "dataset",
            "trained_at_utc",
            "features",
            "metrics",
        }

        missing = required_metadata - set(artifact)

        if missing:
            raise ValueError(
                "Missing model metadata: "
                + ", ".join(sorted(missing))
            )

        version_name = artifact["model_version"]
        metrics = artifact["metrics"]

        if not version_name or len(version_name) > 100:
            raise ValueError("Invalid model version name.")

        artifact_path = str(Path(artifact_path).resolve())

        if len(artifact_path) > 500:
            raise ValueError(
                "Model artifact path exceeds 500 characters."
            )

        feature_config = json.dumps({
            "features": artifact["features"],
            "dataset": artifact["dataset"],
            "training_configuration": artifact.get(
                "training_configuration", {}
            ),
        })

        trained_at = datetime.fromisoformat(
            artifact["trained_at_utc"]
        ).replace(tzinfo=None)

        connection = get_connection()

        try:
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT model_version_id
                FROM model_versions
                WHERE version_name = %s
                """,
                (version_name,),
            )

            existing = cursor.fetchone()

            if existing:
                model_version_id = existing["model_version_id"]

                cursor.execute(
                    """
                    UPDATE model_versions
                    SET algorithm = %s,
                        artifact_path = %s,
                        feature_config = %s,
                        accuracy = %s,
                        precision_score = %s,
                        recall_score = %s,
                        f1_score = %s,
                        trained_at = %s
                    WHERE model_version_id = %s
                    """,
                    (
                        "Random Forest Classifier",
                        artifact_path,
                        feature_config,
                        metrics.get("accuracy"),
                        metrics.get("precision"),
                        metrics.get("recall"),
                        metrics.get("f1_score"),
                        trained_at,
                        model_version_id,
                    ),
                )

            else:
                # Deactivate previous model versions before
                # activating this newly registered version.
                cursor.execute(
                    """
                    UPDATE model_versions
                    SET is_active = 0
                    WHERE is_active = 1
                    """
                )

                cursor.execute(
                    """
                    INSERT INTO model_versions (
                        version_name,
                        algorithm,
                        artifact_path,
                        feature_config,
                        accuracy,
                        precision_score,
                        recall_score,
                        f1_score,
                        is_active,
                        trained_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        version_name,
                        "Random Forest Classifier",
                        artifact_path,
                        feature_config,
                        metrics.get("accuracy"),
                        metrics.get("precision"),
                        metrics.get("recall"),
                        metrics.get("f1_score"),
                        1,
                        trained_at,
                    ),
                )

                model_version_id = cursor.lastrowid

            connection.commit()
            return model_version_id

        except Exception:
            connection.rollback()
            raise

        finally:
            try:
                cursor.close()
            finally:
                connection.close()
