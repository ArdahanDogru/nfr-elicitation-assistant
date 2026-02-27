"""
NFR Elicitation Assistant - Main Application
============================================
Modern menu-based assistant for NFR Framework analysis
"""

import sys
import threading

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QPushButton, QLabel, QFrame
)
from PySide6.QtCore import Qt, QSize, Signal, QObject
from PySide6.QtGui import QFont, QIcon, QPalette, QColor, QPixmap

# Import from same directory (flat structure)
import metamodel
from nfr_queries import getEntity
from classifier_v6 import classify_fr_nfr, classify_nfr_type, classify_fr_type
from menu_llm import MenuLLM
import ollama
from utils import format_entity_name

# Import menu windows
from menu_windows import (
    InfoWindow,
    ClassificationWindow,
    DecompositionWindow,
    AttributionWindow,
    ExamplesWindow,
    NFRTypesWindow,
    OperationalizingSoftgoalsWindow,
    ClaimSoftgoalsWindow,
    SideEffectsWindow,
    WhatsThisWindow,
    OperationalizationDecompositionWindow,
    ChatWindow,
)
# ============================================================================
# BACKGROUND LLM LOADER
# ============================================================================

class BackgroundLLMLoader(QObject):
    """Load LLM, metamodel, and classifier in background thread on startup"""
    finished = Signal(bool)
    
    def __init__(self):
        super().__init__()
        self.loaded = False
    
    def load(self):
        """Warm up the LLM and pre-load metamodel/classifier"""
        try:
            # Step 1: Pre-load metamodel (this prints output to terminal)
            print("⏳ Pre-loading metamodel...")
            import metamodel
            from nfr_queries import getEntity
            print("✅ Metamodel loaded")
            
            # Step 2: Pre-load classifier
            print("⏳ Pre-loading classifier...")
            from classifier_v6 import classify_fr_nfr, classify_nfr_type, classify_fr_type
            print("✅ Classifier loaded")
            
            # Step 3: Warm up LLM with a quick test
            print("⏳ Warming up LLM...")
            import ollama
            ollama.chat(
                model="llama3:8b",
                messages=[{"role": "user", "content": "hi"}],
                options={"num_predict": 1}
            )
            print("✅ LLM warmed up")
            
            self.loaded = True
            self.finished.emit(True)
            print("✅ All components ready!")
        except Exception as e:
            print(f"⚠ï¸ Background loading failed: {e}")
            self.finished.emit(False)



# ============================================================================
# MENU CARD AND HOME SCREEN
# ============================================================================

