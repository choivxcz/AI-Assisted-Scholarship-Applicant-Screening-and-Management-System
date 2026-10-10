
import re

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import (
    QMainWindow,
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QFrame,
    QHeaderView,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QDialogButtonBox,
)

from app.repositories.applicant_repository import ApplicantRepository
from app.repositories.application_repository import ApplicationRepository


# ============================================================
# APPLICANT FORM: REGISTER AND EDIT
# ============================================================

class ApplicantForm(QDialog):
    def __init__(self, applicant=None, parent=None):
        super().__init__(parent)

        self.applicant = applicant
        self.is_editing = applicant is not None

        self.setWindowTitle(
            "Edit Applicant" if self.is_editing else "Register New Applicant"
        )
        self.setMinimumWidth(480)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = QLabel(
            "Edit Applicant" if self.is_editing else "Register Applicant"
        )
        title.setStyleSheet(
            "font-size: 18pt; font-weight: bold; color: #172554;"
        )
        layout.addWidget(title)

        description = QLabel(
            "Update the applicant's information."
            if self.is_editing
            else "Enter the applicant's personal information."
        )
        description.setObjectName("muted")
        layout.addWidget(description)

        form = QFormLayout()
        form.setSpacing(10)

        self.first_name = QLineEdit()
        self.middle_name = QLineEdit()
        self.last_name = QLineEdit()
        self.suffix = QLineEdit()

        self.birth_date = QDateEdit()
        self.birth_date.setCalendarPopup(True)
        self.birth_date.setDisplayFormat("yyyy-MM-dd")
        self.birth_date.setMinimumDate(QDate(1900, 1, 1))
        self.birth_date.setMaximumDate(QDate.currentDate())
        self.birth_date.setSpecialValueText("Not specified")
        self.birth_date.setDate(self.birth_date.minimumDate())

        self.sex = QComboBox()
        self.sex.addItems([
            "Not specified",
            "MALE",
            "FEMALE",
            "OTHER",
            "PREFER_NOT_TO_SAY",
        ])

        self.email = QLineEdit()
        self.phone = QLineEdit()
        self.house_no_street = QLineEdit()
        self.barangay = QLineEdit()
        self.municipality = QLineEdit("Santa Cruz")
        self.province = QLineEdit("Laguna")

        form.addRow("First Name *", self.first_name)
        form.addRow("Middle Name", self.middle_name)
        form.addRow("Last Name *", self.last_name)
        form.addRow("Suffix", self.suffix)
        form.addRow("Birth Date", self.birth_date)
        form.addRow("Sex", self.sex)
        form.addRow("Email", self.email)
        form.addRow("Phone", self.phone)
        form.addRow("House No./Street", self.house_no_street)
        form.addRow("Barangay *", self.barangay)
        form.addRow("Municipality *", self.municipality)
        form.addRow("Province *", self.province)

        layout.addLayout(form)

        note = QLabel("* Required fields")
        note.setObjectName("muted")
        layout.addWidget(note)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(
            QDialogButtonBox.StandardButton.Save
        ).setText("Save Changes" if self.is_editing else "Register Applicant")

        buttons.accepted.connect(self.validate_form)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setStyleSheet("""
            QDialog {
                background-color: #F4F7FB;
                color: #1F2937;
                font-family: Segoe UI;
                font-size: 10pt;
            }
            QLineEdit, QComboBox, QDateEdit {
                background-color: white;
                border: 1px solid #CBD5E1;
                border-radius: 5px;
                padding: 7px;
                min-height: 22px;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
                border: 1px solid #2563EB;
            }
            QPushButton {
                padding: 8px 12px;
            }
        """)

        if self.is_editing:
            self.populate_form()

    def populate_form(self):
        data = self.applicant

        self.first_name.setText(data.get("first_name") or "")
        self.middle_name.setText(data.get("middle_name") or "")
        self.last_name.setText(data.get("last_name") or "")
        self.suffix.setText(data.get("suffix") or "")
        self.email.setText(data.get("email") or "")
        self.phone.setText(data.get("phone") or "")
        self.house_no_street.setText(data.get("house_no_street") or "")
        self.barangay.setText(data.get("barangay") or "")
        self.municipality.setText(data.get("municipality") or "Santa Cruz")
        self.province.setText(data.get("province") or "Laguna")

        current_sex = data.get("sex")
        if current_sex:
            index = self.sex.findText(current_sex)
            if index >= 0:
                self.sex.setCurrentIndex(index)

        birth_date = data.get("birth_date")
        if birth_date:
            date_text = (
                birth_date.strftime("%Y-%m-%d")
                if hasattr(birth_date, "strftime")
                else str(birth_date)[:10]
            )
            parsed_date = QDate.fromString(date_text, "yyyy-MM-dd")
            if parsed_date.isValid():
                self.birth_date.setDate(parsed_date)

    def validate_form(self):
        required_fields = [
            (self.first_name, "First name"),
            (self.last_name, "Last name"),
            (self.barangay, "Barangay"),
            (self.municipality, "Municipality"),
            (self.province, "Province"),
        ]

        for field, label in required_fields:
            if not field.text().strip():
                QMessageBox.warning(
                    self,
                    "Validation Error",
                    f"{label} is required.",
                )
                field.setFocus()
                return

        email = self.email.text().strip()
        if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please enter a valid email address.",
            )
            self.email.setFocus()
            return

        self.accept()

    def get_data(self):
        selected_sex = self.sex.currentText()

        selected_date = None
        if self.birth_date.date() != self.birth_date.minimumDate():
            selected_date = self.birth_date.date().toString("yyyy-MM-dd")

        return {
            "first_name": self.first_name.text().strip(),
            "middle_name": self.middle_name.text().strip() or None,
            "last_name": self.last_name.text().strip(),
            "suffix": self.suffix.text().strip() or None,
            "birth_date": selected_date,
            "sex": None if selected_sex == "Not specified" else selected_sex,
            "email": self.email.text().strip() or None,
            "phone": self.phone.text().strip() or None,
            "house_no_street": self.house_no_street.text().strip() or None,
            "barangay": self.barangay.text().strip(),
            "municipality": self.municipality.text().strip(),
            "province": self.province.text().strip(),
        }


