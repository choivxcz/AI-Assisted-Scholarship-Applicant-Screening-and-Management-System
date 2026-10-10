
from database.connection import get_connection


class ApplicantRepository:
    ALLOWED_SEX = {
        "MALE",
        "FEMALE",
        "OTHER",
        "PREFER_NOT_TO_SAY",
    }

    ALLOWED_UPDATE_FIELDS = {
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
    }

    @staticmethod
    def _validate_required_text(value, field_name):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} is required.")

        return value.strip()

    @staticmethod
    def _validate_sex(sex):
        if sex is None:
            return None

        sex = sex.strip().upper()

        if sex not in ApplicantRepository.ALLOWED_SEX:
            raise ValueError(
                f"Invalid sex value: {sex}. "
                f"Allowed values: {', '.join(sorted(ApplicantRepository.ALLOWED_SEX))}"
            )

        return sex

    @staticmethod
    def create(
        first_name,
        last_name,
        barangay,
        middle_name=None,
        suffix=None,
        birth_date=None,
        sex=None,
        email=None,
        phone=None,
        house_no_street=None,
        municipality="Santa Cruz",
        province="Laguna",
    ):
        first_name = ApplicantRepository._validate_required_text(
            first_name, "First name"
        )
        last_name = ApplicantRepository._validate_required_text(
            last_name, "Last name"
        )
        barangay = ApplicantRepository._validate_required_text(
            barangay, "Barangay"
        )
        municipality = ApplicantRepository._validate_required_text(
            municipality, "Municipality"
        )
        province = ApplicantRepository._validate_required_text(
            province, "Province"
        )
        sex = ApplicantRepository._validate_sex(sex)

        query = """
            INSERT INTO applicants (
                first_name,
                middle_name,
                last_name,
                suffix,
                birth_date,
                sex,
                email,
                phone,
                house_no_street,
                barangay,
                municipality,
                province
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            first_name,
            middle_name.strip() if middle_name else None,
            last_name,
            suffix.strip() if suffix else None,
            birth_date,
            sex,
            email.strip() if email else None,
            phone.strip() if phone else None,
            house_no_street.strip() if house_no_street else None,
            barangay,
            municipality,
            province,
        )

        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(query, values)
                applicant_id = cursor.lastrowid

            connection.commit()
            return applicant_id

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    @staticmethod
    def get_all(include_archived=False):
        query = """
            SELECT
                applicant_id,
                first_name,
                middle_name,
                last_name,
                suffix,
                birth_date,
                sex,
                email,
                phone,
                house_no_street,
                barangay,
                municipality,
                province,
                is_archived,
                created_at,
                updated_at
            FROM applicants
        """

        if not include_archived:
            query += " WHERE is_archived = FALSE"

        query += " ORDER BY last_name, first_name, applicant_id"

        connection = get_connection()

        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute(query)
                return cursor.fetchall()
        finally:
            connection.close()

    @staticmethod
    def get_by_id(applicant_id, include_archived=False):
        query = """
            SELECT
                applicant_id,
                first_name,
                middle_name,
                last_name,
                suffix,
                birth_date,
                sex,
                email,
                phone,
                house_no_street,
                barangay,
                municipality,
                province,
                is_archived,
                created_at,
                updated_at
            FROM applicants
            WHERE applicant_id = %s
        """

        values = [applicant_id]

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
    def search(keyword, include_archived=False):
        if not isinstance(keyword, str) or not keyword.strip():
            return []

        term = f"%{keyword.strip()}%"

        # Intentionally search only the ID and name fields.
        # Phone, email, address, and barangay are excluded.
        query = """
            SELECT
                applicant_id,
                first_name,
                middle_name,
                last_name,
                suffix,
                birth_date,
                sex,
                email,
                phone,
                house_no_street,
                barangay,
                municipality,
                province,
                is_archived,
                created_at,
                updated_at
            FROM applicants
            WHERE (
                CAST(applicant_id AS CHAR) LIKE %s
                OR first_name LIKE %s
                OR middle_name LIKE %s
                OR last_name LIKE %s
                OR CONCAT_WS(
                    ' ',
                    first_name,
                    middle_name,
                    last_name,
                    suffix
                ) LIKE %s
            )
        """

        values = [term] * 5

        if not include_archived:
            query += " AND is_archived = FALSE"

        query += " ORDER BY last_name, first_name, applicant_id"

        connection = get_connection()

        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, tuple(values))
                return cursor.fetchall()
        finally:
            connection.close()

    @staticmethod
    def update(applicant_id, **fields):
        if not fields:
            return False

        invalid_fields = set(fields) - ApplicantRepository.ALLOWED_UPDATE_FIELDS

        if invalid_fields:
            raise ValueError(
                "Unsupported applicant field(s): "
                + ", ".join(sorted(invalid_fields))
            )

        fields = dict(fields)

        if "first_name" in fields:
            fields["first_name"] = ApplicantRepository._validate_required_text(
                fields["first_name"], "First name"
            )

        if "last_name" in fields:
            fields["last_name"] = ApplicantRepository._validate_required_text(
                fields["last_name"], "Last name"
            )

        if "barangay" in fields:
            fields["barangay"] = ApplicantRepository._validate_required_text(
                fields["barangay"], "Barangay"
            )

        if "municipality" in fields:
            fields["municipality"] = ApplicantRepository._validate_required_text(
                fields["municipality"], "Municipality"
            )

        if "province" in fields:
            fields["province"] = ApplicantRepository._validate_required_text(
                fields["province"], "Province"
            )

        if "sex" in fields:
            fields["sex"] = ApplicantRepository._validate_sex(fields["sex"])

        for field in ("middle_name", "suffix", "email", "phone", "house_no_street"):
            if field in fields and isinstance(fields[field], str):
                fields[field] = fields[field].strip() or None

        set_clause = ", ".join(f"`{field}` = %s" for field in fields)
        values = list(fields.values()) + [applicant_id]

        query = f"""
            UPDATE applicants
            SET {set_clause}
            WHERE applicant_id = %s
              AND is_archived = FALSE
        """

        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(query, tuple(values))
                updated = cursor.rowcount > 0

            connection.commit()
            return updated

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    @staticmethod
    def archive(applicant_id):
        """
        Archives the applicant and all associated applications.
        Both updates commit together or are rolled back together.
        """
        connection = get_connection()

        try:
            connection.start_transaction()

            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT applicant_id
                    FROM applicants
                    WHERE applicant_id = %s
                      AND is_archived = FALSE
                    FOR UPDATE
                    """,
                    (applicant_id,),
                )

                if cursor.fetchone() is None:
                    connection.rollback()
                    return False

                cursor.execute(
                    """
                    UPDATE applications
                    SET is_archived = TRUE
                    WHERE applicant_id = %s
                      AND is_archived = FALSE
                    """,
                    (applicant_id,),
                )

                cursor.execute(
                    """
                    UPDATE applicants
                    SET is_archived = TRUE
                    WHERE applicant_id = %s
                      AND is_archived = FALSE
                    """,
                    (applicant_id,),
                )

            connection.commit()
            return True

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()
