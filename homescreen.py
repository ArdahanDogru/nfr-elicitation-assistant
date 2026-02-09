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
    
    def __init__(self, title: str, description: str, icon: str = None, submenu_items: list = None, badge: str = None, parent=None):
        super().__init__(parent)
        self.original_title = title
        self.description = description
        self.callback = None
        self.submenu_items = submenu_items or []  # List of dicts: [{"title": "...", "callback": ...}]
        self.badge = badge  # Optional badge text like "START HERE"
        
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
        # Taller if has submenus (need space for buttons)
        min_height = 250 if self.submenu_items else 190
        self.setMinimumSize(280, min_height)
        self.setMaximumWidth(400)
        
        # Apply artistic stylesheet - highlight if has badge
        if self.badge:
            self.setStyleSheet("""
                MenuCard {
                    background-color: #E8F5E9;
                    border: 3px solid #4CAF50;
                    border-radius: 12px;
                    padding: 10px;
                }
                MenuCard:hover {
                    background-color: #C8E6C9;
                    border: 3px solid #388E3C;
                }
            """)
        else:
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
        title_font = QFont("Segoe UI", 14, QFont.Bold)
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
        desc_font = QFont("Segoe UI", 11)
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
        self.setMinimumSize(1400, 900)  # Larger window - about 2/3 screen
        
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
        """Create header with artistic title and subtitle"""
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
        
        parent_layout.addLayout(header_layout)
    
    def _create_menu_grid(self, parent_layout):
        """Create grid of menu cards directly on blue background"""
        # Grid layout directly without container frame
        grid_layout = QGridLayout()
        grid_layout.setSpacing(20)  # Space between cards
        grid_layout.setContentsMargins(0, 0, 0, 0)  # No extra margins
        
        # Define menu items with icons/emoji - 8 items in 4x2 grid
        menu_items = [
            {
                "title": "❓ What is this (tool) for?",
                "description": "• What should I ask?\n• How good is the response?",
                "callback": self.open_info
            },
            {
                "title": "📖 What is (NFR/FR)?",
                "description": "Look up any NFR or operationalization to start exploring",
                "callback": self.open_whats_this,
                "badge": "🚀 START HERE"
            },
            {
                "title": "🌳 What does X mean? (Decomposition)",
                "description": "Split an NFR into its decompositions to understand its structure",
                "callback": self.open_decomposition
            },
            {
                "title": "🔧 How to achieve X? (Operationalizations)",
                "description": "Explore design decisions and techniques to satisfy an NFR",
                "callback": self.open_operationalizations
            },
            {
                "title": "📚 What is the justification? (Claim)",
                "description": "See who proposed the decomposition approach and why",
                "callback": self.open_claims
            },
            {
                "title": "⚡ Possible side effects? (Contributions)",
                "description": "See which NFRs an operationalization affects",
                "callback": self.open_side_effects
            },
            {
                "title": "📋 Browse Examples",
                "description": "Explore entities, relationships, and constraints in the metamodel",
                "callback": self.open_examples,
                "submenu_items": [
                    {"title": "NFR Types", "callback": self.open_nfr_types},
                    {"title": "Operationalizing Softgoals", "callback": self.open_op_softgoals},
                    {"title": "Claim Softgoals", "callback": self.open_claim_softgoals}
                ]
            },
            {
                "title": "📋 Requirement Classification",
                "description": "Classify requirements into:\n• FR / NFR\n• their specific types",
                "callback": self.open_classification
            }
        ]
        
        # Create cards in 4x2 grid
        for i, item in enumerate(menu_items):
            row = i // 4
            col = i % 4
            
            card = MenuCard(
                title=item["title"],
                description=item["description"],
                submenu_items=item.get("submenu_items", None),
                badge=item.get("badge", None)
            )
            card.set_callback(item["callback"])
            
            grid_layout.addWidget(card, row, col)
        
        # Set column stretch to distribute space evenly (4 columns)
        for col in range(4):
            grid_layout.setColumnStretch(col, 1)
        
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
        self.operationalizations_window = OperationalizationDecompositionWindow("How to achieve X? (Operationalizations)", self)
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