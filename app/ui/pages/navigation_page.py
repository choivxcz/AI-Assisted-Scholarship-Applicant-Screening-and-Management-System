from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
)

# (icon, label) — order must match the pages added in MainWindow.
NAV_ITEMS = [
    ("▦", "Dashboard"),
    ("◉", "Applicants"),
    ("❐", "Applications"),
    ("◫", "ML Screening"),
    ("◷", "Interviews"),
    ("✓", "Scholarship Decisions"),
]


class NavigationPageMixin:
    def create_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(232)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(14, 18, 14, 16)
        layout.setSpacing(6)

        # Brand ---------------------------------------------------------
        brand_row = QHBoxLayout()
        brand_row.setSpacing(10)

        logo = QLabel("🌱")
        logo.setObjectName("brand_logo")
        logo.setFixedSize(40, 40)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        brand_text = QVBoxLayout()
        brand_text.setSpacing(0)
        brand = QLabel("LYDO")
        brand.setObjectName("brand")
        subtitle = QLabel("SANTA CRUZ, LAGUNA")
        subtitle.setObjectName("sidebar_subtitle")
        brand_text.addWidget(brand)
        brand_text.addWidget(subtitle)

        brand_row.addWidget(logo)
        brand_row.addLayout(brand_text)
        brand_row.addStretch()
        layout.addLayout(brand_row)
        layout.addSpacing(22)

        section = QLabel("SCHOLARSHIP WORKSPACE")
        section.setObjectName("sidebar_section")
        layout.addWidget(section)
        layout.addSpacing(4)

        # Navigation ------------------------------------------------------
        self.nav_buttons = []
        for index, (icon, label) in enumerate(NAV_ITEMS):
            button = QPushButton(f"{icon}    {label}")
            button.setObjectName("nav_button")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(
                lambda _checked, i=index: self.navigate(i)
            )
            self.nav_buttons.append(button)
            layout.addWidget(button)

        layout.addSpacing(14)

        # Info card -------------------------------------------------------
        card = QFrame()
        card.setObjectName("sidebar_card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 14, 14, 14)
        card_layout.setSpacing(4)

        card_icon = QLabel("🛡")
        card_icon.setObjectName("sidebar_card_icon")

        card_title = QLabel("Supporting every young ambition.")
        card_title.setObjectName("sidebar_card_title")
        card_title.setWordWrap(True)

        card_text = QLabel(
            "Local Youth Development Office · Santa Cruz, Laguna"
        )
        card_text.setObjectName("sidebar_card_text")
        card_text.setWordWrap(True)

        card_layout.addWidget(card_icon)
        card_layout.addWidget(card_title)
        card_layout.addSpacing(6)
        card_layout.addWidget(card_text)
        layout.addWidget(card)

        layout.addStretch()

        footer = QLabel("?   Workspace guide")
        footer.setObjectName("sidebar_footer")
        layout.addWidget(footer)

        return sidebar

    def navigate(self, index):
        self.pages.setCurrentIndex(index)

        for i, button in enumerate(self.nav_buttons):
            button.setChecked(i == index)

        if hasattr(self, "breadcrumb") and 0 <= index < len(NAV_ITEMS):
            self.breadcrumb.setText(
                f"Scholarships  ›  {NAV_ITEMS[index][1]}"
            )

    def create_placeholder_page(self, title_text, description_text):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(18)

        title = QLabel(title_text)
        title.setObjectName("page_title")

        description = QLabel(description_text)
        description.setObjectName("muted")

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addStretch()

        return page