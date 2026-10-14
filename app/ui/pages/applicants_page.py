
from PyQt6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QMessageBox,
    QLineEdit,
)

from app.repositories.applicant_repository import ApplicantRepository
from app.services.application_service import ApplicationService
from app.ui.forms.applicant_form import ApplicantForm
from app.ui.forms.unified_registration_form import UnifiedRegistrationForm


class ApplicantsPageMixin:
    def create_applicants_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)

        title = QLabel("Applicants")
        title.setObjectName("page_title")

        description = QLabel(
            "Search, register, edit, and archive applicant records."
        )
        description.setObjectName("muted")

        self.applicant_search = QLineEdit()
        self.applicant_search.setPlaceholderText(
            "Search by applicant ID or name..."
        )
        self.applicant_search.textChanged.connect(
            self.refresh_applicants
        )

        button_layout = QHBoxLayout()

        add_button = QPushButton("+ New Scholarship Registration")
        add_button.setObjectName("action_button")
        add_button.clicked.connect(self.open_applicant_form)

        edit_button = QPushButton("Edit Selected")
        edit_button.setObjectName("action_button")
        edit_button.clicked.connect(self.edit_selected_applicant)

        archive_button = QPushButton("Archive Selected")
        archive_button.setObjectName("danger_button")
        archive_button.clicked.connect(self.archive_selected_applicant)

        refresh_button = QPushButton("Refresh")
        refresh_button.setObjectName("action_button")
        refresh_button.clicked.connect(self.refresh_applicants)

        for button in (
            add_button,
            edit_button,
            archive_button,
            refresh_button,
        ):
            button_layout.addWidget(button)

        button_layout.addStretch()

        self.applicants_table = QTableWidget()
        self.applicants_table.setColumnCount(5)
        self.applicants_table.setHorizontalHeaderLabels([
            "ID",
            "First Name",
            "Last Name",
            "Barangay",
            "Phone",
        ])
        self.configure_table(self.applicants_table)

        self.applicants_table.itemDoubleClicked.connect(
            lambda item: self.edit_selected_applicant()
        )

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(self.applicant_search)
        layout.addLayout(button_layout)
        layout.addWidget(self.applicants_table)

        return page

    def open_applicant_form(self):
        dialog = UnifiedRegistrationForm(parent=self)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            applicant_id, application_id = (
                ApplicationService.register_applicant_with_application(
                    applicant_data=dialog.get_applicant_data(),
                    application_data=dialog.get_application_data(),
                )
            )

            QMessageBox.information(
                self,
                "Registration Successful",
                "Applicant and scholarship application saved successfully!\n\n"
                f"Applicant ID: {applicant_id}\n"
                f"Application ID: {application_id}",
            )

            self.refresh_applicants()
            self.refresh_applications()
            self.refresh_dashboard()

        except Exception as error:
            QMessageBox.critical(
                self,
                "Registration Failed",
                "Could not save the applicant and application.\n\n"
                f"{error}",
            )

    def refresh_applicants(self):
        try:
            keyword = self.applicant_search.text().strip()

            if keyword:
                applicants = ApplicantRepository.search(keyword)
            else:
                applicants = ApplicantRepository.get_all()

            self.applicants_table.setRowCount(len(applicants))

            for row, applicant in enumerate(applicants):
                values = [
                    applicant.get("applicant_id"),
                    applicant.get("first_name"),
                    applicant.get("last_name"),
                    applicant.get("barangay"),
                    applicant.get("phone"),
                ]

                for column, value in enumerate(values):
                    self.set_table_item(
                        self.applicants_table,
                        row,
                        column,
                        value,
                    )

        except Exception as error:
            self.show_error("Applicants", error)

    def get_selected_applicant_id(self):
        row = self.applicants_table.currentRow()

        if row < 0:
            QMessageBox.warning(
                self,
                "No Applicant Selected",
                "Please select an applicant from the table first.",
            )
            return None

        item = self.applicants_table.item(row, 0)

        if item is None:
            return None

        try:
            return int(item.text())
        except ValueError:
            QMessageBox.warning(
                self,
                "Invalid Selection",
                "Could not read applicant ID.",
            )
            return None

    def edit_selected_applicant(self):
        applicant_id = self.get_selected_applicant_id()

        if applicant_id is None:
            return

        try:
            applicant = ApplicantRepository.get_by_id(applicant_id)

            if applicant is None:
                QMessageBox.warning(
                    self,
                    "Applicant Not Found",
                    "This applicant is no longer in the active list.",
                )
                self.refresh_applicants()
                return

            dialog = ApplicantForm(
                applicant=applicant,
                parent=self,
            )

            if dialog.exec() != QDialog.DialogCode.Accepted:
                return

            updated = ApplicantRepository.update(
                applicant_id,
                **dialog.get_data(),
            )

            if updated:
                QMessageBox.information(
                    self,
                    "Update Successful",
                    "Applicant information has been updated.",
                )
            else:
                QMessageBox.information(
                    self,
                    "No Changes",
                    "No database changes were detected.",
                )

            self.refresh_applicants()
            self.refresh_dashboard()

        except Exception as error:
            QMessageBox.critical(
                self,
                "Update Failed",
                f"Could not update applicant.\n\n{error}",
            )

    def archive_selected_applicant(self):
        applicant_id = self.get_selected_applicant_id()

        if applicant_id is None:
            return

        try:
            applicant = ApplicantRepository.get_by_id(applicant_id)

            if applicant is None:
                QMessageBox.warning(
                    self,
                    "Applicant Not Found",
                    "This applicant is no longer in the active list.",
                )
                self.refresh_applicants()
                return

            full_name = (
                f"{applicant['first_name']} {applicant['last_name']}"
            )

            answer = QMessageBox.question(
                self,
                "Confirm Archive",
                f"Archive applicant {full_name} (ID: {applicant_id})?\n\n"
                "The applicant and all associated applications will be "
                "archived. Records will be hidden from active lists, "
                "not permanently deleted.",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if answer != QMessageBox.StandardButton.Yes:
                return

            archived = ApplicantRepository.archive(applicant_id)

            if archived:
                QMessageBox.information(
                    self,
                    "Archive Successful",
                    f"{full_name} has been archived.",
                )
            else:
                QMessageBox.information(
                    self,
                    "Not Archived",
                    "The applicant may already be archived.",
                )

            self.refresh_applicants()
            self.refresh_applications()
            self.refresh_dashboard()

        except Exception as error:
            QMessageBox.critical(
                self,
                "Archive Failed",
                f"Could not archive applicant.\n\n{error}",
            )
