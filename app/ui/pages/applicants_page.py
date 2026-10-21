import datetime
import os
import tempfile

from PyQt6.QtCore import QPointF, Qt, pyqtSignal
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFontDatabase,
    QPainter,
    QPen,
    QPixmap,
    QPolygonF,
)
from PyQt6.QtWidgets import (
    QDialog,
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QLineEdit,
    QComboBox,
    QHeaderView,
    QToolButton,
    QMenu,
    QAbstractItemView,
)

from app.repositories.applicant_repository import ApplicantRepository
from app.repositories.application_repository import ApplicationRepository
from app.services.application_service import ApplicationService
from app.ui.forms.applicant_form import ApplicantForm
from app.ui.forms.unified_registration_form import UnifiedRegistrationForm
from app.ui.applicant_details_dialog import show_applicant_details


# ---------------------------------------------------------------- palette
NAVY = "#172554"
BLUE_900 = "#1E3A8A"
BLUE_600 = "#2563EB"
BLUE_700 = "#1D4ED8"
BLUE_300 = "#93C5FD"
BLUE_100 = "#DBEAFE"
BLUE_50 = "#EFF6FF"
BORDER = "#E2E8F0"
MUTED = "#64748B"
ROW_LINE = "#EEF2F7"

ID_ROLE = Qt.ItemDataRole.UserRole
NAME_ROLE = Qt.ItemDataRole.UserRole + 1

PAGE_SIZE = 12

# table columns
COL_SELECT, COL_ID, COL_NAME, COL_BARANGAY = 0, 1, 2, 3
COL_AGE_SEX, COL_PHONE, COL_STATUS, COL_ACTIONS = 4, 5, 6, 7

BADGE_STYLES = {
    "NEW": ("#F1F5F9", "#475569"),
    "UNDER_REVIEW": ("#FEF3C7", "#92400E"),
    "FOR_INTERVIEW": (BLUE_100, BLUE_900),
    "INTERVIEWED": ("#E2E8F0", "#334155"),
    "APPROVED": ("#DCFCE7", "#166534"),
    "REJECTED": ("#FEE2E2", "#991B1B"),
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


def _applicants_qss():
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
QLabel#empty_state {{ color: {MUTED}; font-size: 10pt; }}

QPushButton#primary_button {{
    background: {BLUE_600}; color: white; border: none;
    border-radius: 8px; padding: 0 18px; font-weight: 600;
}}
QPushButton#primary_button:hover {{ background: {BLUE_700}; }}

QPushButton#outline_button, QPushButton#outline_danger_button {{
    background: white; color: {NAVY}; border: 1px solid {BORDER};
    border-radius: 8px; padding: 0 14px; font-weight: 600;
}}
QPushButton#outline_button:hover {{ background: {BLUE_50}; border-color: {BLUE_300}; }}
QPushButton#outline_danger_button:hover {{
    background: #FEF2F2; border-color: #FCA5A5; color: #B91C1C;
}}
QPushButton#outline_button:disabled, QPushButton#outline_danger_button:disabled {{
    color: #94A3B8; background: #F8FAFC;
}}

QPushButton#tab_button {{
    background: transparent; border: none; border-bottom: 2px solid transparent;
    color: {MUTED}; padding: 8px 2px; margin-right: 18px; font-weight: 500;
}}
QPushButton#tab_button:hover {{ color: {BLUE_700}; }}
QPushButton#tab_button:checked {{
    color: {BLUE_600}; border-bottom: 2px solid {BLUE_600}; font-weight: 600;
}}
QFrame#tab_line {{ background: {BORDER}; border: none; }}

QLineEdit#applicant_search {{
    background: white; border: 1px solid {BORDER}; border-radius: 8px;
    padding: 0 12px; color: {NAVY};
}}
QLineEdit#applicant_search:focus {{ border: 1px solid {BLUE_600}; }}

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
QFrame#divider {{ background: {BORDER}; border: none; }}
QLabel#select_check {{ color: {BLUE_600}; font-size: 12pt; }}
QLabel#selection_text {{ color: {NAVY}; font-size: 9pt; }}

