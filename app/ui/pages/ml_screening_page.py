
import json

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QMessageBox,
    QHeaderView,
)

from app.repositories.application_repository import ApplicationRepository
from app.repositories.screening_result_repository import (
    ScreeningResultRepository,
)
from app.services.screening_persistence_service import (
    ScreeningPersistenceService,
)


class MLScreeningPageMixin:
    def create_ml_screening_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)

        title = QLabel("ML Screening")
        title.setObjectName("page_title")

        description = QLabel(
            "Applications are screened automatically the first time this "
            "page opens during a run. The table shows the factors used by "
            "the model and the latest advisory result. This is not an "
            "official decision."
        )
        description.setObjectName("muted")
        description.setWordWrap(True)

        button_row = QHBoxLayout()

        refresh_button = QPushButton("Refresh Applications")
        refresh_button.setObjectName("action_button")
        refresh_button.clicked.connect(
            self.refresh_ml_screening_applications
        )

        rescreen_button = QPushButton("Re-screen All Applications")
        rescreen_button.setObjectName("action_button")
        rescreen_button.clicked.connect(self.rescreen_all_applications)

        button_row.addWidget(refresh_button)
        button_row.addWidget(rescreen_button)
        button_row.addStretch()

        self.ml_screening_columns = [
            ("Application ID", "application_id"),
            ("Applicant ID", "applicant_id"),
            ("Program", "scholarship_program"),
            ("Year", "scholarship_year"),
            ("Status", "status"),
            ("Academic Average", "academic_average"),
            ("Monthly Income", "monthly_income"),
            ("Household Size", "household"),
            ("Children", "children_count"),
            ("Seniors", "senior_count"),
            ("PWDs", "pwd_count"),
            ("Dependent", "dependent"),
            ("Solo Parent", "solo_parent"),
            ("Exam Score", "exam_display"),
            ("Exam %", "exam_percentage"),
            ("Exam Passed", "exam_passed_display"),
            ("MSWDO Threshold", "mswd_threshold"),
            ("MSWDO Eligible", "mswd_eligible"),
            ("4Ps", "four_ps_beneficiary"),
            ("SPES", "spes_beneficiary"),
            ("Scholars in Family", "scholars_in_family"),
            ("ML Prediction", "model_prediction"),
            ("Advisory Result", "predicted_class"),
            ("Qualified Probability", "confidence_display"),
            ("Review Notes", "reasons_display"),
            ("Last Screened", "screened_at"),
        ]

        self.ml_screening_table = QTableWidget()
        self.ml_screening_table.setColumnCount(
            len(self.ml_screening_columns)
        )
        self.ml_screening_table.setHorizontalHeaderLabels(
            [label for label, _key in self.ml_screening_columns]
        )

        self.configure_table(self.ml_screening_table)
        self.ml_screening_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.ml_screening_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.ml_screening_table.setWordWrap(False)
        self.ml_screening_table.setHorizontalScrollMode(
            QTableWidget.ScrollMode.ScrollPerPixel
        )
        self.ml_screening_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.ml_screening_table.horizontalHeader().setStretchLastSection(
            False
        )

        self.ml_screening_result = QLabel(
            "Opening this page will load active applications and screen them."
        )
        self.ml_screening_result.setWordWrap(True)
        self.ml_screening_result.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.ml_screening_result.setStyleSheet(
            "background: white; border: 1px solid #E2E8F0; "
            "border-radius: 8px; padding: 12px;"
        )

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addLayout(button_row)
        layout.addWidget(self.ml_screening_table, 1)
        layout.addWidget(self.ml_screening_result)

        return page

    @staticmethod
    def _as_bool_display(value):
        if value is None or value == "":
            return "Not provided"

        if isinstance(value, str):
            normalized = value.strip().lower()

            if normalized in ("1", "true", "yes"):
                return "Yes"

            if normalized in ("0", "false", "no"):
                return "No"

        return "Yes" if bool(value) else "No"

    @staticmethod
    def _format_money(value):
        if value is None or value == "":
            return "Not provided"

        try:
            return f"₱{float(value):,.2f}"
        except (TypeError, ValueError):
            return str(value)

    @staticmethod
    def _format_number(value, suffix=""):
        if value is None or value == "":
            return "Not provided"

        try:
            return f"{float(value):,.2f}{suffix}"
        except (TypeError, ValueError):
            return str(value)

    def _screen_application_record(self, application, service):
        application_id = int(application["application_id"])
        applicant_data = self._build_screening_input(application)

        return service.screen_application(
            application_id=application_id,
            applicant_data=applicant_data,
            screened_by=None,
        )

    def _run_screening_for_all(self, force_rescreen=False):
        """Screen active applications and report individual failures."""
        try:
            applications = ApplicationRepository.get_all()

            if not applications:
                self.ml_screening_table.setRowCount(0)
                self.ml_screening_result.setText(
                    "No active applications were found."
                )
                return

            service = ScreeningPersistenceService()
            completed = 0
            failures = []

            for application in applications:
                application_id = int(application["application_id"])

                try:
                    existing = self._ml_current_results.get(
                        application_id
                    )

                    if (
                        not force_rescreen
                        and existing
                        and existing.get("model_version_id")
                        == service.model_version_id
                    ):
                        continue

                    result = self._screen_application_record(
                        application,
                        service,
                    )

                    self._ml_current_results[application_id] = {
                        "screening_id": result["screening_id"],
                        "model_version_id": result["model_version_id"],
                        "predicted_class": result["predicted_class"],
                        "model_prediction": result["model_prediction"],
                        "confidence_score": (
                            result["model_probability_percent"] / 100.0
                        ),
                        "model_probability_percent": (
                            result["model_probability_percent"]
                        ),
                        "mswd_threshold": result["mswd_threshold"],
                        "mswd_eligible": result["mswd_eligible"],
                        "exam_percentage": result["exam_percentage"],
                        "exam_passed": result["exam_passed"],
                        "reasons": result.get("reasons", []),
                        "screened_at": "Just screened",
                    }

                    completed += 1

                except Exception as error:
                    failures.append(
                        f"Application {application_id}: {error}"
                    )

            self._populate_ml_screening_table(applications)

            summary = (
                f"Loaded {len(applications)} active application(s). "
                f"New screenings saved: {completed}."
            )

            if failures:
                summary += (
                    "\n\nSome applications could not be screened:\n"
                    + "\n".join(failures[:8])
                )

                if len(failures) > 8:
                    summary += (
                        f"\n…and {len(failures) - 8} more."
                    )

            self.ml_screening_result.setText(summary)

        except Exception as error:
            self.show_error("ML Screening", error)

    def refresh_ml_screening_applications(self):
        """Load active applications and their latest screening results."""
        try:
            applications = ApplicationRepository.get_all()

            if not applications:
                self.ml_screening_table.setRowCount(0)
                self.ml_screening_result.setText(
                    "No active applications were found."
                )
                return

            latest_results = (
                ScreeningResultRepository.get_latest_for_applications(
                    [
                        int(application["application_id"])
                        for application in applications
                    ]
                )
            )

            for application_id, result in latest_results.items():
                if application_id not in self._ml_current_results:
                    self._ml_current_results[application_id] = result

            # Screen every application automatically on the first visit
            # during this application session.
            if not self._ml_auto_screen_done:
                self._ml_auto_screen_done = True
                self._run_screening_for_all(force_rescreen=True)
                return

            # On later refreshes, screen applications that do not have
            # a cached result for the currently registered model version.
            self._run_screening_for_all(force_rescreen=False)

        except Exception as error:
            self.show_error("ML Screening", error)

    def rescreen_all_applications(self):
        answer = QMessageBox.question(
            self,
            "Re-screen All Applications",
            "This will run screening again for every active application "
            "and save new screening records. Continue?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        self._run_screening_for_all(force_rescreen=True)

    def _populate_ml_screening_table(self, applications):
        self.ml_screening_table.setSortingEnabled(False)
        self.ml_screening_table.setRowCount(len(applications))

        for row, application in enumerate(applications):
            application_id = int(application["application_id"])
            saved = self._ml_current_results.get(
                application_id,
                {},
            )

            raw_score = application.get("exam_raw_score")
            total_items = application.get("exam_total_items")
            stored_exam_score = application.get("exam_score")

            if (
                raw_score is not None
                and total_items not in (None, 0, "0", "")
            ):
                exam_display = f"{raw_score}/{total_items}"

                try:
                    exam_percentage = (
                        float(raw_score) / float(total_items) * 100
                    )
                except (TypeError, ValueError, ZeroDivisionError):
                    exam_percentage = None

            elif stored_exam_score is not None:
                exam_display = (
                    f"{stored_exam_score}/100 (stored percentage)"
                )

                try:
                    exam_percentage = float(stored_exam_score)
                except (TypeError, ValueError):
                    exam_percentage = None

            else:
                exam_display = "Not provided"
                exam_percentage = None

            reasons = saved.get("reasons", [])

            if isinstance(reasons, str):
                try:
                    parsed = json.loads(reasons)
                    reasons = (
                        parsed.get("reasons", [])
                        if isinstance(parsed, dict)
                        else parsed
                    )
                except (ValueError, TypeError):
                    reasons = [reasons] if reasons else []

            reasons_display = (
                "; ".join(str(reason) for reason in reasons)
                if reasons
                else "No rule reasons recorded"
            )

            values = {
                "application_id": application_id,
                "applicant_id": application.get("applicant_id"),
                "scholarship_program": application.get(
                    "scholarship_program"
                ),
                "scholarship_year": application.get(
                    "scholarship_year"
                ),
                "status": application.get("status"),
                "academic_average": self._format_number(
                    application.get("academic_average"),
                    "%",
                ),
                "monthly_income": self._format_money(
                    application.get("monthly_income")
                ),
                "household": application.get("household"),
                "children_count": application.get(
                    "children_count",
                    0,
                ),
                "senior_count": application.get("senior_count", 0),
                "pwd_count": application.get("pwd_count", 0),
                "dependent": self._as_bool_display(
                    application.get("dependent")
                ),
                "solo_parent": self._as_bool_display(
                    application.get("solo_parent")
                ),
                "exam_display": exam_display,
                "exam_percentage": self._format_number(
                    saved.get("exam_percentage", exam_percentage),
                    "%",
                ),
                "exam_passed_display": self._as_bool_display(
                    saved.get(
                        "exam_passed",
                        application.get("exam_passed"),
                    )
                ),
                "mswd_threshold": self._format_money(
                    saved.get("mswd_threshold")
                ),
                "mswd_eligible": self._as_bool_display(
                    saved.get(
                        "mswd_eligible",
                        application.get("mswdo_poverty_eligible"),
                    )
                ),
                "four_ps_beneficiary": self._as_bool_display(
                    application.get("four_ps_beneficiary")
                ),
                "spes_beneficiary": self._as_bool_display(
                    application.get("spes_beneficiary")
                ),
                "scholars_in_family": application.get(
                    "scholars_in_family",
                    0,
                ),
                "model_prediction": saved.get(
                    "model_prediction",
                    "Not screened",
                ),
                "predicted_class": saved.get(
                    "predicted_class",
                    "Not screened",
                ),
                "confidence_display": self._format_number(
                    saved.get("model_probability_percent"),
                    "%",
                ),
                "reasons_display": reasons_display,
                "screened_at": saved.get(
                    "screened_at",
                    "Not screened",
                ),
            }

            for column, (_label, key) in enumerate(
                self.ml_screening_columns
            ):
                self.set_table_item(
                    self.ml_screening_table,
                    row,
                    column,
                    values.get(key),
                )

        self.ml_screening_table.setSortingEnabled(True)

    def screen_selected_application(self):
        row = self.ml_screening_table.currentRow()

        if row < 0:
            QMessageBox.warning(
                self,
                "No Application Selected",
                "Select an application first.",
            )
            return

        item = self.ml_screening_table.item(row, 0)

        if item is None:
            QMessageBox.warning(
                self,
                "Invalid Selection",
                "Could not read the application ID.",
            )
            return

        application_id = int(item.text())
        application = ApplicationRepository.get_by_id(
            application_id
        )

        if application is None:
            QMessageBox.warning(
                self,
                "Application Not Found",
                "Refresh the list and try again.",
            )
            return

        answer = QMessageBox.question(
            self,
            "Screen Selected Application",
            f"Run screening for application {application_id}? "
            "A new screening record will be saved.",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            service = ScreeningPersistenceService()
            result = self._screen_application_record(
                application,
                service,
            )

            self._ml_current_results[application_id] = {
                "screening_id": result["screening_id"],
                "model_version_id": result["model_version_id"],
                "predicted_class": result["predicted_class"],
                "model_prediction": result["model_prediction"],
                "confidence_score": (
                    result["model_probability_percent"] / 100.0
                ),
                "model_probability_percent": (
                    result["model_probability_percent"]
                ),
                "mswd_threshold": result["mswd_threshold"],
                "mswd_eligible": result["mswd_eligible"],
                "exam_percentage": result["exam_percentage"],
                "exam_passed": result["exam_passed"],
                "reasons": result.get("reasons", []),
                "screened_at": "Just screened",
            }

            self._populate_ml_screening_table(
                ApplicationRepository.get_all()
            )

            self.ml_screening_result.setText(
                f"Screening saved for application {application_id}. "
                f"Advisory: {result['predicted_class']}; "
                f"qualified-class probability: "
                f"{result['model_probability_percent']:.2f}%. "
                "Human review is required."
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "ML Screening Failed",
                f"Could not screen application {application_id}.\n\n"
                f"{error}",
            )

    @staticmethod
    def _build_screening_input(application):
        """Map stored application fields to the ML screening inputs."""

        def number(field, default=None):
            value = application.get(field, default)

            if value is None or value == "":
                return default

            return float(value)

        average = number("academic_average")
        income = number("monthly_income")
        household = number("household")

        if average is None or income is None or household is None:
            raise ValueError(
                "Missing academic average, monthly income, "
                "or household size."
            )

        raw_score = application.get("exam_raw_score")
        total_items = application.get("exam_total_items")

        if (
            raw_score is not None
            and total_items not in (None, 0, "0", "")
        ):
            exam_score = int(float(raw_score))
            exam_total = int(float(total_items))

        else:
            stored_score = application.get("exam_score")

            if stored_score is None:
                raise ValueError(
                    "No exam score is recorded for this application."
                )

            exam_score = int(round(float(stored_score)))
            exam_total = 100

        dependent_value = application.get("dependents_count")

        if dependent_value is None:
            dependent_value = int(
                bool(application.get("dependent", False))
            )

        return {
            "average": float(average),
            "income": float(income),
            "household": int(household),
            "children": int(application.get("children_count") or 0),
            "seniors": int(application.get("senior_count") or 0),
            "pwds": int(application.get("pwd_count") or 0),
            "dependents": int(dependent_value or 0),
            "solo": int(bool(application.get("solo_parent", False))),
            "exam_score": exam_score,
            "exam_total": exam_total,
            "exam_passed": int(
                bool(application.get("exam_passed", False))
            ),
            "fourps": int(
                bool(application.get("four_ps_beneficiary", False))
            ),
            "spes": int(
                bool(application.get("spes_beneficiary", False))
            ),
            "scholars": int(
                application.get("scholars_in_family") or 0
            ),
        }
