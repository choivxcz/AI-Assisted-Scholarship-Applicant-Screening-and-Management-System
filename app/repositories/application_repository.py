
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

    ALLOWED_UPDATE_FIELDS = {
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

    @staticmethod
    def _validate_application(data):
        if "scholarship_program" in data:
            program = data["scholarship_program"]

            if not isinstance(program, str) or not program.strip():
                raise ValueError("Scholarship program is required.")

            data["scholarship_program"] = program.strip()

        if "scholarship_year" in data:
            year = int(data["scholarship_year"])
            if not 2000 <= year <= 2200:
                raise ValueError("Scholarship year must be between 2000 and 2200.")
            data["scholarship_year"] = year

        if "academic_average" in data:
            average = float(data["academic_average"])
            if not 0 <= average <= 100:
                raise ValueError("Academic average must be between 0 and 100.")
            data["academic_average"] = average

        if "monthly_income" in data:
            income = float(data["monthly_income"])
            if income < 0:
                raise ValueError("Monthly income cannot be negative.")
            data["monthly_income"] = income

        if "exam_score" in data and data["exam_score"] is not None:
            score = float(data["exam_score"])
            if not 0 <= score <= 100:
                raise ValueError("Exam score must be between 0 and 100.")
            data["exam_score"] = score

        count_fields = (
            "household",
            "children_count",
            "senior_count",
            "pwd_count",
            "scholars_in_family",
        )

        for field in count_fields:
            if field in data:
                value = int(data[field])

                if value < 0:
                    raise ValueError(f"{field} cannot be negative.")

                data[field] = value

        if "household" in data and data["household"] < 1:
            raise ValueError("Household size must be at least 1.")

        if all(
            field in data
            for field in ("household", "children_count", "senior_count", "pwd_count")
        ):
            if (
                data["children_count"]
                + data["senior_count"]
                + data["pwd_count"]
                > data["household"]
            ):
                raise ValueError(
                    "Children, seniors, and PWD counts cannot exceed household size."
                )

        if "status" in data:
            status = str(data["status"]).strip().upper()

            if status not in ApplicationRepository.ALLOWED_STATUSES:
                raise ValueError(f"Invalid application status: {status}")

            data["status"] = status

        boolean_fields = (
            "mswdo_poverty_eligible",
            "solo_parent",
            "dependent",
            "exam_passed",
            "four_ps_beneficiary",
            "spes_beneficiary",
            "previous_scholarship",
        )

        for field in boolean_fields:
            if field in data:
                if data[field] not in (True, False, 0, 1):
                    raise ValueError(f"{field} must be true or false.")

                data[field] = bool(data[field])

        return data

    @staticmethod
    def create(
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
        four_ps_beneficiary=False,
        spes_beneficiary=False,
        scholars_in_family=0,
        residency=None,
        previous_scholarship=False,
        status="DRAFT",
        submitted_at=None,
    ):
        data = {
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

        data = ApplicationRepository._validate_application(data)

        columns = ["applicant_id", *data.keys()]
        placeholders = ", ".join(["%s"] * len(columns))
        column_sql = ", ".join(f"`{column}`" for column in columns)

        query = f"""
            INSERT INTO applications ({column_sql})
            VALUES ({placeholders})
        """

        values = [applicant_id, *data.values()]
        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(query, tuple(values))
                application_id = cursor.lastrowid

            connection.commit()
            return application_id

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    @staticmethod
    def get_by_id(application_id, include_archived=False):
        query = """
            SELECT *
            FROM applications
            WHERE application_id = %s
        """

        values = [application_id]

        if not include_archived:
            query += " AND is_archived = FALSE"

        query += " LIMIT 1"

        connection = get_connection()

        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, tuple(values))
                return cursor.fetchone()
        finally:
            connection.close()

    @staticmethod
    def get_all(
        status=None,
        scholarship_year=None,
        include_archived=False,
    ):
        query = """
            SELECT *
            FROM applications
            WHERE 1 = 1
        """
        values = []

        if not include_archived:
            query += " AND is_archived = FALSE"

        if status:
            status = str(status).strip().upper()

            if status not in ApplicationRepository.ALLOWED_STATUSES:
                raise ValueError(f"Invalid application status: {status}")

            query += " AND status = %s"
            values.append(status)

        if scholarship_year is not None:
            query += " AND scholarship_year = %s"
            values.append(scholarship_year)

        query += " ORDER BY created_at DESC, application_id DESC"

        connection = get_connection()

        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, tuple(values))
                return cursor.fetchall()
        finally:
            connection.close()

    @staticmethod
    def search(keyword, include_archived=False):
        if not isinstance(keyword, str) or not keyword.strip():
            return []

        term = f"%{keyword.strip()}%"

        query = """
            SELECT
                a.*,
                p.first_name,
                p.middle_name,
                p.last_name,
                p.suffix
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
                OR CONCAT_WS(
                    ' ',
                    p.first_name,
                    p.middle_name,
                    p.last_name,
                    p.suffix
                ) LIKE %s
            )
        """

        values = [term] * 9

        if not include_archived:
            query += """
                AND a.is_archived = FALSE
                AND p.is_archived = FALSE
            """

        query += " ORDER BY a.created_at DESC, a.application_id DESC"

        connection = get_connection()

        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, tuple(values))
                return cursor.fetchall()
        finally:
            connection.close()

    @staticmethod
    def update(application_id, **fields):
        if not fields:
            return False

        invalid_fields = set(fields) - ApplicationRepository.ALLOWED_UPDATE_FIELDS

        if invalid_fields:
            raise ValueError(
                "Unsupported application field(s): "
                + ", ".join(sorted(invalid_fields))
            )

        fields = ApplicationRepository._validate_application(dict(fields))

        connection = get_connection()

        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute(
                    """
                    SELECT
                        household,
                        children_count,
                        senior_count,
                        pwd_count
                    FROM applications
                    WHERE application_id = %s
                      AND is_archived = FALSE
                    LIMIT 1
                    """,
                    (application_id,),
                )
                current = cursor.fetchone()

                if current is None:
                    connection.rollback()
                    return False

                combined = {
                    "household": current["household"],
                    "children_count": current["children_count"],
                    "senior_count": current["senior_count"],
                    "pwd_count": current["pwd_count"],
                }
                combined.update({
                    field: fields[field]
                    for field in combined
                    if field in fields
                })

                if (
                    combined["household"] < 1
                    or combined["children_count"]
                    + combined["senior_count"]
                    + combined["pwd_count"]
                    > combined["household"]
                ):
                    raise ValueError(
                        "Household counts must be valid and cannot exceed household size."
                    )

            set_clause = ", ".join(
                f"`{field}` = %s" for field in fields
            )
            values = list(fields.values()) + [application_id]

            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    UPDATE applications
                    SET {set_clause}
                    WHERE application_id = %s
                      AND is_archived = FALSE
                    """,
                    tuple(values),
                )
                updated = cursor.rowcount > 0

            connection.commit()
            return updated

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()
