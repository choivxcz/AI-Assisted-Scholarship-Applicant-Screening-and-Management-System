
from app.repositories.applicant_repository import ApplicantRepository
from app.repositories.application_repository import ApplicationRepository
from database.connection import get_connection


class ApplicationService:
    ALLOWED_TRANSITIONS = {
        "DRAFT": {"SUBMITTED", "WITHDRAWN"},
        "SUBMITTED": {"UNDER_REVIEW", "WITHDRAWN"},
        "UNDER_REVIEW": {
            "FOR_INTERVIEW", "REJECTED", "WAITLISTED", "WITHDRAWN"
        },
        "FOR_INTERVIEW": {"INTERVIEWED", "WITHDRAWN"},
        "INTERVIEWED": {
            "RECOMMENDED", "REJECTED", "WAITLISTED", "WITHDRAWN"
        },
        "RECOMMENDED": {"APPROVED", "REJECTED", "WAITLISTED"},
        "WAITLISTED": {"APPROVED", "REJECTED", "WITHDRAWN"},
        "APPROVED": set(),
        "REJECTED": set(),
        "WITHDRAWN": set(),
    }

    @staticmethod
    def mswdo_threshold(household, children, seniors, pwds):
        return (
            max(15000, 4000 * household)
            + 2000 * children
            + 2000 * seniors
            + 2500 * pwds
        )

    @staticmethod
    def register_applicant_with_application(
        applicant_data, application_data
    ):
        applicant_data = dict(applicant_data)
        application_data = dict(application_data)

        # Validate personal information.
        for field in (
            "first_name", "last_name", "barangay",
            "municipality", "province"
        ):
            applicant_data[field] = (
                ApplicantRepository._validate_required_text(
                    applicant_data.get(field),
                    field.replace("_", " ").title()
                )
            )

        applicant_data["sex"] = ApplicantRepository._validate_sex(
            applicant_data.get("sex")
        )

        for field in (
            "middle_name", "suffix", "email", "phone",
            "house_no_street"
        ):
            value = applicant_data.get(field)
            if isinstance(value, str):
                applicant_data[field] = value.strip() or None

        # Required application inputs.
        required = {
            "scholarship_program",
            "scholarship_year",
            "academic_average",
            "monthly_income",
            "household",
            "children_count",
            "senior_count",
            "pwd_count",
            "dependents_count",
            "solo_parent",
            "exam_raw_score",
            "exam_total_items",
            "four_ps_beneficiary",
            "spes_beneficiary",
            "scholars_in_family",
            "residency",
            "previous_scholarship",
            "status",
            "submitted_at",
        }

        missing = required - set(application_data)
        if missing:
            raise ValueError(
                "Missing application field(s): "
                + ", ".join(sorted(missing))
            )

        # Validate household counts.
        household = int(application_data["household"])
        children = int(application_data["children_count"])
        seniors = int(application_data["senior_count"])
        pwds = int(application_data["pwd_count"])
        dependents = int(application_data["dependents_count"])

        if household < 1:
            raise ValueError("Household size must be at least 1.")

        if min(children, seniors, pwds, dependents) < 0:
            raise ValueError("Household counts cannot be negative.")

        if children + seniors + pwds > household:
            raise ValueError(
                "Children, seniors, and PWD counts cannot exceed "
                "household size."
            )

        application_data["household"] = household
        application_data["children_count"] = children
        application_data["senior_count"] = seniors
        application_data["pwd_count"] = pwds
        application_data["dependents_count"] = dependents

        # Calculate MSWDO poverty eligibility.
        threshold = ApplicationService.mswdo_threshold(
            household, children, seniors, pwds
        )
        income = float(application_data["monthly_income"])

        if income < 0:
            raise ValueError("Monthly income cannot be negative.")

        application_data["mswdo_poverty_eligible"] = (
            income <= threshold
        )

        # Keep dependent Boolean compatible with the old schema.
        application_data["dependent"] = dependents > 0

        # Calculate exam percentage and pass status.
        raw_score = application_data["exam_raw_score"]
        total_items = application_data["exam_total_items"]

        if raw_score is None and total_items is None:
            application_data["exam_score"] = None
            application_data["exam_passed"] = False
        else:
            if raw_score is None or total_items is None:
                raise ValueError(
                    "Enter both the exam score and total exam items."
                )

            raw_score = int(raw_score)
            total_items = int(total_items)

            if total_items < 1:
                raise ValueError(
                    "Total exam items must be at least 1."
                )

            if raw_score < 0 or raw_score > total_items:
                raise ValueError(
                    "Exam score must be between 0 and total exam items."
                )

            application_data["exam_raw_score"] = raw_score
            application_data["exam_total_items"] = total_items
            application_data["exam_score"] = round(
                raw_score / total_items * 100, 2
            )
            application_data["exam_passed"] = (
                raw_score >= 0.8 * total_items
            )

        # Validate the application fields supported by the repository.
        application_data = (
            ApplicationRepository._validate_application(
                application_data
            )
        )

        applicant_columns = [
            "first_name", "middle_name", "last_name", "suffix",
            "birth_date", "sex", "email", "phone",
            "house_no_street", "barangay", "municipality", "province",
        ]

        application_columns = [
            "scholarship_program", "scholarship_year",
            "academic_average", "monthly_income",
            "mswdo_poverty_eligible", "household", "children_count",
            "senior_count", "pwd_count", "solo_parent", "dependent",
            "dependents_count", "exam_score", "exam_raw_score",
            "exam_total_items", "exam_passed", "four_ps_beneficiary",
            "spes_beneficiary", "scholars_in_family", "residency",
            "previous_scholarship", "status", "submitted_at",
        ]

        connection = get_connection()

        try:
            connection.start_transaction()

            with connection.cursor() as cursor:
                applicant_sql = (
                    "INSERT INTO applicants ("
                    + ", ".join(f"`{c}`" for c in applicant_columns)
                    + ") VALUES ("
                    + ", ".join(["%s"] * len(applicant_columns))
                    + ")"
                )

                cursor.execute(
                    applicant_sql,
                    tuple(
                        applicant_data.get(c)
                        for c in applicant_columns
                    ),
                )
                applicant_id = cursor.lastrowid

                columns = ["applicant_id", *application_columns]
                application_sql = (
                    "INSERT INTO applications ("
                    + ", ".join(f"`{c}`" for c in columns)
                    + ") VALUES ("
                    + ", ".join(["%s"] * len(columns))
                    + ")"
                )

                values = [
                    applicant_id,
                    *[
                        application_data[c]
                        for c in application_columns
                    ],
                ]

                cursor.execute(application_sql, tuple(values))
                application_id = cursor.lastrowid

            connection.commit()
            return applicant_id, application_id

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    @staticmethod
    def change_status(application_id, new_status):
        if not isinstance(new_status, str):
            raise ValueError("New status must be a string.")

        new_status = new_status.strip().upper()

        if new_status not in ApplicationRepository.ALLOWED_STATUSES:
            raise ValueError(f"Invalid application status: {new_status}")

        application = ApplicationRepository.get_by_id(application_id)

        if application is None:
            return False

        current_status = application["status"]

        if new_status == current_status:
            return True

        allowed = ApplicationService.ALLOWED_TRANSITIONS.get(
            current_status, set()
        )

        if new_status not in allowed:
            raise ValueError(
                f"Cannot change application status from "
                f"{current_status} to {new_status}."
            )

        return ApplicationRepository.update(
            application_id,
            status=new_status,
        )
