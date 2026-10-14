
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
)

from app.repositories.application_repository import ApplicationRepository


class ApplicationsPageMixin:
    def create_applications_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        title = QLabel("Scholarship Applications")
        title.setObjectName("page_title")

        description = QLabel(
            "Scholarship applications and their current statuses."
        )
        description.setObjectName("muted")

        refresh_button = QPushButton("Refresh Applications")
        refresh_button.setObjectName("action_button")
        refresh_button.clicked.connect(self.refresh_applications)

        self.applications_table = QTableWidget()
        self.applications_table.setColumnCount(6)
        self.applications_table.setHorizontalHeaderLabels([
            "Application ID",
            "Applicant ID",
            "Program",
            "Year",
            "Average",
            "Status",
        ])
        self.configure_table(self.applications_table)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(
            refresh_button,
            alignment=Qt.AlignmentFlag.AlignLeft,
        )
        layout.addWidget(self.applications_table)

        return page

    def refresh_applications(self):
        try:
            applications = ApplicationRepository.get_all()
            self.applications_table.setRowCount(len(applications))

            for row, application in enumerate(applications):
                values = [
                    application.get("application_id"),
                    application.get("applicant_id"),
                    application.get("scholarship_program"),
                    application.get("scholarship_year"),
                    application.get("academic_average"),
                    application.get("status"),
                ]

                for column, value in enumerate(values):
                    self.set_table_item(
                        self.applications_table,
                        row,
                        column,
                        value,
                    )

        except Exception as error:
            self.show_error("Applications", error)
