import datetime
import os
import tempfile

from PyQt6.QtCore import QPointF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFontDatabase, QPainter, QPen, QPixmap, QPolygonF
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from app.repositories.applicant_repository import ApplicantRepository
from app.repositories.application_repository import ApplicationRepository
from app.ui.applicant_details_dialog import show_applicant_details


# ---------------------------------------------------------------- palette
NAVY = "#172554"
BLUE_900 = "#1E3A8A"
BLUE_700 = "#1D4ED8"
BLUE_600 = "#2563EB"
BLUE_300 = "#93C5FD"
BLUE_100 = "#DBEAFE"
BLUE_50 = "#EFF6FF"
BORDER = "#E2E8F0"
MUTED = "#64748B"
ROW_LINE = "#EEF2F7"

PAGE_SIZE = 12

# (tab label, statuses it covers) — None means "all"
STAGE_TABS = [
    ("All applications", None),
    ("New", {"NEW"}),
    ("Under review", {"UNDER_REVIEW"}),
    ("For interview", {"FOR_INTERVIEW"}),
    ("Interviewed", {"INTERVIEWED"}),
    ("Decided", {"DECIDED", "APPROVED", "REJECTED"}),
]

BADGE_STYLES = {
    "NEW": ("#F1F5F9", "#475569"),
    "UNDER_REVIEW": ("#FEF3C7", "#92400E"),
    "FOR_INTERVIEW": (BLUE_100, BLUE_900),
    "INTERVIEWED": ("#E2E8F0", "#334155"),
    "APPROVED": ("#DCFCE7", "#166534"),
    "REJECTED": ("#FEE2E2", "#991B1B"),
    "DECIDED": ("#E0E7FF", "#3730A3"),
}


def _font_family():
    """Inter (as in the mockup) if installed, otherwise Segoe UI."""
    return "Inter" if "Inter" in QFontDatabase.families() else "Segoe UI"


def _chevron_path():
    """Small down-arrow icon for combo boxes, drawn once into the temp dir."""
    path = os.path.join(tempfile.gettempdir(), "lydo_chevron_down.png")
    try:
        if not os.path.exists(path):
            pixmap = QPixmap(24, 24)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            pen = QPen(QColor(MUTED))
            pen.setWidthF(2.2)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.drawPolyline(QPolygonF([
                QPointF(7, 9.5), QPointF(12, 14.5), QPointF(17, 9.5),
            ]))
            painter.end()
            pixmap.save(path)
        return path.replace("\\", "/")
    except Exception:
        return ""


