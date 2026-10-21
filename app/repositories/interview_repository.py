from database.connection import get_connection


# Base JOIN used by get_all(), get_upcoming(), and get_today()
_BASE_QUERY = """
    SELECT
        iv.interview_id,
        iv.application_id,
        iv.scheduled_at,
        iv.location,
        iv.status,
        iv.result,
        iv.remarks,
        iv.created_at,
        iv.updated_at,
        app.applicant_id,
        app.scholarship_program,
        app.scholarship_year,
        app.status AS application_status,
        CONCAT_WS(' ', p.first_name, p.middle_name, p.last_name, p.suffix) AS applicant_name,
        CONCAT('APP-', RIGHT(app.scholarship_year, 2), '-', LPAD(iv.application_id, 3, '0')) AS reference_no
    FROM interviews iv
    INNER JOIN applications app ON app.application_id = iv.application_id
    INNER JOIN applicants p ON p.applicant_id = app.applicant_id
    WHERE app.is_archived = FALSE AND p.is_archived = FALSE
"""


class InterviewRepository:
    ALLOWED_STATUSES = {"SCHEDULED", "COMPLETED", "RESCHEDULED", "CANCELLED", "NO_SHOW"}
    ALLOWED_RESULTS = {"PASSED", "FAILED", "FOR_FURTHER_REVIEW"}

    @staticmethod
    def get_all():
        """Returns a list of dicts with full interview data joined to applicants+applications.

        Fields returned per row:
            interview_id, application_id, applicant_id, applicant_name (full name),
            reference_no (formatted as APP-YY-NNN using application_id and scholarship_year),
            scheduled_at, location, status, result, remarks, scholarship_program,
            scholarship_year, application_status, created_at, updated_at
        Ordered by scheduled_at DESC.
        """
        query = _BASE_QUERY + " ORDER BY iv.scheduled_at DESC"
        connection = get_connection()
        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute(query)
                return cursor.fetchall()
        finally:
            connection.close()

    @staticmethod
    def get_by_id(interview_id):
        """Returns a single interview dict (joined to applicants+applications) or None."""
        query = _BASE_QUERY + " AND iv.interview_id = %s LIMIT 1"
        connection = get_connection()
        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, (interview_id,))
                return cursor.fetchone()
        finally:
            connection.close()

    @staticmethod
    def get_upcoming(limit=10):
        """Returns scheduled interviews where scheduled_at >= NOW(), ordered ASC.

        Args:
            limit: Maximum number of rows to return (default 10).
        """
        query = (
            _BASE_QUERY
            + " AND iv.status = 'SCHEDULED' AND iv.scheduled_at >= NOW()"
            + " ORDER BY iv.scheduled_at ASC"
            + f" LIMIT {int(limit)}"
        )
        connection = get_connection()
        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute(query)
                return cursor.fetchall()
        finally:
            connection.close()

    @staticmethod
    def get_today():
        """Returns interviews where DATE(scheduled_at) = CURDATE(), ordered by scheduled_at ASC."""
        query = (
            _BASE_QUERY
            + " AND DATE(iv.scheduled_at) = CURDATE()"
            + " ORDER BY iv.scheduled_at ASC"
        )
        connection = get_connection()
        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute(query)
                return cursor.fetchall()
        finally:
            connection.close()

    @staticmethod
    def create(application_id, scheduled_at, location=None, remarks=None):
        """Inserts a new interview with status='SCHEDULED' and result=NULL.

        Args:
            application_id: The related application's ID.
            scheduled_at:   datetime for the interview.
            location:       Optional venue string.
            remarks:        Optional remarks string.

        Returns:
            The newly created interview_id (int).
        """
        query = """
            INSERT INTO interviews (application_id, scheduled_at, location, remarks, status)
            VALUES (%s, %s, %s, %s, 'SCHEDULED')
        """
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, (application_id, scheduled_at, location, remarks))
                interview_id = cursor.lastrowid
            connection.commit()
            return interview_id
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def update_result(interview_id, result, remarks):
        """Sets status='COMPLETED', result=<result>, remarks=<remarks>.

        Args:
            interview_id: The interview to update.
            result:       Must be one of ALLOWED_RESULTS ('PASSED', 'FAILED', 'FOR_FURTHER_REVIEW').
            remarks:      Official remarks string.

        Returns:
            True if a row was updated, False otherwise.

        Raises:
            ValueError: If result is not in ALLOWED_RESULTS.
        """
        result = str(result).strip().upper()
        if result not in InterviewRepository.ALLOWED_RESULTS:
            raise ValueError(
                f"Invalid interview result '{result}'. "
                f"Allowed values: {', '.join(sorted(InterviewRepository.ALLOWED_RESULTS))}"
            )

        query = """
            UPDATE interviews
            SET status = 'COMPLETED', result = %s, remarks = %s
            WHERE interview_id = %s
        """
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, (result, remarks, interview_id))
                updated = cursor.rowcount > 0
            connection.commit()
            return updated
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def get_stats():
        """Returns a summary dict of interview counts.

        Returns:
            dict with keys:
                "scheduled"         - interviews with status='SCHEDULED'
                "completed"         - interviews with status='COMPLETED'
                "awaiting_decision" - completed interviews where the linked application
                                      status is still FOR_INTERVIEW or INTERVIEWED
                                      (not yet RECOMMENDED / APPROVED / REJECTED)
        """
        query = """
            SELECT
                SUM(iv.status = 'SCHEDULED') AS scheduled,
                SUM(iv.status = 'COMPLETED') AS completed,
                SUM(iv.status = 'COMPLETED' AND app.status IN ('FOR_INTERVIEW','INTERVIEWED')) AS awaiting_decision
            FROM interviews iv
            INNER JOIN applications app ON app.application_id = iv.application_id
            WHERE app.is_archived = FALSE
        """
        connection = get_connection()
        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute(query)
                row = cursor.fetchone() or {}
            return {
                "scheduled": int(row.get("scheduled") or 0),
                "completed": int(row.get("completed") or 0),
                "awaiting_decision": int(row.get("awaiting_decision") or 0),
            }
        finally:
            connection.close()
