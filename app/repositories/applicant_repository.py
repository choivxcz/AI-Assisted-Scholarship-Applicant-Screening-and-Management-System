import re
from datetime import date, datetime

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
        if not isinstance(sex, str) or not sex.strip():
            raise ValueError("Sex is required.")

        sex = sex.strip().upper()
        if sex not in ApplicantRepository.ALLOWED_SEX:
            raise ValueError(
                f"Invalid sex value: {sex}. Allowed values: "
                f"{', '.join(sorted(ApplicantRepository.ALLOWED_SEX))}"
            )
        return sex

    @staticmethod
    def _validate_email(email):
        if not isinstance(email, str) or not email.strip():
            raise ValueError("Email is required.")

        email = email.strip()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise ValueError("Please enter a valid email address.")
        return email

    @staticmethod
    def _validate_phone(phone):
        if not isinstance(phone, str) or not phone.strip():
            raise ValueError("Phone number is required.")

        phone = phone.strip()
        digits = re.sub(r"\D", "", phone)
        if not 7 <= len(digits) <= 15:
            raise ValueError("Phone number must contain 7 to 15 digits.")
        return phone

    @staticmethod
    def _validate_birth_date(birth_date):
        if birth_date is None or not str(birth_date).strip():
            raise ValueError("Birth date is required.")

        if isinstance(birth_date, datetime):
            birth_date = birth_date.date()

        if isinstance(birth_date, date):
            parsed = birth_date
        else:
            try:
                parsed = date.fromisoformat(str(birth_date).strip())
            except ValueError as exc:
                raise ValueError(
                    "Birth date must use YYYY-MM-DD format."
                ) from exc

        if parsed > date.today():
            raise ValueError("Birth date cannot be in the future.")

        if parsed < date(1900, 1, 1):
            raise ValueError(
                "Birth date must be on or after 1900-01-01."
            )

        return parsed.isoformat()

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
        birth_date = ApplicantRepository._validate_birth_date(birth_date)
        sex = ApplicantRepository._validate_sex(sex)
        email = ApplicantRepository._validate_email(email)
        phone = ApplicantRepository._validate_phone(phone)
        house_no_street = ApplicantRepository._validate_required_text(
            house_no_street, "House number/street"
        )

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
            email,
            phone,
            house_no_street,
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

        # Search the ID and name fields only.
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

        required_text_fields = {
            "first_name": "First name",
            "last_name": "Last name",
            "barangay": "Barangay",
            "municipality": "Municipality",
            "province": "Province",
            "house_no_street": "House number/street",
        }

        for field, label in required_text_fields.items():
            if field in fields:
                fields[field] = ApplicantRepository._validate_required_text(
                    fields[field], label
                )

        if "sex" in fields:
            fields["sex"] = ApplicantRepository._validate_sex(fields["sex"])

        if "birth_date" in fields:
            fields["birth_date"] = ApplicantRepository._validate_birth_date(
                fields["birth_date"]
            )

        if "email" in fields:
            fields["email"] = ApplicantRepository._validate_email(
                fields["email"]
            )

        if "phone" in fields:
            fields["phone"] = ApplicantRepository._validate_phone(
                fields["phone"]
            )

        for field in ("middle_name", "suffix"):
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