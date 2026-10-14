
from datetime import datetime, timezone
from pathlib import Path

import joblib

from app.services.ml_screening_service import (
    FEATURES,
    load_and_train,
)


PROJECT_ROOT = Path(__file__).resolve().parent
MODEL_DIR = PROJECT_ROOT / "models"
MODEL_PATH = MODEL_DIR / "scholarship_random_forest.joblib"


def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    print("Training the scholarship screening model...")
    model, metrics = load_and_train()

    artifact = {
        "model": model,
        "features": FEATURES,
        "metrics": metrics,
        "model_version": "rf-1.0.0",
        "trained_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "dataset": "isko.csv",
        "training_configuration": {
            "n_estimators": 300,
            "min_samples_leaf": 3,
            "random_state": 42,
            "test_size": 0.20,
        },
    }

    joblib.dump(artifact, MODEL_PATH)

    print("\nModel saved successfully.")
    print(f"Location: {MODEL_PATH}")
    print(f"Version: {artifact['model_version']}")

    print("\nEvaluation metrics:")
    for name, value in metrics.items():
        if isinstance(value, float):
            print(f"{name}: {value:.4f}")
        else:
            print(f"{name}: {value}")


if __name__ == "__main__":
    main()