def _applications_qss():
    chevron = _chevron_path()
    arrow = (
        f"QComboBox::down-arrow {{ image: url({chevron}); width: 12px; height: 12px; }}"
        if chevron
        else ""
    )
    return f"""
QWidget {{ font-family: "{_font_family()}"; }}
QLabel {{ background: transparent; color: {NAVY}; }}
QLabel#page_title {{ font-size: 21pt; font-weight: 700; color: {NAVY}; }}
QLabel#muted {{ color: {MUTED}; }}
QLabel#small_muted {{ color: {MUTED}; font-size: 8pt; }}
QLabel#guide_title {{ color: {NAVY}; font-size: 8pt; font-weight: 600; }}
QLabel#empty_state {{ color: {MUTED}; font-size: 10pt; }}

QPushButton#primary_button {{
    background: {BLUE_600}; color: white; border: none;
    border-radius: 8px; padding: 0 18px; font-weight: 600;
}}
QPushButton#primary_button:hover {{ background: {BLUE_700}; }}

QPushButton#outline_button {{
    background: white; color: {NAVY}; border: 1px solid {BORDER};
    border-radius: 8px; padding: 0 16px; font-weight: 600;
}}
QPushButton#outline_button:hover {{ background: {BLUE_50}; border-color: {BLUE_300}; }}

QPushButton#tab_button {{
    background: transparent; border: none; border-bottom: 2px solid transparent;
    color: {MUTED}; padding: 8px 2px; margin-right: 18px; font-weight: 500;
}}
QPushButton#tab_button:hover {{ color: {BLUE_700}; }}
QPushButton#tab_button:checked {{
    color: {BLUE_600}; border-bottom: 2px solid {BLUE_600}; font-weight: 600;
}}
QFrame#tab_line, QFrame#divider {{ background: {BORDER}; border: none; }}

QLineEdit#applications_search {{
    background: white; border: 1px solid {BORDER}; border-radius: 8px;
    padding: 0 12px; color: {NAVY};
}}
QLineEdit#applications_search:focus {{ border: 1px solid {BLUE_600}; }}

QComboBox {{
    background: white; border: 1px solid {BORDER}; border-radius: 8px;
    padding: 0 34px 0 12px; color: {NAVY}; min-width: 120px;
}}
QComboBox:hover {{ background: {BLUE_50}; border-color: {BLUE_300}; }}
QComboBox:focus {{ border: 1px solid {BLUE_600}; }}
QComboBox::drop-down {{
    subcontrol-origin: padding; subcontrol-position: center right;
    width: 28px; border: none;
}}
{arrow}
QComboBox QAbstractItemView {{
    background: white; color: {NAVY}; border: 1px solid {BORDER};
    padding: 4px; outline: 0;
    selection-background-color: {BLUE_100}; selection-color: {NAVY};
}}

QFrame#panel {{
    background: white; border: 1px solid {BORDER}; border-radius: 10px;
}}

QTableWidget {{
    background: white; border: none; gridline-color: transparent;
    color: {NAVY}; selection-background-color: {BLUE_100};
    selection-color: {NAVY}; outline: 0;
}}
QTableWidget::item {{ border-bottom: 1px solid {ROW_LINE}; padding-left: 12px; }}
QTableWidget::item:hover {{ background: {BLUE_50}; }}
QTableWidget::item:selected {{ background: {BLUE_100}; color: {NAVY}; }}
QHeaderView::section {{
    background: {BLUE_50}; color: {MUTED}; border: none;
    padding: 10px 12px; font-size: 8pt; font-weight: 600;
}}

QPushButton#pager, QPushButton#pager_current {{
    border: none; border-radius: 6px; min-width: 26px; max-width: 26px;
    min-height: 26px; max-height: 26px; padding: 0; font-size: 8.5pt;
}}
QPushButton#pager {{ background: transparent; color: {MUTED}; }}
QPushButton#pager:hover {{ background: {BLUE_50}; color: {BLUE_700}; }}
QPushButton#pager:disabled {{ color: #CBD5E1; }}
QPushButton#pager_current {{
    background: {BLUE_100}; color: {BLUE_900}; font-weight: 600;
}}
"""


def _status_text(status):
    return str(status).replace("_", " ").capitalize() if status else "—"


def _format_year(year):
    return str(year).replace("-", "–") if year else "—"


def _format_average(value):
    try:
        return f"{float(value):.1f}"
    except (TypeError, ValueError):
        return "—" if value in (None, "") else str(value)


def _short_year():
    return str(datetime.date.today().year)[2:]


def _display_application_id(raw):
    try:
        return f"APP-{_short_year()}-{int(raw):03d}"
    except (TypeError, ValueError):
        return str(raw) if raw not in (None, "") else "—"


def _display_applicant_id(raw):
    try:
        return f"LY-{_short_year()}-{int(raw):03d}"
    except (TypeError, ValueError):
        return str(raw) if raw not in (None, "") else "—"


class _ApplicationsPage(QWidget):
    """Page widget that tells the mixin the first time it is shown."""

    first_shown = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._announced = False

    def showEvent(self, event):
        super().showEvent(event)
        if not self._announced:
            self._announced = True
            self.first_shown.emit()


