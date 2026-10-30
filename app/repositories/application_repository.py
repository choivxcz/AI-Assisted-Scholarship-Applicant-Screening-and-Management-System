
from database.connection import get_connection


class ApplicationRepository:
    ALLOWED_STATUSES = {
        "DRAFT",
        "SUBMITTED",
        "UNDER_REVIEW",
        "FOR_INTERVIEW",
        "INTERVIEWED",
        "RECOMMENDED",
        "APPROVED",
        "REJECTED",
        "WAITLISTED",
        "WITHDRAWN",
    }

    # Only columns that actually exist in the applications table.
    DB_COLUMNS = {
        "applicant_id",
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
    }

    ALLOWED_UPDATE_FIELDS = DB_COLUMNS - {"applicant_id"}

    BOOLEAN_FIELDS = {
        "mswdo_poverty_eligible",
        "solo_parent",
        "dependent",
        "exam_passed",
        "four_ps_beneficiary",
        "spes_beneficiary",
        "previous_scholarship",
    }

    COUNT_FIELDS = {
        "household",
        "children_count",
        "senior_count",
        "pwd_count",
        "scholars_in_family",
    }

    @staticmethod
    def _as_int(value, field_name):
        if isinstance(value, bool):
            raise ValueError(f"{field_name} must be a whole number.")

        try:
            number = int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field_name} must be a whole number.")

        if str(value).strip() != str(number):
            raise ValueError(f"{field_name} must be a whole number.")

        return number

    @classmethod
    def _validate_application(cls, data, *, partial=False):
        data = dict(data)

        if not partial or "scholarship_program" in data:
            program = data.get("scholarship_program")
            if not isinstance(program, str) or not program.strip():
                raise ValueError("Scholarship program is required.")
            data["scholarship_program"] = program.strip()

        if not partial or "scholarship_year" in data:
            year = cls._as_int(data.get("scholarship_year"), "Scholarship year")
            if not 2000 <= year <= 2200:
                raise ValueError("Scholarship year must be between 2000 and 2200.")
            data["scholarship_year"] = year

        if not partial or "academic_average" in data:
            try:
                average = float(data["academic_average"])
            except (KeyError, TypeError, ValueError):
                raise ValueError("Academic average must be a number.")

            if not 0 <= average <= 100:
                raise ValueError("Academic average must be between 0 and 100.")
            data["academic_average"] = average

        if not partial or "monthly_income" in data:
            try:
                income = float(data["monthly_income"])
            except (KeyError, TypeError, ValueError):
                raise ValueError("Monthly income must be a number.")

            if income < 0:
                raise ValueError("Monthly income cannot be negative.")
            data["monthly_income"] = income

        for field in cls.COUNT_FIELDS:
            if field in data:
                value = cls._as_int(data[field], field)
                if value < 0:
                    raise ValueError(f"{field} cannot be negative.")
                data[field] = value

        if "household" in data and data["household"] < 1:
            raise ValueError("Household size must be at least 1.")

        household = data.get("household")
        if household is not None:
            members = (
                data.get("children_count", 0)
                + data.get("senior_count", 0)
                + data.get("pwd_count", 0)
            )
            if members > household:
                raise ValueError(
                    "Children, seniors, and PWD counts cannot exceed household size."
                )

        # The form may send a dependent count, but the database stores only
        # the boolean `dependent` column.
        if "dependents_count" in data:
            dependents = cls._as_int(
                data["dependents_count"], "Dependents count"
            )
            if dependents < 0:
                raise ValueError("Dependents count cannot be negative.")
            data["dependent"] = int(dependents > 0)
            data.pop("dependents_count", None)

        # Raw score and total items are temporary form inputs.
        # The database stores only the exam percentage in exam_score.
        has_raw = "exam_raw_score" in data
        has_total = "exam_total_items" in data

        if has_raw != has_total:
            raise ValueError(
                "Both raw exam score and total exam items are required."
            )

        if has_raw and has_total:
            raw = cls._as_int(data["exam_raw_score"], "Raw exam score")
            total = cls._as_int(data["exam_total_items"], "Total exam items")

            if total < 1:
                raise ValueError("Total exam items must be at least 1.")
            if raw < 0 or raw > total:
                raise ValueError(
                    "Raw exam score must be between 0 and total exam items."
                )

            data["exam_score"] = round((raw / total) * 100, 2)
            data["exam_passed"] = int(raw >= 0.8 * total)

            data.pop("exam_raw_score", None)
            data.pop("exam_total_items", None)

        elif data.get("exam_score") is not None:
            try:
                score = float(data["exam_score"])
            except (TypeError, ValueError):
                raise ValueError("Exam score must be a number.")

            if not 0 <= score <= 100:
                raise ValueError("Exam score must be between 0 and 100.")

            data["exam_score"] = score
            data["exam_passed"] = int(score >= 80)

        for field in cls.BOOLEAN_FIELDS:
            if field not in data:
                continue

            value = data[field]
            if isinstance(value, bool):
                data[field] = int(value)
            elif value in (0, 1, "0", "1"):
                data[field] = int(value)
            else:
                raise ValueError(f"{field} must be true or false.")

        if "status" in data:
            status = str(data["status"]).upper()
            if status not in cls.ALLOWED_STATUSES:
                raise ValueError("Invalid application status.")
            data["status"] = status

        # Drop transient fields and refuse unknown columns before SQL.
        data = {
            key: value
            for key, value in data.items()
            if key in cls.DB_COLUMNS
        }

        return data

    @classmethod
    def create(
        cls,
        applicant_id,
        scholarship_program,
        scholarship_year,
        academic_average,
        monthly_income,
        household,
        children_count=0,
        senior_count=0,
        pwd_count=0,
        mswdo_poverty_eligible=False,
        solo_parent=False,
        dependent=False,
        exam_score=None,
        exam_passed=False,
        exam_raw_score=None,
        exam_total_items=None,
        dependents_count=None,
        four_ps_beneficiary=False,
        spes_beneficiary=False,
        scholars_in_family=0,
        residency=None,
        previous_scholarship=False,
        status="DRAFT",
        submitted_at=None,
    ):
        data = {
            "applicant_id": applicant_id,
            "scholarship_program": scholarship_program,
            "scholarship_year": scholarship_year,
            "academic_average": academic_average,
            "monthly_income": monthly_income,
            "household": household,
            "children_count": children_count,
            "senior_count": senior_count,
            "pwd_count": pwd_count,
            "mswdo_poverty_eligible": mswdo_poverty_eligible,
            "solo_parent": solo_parent,
            "dependent": dependent,
            "exam_score": exam_score,
            "exam_passed": exam_passed,
            "four_ps_beneficiary": four_ps_beneficiary,
            "spes_beneficiary": spes_beneficiary,
            "scholars_in_family": scholars_in_family,
            "residency": residency,
            "previous_scholarship": previous_scholarship,
            "status": status,
            "submitted_at": submitted_at,
        }

        if dependents_count is not None:
            data["dependents_count"] = dependents_count

        if exam_raw_score is not None or exam_total_items is not None:
            data["exam_raw_score"] = exam_raw_score
            data["exam_total_items"] = exam_total_items

        data = cls._validate_application(data)

        columns = list(data.keys())
        placeholders = ", ".join(["%s"] * len(columns))
        column_sql = ", ".join(f"`{column}`" for column in columns)

        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute(
                f"INSERT INTO applications ({column_sql}) "
                f"VALUES ({placeholders})",
                tuple(data[column] for column in columns),
            )
            application_id = cursor.lastrowid
            connection.commit()
            return application_id
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def get_by_id(application_id, include_archived=False):
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            sql = "SELECT * FROM applications WHERE application_id = %s"
            params = [application_id]

            if not include_archived:
                sql += " AND is_archived = 0"

            cursor.execute(sql, tuple(params))
            return cursor.fetchone()
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def get_all(status=None, scholarship_year=None, include_archived=False):
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            sql = "SELECT * FROM applications WHERE 1 = 1"
            params = []

            if not include_archived:
                sql += " AND is_archived = 0"

            if status:
                sql += " AND status = %s"
                params.append(str(status).upper())

            if scholarship_year is not None:
                sql += " AND scholarship_year = %s"
                params.append(scholarship_year)

            sql += " ORDER BY created_at DESC, application_id DESC"
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def search(keyword, include_archived=False):
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            pattern = f"%{keyword}%"
            sql = """
                SELECT a.*, p.first_name, p.middle_name, p.last_name, p.suffix
                FROM applications AS a
                INNER JOIN applicants AS p
                    ON p.applicant_id = a.applicant_id
                WHERE (
                    CAST(a.application_id AS CHAR) LIKE %s
                    OR CAST(a.applicant_id AS CHAR) LIKE %s
                    OR a.scholarship_program LIKE %s
                    OR CAST(a.scholarship_year AS CHAR) LIKE %s
                    OR a.status LIKE %s
                    OR p.first_name LIKE %s
                    OR p.middle_name LIKE %s
                    OR p.last_name LIKE %s
                    OR CONCAT(p.first_name, ' ', p.last_name) LIKE %s
                )
            """
            params = [pattern] * 9

            if not include_archived:
                sql += " AND a.is_archived = 0 AND p.is_archived = 0"

            sql += " ORDER BY a.created_at DESC, a.application_id DESC"
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
        finally:
            cursor.close()
            connection.close()

    @classmethod
    def update(cls, application_id, **fields):
        if not fields:
            return False

        # Translate temporary form inputs to actual database columns.
        fields = dict(fields)

        if "dependents_count" in fields:
            try:
                count = int(fields.pop("dependents_count"))
            except (TypeError, ValueError):
                raise ValueError("Dependents count must be a whole number.")

            if count < 0:
                raise ValueError("Dependents count cannot be negative.")

            fields["dependent"] = int(count > 0)

        raw_present = "exam_raw_score" in fields
        total_present = "exam_total_items" in fields

        if raw_present != total_present:
            raise ValueError(
                "Both raw exam score and total exam items are required."
            )

        if raw_present:
            raw = cls._as_int(fields.pop("exam_raw_score"), "Raw exam score")
            total = cls._as_int(
                fields.pop("exam_total_items"), "Total exam items"
            )

            if total < 1 or raw < 0 or raw > total:
                raise ValueError("Invalid raw exam score or total exam items.")

            fields["exam_score"] = round((raw / total) * 100, 2)
            fields["exam_passed"] = int(raw >= 0.8 * total)

        unknown = set(fields) - cls.ALLOWED_UPDATE_FIELDS
        if unknown:
            raise ValueError(
                "Unsupported application field(s): "
                + ", ".join(sorted(unknown))
            )

        fields = cls._validate_application(fields, partial=True)

        connection = get_connection()
        cursor = connection.cursor()

        try:
            if "household" in fields or any(
                key in fields
                for key in ("children_count", "senior_count", "pwd_count")
            ):
                cursor.execute(
                    """
                    SELECT household, children_count, senior_count, pwd_count
                    FROM applications
                    WHERE application_id = %s AND is_archived = 0
                    """,
                    (application_id,),
                )
                current = cursor.fetchone()

                if current is None:
                    return False

                # This repository expects the default tuple cursor here.
                household = fields.get("household", current[0])
                children = fields.get("children_count", current[1])
                seniors = fields.get("senior_count", current[2])
                pwds = fields.get("pwd_count", current[3])

                if household < 1:
                    raise ValueError("Household size must be at least 1.")

                if children + seniors + pwds > household:
                    raise ValueError(
                        "Children, seniors, and PWD counts cannot exceed household size."
                    )

            columns = list(fields.keys())
            assignments = ", ".join(f"`{column}` = %s" for column in columns)
            values = [fields[column] for column in columns]
            values.append(application_id)

            cursor.execute(
                f"UPDATE applications SET {assignments} "
                "WHERE application_id = %s AND is_archived = 0",
                tuple(values),
            )
            changed = cursor.rowcount > 0
            connection.commit()
            return changed
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()