# ============================================================
# MAIN WINDOW
# ============================================================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "Iskolar ng Bayan | Scholarship Management System"
        )
        self.resize(1250, 780)
        self.setMinimumSize(950, 600)

        self.nav_buttons = []
        self.pages = QStackedWidget()

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
        self.pages.addWidget(self.create_placeholder_page(
            "ML Screening",
            "Machine-learning screening results will appear here.",
        ))
        self.pages.addWidget(self.create_placeholder_page(
            "Interviews",
            "Interview scheduling and records will appear here.",
        ))
        self.pages.addWidget(self.create_placeholder_page(
            "Scholarship Decisions",
            "Recommendations and official decisions will appear here.",
        ))

        content_layout.addWidget(self.pages)
        root_layout.addWidget(content, 1)
        self.setCentralWidget(root)

        self.navigate(0)
        self.refresh_all()

    # --------------------------------------------------------
    # SIDEBAR
    # --------------------------------------------------------

    def create_sidebar(self):
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(235)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 24, 16, 20)
        layout.setSpacing(8)

        brand = QLabel("Iskolar ng Bayan")
        brand.setObjectName("brand")
        subtitle = QLabel("LYDO Scholarship System")
        subtitle.setObjectName("sidebar_subtitle")

        layout.addWidget(brand)
        layout.addWidget(subtitle)
        layout.addSpacing(28)

        for label, index in [
            ("Dashboard", 0),
            ("Applicants", 1),
            ("Applications", 2),
            ("ML Screening", 3),
            ("Interviews", 4),
            ("Scholarship Decisions", 5),
        ]:
            button = QPushButton(label)
            button.setObjectName("nav_button")
            button.setCheckable(True)
            button.clicked.connect(
                lambda checked=False, page=index: self.navigate(page)
            )
            self.nav_buttons.append(button)
            layout.addWidget(button)

        layout.addStretch()

        footer = QLabel(
            "Local Youth Development Office\nSanta Cruz, Laguna"
        )
        footer.setObjectName("sidebar_subtitle")
        footer.setWordWrap(True)
        layout.addWidget(footer)

        return sidebar

    # --------------------------------------------------------
    # DASHBOARD
    # --------------------------------------------------------

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
        self.application_count = self.create_stat_card("Total Applications")
        self.review_count = self.create_stat_card("Under Review")
        self.interview_count = self.create_stat_card("For Interview")

        for card in [
            self.applicant_count,
            self.application_count,
            self.review_count,
            self.interview_count,
        ]:
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
        panel_layout.addWidget(refresh_button, alignment=Qt.AlignmentFlag.AlignLeft)

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

    # --------------------------------------------------------
    # APPLICANTS PAGE
    # --------------------------------------------------------

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
            "Search by applicant ID, name, email, or phone..."
        )
        self.applicant_search.textChanged.connect(self.refresh_applicants)

        button_layout = QHBoxLayout()

        add_button = QPushButton("+ Register Applicant")
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

        for button in [
            add_button, edit_button, archive_button, refresh_button
        ]:
            button_layout.addWidget(button)

        button_layout.addStretch()

        self.applicants_table = QTableWidget()
        self.applicants_table.setColumnCount(5)
        self.applicants_table.setHorizontalHeaderLabels([
            "ID", "First Name", "Last Name", "Barangay", "Phone"
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

    # --------------------------------------------------------
    # APPLICATIONS PAGE
    # --------------------------------------------------------

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
            "Application ID", "Applicant ID", "Program",
            "Year", "Average", "Status"
        ])
        self.configure_table(self.applications_table)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(refresh_button, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.applications_table)

        return page

    def create_placeholder_page(self, title_text, description_text):
        page = QWidget()
        layout = QVBoxLayout(page)

        title = QLabel(title_text)
        title.setObjectName("page_title")
        description = QLabel(description_text)
        description.setObjectName("muted")
        description.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addStretch()
        return page

    # --------------------------------------------------------
    # TABLE HELPERS
    # --------------------------------------------------------

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
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        table.setItem(row, column, item)

    def navigate(self, index):
        self.pages.setCurrentIndex(index)

        for i, button in enumerate(self.nav_buttons):
            button.setChecked(i == index)

        if index == 0:
            self.refresh_dashboard()
        elif index == 1:
            self.refresh_applicants()
        elif index == 2:
            self.refresh_applications()

    # --------------------------------------------------------
    # REGISTER APPLICANT
    # --------------------------------------------------------

    def open_applicant_form(self):
        dialog = ApplicantForm(parent=self)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            applicant_id = ApplicantRepository.create(**dialog.get_data())

            QMessageBox.information(
                self,
                "Registration Successful",
                f"Applicant registered successfully!\n\n"
                f"Applicant ID: {applicant_id}",
            )

            self.refresh_applicants()
            self.refresh_dashboard()

        except Exception as error:
            QMessageBox.critical(
                self,
                "Registration Failed",
                f"Could not register applicant.\n\n{error}",
            )

    # --------------------------------------------------------
    # SEARCH AND REFRESH APPLICANTS
    # --------------------------------------------------------

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
                    applicant["applicant_id"],
                    applicant["first_name"],
                    applicant["last_name"],
                    applicant["barangay"],
                    applicant["phone"],
                ]

                for column, value in enumerate(values):
                    self.set_table_item(
                        self.applicants_table, row, column, value
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
                self, "Invalid Selection", "Could not read applicant ID."
            )
            return None

    # --------------------------------------------------------
    # EDIT APPLICANT
    # --------------------------------------------------------

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

            dialog = ApplicantForm(applicant=applicant, parent=self)

            if dialog.exec() != QDialog.DialogCode.Accepted:
                return

            updated = ApplicantRepository.update(
                applicant_id, **dialog.get_data()
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

    # --------------------------------------------------------
    # ARCHIVE APPLICANT
    # --------------------------------------------------------

    def archive_selected_applicant(self):
        applicant_id = self.get_selected_applicant_id()

        if applicant_id is None:
            return

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
            "The record will be hidden from active applicant lists. "
            "It will not be permanently deleted.",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
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
            self.refresh_dashboard()

        except Exception as error:
            QMessageBox.critical(
                self,
                "Archive Failed",
                f"Could not archive applicant.\n\n{error}",
            )

    # --------------------------------------------------------
    # REFRESH DASHBOARD AND APPLICATIONS
    # --------------------------------------------------------

    def refresh_dashboard(self):
        try:
            applicants = ApplicantRepository.get_all()
            applications = ApplicationRepository.get_all()

            self.applicant_count.value_label.setText(str(len(applicants)))
            self.application_count.value_label.setText(str(len(applications)))
            self.review_count.value_label.setText(
                str(sum(
                    item["status"] == "UNDER_REVIEW"
                    for item in applications
                ))
            )
            self.interview_count.value_label.setText(
                str(sum(
                    item["status"] == "FOR_INTERVIEW"
                    for item in applications
                ))
            )

        except Exception as error:
            self.show_error("Dashboard", error)

    def refresh_applications(self):
        try:
            applications = ApplicationRepository.get_all()
            self.applications_table.setRowCount(len(applications))

            for row, application in enumerate(applications):
                values = [
                    application["application_id"],
                    application["applicant_id"],
                    application["scholarship_program"],
                    application["scholarship_year"],
                    application["academic_average"],
                    application["status"],
                ]

                for column, value in enumerate(values):
                    self.set_table_item(
                        self.applications_table, row, column, value
                    )

        except Exception as error:
            self.show_error("Applications", error)

    def refresh_all(self):
        self.refresh_dashboard()
        self.refresh_applicants()
        self.refresh_applications()

    # --------------------------------------------------------
    # ERROR HANDLING
    # --------------------------------------------------------

    def show_error(self, context, error):
        QMessageBox.warning(
            self,
            f"{context} Error",
            f"Could not load {context.lower()} data.\n\n{error}",
        )
