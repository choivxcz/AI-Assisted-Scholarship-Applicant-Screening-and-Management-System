
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
)


class NavigationPageMixin:
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

        navigation_items = [
            ("Dashboard", 0),
            ("Applicants", 1),
            ("Applications", 2),
            ("ML Screening", 3),
            ("Interviews", 4),
            ("Scholarship Decisions", 5),
        ]

        for label, index in navigation_items:
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
        elif index == 3:
            self.refresh_ml_screening_applications()

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
