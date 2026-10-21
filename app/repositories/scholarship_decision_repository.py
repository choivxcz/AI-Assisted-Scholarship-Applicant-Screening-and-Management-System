from database.connection import get_connection


class ScholarshipDecisionRepository:
    ALLOWED_DECISIONS = {"APPROVED", "REJECTED", "WAITLISTED"}

    @staticmethod
    def get_all():
        query = """
            SELECT
                d.decision_id,
                d.application_id,
                d.decision,
                d.reason,
                d.decided_at,
                a.applicant_id,
                a.scholarship_program,
                a.scholarship_year,
                a.status AS application_status,
                CONCAT_WS(
                    ' ', p.first_name, p.middle_name, p.last_name, p.suffix
                ) AS applicant_name,
                i.result AS interview_result
            FROM scholarship_decisions d
            INNER JOIN applications a ON a.application_id = d.application_id
            INNER JOIN applicants p ON p.applicant_id = a.applicant_id
            LEFT JOIN interviews i ON i.interview_id = (
                SELECT MAX(i2.interview_id)
                FROM interviews i2
                WHERE i2.application_id = a.application_id
            )
            WHERE a.is_archived = FALSE AND p.is_archived = FALSE
            ORDER BY d.decided_at DESC, d.decision_id DESC
        """
        connection = get_connection()
        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute(query)
                return cursor.fetchall()
        finally:
            connection.close()

    @staticmethod
    def save(application_id, decision, reason, decided_at):
        decision = str(decision).strip().upper()
        if decision not in ScholarshipDecisionRepository.ALLOWED_DECISIONS:
            raise ValueError(f"Invalid scholarship decision: {decision}")
        if not str(reason).strip():
            raise ValueError("Decision reason is required.")

        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO scholarship_decisions
                        (application_id, decision, reason, decided_at)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (application_id, decision, reason.strip(), decided_at),
                )
                decision_id = cursor.lastrowid
                cursor.execute(
                    """
                    UPDATE applications
                    SET status = %s
                    WHERE application_id = %s AND is_archived = FALSE
                    """,
                    (decision, application_id),
                )
            connection.commit()
            return decision_id
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
