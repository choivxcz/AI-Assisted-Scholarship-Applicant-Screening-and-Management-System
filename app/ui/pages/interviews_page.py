from datetime import datetime, timedelta

from PyQt6.QtCore import QDate, QTime, Qt, pyqtSignal
from PyQt6.QtGui import QFontDatabase
from PyQt6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

# Signed-in user shown in the top bar: (name, role, initials)
CURRENT_USER = ("Mika Reyes", "LYDO Administrator", "MR")
SLOT_MINUTES = 30

RESULT_CHOICES = ["Recommended", "For deliberation", "Not recommended"]
RESULT_PLACEHOLDER = "Select result"

# status / result -> (background, text)
STATUS_STYLES = {
    "Scheduled": ("#DBEAFE", "#1D4ED8"),
    "Completed": ("#BFDBFE", "#1E40AF"),
}

RESULT_STYLES = {
    "Not recorded": ("#EFF6FF", "#475569"),
    "Recommended": ("#DBEAFE", "#1D4ED8"),
    "For deliberation": ("#BFDBFE", "#1E40AF"),
    "Not recommended": ("#FEE2E2", "#B91C1C"),
}

SAMPLE_INTERVIEWS = [
    {"name": "Gabriel Santos", "ref": "APP-26-002",
     "when": datetime(2026, 10, 19, 9, 0), "interviewer": "Mika Reyes",
     "status": "Scheduled", "result": "Not recorded",
     "remarks": "LYDO office · Confirmed"},
    {"name": "Camille Reyes", "ref": "APP-26-007",
     "when": datetime(2026, 10, 19, 9, 30), "interviewer": "Ana Lim",
     "status": "Scheduled", "result": "Not recorded",
     "remarks": "LYDO office · Confirmed"},
    {"name": "Andrea Dela Cruz", "ref": "APP-26-003",
     "when": datetime(2026, 10, 15, 10, 0), "interviewer": "Mika Reyes",
     "status": "Completed", "result": "Recommended",
     "remarks": "Academic and residency records verified."},
    {"name": "Paolo Villanueva", "ref": "APP-26-008",
     "when": datetime(2026, 10, 15, 10, 30), "interviewer": "Ana Lim",
     "status": "Completed", "result": "For deliberation",
     "remarks": "Clarify household declaration."},
    {"name": "Miguel Ramos", "ref": "APP-26-004",
     "when": datetime(2026, 10, 14, 9, 0), "interviewer": "Mika Reyes",
     "status": "Completed", "result": "Recommended",
     "remarks": "Records complete; endorsed to committee."},
    {"name": "Joshua Navarro", "ref": "APP-26-006",
     "when": datetime(2026, 10, 14, 9, 30), "interviewer": "Ana Lim",
     "status": "Completed", "result": "Not recommended",
     "remarks": "Residency requirement not substantiated."},
]

