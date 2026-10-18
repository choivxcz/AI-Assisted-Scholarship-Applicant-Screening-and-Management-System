
from pathlib import Path

import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
)
from sklearn.model_selection import train_test_split

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_CSV = PROJECT_ROOT / "isko.csv"

MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "scholarship_random_forest.joblib"
)

FEATURES = [
    "AcademicAverage",
    "MonthlyIncome",
    "MSWDOPovertyEligible",
    "Household",
    "ChildrenCount",
    "SeniorCount",
    "PWDCount",
    "SoloParent",
    "Dependent",
    "ExamPassed",
    "4psBeneficiaries",
    "SPESBeneficiaries",
    "ScholarsInFamily",
]

REQUIRED_COLUMNS = FEATURES + [
    "ScholarshipQualified",
    "MSWDOPovertyEligible",
    "SoloParent",
    "ExamPassed",
    "4psBeneficiaries",
    "SPESBeneficiaries",
    "ScholarsInFamily",
]

def load_saved_model():

    if not MODEL_PATH.is_file():
        raise FileNotFoundError(
            f"Saved model not found: {MODEL_PATH}\n"
            "Please run train_ml_model.py first."
        )

    try:
        artifact = joblib.load(MODEL_PATH)
    except Exception as exc:
        raise RuntimeError(
            f"Unable to load the saved model: {MODEL_PATH}"
        ) from exc

    if not isinstance(artifact, dict):
        raise ValueError(
            "Invalid model artifact. Expected a dictionary."
        )

    saved_features = artifact.get("features")

    if saved_features != FEATURES:
        raise ValueError(
            "The saved model's feature configuration does not "
            "match the current ML service.\n"
            "Please retrain the model using train_ml_model.py."
        )

    model = artifact.get("model")

    if not isinstance(model, RandomForestClassifier):
        raise ValueError(
            "The saved artifact does not contain a valid "
            "RandomForestClassifier."
        )

    if not hasattr(model, "n_features_in_"):
        raise ValueError(
            "The saved model has not been fitted."
        )

    if model.n_features_in_ != len(FEATURES):
        raise ValueError(
            "The saved model has an unexpected number of features."
        )

    if list(model.classes_) != [0, 1]:
        raise ValueError(
            "The saved model must support both classes: "
            "0 = Not qualified and 1 = Qualified."
        )

    return model, artifact

def _yes_no_to_int(series):
    """Convert Yes/No values to 1/0."""

    values = series.astype(str).str.strip().str.lower()

    invalid = ~values.isin(["yes", "no"])

    if invalid.any():
        raise ValueError(
            "Unexpected Yes/No values: "
            f"{values[invalid].unique().tolist()}"
        )

    return values.map({
        "yes": 1,
        "no": 0,
    }).astype(int)


def prepare_features(df):

    X = pd.DataFrame(index=df.index)

    X["AcademicAverage"] = pd.to_numeric(
        df["AcademicAverage"],
        errors="raise",
    )

    X["MonthlyIncome"] = pd.to_numeric(
        df["MonthlyIncome"],
        errors="raise",
    )

    X["MSWDOPovertyEligible"] = _yes_no_to_int(
        df["MSWDOPovertyEligible"]
    )

    X["Household"] = pd.to_numeric(
        df["Household"],
        errors="raise",
    )

    X["ChildrenCount"] = pd.to_numeric(
        df["ChildrenCount"],
        errors="raise",
    )

    X["SeniorCount"] = pd.to_numeric(
        df["SeniorCount"],
        errors="raise",
    )

    X["PWDCount"] = pd.to_numeric(
        df["PWDCount"],
        errors="raise",
    )

    X["SoloParent"] = _yes_no_to_int(
        df["SoloParent"]
    )

    X["Dependent"] = pd.to_numeric(
        df["Dependent"],
        errors="raise",
    )

    X["ExamPassed"] = _yes_no_to_int(
        df["ExamPassed"]
    )

    X["4psBeneficiaries"] = _yes_no_to_int(
        df["4psBeneficiaries"]
    )

    X["SPESBeneficiaries"] = _yes_no_to_int(
        df["SPESBeneficiaries"]
    )

    X["ScholarsInFamily"] = (
        pd.to_numeric(
            df["ScholarsInFamily"],
            errors="raise",
        ) >= 1
    ).astype(int)

    X = X[FEATURES]

    if X.isnull().any().any():
        raise ValueError(
            "Dataset contains missing feature values."
        )

    if not X.apply(
        lambda column: column.map(
            lambda value: (
                pd.notna(value)
                and float(value) != float("inf")
                and float(value) != float("-inf")
            )
        )
    ).all().all():
        raise ValueError(
            "Dataset contains non-finite feature values."
        )

    return X

