
from app.repositories.applicant_repository import ApplicantRepository
from app.repositories.application_repository import ApplicationRepository
from database.connection import get_connection


class ApplicationService:
    ALLOWED_TRANSITIONS = {
        "DRAFT": {"SUBMITTED", "FOR_INTERVIEW", "WITHDRAWN"},
        "SUBMITTED": {"UNDER_REVIEW", "FOR_INTERVIEW", "WITHDRAWN"},
        "UNDER_REVIEW": {
            "FOR_INTERVIEW",
            "REJECTED",
            "WAITLISTED",
            "WITHDRAWN",
        },
        "FOR_INTERVIEW": {"INTERVIEWED", "WITHDRAWN"},
        "INTERVIEWED": {
            "RECOMMENDED",
            "REJECTED",
            "WAITLISTED",
            "WITHDRAWN",
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
    def _as_int(value, field_name):
        if isinstance(value, bool):
            raise ValueError(f"{field_name} must be a whole number.")

        try:
            result = int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field_name} must be a whole number.")

        if str(value).strip() != str(result):
            raise ValueError(f"{field_name} must be a whole number.")

        return result

    @classmethod
    def register_applicant_with_application(
        cls, applicant_data, application_data
    ):
        applicant_data = dict(applicant_data)
        application_data = dict(application_data)

        required_applicant = [
            "first_name",
            "last_name",
            "house_no_street",
            "barangay",
            "municipality",
            "province",
        ]

        for field in required_applicant:
            value = applicant_data.get(field)
            if value is None or not str(value).strip():
                raise ValueError(f"{field.replace('_', ' ').title()} is required.")

        for field in (
            "first_name",
            "middle_name",
            "last_name",
            "suffix",
            "house_no_street",
            "barangay",
            "municipality",
            "province",
        ):
            if field in applicant_data:
                value = applicant_data[field]
                applicant_data[field] = (
                    str(value).strip() or None if value is not None else None
                )

        applicant_data["first_name"] = applicant_data["first_name"]
        applicant_data["last_name"] = applicant_data["last_name"]

        # Use the existing repository validators when available.
        if applicant_data.get("birth_date") and hasattr(
            ApplicantRepository, "_validate_birth_date"
        ):
            ApplicantRepository._validate_birth_date(
                applicant_data["birth_date"]
            )

        if applicant_data.get("sex") and hasattr(
            ApplicantRepository, "_validate_sex"
        ):
            ApplicantRepository._validate_sex(applicant_data["sex"])

        if applicant_data.get("email") and hasattr(
            ApplicantRepository, "_validate_email"
        ):
            ApplicantRepository._validate_email(applicant_data["email"])

        if applicant_data.get("phone") and hasattr(
            ApplicantRepository, "_validate_phone"
        ):
            ApplicantRepository._validate_phone(applicant_data["phone"])

        required_application = [
            "scholarship_program",
            "scholarship_year",
            "academic_average",
            "monthly_income",
            "household",
            "children_count",
            "senior_count",
            "pwd_count",
            "exam_raw_score",
            "exam_total_items",
        ]

        missing = [
            field
            for field in required_application
            if field not in application_data
            or application_data[field] in (None, "")
        ]
        if missing:
            raise ValueError(
                "Missing application field(s): " + ", ".join(missing)
            )

        household = cls._as_int(application_data["household"], "Household")
        children = cls._as_int(
            application_data.get("children_count", 0), "Children count"
        )
        seniors = cls._as_int(
            application_data.get("senior_count", 0), "Senior count"
        )
        pwds = cls._as_int(
            application_data.get("pwd_count", 0), "PWD count"
        )

        # The current database stores a boolean dependent column, not a count.
        dependents = cls._as_int(
            application_data.get("dependents_count", 0), "Dependents count"
        )

        if household < 1:
            raise ValueError("Household size must be at least 1.")

        if min(children, seniors, pwds, dependents) < 0:
            raise ValueError("Household counts cannot be negative.")

        if children + seniors + pwds > household:
            raise ValueError(
                "Children, seniors, and PWD counts cannot exceed household size."
            )

        raw_score = cls._as_int(
            application_data["exam_raw_score"], "Raw exam score"
        )
        total_items = cls._as_int(
            application_data["exam_total_items"], "Total exam items"
        )

        if total_items < 1:
            raise ValueError("Total exam items must be at least 1.")

        if raw_score < 0 or raw_score > total_items:
            raise ValueError(
                "Raw exam score must be between 0 and total exam items."
            )

        try:
            average = float(application_data["academic_average"])
            income = float(application_data["monthly_income"])
        except (TypeError, ValueError):
            raise ValueError(
                "Academic average and monthly income must be numeric."
            )

        if not 0 <= average <= 100:
            raise ValueError("Academic average must be between 0 and 100.")

        if income < 0:
            raise ValueError("Monthly income cannot be negative.")

        threshold = cls.mswdo_threshold(
            household, children, seniors, pwds
        )

        # These are the only exam values saved to the current database.
        application_data["exam_score"] = round(
            (raw_score / total_items) * 100, 2
        )
        application_data["exam_passed"] = int(
            raw_score >= 0.8 * total_items
        )
        application_data["dependent"] = int(dependents > 0)
        application_data["mswdo_poverty_eligible"] = int(
            income <= threshold
        )

        # Keep transient form fields out of the SQL insert.
        application_data.pop("exam_raw_score", None)
        application_data.pop("exam_total_items", None)
        application_data.pop("dependents_count", None)

        # Apply the repository's validation and column filtering.
        application_data = ApplicationRepository._validate_application(
            application_data
        )

        applicant_columns = [
            "first_name",
            "middle_name",
            "last_name",
            "suffix",
            "birth_date",
            "sex",
            "email",
            "phone",
            "house_no_street",
            "barangay",
            "municipality",
            "province",
        ]

        applicant_data = {
            key: applicant_data_value
            for key, applicant_data_value in applicant_data.items()
            if key in applicant_columns
        }

        application_columns = [
            "scholarship_program",
            "scholarship_year",
            "academic_average",
            "monthly_income",
            "mswdo_poverty_eligible",
            "household",
            "children_count",
            "senior_count",
            "pwd_count",
            "solo_parent",
            "dependent",
            "exam_score",
            "exam_passed",
            "four_ps_beneficiary",
            "spes_beneficiary",
            "scholars_in_family",
            "residency",
            "previous_scholarship",
            "status",
            "submitted_at",
        ]

        application_data = {
            key: application_data[key]
            for key in application_columns
            if key in application_data
        }

        connection = get_connection()
        cursor = connection.cursor()

        try:
            applicant_keys = list(applicant_data.keys())
            applicant_sql = ", ".join(
                f"`{column}`" for column in applicant_keys
            )
            applicant_placeholders = ", ".join(
                ["%s"] * len(applicant_keys)
            )

            cursor.execute(
                f"INSERT INTO applicants ({applicant_sql}) "
                f"VALUES ({applicant_placeholders})",
                tuple(applicant_data[key] for key in applicant_keys),
            )
            applicant_id = cursor.lastrowid

            application_data["applicant_id"] = applicant_id
            application_keys = list(application_data.keys())
            application_sql = ", ".join(
                f"`{column}`" for column in application_keys
            )
            application_placeholders = ", ".join(
                ["%s"] * len(application_keys)
            )

            cursor.execute(
                f"INSERT INTO applications ({application_sql}) "
                f"VALUES ({application_placeholders})",
                tuple(application_data[key] for key in application_keys),
            )
            application_id = cursor.lastrowid

            connection.commit()
            return {
                "applicant_id": applicant_id,
                "application_id": application_id,
            }

        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    @classmethod
    def change_status(cls, application_id, new_status):
        if not isinstance(new_status, str):
            raise ValueError("Application status must be text.")

        new_status = new_status.upper()

        if new_status not in ApplicationRepository.ALLOWED_STATUSES:
            raise ValueError("Invalid application status.")

        current = ApplicationRepository.get_by_id(application_id)
        if not current:
            raise ValueError("Application was not found.")

        old_status = current["status"]

        if old_status == new_status:
            return True

        allowed_next = cls.ALLOWED_TRANSITIONS.get(old_status, set())
        if new_status not in allowed_next:
            raise ValueError(
                f"Status transition from {old_status} to {new_status} is not allowed."
            )

        return ApplicationRepository.update(
            application_id, status=new_status
        )