STYLE = """
QWidget { font-family: "%FONT%"; }
QWidget#iv_page { background: #f7f9fc; }

/* top bar */
QFrame#iv_topbar { background: #ffffff; border: none;
    border-bottom: 1px solid #e2e8f0; }
QLabel#iv_crumb { color: #64748b; font-size: 9pt; }
QLabel#iv_crumb_current { color: #0f172a; font-weight: 600; font-size: 9pt; }
QLabel#iv_chip { background: #EFF6FF; color: #475569; font-size: 8pt;
    padding: 5px 9px; border-radius: 4px; }
QLabel#iv_top_text { color: #64748b; font-size: 9pt; }
QLabel#iv_avatar { background: #DBEAFE; color: #2457A7; font-weight: 600;
    font-size: 8pt; border-radius: 16px; }
QLabel#iv_user_name { color: #0f172a; font-weight: 600; font-size: 9pt; }
QLabel#iv_user_role { color: #64748b; font-size: 8pt; }

/* headings */
QLabel#iv_title { font-size: 22pt; font-weight: 600; color: #0f172a; }
QLabel#iv_muted { color: #64748b; font-size: 9pt; }
QLabel#iv_panel_title { font-size: 12pt; color: #0f172a; }

/* buttons */
QPushButton#iv_primary { background: #2457A7; border: none;
    border-radius: 6px; padding: 10px 18px; font-weight: 600; font-size: 9pt;
    color: #ffffff; }
QPushButton#iv_primary:hover { background: #1D4485; }
QPushButton#iv_primary:disabled { background: #93B4E8; }
QPushButton#iv_secondary { background: #ffffff; border: 1px solid #dbe2ea;
    border-radius: 6px; padding: 9px 16px; font-weight: 600; font-size: 9pt;
    color: #0f172a; }
QPushButton#iv_secondary:hover { background: #f1f5f9; }

/* summary cards */
QFrame#iv_next_card { background: #173B70; border: none; border-radius: 6px; }
QFrame#iv_next_card QLabel { background: transparent; }
QFrame#iv_date_box { background: #2457A7; border: none; border-radius: 6px; }
QLabel#iv_date_month { color: #DBEAFE; font-size: 8pt; font-weight: 600; }
QLabel#iv_date_day { color: #ffffff; font-size: 20pt; font-weight: 600; }
QLabel#iv_next_title { color: #ffffff; font-size: 11pt; font-weight: 600; }
QLabel#iv_next_meta { color: #DBEAFE; font-size: 8.5pt; }
QFrame#iv_stat_card, QFrame#iv_panel { background: #ffffff;
    border: 1px solid #e2e8f0; border-radius: 6px; }
QLabel#iv_stat_label { color: #64748b; font-size: 9pt; }
QLabel#iv_stat_value { font-size: 24pt; font-weight: 600; color: #0f172a; }

/* tabs */
QPushButton#iv_tab { background: transparent; border: none;
    border-bottom: 2px solid transparent; color: #64748b; font-size: 9pt;
    padding: 10px 2px; }
QPushButton#iv_tab:checked { color: #2457A7; font-weight: 600;
    border-bottom: 2px solid #2457A7; }

/* inputs */
QLineEdit#iv_input { background: #ffffff; border: 1px solid #dbe2ea;
    border-radius: 6px; padding: 0 12px; font-size: 9pt; color: #0f172a; }
QLineEdit#iv_input:focus { border: 1px solid #2457A7; }
QLineEdit#iv_input:disabled { background: #f1f5f9; color: #94a3b8; }
QComboBox#iv_combo { background: #ffffff; border: 1px solid #dbe2ea;
    border-radius: 6px; padding: 0 12px; font-size: 9pt; color: #0f172a; }
QComboBox#iv_combo:disabled { background: #f1f5f9; color: #94a3b8; }
QComboBox#iv_combo QAbstractItemView { background: #ffffff; color: #0f172a;
    border: 1px solid #dbe2ea; selection-background-color: #DBEAFE;
    selection-color: #0f172a; outline: none; }
QLabel#iv_field_label { color: #334155; font-weight: 600; font-size: 8.5pt; }

/* table */
QFrame#iv_table_header { background: #f4f6f9; border: none;
    border-radius: 4px; }
QLabel#iv_th { color: #64748b; font-weight: 600; font-size: 7.5pt; }
QFrame#iv_row { background: transparent; border: none;
    border-bottom: 1px solid #e8edf2; }
QFrame#iv_row[last="true"] { border-bottom: none; }
QFrame#iv_row[selected="true"] { background: #DBEAFE; }
QLabel#iv_cell_name { color: #0f172a; font-weight: 600; font-size: 9pt; }
QLabel#iv_cell_ref { color: #94a3b8; font-size: 7.5pt; }
QLabel#iv_cell_text { color: #334155; font-size: 9pt; }
QLabel#iv_cell_remarks { color: #64748b; font-size: 8.5pt; }
QLabel#iv_foot_note { color: #64748b; font-size: 8.5pt; }

/* result panel */
QFrame#iv_note { background: #EFF6FF; border: none; border-radius: 4px; }
QLabel#iv_note_text { color: #64748b; font-size: 8.5pt; }
QLabel#iv_footer { color: #64748b; font-size: 8pt; }
"""


def _font_family():
    """Inter (as in the mockup) if installed, otherwise Segoe UI."""
    return "Inter" if "Inter" in QFontDatabase.families() else "Segoe UI"


