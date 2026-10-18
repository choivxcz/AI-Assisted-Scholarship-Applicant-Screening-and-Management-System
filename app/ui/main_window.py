from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QFrame,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QStackedWidget,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QHeaderView,
)

from app.ui.pages.navigation_page import NavigationPageMixin
from app.ui.pages.dashboard_page import DashboardPageMixin
from app.ui.pages.applicants_page import ApplicantsPageMixin
from app.ui.pages.applications_page import ApplicationsPageMixin
from app.ui.pages.ml_screening_page import MLScreeningPageMixin
from app.ui.pages.interviews_page import InterviewsPageMixin
from app.ui.pages.decisions_page import DecisionsPageMixin


class MainWindow(
    QMainWindow,
    NavigationPageMixin,
    DashboardPageMixin,
    ApplicantsPageMixin,
    ApplicationsPageMixin,
    MLScreeningPageMixin,
    InterviewsPageMixin,
    DecisionsPageMixin,
):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "Iskolar ng Bayan | Scholarship Management System"
        )
        self.resize(1280, 800)
        self.setMinimumSize(950, 600)

        self.nav_buttons = []
        self.pages = QStackedWidget()

        # ML screening state must exist before pages are initialized.
        self._ml_current_results = {}
        self._ml_auto_screen_done = False

        self.setStyleSheet("""
            QMainWindow, QWidget#content {
                background-color: #F4F7FB;
                color: #1F2937;
                font-family: Segoe UI;
                font-size: 10pt;
            }

            /* ---------------- Sidebar ---------------- */
            QFrame#sidebar {
                background-color: #172554;
            }

            QLabel#brand_logo {
                background-color: #1E3A8A;
                border-radius: 8px;
                color: white;
                font-size: 15pt;
            }

            QLabel#brand {
                color: white;
                font-size: 16pt;
                font-weight: 500;
            }

            QLabel#sidebar_subtitle {
                color: #CBD5E1;
                font-size: 8pt;
            }

            QLabel#sidebar_section {
                color: #93C5FD;
                font-size: 7.5pt;
                font-weight: 600;
            }

            QPushButton#nav_button {
                background-color: transparent;
                color: #E2E8F0;
                border: none;
                text-align: left;
                padding: 11px 12px;
                border-radius: 8px;
            }

            QPushButton#nav_button:hover {
                background-color: #1B2F6E;
            }

            QPushButton#nav_button:checked {
                background-color: #1E3A8A;
                color: white;
                font-weight: bold;
            }

            QFrame#sidebar_card {
                background-color: rgba(255, 255, 255, 0.07);
                border: none;
                border-radius: 10px;
            }

            QLabel#sidebar_card_icon {
                color: #93C5FD;
                font-size: 12pt;
            }

            QLabel#sidebar_card_title {
                color: white;
                font-weight: bold;
                font-size: 9.5pt;
            }

            QLabel#sidebar_card_text {
                color: #CBD5E1;
                font-size: 8pt;
            }

            QLabel#sidebar_footer {
                color: #CBD5E1;
                font-size: 9pt;
            }

            /* ---------------- Top bar ---------------- */
            QFrame#topbar {
                background-color: white;
                border: none;
                border-bottom: 1px solid #E2E8F0;
            }

            QLabel#breadcrumb {
                color: #64748B;
            }

            QLabel#breadcrumb_current {
                color: #172554;
                font-weight: 600;
            }

            QLabel#chip {
                background-color: #EFF6FF;
                color: #475569;
                border-radius: 4px;
                padding: 3px 9px;
                font-size: 8pt;
            }

            QLabel#topbar_text {
                color: #475569;
                font-size: 9pt;
            }

            QLabel#avatar {
                background-color: #DBEAFE;
                color: #1E3A8A;
                border-radius: 17px;
                font-weight: bold;
                font-size: 9pt;
            }

            QLabel#user_name {
                color: #172554;
                font-weight: 600;
                font-size: 9pt;
            }

            QLabel#user_role {
                color: #64748B;
                font-size: 8pt;
            }

            /* ---------------- Pages ---------------- */
            QScrollArea#page_scroll {
                background: transparent;
                border: none;
            }

            QScrollArea#page_scroll > QWidget > QWidget {
                background: transparent;
            }

            QScrollBar:vertical {
                background: transparent;
                width: 10px;
                margin: 2px;
            }

            QScrollBar::handle:vertical {
                background: #CBD5E1;
                border-radius: 4px;
                min-height: 30px;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QLabel#page_title {
                font-size: 23pt;
                font-weight: bold;
                color: #172554;
            }

            QLabel#muted {
                color: #64748B;
            }

            QFrame#stat_card, QFrame#panel {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
            }

            QLabel#stat_label {
                color: #64748B;
            }

            QLabel#stat_value {
                color: #172554;
                font-size: 24pt;
                font-weight: bold;
            }

            QPushButton#action_button {
                background-color: #2563EB;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 9px 13px;
                font-weight: bold;
            }

            QPushButton#action_button:hover {
                background-color: #1D4ED8;
            }

            QPushButton#danger_button {
                background-color: #DC2626;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 9px 13px;
                font-weight: bold;
            }

            QPushButton#danger_button:hover {
                background-color: #B91C1C;
            }

            QLineEdit {
                background-color: white;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 9px;
            }

            QLineEdit:focus {
                border: 1px solid #2563EB;
            }

            QTableWidget {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                gridline-color: #E2E8F0;
                selection-background-color: #DBEAFE;
                selection-color: #172554;
            }

            QHeaderView::section {
                background-color: #EFF4FA;
                color: #334155;
                padding: 9px;
                border: none;
                border-bottom: 1px solid #CBD5E1;
                font-weight: bold;
            }
        """)

        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self.create_sidebar())

        content = QWidget()
        content.setObjectName("content")

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        content_layout.addWidget(self.create_topbar())

        # Page order must match the sidebar (NAV_ITEMS) order.
        self.pages.addWidget(self.create_dashboard())             # 0
        self.pages.addWidget(self.create_applicants_page())       # 1
        self.pages.addWidget(self.create_applications_page())     # 2
        self.pages.addWidget(self.create_ml_screening_page())     # 3
        self.pages.addWidget(self.create_interviews_page())       # 4

        self.pages.addWidget(self.create_decisions_page())        # 5

        # Pages live inside a scroll area so the dashboard never gets cut off.
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(28, 24, 28, 24)
        body_layout.addWidget(self.pages)

        scroll = QScrollArea()
        scroll.setObjectName("page_scroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll.setWidget(body)

        content_layout.addWidget(scroll, 1)
        root_layout.addWidget(content, 1)

        self.setCentralWidget(root)

        self.navigate(0)
        self.refresh_all()

    def create_topbar(self):
        bar = QFrame()
        bar.setObjectName("topbar")
        bar.setFixedHeight(56)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(28, 0, 28, 0)
        layout.setSpacing(14)

        self.breadcrumb = QLabel("Scholarships  ›  Dashboard")
        self.breadcrumb.setObjectName("breadcrumb")

        chip = QLabel("Demonstration data")
        chip.setObjectName("chip")

        academic_year = QLabel("AY 2026–2027")
        academic_year.setObjectName("topbar_text")

        avatar = QLabel("MR")
        avatar.setObjectName("avatar")
        avatar.setFixedSize(34, 34)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        user_name = QLabel("Mika Reyes")
        user_name.setObjectName("user_name")
        user_role = QLabel("LYDO Administrator")
        user_role.setObjectName("user_role")

        user_text = QVBoxLayout()
        user_text.setSpacing(0)
        user_text.addWidget(user_name)
        user_text.addWidget(user_role)

        layout.addWidget(self.breadcrumb)
        layout.addStretch()
        layout.addWidget(chip)
        layout.addWidget(academic_year)
        layout.addWidget(avatar)
        layout.addLayout(user_text)

        return bar

    @staticmethod
    def configure_table(table):
        table.setAlternatingRowColors(True)
        table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

    @staticmethod
    def set_table_item(table, row, column, value):
        item = QTableWidgetItem(
            "" if value is None else str(value)
        )
        item.setFlags(
            item.flags() & ~Qt.ItemFlag.ItemIsEditable
        )
        table.setItem(row, column, item)

    def refresh_all(self):
        self.refresh_dashboard()
        self.refresh_applicants()
        self.refresh_applications()
        self.refresh_interviews()
        self.refresh_decisions()

    def show_error(self, context, error):
        QMessageBox.warning(
            self,
            f"{context} Error",
            f"Could not load {context.lower()} data.\n\n{error}",
        )