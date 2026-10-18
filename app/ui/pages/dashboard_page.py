from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFontDatabase
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.repositories.application_repository import ApplicationRepository

USE_SAMPLE_DATA = True  # True = exact numbers from the mockup

# status -> (label, background, text)
STATUS_STYLES = {
    "SUBMITTED": ("Newly submitted", "#e0ebff", "#1d4ed8"),
    "UNDER_REVIEW": ("Under review", "#fdf0c8", "#b45309"),
    "FOR_INTERVIEW": ("Selected for interview", "#dbe8ff", "#1d4ed8"),
    "INTERVIEWED": ("Interviewed", "#e0e7ff", "#4338ca"),
    "RECOMMENDED": ("Recommended", "#ccfbf1", "#0f766e"),
    "FINAL_DECISION": ("Final decision", "#dbe8ff", "#1d4ed8"),
}

SAMPLE = {
    "total": 248,
    "awaiting": 68,
    "queue": 44,
    "approved": 48,
    "recent": [
        ("Ana Villanueva", "Pagsawitan", "12 Oct 2026", "SUBMITTED"),
        ("Gabriel Mendoza", "Calios", "11 Oct 2026", "UNDER_REVIEW"),
        ("Luis Navarro", "Duhat", "10 Oct 2026", "UNDER_REVIEW"),
        ("Sofia Bautista", "Gatid", "07 Oct 2026", "FOR_INTERVIEW"),
        ("Maria Dela Cruz", "Pagsawitan", "05 Oct 2026", "FINAL_DECISION"),
    ],
    "outcome": "Maria Dela Cruz · Scholarship outcome: "
               "Approved by Elena Ramos, 09 Oct",
    "interviews": [
        ("09:00", "Sofia Bautista", "SC-2026-0219 · Elena Ramos"),
        ("09:30", "Paolo Garcia", "SC-2026-0208 · Elena Ramos"),
        ("10:00", "Janelle Ramos", "SC-2026-0205 · Marco Santos"),
    ],
    "date": "12 Oct 2026",
    "interview_day": "Monday, 12 October · LYDO office",
}

STYLE = """
QWidget { font-family: "%FONT%"; }
QWidget#dashboard_page { background: #f7f9fc; }

/* top bar */
QFrame#topbar { background: #ffffff; border: none;
    border-bottom: 1px solid #e2e8f0; }
QLabel#crumb { color: #64748b; font-size: 9pt; }
QLabel#crumb_current { color: #0f172a; font-weight: 600; font-size: 9pt; }
QLabel#sample_chip { background: #e8eeff; color: #2548c4; font-size: 8pt;
    font-weight: 600; padding: 5px 9px; border-radius: 4px; }
QLabel#top_date { color: #64748b; font-size: 9pt; }
QLabel#avatar { background: #dbe6ff; color: #2548c4; font-weight: 600;
    font-size: 8pt; border-radius: 16px; }
QLabel#user_name { color: #0f172a; font-weight: 600; font-size: 9pt; }
QLabel#user_role { color: #64748b; font-size: 8pt; }
QFrame#vsep { background: #e2e8f0; border: none; }

/* headings */
QLabel#page_title { font-size: 22pt; font-weight: 600; color: #0f172a; }
QLabel#muted { color: #64748b; font-size: 9pt; }
QLabel#panel_title { font-size: 12pt; font-weight: 600; color: #0f172a; }

/* buttons */
QPushButton#secondary_button { background: #ffffff; border: 1px solid #dbe2ea;
    border-radius: 6px; padding: 9px 16px; font-weight: 600; font-size: 9pt;
    color: #0f172a; }
QPushButton#secondary_button:hover { background: #f1f5f9; }
QPushButton#action_button { background: #2563eb; border: none;
    border-radius: 6px; padding: 10px 18px; font-weight: 600; font-size: 9pt;
    color: #ffffff; }
QPushButton#action_button:hover { background: #1d4ed8; }
QPushButton#link_button { background: transparent; border: none;
    color: #0f766e; font-weight: 600; font-size: 9pt; padding: 0; }

/* cards / panels */
QFrame#stat_card, QFrame#panel { background: #ffffff;
    border: 1px solid #e2e8f0; border-radius: 6px; }
QLabel#stat_label { color: #64748b; font-size: 9.5pt; }
QLabel#stat_value { font-size: 24pt; font-weight: 600; color: #0f172a; }

/* table */
QFrame#table_header { background: #f4f6f9; border: none; border-radius: 4px; }
QLabel#th { color: #64748b; font-weight: 600; font-size: 8.5pt; }
QFrame#table_row { background: transparent; border: none;
    border-bottom: 1px solid #e2e8f0; }
QFrame#table_row[last="true"] { border-bottom: none; }
QLabel#cell_bold { color: #0f172a; font-weight: 600; font-size: 9pt; }
QLabel#cell_muted { color: #64748b; font-size: 9pt; }
QLabel#foot_note { color: #64748b; font-size: 8.5pt; }

/* interviews */
QLabel#time_chip { background: #f1f5f9; color: #2563eb; font-weight: 600;
    font-size: 10pt; padding: 8px 10px; border-radius: 4px; }
QLabel#iv_name { color: #0f172a; font-weight: 600; font-size: 10pt; }
QLabel#iv_meta { color: #64748b; font-size: 8.5pt; }

/* banner */
QFrame#info_banner { background: #e0ebff; border: 1px solid #cfe0ff;
    border-radius: 4px; }
QLabel#info_text { color: #1d4ed8; font-size: 9.5pt; }
"""