def load_and_train(csv_path=DEFAULT_CSV):

    csv_path = Path(csv_path)

    if not csv_path.is_absolute():
        csv_path = PROJECT_ROOT / csv_path

    if not csv_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {csv_path}"
        )

    df = pd.read_csv(csv_path)

    missing = set(REQUIRED_COLUMNS) - set(df.columns)

    if missing:
        raise ValueError(
            "Dataset is missing columns: "
            + ", ".join(sorted(missing))
        )

    labels = (
        df["ScholarshipQualified"]
        .astype(str)
        .str.strip()
    )

    invalid_labels = ~labels.isin(["Yes", "No"])

    if invalid_labels.any():
        raise ValueError(
            "ScholarshipQualified must contain only Yes or No."
        )

    X = prepare_features(df)

    y = labels.map({
        "No": 0,
        "Yes": 1,
    }).astype(int)

    if y.nunique() != 2 or y.value_counts().min() < 2:
        raise ValueError(
            "Training requires at least two examples of each class."
        )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )

    model = RandomForestClassifier(
        n_estimators=300,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    metrics = {
        "accuracy": accuracy_score(
            y_test,
            predictions,
        ),
        "precision": precision_score(
            y_test,
            predictions,
            zero_division=0,
        ),
        "recall": recall_score(
            y_test,
            predictions,
            zero_division=0,
        ),
        "f1_score": f1_score(
            y_test,
            predictions,
            zero_division=0,
        ),
        "training_rows": len(X_train),
        "testing_rows": len(X_test),
    }

    return model, metrics

def mswd_threshold(household, children, seniors, pwds):
    
    return (
        max(15000, 4000 * household)
        + 2000 * children
        + 2000 * seniors
        + 2500 * pwds
    )

def evaluate_applicant(model, applicant):

    required = {
        "average",
        "income",
        "household",
        "children",
        "seniors",
        "pwds",
        "dependents",
        "solo",
        "exam_score",
        "exam_total",
        "exam_passed",
        "fourps",
        "spes",
        "scholars",
    }

    missing = required - set(applicant)

    if missing:
        raise ValueError(
            "Missing applicant values: "
            + ", ".join(sorted(missing))
        )

    average = float(applicant["average"])
    income = float(applicant["income"])

    household = int(applicant["household"])
    children = int(applicant["children"])
    seniors = int(applicant["seniors"])
    pwds = int(applicant["pwds"])
    dependents = int(applicant["dependents"])

    exam_score = int(applicant["exam_score"])
    exam_total = int(applicant["exam_total"])

    if not 0 <= average <= 100:
        raise ValueError(
            "Academic average must be between 0 and 100."
        )

    if income < 0:
        raise ValueError(
            "Monthly income cannot be negative."
        )

    if household < 1:
        raise ValueError(
            "Household size must be at least 1."
        )

    if min(children, seniors, pwds, dependents) < 0:
        raise ValueError(
            "Household counts cannot be negative."
        )

    if children + seniors + pwds > household:
        raise ValueError(
            "Children, seniors, and PWD counts cannot exceed "
            "household size."
        )

    if exam_total < 1 or not 0 <= exam_score <= exam_total:
        raise ValueError(
            "Exam score or total items is invalid."
        )

    for key in ("solo", "exam_passed", "fourps", "spes"):
        if applicant[key] not in (0, 1, False, True):
            raise ValueError(
                f"{key} must be a Boolean or 0/1."
            )

    scholars = int(applicant["scholars"])

    if scholars < 0:
        raise ValueError(
            "Scholars count cannot be negative."
        )

    exam_passed = int(
        exam_score >= 0.8 * exam_total
    )

    threshold = mswd_threshold(
        household,
        children,
        seniors,
        pwds,
    )

    mswd_eligible = income <= threshold

    row = pd.DataFrame([{
        "AcademicAverage": average,
        "MonthlyIncome": income,
        "MSWDOPovertyEligible": int(mswd_eligible),
        "Household": household,
        "ChildrenCount": children,
        "SeniorCount": seniors,
        "PWDCount": pwds,
        "SoloParent": int(applicant["solo"]),
        "Dependent": dependents,
        "ExamPassed": exam_passed,
        "4psBeneficiaries": int(applicant["fourps"]),
        "SPESBeneficiaries": int(applicant["spes"]),
        "ScholarsInFamily": int(scholars >= 1),
    }])[FEATURES]

    prediction = int(model.predict(row)[0])

    probabilities = dict(
        zip(
            model.classes_,
            model.predict_proba(row)[0],
        )
    )

    probability = float(
        probabilities.get(1, 0.0)
    ) * 100

    reasons = []

    if average <= 75:
        reasons.append(
            "Academic average must be greater than 75."
        )

    if applicant["spes"]:
        reasons.append(
            
            "Applicant is an SPES beneficiary."
        )

    if applicant["fourps"]:
        reasons.append(
            "Applicant is a 4Ps beneficiary."
        )

    if scholars >= 1:
        reasons.append(
            "Family already has a scholar."
        )
    qualified = not reasons and prediction == 1

    exam_percentage = (
        exam_score / exam_total * 100
    )

    return {
        "predicted_class": (
            "Proceed To Interview"
            if qualified
            else "Needs Official Review"
        ),
        "model_prediction": (
            "QUALIFIED"
            if prediction == 1
            else "NOT_QUALIFIED"
        ),
        "model_probability_percent": probability,
        "exam_percentage": exam_percentage,
        "exam_passed": bool(exam_passed),
        "mswd_threshold": threshold,
        "mswd_eligible": bool(mswd_eligible),
        "reasons": reasons,
        "passing_rate": None,
        "requires_human_review": True,
    }
