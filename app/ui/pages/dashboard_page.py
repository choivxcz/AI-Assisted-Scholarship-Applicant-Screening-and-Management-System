
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
)

from app.repositories.applicant_repository import ApplicantRepository
from app.repositories.application_repository import ApplicationRepository


class DashboardPageMixin:
    def create_dashboard(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(18)

        title = QLabel("Dashboard")
        title.setObjectName("page_title")

        description = QLabel(
            "Overview of applicants and scholarship applications."
        )
        description.setObjectName("muted")

        layout.addWidget(title)
        layout.addWidget(description)

        cards = QHBoxLayout()
        cards.setSpacing(14)

        self.applicant_count = self.create_stat_card(
            "Total Active Applicants"
        )
        self.application_count = self.create_stat_card(
            "Total Applications"
        )
        self.review_count = self.create_stat_card("Under Review")
        self.interview_count = self.create_stat_card("For Interview")

        for card in (
            self.applicant_count,
            self.application_count,
            self.review_count,
            self.interview_count,
        ):
            cards.addWidget(card)

        layout.addLayout(cards)

        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)

        panel_title = QLabel("Welcome to Iskolar ng Bayan")
        panel_title.setStyleSheet(
            "font-size: 15pt; font-weight: bold; color: #172554;"
        )

        panel_description = QLabel(
            "Manage applicants, scholarship applications, screening, "
            "interviews, and scholarship decisions."
        )
        panel_description.setWordWrap(True)
        panel_description.setObjectName("muted")

        refresh_button = QPushButton("Refresh Dashboard")
        refresh_button.setObjectName("action_button")
        refresh_button.clicked.connect(self.refresh_all)

        panel_layout.addWidget(panel_title)
        panel_layout.addWidget(panel_description)
        panel_layout.addWidget(
            refresh_button,
            alignment=Qt.AlignmentFlag.AlignLeft,
        )

        layout.addWidget(panel)
        layout.addStretch()

        return page

    def create_stat_card(self, label_text):
        card = QFrame()
        card.setObjectName("stat_card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)

        label = QLabel(label_text)
        label.setObjectName("stat_label")

        value = QLabel("—")
        value.setObjectName("stat_value")

        layout.addWidget(label)
        layout.addWidget(value)

        card.value_label = value
        return card

    def refresh_dashboard(self):
        try:
            applicants = ApplicantRepository.get_all()
            applications = ApplicationRepository.get_all()

            self.applicant_count.value_label.setText(
                str(len(applicants))
            )
            self.application_count.value_label.setText(
                str(len(applications))
            )
            self.review_count.value_label.setText(
                str(sum(
                    item.get("status") == "UNDER_REVIEW"
                    for item in applications
                ))
            )
            self.interview_count.value_label.setText(
                str(sum(
                    item.get("status") == "FOR_INTERVIEW"
                    for item in applications
                ))
            )

        except Exception as error:
            self.show_error("Dashboard", error)