QTableWidget {{
    background: white; border: none; gridline-color: transparent;
    color: {NAVY}; selection-background-color: {BLUE_100};
    selection-color: {NAVY}; outline: 0;
}}
QTableWidget::item {{ border-bottom: 1px solid {ROW_LINE}; padding-left: 8px; }}
QTableWidget::item:hover {{ background: {BLUE_50}; }}
QTableWidget::item:selected {{ background: {BLUE_100}; color: {NAVY}; }}
QHeaderView::section {{
    background: {BLUE_50}; color: {MUTED}; border: none;
    padding: 10px 8px; font-size: 8pt; font-weight: 600;
}}

QLabel#row_avatar {{
    background: #BFDBFE; color: {BLUE_900}; border-radius: 14px;
    font-size: 7.5pt; font-weight: 700;
}}
QLabel#row_name {{ color: {NAVY}; font-weight: 500; }}

QToolButton#row_menu {{
    background: transparent; border: none; color: {MUTED};
    font-size: 12pt; font-weight: bold; padding: 2px 8px;
}}
QToolButton#row_menu:hover {{ background: {BLUE_50}; border-radius: 6px; }}
QToolButton#row_menu::menu-indicator {{ image: none; }}
QMenu {{ background: white; border: 1px solid {BORDER}; padding: 4px; }}
QMenu::item {{ padding: 7px 22px; color: {NAVY}; border-radius: 4px; }}
QMenu::item:selected {{ background: {BLUE_100}; }}

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


def _pick(item, *keys):
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return value
    return None


def _status_text(status):
    if not status:
        return "—"
    return str(status).replace("_", " ").capitalize()


def _initials(first, last):
    return (
        (str(first or "")[:1] + str(last or "")[:1]).upper() or "?"
    )


def _age(applicant):
    age = _pick(applicant, "age")
    if age is not None:
        return str(age)

    born = _pick(
        applicant, "birthdate", "birth_date", "date_of_birth", "birthday"
    )
    if born is None:
        return "—"

    try:
        if isinstance(born, str):
            born = datetime.date.fromisoformat(born[:10])
        elif isinstance(born, datetime.datetime):
            born = born.date()
        today = datetime.date.today()
        years = today.year - born.year - (
            (today.month, today.day) < (born.month, born.day)
        )
        return str(years)
    except Exception:
        return "—"


def _sex(applicant):
    sex = _pick(applicant, "sex", "gender")
    return str(sex)[:1].upper() if sex else "—"


def _mask_phone(phone):
    """Show 09•• ••• 4100 — return the number unchanged to unmask."""
    digits = str(phone or "").strip()
    if len(digits) < 6:
        return digits or "—"
    return f"{digits[:2]}•• ••• {digits[-4:]}"


def _display_id(applicant):
    code = _pick(applicant, "applicant_code")
    if code:
        return str(code)
    raw = applicant.get("applicant_id")
    try:
        return f"LY-{str(datetime.date.today().year)[2:]}-{int(raw):03d}"
    except (TypeError, ValueError):
        return str(raw)


class _ApplicantsPage(QWidget):
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