class MenuCard(QFrame):
    """A clickable card for each menu item - Icon centered, title below"""
    
    def __init__(self, title: str, description: str, icon: str = None, submenu_items: list = None, badge: str = None, color_scheme: str = None, parent=None):
        super().__init__(parent)
        self.original_title = title
        self.description = description
        self.callback = None
        self.submenu_items = submenu_items or []  # List of dicts: [{"title": "...", "callback": ...}]
        self.badge = badge  # Optional badge text like "START HERE"
        self.color_scheme = color_scheme  # 'green', 'blue', or None (default white)
        
        # Extract emoji/icon from title if present
        # Emojis are typically at the start, followed by space or newline
        self.icon_char = ""
        self.title_text = title
        
        # Check if first character(s) are emoji (they're usually 1-2 chars in Python)
        if title and len(title) > 1:
            # Find the first space or newline
            first_break = -1
            for i, char in enumerate(title):
                if char in ' \n':
                    first_break = i
                    break
            
            if first_break > 0:
                potential_icon = title[:first_break].strip()
                # Check if it looks like an emoji (not alphanumeric)
                if potential_icon and not potential_icon[0].isalnum():
                    self.icon_char = potential_icon
                    self.title_text = title[first_break:].strip()
        
        # Card styling - Adjusted for 4-column layout
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(0)
        self.setCursor(Qt.PointingHandCursor)
        # Fixed size for all buttons - square/tall enough to show all text
        self.setMinimumSize(300, 320)  # Width, Height - more square
        self.setMaximumSize(400, 320)  # Same height for all
        
        # Apply artistic stylesheet based on color_scheme
        if self.color_scheme == 'green':
            # Green scheme - for Verification (more pronounced border)
            self.setStyleSheet("""
                MenuCard {
                    background-color: #C8E6C9;
                    border: 5px solid #4CAF50;
                    border-radius: 12px;
                    padding: 10px;
                }
                MenuCard:hover {
                    background-color: #A5D6A7;
                    border: 5px solid #388E3C;
                }
            """)
        elif self.color_scheme == 'blue':
            # Blue scheme - for Browse Examples and Classification (more pronounced border)
            self.setStyleSheet("""
                MenuCard {
                    background-color: #BBDEFB;
                    border: 5px solid #2196F3;
                    border-radius: 12px;
                    padding: 10px;
                }
                MenuCard:hover {
                    background-color: #90CAF9;
                    border: 5px solid #1976D2;
                }
            """)
        else:
            # Default white scheme (same for all white cards including badge items)
            self.setStyleSheet("""
                MenuCard {
                    background-color: white;
                    border: 2px solid #e0e0e0;
                    border-radius: 12px;
                    padding: 10px;
                }
                MenuCard:hover {
                    background-color: #f8fbff;
                    border: 2px solid #2196F3;
                }
            """)
        
        # Layout
        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(14, 12, 14, 12)
        
        # Badge (if provided) - at the top right
        if self.badge:
            badge_label = QLabel(self.badge)
            badge_label.setStyleSheet("""
                background-color: #4CAF50;
                color: white;
                font-size: 9pt;
                font-weight: bold;
                padding: 4px 10px;
                border-radius: 10px;
            """)
            badge_label.setAlignment(Qt.AlignCenter)
            badge_label.setFixedHeight(24)
            layout.addWidget(badge_label, alignment=Qt.AlignCenter)
            layout.addSpacing(4)
        
        # Icon - LARGE and CENTERED
        if self.icon_char:
            icon_label = QLabel(self.icon_char)
            icon_font = QFont("Segoe UI Emoji", 32)  # Large emoji
            icon_label.setFont(icon_font)
            icon_label.setStyleSheet("padding: 0px; margin: 0px;")
            icon_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(icon_label, stretch=0)
        
        # Title text - centered below icon
        title_label = QLabel(self.title_text)
        title_font = QFont("Segoe UI", 22, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("""
            color: #1a237e;
            letter-spacing: 0.3px;
            padding-top: 2px;
        """)
        title_label.setWordWrap(True)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label, stretch=0)
        
        # Description - left-align if contains bullets, center otherwise
        desc_html = description.replace('\n', '<br>')
        has_bullets = '•' in description
        
        desc_label = QLabel(desc_html)
        desc_font = QFont("Segoe UI", 16)
        desc_label.setFont(desc_font)
        desc_label.setStyleSheet("""
            color: #424242;
            line-height: 1.4;
            letter-spacing: 0.2px;
            padding-top: 6px;
        """)
        desc_label.setWordWrap(True)
        # Left-align for bullet lists, center for regular text
        if has_bullets:
            desc_label.setAlignment(Qt.AlignLeft)
        else:
            desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setTextFormat(Qt.RichText)  # Enable HTML rendering
        layout.addWidget(desc_label, stretch=1)
        
        # Sub-menu buttons (if provided)
        if self.submenu_items:
            # Add a small separator
            layout.addSpacing(8)
            
            # Create a container for submenu buttons
            submenu_layout = QVBoxLayout()
            submenu_layout.setSpacing(6)
            submenu_layout.setContentsMargins(0, 0, 0, 0)
            
            for item in self.submenu_items:
                submenu_btn = QPushButton(item["title"])
                submenu_btn.setMinimumHeight(32)
                submenu_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2196F3;
                        color: white;
                        font-size: 10pt;
                        font-weight: 600;
                        border: none;
                        border-radius: 6px;
                        padding: 6px 12px;
                        text-align: center;
                    }
                    QPushButton:hover {
                        background-color: #1976D2;
                    }
                    QPushButton:pressed {
                        background-color: #1565C0;
                    }
                """)
                submenu_btn.setCursor(Qt.PointingHandCursor)
                
                # Connect callback
                if "callback" in item and item["callback"]:
                    submenu_btn.clicked.connect(item["callback"])
                
                submenu_layout.addWidget(submenu_btn)
            
            layout.addLayout(submenu_layout)
        
        layout.addStretch(1)
        self.setLayout(layout)
    

    def set_callback(self, callback):
        """Set function to call when card is clicked"""
        self.callback = callback
    
    def mousePressEvent(self, event):
        """Handle click event"""
        if self.callback:
            self.callback()
        super().mousePressEvent(event)


class HomeScreen(QMainWindow):
    """Main home screen with menu of functionalities"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NFR Elicitation AI Assistant")
        self.setMinimumSize(1600, 900)  # Larger window for 5+4 grid layout
        
        # Start background LLM loading
        self.llm_loader = BackgroundLLMLoader()
        self.llm_thread = threading.Thread(target=self.llm_loader.load, daemon=True)
        self.llm_thread.start()
        
        # Set window background
        self.setStyleSheet("QMainWindow { background-color: #2c5aa0; }")
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout with adjusted margins for more card space
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(50, 30, 50, 20)  # Left, Top, Right, Bottom
        main_layout.setSpacing(25)
        
        # Header
        self._create_header(main_layout)
        
        # Menu grid
        self._create_menu_grid(main_layout)
        
        # Footer
        self._create_footer(main_layout)
    
    def _create_header(self, parent_layout):
        """Create header with artistic title, subtitle, and Help button"""
        # Outer horizontal layout to position Help button on the right
        header_outer_layout = QHBoxLayout()
        header_outer_layout.setContentsMargins(20, 10, 20, 0)
        
        # Left spacer for balance
        header_outer_layout.addStretch(1)
        
        # Center vertical layout for title and subtitle
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)
        
        # Title - more artistic with better font
        title = QLabel("NFR Elicitation AI Assistant")
        title_font = QFont("Segoe UI", 32, QFont.Bold)
        title.setFont(title_font)
        title.setStyleSheet("""
            color: white;
            letter-spacing: 1px;
            padding: 10px;
        """)
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)
        
        # Subtitle - elegant styling
        subtitle = QLabel("Requirements Engineering powered by the NFR Framework")
        subtitle_font = QFont("Segoe UI", 13)
        subtitle.setFont(subtitle_font)
        subtitle.setStyleSheet("""
            color: #e3f2fd;
            letter-spacing: 0.5px;
            font-weight: 300;
        """)
        subtitle.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(subtitle)
        
        header_outer_layout.addLayout(header_layout)
        
        # Right spacer (smaller to make room for Help button)
        header_outer_layout.addStretch(1)
        
        # Help button on the right
        help_button = QPushButton("❓ Help")
        help_button.setMinimumSize(100, 40)
        help_button.setMaximumSize(120, 40)
        help_button.setStyleSheet("""
            QPushButton {
                background-color: #E53935;
                color: white;
                font-size: 12pt;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #C62828;
            }
            QPushButton:pressed {
                background-color: #B71C1C;
            }
        """)
        help_button.setCursor(Qt.PointingHandCursor)
        help_button.clicked.connect(self.open_info)
        
        # Add button aligned to top right
        button_container = QVBoxLayout()
        button_container.addWidget(help_button)
        button_container.addStretch()
        header_outer_layout.addLayout(button_container)
        
        parent_layout.addLayout(header_outer_layout)
    
    def _create_menu_grid(self, parent_layout):
        """Create grid of menu cards directly on blue background"""
        # Grid layout directly without container frame
        grid_layout = QGridLayout()
        grid_layout.setSpacing(25)  # Space between cards (increased for 5+4 layout)
        grid_layout.setContentsMargins(0, 0, 0, 0)  # No extra margins
        
        # Define menu items - 7 items in 4+3 grid (Verification removed)
        menu_items = [
            {
                "title": "📖 What is this NFR?",
                "description": "Enter an NFR of your choice.",
                "callback": self.open_whats_this,
                "badge": "🚀 START HERE"
            },
            {
                "title": "🌳 What does this NFR mean? (Decomposition)",
                "description": "Split an NFR into its decompositions to understand its structure",
                "callback": self.open_decomposition
            },
            {
                "title": "🔧 How to achieve this NFR? (Operationalizations)",
                "description": "Explore design decisions and techniques to satisfy an NFR",
                "callback": self.open_operationalizations
            },
            {
                "title": "⚡ Possible side effects? (Correlation Rules)",
                "description": "See which NFRs an operationalization affects",
                "callback": self.open_side_effects
            },
            {
                "title": "📚 What is the justification? (Claim)",
                "description": "See who proposed the decomposition approach and why",
                "callback": self.open_claims
            },
            {
                "title": "📋 Browse Examples",
                "description": "Explore entities, relationships, and constraints in the metamodel",
                "callback": self.open_examples,
                "color_scheme": "blue"
            },
            {
                "title": "✅ Requirement Classification",
                "description": "Classify requirements into:\n• FR / NFR\n• their specific types",
                "callback": self.open_classification,
                "color_scheme": "blue"
            }
        ]
        
        # Create cards in 4+3 grid (4 on first row, 3 centered on second row)
        # Using 8-column grid: each button spans 2 columns
        # First row: buttons at (0-1), (2-3), (4-5), (6-7)
        # Second row: empty (0), buttons at (1-2), (3-4), (5-6), empty (7)
        
        # First row: 4 buttons, each spanning 2 columns
        for i in range(4):
            card = MenuCard(
                title=menu_items[i]["title"],
                description=menu_items[i]["description"],
                submenu_items=menu_items[i].get("submenu_items", None),
                badge=menu_items[i].get("badge", None),
                color_scheme=menu_items[i].get("color_scheme", None)
            )
            card.set_callback(menu_items[i]["callback"])
            # Add button spanning 2 columns
            grid_layout.addWidget(card, 0, i * 2, 1, 2)
        
        # Second row: 3 centered buttons with empty space on sides
        # Left spacer (column 0)
        spacer_left = QWidget()
        grid_layout.addWidget(spacer_left, 1, 0)
        
        # 3 buttons, each spanning 2 columns, starting at column 1
        for i in range(3):
            card = MenuCard(
                title=menu_items[i + 4]["title"],
                description=menu_items[i + 4]["description"],
                submenu_items=menu_items[i + 4].get("submenu_items", None),
                badge=menu_items[i + 4].get("badge", None),
                color_scheme=menu_items[i + 4].get("color_scheme", None)
            )
            card.set_callback(menu_items[i + 4]["callback"])
            # Add button spanning 2 columns, offset by 1
            grid_layout.addWidget(card, 1, (i * 2) + 1, 1, 2)
        
        # Right spacer (column 7)
        spacer_right = QWidget()
        grid_layout.addWidget(spacer_right, 1, 7)
        
        # Set equal stretch for all columns
        for col in range(8):
            grid_layout.setColumnStretch(col, 1)
        
        # 8-column grid with equal stretch
        # First row: buttons span columns (0-1), (2-3), (4-5), (6-7)
        # Second row: empty (0), buttons span (1-2), (3-4), (5-6), empty (7)
        
        # Set row stretch
        for row in range(2):
            grid_layout.setRowStretch(row, 1)
        
        parent_layout.addLayout(grid_layout, stretch=1)
    
    def _create_footer(self, parent_layout):
        """Create footer with additional info and logo"""
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 10, 0, 0)
        
        # Footer text on left
        footer = QLabel("Master's Thesis Project - UT Dallas - 2024/2025")
        footer_font = QFont("Arial", 9)
        footer.setFont(footer_font)
        footer.setStyleSheet("color: #e0e0e0;")
        footer.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        footer_layout.addWidget(footer)
        
        # Spacer
        footer_layout.addStretch(1)
        
        # Logo on right (if available) - CLICKABLE
        try:
            from PySide6.QtGui import QPixmap, QIcon
            
            # Create clickable logo button
            logo_button = QPushButton()
            logo_button.setFlat(True)
            logo_button.setCursor(Qt.PointingHandCursor)
            logo_button.setStyleSheet("""
                QPushButton {
                    border: none;
                    background: transparent;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 8px;
                }
            """)
            
            # Try to load logo (you can change the path)
            pixmap = QPixmap("re_lab_logo.png")  # Change filename as needed
            if not pixmap.isNull():
                # Scale logo to reasonable size
                scaled_pixmap = pixmap.scaled(120, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                logo_button.setIcon(QIcon(scaled_pixmap))
                logo_button.setIconSize(scaled_pixmap.size())
                logo_button.setFixedSize(scaled_pixmap.size())
                
                # Make it clickable - open URL
                logo_button.clicked.connect(lambda: self.open_logo_url())
                
                footer_layout.addWidget(logo_button)
        except:
            # If logo not found, just skip it
            pass
        
        parent_layout.addLayout(footer_layout)
    
    # Menu item callbacks
    def open_info(self):
        """Open Info module - What is this tool for?"""
        print("Opening Info...")
        self.hide()
        self.info_window = InfoWindow("What is this (tool) for?", self)
        self.info_window.show()
    
    def open_whats_this(self):
        """Open What is (NFR/FR)? module"""
        print("Opening What is NFR/FR...")
        self.hide()
        self.whats_this_window = WhatsThisWindow("What is (NFR/FR)?", self)
        self.whats_this_window.show()
    
    def open_decomposition(self):
        """Open Decomposition module - General (all types)"""
        print("Opening Decomposition (General)...")
        self.hide()
        self.decomposition_window = DecompositionWindow("What does X mean? (Decomposition)", self)
        self.decomposition_window.show()
    
    def open_claims(self):
        """Open Claims/Justification module"""
        print("Opening Claims...")
        self.hide()
        self.claims_window = AttributionWindow("What is the justification? (Claim)", self)
        self.claims_window.show()
    
    def open_operationalizations(self):
        """Open How to achieve X? - shows operationalizations for NFRs"""
        print("Opening How to achieve X? (Operationalizations)...")
        self.hide()
        self.operationalizations_window = OperationalizationDecompositionWindow("Operationalizations - Functional Decisions", self)
        self.operationalizations_window.show()
    
    def open_examples(self):
        """Open Examples Browser module"""
        print("Opening Examples Browser...")
        self.hide()
        self.examples_window = ExamplesWindow("Browse Examples", self)
        self.examples_window.show()
    
    def open_nfr_types(self):
        """Open NFR Types sub-menu"""
        print("Opening NFR Types...")
        self.hide()
        self.nfr_types_window = NFRTypesWindow("NFR Type Examples", self)
        self.nfr_types_window.show()
    
    def open_op_softgoals(self):
        """Open Operationalizing Softgoals sub-menu"""
        print("Opening Operationalizing Softgoals...")
        self.hide()
        self.op_softgoals_window = OperationalizingSoftgoalsWindow("Operationalizing Softgoal Examples", self)
        self.op_softgoals_window.show()
    
    def open_claim_softgoals(self):
        """Open Claim Softgoals sub-menu"""
        print("Opening Claim Softgoals...")
        self.hide()
        self.claim_softgoals_window = ClaimSoftgoalsWindow("Claim Softgoal Examples", self)
        self.claim_softgoals_window.show()
    
    def open_side_effects(self):
        """Open Side Effects module - Contributions"""
        print("Opening Side Effects...")
        self.hide()
        self.side_effects_window = SideEffectsWindow("Possible side effects? (Contributions)", self)
        self.side_effects_window.show()
    
    
    def open_classification(self):
        """Open Requirement Classification module"""
        print("Opening Classification...")
        self.hide()
        self.classification_window = ClassificationWindow("Requirement Classification", self)
        self.classification_window.show()
    
    def open_chat(self):
        """Open Chat window"""
        print("Opening Chat...")
        self.hide()
        self.chat_window = ChatWindow("Chat - NFR Framework Assistant", self)
        self.chat_window.show()
    
    def open_logo_url(self):
        """Open URL when logo is clicked"""
        try:
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl
            
            # Change this URL to your desired link
            url = "https://github.com/yourusername/nfr-framework"  # Update with actual URL
            
            QDesktopServices.openUrl(QUrl(url))
            print(f"Opening URL: {url}")
            
        except Exception as e:
            print(f"Error opening URL: {e}")


def main():
    """Launch the NFR Elicitation Assistant"""
    print("="*70)
    print("NFR ELICITATION AI ASSISTANT")
    print("="*70)
    print("Version: 2.0 (Menu-based)")
    print("Framework: PySide6")
    print("="*70)
    print()
    print("💡 TIP: Place 're_lab_logo.png' in the same directory to show logo")
    print()
    
    # Create application
    app = QApplication(sys.argv)
    
    # Set application-wide font
    app_font = QFont("Arial", 10)
    app.setFont(app_font)
    
    # Create and show home screen
    home = HomeScreen()
    home.show()
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()