
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QStackedWidget,
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


class MainWindow(
    QMainWindow,
    NavigationPageMixin,
    DashboardPageMixin,
    ApplicantsPageMixin,
    ApplicationsPageMixin,
    MLScreeningPageMixin,
):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "Iskolar ng Bayan | Scholarship Management System"
        )
        self.resize(1250, 780)
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

            QWidget#sidebar {
                background-color: #172554;
            }

            QLabel#brand {
                color: white;
                font-size: 18pt;
                font-weight: bold;
            }

            QLabel#sidebar_subtitle {
                color: #CBD5E1;
                font-size: 9pt;
            }

            QPushButton#nav_button {
                background-color: transparent;
                color: #E2E8F0;
                border: none;
                text-align: left;
                padding: 12px;
                border-radius: 6px;
            }

            QPushButton#nav_button:hover {
                background-color: #263B70;
            }

            QPushButton#nav_button:checked {
                background-color: #2563EB;
                color: white;
                font-weight: bold;
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
        content_layout.setContentsMargins(28, 24, 28, 24)

        self.pages.addWidget(self.create_dashboard())
        self.pages.addWidget(self.create_applicants_page())
        self.pages.addWidget(self.create_applications_page())
        self.pages.addWidget(self.create_ml_screening_page())

        self.pages.addWidget(
            self.create_placeholder_page(
                "Interviews",
                "Interview scheduling and records will appear here.",
            )
        )

        self.pages.addWidget(
            self.create_placeholder_page(
                "Scholarship Decisions",
                "Recommendations and official decisions will appear here.",
            )
        )

        content_layout.addWidget(self.pages)
        root_layout.addWidget(content, 1)

        self.setCentralWidget(root)

        self.navigate(0)
        self.refresh_all()

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

    def show_error(self, context, error):
        QMessageBox.warning(
            self,
            f"{context} Error",
            f"Could not load {context.lower()} data.\n\n{error}",
        )