def _font_family():
    """Inter (as in the mockup) if installed, otherwise Segoe UI."""
    return "Inter" if "Inter" in QFontDatabase.families() else "Segoe UI"


class DashboardPageMixin:
    # ------------------------------------------------------------------ UI
    def create_dashboard(self):
        page = QWidget()
        page.setObjectName("dashboard_page")
        page.setStyleSheet(STYLE.replace("%FONT%", _font_family()))

        root = QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._create_topbar())

        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(32, 32, 32, 20)
        layout.setSpacing(22)

        layout.addLayout(self._create_header())
        layout.addLayout(self._create_stat_cards())

        lower = QHBoxLayout()
        lower.setSpacing(20)
        lower.addWidget(self._create_recent_panel(), 3,
                        alignment=Qt.AlignmentFlag.AlignTop)
        lower.addWidget(
            self._create_interviews_panel(), 2,
            alignment=Qt.AlignmentFlag.AlignTop,
        )
        layout.addLayout(lower)

        layout.addWidget(self._create_banner())
        layout.addStretch()

        root.addWidget(body, 1)
        return page

    def _create_topbar(self):
        bar = QFrame()
        bar.setObjectName("topbar")
        bar.setFixedHeight(64)
        row = QHBoxLayout(bar)
        row.setContentsMargins(32, 0, 32, 0)
        row.setSpacing(10)

        v_center = Qt.AlignmentFlag.AlignVCenter

        crumb = QLabel("Workspace")
        crumb.setObjectName("crumb")
        slash = QLabel("/")
        slash.setObjectName("crumb")
        current = QLabel("Dashboard")
        current.setObjectName("crumb_current")

        self.sample_chip = QLabel("SAMPLE DATA")
        self.sample_chip.setObjectName("sample_chip")
        self.top_date = QLabel("")
        self.top_date.setObjectName("top_date")

        sep = QFrame()
        sep.setObjectName("vsep")
        sep.setFixedSize(1, 32)

        avatar = QLabel("ER")
        avatar.setObjectName("avatar")
        avatar.setFixedSize(32, 32)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        user_box = QWidget()
        user = QVBoxLayout(user_box)
        user.setContentsMargins(0, 0, 0, 0)
        user.setSpacing(0)
        name = QLabel("Elena Ramos")
        name.setObjectName("user_name")
        role = QLabel("Authorized official · Admin")
        role.setObjectName("user_role")
        user.addWidget(name)
        user.addWidget(role)

        row.addWidget(crumb, 0, v_center)
        row.addWidget(slash, 0, v_center)
        row.addWidget(current, 0, v_center)
        row.addStretch()
        row.addWidget(self.sample_chip, 0, v_center)
        row.addWidget(self.top_date, 0, v_center)
        row.addSpacing(6)
        row.addWidget(sep, 0, v_center)
        row.addSpacing(6)
        row.addWidget(avatar, 0, v_center)
        row.addWidget(user_box, 0, v_center)
        return bar

    def _create_header(self):
        row = QHBoxLayout()

        text = QVBoxLayout()
        text.setSpacing(6)
        title = QLabel("Scholarship overview")
        title.setObjectName("page_title")
        sub = QLabel("Academic year 2026–2027 · Your application cycle at a glance")
        sub.setObjectName("muted")
        text.addWidget(title)
        text.addWidget(sub)

        new_button = QPushButton("New application")
        new_button.setObjectName("action_button")
        new_button.setCursor(Qt.CursorShape.PointingHandCursor)
        new_button.clicked.connect(self.open_new_application)

        row.addLayout(text)
        row.addStretch()
        row.addWidget(new_button, alignment=Qt.AlignmentFlag.AlignTop)
        return row

    def _create_stat_cards(self):
        cards = QHBoxLayout()
        cards.setSpacing(16)

        self.application_count = self.create_stat_card(
            "Total applications", "Across 8 sample barangays")
        self.review_count = self.create_stat_card(
            "Awaiting review", "Official review required")
        self.interview_count = self.create_stat_card(
            "Interview queue", "Selected by LYDO officials")
        self.approved_count = self.create_stat_card(
            "Approved scholars", "Final decisions recorded")

        for card in (self.application_count, self.review_count,
                     self.interview_count, self.approved_count):
            cards.addWidget(card, 1)
        return cards

    def create_stat_card(self, label_text, caption_text=""):
        card = QFrame()
        card.setObjectName("stat_card")
        card.setFixedHeight(146)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)

        top = QHBoxLayout()
        label = QLabel(label_text)
        label.setObjectName("stat_label")
        top.addWidget(label)
        top.addStretch()

        value = QLabel("—")
        value.setObjectName("stat_value")

        caption = QLabel(caption_text)
        caption.setObjectName("muted")

        layout.addLayout(top)
        layout.addSpacing(8)
        layout.addWidget(value)
        layout.addStretch()
        layout.addWidget(caption)

        card.value_label = value
        card.caption_label = caption
        return card

    def _create_recent_panel(self):
        panel = QFrame()
        panel.setObjectName("panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(3)
        title = QLabel("Recent applications")
        title.setObjectName("panel_title")
        sub = QLabel("Latest sample records and official statuses")
        sub.setObjectName("muted")
        titles.addWidget(title)
        titles.addWidget(sub)

        view_records = QPushButton("View records")
        view_records.setObjectName("link_button")
        view_records.setCursor(Qt.CursorShape.PointingHandCursor)
        view_records.clicked.connect(self.open_applicants_page)

        header.addLayout(titles)
        header.addStretch()
        header.addWidget(view_records, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(header)

        # column header
        th = QFrame()
        th.setObjectName("table_header")
        th.setFixedHeight(36)
        th_row = QHBoxLayout(th)
        th_row.setContentsMargins(12, 0, 12, 0)
        th_row.setSpacing(0)
        for text, stretch in (("Applicant", 205), ("Barangay", 130),
                              ("Submitted", 112), ("Official status", 255)):
            label = QLabel(text)
            label.setObjectName("th")
            th_row.addWidget(label, stretch)
        layout.addWidget(th)

        self.recent_rows = QVBoxLayout()
        self.recent_rows.setSpacing(0)
        layout.addLayout(self.recent_rows)

        self.recent_note = QLabel("")
        self.recent_note.setObjectName("foot_note")
        layout.addWidget(self.recent_note)
        return panel

    def _create_interviews_panel(self):
        panel = QFrame()
        panel.setObjectName("panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)

        title = QLabel("Upcoming interviews")
        title.setObjectName("panel_title")
        self.interviews_subtitle = QLabel("")
        self.interviews_subtitle.setObjectName("muted")

        self.interviews_layout = QVBoxLayout()
        self.interviews_layout.setSpacing(22)

        open_button = QPushButton("Open interview schedule")
        open_button.setObjectName("secondary_button")
        open_button.setCursor(Qt.CursorShape.PointingHandCursor)
        open_button.clicked.connect(self.open_interviews_page)

        layout.addWidget(title)
        layout.addSpacing(3)
        layout.addWidget(self.interviews_subtitle)
        layout.addSpacing(18)
        layout.addLayout(self.interviews_layout)
        layout.addSpacing(22)
        layout.addWidget(open_button, alignment=Qt.AlignmentFlag.AlignLeft)
        return panel

    def _create_banner(self):
        banner = QFrame()
        banner.setObjectName("info_banner")
        banner.setFixedHeight(40)
        row = QHBoxLayout(banner)
        row.setContentsMargins(16, 0, 16, 0)
        row.setSpacing(10)

        text = QLabel(
            "AI screening supports review only. Interviews and final "
            "scholarship decisions are made by authorized LYDO officials."
        )
        text.setObjectName("info_text")

        row.addWidget(text)
        row.addStretch()
        return banner

    # ------------------------------------------------------------ Refresh
    def refresh_dashboard(self):
        try:
            data = SAMPLE if USE_SAMPLE_DATA else self._load_dashboard_data()

            self.sample_chip.setVisible(USE_SAMPLE_DATA)
            self.top_date.setText(data["date"])

            self.application_count.value_label.setText(str(data["total"]))
            self.review_count.value_label.setText(str(data["awaiting"]))
            self.interview_count.value_label.setText(str(data["queue"]))
            self.approved_count.value_label.setText(str(data["approved"]))

            self._fill_recent(data["recent"], data["outcome"])
            self._fill_interviews(data["interviews"], data["interview_day"])

        except Exception as error:
            self.show_error("Dashboard", error)

    def _load_dashboard_data(self):
        applications = ApplicationRepository.get_all()

        counts = {}
        for item in applications:
            counts[item.get("status")] = counts.get(item.get("status"), 0) + 1

        recent_src = sorted(
            applications,
            key=lambda a: str(a.get("submitted_at") or a.get("created_at") or ""),
            reverse=True,
        )[:5]
        recent = [
            (
                a.get("applicant_name") or a.get("full_name") or "—",
                a.get("barangay") or "—",
                self._format_date(a.get("submitted_at") or a.get("created_at")),
                a.get("status"),
            )
            for a in recent_src
        ]

        today = datetime.now()
        todays = sorted(
            (a for a in applications
             if str(a.get("interview_date") or "").startswith(
                 today.strftime("%Y-%m-%d"))),
            key=lambda a: str(a.get("interview_time") or ""),
        )[:3]
        interviews = [
            (
                str(a.get("interview_time") or "—")[:5],
                a.get("applicant_name") or a.get("full_name") or "—",
                f"{a.get('reference_no', '')} · {a.get('interviewer', '')}",
            )
            for a in todays
        ]

        return {
            "total": len(applications),
            "awaiting": counts.get("UNDER_REVIEW", 0),
            "queue": counts.get("FOR_INTERVIEW", 0),
            "approved": counts.get("APPROVED", 0),
            "recent": recent,
            "outcome": "",
            "interviews": interviews,
            "date": today.strftime("%d %b %Y"),
            "interview_day": today.strftime("%A, %d %B · LYDO office"),
        }

    def _fill_recent(self, rows, outcome):
        self._clear_layout(self.recent_rows)

        for index, (name, barangay, submitted, status) in enumerate(rows):
            row_frame = QFrame()
            row_frame.setObjectName("table_row")
            row_frame.setProperty("last", index == len(rows) - 1)
            row_frame.setFixedHeight(54)
            row = QHBoxLayout(row_frame)
            row.setContentsMargins(12, 0, 12, 0)
            row.setSpacing(0)

            name_label = QLabel(name)
            name_label.setObjectName("cell_bold")
            barangay_label = QLabel(barangay)
            barangay_label.setObjectName("cell_muted")
            submitted_label = QLabel(submitted)
            submitted_label.setObjectName("cell_muted")

            row.addWidget(name_label, 205)
            row.addWidget(barangay_label, 130)
            row.addWidget(submitted_label, 112)
            row.addWidget(self._status_pill(status), 255)
            self.recent_rows.addWidget(row_frame)

        self.recent_note.setText(outcome)
        self.recent_note.setVisible(bool(outcome))

    def _status_pill(self, status):
        label, bg, fg = STATUS_STYLES.get(
            status,
            (str(status or "—").replace("_", " ").title(), "#e5e7eb", "#374151"),
        )
        pill = QLabel(label)
        pill.setStyleSheet(
            f"background: {bg}; color: {fg}; border-radius: 3px;"
            "padding: 4px 9px; font-size: 8.5pt; font-weight: 600;"
        )
        wrapper = QWidget()
        wrapper.setStyleSheet("background: transparent;")
        row = QHBoxLayout(wrapper)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(pill, 0, Qt.AlignmentFlag.AlignVCenter)
        row.addStretch()
        return wrapper

    def _fill_interviews(self, interviews, day_text):
        self._clear_layout(self.interviews_layout)
        self.interviews_subtitle.setText(day_text)

        if not interviews:
            empty = QLabel("No interviews scheduled today.")
            empty.setObjectName("muted")
            self.interviews_layout.addWidget(empty)
            return

        for time_text, name, meta in interviews:
            row = QHBoxLayout()
            row.setSpacing(14)

            chip = QLabel(time_text)
            chip.setObjectName("time_chip")
            chip.setFixedWidth(60)
            chip.setAlignment(Qt.AlignmentFlag.AlignCenter)

            details = QVBoxLayout()
            details.setSpacing(2)
            name_label = QLabel(name)
            name_label.setObjectName("iv_name")
            meta_label = QLabel(meta)
            meta_label.setObjectName("iv_meta")
            details.addWidget(name_label)
            details.addWidget(meta_label)

            row.addWidget(chip, alignment=Qt.AlignmentFlag.AlignTop)
            row.addLayout(details)
            row.addStretch()
            self.interviews_layout.addLayout(row)

    # ------------------------------------------------------------ Helpers
    @staticmethod
    def _format_date(value):
        if not value:
            return "—"
        if isinstance(value, datetime):
            return value.strftime("%d %b %Y")
        try:
            return datetime.fromisoformat(str(value)).strftime("%d %b %Y")
        except ValueError:
            return str(value)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    # ----------------------------------------------------------- Navigation
    def open_new_application(self):
        # Opens the Applications page (index 2 in MainWindow.PAGE_INDEX).
        if hasattr(self, "navigate"):
            self.navigate(2)

    def open_applicants_page(self):
        if hasattr(self, "navigate"):
            self.navigate(1)

    def open_interviews_page(self):
        if hasattr(self, "navigate"):
            self.navigate(4)


# ---------------------------------------------------------------- Sidebar
class Sidebar(QFrame):
    """Left navigation from the mockup. Emits the page key when clicked."""

    page_requested = pyqtSignal(str)
    sign_out_requested = pyqtSignal()

    NAV = [
        ("dashboard", "Dashboard"),
        ("applicants", "Applicants"),
        ("interviews", "Interviews"),
        ("decisions", "Decisions"),
        ("reports", "Reports"),
    ]

    STYLE = """
    QWidget { font-family: "%FONT%"; }
    QFrame#sidebar { background: #0e2a4a; border: none; }
    QLabel#brand { color: #ffffff; font-size: 20pt; font-weight: 700;
        background: transparent; }
    QLabel#brand_sub { color: #9fb3cc; font-size: 8pt; background: transparent; }
    QLabel#brand_sub2 { color: #c5d3e6; font-size: 9pt; background: transparent; }
    QPushButton#nav_button { background: transparent; color: #c5d3e6;
        border: none; border-radius: 6px; text-align: left;
        padding: 12px 16px; font-size: 10pt; }
    QPushButton#nav_button:hover { background: #163a63; }
    QPushButton#nav_button:checked { background: #2f6db5; color: #ffffff;
        font-weight: 600; }
    QPushButton#side_link { background: transparent; color: #c5d3e6;
        border: none; text-align: left; padding: 8px 0; font-size: 9pt; }
    QLabel#restricted { color: #9fb3cc; font-size: 7.5pt;
        background: transparent; }
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(224)
        self.setStyleSheet(self.STYLE.replace("%FONT%", _font_family()))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 28, 16, 16)
        layout.setSpacing(0)

        brand = QLabel("LYDO")
        brand.setObjectName("brand")
        brand_sub = QLabel("SANTA CRUZ, LAGUNA")
        brand_sub.setObjectName("brand_sub")
        brand_sub2 = QLabel("Scholarship workspace")
        brand_sub2.setObjectName("brand_sub2")

        layout.addWidget(brand)
        layout.addSpacing(10)
        layout.addWidget(brand_sub)
        layout.addSpacing(4)
        layout.addWidget(brand_sub2)
        layout.addSpacing(28)

        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self.buttons = {}
        for key, text in self.NAV:
            button = QPushButton(text)
            button.setObjectName("nav_button")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(
                lambda _checked, k=key: self.page_requested.emit(k)
            )
            self.group.addButton(button)
            self.buttons[key] = button
            layout.addWidget(button)
            layout.addSpacing(4)
        self.buttons["dashboard"].setChecked(True)

        layout.addStretch()

        admin = QPushButton("Administration")
        admin.setObjectName("side_link")
        restricted = QLabel("Restricted to authorized personnel")
        restricted.setObjectName("restricted")
        sign_out = QPushButton("Sign out")
        sign_out.setObjectName("side_link")
        sign_out.setCursor(Qt.CursorShape.PointingHandCursor)
        sign_out.clicked.connect(self.sign_out_requested.emit)

        layout.addWidget(admin)
        layout.addWidget(restricted)
        layout.addSpacing(18)
        layout.addWidget(sign_out)