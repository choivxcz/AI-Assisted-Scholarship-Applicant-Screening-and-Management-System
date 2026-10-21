from datetime import date, datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QFormLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.repositories.applicant_repository import ApplicantRepository
from app.repositories.application_repository import ApplicationRepository


def _display_value(value):
    if value is None or value == "":
        return "Not provided"
    if isinstance(value, (datetime, date)):
        return value.strftime("%d %b %Y %I:%M %p")
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def _label(key):
    return key.replace("_", " ").strip().title()


class ApplicantDetailsDialog(QDialog):
    def __init__(self, applicant_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Applicant details")
        self.setMinimumSize(620, 560)

        applicant = ApplicantRepository.get_by_id(
            applicant_id, include_archived=True
        )
        if applicant is None:
            raise ValueError(f"Applicant {applicant_id} was not found.")

        applications = [
            application
            for application in ApplicationRepository.get_all(
                include_archived=True
            )
            if application.get("applicant_id") == applicant_id
        ]

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 16)
        root.setSpacing(12)

        name = " ".join(
            str(applicant.get(field) or "")
            for field in ("first_name", "middle_name", "last_name", "suffix")
        ).split()
        title = QLabel(" ".join(name) or f"Applicant {applicant_id}")
        title.setStyleSheet("font-size: 16pt; font-weight: 700;")
        root.addWidget(title)

        subtitle = QLabel(
            f"Applicant ID: {applicant_id} · "
            f"{len(applications)} application(s)"
        )
        subtitle.setStyleSheet("color: #64748B;")
        root.addWidget(subtitle)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 8, 0)
        content_layout.setSpacing(16)

        self._add_section(content_layout, "Applicant information", applicant)
        if applications:
            for index, application in enumerate(applications, 1):
                self._add_section(
                    content_layout,
                    f"Scholarship application {index}",
                    application,
                )
        else:
            content_layout.addWidget(
                QLabel("No scholarship application is recorded for this applicant.")
            )
        content_layout.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        root.addWidget(buttons)

    @staticmethod
    def _add_section(parent_layout, title, values):
        section = QWidget()
        layout = QFormLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(20)
        layout.setVerticalSpacing(6)

        heading = QLabel(title)
        heading.setStyleSheet(
            "color: #1D4ED8; font-size: 11pt; font-weight: 700;"
        )
        parent_layout.addWidget(heading)
        for key, value in values.items():
            field = QLabel(_display_value(value))
            field.setWordWrap(True)
            field.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            layout.addRow(QLabel(_label(key)), field)
        parent_layout.addWidget(section)


def show_applicant_details(parent, applicant_id):
    dialog = ApplicantDetailsDialog(applicant_id, parent=parent)
    dialog.exec()
