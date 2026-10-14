
import re

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QDialogButtonBox,
    QFrame,
    QGroupBox,
    QScrollArea,
    QCheckBox,
    QSpinBox,
    QDoubleSpinBox,
    QMessageBox,
)


class UnifiedRegistrationForm(QDialog):
    """Combined applicant registration and scholarship application form."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("New Scholarship Registration")
        self.setMinimumSize(760, 720)
        self.resize(850, 820)
        self.setModal(True)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(20, 18, 20, 18)
        outer_layout.setSpacing(12)

        title = QLabel("New Scholarship Registration")
        title.setStyleSheet(
            "font-size: 19pt; font-weight: bold; color: #172554;"
        )

        subtitle = QLabel(
            "Complete both sections below. The applicant and application "
            "will be saved together."
        )
        subtitle.setObjectName("muted")
        subtitle.setWordWrap(True)

        outer_layout.addWidget(title)
        outer_layout.addWidget(subtitle)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(2, 2, 8, 2)
        content_layout.setSpacing(14)

        # ============================================================
        # PART A — APPLICANT INFORMATION
        # ============================================================

        applicant_group = QGroupBox("Part A — Applicant Information")
        applicant_form = QFormLayout(applicant_group)
        applicant_form.setSpacing(9)

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
        self.email.setPlaceholderText("Enter email address")

        self.phone = QLineEdit()
        self.phone.setPlaceholderText("Enter phone number")

        self.house_no_street = QLineEdit()
        self.house_no_street.setPlaceholderText(
            "Enter house number and street"
        )

        self.barangay = QLineEdit()
        self.municipality = QLineEdit("Santa Cruz")
        self.province = QLineEdit("Laguna")

        applicant_form.addRow("First Name *", self.first_name)
        applicant_form.addRow("Middle Name", self.middle_name)
        applicant_form.addRow("Last Name *", self.last_name)
        applicant_form.addRow("Suffix", self.suffix)
        applicant_form.addRow("Birth Date *", self.birth_date)
        applicant_form.addRow("Sex *", self.sex)
        applicant_form.addRow("Email *", self.email)
        applicant_form.addRow("Phone *", self.phone)
        applicant_form.addRow("House No./Street *", self.house_no_street)
        applicant_form.addRow("Barangay *", self.barangay)
        applicant_form.addRow("Municipality *", self.municipality)
        applicant_form.addRow("Province *", self.province)

        content_layout.addWidget(applicant_group)

        # ============================================================
        # PART B — SCHOLARSHIP APPLICATION
        # ============================================================

        application_group = QGroupBox(
            "Part B — Scholarship Application"
        )
        application_form = QFormLayout(application_group)
        application_form.setSpacing(9)

        # Scholarship program is no longer entered by the user.
        # The database requires a program value, so use the system's
        # existing default program label.
        self.scholarship_year = QSpinBox()
        self.scholarship_year.setRange(2000, 2200)
        self.scholarship_year.setValue(QDate.currentDate().year())

        self.academic_average = QDoubleSpinBox()
        self.academic_average.setRange(0, 100)
        self.academic_average.setDecimals(2)
        self.academic_average.setSingleStep(0.25)

        self.monthly_income = QDoubleSpinBox()
        self.monthly_income.setRange(0, 999999999)
        self.monthly_income.setDecimals(2)
        self.monthly_income.setSingleStep(500)

        self.mswdo_poverty_eligible = QCheckBox(
            "Calculated automatically"
        )
        self.mswdo_poverty_eligible.setEnabled(False)

        self.household = QSpinBox()
        self.household.setRange(1, 1000)
        self.household.setValue(1)

        self.children_count = QSpinBox()
        self.children_count.setRange(0, 1000)
        self.children_count.setValue(0)

        self.senior_count = QSpinBox()
        self.senior_count.setRange(0, 1000)
        self.senior_count.setValue(0)

        self.pwd_count = QSpinBox()
        self.pwd_count.setRange(0, 1000)
        self.pwd_count.setValue(0)

        self.solo_parent = QCheckBox("Yes")

        self.dependents_count = QSpinBox()
        self.dependents_count.setRange(0, 1000)
        self.dependents_count.setValue(0)

        # At least one exam item must be specified.
        self.exam_total_items = QSpinBox()
        self.exam_total_items.setRange(1, 1000)
        self.exam_total_items.setValue(1)

        self.exam_raw_score = QSpinBox()
        self.exam_raw_score.setRange(0, 1)
        self.exam_raw_score.setValue(0)

        self.exam_passed = QCheckBox("Calculated automatically")
        self.exam_passed.setEnabled(False)

        self.four_ps_beneficiary = QCheckBox("Yes")
        self.spes_beneficiary = QCheckBox("Yes")

        self.scholars_in_family = QSpinBox()
        self.scholars_in_family.setRange(0, 1000)
        self.scholars_in_family.setValue(0)

        self.previous_scholarship = QCheckBox("Yes")

        application_form.addRow(
            "Scholarship Year *", self.scholarship_year
        )
        application_form.addRow(
            "Academic Average (0–100) *", self.academic_average
        )
        application_form.addRow(
            "Monthly Household Income (₱) *", self.monthly_income
        )
        application_form.addRow(
            "MSWDO Poverty Eligibility", self.mswdo_poverty_eligible
        )
        application_form.addRow(
            "Household Size *", self.household
        )
        application_form.addRow(
            "Children Count *", self.children_count
        )
        application_form.addRow(
            "Senior Count *", self.senior_count
        )
        application_form.addRow(
            "PWD Count *", self.pwd_count
        )
        application_form.addRow(
            "Solo Parent", self.solo_parent
        )
        application_form.addRow(
            "Number of Dependents *", self.dependents_count
        )
        application_form.addRow(
            "Exam Total Items *", self.exam_total_items
        )
        application_form.addRow(
            "Raw Exam Score *", self.exam_raw_score
        )
        application_form.addRow(
            "Exam Status", self.exam_passed
        )
        application_form.addRow(
            "4Ps Beneficiary", self.four_ps_beneficiary
        )
        application_form.addRow(
            "SPES Beneficiary", self.spes_beneficiary
        )
        application_form.addRow(
            "Scholars in Family", self.scholars_in_family
        )
        application_form.addRow(
            "Previous Scholarship", self.previous_scholarship
        )

        # Residency has been removed from the visible form.

        content_layout.addWidget(application_group)

        # Update derived values whenever relevant input changes.
        for widget in (
            self.monthly_income,
            self.household,
            self.children_count,
            self.senior_count,
            self.pwd_count,
        ):
            widget.valueChanged.connect(
                self._update_mswdo_eligibility
            )

        self.exam_total_items.valueChanged.connect(
            self._update_exam_controls
        )
        self.exam_raw_score.valueChanged.connect(
            self._update_exam_controls
        )

        self._update_mswdo_eligibility()
        self._update_exam_controls()

        note = QLabel(
            "* Required fields. Enter the information from the "
            "applicant's supporting documents. Enter 0 for counts "
            "that do not apply."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)

        content_layout.addWidget(note)

        scroll.setWidget(content)
        outer_layout.addWidget(scroll, 1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.button(
            QDialogButtonBox.StandardButton.Save
        ).setText("Save Applicant and Application")

        buttons.accepted.connect(self.validate_form)
        buttons.rejected.connect(self.reject)

        outer_layout.addWidget(buttons)

        self.setStyleSheet("""
            QDialog {
                background-color: #F4F7FB;
                color: #1F2937;
                font-family: Segoe UI;
                font-size: 10pt;
            }

            QGroupBox {
                background: white;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                margin-top: 10px;
                padding: 12px;
                font-weight: bold;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 5px;
                color: #172554;
            }

            QLineEdit, QComboBox, QDateEdit,
            QSpinBox, QDoubleSpinBox {
                background: white;
                border: 1px solid #CBD5E1;
                border-radius: 5px;
                padding: 6px;
                min-height: 22px;
            }

            QLineEdit:focus, QComboBox:focus,
            QDateEdit:focus, QSpinBox:focus,
            QDoubleSpinBox:focus {
                border: 1px solid #2563EB;
            }

            QPushButton {
                padding: 8px 12px;
            }
        """)

    # ================================================================
    # AUTOMATIC MSWDO ELIGIBILITY
    # ================================================================

    def _mswdo_threshold(self):
        household = self.household.value()
        children = self.children_count.value()
        seniors = self.senior_count.value()
        pwds = self.pwd_count.value()

        return (
            max(15000, 4000 * household)
            + 2000 * children
            + 2000 * seniors
            + 2500 * pwds
        )

    def _update_mswdo_eligibility(self, *_):
        threshold = self._mswdo_threshold()
        eligible = self.monthly_income.value() <= threshold

        self.mswdo_poverty_eligible.setChecked(eligible)
        self.mswdo_poverty_eligible.setText(
            f"{'Yes' if eligible else 'No'} — "
            f"threshold ₱{threshold:,.2f}"
        )

    # ================================================================
    # AUTOMATIC EXAM CALCULATION
    # ================================================================

    def _update_exam_controls(self, *_):
        total = self.exam_total_items.value()

        self.exam_raw_score.setMaximum(total)

        if self.exam_raw_score.value() > total:
            self.exam_raw_score.setValue(total)

        score = self.exam_raw_score.value()
        passed = score >= 0.8 * total

        self.exam_passed.setChecked(passed)
        self.exam_passed.setText(
            f"{'Passed' if passed else 'Failed'} "
            f"({score}/{total}; {score / total * 100:.1f}%)"
        )

    # ================================================================
    # VALIDATION
    # ================================================================

    def validate_form(self):
        required_text_fields = [
            (self.first_name, "First name"),
            (self.last_name, "Last name"),
            (self.email, "Email"),
            (self.phone, "Phone"),
            (self.house_no_street, "House number/street"),
            (self.barangay, "Barangay"),
            (self.municipality, "Municipality"),
            (self.province, "Province"),
        ]

        for field, label in required_text_fields:
            if not field.text().strip():
                QMessageBox.warning(
                    self,
                    "Validation Error",
                    f"{label} is required.",
                )
                field.setFocus()
                return

        if self.birth_date.date() == self.birth_date.minimumDate():
            QMessageBox.warning(
                self,
                "Validation Error",
                "Birth date is required. Please select the applicant's "
                "actual birth date.",
            )
            self.birth_date.setFocus()
            return

        if self.sex.currentIndex() == 0:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please select the applicant's sex.",
            )
            self.sex.setFocus()
            return

        email = self.email.text().strip()

        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please enter a valid email address.",
            )
            self.email.setFocus()
            return

        if self.academic_average.value() <= 0:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Academic average must be greater than 0.",
            )
            self.academic_average.setFocus()
            return

        special_counts = (
            self.children_count.value()
            + self.senior_count.value()
            + self.pwd_count.value()
        )

        if special_counts > self.household.value():
            QMessageBox.warning(
                self,
                "Validation Error",
                "Children, seniors, and PWD counts cannot exceed "
                "household size.",
            )
            return

        if self.dependents_count.value() > self.household.value():
            QMessageBox.warning(
                self,
                "Validation Error",
                "Number of dependents cannot exceed household size.",
            )
            self.dependents_count.setFocus()
            return

        if self.exam_total_items.value() < 1:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Exam total items must be at least 1.",
            )
            self.exam_total_items.setFocus()
            return

        if not (
            0 <= self.exam_raw_score.value()
            <= self.exam_total_items.value()
        ):
            QMessageBox.warning(
                self,
                "Validation Error",
                "Raw exam score must be between 0 and the total exam items.",
            )
            self.exam_raw_score.setFocus()
            return

        self.accept()

    # ================================================================
    # APPLICANT DATA
    # ================================================================

    def get_applicant_data(self):
        selected_date = self.birth_date.date().toString("yyyy-MM-dd")
        selected_sex = self.sex.currentText()

        return {
            "first_name": self.first_name.text().strip(),
            "middle_name": self.middle_name.text().strip() or None,
            "last_name": self.last_name.text().strip(),
            "suffix": self.suffix.text().strip() or None,
            "birth_date": selected_date,
            "sex": selected_sex,
            "email": self.email.text().strip(),
            "phone": self.phone.text().strip(),
            "house_no_street": self.house_no_street.text().strip(),
            "barangay": self.barangay.text().strip(),
            "municipality": self.municipality.text().strip(),
            "province": self.province.text().strip(),
        }

    # ================================================================
    # SCHOLARSHIP APPLICATION DATA
    # ================================================================

    def get_application_data(self):
        total_items = self.exam_total_items.value()
        raw_score = self.exam_raw_score.value()

        exam_percentage = round(
            raw_score / total_items * 100,
            2,
        )

        return {
            # The program field remains in the database schema even
            # though it is no longer shown in the registration form.
            "scholarship_program": "LYDO",
            "scholarship_year": self.scholarship_year.value(),
            "academic_average": self.academic_average.value(),
            "monthly_income": self.monthly_income.value(),
            "mswdo_poverty_eligible": (
                self.mswdo_poverty_eligible.isChecked()
            ),
            "household": self.household.value(),
            "children_count": self.children_count.value(),
            "senior_count": self.senior_count.value(),
            "pwd_count": self.pwd_count.value(),
            "solo_parent": self.solo_parent.isChecked(),
            "dependent": self.dependents_count.value() > 0,
            "dependents_count": self.dependents_count.value(),
            "exam_score": exam_percentage,
            "exam_raw_score": raw_score,
            "exam_total_items": total_items,
            "exam_passed": raw_score >= 0.8 * total_items,
            "four_ps_beneficiary": (
                self.four_ps_beneficiary.isChecked()
            ),
            "spes_beneficiary": self.spes_beneficiary.isChecked(),
            "scholars_in_family": self.scholars_in_family.value(),
            # Residency is no longer collected through the UI.
            "residency": None,
            "previous_scholarship": (
                self.previous_scholarship.isChecked()
            ),
            "status": "DRAFT",
            "submitted_at": None,
        }
