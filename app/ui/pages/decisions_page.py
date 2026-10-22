from datetime import date, datetime

from PyQt6.QtCore import QDate, Qt, pyqtSignal
from PyQt6.QtGui import QFontDatabase
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from app.repositories.application_repository import ApplicationRepository
from app.repositories.applicant_repository import ApplicantRepository
from app.repositories.interview_repository import InterviewRepository
from app.repositories.scholarship_decision_repository import (
    ScholarshipDecisionRepository,
)

# Decision-makers offered in the form: "Name · Role"
DECISION_MAKERS = [
    "Mika Reyes · Authorized LYDO official",
    "Ana Lim · Authorized LYDO official",
]
DECISION_PLACEHOLDER = "Select: Approved / Rejected / Pending"
DECISION_CHOICES = ["Approved", "Rejected", "Waitlisted", "Pending"]

INTERVIEW_RESULT_LABELS = {
    "PASSED": "Recommended",
    "FAILED": "Not recommended",
    "FOR_FURTHER_REVIEW": "For deliberation",
}

# decision -> (background, text)
DECISION_STYLES = {
    "Pending": ("#dbeafe", "#2563eb"),
    "Approved": ("#bfdbfe", "#1d4ed8"),
    "Rejected": ("#fee2e2", "#dc2626"),
}

# Sample records from the mockup. Replace with repository data later.
SAMPLE_DECISIONS = [
    {"name": "Andrea Dela Cruz", "ref": "APP-26-003", "lyref": "LY-26-003",
     "program": "College Scholarship", "year": "2026–2027",
     "outcome": "Recommended", "decision": "Pending", "maker": "—",
     "date": None, "remarks": "Awaiting committee evaluation."},
    {"name": "Paolo Villanueva", "ref": "APP-26-008", "lyref": "LY-26-008",
     "program": "College Scholarship", "year": "2026–2027",
     "outcome": "For deliberation", "decision": "Pending", "maker": "—",
     "date": None, "remarks": "Confirm household declaration."},
    {"name": "Miguel Ramos", "ref": "APP-26-004", "lyref": "LY-26-004",
     "program": "College Scholarship", "year": "2026–2027",
     "outcome": "Recommended", "decision": "Approved", "maker": "Mika Reyes",
     "date": date(2026, 10, 15),
     "remarks": "Committee confirmed complete requirements."},
    {"name": "Joshua Navarro", "ref": "APP-26-006", "lyref": "LY-26-006",
     "program": "College Scholarship", "year": "2026–2027",
     "outcome": "Not recommended", "decision": "Rejected",
     "maker": "Mika Reyes", "date": date(2026, 10, 15),
     "remarks": "Residency requirement not substantiated."},
]