class ApplicantsPageMixin:
    # ------------------------------------------------------------------
    # Page
    # ------------------------------------------------------------------
    def create_applicants_page(self):
        self._applicants_view = "active"
        self._applicants_loaded = False
        self._applicants_active = []
        self._applicants_archived = []
        self._applicants_statuses = {}
        self._applicants_page_index = 0

        page = _ApplicantsPage()
        page.setStyleSheet(_applicants_qss())
        page.first_shown.connect(self._applicants_on_first_shown)

        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # Header ---------------------------------------------------------
        header = QHBoxLayout()

        heading = QVBoxLayout()
        heading.setSpacing(2)

        title = QLabel("Applicants")
        title.setObjectName("page_title")

        description = QLabel(
            "One secure register for your youth scholarship applicants."
        )
        description.setObjectName("muted")

        heading.addWidget(title)
        heading.addWidget(description)

        add_button = QPushButton("+  Add new applicant")
        add_button.setObjectName("primary_button")
        add_button.setFixedHeight(38)
        add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        add_button.clicked.connect(self.open_applicant_form)

        header.addLayout(heading)
        header.addStretch()
        header.addWidget(
            add_button, alignment=Qt.AlignmentFlag.AlignTop
        )
        layout.addLayout(header)

        # Tabs -----------------------------------------------------------
        tabs = QHBoxLayout()
        tabs.setSpacing(0)

        self.active_tab = QPushButton("Active applicants  0")
        self.archived_tab = QPushButton("Archived  0")
        for view, tab in (
            ("active", self.active_tab),
            ("archived", self.archived_tab),
        ):
            tab.setObjectName("tab_button")
            tab.setCheckable(True)
            tab.setCursor(Qt.CursorShape.PointingHandCursor)
            tab.clicked.connect(
                lambda _checked, v=view: self._set_applicants_view(v)
            )
            tabs.addWidget(tab)
        self.active_tab.setChecked(True)
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

        self.applicant_search = QLineEdit()
        self.applicant_search.setObjectName("applicant_search")
        self.applicant_search.setPlaceholderText(
            "🔍  Search name, applicant ID or barangay"
        )
        self.applicant_search.setFixedHeight(38)
        self.applicant_search.setMinimumWidth(320)
        self.applicant_search.setMaximumWidth(380)
        self.applicant_search.setClearButtonEnabled(True)
        self.applicant_search.textChanged.connect(
            self._applicants_filters_changed
        )

        self.barangay_filter = QComboBox()
        self.barangay_filter.setFixedHeight(38)
        self.barangay_filter.setCursor(Qt.CursorShape.PointingHandCursor)
        self.barangay_filter.addItem("All barangays")

        self.status_filter = QComboBox()
        self.status_filter.setFixedHeight(38)
        self.status_filter.setCursor(Qt.CursorShape.PointingHandCursor)
        self.status_filter.addItem("All statuses", None)

        refresh_button = QPushButton("⟳  Refresh")
        refresh_button.setObjectName("outline_button")
        refresh_button.setFixedHeight(38)
        refresh_button.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_button.clicked.connect(self.refresh_applicants)

        self.barangay_filter.currentIndexChanged.connect(
            self._applicants_filters_changed
        )
        self.status_filter.currentIndexChanged.connect(
            self._applicants_filters_changed
        )

        filters.addWidget(self.applicant_search)
        filters.addStretch()
        filters.addWidget(self.barangay_filter)
        filters.addWidget(self.status_filter)
        filters.addWidget(refresh_button)
        layout.addLayout(filters)

        # Table panel --------------------------------------------------------
        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)

        # selection bar
        bar = QHBoxLayout()
        bar.setContentsMargins(18, 10, 18, 10)
        bar.setSpacing(10)

        self.selection_check = QLabel("☐")
        self.selection_check.setObjectName("select_check")
        self.selection_label = QLabel("No applicant selected")
        self.selection_label.setObjectName("selection_text")

        self.edit_button = QPushButton("✎  Edit")
        self.edit_button.setObjectName("outline_button")
        self.edit_button.setFixedHeight(34)
        self.edit_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_button.clicked.connect(self.edit_selected_applicant)

        self.archive_button = QPushButton("▣  Archive")
        self.archive_button.setObjectName("outline_danger_button")
        self.archive_button.setFixedHeight(34)
        self.archive_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.archive_button.clicked.connect(
            self.archive_selected_applicant
        )

        bar.addWidget(self.selection_check)
        bar.addWidget(self.selection_label)
        bar.addStretch()
        bar.addWidget(self.edit_button)
        bar.addWidget(self.archive_button)
        panel_layout.addLayout(bar)

        top_line = QFrame()
        top_line.setObjectName("divider")
        top_line.setFixedHeight(1)
        panel_layout.addWidget(top_line)

        # table
        self.applicants_table = QTableWidget()
        self.applicants_table.setColumnCount(8)
        self.applicants_table.setHorizontalHeaderLabels([
            "",
            "APPLICANT ID",
            "APPLICANT",
            "BARANGAY",
            "AGE / SEX",
            "CONTACT NUMBER",
            "APPLICATION STATUS",
            "",
        ])
        self.configure_table(self.applicants_table)
        self._style_applicants_table()

        self.applicants_table.itemDoubleClicked.connect(
            lambda item: self.edit_selected_applicant()
        )
        self.applicants_table.itemSelectionChanged.connect(
            self._update_selection_bar
        )
        self.applicants_table.cellClicked.connect(
            self._applicant_cell_clicked
        )

        self.applicants_panel_layout = panel_layout
        panel_layout.addWidget(self.applicants_table, 1)

        self.applicants_empty = QLabel("")
        self.applicants_empty.setObjectName("empty_state")
        self.applicants_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.applicants_empty.setWordWrap(True)
        self.applicants_empty.hide()
        panel_layout.addWidget(self.applicants_empty, 1)

        bottom_line = QFrame()
        bottom_line.setObjectName("divider")
        bottom_line.setFixedHeight(1)
        panel_layout.addWidget(bottom_line)

        # footer inside panel
        foot = QHBoxLayout()
        foot.setContentsMargins(18, 10, 18, 10)
        self.applicants_footer = QLabel("")
        self.applicants_footer.setObjectName("small_muted")

        foot.addWidget(self.applicants_footer)
        foot.addStretch()
        self.applicants_pager = QHBoxLayout()
        self.applicants_pager.setSpacing(4)
        foot.addLayout(self.applicants_pager)
        panel_layout.addLayout(foot)

        layout.addWidget(panel, 1)

        # page footer ----------------------------------------------------------
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

        self._rebuild_applicants_pager(0, 1)
        return page

    def _applicants_on_first_shown(self):
        # Load data the first time the page appears, in case the main window
        # does not call refresh_applicants itself.
        if not self._applicants_loaded:
            self.refresh_applicants()

    def _style_applicants_table(self):
        table = self.applicants_table
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
        table.verticalHeader().setDefaultSectionSize(46)
        table.horizontalHeader().setFixedHeight(38)
        table.horizontalHeader().setHighlightSections(False)
        table.horizontalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        header = table.horizontalHeader()
        fixed = QHeaderView.ResizeMode.Fixed
        stretch = QHeaderView.ResizeMode.Stretch

        for column, mode, width in (
            (COL_SELECT, fixed, 44),
            (COL_ID, fixed, 120),
            (COL_NAME, stretch, None),
            (COL_BARANGAY, stretch, None),
            (COL_AGE_SEX, fixed, 90),
            (COL_PHONE, fixed, 140),
            (COL_STATUS, fixed, 150),
            (COL_ACTIONS, fixed, 60),
        ):
            header.setSectionResizeMode(column, mode)
            if width:
                table.setColumnWidth(column, width)

    # ------------------------------------------------------------------
    # Tabs / selection
    # ------------------------------------------------------------------
    def _set_applicants_view(self, view):
        self._applicants_view = view
        self._applicants_page_index = 0
        self.active_tab.setChecked(view == "active")
        self.archived_tab.setChecked(view == "archived")

        is_active = view == "active"
        self.edit_button.setEnabled(is_active)
        self.archive_button.setEnabled(is_active)

        # filter lists depend on which tab is showing
        self._update_filter_options(
            self._applicants_base(), self._applicants_statuses
        )
        self._render_applicants()

    def _applicants_filters_changed(self, *_):
        # Search and filters work on the records already loaded, so typing
        # does not query the database again.
        self._applicants_page_index = 0
        self._render_applicants()

    def _go_to_applicants_page(self, index):
        self._applicants_page_index = index
        self._render_applicants()

    def _update_selection_bar(self):
        table = self.applicants_table
        rows = sorted({index.row() for index in table.selectedIndexes()})

        for row in range(table.rowCount()):
            item = table.item(row, COL_SELECT)
            if item is not None:
                selected = row in rows
                item.setText("☑" if selected else "☐")
                item.setForeground(
                    QBrush(QColor(BLUE_600 if selected else MUTED))
                )

        if not rows:
            self.selection_check.setText("☐")
            self.selection_label.setText("No applicant selected")
            return

        id_item = table.item(rows[0], COL_ID)
        name = id_item.data(NAME_ROLE) if id_item else ""
        self.selection_check.setText("☑")
        self.selection_label.setText(f"{len(rows)} selected · {name}")

    def _get_archived_applicants(self):
        getter = getattr(ApplicantRepository, "get_archived", None)
        if getter is None:
            return []
        try:
            return getter()
        except Exception:
            return []

    def _rebuild_applicants_pager(self, current, pages):
        layout = self.applicants_pager
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
                lambda _checked, t=target: self._go_to_applicants_page(t)
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
    # Row widgets
    # ------------------------------------------------------------------
    def _make_name_cell(self, applicant):
        first = applicant.get("first_name")
        last = applicant.get("last_name")

        holder = QWidget()
        holder.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )
        layout = QHBoxLayout(holder)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(10)

        avatar = QLabel(_initials(first, last))
        avatar.setObjectName("row_avatar")
        avatar.setFixedSize(28, 28)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        name = QLabel(f"{first or ''} {last or ''}".strip())
        name.setObjectName("row_name")

        layout.addWidget(avatar)
        layout.addWidget(name)
        layout.addStretch()
        return holder

    def _make_status_cell(self, status):
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

    def _make_menu_cell(self, row):
        button = QToolButton()
        button.setObjectName("row_menu")
        button.setText("⋯")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        menu = QMenu(button)
        if self._applicants_view == "active":
            edit_action = menu.addAction("Edit")
            edit_action.triggered.connect(
                lambda _checked=False, r=row: self._row_action(
                    r, self.edit_selected_applicant
                )
            )
            archive_action = menu.addAction("Archive")
            archive_action.triggered.connect(
                lambda _checked=False, r=row: self._row_action(
                    r, self.archive_selected_applicant
                )
            )
        else:
            menu.addAction("No actions").setEnabled(False)

        button.setMenu(menu)

        holder = QWidget()
        layout = QHBoxLayout(holder)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignCenter)
        return holder

    def _row_action(self, row, action):
        self.applicants_table.setCurrentCell(row, COL_ID)
        self.applicants_table.selectRow(row)
        action()

    def _applicant_cell_clicked(self, row, column):
        if column == COL_ACTIONS:
            return
        item = self.applicants_table.item(row, COL_ID)
        if item is None:
            return
        applicant_id = item.data(ID_ROLE)
        if applicant_id is None:
            return
        try:
            show_applicant_details(self, int(applicant_id))
        except Exception as error:
            self.show_error("Applicant details", error)

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Load + render
    # ------------------------------------------------------------------
    def _applicants_base(self):
        if self._applicants_view == "archived":
            return self._applicants_archived
        return self._applicants_active

    def _update_filter_options(self, base, statuses):
        barangays = sorted({
            str(a.get("barangay")) for a in base if a.get("barangay")
        })
        present = sorted({
            statuses.get(a.get("applicant_id"))
            for a in base
            if statuses.get(a.get("applicant_id"))
        })

        current_barangay = self.barangay_filter.currentText()
        current_status = self.status_filter.currentData()

        self.barangay_filter.blockSignals(True)
        self.status_filter.blockSignals(True)

        self.barangay_filter.clear()
        self.barangay_filter.addItem("All barangays")
        self.barangay_filter.addItems(barangays)
        index = self.barangay_filter.findText(current_barangay)
        self.barangay_filter.setCurrentIndex(max(index, 0))

        self.status_filter.clear()
        self.status_filter.addItem("All statuses", None)
        for status in present:
            self.status_filter.addItem(_status_text(status), status)
        index = self.status_filter.findData(current_status)
        self.status_filter.setCurrentIndex(max(index, 0))

        self.barangay_filter.blockSignals(False)
        self.status_filter.blockSignals(False)

    def refresh_applicants(self, *_):
        """Reload applicants from the database and redraw the page."""
        try:
            self._applicants_active = ApplicantRepository.get_all()
            self._applicants_archived = self._get_archived_applicants()

            statuses = {}
            for application in ApplicationRepository.get_all():
                statuses[application.get("applicant_id")] = (
                    application.get("status")
                )
            self._applicants_statuses = statuses
            self._applicants_loaded = True

            self._update_filter_options(self._applicants_base(), statuses)
            self._render_applicants()

        except Exception as error:
            self.show_error("Applicants", error)

    def _render_applicants(self):
        try:
            all_active = self._applicants_active
            archived = self._applicants_archived
            statuses = self._applicants_statuses
            archived_view = self._applicants_view == "archived"

            needle = self.applicant_search.text().strip().lower()
            base = self._applicants_base()
            if needle:
                base = [
                    a for a in base
                    if needle in " ".join(
                        str(v or "")
                        for v in (
                            a.get("applicant_id"),
                            _display_id(a),
                            a.get("first_name"),
                            a.get("last_name"),
                            a.get("barangay"),
                        )
                    ).lower()
                ]

            barangay = (
                self.barangay_filter.currentText()
                if self.barangay_filter.currentIndex() > 0
                else None
            )
            status_filter = self.status_filter.currentData()

            rows = []
            for applicant in base:
                status = statuses.get(applicant.get("applicant_id"))
                if barangay and str(applicant.get("barangay")) != barangay:
                    continue
                if status_filter and status != status_filter:
                    continue
                rows.append((applicant, status))

            pages = max(1, -(-len(rows) // PAGE_SIZE))
            self._applicants_page_index = min(
                self._applicants_page_index, pages - 1
            )
            start = self._applicants_page_index * PAGE_SIZE
            page_rows = rows[start:start + PAGE_SIZE]

            table = self.applicants_table
            table.clearSelection()
            table.setRowCount(len(page_rows))

            for row, (applicant, status) in enumerate(page_rows):
                self.set_table_item(table, row, COL_SELECT, "☐")
                select_item = table.item(row, COL_SELECT)
                select_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                select_item.setForeground(QBrush(QColor(MUTED)))

                self.set_table_item(
                    table, row, COL_ID, _display_id(applicant)
                )
                id_item = table.item(row, COL_ID)
                id_item.setData(ID_ROLE, applicant.get("applicant_id"))
                id_item.setData(
                    NAME_ROLE,
                    f"{applicant.get('first_name') or ''} "
                    f"{applicant.get('last_name') or ''}".strip(),
                )

                self.set_table_item(table, row, COL_NAME, "")
                table.setCellWidget(
                    row, COL_NAME, self._make_name_cell(applicant)
                )

                self.set_table_item(
                    table, row, COL_BARANGAY, applicant.get("barangay")
                )
                self.set_table_item(
                    table,
                    row,
                    COL_AGE_SEX,
                    f"{_age(applicant)} / {_sex(applicant)}",
                )
                self.set_table_item(
                    table,
                    row,
                    COL_PHONE,
                    _mask_phone(applicant.get("phone")),
                )

                self.set_table_item(table, row, COL_STATUS, "")
                table.setCellWidget(
                    row, COL_STATUS, self._make_status_cell(status)
                )

                self.set_table_item(table, row, COL_ACTIONS, "")
                table.setCellWidget(
                    row, COL_ACTIONS, self._make_menu_cell(row)
                )

            # Empty state: keep the header, replace the blank body with a note.
            panel_layout = self.applicants_panel_layout
            if page_rows:
                table.setMinimumHeight(320)
                table.setMaximumHeight(16777215)
                panel_layout.setStretchFactor(table, 1)
                panel_layout.setStretchFactor(self.applicants_empty, 0)
                self.applicants_empty.hide()
            else:
                table.setMinimumHeight(0)
                table.setMaximumHeight(40)
                panel_layout.setStretchFactor(table, 0)
                panel_layout.setStretchFactor(self.applicants_empty, 1)
                if archived_view and not archived:
                    message = "No archived applicants."
                elif not self._applicants_base():
                    message = "No applicants have been registered yet."
                else:
                    message = "No applicants match the current filters."
                self.applicants_empty.setText(message)
                self.applicants_empty.show()

            # tabs + footer
            self.active_tab.setText(
                f"Active applicants  {len(all_active)}"
            )
            self.archived_tab.setText(f"Archived  {len(archived)}")

            scope = "archived" if archived_view else "active"
            total = len(archived) if archived_view else len(all_active)
            plural = "" if len(archived) == 1 else "s"
            if len(rows) > PAGE_SIZE:
                shown = (
                    f"Showing {start + 1}–{start + len(page_rows)} "
                    f"of {len(rows)} {scope} applicants"
                )
            else:
                shown = f"Showing {len(page_rows)} of {total} {scope} applicants"
            self.applicants_footer.setText(
                f"{shown} · {len(archived)} archived record{plural}"
            )
            self._rebuild_applicants_pager(
                self._applicants_page_index, pages
            )

            self._update_selection_bar()

        except Exception as error:
            self.show_error("Applicants", error)

    # ------------------------------------------------------------------
    # Selection helpers and actions
    # ------------------------------------------------------------------
    def get_selected_applicant_id(self):
        row = self.applicants_table.currentRow()

        if row < 0:
            QMessageBox.warning(
                self,
                "No Applicant Selected",
                "Please select an applicant from the table first.",
            )
            return None

        item = self.applicants_table.item(row, COL_ID)

        if item is None:
            return None

        try:
            return int(item.data(ID_ROLE))
        except (TypeError, ValueError):
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