class ApplicationsPageMixin:
    # ------------------------------------------------------------------
    # Page
    # ------------------------------------------------------------------
    def create_applications_page(self):
        self._applications_stage = 0
        self._applications_year_ready = False
        self._applications_records = []
        self._applications_page_rows = []
        self._applications_loaded = False
        self._applications_page_index = 0

        page = _ApplicationsPage()
        page.setStyleSheet(_applications_qss())
        page.first_shown.connect(self._applications_on_first_shown)

        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # Header ---------------------------------------------------------
        header = QHBoxLayout()

        heading = QVBoxLayout()
        heading.setSpacing(2)

        title = QLabel("Applications")
        title.setObjectName("page_title")

        description = QLabel(
            "Follow each scholarship application from submission to "
            "official decision."
        )
        description.setObjectName("muted")

        heading.addWidget(title)
        heading.addWidget(description)

        refresh_button = QPushButton("⟳  Refresh")
        refresh_button.setObjectName("outline_button")
        refresh_button.setFixedHeight(38)
        refresh_button.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_button.clicked.connect(self.refresh_applications)

        new_button = QPushButton("+  New application")
        new_button.setObjectName("primary_button")
        new_button.setFixedHeight(38)
        new_button.setCursor(Qt.CursorShape.PointingHandCursor)
        new_button.clicked.connect(self._new_application)

        header.addLayout(heading)
        header.addStretch()
        header.addWidget(
            refresh_button, alignment=Qt.AlignmentFlag.AlignTop
        )
        header.addWidget(new_button, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(header)

        # Stage tabs -------------------------------------------------------
        tabs = QHBoxLayout()
        tabs.setSpacing(0)
        self.application_tabs = []
        for index, (label, _statuses) in enumerate(STAGE_TABS):
            tab = QPushButton(f"{label}  0")
            tab.setObjectName("tab_button")
            tab.setCheckable(True)
            tab.setCursor(Qt.CursorShape.PointingHandCursor)
            tab.clicked.connect(
                lambda _checked, i=index: self._set_application_stage(i)
            )
            self.application_tabs.append(tab)
            tabs.addWidget(tab)
        self.application_tabs[0].setChecked(True)
        tabs.addStretch()

        tab_line = QFrame()
        tab_line.setObjectName("tab_line")
        tab_line.setFixedHeight(1)

        tab_box = QVBoxLayout()
        tab_box.setSpacing(0)
        tab_box.addLayout(tabs)
        tab_box.addWidget(tab_line)
        layout.addLayout(tab_box)

        # Filters ----------------------------------------------------------
        filters = QHBoxLayout()
        filters.setSpacing(10)

        self.application_search = QLineEdit()
        self.application_search.setObjectName("applications_search")
        self.application_search.setPlaceholderText(
            "🔍  Search application ID or applicant"
        )
        self.application_search.setFixedHeight(38)
        self.application_search.setMinimumWidth(320)
        self.application_search.setMaximumWidth(380)
        self.application_search.setClearButtonEnabled(True)
        self.application_search.textChanged.connect(
            self._applications_filters_changed
        )

        self.program_filter = QComboBox()
        self.program_filter.setFixedHeight(38)
        self.program_filter.setCursor(Qt.CursorShape.PointingHandCursor)
        self.program_filter.addItem("All programs", None)

        self.year_filter = QComboBox()
        self.year_filter.setFixedHeight(38)
        self.year_filter.setCursor(Qt.CursorShape.PointingHandCursor)
        self.year_filter.addItem("All years", None)

        self.program_filter.currentIndexChanged.connect(
            self._applications_filters_changed
        )
        self.year_filter.currentIndexChanged.connect(
            self._applications_filters_changed
        )

        filters.addWidget(self.application_search)
        filters.addStretch()
        filters.addWidget(self.program_filter)
        filters.addWidget(self.year_filter)
        layout.addLayout(filters)

        # Table panel --------------------------------------------------------
        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)

        self.applications_table = QTableWidget()
        self.applications_table.setColumnCount(7)
        self.applications_table.setHorizontalHeaderLabels([
            "APPLICATION ID",
            "APPLICANT ID",
            "APPLICANT",
            "PROGRAM",
            "YEAR",
            "AVERAGE",
            "STATUS OF SCHOLAR",
        ])
        self.configure_table(self.applications_table)
        self._style_applications_table()
        self.applications_table.cellClicked.connect(
            self._application_cell_clicked
        )
        self.applications_panel_layout = panel_layout
        panel_layout.addWidget(self.applications_table, 1)

        self.applications_empty = QLabel("")
        self.applications_empty.setObjectName("empty_state")
        self.applications_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.applications_empty.setWordWrap(True)
        self.applications_empty.hide()
        panel_layout.addWidget(self.applications_empty, 1)

        line = QFrame()
        line.setObjectName("divider")
        line.setFixedHeight(1)
        panel_layout.addWidget(line)

        foot = QHBoxLayout()
        foot.setContentsMargins(18, 10, 18, 10)
        self.applications_footer = QLabel("")
        self.applications_footer.setObjectName("small_muted")
        foot.addWidget(self.applications_footer)
        foot.addStretch()
        self.applications_pager = QHBoxLayout()
        self.applications_pager.setSpacing(4)
        foot.addLayout(self.applications_pager)
        panel_layout.addLayout(foot)

        layout.addWidget(panel, 1)

        # Status guide -----------------------------------------------------------
        guide = QHBoxLayout()
        guide.setContentsMargins(6, 0, 0, 0)
        guide.setSpacing(16)
        guide_title = QLabel("Status guide")
        guide_title.setObjectName("guide_title")
        guide_text = QLabel(
            "New → Under review → For interview → Interviewed → "
            "Approved / Rejected. Only authorized officials record final "
            "scholarship decisions."
        )
        guide_text.setObjectName("small_muted")
        guide_text.setWordWrap(True)
        guide.addWidget(guide_title)
        guide.addWidget(guide_text, 1)
        layout.addLayout(guide)

        # Page footer ----------------------------------------------------------
        page_footer = QHBoxLayout()
        left = QLabel(
            "Fictional records for demonstration only. "
            "Authorized LYDO personnel access."
        )
        left.setObjectName("small_muted")
        right = QLabel("Santa Cruz, Laguna · LYDO")
        right.setObjectName("small_muted")
        page_footer.addWidget(left)
        page_footer.addStretch()
        page_footer.addWidget(right)
        layout.addLayout(page_footer)

        self._rebuild_applications_pager(1, 1)
        return page

    def _applications_on_first_shown(self):
        # Load data the first time the page appears, in case the main window
        # does not call refresh_applications itself.
        if not self._applications_loaded:
            self.refresh_applications()

    def _style_applications_table(self):
        table = self.applications_table
        table.setAlternatingRowColors(False)
        table.setShowGrid(False)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.setWordWrap(False)
        table.setMouseTracking(True)
        table.setMinimumHeight(320)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        table.setVerticalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel
        )
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(44)
        table.horizontalHeader().setFixedHeight(38)
        table.horizontalHeader().setHighlightSections(False)
        table.horizontalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        header = table.horizontalHeader()
        fixed = QHeaderView.ResizeMode.Fixed
        stretch = QHeaderView.ResizeMode.Stretch

        for column, mode, width in (
            (0, fixed, 150),
            (1, fixed, 130),
            (2, stretch, None),
            (3, stretch, None),
            (4, fixed, 110),
            (5, fixed, 100),
            (6, fixed, 170),
        ):
            header.setSectionResizeMode(column, mode)
            if width:
                table.setColumnWidth(column, width)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _new_application(self):
        # Applications are created together with their applicant,
        # so this opens the same registration form as the Applicants page.
        opener = getattr(self, "open_applicant_form", None)
        if opener is not None:
            opener()

    def _set_application_stage(self, index):
        self._applications_stage = index
        self._applications_page_index = 0
        for i, tab in enumerate(self.application_tabs):
            tab.setChecked(i == index)
        self._render_applications()

    def _applications_filters_changed(self, *_):
        # Search and filters work on the records already loaded, so typing
        # does not query the database again.
        self._applications_page_index = 0
        self._render_applications()

    def _go_to_applications_page(self, index):
        self._applications_page_index = index
        self._render_applications()

    # ------------------------------------------------------------------
    # Row widgets
    # ------------------------------------------------------------------
    def _make_application_badge(self, status):
        background, color = BADGE_STYLES.get(
            status, ("#F1F5F9", "#475569")
        )

        holder = QWidget()
        holder.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )
        layout = QHBoxLayout(holder)
        layout.setContentsMargins(8, 0, 8, 0)

        badge = QLabel(_status_text(status))
        badge.setStyleSheet(
            f"background: {background}; color: {color};"
            "border-radius: 4px; padding: 3px 10px;"
            "font-size: 8pt; font-weight: 600;"
        )
        layout.addWidget(badge, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addStretch()
        return holder

    def _application_cell_clicked(self, row, _column):
        if row < 0 or row >= len(self._applications_page_rows):
            return
        applicant_id = self._applications_page_rows[row].get("applicant_id_raw")
        if applicant_id is None:
            return
        try:
            show_applicant_details(self, int(applicant_id))
        except Exception as error:
            self.show_error("Applicant details", error)

    def _rebuild_applications_pager(self, current, pages):
        layout = self.applications_pager
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        def add(text, target, name="pager", enabled=True):
            button = QPushButton(text)
            button.setObjectName(name)
            button.setEnabled(enabled)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(
                lambda _checked, t=target: self._go_to_applications_page(t)
            )
            layout.addWidget(button)

        add("‹", current - 1, enabled=current > 0)

        first = max(0, min(current - 2, pages - 5))
        last = min(pages, first + 5)
        for index in range(first, last):
            add(
                str(index + 1),
                index,
                "pager_current" if index == current else "pager",
            )

        add("›", current + 1, enabled=current < pages - 1)

    # ------------------------------------------------------------------
    # Load + render
    # ------------------------------------------------------------------
    def _update_application_filters(self, records):
        programs = sorted({
            r["program"] for r in records if r["program"] != "—"
        })
        years = sorted(
            {r["year_raw"] for r in records if r["year_raw"]}, reverse=True
        )

        current_program = self.program_filter.currentData()
        current_year = self.year_filter.currentData()

        self.program_filter.blockSignals(True)
        self.year_filter.blockSignals(True)

        self.program_filter.clear()
        self.program_filter.addItem("All programs", None)
        for program in programs:
            self.program_filter.addItem(program, program)
        self.program_filter.setCurrentIndex(
            max(self.program_filter.findData(current_program), 0)
        )

        self.year_filter.clear()
        self.year_filter.addItem("All years", None)
        for year in years:
            self.year_filter.addItem(_format_year(year), year)

        if not self._applications_year_ready and years:
            # first load: show the latest scholarship year, like the design
            self.year_filter.setCurrentIndex(1)
            self._applications_year_ready = True
        else:
            self.year_filter.setCurrentIndex(
                max(self.year_filter.findData(current_year), 0)
            )

        self.program_filter.blockSignals(False)
        self.year_filter.blockSignals(False)

    def refresh_applications(self, *_):
        """Reload applications from the database and redraw the page."""
        try:
            applications = ApplicationRepository.get_all()

            names = {}
            for applicant in ApplicantRepository.get_all():
                names[applicant.get("applicant_id")] = (
                    f"{applicant.get('first_name') or ''} "
                    f"{applicant.get('last_name') or ''}"
                ).strip()

            records = []
            for item in applications:
                applicant_id = item.get("applicant_id")
                records.append({
                    "application_id_raw": item.get("application_id"),
                    "applicant_id_raw": applicant_id,
                    "id": _display_application_id(
                        item.get("application_id")
                    ),
                    "applicant_id": _display_applicant_id(applicant_id),
                    "name": names.get(applicant_id) or "—",
                    "program": item.get("scholarship_program") or "—",
                    "year_raw": item.get("scholarship_year"),
                    "average": _format_average(
                        item.get("academic_average")
                    ),
                    "status": item.get("status"),
                })

            self._applications_records = records
            self._applications_loaded = True
            self._update_application_filters(records)
            self._render_applications()

        except Exception as error:
            self.show_error("Applications", error)

    def _render_applications(self):
        try:
            records = self._applications_records

            keyword = self.application_search.text().strip().lower()
            program = self.program_filter.currentData()
            year = self.year_filter.currentData()

            # everything except the stage tab (so tab counts stay useful)
            scoped = []
            for record in records:
                if program and record["program"] != program:
                    continue
                if year and record["year_raw"] != year:
                    continue
                if keyword and keyword not in " ".join(
                    str(record[k])
                    for k in ("id", "applicant_id", "name")
                ).lower():
                    continue
                scoped.append(record)

            for tab, (label, statuses) in zip(
                self.application_tabs, STAGE_TABS
            ):
                count = (
                    len(scoped)
                    if statuses is None
                    else sum(r["status"] in statuses for r in scoped)
                )
                tab.setText(f"{label}  {count}")

            _label, statuses = STAGE_TABS[self._applications_stage]
            shown = [
                r for r in scoped
                if statuses is None or r["status"] in statuses
            ]

            pages = max(1, -(-len(shown) // PAGE_SIZE))
            self._applications_page_index = min(
                self._applications_page_index, pages - 1
            )
            start = self._applications_page_index * PAGE_SIZE
            page_rows = shown[start:start + PAGE_SIZE]
            self._applications_page_rows = page_rows

            table = self.applications_table
            table.clearSelection()
            table.setRowCount(len(page_rows))

            for row, record in enumerate(page_rows):
                for column, value in enumerate((
                    record["id"],
                    record["applicant_id"],
                    record["name"],
                    record["program"],
                    _format_year(record["year_raw"]),
                    record["average"],
                )):
                    self.set_table_item(table, row, column, value)

                self.set_table_item(table, row, 6, "")
                table.setCellWidget(
                    row, 6, self._make_application_badge(record["status"])
                )

            # Empty state: keep the header, replace the blank body with a note.
            panel_layout = self.applications_panel_layout
            if page_rows:
                table.setMinimumHeight(320)
                table.setMaximumHeight(16777215)
                panel_layout.setStretchFactor(table, 1)
                panel_layout.setStretchFactor(self.applications_empty, 0)
                self.applications_empty.hide()
            else:
                # Table shrinks to just its header; the note takes the rest.
                table.setMinimumHeight(0)
                table.setMaximumHeight(40)
                panel_layout.setStretchFactor(table, 0)
                panel_layout.setStretchFactor(self.applications_empty, 1)
                if not records:
                    self.applications_empty.setText(
                        "No applications have been recorded yet."
                    )
                else:
                    self.applications_empty.setText(
                        "No applications match the current filters."
                    )
                self.applications_empty.show()

            year_text = (
                f"Scholarship year {_format_year(year)}"
                if year
                else "All scholarship years"
            )
            if len(shown) > PAGE_SIZE:
                summary = (
                    f"Showing {start + 1}–{start + len(page_rows)} "
                    f"of {len(shown)} applications"
                )
            else:
                summary = (
                    f"Showing {len(page_rows)} of {len(records)} applications"
                )
            self.applications_footer.setText(f"{summary} · {year_text}")
            self._rebuild_applications_pager(
                self._applications_page_index, pages
            )

        except Exception as error:
            self.show_error("Applications", error)