def _fmt_time(value):
    return value.strftime("%I:%M %p").lstrip("0")


def _fmt_short(value):
    return f"{value.day} {value.strftime('%b')} · {_fmt_time(value)}"


def _fmt_long(value):
    return f"{value.day} {value.strftime('%B %Y')}, {_fmt_time(value)}"


def _month_label(value):
    return value.strftime("%B %Y")


def _pill_css(background, color):
    return (
        f"background: {background}; color: {color}; border-radius: 3px;"
        "padding: 4px 9px; font-size: 8pt; font-weight: 600;"
    )


class ClickableFrame(QFrame):
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class InterviewsPageMixin:
    # ------------------------------------------------------------------ UI
    def create_interviews_page(self, with_topbar=False):
        # with_topbar=False when the main window already draws its own top bar.
        self._iv_records = [dict(item) for item in SAMPLE_INTERVIEWS]
        self._iv_selected = None
        self._iv_tab = "all"

        page = QWidget()
        page.setObjectName("iv_page")
        style = STYLE.replace("%FONT%", _font_family())
        if not with_topbar:
            # Embedded in the main window: it already provides the page
            # padding and background, so don't add a second set.
            style += "\nQWidget#iv_page { background: transparent; }\n"
        page.setStyleSheet(style)

        root = QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        if with_topbar:
            root.addWidget(self._iv_create_topbar())

        body = QWidget()
        layout = QVBoxLayout(body)
        if with_topbar:
            layout.setContentsMargins(32, 32, 32, 20)
        else:
            layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        layout.addLayout(self._iv_create_header())
        layout.addLayout(self._iv_create_summary())
        layout.addLayout(self._iv_create_tabs())
        layout.addWidget(self._iv_create_table_panel())
        layout.addWidget(self._iv_create_result_panel())
        layout.addLayout(self._iv_create_footer())
        layout.addStretch()

        root.addWidget(body, 1)
        return page

    def _iv_create_topbar(self):
        bar = QFrame()
        bar.setObjectName("iv_topbar")
        bar.setFixedHeight(64)
        row = QHBoxLayout(bar)
        row.setContentsMargins(32, 0, 32, 0)
        row.setSpacing(10)

        v_center = Qt.AlignmentFlag.AlignVCenter

        crumb = QLabel("Scholarships")
        crumb.setObjectName("iv_crumb")
        slash = QLabel("/")
        slash.setObjectName("iv_crumb")
        current = QLabel("Interviews")
        current.setObjectName("iv_crumb_current")

        chip = QLabel("Demonstration data")
        chip.setObjectName("iv_chip")
        year = QLabel("AY 2026–2027")
        year.setObjectName("iv_top_text")

        name, role, initials = CURRENT_USER
        avatar = QLabel(initials)
        avatar.setObjectName("iv_avatar")
        avatar.setFixedSize(32, 32)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        user_box = QWidget()
        user = QVBoxLayout(user_box)
        user.setContentsMargins(0, 0, 0, 0)
        user.setSpacing(0)
        name_label = QLabel(name)
        name_label.setObjectName("iv_user_name")
        role_label = QLabel(role)
        role_label.setObjectName("iv_user_role")
        user.addWidget(name_label)
        user.addWidget(role_label)

        row.addWidget(crumb, 0, v_center)
        row.addWidget(slash, 0, v_center)
        row.addWidget(current, 0, v_center)
        row.addStretch()
        row.addWidget(chip, 0, v_center)
        row.addWidget(year, 0, v_center)
        row.addSpacing(6)
        row.addWidget(avatar, 0, v_center)
        row.addWidget(user_box, 0, v_center)
        return bar

    def _iv_create_header(self):
        row = QHBoxLayout()

        text = QVBoxLayout()
        text.setSpacing(6)
        title = QLabel("Interviews")
        title.setObjectName("iv_title")
        sub = QLabel(
            "Schedule human interviews and keep a clear record of "
            "official evaluations."
        )
        sub.setObjectName("iv_muted")
        text.addWidget(title)
        text.addWidget(sub)

        refresh = QPushButton("Refresh")
        refresh.setObjectName("iv_secondary")
        refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh.clicked.connect(self.refresh_interviews)

        schedule = QPushButton("Schedule interview")
        schedule.setObjectName("iv_primary")
        schedule.setCursor(Qt.CursorShape.PointingHandCursor)
        schedule.clicked.connect(self.open_schedule_interview)

        row.addLayout(text)
        row.addStretch()
        row.addWidget(refresh, alignment=Qt.AlignmentFlag.AlignTop)
        row.addSpacing(10)
        row.addWidget(schedule, alignment=Qt.AlignmentFlag.AlignTop)
        return row

    def _iv_create_summary(self):
        row = QHBoxLayout()
        row.setSpacing(16)

        # Next interview day (dark card)
        card = QFrame()
        card.setObjectName("iv_next_card")
        card.setFixedHeight(108)
        card_row = QHBoxLayout(card)
        card_row.setContentsMargins(20, 16, 20, 16)
        card_row.setSpacing(16)

        date_box = QFrame()
        date_box.setObjectName("iv_date_box")
        date_box.setFixedSize(56, 64)
        date_layout = QVBoxLayout(date_box)
        date_layout.setContentsMargins(0, 0, 0, 0)
        date_layout.setSpacing(0)
        date_layout.addStretch()
        self._iv_date_month = QLabel("—")
        self._iv_date_month.setObjectName("iv_date_month")
        self._iv_date_month.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._iv_date_day = QLabel("—")
        self._iv_date_day.setObjectName("iv_date_day")
        self._iv_date_day.setAlignment(Qt.AlignmentFlag.AlignCenter)
        date_layout.addWidget(self._iv_date_month)
        date_layout.addWidget(self._iv_date_day)
        date_layout.addStretch()

        text = QVBoxLayout()
        text.setSpacing(3)
        title = QLabel("Next interview day")
        title.setObjectName("iv_next_title")
        self._iv_next_line1 = QLabel("")
        self._iv_next_line1.setObjectName("iv_next_meta")
        self._iv_next_line2 = QLabel("")
        self._iv_next_line2.setObjectName("iv_next_meta")
        text.addStretch()
        text.addWidget(title)
        text.addWidget(self._iv_next_line1)
        text.addWidget(self._iv_next_line2)
        text.addStretch()

        card_row.addWidget(date_box)
        card_row.addLayout(text, 1)
        row.addWidget(card, 8)

        scheduled, self._iv_stat_scheduled = self._iv_stat_card(
            "Scheduled", "Ready for human interview")
        completed, self._iv_stat_completed = self._iv_stat_card(
            "Completed", "Official results recorded")
        awaiting, self._iv_stat_awaiting = self._iv_stat_card(
            "Awaiting decision", "Interviewed · committee review")
        for stat in (scheduled, completed, awaiting):
            row.addWidget(stat, 5)
        return row

    def _iv_stat_card(self, label_text, caption_text):
        card = QFrame()
        card.setObjectName("iv_stat_card")
        card.setFixedHeight(108)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(0)

        label = QLabel(label_text)
        label.setObjectName("iv_stat_label")
        value = QLabel("—")
        value.setObjectName("iv_stat_value")
        caption = QLabel(caption_text)
        caption.setObjectName("iv_muted")

        layout.addWidget(label)
        layout.addWidget(value)
        layout.addStretch()
        layout.addWidget(caption)
        return card, value

    def _iv_create_tabs(self):
        row = QHBoxLayout()
        row.setSpacing(22)

        self._iv_tab_group = QButtonGroup(self)
        self._iv_tab_group.setExclusive(True)
        self._iv_tab_buttons = {}
        for key in ("all", "upcoming", "completed"):
            button = QPushButton("")
            button.setObjectName("iv_tab")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda _checked, k=key: self._iv_set_tab(k))
            self._iv_tab_group.addButton(button)
            self._iv_tab_buttons[key] = button
            row.addWidget(button)
        self._iv_tab_buttons["all"].setChecked(True)
        row.addStretch()
        return row

    def _iv_create_table_panel(self):
        panel = QFrame()
        panel.setObjectName("iv_panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(12)

        filters = QHBoxLayout()
        filters.setSpacing(10)

        self._iv_search = QLineEdit()
        self._iv_search.setObjectName("iv_input")
        self._iv_search.setPlaceholderText("Search applicant or application")
        self._iv_search.setFixedSize(320, 38)
        self._iv_search.textChanged.connect(lambda _text: self._iv_render_rows())

        self._iv_interviewer = QComboBox()
        self._iv_interviewer.setObjectName("iv_combo")
        self._iv_interviewer.setFixedHeight(38)
        self._iv_interviewer.setMinimumWidth(170)
        self._iv_interviewer.currentIndexChanged.connect(
            lambda _index: self._iv_render_rows())

        self._iv_month_combo = QComboBox()
        self._iv_month_combo.setObjectName("iv_combo")
        self._iv_month_combo.setFixedHeight(38)
        self._iv_month_combo.setMinimumWidth(150)
        self._iv_month_combo.currentIndexChanged.connect(
            lambda _index: self._iv_render_rows())

        filters.addWidget(self._iv_search)
        filters.addStretch()
        filters.addWidget(self._iv_interviewer)
        filters.addWidget(self._iv_month_combo)
        layout.addLayout(filters)

        header = QFrame()
        header.setObjectName("iv_table_header")
        header.setFixedHeight(40)
        header_row = QHBoxLayout(header)
        header_row.setContentsMargins(12, 0, 12, 0)
        header_row.setSpacing(0)
        for text, stretch in (
            ("APPLICANT / APPLICATION", 220), ("DATE / TIME · 2026", 160),
            ("INTERVIEWER", 140), ("INTERVIEW STATUS", 140),
            ("RESULT", 150), ("OFFICIAL REMARKS", 320),
        ):
            label = QLabel(text)
            label.setObjectName("iv_th")
            header_row.addWidget(label, stretch)
        layout.addWidget(header)

        self._iv_rows = QVBoxLayout()
        self._iv_rows.setSpacing(0)
        layout.addLayout(self._iv_rows)

        self._iv_count_note = QLabel("")
        self._iv_count_note.setObjectName("iv_foot_note")
        layout.addWidget(self._iv_count_note)
        return panel

    def _iv_create_result_panel(self):
        panel = QFrame()
        panel.setObjectName("iv_panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 18, 20, 14)
        layout.setSpacing(12)

        top = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(3)
        self._iv_result_title = QLabel("Interview result")
        self._iv_result_title.setObjectName("iv_panel_title")
        self._iv_result_meta = QLabel("")
        self._iv_result_meta.setObjectName("iv_muted")
        titles.addWidget(self._iv_result_title)
        titles.addWidget(self._iv_result_meta)

        self._iv_result_status = QLabel("")
        top.addLayout(titles)
        top.addStretch()
        top.addWidget(self._iv_result_status, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(top)

        form = QHBoxLayout()
        form.setSpacing(12)

        result_col = QVBoxLayout()
        result_col.setSpacing(6)
        result_label = QLabel("Interview result *")
        result_label.setObjectName("iv_field_label")
        self._iv_result_combo = QComboBox()
        self._iv_result_combo.setObjectName("iv_combo")
        self._iv_result_combo.setFixedSize(240, 38)
        self._iv_result_combo.addItem(RESULT_PLACEHOLDER)
        self._iv_result_combo.addItems(RESULT_CHOICES)
        result_col.addWidget(result_label)
        result_col.addWidget(self._iv_result_combo)

        remarks_col = QVBoxLayout()
        remarks_col.setSpacing(6)
        remarks_label = QLabel("Official remarks *")
        remarks_label.setObjectName("iv_field_label")
        self._iv_result_remarks = QLineEdit()
        self._iv_result_remarks.setObjectName("iv_input")
        self._iv_result_remarks.setFixedHeight(38)
        self._iv_result_remarks.setPlaceholderText("Enter official remarks")
        self._iv_result_remarks.returnPressed.connect(self._iv_record_result)
        remarks_col.addWidget(remarks_label)
        remarks_col.addWidget(self._iv_result_remarks)

        button_col = QVBoxLayout()
        button_col.setSpacing(6)
        button_col.addSpacing(18)
        self._iv_record_button = QPushButton("Record result")
        self._iv_record_button.setObjectName("iv_primary")
        self._iv_record_button.setFixedHeight(38)
        self._iv_record_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._iv_record_button.clicked.connect(self._iv_record_result)
        button_col.addWidget(self._iv_record_button)

        form.addLayout(result_col)
        form.addLayout(remarks_col, 1)
        form.addLayout(button_col)
        layout.addLayout(form)

        note = QFrame()
        note.setObjectName("iv_note")
        note.setFixedHeight(36)
        note_row = QHBoxLayout(note)
        note_row.setContentsMargins(14, 0, 14, 0)
        note_text = QLabel(
            "An interview recommendation is not an award. Record the final "
            "evaluation in Scholarship Decisions."
        )
        note_text.setObjectName("iv_note_text")
        note_row.addWidget(note_text)
        note_row.addStretch()
        layout.addWidget(note)
        return panel

    def _iv_create_footer(self):
        row = QHBoxLayout()
        left = QLabel("Fictional records for demonstration only. "
                      "Authorized LYDO personnel access.")
        left.setObjectName("iv_footer")
        right = QLabel("Santa Cruz, Laguna · LYDO")
        right.setObjectName("iv_footer")
        row.addWidget(left)
        row.addStretch()
        row.addWidget(right)
        return row

    # ------------------------------------------------------------ Refresh
    def refresh_interviews(self):
        try:
            records = self._iv_records
            scheduled = [r for r in records if r["status"] == "Scheduled"]
            completed = [r for r in records if r["status"] == "Completed"]
            awaiting = [r for r in completed if r["result"] == "Recommended"]

            self._iv_stat_scheduled.setText(str(len(scheduled)))
            self._iv_stat_completed.setText(str(len(completed)))
            self._iv_stat_awaiting.setText(str(len(awaiting)))

            self._iv_tab_buttons["all"].setText(
                f"All interviews  {len(records)}")
            self._iv_tab_buttons["upcoming"].setText(
                f"Upcoming  {len(scheduled)}")
            self._iv_tab_buttons["completed"].setText(
                f"Completed  {len(completed)}")

            self._iv_fill_next_day(scheduled)
            self._iv_populate_filters(records)

            if not any(r["ref"] == self._iv_selected for r in records):
                first = completed[0] if completed else (
                    records[0] if records else None)
                self._iv_selected = first["ref"] if first else None

            self._iv_render_rows()
            self._iv_fill_result_panel()
        except Exception as error:
            self.show_error("Interviews", error)

    def _iv_fill_next_day(self, scheduled):
        if not scheduled:
            self._iv_date_month.setText("—")
            self._iv_date_day.setText("—")
            self._iv_next_line1.setText("No scheduled interviews")
            self._iv_next_line2.setText("")
            return

        day = min(r["when"].date() for r in scheduled)
        same_day = sorted(
            (r for r in scheduled if r["when"].date() == day),
            key=lambda r: r["when"],
        )
        first = same_day[0]["when"]
        last = same_day[-1]["when"] + timedelta(minutes=SLOT_MINUTES)
        count = len(same_day)

        self._iv_date_month.setText(first.strftime("%b").upper())
        self._iv_date_day.setText(str(first.day))
        self._iv_next_line1.setText(
            f"{first.strftime('%A')} · {count} "
            f"applicant{'s' if count != 1 else ''} · LYDO office"
        )
        self._iv_next_line2.setText(
            f"{_fmt_time(first)} – {_fmt_time(last)} · "
            f"{SLOT_MINUTES}-minute slots"
        )

    def _iv_populate_filters(self, records):
        interviewers = ["All interviewers"] + sorted(
            {r["interviewer"] for r in records})
        months = []
        for record in sorted(records, key=lambda r: r["when"], reverse=True):
            label = _month_label(record["when"])
            if label not in months:
                months.append(label)

        for combo, items in ((self._iv_interviewer, interviewers),
                             (self._iv_month_combo, months)):
            current = combo.currentText()
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(items)
            index = combo.findText(current)
            combo.setCurrentIndex(index if index >= 0 else 0)
            combo.blockSignals(False)

    # -------------------------------------------------------------- Table
    def _iv_set_tab(self, key):
        self._iv_tab = key
        self._iv_render_rows()

    def _iv_filtered(self):
        text = self._iv_search.text().strip().lower()
        who = self._iv_interviewer.currentText()
        month = self._iv_month_combo.currentText()

        rows = []
        for record in self._iv_records:
            if self._iv_tab == "upcoming" and record["status"] != "Scheduled":
                continue
            if self._iv_tab == "completed" and record["status"] != "Completed":
                continue
            if who and who != "All interviewers" and record["interviewer"] != who:
                continue
            if month and _month_label(record["when"]) != month:
                continue
            if text and text not in record["name"].lower() \
                    and text not in record["ref"].lower():
                continue
            rows.append(record)

        return sorted(
            rows, key=lambda r: (-r["when"].toordinal(), r["when"].time()))

    def _iv_clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._iv_clear_layout(item.layout())

    def _iv_render_rows(self):
        self._iv_clear_layout(self._iv_rows)
        rows = self._iv_filtered()

        if not rows:
            empty = QLabel("No interviews match the current filters.")
            empty.setObjectName("iv_muted")
            empty.setContentsMargins(12, 18, 12, 18)
            self._iv_rows.addWidget(empty)

        for index, record in enumerate(rows):
            frame = ClickableFrame()
            frame.setObjectName("iv_row")
            frame.setProperty("last", index == len(rows) - 1)
            frame.setProperty("selected", record["ref"] == self._iv_selected)
            frame.setFixedHeight(60)
            frame.setCursor(Qt.CursorShape.PointingHandCursor)
            frame.clicked.connect(
                lambda ref=record["ref"]: self._iv_select(ref))

            row = QHBoxLayout(frame)
            row.setContentsMargins(12, 0, 12, 0)
            row.setSpacing(0)

            who = QWidget()
            who_layout = QVBoxLayout(who)
            who_layout.setContentsMargins(0, 0, 0, 0)
            who_layout.setSpacing(2)
            who_layout.addStretch()
            name = QLabel(record["name"])
            name.setObjectName("iv_cell_name")
            ref = QLabel(record["ref"])
            ref.setObjectName("iv_cell_ref")
            who_layout.addWidget(name)
            who_layout.addWidget(ref)
            who_layout.addStretch()

            when = QLabel(_fmt_short(record["when"]))
            when.setObjectName("iv_cell_text")
            interviewer = QLabel(record["interviewer"])
            interviewer.setObjectName("iv_cell_text")
            remarks = QLabel(record["remarks"])
            remarks.setObjectName("iv_cell_remarks")

            row.addWidget(who, 220)
            row.addWidget(when, 160)
            row.addWidget(interviewer, 140)
            row.addWidget(self._iv_pill(record["status"], STATUS_STYLES), 140)
            row.addWidget(self._iv_pill(record["result"], RESULT_STYLES), 150)
            row.addWidget(remarks, 320)
            self._iv_rows.addWidget(frame)

        self._iv_count_note.setText(
            f"{len(rows)} interview record{'s' if len(rows) != 1 else ''} · "
            "All interviews are conducted by LYDO officials, never by AI."
        )

    def _iv_pill(self, text, styles):
        background, color = styles.get(text, ("#eef1f4", "#475569"))
        pill = QLabel(text)
        pill.setStyleSheet(_pill_css(background, color))
        wrapper = QWidget()
        wrapper.setStyleSheet("background: transparent;")
        row = QHBoxLayout(wrapper)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(pill, 0, Qt.AlignmentFlag.AlignVCenter)
        row.addStretch()
        return wrapper

    def _iv_select(self, ref):
        self._iv_selected = ref
        self._iv_render_rows()
        self._iv_fill_result_panel()

    # -------------------------------------------------------- Result panel
    def _iv_get_selected(self):
        for record in self._iv_records:
            if record["ref"] == self._iv_selected:
                return record
        return None

    def _iv_fill_result_panel(self):
        record = self._iv_get_selected()
        enabled = record is not None
        self._iv_result_combo.setEnabled(enabled)
        self._iv_result_remarks.setEnabled(enabled)
        self._iv_record_button.setEnabled(enabled)

        if record is None:
            self._iv_result_title.setText("Interview result")
            self._iv_result_meta.setText(
                "Select an interview to record its result.")
            self._iv_result_status.hide()
            self._iv_result_combo.setCurrentIndex(0)
            self._iv_result_remarks.clear()
            return

        self._iv_result_title.setText(f"Interview result · {record['name']}")
        self._iv_result_meta.setText(
            f"{record['ref']} · {_fmt_long(record['when'])} · "
            f"Interviewer: {record['interviewer']}"
        )

        background, color = STATUS_STYLES.get(
            record["status"], ("#eef1f4", "#475569"))
        self._iv_result_status.setText(record["status"])
        self._iv_result_status.setStyleSheet(_pill_css(background, color))
        self._iv_result_status.show()

        index = self._iv_result_combo.findText(record["result"])
        self._iv_result_combo.setCurrentIndex(index if index > 0 else 0)
        if record["status"] == "Completed":
            self._iv_result_remarks.setText(record["remarks"])
        else:
            self._iv_result_remarks.clear()

    def _iv_record_result(self):
        record = self._iv_get_selected()
        if record is None:
            return

        result = self._iv_result_combo.currentText()
        remarks = self._iv_result_remarks.text().strip()
        if result == RESULT_PLACEHOLDER or not remarks:
            QMessageBox.warning(
                self,
                "Interview result",
                "Select an interview result and enter the official remarks "
                "before recording.",
            )
            return

        # In-memory only. Save to the database here when it is connected.
        record["status"] = "Completed"
        record["result"] = result
        record["remarks"] = remarks
        self.refresh_interviews()

    # ------------------------------------------------- Schedule interview
    def open_schedule_interview(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Schedule interview")
        dialog.setMinimumWidth(420)

        form = QFormLayout(dialog)
        form.setContentsMargins(20, 20, 20, 20)
        form.setSpacing(12)

        name = QLineEdit()
        ref = QLineEdit()
        ref.setPlaceholderText("APP-26-009")

        date = QDateEdit(QDate.currentDate())
        date.setCalendarPopup(True)
        date.setDisplayFormat("dd MMM yyyy")

        time = QTimeEdit(QTime(9, 0))
        time.setDisplayFormat("h:mm AP")

        who = QComboBox()
        who.setEditable(True)
        who.addItems(sorted({r["interviewer"] for r in self._iv_records}))

        form.addRow("Applicant name", name)
        form.addRow("Application no.", ref)
        form.addRow("Date", date)
        form.addRow("Time", time)
        form.addRow("Interviewer", who)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Schedule")
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        applicant = name.text().strip()
        app_no = ref.text().strip().upper()
        interviewer = who.currentText().strip()
        if not applicant or not app_no or not interviewer:
            QMessageBox.warning(
                self, "Schedule interview",
                "Applicant name, application number and interviewer "
                "are required.")
            return
        if any(r["ref"] == app_no for r in self._iv_records):
            QMessageBox.warning(
                self, "Schedule interview",
                f"{app_no} already has an interview record.")
            return

        picked_date, picked_time = date.date(), time.time()
        when = datetime(
            picked_date.year(), picked_date.month(), picked_date.day(),
            picked_time.hour(), picked_time.minute(),
        )

        # In-memory only. Save to the database here when it is connected.
        self._iv_records.append({
            "name": applicant, "ref": app_no, "when": when,
            "interviewer": interviewer, "status": "Scheduled",
            "result": "Not recorded", "remarks": "LYDO office",
        })
        self._iv_selected = app_no
        self.refresh_interviews()

        # Make sure the new record is visible.
        self._iv_tab_buttons["all"].setChecked(True)
        self._iv_tab = "all"
        self._iv_interviewer.setCurrentIndex(0)
        month_index = self._iv_month_combo.findText(_month_label(when))
        if month_index >= 0:
            self._iv_month_combo.setCurrentIndex(month_index)
        self._iv_search.clear()
        self._iv_render_rows()
        self._iv_fill_result_panel()