STYLE = """
QWidget { font-family: "%FONT%"; }
QWidget#dc_page { background: transparent; }

/* headings */
QLabel#dc_title { font-size: 22pt; font-weight: 600; color: #0f172a; }
QLabel#dc_muted { color: #64748b; font-size: 9pt; }
QLabel#dc_panel_title { font-size: 12pt; color: #0f172a; }

/* buttons */
QPushButton#dc_primary {
    background: #2563eb;
}
QPushButton#dc_primary:hover {
    background: #1d4ed8;
}
QPushButton#dc_primary:disabled {
    background: #93c5fd;
}

QPushButton#dc_secondary { background: #ffffff; border: 1px solid #dbe2ea;
    border-radius: 6px; padding: 9px 16px; font-weight: 600; font-size: 9pt;
    color: #0f172a; }
QPushButton#dc_secondary:hover { background: #f1f5f9; }
QPushButton#dc_secondary:disabled { color: #94a3b8; }
QPushButton#dc_row_action { background: #EFF6FF; border: 1px solid #DBEAFE;
    border-radius: 4px; padding: 4px 10px; font-weight: 600; font-size: 8pt;
    color: #1D4ED8; }
QPushButton#dc_row_action:hover { background: #DBEAFE; }
QPushButton#dc_row_action::menu-indicator { image: none; width: 0px; }
QMenu { background: #ffffff; border: 1px solid #e2e8f0; padding: 4px; }
QMenu::item { padding: 7px 22px; color: #334155; font-size: 9pt; }
QMenu::item:selected { background: #dbeafe; color: #0f172a; }

/* banner */
QFrame#dc_banner {
    background: #dbeafe;
}

QLabel#dc_banner_title {
    color: #1e40af;
}

QLabel#dc_banner_text {
    color: #475569;
}

/* stat cards */
QFrame#dc_stat_card, QFrame#dc_panel { background: #ffffff;
    border: 1px solid #e2e8f0; border-radius: 6px; }
QLabel#dc_stat_label { color: #0f172a; font-weight: 600; font-size: 9pt; }
QLabel#dc_stat_caption { color: #64748b; font-size: 8pt; }
QLabel#dc_num_pending { color: #b45309; font-size: 24pt; }
QLabel#dc_num_approved { color: #2563eb; font-size: 24pt; }
QLabel#dc_num_rejected { color: #b91c1c; font-size: 24pt; }

/* inputs */
QLineEdit#dc_input { background: #ffffff; border: 1px solid #dbe2ea;
    border-radius: 6px; padding: 0 12px; font-size: 9pt; color: #0f172a; }
QLineEdit#dc_input:focus { border: 1px solid #2563eb; }
QLineEdit#dc_input:disabled { background: #f1f5f9; color: #94a3b8; }
QComboBox#dc_combo, QDateEdit#dc_date { background: #ffffff;
    border: 1px solid #dbe2ea; border-radius: 6px; padding: 0 12px;
    font-size: 9pt; color: #0f172a; }
QComboBox#dc_combo:disabled, QDateEdit#dc_date:disabled {
    background: #f1f5f9; color: #94a3b8; }
QComboBox#dc_combo QAbstractItemView { background: #ffffff; color: #0f172a;
    border: 1px solid #dbe2ea; selection-background-color: #dbeafe;
    selection-color: #0f172a; outline: none; }
QLabel#dc_field_label { color: #334155; font-weight: 600; font-size: 8.5pt; }
QCheckBox#dc_confirm { color: #64748b; font-size: 8pt; }

/* table */
QFrame#dc_table_header { background: #f4f6f9; border: none;
    border-radius: 4px; }
QLabel#dc_th { color: #64748b; font-weight: 600; font-size: 7.5pt; }
QFrame#dc_row { background: transparent; border: none;
    border-bottom: 1px solid #e8edf2; }
QFrame#dc_row[last="true"] { border-bottom: none; }
QFrame#dc_row[selected="true"] { background: #dbeafe; }
QLabel#dc_cell_name { color: #0f172a; font-weight: 600; font-size: 9pt; }
QLabel#dc_cell_ref { color: #94a3b8; font-size: 7.5pt; }
QLabel#dc_cell_text { color: #334155; font-size: 9pt; }
QLabel#dc_cell_remarks { color: #64748b; font-size: 8.5pt; }
QLabel#dc_foot_note { color: #64748b; font-size: 8.5pt; }
QLabel#dc_footer { color: #64748b; font-size: 8pt; }

/* failed interviews */
QFrame#dc_failed_panel { background: #fff7f7; border: 1px solid #fecaca;
    border-radius: 6px; }
QFrame#dc_failed_header { background: #fee2e2; border: none;
    border-radius: 4px; }
QLabel#dc_failed_title { font-size: 12pt; color: #991b1b; }
QLabel#dc_failed_note { color: #b91c1c; font-size: 8.5pt; }
QLabel#dc_failed_count { background: #fee2e2; color: #b91c1c;
    border-radius: 3px; padding: 4px 9px; font-size: 8pt; font-weight: 600; }
QLabel#dc_failed_th { color: #b91c1c; font-weight: 600; font-size: 7.5pt; }
QLabel#dc_failed_outcome { color: #b91c1c; font-weight: 600; font-size: 8.5pt; }
QFrame#dc_failed_row { background: transparent; border: none;
    border-bottom: 1px solid #fee2e2; }
QFrame#dc_failed_row[last="true"] { border-bottom: none; }
"""


def _font_family():
    """Inter (as in the mockup) if installed, otherwise Segoe UI."""
    return "Inter" if "Inter" in QFontDatabase.families() else "Segoe UI"


def _fmt_date(value):
    if not value:
        return "—"
    return f"{value.day} {value.strftime('%b %Y')}"


def _fmt_date_long(value):
    return f"{value.day} {value.strftime('%B %Y')}"


def _fmt_interview_when(value):
    if not value:
        return "—"
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value
    return (
        f"{value.day} {value.strftime('%b %Y')} · "
        f"{value.strftime('%I:%M %p').lstrip('0')}"
    )


def _pill_css(background, color):
    return (
        f"background: {background}; color: {color}; border-radius: 3px;"
        "padding: 4px 9px; font-size: 8pt; font-weight: 600;"
    )


