import os
import sys

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split


DEFAULT_CSV = "isko.csv"


WEIGHTS = {
    "AcademicAverage": 13.64,
    "MonthlyFamilyIncome": 18.18,
    "MSWDOPovertyEligible": 18.18,
    "HouseHold": 4.55,
    "ChildrenCount": 9.09,
    "SeniorCount": 9.09,
    "PWDCount": 9.09,
    "SoloParent": 4.55,
    "Dependent": 9.09,
    "ExamPassed": 4.55,
}


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


def mswd_threshold(household, children, seniors, pwds):
    return (
        max(15000, 4000 * household)
        + 2000 * children
        + 2000 * seniors
        + 2500 * pwds
    )


def clip01(x):
    return max(0.0, min(1.0, x))


def ask_float(prompt, lo, hi):
    while True:
        try:
            value = float(input(prompt).strip().replace(",", ""))

            if lo <= value <= hi:
                return value

        except ValueError:
            pass

        print("Invalid input. Please enter a valid number.")


def ask_int(prompt, lo, hi):
    while True:
        try:
            value = int(input(prompt).strip())

            if lo <= value <= hi:
                return value

        except ValueError:
            pass

        print("Invalid input. Please enter a whole number.")


def ask_yes_no(prompt):
    while True:
        value = input(prompt + " (y/n): ").strip().lower()

        if value in ("y", "yes"):
            return 1

        if value in ("n", "no"):
            return 0

        print("Invalid input. Please enter y or n.")


def load_and_train(csv_path):
    df = pd.read_csv(csv_path)

    X = pd.DataFrame({
        "AcademicAverage": df["AcademicAverage"],
        "MonthlyIncome": df["MonthlyIncome"],
        "MSWDOPovertyEligible":
            (df["MSWDOPovertyEligible"] == "Yes").astype(int),
        "Household": df["Household"],
        "ChildrenCount": df["ChildrenCount"],
        "SeniorCount": df["SeniorCount"],
        "PWDCount": df["PWDCount"],
        "SoloParent":
            (df["SoloParent"] == "Yes").astype(int),
        "Dependent": df["Dependent"],
        "ExamPassed":
            (df["ExamPassed"] == "Yes").astype(int),
        "4psBeneficiaries":
            (df["4psBeneficiaries"] == "Yes").astype(int),
        "SPESBeneficiaries":
            (df["SPESBeneficiaries"] == "Yes").astype(int),
        "ScholarsInFamily":
            (df["ScholarsInFamily"] >= 1).astype(int),
    })[FEATURES]

    y = (df["ScholarshipQualified"] == "Yes").astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=300,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, y_train)

    accuracy = accuracy_score(
        y_test,
        model.predict(X_test)
    )

    return model, accuracy


def passing_rate(applicant, mswd_eligible, threshold):

    income = applicant["income"]

    if income <= threshold:
        income_score = (
            0.5
            + 0.5 * (threshold - income) / threshold
        )
    else:
        income_score = (
            0.5
            * clip01(
                1 - (income - threshold) / threshold
            )
        )

    scores = {
        "AcademicAverage":
            clip01((applicant["average"] - 75) / 25),

        "MonthlyFamilyIncome":
            clip01(income_score),

        "MSWDOPovertyEligible":
            1.0 if mswd_eligible else 0.0,

        "HouseHold":
            clip01((applicant["household"] - 1) / 7),

        "ChildrenCount":
            clip01(applicant["children"] / 5),

        "SeniorCount":
            clip01(applicant["seniors"] / 2),

        "PWDCount":
            clip01(applicant["pwds"] / 2),

        "SoloParent":
            float(applicant["solo"]),

        "Dependent":
            clip01(applicant["dependents"] / 7),

        "ExamPassed":
            float(applicant["exam_passed"]),
    }

    total_weight = sum(WEIGHTS.values())

    rate = (
        sum(
            scores[key] * WEIGHTS[key]
            for key in WEIGHTS
        )
        / total_weight
        * 100
    )

    return rate


