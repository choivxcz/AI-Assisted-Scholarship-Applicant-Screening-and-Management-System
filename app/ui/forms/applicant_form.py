import re

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QLineEdit, QComboBox,
    QDateEdit, QDialogButtonBox, QMessageBox,
)


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