class ClickableRow(QFrame):
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class DecisionsPageMixin:
    # ------------------------------------------------------------------ UI
    def create_decisions_page(self):
        self._dc_records = []
        self._dc_failed_records = []
        self._dc_total_applications = 0
        self._applicants_for_decisions = []
        self._dc_selected = None

        page = QWidget()
        page.setObjectName("dc_page")
        page.setStyleSheet(STYLE.replace("%FONT%", _font_family()))

        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        layout.addLayout(self._dc_create_header())
        layout.addWidget(self._dc_create_banner())
        layout.addLayout(self._dc_create_stats())
        layout.addWidget(self._dc_create_table_panel())
        layout.addWidget(self._dc_create_failed_panel())
        self._dc_record_panel = self._dc_create_record_panel()
        layout.addWidget(self._dc_record_panel)
        layout.addLayout(self._dc_create_footer())
        layout.addStretch()
        return page

    def _dc_create_header(self):
        row = QHBoxLayout()

        text = QVBoxLayout()
        text.setSpacing(6)
        title = QLabel("Scholarship Decisions")
        title.setObjectName("dc_title")
        sub = QLabel("Record accountable, human-led final scholarship evaluations.")
        sub.setObjectName("dc_muted")
        text.addWidget(title)
        text.addWidget(sub)

        refresh = QPushButton("Refresh")
        refresh.setObjectName("dc_secondary")
        refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh.clicked.connect(self.refresh_decisions)

        record = QPushButton("Record official decision")
        record.setObjectName("dc_primary")
        record.setCursor(Qt.CursorShape.PointingHandCursor)
        record.clicked.connect(self._dc_start_recording)

        row.addLayout(text)
        row.addStretch()
        row.addWidget(refresh, alignment=Qt.AlignmentFlag.AlignTop)
        row.addSpacing(10)
        row.addWidget(record, alignment=Qt.AlignmentFlag.AlignTop)
        return row

    def _dc_create_banner(self):
        banner = QFrame()
        banner.setObjectName("dc_banner")
        layout = QVBoxLayout(banner)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(3)

        title = QLabel("Final authority rests with authorized LYDO officials.")
        title.setObjectName("dc_banner_title")
        text = QLabel(
            "AI screening never automatically awards or rejects a "
            "scholarship. Review the application, supporting records and "
            "human interview outcome before recording an official decision."
        )
        text.setObjectName("dc_banner_text")
        text.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(text)
        return banner

    def _dc_create_stats(self):
        row = QHBoxLayout()
        row.setSpacing(16)

        pending, self._dc_stat_pending = self._dc_stat_card(
            "Pending evaluation", "dc_num_pending")
        approved, self._dc_stat_approved = self._dc_stat_card(
            "Approved", "dc_num_approved")
        rejected, self._dc_stat_rejected = self._dc_stat_card(
            "Rejected", "dc_num_rejected")
        for card in (pending, approved, rejected):
            row.addWidget(card, 1)
        return row

    def _dc_stat_card(self, label_text, number_name):
        card = QFrame()
        card.setObjectName("dc_stat_card")
        card.setFixedHeight(78)
        row = QHBoxLayout(card)
        row.setContentsMargins(20, 0, 20, 0)
        row.setSpacing(14)

        number = QLabel("0")
        number.setObjectName(number_name)

        text = QVBoxLayout()
        text.setSpacing(2)
        label = QLabel(label_text)
        label.setObjectName("dc_stat_label")
        caption = QLabel("AY 2026–2027")
        caption.setObjectName("dc_stat_caption")
        text.addStretch()
        text.addWidget(label)
        text.addWidget(caption)
        text.addStretch()

        row.addWidget(number)
        row.addLayout(text)
        row.addStretch()
        return card, number

    def _dc_create_table_panel(self):
        panel = QFrame()
        panel.setObjectName("dc_panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(12)

        filters = QHBoxLayout()
        filters.setSpacing(10)

        self._dc_search = QLineEdit()
        self._dc_search.setObjectName("dc_input")
        self._dc_search.setPlaceholderText("Search applicant or application")
        self._dc_search.setFixedSize(320, 38)
        self._dc_search.textChanged.connect(
            lambda _text: self._dc_apply_filters())

        self._dc_filter = QComboBox()
        self._dc_filter.setObjectName("dc_combo")
        self._dc_filter.setFixedHeight(38)
        self._dc_filter.setMinimumWidth(150)
        self._dc_filter.addItems(["All decisions", "Pending", "Approved", "Rejected"])
        self._dc_filter.currentIndexChanged.connect(
            lambda _index: self._dc_apply_filters())

        self._dc_year = QComboBox()
        self._dc_year.setObjectName("dc_combo")
        self._dc_year.setFixedHeight(38)
        self._dc_year.setMinimumWidth(130)
        self._dc_year.currentIndexChanged.connect(
            lambda _index: self._dc_apply_filters())

        filters.addWidget(self._dc_search)
        filters.addStretch()
        filters.addWidget(self._dc_filter)
        filters.addWidget(self._dc_year)
        layout.addLayout(filters)

        header = QFrame()
        header.setObjectName("dc_table_header")
        header.setFixedHeight(40)
        header_row = QHBoxLayout(header)
        header_row.setContentsMargins(12, 0, 12, 0)
        header_row.setSpacing(0)
        for text, stretch in (
            ("APPLICANT / APPLICATION", 200), ("PROGRAM", 140),
            ("INTERVIEW OUTCOME", 130), ("OFFICIAL DECISION", 125),
            ("DECISION-MAKER", 110), ("DATE", 100),
            ("REMARKS / REASON", 220), ("SAVE DECISION", 160),
        ):
            label = QLabel(text)
            label.setObjectName("dc_th")
            header_row.addWidget(label, stretch)
        layout.addWidget(header)

        self._dc_rows = QVBoxLayout()
        self._dc_rows.setSpacing(0)
        layout.addLayout(self._dc_rows)

        self._dc_count_note = QLabel("")
        self._dc_count_note.setObjectName("dc_foot_note")
        layout.addWidget(self._dc_count_note)
        return panel

    def _dc_create_failed_panel(self):
        panel = QFrame()
        panel.setObjectName("dc_failed_panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(12)

        top = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(3)
        title = QLabel("Failed interviews")
        title.setObjectName("dc_failed_title")
        note = QLabel(
            "Applicants not recommended during the human interview. "
            "The interview remarks show why they failed."
        )
        note.setObjectName("dc_failed_note")
        note.setWordWrap(True)
        titles.addWidget(title)
        titles.addWidget(note)

        self._dc_failed_count = QLabel("0")
        self._dc_failed_count.setObjectName("dc_failed_count")
        top.addLayout(titles, 1)
        top.addWidget(
            self._dc_failed_count, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(top)

        header = QFrame()
        header.setObjectName("dc_failed_header")
        header.setFixedHeight(40)
        header_row = QHBoxLayout(header)
        header_row.setContentsMargins(12, 0, 12, 0)
        header_row.setSpacing(0)
        for text, stretch in (
            ("APPLICANT / APPLICATION", 200), ("PROGRAM", 150),
            ("INTERVIEW OUTCOME", 130), ("INTERVIEWER", 130),
            ("INTERVIEW DATE", 130), ("REASON / REMARKS", 300),
        ):
            label = QLabel(text)
            label.setObjectName("dc_failed_th")
            header_row.addWidget(label, stretch)
        layout.addWidget(header)

        self._dc_failed_rows = QVBoxLayout()
        self._dc_failed_rows.setSpacing(0)
        layout.addLayout(self._dc_failed_rows)
        return panel

    def _dc_create_record_panel(self):
        panel = QFrame()
        panel.setObjectName("dc_panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(12)

        top = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(3)
        self._dc_form_title = QLabel("Record official decision")
        self._dc_form_title.setObjectName("dc_panel_title")
        self._dc_form_meta = QLabel("")
        self._dc_form_meta.setObjectName("dc_muted")
        titles.addWidget(self._dc_form_title)
        titles.addWidget(self._dc_form_meta)

        self._dc_form_status = QLabel("")
        top.addLayout(titles)
        top.addStretch()
        top.addWidget(self._dc_form_status, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(top)

        fields = QHBoxLayout()
        fields.setSpacing(16)

        self._dc_decision_combo = QComboBox()
        self._dc_decision_combo.setObjectName("dc_combo")
        self._dc_decision_combo.setFixedHeight(38)
        self._dc_decision_combo.addItem(DECISION_PLACEHOLDER)
        self._dc_decision_combo.addItems(DECISION_CHOICES)

        self._dc_maker_combo = QComboBox()
        self._dc_maker_combo.setObjectName("dc_combo")
        self._dc_maker_combo.setFixedHeight(38)
        self._dc_maker_combo.addItems(DECISION_MAKERS)

        self._dc_date_edit = QDateEdit(QDate.currentDate())
        self._dc_date_edit.setObjectName("dc_date")
        self._dc_date_edit.setFixedHeight(38)
        self._dc_date_edit.setCalendarPopup(True)
        self._dc_date_edit.setDisplayFormat("d MMMM yyyy")

        fields.addLayout(self._dc_field("Official decision *", self._dc_decision_combo), 3)
        fields.addLayout(self._dc_field("Decision-maker *", self._dc_maker_combo), 3)
        fields.addLayout(self._dc_field("Decision date *", self._dc_date_edit), 2)
        layout.addLayout(fields)

        self._dc_remarks = QLineEdit()
        self._dc_remarks.setObjectName("dc_input")
        self._dc_remarks.setFixedHeight(38)
        self._dc_remarks.setPlaceholderText(
            "Enter the committee's evaluation and the reason for the decision")
        layout.addLayout(self._dc_field("Official remarks / reason *", self._dc_remarks))

        bottom = QHBoxLayout()
        bottom.setSpacing(10)
        self._dc_confirm = QCheckBox(
            "I confirm the application and human interview were reviewed. "
            "This is an official LYDO decision."
        )
        self._dc_confirm.setObjectName("dc_confirm")

        self._dc_cancel_button = QPushButton("Cancel")
        self._dc_cancel_button.setObjectName("dc_secondary")
        self._dc_cancel_button.setFixedHeight(38)
        self._dc_cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._dc_cancel_button.clicked.connect(self._dc_fill_form)

        self._dc_save_button = QPushButton("Save official decision")
        self._dc_save_button.setObjectName("dc_primary")
        self._dc_save_button.setFixedHeight(38)
        self._dc_save_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._dc_save_button.clicked.connect(self._dc_save_decision)

        bottom.addWidget(self._dc_confirm)
        bottom.addStretch()
        bottom.addWidget(self._dc_cancel_button)
        bottom.addWidget(self._dc_save_button)
        layout.addLayout(bottom)
        return panel

    @staticmethod
    def _dc_field(label_text, widget):
        column = QVBoxLayout()
        column.setSpacing(6)
        label = QLabel(label_text)
        label.setObjectName("dc_field_label")
        column.addWidget(label)
        column.addWidget(widget)
        return column

    def _dc_create_footer(self):
        row = QHBoxLayout()
        left = QLabel("Fictional records for demonstration only. "
                      "Authorized LYDO personnel access.")
        left.setObjectName("dc_footer")
        right = QLabel("Santa Cruz, Laguna · LYDO")
        right.setObjectName("dc_footer")
        row.addWidget(left)
        row.addStretch()
        row.addWidget(right)
        return row

    # ------------------------------------------------------------ Refresh
    def refresh_decisions(self):
        try:
            decisions = ScholarshipDecisionRepository.get_all()
            applications = ApplicationRepository.get_all()
            interviews = InterviewRepository.get_all()
            self._applicants_for_decisions = ApplicantRepository.get_all()
            self._dc_total_applications = len(applications)
            decided_by_application = {
                row["application_id"]: row for row in decisions
            }

            latest_interviews = {}
            for interview in interviews:
                application_id = interview.get("application_id")
                if application_id is None:
                    continue
                current = latest_interviews.get(application_id)
                if (
                    current is None
                    or (interview.get("interview_id") or 0)
                    > (current.get("interview_id") or 0)
                ):
                    latest_interviews[application_id] = interview

            records = []
            failed_records = []
            for application in applications:
                application_id = application.get("application_id")
                applicant_id = application.get("applicant_id")
                interview = latest_interviews.get(application_id)
                decision = decided_by_application.get(application_id)
                status = str(application.get("status") or "").strip().upper()

                interview_result = str(
                    (interview or {}).get("result")
                    or (decision or {}).get("interview_result")
                    or ""
                ).strip().upper()
                outcome = INTERVIEW_RESULT_LABELS.get(
                    interview_result, "For deliberation"
                )

                name = (
                    (interview or {}).get("applicant_name")
                    or application.get("applicant_name")
                )
                if not name:
                    applicant = next(
                        (
                            item for item in self._applicants_for_decisions
                            if item.get("applicant_id") == applicant_id
                        ),
                        None,
                    )
                    name = (
                        " ".join(
                            str(applicant.get(field) or "")
                            for field in ("first_name", "last_name")
                        ).strip()
                        if applicant else "—"
                    )

                year_value = str(
                    application.get("scholarship_year") or ""
                )
                ref = (
                    (interview or {}).get("reference_no")
                    or f"APP-{year_value[-2:]}-{int(application_id):03d}"
                )
                lyref = f"LY-{year_value[-2:]}-{int(applicant_id):03d}"
                program = application.get("scholarship_program") or "—"
                year = str(application.get("scholarship_year") or "—")

                if interview_result == "FAILED":
                    failed_records.append({
                        "application_id": application_id,
                        "name": name,
                        "ref": ref,
                        "program": program,
                        "year": year,
                        "interviewer": (
                            (interview or {}).get("location") or "—"
                        ),
                        "date": (interview or {}).get("scheduled_at"),
                        "remarks": (
                            (interview or {}).get("remarks")
                            or "No interview remarks recorded."
                        ),
                    })
                    continue

                if (
                    interview_result in {"PASSED", "FOR_FURTHER_REVIEW"}
                    or decision is not None
                    or status in {
                        "INTERVIEWED", "RECOMMENDED", "APPROVED",
                        "REJECTED", "WAITLISTED",
                    }
                ):
                    decision_text = (
                        decision["decision"].title()
                        if decision else "Pending"
                    )
                    records.append({
                        "application_id": application_id,
                        "name": name,
                        "ref": ref,
                        "lyref": lyref,
                        "program": program,
                        "year": year,
                        "outcome": outcome,
                        "decision": decision_text,
                        "maker": (
                            "Authorized LYDO official" if decision else "—"
                        ),
                        "date": (
                            decision.get("decided_at").date()
                            if decision and hasattr(
                                decision.get("decided_at"), "date"
                            )
                            else decision.get("decided_at") if decision
                            else None
                        ),
                        "remarks": decision["reason"] if decision
                        else "Awaiting committee evaluation.",
                    })

            self._dc_records = records
            self._dc_failed_records = failed_records
            counts = {"Pending": 0, "Approved": 0, "Rejected": 0}
            for record in records:
                if record["decision"] in counts:
                    counts[record["decision"]] += 1

            self._dc_stat_pending.setText(str(counts["Pending"]))
            self._dc_stat_approved.setText(str(counts["Approved"]))
            self._dc_stat_rejected.setText(str(counts["Rejected"]))

            self._dc_populate_years(records + failed_records)

            if not any(r["ref"] == self._dc_selected for r in records):
                pending = [r for r in records if r["decision"] == "Pending"]
                first = pending[0] if pending else (
                    records[0] if records else None)
                self._dc_selected = first["ref"] if first else None

            self._dc_render_rows()
            self._dc_render_failed_rows()
            self._dc_fill_form()
        except Exception as error:
            self.show_error("Decisions", error)

    def _dc_populate_years(self, records):
        years = sorted({r["year"] for r in records}, reverse=True)
        current = self._dc_year.currentText()
        self._dc_year.blockSignals(True)
        self._dc_year.clear()
        self._dc_year.addItems(years)
        index = self._dc_year.findText(current)
        self._dc_year.setCurrentIndex(index if index >= 0 else 0)
        self._dc_year.blockSignals(False)

    # -------------------------------------------------------------- Table
    def _dc_apply_filters(self):
        self._dc_render_rows()
        self._dc_render_failed_rows()

    def _dc_filtered(self):
        text = self._dc_search.text().strip().lower()
        decision = self._dc_filter.currentText()
        year = self._dc_year.currentText()

        rows = []
        for record in self._dc_records:
            if decision != "All decisions" and record["decision"] != decision:
                continue
            if year and record["year"] != year:
                continue
            if text and text not in record["name"].lower() \
                    and text not in record["ref"].lower():
                continue
            rows.append(record)
        return rows

    def _dc_filtered_failed(self):
        text = self._dc_search.text().strip().lower()
        year = self._dc_year.currentText()

        rows = []
        for record in self._dc_failed_records:
            if year and record["year"] != year:
                continue
            if text and text not in record["name"].lower() \
                    and text not in record["ref"].lower():
                continue
            rows.append(record)
        return rows

    def _dc_clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._dc_clear_layout(item.layout())

    def _dc_render_rows(self):
        self._dc_clear_layout(self._dc_rows)
        rows = self._dc_filtered()

        if not rows:
            empty = QLabel("No applications match the current filters.")
            empty.setObjectName("dc_muted")
            empty.setContentsMargins(12, 18, 12, 18)
            self._dc_rows.addWidget(empty)

        for index, record in enumerate(rows):
            frame = ClickableRow()
            frame.setObjectName("dc_row")
            frame.setProperty("last", index == len(rows) - 1)
            frame.setProperty("selected", record["ref"] == self._dc_selected)
            frame.setFixedHeight(64)
            frame.setCursor(Qt.CursorShape.PointingHandCursor)
            frame.clicked.connect(lambda ref=record["ref"]: self._dc_select(ref))

            row = QHBoxLayout(frame)
            row.setContentsMargins(12, 0, 12, 0)
            row.setSpacing(0)

            who = QWidget()
            who_layout = QVBoxLayout(who)
            who_layout.setContentsMargins(0, 0, 0, 0)
            who_layout.setSpacing(2)
            who_layout.addStretch()
            name = QLabel(record["name"])
            name.setObjectName("dc_cell_name")
            ref = QLabel(record["ref"])
            ref.setObjectName("dc_cell_ref")
            who_layout.addWidget(name)
            who_layout.addWidget(ref)
            who_layout.addStretch()

            program = QLabel(record["program"])
            program.setObjectName("dc_cell_text")
            outcome = QLabel(record["outcome"])
            outcome.setObjectName("dc_cell_text")
            maker = QLabel(record["maker"])
            maker.setObjectName("dc_cell_text")
            when = QLabel(_fmt_date(record["date"]))
            when.setObjectName("dc_cell_text")
            remarks = QLabel(record["remarks"])
            remarks.setObjectName("dc_cell_remarks")

            row.addWidget(who, 200)
            row.addWidget(program, 140)
            row.addWidget(outcome, 130)
            row.addWidget(self._dc_pill(record["decision"]), 125)
            row.addWidget(maker, 110)
            row.addWidget(when, 100)
            row.addWidget(remarks, 220)
            row.addWidget(self._dc_decision_actions(record), 160)
            self._dc_rows.addWidget(frame)

        failed = len(self._dc_failed_records)
        earlier = max(
            self._dc_total_applications
            - len(self._dc_records)
            - failed,
            0,
        )
        self._dc_count_note.setText(
            f"{len(rows)} application{'s' if len(rows) != 1 else ''} in final "
            f"evaluation · {failed} failed interview"
            f"{'s' if failed != 1 else ''} · {earlier} application"
            f"{'s' if earlier != 1 else ''} in earlier stages"
        )

    def _dc_render_failed_rows(self):
        self._dc_clear_layout(self._dc_failed_rows)
        rows = self._dc_filtered_failed()
        total = len(self._dc_failed_records)
        self._dc_failed_count.setText(str(total))

        if not rows:
            empty = QLabel(
                "No failed interviews match the current filters."
                if total else "No failed interviews recorded."
            )
            empty.setObjectName("dc_failed_note")
            empty.setContentsMargins(12, 14, 12, 14)
            self._dc_failed_rows.addWidget(empty)
            return

        for index, record in enumerate(rows):
            frame = QFrame()
            frame.setObjectName("dc_failed_row")
            frame.setProperty("last", index == len(rows) - 1)
            frame.setFixedHeight(64)

            row = QHBoxLayout(frame)
            row.setContentsMargins(12, 0, 12, 0)
            row.setSpacing(0)

            who = QWidget()
            who_layout = QVBoxLayout(who)
            who_layout.setContentsMargins(0, 0, 0, 0)
            who_layout.setSpacing(2)
            who_layout.addStretch()
            name = QLabel(record["name"])
            name.setObjectName("dc_cell_name")
            ref = QLabel(record["ref"])
            ref.setObjectName("dc_cell_ref")
            who_layout.addWidget(name)
            who_layout.addWidget(ref)
            who_layout.addStretch()

            program = QLabel(record["program"])
            program.setObjectName("dc_cell_text")
            outcome = QLabel("Not recommended")
            outcome.setObjectName("dc_failed_outcome")
            interviewer = QLabel(record["interviewer"])
            interviewer.setObjectName("dc_cell_text")
            when = QLabel(_fmt_interview_when(record["date"]))
            when.setObjectName("dc_cell_text")
            remarks = QLabel(record["remarks"])
            remarks.setObjectName("dc_cell_remarks")
            remarks.setToolTip(record["remarks"])

            row.addWidget(who, 200)
            row.addWidget(program, 150)
            row.addWidget(outcome, 130)
            row.addWidget(interviewer, 130)
            row.addWidget(when, 130)
            row.addWidget(remarks, 300)
            self._dc_failed_rows.addWidget(frame)

    def _dc_pill(self, text):
        background, color = DECISION_STYLES.get(text, ("#eef1f4", "#475569"))
        pill = QLabel(text)
        pill.setStyleSheet(_pill_css(background, color))
        wrapper = QWidget()
        wrapper.setStyleSheet("background: transparent;")
        row = QHBoxLayout(wrapper)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(pill, 0, Qt.AlignmentFlag.AlignVCenter)
        row.addStretch()
        return wrapper

    def _dc_decision_actions(self, record):
        button = QPushButton("Save decision  ▾")
        button.setObjectName("dc_row_action")
        button.setFixedHeight(28)
        button.setCursor(Qt.CursorShape.PointingHandCursor)

        menu = QMenu(button)
        for value in ("Approved", "Rejected", "Waitlisted"):
            action = menu.addAction(value)
            action.triggered.connect(
                lambda _checked=False, decision=value, rec=record:
                self._dc_open_decision_dialog(rec, decision)
            )
        button.setMenu(menu)

        wrapper = QWidget()
        wrapper.setStyleSheet("background: transparent;")
        row = QHBoxLayout(wrapper)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(button, 0, Qt.AlignmentFlag.AlignVCenter)
        row.addStretch()
        return wrapper

    def _dc_open_decision_dialog(self, record, initial_decision):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Save official decision · {record['name']}")
        dialog.setMinimumWidth(480)
        dialog.setStyleSheet(STYLE.replace("%FONT%", _font_family()))

        form = QFormLayout(dialog)
        form.setContentsMargins(20, 20, 20, 20)
        form.setSpacing(12)

        application = QLineEdit(
            f"{record['ref']} · {record['program']} · "
            f"Interview: {record['outcome']}"
        )
        application.setObjectName("dc_input")
        application.setReadOnly(True)
        application.setFixedHeight(38)

        decision_combo = QComboBox()
        decision_combo.setObjectName("dc_combo")
        decision_combo.setFixedHeight(38)
        decision_combo.addItems(DECISION_CHOICES[:3])
        decision_combo.setCurrentText(initial_decision)

        maker_combo = QComboBox()
        maker_combo.setObjectName("dc_combo")
        maker_combo.setFixedHeight(38)
        maker_combo.addItems(DECISION_MAKERS)
        if record["decision"] != "Pending":
            for index in range(maker_combo.count()):
                if maker_combo.itemText(index).startswith(record["maker"]):
                    maker_combo.setCurrentIndex(index)
                    break

        record_date = record.get("date")
        date_value = (
            QDate(record_date.year, record_date.month, record_date.day)
            if record_date else QDate.currentDate()
        )
        date_edit = QDateEdit(date_value)
        date_edit.setObjectName("dc_date")
        date_edit.setFixedHeight(38)
        date_edit.setCalendarPopup(True)
        date_edit.setDisplayFormat("d MMMM yyyy")

        reason = QLineEdit()
        reason.setObjectName("dc_input")
        reason.setFixedHeight(38)
        reason.setPlaceholderText("Enter the reason for this final decision")
        if record["decision"] != "Pending":
            reason.setText(record["remarks"])

        confirm = QCheckBox(
            "I confirm the application and human interview were reviewed. "
            "This is an official LYDO decision."
        )
        confirm.setObjectName("dc_confirm")

        form.addRow("Application", application)
        form.addRow("Final decision *", decision_combo)
        form.addRow("Decision-maker *", maker_combo)
        form.addRow("Decision date *", date_edit)
        form.addRow("Reason / remarks *", reason)
        form.addRow(confirm)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        save_button = buttons.button(QDialogButtonBox.StandardButton.Save)
        save_button.setText("Save official decision")
        save_button.setObjectName("dc_primary")
        save_button.setFixedHeight(38)
        save_button.setCursor(Qt.CursorShape.PointingHandCursor)

        cancel_button = buttons.button(
            QDialogButtonBox.StandardButton.Cancel
        )
        cancel_button.setObjectName("dc_secondary")
        cancel_button.setFixedHeight(38)
        cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        form.addRow(buttons)

        def save_decision():
            maker = maker_combo.currentText().split(" · ")[0].strip()
            remark_text = reason.text().strip()

            if not maker or not remark_text:
                QMessageBox.warning(
                    dialog,
                    "Official decision",
                    "Select a decision-maker and enter the official remarks "
                    "or reason before saving.",
                )
                return

            if not confirm.isChecked():
                QMessageBox.warning(
                    dialog,
                    "Official decision",
                    "Confirm that the application and the human interview "
                    "were reviewed before saving an official decision.",
                )
                return

            picked = date_edit.date()
            decided_on = date(
                picked.year(), picked.month(), picked.day()
            )

            try:
                ScholarshipDecisionRepository.save(
                    record["application_id"],
                    decision_combo.currentText(),
                    remark_text,
                    decided_on,
                )
            except Exception as error:
                QMessageBox.critical(
                    dialog,
                    "Save decision",
                    f"Could not save the official decision.\n\n{error}",
                )
                return

            dialog.accept()
            self.refresh_decisions()
            for method in ("refresh_dashboard", "refresh_applications"):
                if hasattr(self, method):
                    getattr(self, method)()

        buttons.accepted.connect(save_decision)
        buttons.rejected.connect(dialog.reject)
        dialog.exec()

    def _dc_select(self, ref):
        self._dc_selected = ref
        self._dc_render_rows()
        self._dc_fill_form()

    # --------------------------------------------------------------- Form
    def _dc_get_selected(self):
        for record in self._dc_records:
            if record["ref"] == self._dc_selected:
                return record
        return None

    def _dc_fill_form(self):
        record = self._dc_get_selected()
        enabled = record is not None
        for widget in (self._dc_decision_combo, self._dc_maker_combo,
                       self._dc_date_edit, self._dc_remarks, self._dc_confirm,
                       self._dc_cancel_button, self._dc_save_button):
            widget.setEnabled(enabled)

        self._dc_confirm.setChecked(False)

        if record is None:
            self._dc_form_title.setText("Record official decision")
            self._dc_form_meta.setText(
                "Select an application to record its official decision.")
            self._dc_form_status.hide()
            self._dc_decision_combo.setCurrentIndex(0)
            self._dc_remarks.clear()
            return

        self._dc_form_title.setText(
            f"Record official decision · {record['name']}")
        self._dc_form_meta.setText(
            f"{record['ref']} · {record['lyref']} · {record['program']} · "
            f"Interview: {record['outcome']}"
        )

        background, color = DECISION_STYLES.get(
            record["decision"], ("#eef1f4", "#475569"))
        self._dc_form_status.setText(record["decision"])
        self._dc_form_status.setStyleSheet(_pill_css(background, color))
        self._dc_form_status.show()

        decided = record["decision"] != "Pending"
        if decided:
            self._dc_decision_combo.setCurrentText(record["decision"])
            self._dc_remarks.setText(record["remarks"])
            for index in range(self._dc_maker_combo.count()):
                if self._dc_maker_combo.itemText(index).startswith(record["maker"]):
                    self._dc_maker_combo.setCurrentIndex(index)
                    break
            if record["date"]:
                self._dc_date_edit.setDate(QDate(
                    record["date"].year, record["date"].month,
                    record["date"].day))
        else:
            self._dc_decision_combo.setCurrentIndex(0)
            self._dc_remarks.clear()
            self._dc_maker_combo.setCurrentIndex(0)
            self._dc_date_edit.setDate(QDate.currentDate())

    def _dc_start_recording(self):
        record = self._dc_get_selected()
        if record is None or record["decision"] != "Pending":
            pending = [r for r in self._dc_records if r["decision"] == "Pending"]
            if pending:
                self._dc_select(pending[0]["ref"])
        self._dc_scroll_to(self._dc_record_panel)
        self._dc_decision_combo.setFocus()

    def _dc_scroll_to(self, widget):
        parent = widget.parentWidget()
        while parent is not None:
            if isinstance(parent, QScrollArea):
                parent.ensureWidgetVisible(widget)
                return
            parent = parent.parentWidget()

    def _dc_save_decision(self):
        record = self._dc_get_selected()
        if record is None:
            return

        decision = self._dc_decision_combo.currentText()
        maker = self._dc_maker_combo.currentText().split(" · ")[0].strip()
        remarks = self._dc_remarks.text().strip()

        if decision == DECISION_PLACEHOLDER or not maker or not remarks:
            QMessageBox.warning(
                self,
                "Official decision",
                "Select an official decision, a decision-maker, and enter "
                "the official remarks or reason before saving.",
            )
            return

        if not self._dc_confirm.isChecked():
            QMessageBox.warning(
                self,
                "Official decision",
                "Confirm that the application and the human interview were "
                "reviewed before saving an official decision.",
            )
            return

        picked = self._dc_date_edit.date()
        decided_on = datetime(picked.year(), picked.month(), picked.day()).date()

        if decision == "Pending":
            QMessageBox.warning(
                self, "Official decision",
                "Choose Approved, Rejected, or Waitlisted to save a final decision.",
            )
            return

        try:
            ScholarshipDecisionRepository.save(
                record["application_id"], decision, remarks, decided_on
            )
        except Exception as error:
            self.show_error("Save decision", error)
            return
        self.refresh_decisions()