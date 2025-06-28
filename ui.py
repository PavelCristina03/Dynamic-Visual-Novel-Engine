import os
import re
import sys

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QInputDialog, QLabel, QStackedLayout, QListWidget, QListWidgetItem,
    QLineEdit, QCheckBox, QMessageBox, QSpacerItem, QSizePolicy, QFrame, QScrollArea, QProgressBar, QGraphicsDropShadowEffect
)
from PySide6.QtGui import QPixmap, QFont, QColor, QLinearGradient, QPainter, QIcon
from PySide6.QtCore import Qt, QTimer, Slot, QPropertyAnimation, QEasingCurve, QPoint
from main import GameEngine


class Style:
    # Color palette
    #PRIMARY = "#6a5acd"  # Slate blue
    #SECONDARY = "#9370db"  # Medium purple
    PRIMARY = "#a39dc7" 
    SECONDARY = "#9285a9"
    ACCENT = "#ff8c00"  # Dark orange
    DARK = "#2F2B52"  # Dark blue
    DARKER = "#0C0A1C"  # Darker blue
    LIGHT = "#e6e6fa"  # Lavender
    TEXT = "#f8f8ff"  # Ghost white
    TEXT_SECONDARY = "#d3d3d3"  # Light gray

    # Gradients
    @staticmethod
    def primary_gradient():
        gradient = QLinearGradient(0, 0, 0, 400)
        gradient.setColorAt(0, QColor(106, 90, 205))  # Slate blue
        gradient.setColorAt(1, QColor(72, 61, 139))  # Dark slate blue
        return gradient

    @staticmethod
    def dark_gradient():
        gradient = QLinearGradient(0, 0, 0, 400)
        gradient.setColorAt(0, QColor(26, 26, 46))  # Dark blue
        gradient.setColorAt(1, QColor(10, 10, 20))  # Almost black
        return gradient

    # Fonts
    TITLE_FONT = QFont("Montserrat", 32, QFont.Bold)
    HEADER_FONT = QFont("Montserrat", 24, QFont.Bold)
    SUBHEADER_FONT = QFont("Montserrat", 18, QFont.Medium)
    BODY_FONT = QFont("Open Sans", 14)
    BUTTON_FONT = QFont("Open Sans", 12, QFont.Bold)
    SMALL_FONT = QFont("Open Sans", 11)

    # Stylesheets
    MAIN_WINDOW = f"""
        background-color: {DARK};
        color: {TEXT};
    """

    BUTTON_PRIMARY = f"""
        QPushButton {{
            background-color: {PRIMARY};
            color: {TEXT};
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font: bold 14px;
        }}
        QPushButton:hover {{
            background-color: {SECONDARY};
        }}
        QPushButton:disabled {{
            background-color: #555;
            color: #999;
        }}
    """

    BUTTON_SECONDARY = f"""
        QPushButton {{
            background-color: transparent;
            color: {TEXT};
            border: 2px solid {PRIMARY};
            border-radius: 8px;
            padding: 10px 20px;
            font: bold 14px;
        }}
        QPushButton:hover {{
            background-color: rgba(106, 90, 205, 0.2);
        }}
    """

    BUTTON_ACCENT = f"""
        QPushButton {{
            background-color: {ACCENT};
            color: {DARK};
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font: bold 14px;
        }}
        QPushButton:hover {{
            background-color: #ff9e40;
        }}
    """

    CARD_STYLE = f"""
        background-color: {DARKER};
        border-radius: 12px;
        padding: 20px;
    """

    INPUT_STYLE = f"""
        QLineEdit, QTextEdit {{
            background-color: {DARKER};
            color: {TEXT};
            border: 1px solid {PRIMARY};
            border-radius: 6px;
            padding: 8px;
            font: 14px;
        }}
        QLineEdit:focus, QTextEdit:focus {{
            border: 2px solid {SECONDARY};
        }}
    """

    LIST_ITEM_STYLE = f"""
        QListWidget {{
            background-color: {DARKER};
            border: 1px solid {PRIMARY};
            border-radius: 8px;
            padding: 5px;
        }}
        QListWidget::item {{
            background-color: transparent;
            padding: 10px;
            border-bottom: 1px solid rgba(106, 90, 205, 0.3);
        }}
        QListWidget::item:hover {{
            background-color: rgba(106, 90, 205, 0.2);
        }}
        QListWidget::item:selected {{
            background-color: {PRIMARY};
            color: {TEXT};
        }}
    """

    CHECKBOX_STYLE = f"""
        QCheckBox {{
            color: {TEXT};
            spacing: 8px;
        }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {PRIMARY};
            border-radius: 4px;
        }}
        QCheckBox::indicator:checked {{
            background-color: {PRIMARY};
            image: url(:/images/checkmark.png);
        }}
    """
    COMPANION_CARD = """
        background-color: {DARKER};
        border-radius: 6px;
        padding: 5px;
        margin: 2px;
    """
    
    COMPANION_CARD_SELECTED = """
        background-color: rgba(106, 90, 205, 0.2);
        outline: 1px solid {PRIMARY};
        border-radius: 6px;
        padding: 5px;
        margin: 2px;
    """
    
    @staticmethod
    def companion_card_style(selected=False):
        """Returns formatted companion card style"""
        style = Style.COMPANION_CARD_SELECTED if selected else Style.COMPANION_CARD
        return style.format(
            DARKER=Style.DARKER,
            PRIMARY=Style.PRIMARY
        )
    CHECKBOX_STYLE = f"""
        QCheckBox {{
            color: {TEXT};
            spacing: 8px;
        }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {PRIMARY};
            border-radius: 4px;
        }}
        QCheckBox::indicator:checked {{
            background-color: {PRIMARY};
            image: url(:/images/checkmark.png);
        }}
    """

    MSGBOX = f"""
        QMessageBox {{
            background-color: {DARKER};
            color: {TEXT};
            border-radius: 8px;
            padding: 16px;
        }}
        QMessageBox QLabel {{
            color: {TEXT};
            font: {BODY_FONT.pointSize()}px "{BODY_FONT.family()}";
        }}
        QMessageBox QPushButton {{
            background-color: {PRIMARY};
            color: {DARK};
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font: bold {BUTTON_FONT.pointSize()}px "{BUTTON_FONT.family()}";
        }}
        QMessageBox QPushButton:hover {{
            background-color: {SECONDARY};
        }}
    """
    SIDEBAR_STYLE = f"""
        /* Sidebar background + border */
        background-color: {DARKER};
        border-left: 2px solid {PRIMARY};
        border-radius: 8px 0 0 8px;
        padding: 0; 

        /* Make the scroll area fill the sidebar */
        QScrollArea {{
        border: none;
        padding: 15px;         /* move your padding here */
        }}

        /* Vertical scrollbar styling */
        QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 0;
        }}
        QScrollBar::handle:vertical {{
        background: rgba(163,157,199,0.6);
        border-radius: 4px;
        }}
        QScrollBar::add-line, QScrollBar::sub-line {{
        height: 0;
        }}
    """


    STAT_BAR_STYLE = f"""
        QProgressBar {{
            border: 1px solid {PRIMARY};
            border-radius: 4px;
            text-align: center;
            color: {TEXT};
        }}
        QProgressBar::chunk {{
            background-color: {PRIMARY};
        }}
    """

    OVERLAY_STYLE = """
        background-color: rgba(0, 0, 0, 0.7);
    """
    



class AnimatedButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._animation = QPropertyAnimation(self, b"geometry")
        self._animation.setDuration(200)
        self._animation.setEasingCurve(QEasingCurve.OutBack)

    def enterEvent(self, event):
        self._animation.stop()
        self._animation.setStartValue(self.geometry())
        self._animation.setEndValue(self.geometry().adjusted(-5, -5, 5, 5))
        self._animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animation.stop()
        self._animation.setStartValue(self.geometry())
        self._animation.setEndValue(self.geometry().adjusted(5, 5, -5, -5))
        self._animation.start()
        super().leaveEvent(event)


class GradientWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)

    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(26, 26, 46))  # Dark blue
        gradient.setColorAt(1, QColor(10, 10, 20))  # Almost black
        painter.fillRect(self.rect(), gradient)



class TitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = parent

        # Draw via stylesheet; fixed slim height
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(28)

        # Solid dark background (use the same as Style.DARK)
        self.setStyleSheet("background-color: #0C0A1C;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(8)

        # App icon (24×24)
        ico = QLabel()
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "icon.ico")
        pix = QPixmap(icon_path).scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        ico.setPixmap(pix)
        layout.addWidget(ico)

        # Title text
        title = QLabel(self.window.windowTitle())
        title.setStyleSheet("color: #f8f8ff; font-weight: bold;")
        layout.addWidget(title)

        layout.addStretch()

        # Common button style
        btn_style = """
            QPushButton {
                background: transparent;
                color: #f8f8ff;
                border: none;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(106, 90, 205, 0.2);
            }
        """

        # All buttons 28×28
        for symbol, slot, hover_color in [
            ("–", self.window.showMinimized, None),
            ("▢", self._toggle_max_restore, None),
            ("✕", self.window.close, "rgba(255,100,100,0.6)")
        ]:
            btn = QPushButton(symbol)
            btn.setFixedSize(28, 28)

            if hover_color:
                # override hover only for close
                btn.setStyleSheet(f"""
                    QPushButton {{ background: transparent; color: #f8f8ff; border: none; font-size:16px; }}
                    QPushButton:hover {{ background-color: {hover_color}; }}
                """)
            else:
                btn.setStyleSheet(btn_style)

            btn.clicked.connect(slot)
            layout.addWidget(btn)

    def _toggle_max_restore(self):
        if self.window.isMaximized():
            self.window.showNormal()
        else:
            self.window.showMaximized()

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self._drag_pos = ev.globalPosition().toPoint() - self.window.frameGeometry().topLeft()
            ev.accept()

    def mouseMoveEvent(self, ev):
        if ev.buttons() & Qt.LeftButton:
            self.window.move(ev.globalPosition().toPoint() - self._drag_pos)
            ev.accept()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "resources", "icon.ico")))
        # apply your message-box style globally
        QApplication.instance().setStyleSheet(Style.MSGBOX)
        # 1) Turn *off* all native decorations, replace flags with Frameless
        self.setWindowFlags(Qt.FramelessWindowHint)

        # 2) Allow our widget to paint outside the normal window area
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Now your custom TitleBar really will be the *only* bar.
        # The rest of your styling & layout code follows…
        self.setWindowTitle("Visual Novel Engine")
        self.setMinimumSize(900, 700)

        # Wrap TitleBar + Content in a single container
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0,0,0,0)
        container_layout.setSpacing(0)

        # 3) Insert your custom TitleBar at the top:
        self.title_bar = TitleBar(self)
        container_layout.addWidget(self.title_bar)

        # 4) Then the gradient + stacked layout:
        central = GradientWidget()
        self.stack = QStackedLayout()
        central.setLayout(self.stack)
        container_layout.addWidget(central)

        self.setCentralWidget(container)

        # Game engine & state
        self.engine = None
        self._companion_options = []
        self._companion_widgets = []
        self._chosen_companion = None
        self._is_generating = False
        self._custom_choice_active = False

        # Animation timers
        self._anim_timer = QTimer(self, interval=20)
        self._anim_timer.timeout.connect(self._on_anim_timeout)
        self._loading_timer = QTimer(self, interval=500)
        self._loading_timer.timeout.connect(self._animate_loading)
        self._loading_dots = 0

        # Text animation buffers
        self._full_text = ""
        self._anim_index = 0
        self._anim_section = None

        # Build UI pages
        self._build_landing_page()      # 0
        self._build_setup_page()        # 1
        self._build_companion_page()    # 2
        self._build_loading_page()      # 3
        self._build_premise_page()      # 4
        self._build_profile_page()      # 5
        self._build_game_page()         # 6

        self.stack.setCurrentIndex(0)

    def _create_button(self, text, callback=None, style=Style.BUTTON_PRIMARY, enabled=True):
        btn = QPushButton(text)
        btn.setStyleSheet(style)
        if callback:
            btn.clicked.connect(callback)
        btn.setEnabled(enabled)
        return btn

    def _build_landing_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(40)
        layout.setAlignment(Qt.AlignCenter)

        # Title section
        title = QLabel("Visual Novel Engine")
        title.setFont(Style.TITLE_FONT)
        title.setStyleSheet(f"color: {Style.PRIMARY};")
        title.setAlignment(Qt.AlignCenter)

        tagline = QLabel("Craft your own interactive story")
        tagline.setFont(Style.SUBHEADER_FONT)
        tagline.setStyleSheet(f"color: {Style.TEXT_SECONDARY};")
        tagline.setAlignment(Qt.AlignCenter)

        # Button section
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(30)
        btn_layout.setAlignment(Qt.AlignCenter)

        new_btn = self._create_button(
            "New Story", self._goto_setup,
            Style.BUTTON_PRIMARY
        )
        new_btn.setFixedSize(200, 60)

        resume_btn = self._create_button(
            "Continue", self._on_resume_clicked,
            Style.BUTTON_SECONDARY,
            enabled=os.path.isfile("savegame.json")
        )
        resume_btn.setFixedSize(200, 60)

        btn_layout.addWidget(new_btn)
        btn_layout.addWidget(resume_btn)

        # Add widgets to layout
        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(tagline)
        layout.addStretch()
        layout.addLayout(btn_layout)
        layout.addStretch()

        self.stack.addWidget(page)

    def _build_setup_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        # Header
        header = QLabel("Story Setup")
        header.setFont(Style.HEADER_FONT)
        header.setStyleSheet(f"color: {Style.PRIMARY};")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Form container
        form_container = QWidget()
        form_container.setStyleSheet(Style.CARD_STYLE)
        form_layout = QGridLayout(form_container)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(15)

        # Form elements
        self.custom_cb = QCheckBox("Generate custom premise?")
        self.custom_cb.setFont(Style.BODY_FONT)
        self.custom_cb.setStyleSheet(Style.CHECKBOX_STYLE)

        lbl_genre = QLabel("Genre:")
        lbl_genre.setFont(Style.BODY_FONT)
        lbl_genre.setStyleSheet(f"color: {Style.TEXT};")

        self.genre_input = QLineEdit()
        self.genre_input.setPlaceholderText("e.g. Fantasy, Sci-Fi, Mystery...")
        self.genre_input.setStyleSheet(Style.INPUT_STYLE)
        self.genre_input.setFont(Style.BODY_FONT)

        lbl_art = QLabel("Art Style (optional):")
        lbl_art.setFont(Style.BODY_FONT)
        lbl_art.setStyleSheet(f"color: {Style.TEXT};")

        self.art_input = QLineEdit()
        self.art_input.setPlaceholderText("e.g. Anime, Watercolor, Pixel Art...")
        self.art_input.setStyleSheet(Style.INPUT_STYLE)
        self.art_input.setFont(Style.BODY_FONT)

        # Add to form
        form_layout.addWidget(self.custom_cb, 0, 0, 1, 2)
        form_layout.addWidget(lbl_genre, 1, 0)
        form_layout.addWidget(self.genre_input, 1, 1)
        form_layout.addWidget(lbl_art, 2, 0)
        form_layout.addWidget(self.art_input, 2, 1)

        layout.addWidget(form_container)

        # Navigation buttons
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(20)
        nav_layout.setAlignment(Qt.AlignRight)

        back_btn = self._create_button(
            "Back", lambda: self.stack.setCurrentIndex(0),
            Style.BUTTON_SECONDARY
        )
        back_btn.setFixedSize(120, 60)

        self.setup_next = self._create_button(
            "Continue", self._start_new_game,
            Style.BUTTON_PRIMARY,
            enabled=False
        )
        self.setup_next.setFixedSize(120, 60)

        nav_layout.addWidget(back_btn)
        nav_layout.addWidget(self.setup_next)
        layout.addLayout(nav_layout)

        # Connect signals
        self.genre_input.textChanged.connect(
            lambda t: self.setup_next.setEnabled(bool(t.strip()))
        )

        self.stack.addWidget(page)

    def _build_companion_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        # Header
        header = QLabel("Choose Your Companion")
        header.setFont(Style.HEADER_FONT)
        header.setStyleSheet(f"color: {Style.PRIMARY};")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Companion list container
        container = QWidget()
        container.setStyleSheet(Style.CARD_STYLE)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(10)
        container_layout.setAlignment(Qt.AlignTop)

        self.companion_list = QListWidget()
        # keep ghost-white text, pin height, kill scrollbars & frames
        self.companion_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {Style.DARKER};
                border: 1px solid {Style.PRIMARY};
                border-radius: 8px;
                padding: 5px;
            }}
            QListWidget::item {{
                background: transparent;
                padding: 0px;
                border: none;
                margin: 2px;
            }}
            QListWidget::item:hover {{
                background: transparent;
            }}
            QListWidget::item:selected {{
                background: transparent;
            }}
        """)
        self.companion_list.setSelectionMode(QListWidget.SingleSelection)
        self.companion_list.itemClicked.connect(self._on_companion_click)
        self.companion_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.companion_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.companion_list.setFrameShape(QFrame.NoFrame)

        container_layout.addWidget(self.companion_list)
        layout.addWidget(container, stretch=1)

        # Navigation buttons
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(20)
        nav_layout.setAlignment(Qt.AlignRight)

        back_btn = self._create_button(
            "Back", lambda: self.stack.setCurrentIndex(1),
            Style.BUTTON_SECONDARY
        )
        back_btn.setFixedSize(120, 40)

        self.companion_next = self._create_button(
            "Continue", self._select_companion,
            Style.BUTTON_PRIMARY,
            enabled=False
        )
        self.companion_next.setFixedSize(120, 40)

        nav_layout.addWidget(back_btn)
        nav_layout.addWidget(self.companion_next)
        layout.addLayout(nav_layout)

        self.stack.addWidget(page)

    def _build_loading_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)

        self.loading_label = QLabel("Loading")
        self.loading_label.setFont(Style.HEADER_FONT)
        self.loading_label.setStyleSheet(f"color: {Style.PRIMARY};")
        self.loading_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.loading_label)
        self.stack.addWidget(page)

    def _build_premise_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        # Header
        header = QLabel("Story Premise")
        header.setFont(Style.HEADER_FONT)
        header.setStyleSheet(f"color: {Style.PRIMARY};")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Text container
        container = QWidget()
        container.setStyleSheet(Style.CARD_STYLE)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 20, 20, 20)

        self.premise_label = QLabel()
        self.premise_label.setFont(Style.BODY_FONT)
        self.premise_label.setStyleSheet(f"color: {Style.TEXT};")
        self.premise_label.setWordWrap(True)
        self.premise_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.premise_label)
        scroll.setStyleSheet("border: none;")

        container_layout.addWidget(scroll)
        layout.addWidget(container, stretch=1)

        # Navigation buttons
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(20)
        nav_layout.setAlignment(Qt.AlignRight)

        self.premise_next = self._create_button(
            "Continue", self._show_profile,
            Style.BUTTON_PRIMARY,
            enabled=False
        )
        self.premise_next.setFixedSize(120, 40)

        nav_layout.addWidget(self.premise_next)
        layout.addLayout(nav_layout)

        self.stack.addWidget(page)

    def _build_profile_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        # Header
        header = QLabel("Your Character")
        header.setFont(Style.HEADER_FONT)
        header.setStyleSheet(f"color: {Style.PRIMARY};")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Text container
        container = QWidget()
        container.setStyleSheet(Style.CARD_STYLE)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 20, 20, 20)

        self.profile_label = QLabel()
        self.profile_label.setFont(Style.BODY_FONT)
        self.profile_label.setStyleSheet(f"color: {Style.TEXT};")
        self.profile_label.setWordWrap(True)
        self.profile_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.profile_label)
        scroll.setStyleSheet("border: none;")

        container_layout.addWidget(scroll)
        layout.addWidget(container, stretch=1)

        # Navigation buttons
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(20)
        nav_layout.setAlignment(Qt.AlignRight)

        back_btn = self._create_button(
            "Back", self._back_to_premise,
            Style.BUTTON_SECONDARY
        )
        back_btn.setFixedSize(120, 40)

        self.profile_next = self._create_button(
            "Begin Story", self._enter_game,
            Style.BUTTON_ACCENT,
            enabled=False
        )
        self.profile_next.setFixedSize(120, 40)

        nav_layout.addWidget(back_btn)
        nav_layout.addWidget(self.profile_next)
        layout.addLayout(nav_layout)

        self.stack.addWidget(page)

    def _build_game_page(self):
        page = QWidget()
        layout = QGridLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Background image
        self.background_label = QLabel()
        self.background_label.setScaledContents(True)
        layout.addWidget(self.background_label, 0, 0, 1, 1)

        # Create the profile sidebar and overlay (but don't show them yet)
        self._create_profile_sidebar()
        self.sidebar.hide()
        self.sidebar_overlay.hide()
        
        # Add floating menu button in top-left (below title bar)
        self.menu_button = self._create_button(
            "Main Menu", self._return_to_main_menu,
            Style.BUTTON_SECONDARY
        )
        self.menu_button.setFixedSize(100, 40)
        self.menu_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {Style.DARKER};
                color: {Style.TEXT};
                border: 1px solid {Style.PRIMARY};
                border-radius: 6px;
                padding: 8px;
                font: bold 12px;
            }}
            QPushButton:hover {{
                background-color: {Style.PRIMARY};
            }}
        """)
        
        # Create container for the floating button
        button_container = QWidget()
        button_container.setLayout(QHBoxLayout())
        button_container.layout().setContentsMargins(20, 10, 0, 0)
        button_container.layout().addWidget(self.menu_button)
        button_container.layout().addStretch()
        button_container.setStyleSheet("background: transparent;")
        
        # Add to layout (top-left position)
        layout.addWidget(button_container, 0, 0, 1, 1, Qt.AlignTop | Qt.AlignLeft)

        # profile button
        self.profile_button = self._create_button(
            "Profiles", self._toggle_profile_sidebar,
            Style.BUTTON_SECONDARY
        )
        self.profile_button.setFixedSize(100, 40)
        self.profile_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {Style.DARKER};
                color: {Style.TEXT};
                border: 1px solid {Style.PRIMARY};
                border-radius: 6px;
                padding: 8px;
                font: bold 12px;
            }}
            QPushButton:hover {{
                background-color: {Style.PRIMARY};
            }}
        """)
        button_container.layout().addWidget(self.profile_button)

        # Text frame overlay
        frame = QFrame()
        frame.setStyleSheet(f"""
            background-color: rgba(26, 26, 46, 0.85);
            border-top: 2px solid {Style.PRIMARY};
            border-radius: 0;
        """)
        frame.setFixedHeight(250)
        layout.addWidget(frame, 1, 0, 1, 1)

                # Add them to the layout (but keep them hidden)
        layout.addWidget(self.sidebar_overlay, 0, 0, 2, 1)
        layout.addWidget(self.sidebar, 0, 0, 2, 1, Qt.AlignRight)

        frame_layout = QHBoxLayout(frame)
        frame_layout.setContentsMargins(20, 15, 20, 15)
        frame_layout.setSpacing(15)

        # Character portrait
        self.portrait_label = QLabel()
        self.portrait_label.setFixedSize(220, 220)
        self.portrait_label.setStyleSheet("border-radius: 8px;")
        self.portrait_label.setScaledContents(True)
        self.portrait_label.hide()
        frame_layout.addWidget(self.portrait_label)

        # Right side content
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        # Speaker name
        self.speaker_label = QLabel()
        self.speaker_label.setFont(Style.SUBHEADER_FONT)
        self.speaker_label.setStyleSheet(f"color: {Style.PRIMARY};")
        self.speaker_label.hide()
        right_layout.addWidget(self.speaker_label)

        # Text content
        self.paragraph_label = QLabel()
        self.paragraph_label.setFont(Style.BODY_FONT)
        self.paragraph_label.setStyleSheet(f"color: {Style.TEXT};")
        self.paragraph_label.setWordWrap(True)
        self.paragraph_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        right_layout.addWidget(self.paragraph_label, stretch=1)

        # Custom choice input
        self.custom_choice_container = QWidget()
        self.custom_choice_container.setStyleSheet(f"""
            background-color: {Style.DARKER};
            border: 2px solid {Style.PRIMARY};
            border-radius: 8px;
            padding: 10px;
        """)
        self.custom_choice_container.hide()
        
        custom_layout = QHBoxLayout(self.custom_choice_container)
        custom_layout.setContentsMargins(5, 5, 5, 5)
        
        self.custom_input = QLineEdit()
        self.custom_input.setPlaceholderText("Enter your choice...")
        self.custom_input.setStyleSheet(Style.INPUT_STYLE)
        custom_layout.addWidget(self.custom_input, stretch=1)

        self.submit_custom_btn = self._create_button(
            "Submit", self._submit_custom_choice,
            Style.BUTTON_PRIMARY
        )
        self.submit_custom_btn.setFixedSize(100, 50)
        custom_layout.addWidget(self.submit_custom_btn)

        self.cancel_custom_btn = self._create_button(
            "Cancel", self._cancel_custom_choice,
            Style.BUTTON_SECONDARY
        )
        self.cancel_custom_btn.setFixedSize(100, 50)
        custom_layout.addWidget(self.cancel_custom_btn)

        right_layout.addWidget(self.custom_choice_container)

        # Choices list
        self.choices_container = QWidget()
        self.choices_container.hide()
        self.choices_layout = QVBoxLayout(self.choices_container)
        self.choices_layout.setSpacing(5)
        right_layout.addWidget(self.choices_container)

        # Navigation buttons
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(15)
        
        self.back_button = self._create_button(
            "◀ Back", self._on_back_clicked,
            Style.BUTTON_SECONDARY
        )
        self.back_button.setFixedSize(100, 40)
        nav_layout.addWidget(self.back_button)

        nav_layout.addStretch()

        self.skip_button = self._create_button(
            "Skip", self._skip_animation,
            Style.BUTTON_SECONDARY
        )
        self.skip_button.setFixedSize(100, 40)
        self.skip_button.hide()
        nav_layout.addWidget(self.skip_button)

        self.next_button = self._create_button(
            "Next ▶", self._on_next_clicked,
            Style.BUTTON_PRIMARY
        )
        self.next_button.setFixedSize(100, 40)
        nav_layout.addWidget(self.next_button)

        right_layout.addLayout(nav_layout)
        frame_layout.addLayout(right_layout, stretch=1)

        self.stack.addWidget(page)  

    def _goto_setup(self):
        self.genre_input.clear()
        self.art_input.clear()
        self.custom_cb.setChecked(False)
        self.setup_next.setEnabled(False)
        self.stack.setCurrentIndex(1)

    def _start_new_game(self):
        genre = self.genre_input.text().strip().lower()
        art_style = self.art_input.text().strip()
        choice = "custom" if self.custom_cb.isChecked() else "default"

        self.engine = GameEngine()
        self._companion_options = self.engine.start_new_game(genre, art_style, choice)

        self._populate_companion_list()
        self.stack.setCurrentIndex(2)
                        
    def _populate_companion_list(self):
        self.companion_list.clear()
        self._companion_widgets.clear()

        for companion in self._companion_options:
            item = QListWidgetItem()
            widget = QWidget()
            layout = QVBoxLayout(widget)
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setSpacing(5)

            # Name label
            name = QLabel(companion["name"])
            name.setFont(QFont("Open Sans", 12, QFont.Bold))
            name.setStyleSheet(f"color: {Style.TEXT};")

            # Description label
            desc = QLabel(companion["description"])
            desc.setFont(QFont("Open Sans", 10))
            desc.setStyleSheet(f"color: {Style.TEXT_SECONDARY};")
            desc.setWordWrap(True)

            layout.addWidget(name)
            layout.addWidget(desc)
            widget.setLayout(layout)

            # Base widget styling with consistent sizing
            widget.setStyleSheet(Style.companion_card_style())

            item.setSizeHint(widget.sizeHint())
            self.companion_list.addItem(item)
            self.companion_list.setItemWidget(item, widget)
            self._companion_widgets.append(widget)

        # Adjust list height
        total_h = sum(
            self.companion_list.sizeHintForRow(i)
            for i in range(self.companion_list.count())
        )
        total_h += 2 * self.companion_list.frameWidth() + 10
        self.companion_list.setFixedHeight(min(total_h, 400))


    def _on_companion_click(self, item):
        idx = self.companion_list.row(item)
        self._chosen_companion = idx
        self.companion_next.setEnabled(True)
        
        for i in range(self.companion_list.count()):
            widget = self.companion_list.itemWidget(self.companion_list.item(i))
            if widget:
                # Apply appropriate style
                widget.setStyleSheet(Style.companion_card_style(selected=(i == idx)))
                
                # Update text colors
                for child in widget.findChildren(QLabel):
                    if i == idx or child.text() in [c["name"] for c in self._companion_options]:
                        child.setStyleSheet(f"color: {Style.TEXT};")
                    else:
                        child.setStyleSheet(f"color: {Style.TEXT_SECONDARY};")      
    
    def _select_companion(self):
        idx = self._chosen_companion or 0
        self.engine.select_companion(idx, self._companion_options)
        self._show_loading("Generating story premise...")
        QTimer.singleShot(2000, self._show_premise)

    def _show_loading(self, message="Loading"):
        self._is_generating = True
        self._loading_dots = 0
        self.loading_label.setText(message)
        self._loading_timer.start()
        self.stack.setCurrentIndex(3)

    def _animate_loading(self):
        self._loading_dots = (self._loading_dots + 1) % 4
        dots = "." * self._loading_dots
        spaces = " " * (3 - self._loading_dots)
        base = self.loading_label.text().split('.')[0]
        self.loading_label.setText(f"{base}{dots}{spaces}")

    def _show_premise(self):
        self._loading_timer.stop()
        self._is_generating = False
        
        so = self.engine.state.story_outline
        overview = so["world_data"].get("world_overview", "")
        pb = so["player_backstory"]
        name = pb.get("name", "")
        origin = pb.get("origin_story", "")
        
        txt = f"<h3 style='color:{Style.PRIMARY};'>World Overview</h3>{overview}"
        txt += f"<br><br><h3 style='color:{Style.PRIMARY};'>Your Character</h3>"
        txt += f"<b>Name:</b> {name}<br>{origin}"
        
        self.premise_label.setText("")
        self.stack.setCurrentIndex(4)
        self._start_anim(txt, section="premise")

    def _show_profile(self):
        txt = getattr(
            self.engine.state, "player_profile_description",
            "You are the chosen one."
        )
        self.profile_label.setText("")
        self.stack.setCurrentIndex(5)
        self._start_anim(txt, section="profile")

    def _back_to_premise(self):
        self.stack.setCurrentIndex(4)
        self.premise_next.setEnabled(False)

    def _enter_game(self):
        self._display_scene()
        self.stack.setCurrentIndex(6)

    def _on_resume_clicked(self):
        self.engine = GameEngine()
        self.engine.resume_game()
        self._display_scene()
        self.stack.setCurrentIndex(6)

    def _display_scene(self):
        text = self.engine.get_current_text()
        self.paragraphs = [
            p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()
        ]
        self.current_par = 0

        # Set background image
        img = self.engine.get_current_image_path()
        if img and os.path.isfile(img):
            pix = QPixmap(img).scaled(
                self.width(), self.height(),
                Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            self.background_label.setPixmap(pix)
        else:
            self.background_label.clear()

        self.choices_container.hide()
        self.custom_choice_container.hide()
        self._show_paragraph()

    def _show_paragraph(self):
        self.choices_container.hide()
        self.custom_choice_container.hide()
        self._custom_choice_active = False

        self.paragraph_label.show()
        self.speaker_label.show()
        self.portrait_label.show()

        para = self.paragraphs[self.current_par]
        m = re.match(r'^([^:]+):\s*"(.*)"$', para)
        
        if m:
            speaker, spoken = m.groups()
            self.speaker_label.setText(speaker)

            # ── try exact match, then fall back to first name ──
            url = self.engine.state.character_image_urls.get(speaker)
            if not url and " " in speaker:
                first = speaker.split()[0]
                url = self.engine.state.character_image_urls.get(first)

            if url and os.path.isfile(url):
                pix = QPixmap(url).scaled(
                    self.portrait_label.size(),
                    Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.portrait_label.setPixmap(pix)
                self.portrait_label.show()
            else:
                self.portrait_label.hide()

                
            self._start_anim(spoken, section=None)
        else:
            self.speaker_label.hide()
            self.portrait_label.hide()
            self._start_anim(para, section=None)

        self.back_button.setEnabled(self.current_par > 0)
        self.next_button.setText("Next ▶")

    def _on_choice_clicked(self, item):
        if self._is_generating:
            return

        txt = item.text().strip()
        if txt == "[Custom Choice]":
            self._activate_custom_choice()
        else:
            self._process_choice(txt)

    def _activate_custom_choice(self):
        self.choices_container.hide()
        self.custom_choice_container.show()
        self.custom_input.clear()
        self.custom_input.setFocus()
        self._custom_choice_active = True
        self.next_button.setEnabled(False)

    def _submit_custom_choice(self):
        choice = self.custom_input.text().strip()
        if not choice:
            QMessageBox.warning(self, "Empty Choice", "Please enter your choice")
            return
        
        self._process_choice(choice)

    def _cancel_custom_choice(self):
        self.custom_choice_container.hide()
        self.choices_container.show()
        self._custom_choice_active = False
        self.next_button.setEnabled(True)

    def _process_choice(self, choice):
        self._show_loading("Generating next scene...")
        QTimer.singleShot(100, lambda: self._complete_choice_processing(choice))

    def _complete_choice_processing(self, choice):
        self._loading_timer.stop()
        self._is_generating = False
        self.engine.make_choice(choice)
        self._display_scene()
        self.stack.setCurrentIndex(6)

    def _on_back_clicked(self):
        if self._is_generating:
            return
            
        if self.current_par > 0:
            self.current_par -= 1
            self._show_paragraph()

    def _on_next_clicked(self):
        if self._is_generating:
            return
            
        if self._anim_timer.isActive():
            self._skip_animation()
            return

        if self.current_par < len(self.paragraphs) - 1:
            self.current_par += 1
            self._show_paragraph()
        else:
            self._show_choices()

    def _on_choice_text(self, choice):
        if choice == "[Custom Choice]":
            self._activate_custom_choice()
        else:
            self._process_choice(choice)


    def _show_choices(self):
        # hide prose & portrait
        self.paragraph_label.hide()
        self.speaker_label.hide()
        self.portrait_label.hide()
        self.skip_button.hide()

        # clear out any old buttons
        for i in reversed(range(self.choices_layout.count())):
            btn = self.choices_layout.takeAt(i).widget()
            if btn:
                btn.deleteLater()

        # get the new choices
        choices = self.engine.get_current_choices()
        for text in choices + ["[Custom Choice]"]:
            btn = QPushButton(text)
            btn.setFont(Style.SMALL_FONT)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Style.DARKER};
                    color: {Style.TEXT};
                    border: 1px solid {Style.PRIMARY};
                    border-radius: 6px;
                    padding: 8px;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background-color: {Style.PRIMARY};
                    color: {Style.DARK};
                }}
            """)
            btn.clicked.connect(lambda _, t=text: self._on_choice_text(t))
            self.choices_layout.addWidget(btn)

        # show them
        self.choices_container.show()
        self.back_button.setEnabled(True)
        self.next_button.setEnabled(False)


    def _start_anim(self, text, section):
        self._full_text = text
        self._anim_index = 0
        self._anim_section = section

        lbl = {
            "premise": self.premise_label,
            "profile": self.profile_label,
            None: self.paragraph_label
        }[section]

        lbl.setText("")
        self.skip_button.setVisible(section is None)
        self._anim_timer.start()

    def _on_anim_timeout(self):
        lbl = {
            "premise": self.premise_label,
            "profile": self.profile_label,
            None: self.paragraph_label
        }[self._anim_section]

        if self._anim_index < len(self._full_text):
            lbl.setText(lbl.text() + self._full_text[self._anim_index])
            self._anim_index += 1
        else:
            # Animation complete
            self._anim_timer.stop()
            if self._anim_section in ("premise", "profile"):
                # Enable the continue button on text pages
                getattr(self, f"{self._anim_section}_next").setEnabled(True)
            else:
                # In-game text: show navigation
                self.skip_button.hide()
                self.next_button.setEnabled(True)
                self.back_button.setEnabled(self.current_par > 0)
            self._anim_section = None

    def _skip_animation(self):
        """Immediately finish the current text animation."""
        lbl = {
            "premise": self.premise_label,
            "profile": self.profile_label,
            None: self.paragraph_label
        }[self._anim_section]
        lbl.setText(self._full_text)
        self._anim_timer.stop()
        # Restore buttons
        self.skip_button.hide()
        self.next_button.setEnabled(True)
        self.back_button.setEnabled(self.current_par > 0)
        self._anim_section = None

    def keyPressEvent(self, event):
        """Keyboard navigation support."""
        if event.key() == Qt.Key_Left:
            self._on_back_clicked()
        elif event.key() == Qt.Key_Right:
            self._on_next_clicked()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter) and self._custom_choice_active:
            self._submit_custom_choice()
        elif event.key() == Qt.Key_Escape and self._custom_choice_active:
            self._cancel_custom_choice()
        else:
            super().keyPressEvent(event)

    def _return_to_main_menu(self):
        """Return to the main menu from the game page."""
        if self._is_generating:
            return

        # Build a frameless, styled confirmation dialog
        msg_box = QMessageBox(self)
        msg_box.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setWindowTitle("Return to Main Menu")
        msg_box.setText("Are you sure you want to return to the main menu? Your progress will be saved.")
        msg_box.setStyleSheet(Style.MSGBOX)

        yes_button = msg_box.addButton("Yes", QMessageBox.YesRole)
        no_button  = msg_box.addButton("No",  QMessageBox.NoRole)

        msg_box.setFixedSize(400, 200)
        # center over main window
        geom = self.geometry()
        msg_box.move(geom.center() - msg_box.rect().center())

        msg_box.exec()

        if msg_box.clickedButton() is yes_button:
            # persist via the GameState save
            if self.engine and self.engine.state:
                self.engine.state.save_game()

            # inline reset of all UI/engine state
            self.engine = None
            self._companion_options = []
            self._companion_widgets = []
            self._chosen_companion = None
            self._is_generating = False
            self._custom_choice_active = False

            # go back to the landing page
            self.stack.setCurrentIndex(0)

    def _create_profile_sidebar(self):
        """Creates the profile sidebar widget with a fixed header and a vertically scrollable body."""
        # ——— 1) Outer container ———
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(300)
        self.sidebar.setStyleSheet(Style.SIDEBAR_STYLE)

        # inset drop-shadow
        shadow = QGraphicsDropShadowEffect(self.sidebar)
        shadow.setBlurRadius(16)
        shadow.setOffset(-4, 0)
        shadow.setColor(QColor(0, 0, 0, 160))
        self.sidebar.setGraphicsEffect(shadow)

        # ——— 2) Layout for sidebar ———
        outer = QVBoxLayout(self.sidebar)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ——— 3) Fixed header with close button ———
        header = QWidget()
        hdr_layout = QHBoxLayout(header)
        hdr_layout.setContentsMargins(8, 8, 8, 8)
        hdr_layout.addStretch()
        close_btn = QPushButton("×")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Style.TEXT};
                border: none;
                font-size: 20px;
            }}
            QPushButton:hover {{
                color: {Style.ACCENT};
            }}
        """)
        close_btn.clicked.connect(self._toggle_profile_sidebar)
        hdr_layout.addWidget(close_btn)
        outer.addWidget(header, 0)

        # ——— 4) Scroll area (vertical only) ———
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        outer.addWidget(scroll, 1)

        # ——— 5) Scrollable content widget ———
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll.setWidget(content)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # ——— 6) Player portrait & name ———
        self.player_portrait = QLabel()
        self.player_portrait.setFixedSize(240, 240)
        self.player_portrait.setAlignment(Qt.AlignCenter)
        self.player_portrait.setStyleSheet(
            f"border:2px solid {Style.PRIMARY}; border-radius:120px;"
        )
        layout.addWidget(self.player_portrait, alignment=Qt.AlignHCenter)

        self.player_name = QLabel()
        self.player_name.setFont(QFont(Style.BODY_FONT.family(), 14, QFont.Bold))
        self.player_name.setAlignment(Qt.AlignCenter)
        self.player_name.setStyleSheet(f"color: {Style.TEXT}; margin-top:8px;")
        self.player_name.setWordWrap(True)
        self.player_name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(self.player_name, alignment=Qt.AlignHCenter)

        # ——— 7) Personality analysis ———
        pers_lbl = QLabel("Personality")
        pers_lbl.setFont(QFont(Style.BODY_FONT.family(), 12, QFont.Medium))
        pers_lbl.setStyleSheet(f"color: {Style.PRIMARY}; margin-top:12px;")
        layout.addWidget(pers_lbl)

        self.personality_analysis = QLabel()
        self.personality_analysis.setFont(Style.SMALL_FONT)
        self.personality_analysis.setStyleSheet(f"color: {Style.TEXT};")
        self.personality_analysis.setWordWrap(True)
        self.personality_analysis.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Preferred
        )
        layout.addWidget(self.personality_analysis)

        # ——— 8) Separator ———
        sep0 = QFrame()
        sep0.setFrameShape(QFrame.HLine)
        sep0.setFixedHeight(1)
        sep0.setStyleSheet(f"background-color: {Style.PRIMARY}; border:none;")
        layout.addWidget(sep0)

        # ——— 9) Player stats bars ———
        BAR_WIDTH, BAR_HEIGHT = 150, 24
        self.player_stats = {}
        for stat in ["bravery", "curiosity", "empathy", "communication", "trust"]:
            lbl = QLabel(stat.capitalize())
            lbl.setFont(QFont(Style.BODY_FONT.family(), 12, QFont.Medium))
            lbl.setStyleSheet(f"color: {Style.TEXT};")
            lbl.setFixedWidth(100)

            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setFormat("")  
            bar.setFixedSize(BAR_WIDTH, BAR_HEIGHT)
            bar.setStyleSheet(Style.STAT_BAR_STYLE)

            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(5)
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(bar)
            layout.addLayout(row)
            self.player_stats[stat] = bar

        # ——— 10) Separator ———
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setFixedHeight(1)
        sep1.setStyleSheet(f"background-color: {Style.PRIMARY}; border:none;")
        layout.addWidget(sep1)

        # ——— 11) Companion portrait & name ———
        self.companion_portrait = QLabel()
        self.companion_portrait.setFixedSize(240, 240)
        self.companion_portrait.setAlignment(Qt.AlignCenter)
        self.companion_portrait.setStyleSheet(
            f"border:2px solid {Style.PRIMARY}; border-radius:120px;"
        )
        layout.addWidget(self.companion_portrait, alignment=Qt.AlignHCenter)

        self.companion_name = QLabel()
        self.companion_name.setFont(QFont(Style.BODY_FONT.family(), 14, QFont.Bold))
        self.companion_name.setAlignment(Qt.AlignCenter)
        self.companion_name.setStyleSheet(f"color: {Style.TEXT}; margin-top:8px;")
        self.companion_name.setWordWrap(True)
        self.companion_name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(self.companion_name, alignment=Qt.AlignHCenter)

        # ——— 12) Companion description ———
        self.companion_desc = QLabel()
        self.companion_desc.setFont(Style.SMALL_FONT)
        self.companion_desc.setStyleSheet(f"color: {Style.TEXT};")
        self.companion_desc.setWordWrap(True)
        self.companion_desc.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Preferred
        )
        layout.addWidget(self.companion_desc)

        # ——— 13) Companion stats bars ———
        self.companion_stats = {}
        for stat in ["trust", "fear", "affection"]:
            lbl = QLabel(stat.capitalize())
            lbl.setFont(Style.SMALL_FONT)
            lbl.setStyleSheet(f"color: {Style.TEXT};")
            lbl.setFixedWidth(100)

            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setFormat("")
            bar.setFixedSize(BAR_WIDTH, BAR_HEIGHT)
            bar.setStyleSheet(Style.STAT_BAR_STYLE)

            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(5)
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(bar)
            layout.addLayout(row)
            self.companion_stats[stat] = bar

        layout.addStretch()

        # ——— 14) Overlay & animation setup ———
        self.sidebar_overlay = QWidget(self.sidebar.parent())
        self.sidebar_overlay.setStyleSheet(Style.OVERLAY_STYLE)
        self.sidebar_overlay.hide()

        self.sidebar_animation = QPropertyAnimation(self.sidebar, b"pos")
        self.sidebar_animation.setDuration(300)
        self.sidebar_animation.setEasingCurve(QEasingCurve.OutCubic)

        return self.sidebar, self.sidebar_overlay

    def _toggle_profile_sidebar(self):
        """Toggles the profile sidebar visibility"""
        if not hasattr(self, 'sidebar'):
            return
            
        if self.sidebar.isVisible():
            self._hide_profile_sidebar()
        else:
            self._show_profile_sidebar()

    def _show_profile_sidebar(self):
        """Shows the profile sidebar with animation"""
        if not hasattr(self, 'sidebar'):
            self.sidebar, self.sidebar_overlay = self._create_profile_sidebar()
            self.stack.currentWidget().layout().addWidget(self.sidebar_overlay)
            self.stack.currentWidget().layout().addWidget(self.sidebar)
            
        self._update_profile_data()
        
        # Position sidebar off-screen to the right
        self.sidebar.move(self.width(), 0)
        self.sidebar.show()
        
        # Setup overlay
        self.sidebar_overlay.setGeometry(0, 0, self.width(), self.height())
        self.sidebar_overlay.show()
        
        # Animate sidebar in
        self.sidebar_animation.setStartValue(self.sidebar.pos())
        self.sidebar_animation.setEndValue(QPoint(self.width() - self.sidebar.width(), 0))
        self.sidebar_animation.start()

    def _hide_profile_sidebar(self):
        """Hides the profile sidebar with animation"""
        if not hasattr(self, 'sidebar') or not self.sidebar.isVisible():
            return
        
        # Animate sidebar out
        self.sidebar_animation.setStartValue(self.sidebar.pos())
        self.sidebar_animation.setEndValue(QPoint(self.width(), 0))
        self.sidebar_animation.start()
        
        # Hide overlay when animation finishes
        self.sidebar_animation.finished.connect(lambda: (
            self.sidebar.hide(),
            self.sidebar_overlay.hide(),
            self.sidebar_animation.finished.disconnect()
        ))


    def _update_profile_data(self):
        """Updates the profile sidebar with current game data, including personality analysis."""
        if not hasattr(self, 'engine') or not self.engine.state:
            return

        state = self.engine.state

        # Player name & portrait
        name = state.story_outline["player_backstory"]["name"]
        self.player_name.setText(f"{name} — You")
        img = state.character_image_urls.get(name)
        if img and os.path.isfile(img):
            pix = QPixmap(img).scaled(
                self.player_portrait.size(),
                Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            self.player_portrait.setPixmap(pix)

        # Personality analysis
        text = getattr(state, "last_personality_analysis", "").strip()
        if not text:
            text = "Make some choices to see your personality analysis here."
        self.personality_analysis.setText(text)

        # Player stats (displayed with one decimal)
        for stat, val in state.player_profile.items():
            if stat in self.player_stats:
                bar = self.player_stats[stat]
                bar.setValue(int(val * 10))         # e.g. 7.3 → 73
                bar.setFormat(f"{val:.1f}")         # display "7.3"

        # Companion data
        if state.companion_name:
            self.companion_name.setText(state.companion_name)
            self.companion_desc.setText(state.companion_description)

            cimg = state.character_image_urls.get(state.companion_name)
            if cimg and os.path.isfile(cimg):
                pix = QPixmap(cimg).scaled(
                    self.companion_portrait.size(),
                    Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
                )
                self.companion_portrait.setPixmap(pix)

            # Companion stats (also one-decimal)
            for stat, val in state.companion_profile.items():
                if stat in self.companion_stats:
                    bar = self.companion_stats[stat]
                    bar.setValue(int(val * 10))
                    bar.setFormat(f"{val:.1f}")

if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        os.chdir(os.path.dirname(sys.executable))
    app = QApplication(sys.argv)

    app.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "resources", "icon.ico")))
    window = MainWindow()
    window.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "resources", "icon.ico")))
    window.show()
    sys.exit(app.exec())