def collect_applicant():

    applicant = {}

    print()
    print("Enter Applicant Information")
    print()

    applicant["average"] = ask_float(
        "Academic average: ",
        0,
        100
    )

    applicant["income"] = ask_float(
        "Monthly family income: ",
        0,
        10_000_000
    )

    applicant["household"] = ask_int(
        "Household size: ",
        1,
        30
    )

    applicant["children"] = ask_int(
        "Number of children: ",
        0,
        30
    )

    applicant["seniors"] = ask_int(
        "Number of senior citizens: ",
        0,
        30
    )

    applicant["pwds"] = ask_int(
        "Number of PWD members: ",
        0,
        30
    )

    applicant["dependents"] = ask_int(
        "Number of dependents: ",
        0,
        30
    )

    applicant["solo"] = ask_yes_no(
        "Solo parent?"
    )

    total_items = ask_int(
        "Exam total items: ",
        1,
        1000
    )

    applicant["exam_score"] = ask_int(
        f"Exam score (0-{total_items}): ",
        0,
        total_items
    )

    applicant["exam_total"] = total_items

    applicant["exam_passed"] = (
        1
        if applicant["exam_score"] >= 0.8 * total_items
        else 0
    )

    applicant["fourps"] = ask_yes_no(
        "4Ps beneficiary?"
    )

    applicant["spes"] = ask_yes_no(
        "SPES beneficiary?"
    )

    scholars = ask_int(
        "Scholars already in the family: ",
        0,
        30
    )

    applicant["scholars"] = (
        1 if scholars >= 1 else 0
    )

    return applicant


def evaluate(model, applicant):

    threshold = mswd_threshold(
        applicant["household"],
        applicant["children"],
        applicant["seniors"],
        applicant["pwds"]
    )

    mswd_eligible = (
        applicant["income"] <= threshold
    )

    row = pd.DataFrame([{
        "AcademicAverage":
            applicant["average"],

        "MonthlyIncome":
            applicant["income"],

        "MSWDOPovertyEligible":
            int(mswd_eligible),

        "Household":
            applicant["household"],

        "ChildrenCount":
            applicant["children"],

        "SeniorCount":
            applicant["seniors"],

        "PWDCount":
            applicant["pwds"],

        "SoloParent":
            applicant["solo"],

        "Dependent":
            applicant["dependents"],

        "ExamPassed":
            applicant["exam_passed"],

        "4psBeneficiaries":
            applicant["fourps"],

        "SPESBeneficiaries":
            applicant["spes"],

        "ScholarsInFamily":
            applicant["scholars"],
    }])[FEATURES]

    prediction = model.predict(row)[0]

    probability = (
        model.predict_proba(row)[0][1]
        * 100
    )

    rate = passing_rate(
        applicant,
        mswd_eligible,
        threshold
    )

    reasons = []

    if applicant["average"] <= 75:
        reasons.append(
            "Academic average must be greater than 75"
        )

    if applicant["spes"]:
        reasons.append(
            "Applicant is an SPES beneficiary"
        )

    if applicant["fourps"]:
        reasons.append(
            "Applicant is a 4Ps beneficiary"
        )

    if applicant["scholars"]:
        reasons.append(
            "Family already has a scholar"
        )

    qualified = (
        not reasons
        and prediction == 1
    )

    exam_percentage = (
        applicant["exam_score"]
        / applicant["exam_total"]
        * 100
    )

    print()
    print("Evaluation Result")
    print()

    print(
        f"Exam result: "
        f"{applicant['exam_score']}/"
        f"{applicant['exam_total']} "
        f"({exam_percentage:.1f}%)"
    )

    if applicant["exam_passed"]:
        print("Exam status: Passed")
    else:
        print("Exam status: Failed")

    print(
        f"MSWDO income threshold: "
        f"PHP {threshold:,.2f}"
    )

    if mswd_eligible:
        print("MSWDO poverty eligible: Yes")
    else:
        print("MSWDO poverty eligible: No")

    print(
        f"Random Forest probability: "
        f"{probability:.2f}%"
    )

    print(
        f"Passing rate: "
        f"{rate:.2f}%"
    )

    if reasons:
        print()
        print("Disqualification reasons:")

        for reason in reasons:
            print("-", reason)

    print()

    if qualified:
        print("Final result: QUALIFIED")
    else:
        print("Final result: NOT QUALIFIED")


def main():

    current_directory = os.path.dirname(
        os.path.abspath(__file__)
    )

    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    else:
        csv_path = os.path.join(
            current_directory,
            DEFAULT_CSV
        )

    if not os.path.exists(csv_path):
        print("Dataset not found:", csv_path)
        sys.exit()

    print("Scholarship Qualification System")
    print()

    model, accuracy = load_and_train(
        csv_path
    )

    print(
        f"Model accuracy: "
        f"{accuracy * 100:.2f}%"
    )

    while True:

        applicant = collect_applicant()

        evaluate(
            model,
            applicant
        )

        print()

        again = input(
            "Evaluate another applicant? (y/n): "
        ).strip().lower()

        if again not in ("y", "yes"):
            break

    print()
    print("Program ended.")


if __name__ == "__main__":

    try:
        main()

    except (KeyboardInterrupt, EOFError):
        print()
        print("Program ended.")