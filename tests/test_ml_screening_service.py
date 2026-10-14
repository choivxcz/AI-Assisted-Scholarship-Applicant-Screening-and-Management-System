
from app.services.ml_screening_service import (
    load_saved_model,
    evaluate_applicant,
)


def main():
    print("Loading saved scholarship screening model...")

    # Load the existing model; do not retrain it.
    model, artifact = load_saved_model()

    metrics = artifact.get("metrics", {})

    print("\nSaved model information:")
    print(f"Version: {artifact.get('model_version')}")
    print(f"Dataset: {artifact.get('dataset')}")
    print(f"Trained at (UTC): {artifact.get('trained_at_utc')}")

    print("\nSaved evaluation metrics:")

    for name, value in metrics.items():
        if isinstance(value, float):
            print(f"{name}: {value:.4f} ({value * 100:.2f}%)")
        else:
            print(f"{name}: {value}")

    # Sample data for testing only.
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

    result = evaluate_applicant(model, sample_applicant)

    print("\nSample screening result:")

    for key, value in result.items():
        print(f"{key}: {value}")

    print("\nSaved-model test completed successfully.")


if __name__ == "__main__":
    main()
