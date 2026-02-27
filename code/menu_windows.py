"""
NFR Elicitation Assistant - Menu Windows Module
===============================================
Contains all menu item window classes
"""

import threading
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QPushButton, QLabel, QFrame, QTextEdit, QLineEdit,
    QScrollArea, QSizePolicy, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt, Slot, QSize, QMetaObject, Q_ARG, Signal, QObject, QTimer
from PySide6.QtGui import QFont, QColor

from utils import (
    format_entity_name,
    validate_requirement,
    get_nfr_and_children,
    fuzzy_match_entity
)
from nfr_queries import getClaimsFor

# Import MenuLLM for GenAI-powered responses
try:
    from menu_llm import MenuLLM
    MENU_LLM_AVAILABLE = True
except ImportError:
    print("⚠️ MenuLLM not available - responses will use raw metamodel output")
    MENU_LLM_AVAILABLE = False
    MenuLLM = None


class ModuleWindow(QMainWindow):
    """Base window class for all module features with back button"""
    
    def __init__(self, module_name: str, parent_home_screen):
        super().__init__()
        self.module_name = module_name
        self.parent_home_screen = parent_home_screen
        
        # Window setup
        self.setWindowTitle(f"NFR Assistant - {module_name}")
        self.setMinimumSize(1200, 850)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create back button bar
        self._create_back_bar(main_layout)
        
        # Create content area (to be filled by subclasses)
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background-color: #f5f5f5;")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.addWidget(self.content_widget)
        
        # Setup module-specific content (override in subclass)
        self.setup_content()
    
    def _create_back_bar(self, parent_layout):
        """Create top bar with back button"""
        back_bar = QWidget()
        back_bar.setFixedHeight(60)
        back_bar.setStyleSheet("background-color: #2196F3;")
        
        bar_layout = QHBoxLayout(back_bar)
        bar_layout.setContentsMargins(15, 0, 15, 0)
        
        # Back button
        back_btn = QPushButton("<- Back to Menu")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976D2;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14pt;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.clicked.connect(self.return_to_menu)
        bar_layout.addWidget(back_btn)
        
        # Module title
        title_label = QLabel(self.module_name)
        title_label.setStyleSheet("""
            color: white;
            font-size: 16pt;
            font-weight: bold;
            padding-left: 20px;
        """)
        bar_layout.addWidget(title_label)
        
        bar_layout.addStretch()
        
        parent_layout.addWidget(back_bar)
    
    def setup_content(self):
        """Override this method in subclasses to add module-specific content"""
        # Default: show placeholder
        label = QLabel(f"{self.module_name}\n\nModule content will be implemented here.")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            font-size: 14pt;
            color: #666;
            padding: 50px;
        """)
        self.content_layout.addWidget(label)
    
    def return_to_menu(self):
        """Close module window and show home screen"""
        self.close()
        self.parent_home_screen.show()
    
    def closeEvent(self, event):
        """Handle window close (X button)"""
        # Only show homescreen if not navigating to another pipeline window
        if not getattr(self, '_navigating_pipeline', False):
            self.parent_home_screen.show()
        event.accept()


# Specialized Module Windows

class InfoWindow(ModuleWindow):
    """Window explaining what this tool is for - concise table + quality cards"""
    
    def setup_content(self):
        from PySide6.QtWidgets import QLabel, QFrame, QScrollArea, QGridLayout, QSizePolicy, QTableWidget, QTableWidgetItem, QHeaderView
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        content_layout.setContentsMargins(25, 20, 25, 20)
        
        # Title
        title = QLabel("🎯 NFR Framework Assistant")
        title.setStyleSheet("font-size: 22pt; font-weight: bold; color: #1565C0;")
        title.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(title)
        
        # One-line intro
        intro = QLabel("A requirements engineering tool grounded on the NFR Framework metamodel.")
        intro.setStyleSheet("font-size: 12pt; color: #555; margin-bottom: 5px;")
        intro.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(intro)
        
        # ============================================================
        # SECTION 1: What should I ask? - TABLE FORMAT
        # ============================================================
        section1_title = QLabel("❓ What should I ask?")
        section1_title.setStyleSheet("font-size: 14pt; font-weight: bold; color: #1565C0; padding-top: 10px;")
        section1_title.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(section1_title)
        
        # Create styled table
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Menu Item", "You Type", "You Get"])
        table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #1565C0;
                color: white;
                font-weight: bold;
                font-size: 12pt;
                padding: 8px;
                border: none;
            }
        """)
        
        # Table data - ALL menu items
        rows = [
            ("📖 What is (NFR/FR)?", '"Performance" or "Encryption"', "Comprehensive info about any NFR or operationalization"),
            ("🌳 Decomposition", '"Security" or "Performance"', "Sub-types (e.g., Security â†’ Confidentiality, Integrity, Availability)"),
            ("🔧 Operationalizations", '"Performance" or "Security"', "Techniques that achieve it (e.g., Caching, Indexing)"),
            ("⚡ Side Effects", '"Indexing" or "Encryption"', "Which NFRs the technique helps or hurts"),
            ("ðŸ“š Claims", '"Security"', "Academic sources for decompositions"),
            ("📋 Classify Requirements", '"The system shall respond in 2 seconds"', "FR or NFR + specific type (e.g., Performance)"),
            ("🔍 Browse Examples", "Select a category", "Explore 47+ NFR types, operationalizations, claims"),
            ("💬 Chat", '"What is Usability?"', "Free-form answers from the metamodel"),
        ]
        
        table.setRowCount(len(rows))
        
        for row_idx, (menu, input_text, output) in enumerate(rows):
            # Menu item
            menu_item = QTableWidgetItem(menu)
            menu_item.setFlags(menu_item.flags() & ~Qt.ItemIsEditable)
            
            # Input
            input_item = QTableWidgetItem(input_text)
            input_item.setFlags(input_item.flags() & ~Qt.ItemIsEditable)
            input_item.setForeground(Qt.darkBlue)
            
            # Output
            output_item = QTableWidgetItem(output)
            output_item.setFlags(output_item.flags() & ~Qt.ItemIsEditable)
            output_item.setForeground(Qt.darkGreen)
            
            table.setItem(row_idx, 0, menu_item)
            table.setItem(row_idx, 1, input_item)
            table.setItem(row_idx, 2, output_item)
        
        # Table styling
        table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ccc;
                border-radius: 5px;
                font-size: 11pt;
                gridline-color: #ddd;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:alternate {
                background-color: #f5f5f5;
            }
        """)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        table.setMaximumHeight(300)
        
        content_layout.addWidget(table)
        
        # ============================================================
        # SECTION 2: Guided Pipeline Note
        # ============================================================
        section2_title = QLabel("🧭 Guided Exploration Pipeline")
        section2_title.setStyleSheet("font-size: 14pt; font-weight: bold; color: #2E7D32; padding-top: 15px;")
        section2_title.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(section2_title)
        
        pipeline_note = QLabel(
            "The first 5 menu items form a <b>guided pipeline</b>. Start from \"📖 What is (NFR/FR)?\" "
            "and use the <b>â†’ Next</b> buttons to explore systematically. Each window also has a <b>â† Back</b> button "
            "to retrace your steps."
        )
        pipeline_note.setWordWrap(True)
        pipeline_note.setStyleSheet("font-size: 11pt; color: #444; padding: 10px; background-color: #E8F5E9; border-radius: 8px;")
        pipeline_note.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(pipeline_note)
        
        # ============================================================
        # SECTION 3: How good is the response? - EQUAL SIZE CARDS
        # ============================================================
        section3_title = QLabel("✅ How good is the response?")
        section3_title.setStyleSheet("font-size: 14pt; font-weight: bold; color: #F57C00; padding-top: 15px;")
        section3_title.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(section3_title)
        
        # Quality grid - 4 columns
        quality_grid = QGridLayout()
        quality_grid.setSpacing(12)
        
        CARD_TITLE_STYLE = "font-size: 12pt; font-weight: bold; color: #333; margin-bottom: 3px;"
        CARD_CONTENT_STYLE = "font-size: 10pt; color: #444; line-height: 1.4;"
        
        quality_cards = [
            {
                "title": "🎯 Grounded",
                "color": "#E8F5E9",
                "border": "#A5D6A7",
                "content": "Answers from the <b>NFR Framework metamodel</b>, not general AI knowledge."
            },
            {
                "title": "ðŸ“Š Accuracy",
                "color": "#E3F2FD",
                "border": "#90CAF9",
                "content": "<b>~0.74 F1 score</b> on PROMISE dataset. Shows ⚠ï¸ when uncertain."
            },
            {
                "title": "🔗 Traceable",
                "color": "#FFF3E0",
                "border": "#FFCC80",
                "content": "Decompositions cite sources. Click <b>Details</b> to see function calls."
            },
            {
                "title": "⚠ï¸ Limits",
                "color": "#FFEBEE",
                "border": "#EF9A9A",
                "content": "47+ NFR types. Custom NFRs may not be recognized."
            }
        ]
        
        for col, card_info in enumerate(quality_cards):
            card = QFrame()
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            card.setMinimumHeight(80)
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {card_info['color']};
                    border: 2px solid {card_info['border']};
                    border-radius: 8px;
                }}
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(2)
            card_layout.setContentsMargins(10, 8, 10, 8)
            
            card_title = QLabel(card_info['title'])
            card_title.setStyleSheet(CARD_TITLE_STYLE)
            card_title.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(card_title)
            
            text_label = QLabel(card_info['content'])
            text_label.setStyleSheet(CARD_CONTENT_STYLE)
            text_label.setWordWrap(True)
            text_label.setTextFormat(Qt.RichText)
            text_label.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(text_label)
            
            quality_grid.addWidget(card, 0, col)
            quality_grid.setColumnStretch(col, 1)
        
        content_layout.addLayout(quality_grid)
        
        # Footer tip
        tip_label = QLabel("💡 <b>Tip:</b> Start with the green \"📖 What is (NFR/FR)?\" card on the home screen to begin exploring!")
        tip_label.setWordWrap(True)
        tip_label.setStyleSheet("font-size: 11pt; color: #666; padding-top: 10px;")
        tip_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(tip_label)
        
        content_layout.addStretch()
        self.content_layout.addWidget(content_widget)


class ClassificationWindow(ModuleWindow):
    """Window for requirement classification"""
    
    def setup_content(self):
        # Initialize MenuLLM for AI-powered responses
        self.menu_llm = MenuLLM() if MENU_LLM_AVAILABLE else None

        from PySide6.QtWidgets import QTextEdit, QLabel, QHBoxLayout, QMessageBox
        
        # Store last classification category and type
        self.last_category = None
        self.current_nfr_type = None  # Store the classified NFR type for navigation
        
        # Instruction label
        instruction = QLabel("Enter a requirement to classify:")
        instruction.setStyleSheet("font-size: 14pt; font-weight: bold; color: #333; margin-bottom: 10px;")
        self.content_layout.addWidget(instruction)
        
        # Text input - SHORTER
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Example: The system shall respond within 2 seconds...")
        self.text_input.setMinimumHeight(120)  # Reduced from 200
        self.text_input.setMaximumHeight(150)
        self.text_input.setStyleSheet("""
            QTextEdit {
                font-size: 13pt;
                padding: 15px;
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: white;
            }
            QTextEdit:focus {
                border: 2px solid #2196F3;
            }
        """)
        self.content_layout.addWidget(self.text_input)
        
        # Two buttons side by side
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        # Button 1: FR vs NFR Classification
        fr_nfr_btn = QPushButton("ðŸ“Š Classify: FR vs NFR")
        fr_nfr_btn.setMinimumHeight(50)
        fr_nfr_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 13pt;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 15px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        fr_nfr_btn.setCursor(Qt.PointingHandCursor)
        fr_nfr_btn.clicked.connect(self.classify_fr_nfr)
        button_layout.addWidget(fr_nfr_btn)
        
        # Button 2: Specific NFR Type Classification
        nfr_type_btn = QPushButton("â„¹ï¸Â Classify: Specific Type")
        nfr_type_btn.setMinimumHeight(50)
        nfr_type_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 13pt;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 15px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """)
        nfr_type_btn.setCursor(Qt.PointingHandCursor)
        nfr_type_btn.clicked.connect(self.classify_nfr_type)
        button_layout.addWidget(nfr_type_btn)
        
        self.content_layout.addLayout(button_layout)
        
        # Results area - QTextEdit for scrollable and selectable text
        self.results_label = QTextEdit()
        self.results_label.setReadOnly(True)
        self.results_label.setPlaceholderText("Results will appear here...")
        self.results_label.setStyleSheet("""
            QTextEdit {
                font-size: 14pt;
                padding: 20px;
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 20px;
            }
        """)
        # Make text selectable
        self.results_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
        )
        self.content_layout.addWidget(self.results_label)
        
        
        # Navigation buttons (initially hidden)
        self.nav_layout = QHBoxLayout()
        self.nav_layout.setSpacing(15)
        
        # "Continue Pipeline" label
        self.pipeline_label = QLabel("🔗 <b>Continue Exploring:</b>")
        self.pipeline_label.setStyleSheet("font-size: 13pt; color: #333; margin-top: 15px;")
        self.pipeline_label.setVisible(False)
        
        # Button 1: What does X mean? (Decomposition)
        self.decomp_btn = QPushButton("📖 What does X mean?")
        self.decomp_btn.setMinimumHeight(45)
        self.decomp_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-size: 12pt;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 12px;
            }
            QPushButton:hover {
                background-color: #FB8C00;
            }
            QPushButton:pressed {
                background-color: #F57C00;
            }
        """)
        self.decomp_btn.setCursor(Qt.PointingHandCursor)
        self.decomp_btn.clicked.connect(self.go_to_decomposition)
        self.decomp_btn.setVisible(False)
        
        # Button 2: How to achieve X? (Operationalizations)
        self.operationalize_btn = QPushButton("🔧 How to achieve X?")
        self.operationalize_btn.setMinimumHeight(45)
        self.operationalize_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                font-size: 12pt;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 12px;
            }
            QPushButton:hover {
                background-color: #8E24AA;
            }
            QPushButton:pressed {
                background-color: #7B1FA2;
            }
        """)
        self.operationalize_btn.setCursor(Qt.PointingHandCursor)
        self.operationalize_btn.clicked.connect(self.go_to_operationalizations)
        self.operationalize_btn.setVisible(False)
        
        # Add buttons to navigation layout
        self.nav_layout.addWidget(self.decomp_btn)
        self.nav_layout.addWidget(self.operationalize_btn)
        
        # Add to main layout
        self.content_layout.addWidget(self.pipeline_label)
        self.content_layout.addLayout(self.nav_layout)
        
        self.content_layout.addStretch()
        
        self.content_layout.addStretch()
    
    def classify_fr_nfr(self):
        """Classify requirement as FR or NFR (Stage 1)"""
        from PySide6.QtWidgets import QMessageBox
        
        text = self.text_input.toPlainText().strip()
        if not text:
            self.results_label.setText("⚠ï¸ Please enter a requirement first")
            return
        
        # Validate input
        if not validate_requirement(text):
            QMessageBox.warning(
                self,
                "Invalid Input",
                "This doesn't look like a requirement.\n\nPlease enter a proper requirement statement with keywords like 'shall', 'must', 'system', etc."
            )
            return
        
        # Show loading indicator immediately
        self.results_label.setText("⏳ Classifying FR vs NFR...")
        QApplication.processEvents()  # Force UI update
        
        # Run classification in background thread
        def do_classify():
            try:
                from classifier_v6 import classify_fr_nfr
                result = classify_fr_nfr(text)
                
                # Store category for next classification
                self.last_category = result
                
                # Format result
                if result == 'NFR':
                    response = "✅ Classification: Non-Functional Requirement (NFR)\n\n"
                    response += "This requirement describes a quality attribute or constraint on how the system should perform.\n\n"
                    response += "💡 Use 'Classify: Specific Type' to identify which NFR type (Performance, Security, etc.)"
                elif result == 'FR':
                    response = "✅ Classification: Functional Requirement (FR)\n\n"
                    response += "This requirement describes what the system should do - a specific function or behavior.\n\n"
                    response += "💡 Use 'Classify: Specific Type' to identify which FR type (Process, Display, etc.)"
                else:
                    response = f"Classification: {result}"
                
                return response
                
            except ImportError:
                return "⚠ï¸ Error: classifier_v6.py not found\n\nMake sure the classifier module is in the project directory."
            except Exception as e:
                return f"⚠ï¸ Error during classification:\n{str(e)}"
        
        # Run in thread and update UI
        import threading
        def run_and_update():
            result = do_classify()
            from PySide6.QtCore import QMetaObject, Qt as QtCore_Qt, Q_ARG
            QMetaObject.invokeMethod(self.results_label, "setText", 
                                    QtCore_Qt.QueuedConnection, Q_ARG(str, result))
        
        thread = threading.Thread(target=run_and_update, daemon=True)
        thread.start()
    
    def classify_nfr_type(self):
        """Classify into specific type (FR or NFR type based on previous classification)"""
        from PySide6.QtWidgets import QMessageBox
        
        text = self.text_input.toPlainText().strip()
        if not text:
            self.results_label.setText("⚠ï¸ Please enter a requirement first")
            return
        
        # Validate input
        if not validate_requirement(text):
            QMessageBox.warning(
                self,
                "Invalid Input",
                "This doesn't look like a requirement.\n\nPlease enter a proper requirement statement with keywords like 'shall', 'must', 'system', etc."
            )
            return
        
        # Show loading indicator immediately
        self.results_label.setText("⏳ Classifying specific type...")
        QApplication.processEvents()  # Force UI update
        
        # Run classification in background thread
        def do_classify():
            try:
                from classifier_v6 import classify_fr_nfr, classify_nfr_type, classify_fr_type
                from nfr_queries import getEntity
                
                # Determine category (use stored or classify again)
                if self.last_category is None:
                    category = classify_fr_nfr(text)
                    self.last_category = category
                else:
                    category = self.last_category
                
                if category == "NFR":
                    # Classify NFR type - now returns (type, warning)
                    result, warning = classify_nfr_type(text)
                    formatted_name = format_entity_name(result)
                    
                    # Check if warning (LLM fallback)
                    if warning:
                        response = f"⚠ï¸ **NFR Type: {formatted_name}**\n\n"
                        response += f"**Note:** {warning}\n\n"
                        response += "The classifier could not find an exact match in the metamodel.\n"
                        response += "The above type is suggested by the LLM but may not be in the knowledge base."
                    else:
                        response = f"✅ **NFR Type: {formatted_name}**\n\n"
                        
                        # Get description from metamodel
                        entity = getEntity(result)
                        if entity and hasattr(entity, 'description'):
                            response += f"**Description:** {entity.description}\n\n"
                        
                        response += "This is a non-functional requirement focusing on quality attributes."
                
                else:  # FR
                    # Classify FR type - now returns (type, warning)
                    result, warning = classify_fr_type(text)
                    formatted_name = format_entity_name(result)
                    
                    if warning:
                        response = f"⚠ï¸ **FR Type: {formatted_name}**\n\n"
                        response += f"**Note:** {warning}\n\n"
                        response += "The classifier used LLM fallback for this type."
                    else:
                        response = f"✅ **FR Type: {formatted_name}**\n\n"
                        response += "This is a functional requirement describing system behavior."
                
                
                # Store the classified type for navigation (only if NFR)
                self.current_nfr_type = result if category == "NFR" else None
                return response
                
            except ImportError:
                return "⚠ï¸ Error: classifier_v6.py not found\n\nMake sure the classifier module is in the project directory."
            except Exception as e:
                return f"⚠ï¸ Error during classification:\n{str(e)}"
        
        # Run in thread and update UI
        import threading
        def run_and_update():
            result_text = do_classify()
            from PySide6.QtCore import QMetaObject, Qt as QtCore_Qt, Q_ARG
            QMetaObject.invokeMethod(self.results_label, "setText", 
                                    QtCore_Qt.QueuedConnection, Q_ARG(str, result_text))
            
            # If NFR classification successful, show navigation buttons
            if self.last_category == "NFR" and self.current_nfr_type and "✅" in result_text:
                QMetaObject.invokeMethod(
                    self, "_show_navigation_buttons",
                    QtCore_Qt.QueuedConnection
                )
        thread = threading.Thread(target=run_and_update, daemon=True)
        thread.start()



    @Slot()
    def _show_navigation_buttons(self):
        """Show navigation buttons after successful NFR classification"""
        self.pipeline_label.setVisible(True)
        self.decomp_btn.setVisible(True)
        self.operationalize_btn.setVisible(True)
    
    def go_to_decomposition(self):
        """Navigate to NFR Decomposition window"""
        if self.current_nfr_type:
            # Clean up entity name
            clean_name = self.current_nfr_type.replace('Type', '').replace('Softgoal', '')
            
            # Set flag to prevent homescreen from showing on close
            self._navigating_pipeline = True
            self.hide()
            
            self.decomp_window = NFRDecompositionWindow(
                "What does X mean? (Decomposition)",
                self.parent_home_screen,
                initial_entity=clean_name
            )
            self.decomp_window.show()
            self.close()
    
    def go_to_operationalizations(self):
        """Navigate to Operationalization Decomposition window"""
        if self.current_nfr_type:
            # Clean up entity name
            clean_name = self.current_nfr_type.replace('Type', '').replace('Softgoal', '')
            
            # Set flag to prevent homescreen from showing on close
            self._navigating_pipeline = True
            self.hide()
            
            self.operationalize_window = OperationalizationDecompositionWindow(
                "How can we do it? (Operationalizing Softgoals)",
                self.parent_home_screen,
                initial_entity=clean_name
            )
            self.operationalize_window.show()
            self.close()
    


class DecompositionWindow(ModuleWindow):
    """Window for requirement decomposition"""
    
    def setup_content(self):
        # Initialize MenuLLM for AI-powered responses
        self.menu_llm = MenuLLM() if MENU_LLM_AVAILABLE else None

        from PySide6.QtWidgets import QLineEdit, QLabel
        
        # Instruction label
        instruction = QLabel("Enter an NFR type to see its decompositions:")
        instruction.setStyleSheet("font-size: 14pt; font-weight: bold; color: #333; margin-bottom: 10px;")
        self.content_layout.addWidget(instruction)
        
        # Single-line input
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Example: Performance, Security, Usability...")
        self.text_input.setMinimumHeight(60)
        self.text_input.setStyleSheet("""
            QLineEdit {
                font-size: 14pt;
                padding: 15px;
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
            }
        """)
        self.content_layout.addWidget(self.text_input)
        
        # Decompose button
        decompose_btn = QPushButton("🌳 Show Decompositions")
        decompose_btn.setMinimumHeight(50)
        decompose_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                font-size: 14pt;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 15px;
            }
            QPushButton:hover {
                background-color: #8E24AA;
            }
            QPushButton:pressed {
                background-color: #7B1FA2;
            }
        """)
        decompose_btn.setCursor(Qt.PointingHandCursor)
        decompose_btn.clicked.connect(self.show_decompositions)
        self.content_layout.addWidget(decompose_btn)
        
        # Results area - QTextEdit for scrollable and selectable text
        from PySide6.QtWidgets import QTextEdit
        self.results_label = QTextEdit()
        self.results_label.setReadOnly(True)
        self.results_label.setPlaceholderText("Results will appear here...")
        self.results_label.setMinimumHeight(400)  # Expanded output box
        self.results_label.setStyleSheet("""
            QTextEdit {
                font-size: 14pt;
                padding: 20px;
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 20px;
            }
        """)
        # Make text selectable
        self.results_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
        )
        self.content_layout.addWidget(self.results_label, stretch=1)  # Give stretch priority
    
    def show_decompositions(self):
        """Show decompositions for the given NFR type with LLM explanation"""
        text = self.text_input.text().strip()
        if not text:
            self.results_label.setText("⚠️ Please enter an NFR type first")
            return
        
        # Show loading
        self.results_label.setText("⏳ Searching for decompositions...")
        QApplication.processEvents()
        
        try:
            from nfr_queries import getEntity, getDecompositionsFor, getEntityName, format_entity_name
            
            # Fuzzy match
            matched_name, suggestion = fuzzy_match_entity(text)
            if not matched_name:
                self.results_label.setText(suggestion)
                return
            
            entity = getEntity(matched_name)
            decomps = getDecompositionsFor(entity)
            
            if not decomps:
                self.results_label.setText(f"ℹ️ {format_entity_name(matched_name)} has no decomposition methods defined.")
                return
            
            # Build context for LLM
            context = f"{format_entity_name(matched_name)} has {len(decomps)} decomposition method(s):\n\n"
            for i, decomp in enumerate(decomps, 1):
                context += f"{i}. {decomp.name}\n"
                if hasattr(decomp, 'offspring'):
                    offspring_names = [format_entity_name(o.__name__) for o in decomp.offspring]
                    context += f"   Offspring: {', '.join(offspring_names)}\n"
                context += "\n"
            
            # Use MenuLLM for natural explanation
            if self.menu_llm:
                llm_response = self.menu_llm.respond(
                    action_type="decompose",
                    user_input=format_entity_name(matched_name),
                    metamodel_context=context
                )
                self.results_label.setText(suggestion + llm_response)
            else:
                self.results_label.setText(suggestion + context)
            
            # Store current entity for navigation
            self.current_entity = matched_name
            
            # Show navigation button to "How to achieve X?"
            self.show_navigation_button()
            
        except Exception as e:
            import traceback
            self.results_label.setText(f"❌ Error: {str(e)}\n\n{traceback.format_exc()}")
    
    def show_navigation_button(self):
        """Show navigation button to next step in pipeline"""
        # Check if button already exists
        if not hasattr(self, 'next_step_btn'):
            self.next_step_btn = QPushButton("🔧 How to achieve [X]? →")
            self.next_step_btn.setMinimumHeight(50)
            self.next_step_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    font-size: 13pt;
                    font-weight: bold;
                    border: none;
                    border-radius: 8px;
                    padding: 12px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #3d8b40;
                }
            """)
            self.next_step_btn.setCursor(Qt.PointingHandCursor)
            self.next_step_btn.clicked.connect(self.go_to_operationalizations)
            self.content_layout.addWidget(self.next_step_btn)
        
        # Update button text
        if hasattr(self, 'current_entity'):
            from nfr_queries import format_entity_name
            self.next_step_btn.setText(f"🔧 How to achieve {format_entity_name(self.current_entity)}? →")
        
        self.next_step_btn.setVisible(True)
    
    def go_to_operationalizations(self):
        """Navigate to How to achieve X? window"""
        if hasattr(self, 'current_entity'):
            self.hide()
            self.op_window = OperationalizationDecompositionWindow(
                "Operationalizations - Functional Decisions",
                self.parent_home_screen,
                initial_entity=self.current_entity
            )
            self.op_window.show()
    
class AttributionWindow(ModuleWindow):
    """Window for attribution (According to whom?)"""
    
    def __init__(self, module_name: str, parent_home_screen, initial_entity: str = None, came_from: list = None):
        self.initial_entity = initial_entity
        self.current_entity = None
        self.came_from = came_from or []  # List of (WindowClass, entity_name) tuples for back navigation history
        super().__init__(module_name, parent_home_screen)
        
        # If initial entity provided, auto-fill and search
        if self.initial_entity:
            self.text_input.setText(self.initial_entity)
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, self.find_attribution)
    
    def setup_content(self):
        # Initialize MenuLLM for AI-powered responses
        self.menu_llm = MenuLLM() if MENU_LLM_AVAILABLE else None

        from PySide6.QtWidgets import QLineEdit, QLabel
        
        # Back button (if came from somewhere in pipeline)
        self.back_btn = QPushButton("â† Back")
        self.back_btn.setMinimumHeight(40)
        self.back_btn.setMaximumWidth(100)
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: #78909C;
                color: white;
                font-size: 11pt;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #607D8B;
            }
            QPushButton:pressed {
                background-color: #546E7A;
            }
        """)
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.clicked.connect(self.go_back)
        self.back_btn.setVisible(bool(self.came_from))
        self.content_layout.addWidget(self.back_btn)
        
        # Instruction label
        instruction = QLabel("Enter a softgoal to see its decompositions and sources:")
        instruction.setStyleSheet("font-size: 14pt; font-weight: bold; color: #333; margin-bottom: 10px;")
        self.content_layout.addWidget(instruction)
        
        # Single-line input
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Example: Performance, Security, Usability...")
        self.text_input.setMinimumHeight(60)
        self.text_input.setStyleSheet("""
            QLineEdit {
                font-size: 14pt;
                padding: 15px;
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
            }
        """)
        self.content_layout.addWidget(self.text_input)
        
        # Attribution button
        attribution_btn = QPushButton("🌳 Show Decompositions & Sources")
        attribution_btn.setMinimumHeight(50)
        attribution_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-size: 14pt;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 15px;
            }
            QPushButton:hover {
                background-color: #FB8C00;
            }
            QPushButton:pressed {
                background-color: #F57C00;
            }
        """)
        attribution_btn.setCursor(Qt.PointingHandCursor)
        attribution_btn.clicked.connect(self.find_attribution)
        self.content_layout.addWidget(attribution_btn)
        
        # Results area - QTextEdit for scrollable and selectable text
        from PySide6.QtWidgets import QTextEdit
        self.results_label = QTextEdit()
        self.results_label.setReadOnly(True)
        self.results_label.setPlaceholderText("Results will appear here...")
        self.results_label.setMinimumHeight(400)  # Expanded output box
        self.results_label.setStyleSheet("""
            QTextEdit {
                font-size: 14pt;
                padding: 20px;
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 20px;
            }
        """)
        # Make text selectable
        self.results_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
        )
        self.content_layout.addWidget(self.results_label, stretch=1)  # Give stretch priority

    def find_attribution(self):
        """Show decompositions and their sources/attributions - CLAIMS EMPHASIZED"""
        text = self.text_input.text().strip()
        if not text:
            self.results_label.setText("⚠ï¸ Please enter a softgoal first")
            return
        
        # Show loading indicator immediately
        self.results_label.setText("⏳ Searching for justifications and sources...")
        QApplication.processEvents()  # Force UI update
        
        # Run in background thread
        def do_search():
            try:
                from nfr_queries import getEntity, getDecompositionsFor, getEntityName
                import metamodel
                import inspect
                
                # Use fuzzy matching helper
                matched_name, suggestion = fuzzy_match_entity(text)
                if not matched_name:
                    return suggestion  # This is the error message
                
                entity = getEntity(matched_name)
                entity_name = getEntityName(entity)
                
                # Get decompositions
                decomps = getDecompositionsFor(entity)
                
                response = suggestion  # Start with suggestion if any
                
                # ================================================================
                # CASE 1: Entity has decompositions (NFR/FR Types)
                # ================================================================
                if decomps:
                    # Collect all claims for this entity type
                    all_claims_for_type = []
                    parent_type_name = entity_name.replace('Type', '').replace('Softgoal', '')
                    
                    # Collect ALL ClaimSoftgoals (matching will filter later)
                    for name, obj in inspect.getmembers(metamodel):
                        if hasattr(metamodel, 'ClaimSoftgoal'):
                            if isinstance(obj, metamodel.ClaimSoftgoal):
                                argument_str = getattr(obj, 'argument', '')
                                if argument_str:
                                    all_claims_for_type.append({
                                        'name': name,
                                        'argument': argument_str
                                    })
                    
                    # Match claims to decompositions by content (what they decompose into)
                    
                    for i, decomp in enumerate(decomps, 1):
                        # Get claims using universal query function
                        claims = getClaimsFor(decomp)
                        
                        # Format offspring names
                        offspring_names = []
                        if hasattr(decomp, 'offspring'):
                            offspring_names = [format_entity_name(o.__name__) for o in decomp.offspring]
                        
                        decomp_desc = getattr(decomp, 'description', '')
                        
                        # Display decomposition with its claim
                        source_description = "Not specified"
                        if claims:
                            source_description = claims[0].argument
                        
                        response += f"📚 {source_description}\n"
                        response += "-" * 50 + "\n\n"
                        
                        # Description (how it's decomposed)
                        if decomp_desc:
                            response += f"   **Description**: {decomp_desc}\n\n"
                        
                        # What it decomposes into
                        if offspring_names:
                            response += f"   **Decomposes into**: {', '.join(offspring_names)}\n\n"
                        
                        response += "\n"
                    
                    return response
                
                # ================================================================
                # CASE 2: No decompositions - Check if it's an operationalization
                # ================================================================
                else:
                    parent_type_name = entity_name.replace('Type', '').replace('Softgoal', '')
                    
                    # Search for claims about this entity
                    # Try FLEXIBLE matching - match if either string contains the other
                    operationalization_claims = []
                    
                    for name, obj in inspect.getmembers(metamodel):
                        if hasattr(metamodel, 'ClaimSoftgoal'):
                            if isinstance(obj, metamodel.ClaimSoftgoal):
                                claim_topic = getattr(obj, 'topic', None)
                                if claim_topic:
                                    topic_str = str(claim_topic)
                                    
                                    # Extract just the topic name from SoftgoalTopic('TopicName')
                                    import re
                                    match = re.search(r"SoftgoalTopic\('([^']+)'\)", topic_str)
                                    if match:
                                        topic_name = match.group(1)
                                    else:
                                        topic_name = topic_str
                                    
                                    # Remove spaces and make lowercase for matching
                                    topic_normalized = topic_name.lower().replace(' ', '').replace('-', '')
                                    entity_normalized = parent_type_name.lower().replace(' ', '').replace('-', '')
                                    
                                    # Match if one contains the other
                                    if (entity_normalized in topic_normalized or 
                                        topic_normalized in entity_normalized):
                                        
                                        argument_str = getattr(obj, 'argument', '')
                                        operationalization_claims.append({
                                            'name': name,
                                            'argument': argument_str,
                                            'obj': obj
                                        })
                    
                    if operationalization_claims:
                        # Show contribution claims WITHOUT header
                        for claim in operationalization_claims:
                            # Get claim argument (source)
                            source_description = "Not specified"
                            if claim.get('argument'):
                                source_description = claim['argument']
                            
                            response += f"ðŸ“š {source_description}\n"
                            response += "-" * 50 + "\n\n"
                            
                            # Check what this operationalization contributes to
                            try:
                                from nfr_queries import checkContributionToAnyNFR
                                contrib_result = checkContributionToAnyNFR(parent_type_name)
                                
                                if contrib_result and contrib_result.get('contributes'):
                                    response += "   **Operationalizes**:\n"
                                    for target, contrib_type in contrib_result.get('details', []):
                                        response += f"   • {target} ({contrib_type})\n"
                                    response += "\n"
                            except ImportError:
                                # If function doesn't exist, just show the claim
                                pass
                            
                            response += "\n"
                        
                        return response
                    else:
                        # No claims found for this entity
                        formatted_name = format_entity_name(entity_name)
                        return f"â„¹ï¸ {formatted_name} has no decomposition methods or associated claims defined in the metamodel."
            
            except ImportError as ie:
                return f"❌ Import Error: {str(ie)}\n\nMake sure nfr_queries.py is available."
            except Exception as e:
                import traceback
                return f"❌ Error: {str(e)}\n\n{traceback.format_exc()}"
        
        # Run search in thread
        import threading
        def run_and_update():
            result = do_search()
            from PySide6.QtCore import QMetaObject, Qt as QtCore_Qt, Q_ARG
            QMetaObject.invokeMethod(self.results_label, "setText", 
                                    QtCore_Qt.QueuedConnection, Q_ARG(str, result))
        
        thread = threading.Thread(target=run_and_update, daemon=True)
        thread.start()


    def go_back(self):
        """Navigate back to previous window in history"""
        if self.came_from:
            # Pop the last window from history
            window_type, entity = self.came_from[-1]
            remaining_history = self.came_from[:-1]
            
            self._navigating_pipeline = True
            self.hide()
            
            if window_type == 'SideEffectsWindow':
                self.back_window = SideEffectsWindow(
                    "Possible side effects? (Contributions)", self.parent_home_screen,
                    initial_entity=entity,
                    came_from=remaining_history
                )
            elif window_type == 'OperationalizationDecompositionWindow':
                self.back_window = OperationalizationDecompositionWindow(
                    "Operationalization Decompositions", self.parent_home_screen,
                    initial_entity=entity,
                    came_from=remaining_history
                )
            elif window_type == 'NFRDecompositionWindow':
                self.back_window = NFRDecompositionWindow(
                    "NFR Decompositions", self.parent_home_screen,
                    initial_entity=entity,
                    came_from=remaining_history
                )
            elif window_type == 'WhatsThisWindow':
                self.back_window = WhatsThisWindow(
                    "What is this?", self.parent_home_screen,
                    initial_entity=entity,
                    came_from=remaining_history
                )
            else:
                self.parent_home_screen.show()
                self.close()
                return
            
            self.back_window.show()
            self.close()


# ============================================================================
# BROWSE EXAMPLES WINDOWS
# Replace OperationalizationWindow with these 4 windows
# ============================================================================


class ExamplesWindow(ModuleWindow):
    """Main window for browsing all metamodel examples"""
    
    def setup_content(self):
        # Initialize MenuLLM for AI-powered responses
        self.menu_llm = MenuLLM() if MENU_LLM_AVAILABLE else None

        from PySide6.QtWidgets import QLabel, QComboBox, QPushButton, QTextEdit, QLineEdit, QHBoxLayout
        
        # Title
        title = QLabel("Browse Metamodel Examples")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #1565C0; margin-bottom: 10px;")
        self.content_layout.addWidget(title)
        
        # Description
        desc = QLabel("Explore entities, relationships, and constraints in the NFR Framework metamodel")
        desc.setStyleSheet("font-size: 12pt; color: #666; margin-bottom: 20px;")
        self.content_layout.addWidget(desc)
        
        # Category selection
        category_label = QLabel("Select category:")
        category_label.setStyleSheet("font-size: 13pt; font-weight: bold; color: #333; margin-top: 10px;")
        self.content_layout.addWidget(category_label)
        
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "NFR Types",
            "Operationalizing Softgoals",
            "Functional Requirement Types",
            "Claim Softgoals",
            "Decomposition Methods",
            "Contribution Links (Relationships)",
            "Correlation Links (Argumentation)"
        ])
        self.category_combo.setMinimumHeight(40)
        self.category_combo.setStyleSheet("""
            QComboBox {
                font-size: 13pt;
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: white;
            }
            QComboBox:focus {
                border: 2px solid #2196F3;
            }
        """)
        self.content_layout.addWidget(self.category_combo)
        
        # Show Examples button
        show_btn = QPushButton("📋 Show Examples")
        show_btn.setMinimumHeight(50)
        show_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14pt;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 12px;
                margin-top: 15px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        show_btn.setCursor(Qt.PointingHandCursor)
        show_btn.clicked.connect(self.show_examples)
        self.content_layout.addWidget(show_btn)
        
        # Results area
        self.results_label = QTextEdit()
        self.results_label.setReadOnly(True)
        self.results_label.setPlaceholderText("Examples will appear here...")
        self.results_label.setMinimumHeight(250)
        self.results_label.setStyleSheet("""
            QTextEdit {
                font-size: 13pt;
                padding: 15px;
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 15px;
            }
        """)
        self.results_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
        )
        self.content_layout.addWidget(self.results_label, stretch=1)
        
        # Details section
        details_layout = QHBoxLayout()
        
        details_label = QLabel("Enter number for details:")
        details_label.setStyleSheet("font-size: 12pt; color: #333;")
        details_layout.addWidget(details_label)
        
        self.detail_input = QLineEdit()
        self.detail_input.setPlaceholderText("e.g., 1")
        self.detail_input.setMaximumWidth(100)
        self.detail_input.setMinimumHeight(35)
        self.detail_input.setStyleSheet("""
            QLineEdit {
                font-size: 12pt;
                padding: 5px;
                border: 2px solid #ddd;
                border-radius: 5px;
            }
        """)
        details_layout.addWidget(self.detail_input)
        
        detail_btn = QPushButton("🔝 Show Details")
        detail_btn.setMinimumHeight(35)
        detail_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 11pt;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        detail_btn.setCursor(Qt.PointingHandCursor)
        detail_btn.clicked.connect(self.show_details)
        details_layout.addWidget(detail_btn)
        
        details_layout.addStretch()
        self.content_layout.addLayout(details_layout)
        
        # Details display area
        self.details_label = QTextEdit()
        self.details_label.setReadOnly(True)
        self.details_label.setPlaceholderText("Select an item number and click 'Show Details' to see more information...")
        self.details_label.setMinimumHeight(150)
        self.details_label.setStyleSheet("""
            QTextEdit {
                font-size: 12pt;
                padding: 15px;
                background-color: #f5f5f5;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
            }
        """)
        self.details_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
        )
        self.content_layout.addWidget(self.details_label, stretch=1)
        
        # Store current examples for detail lookup
        self.current_examples = []
    
    def show_examples(self):
        """Show examples for selected category"""
        category = self.category_combo.currentText()
        self.results_label.setText(f"⏳ Loading {category}...")
        QApplication.processEvents()
        
        def do_query():
            try:
                import metamodel
                import inspect
                from nfr_queries import getEntityName, format_entity_name
                
                examples = []
                
                if category == "NFR Types":
                    # Find all NFRSoftgoalType subclasses
                    for name, obj in inspect.getmembers(metamodel):
                        if inspect.isclass(obj) and hasattr(metamodel, 'NFRSoftgoalType'):
                            try:
                                if issubclass(obj, metamodel.NFRSoftgoalType) and obj != metamodel.NFRSoftgoalType:
                                    if not name.endswith('MetaClass') and 'Type' in name:
                                        examples.append((name, obj))
                            except TypeError:
                                pass
                
                elif category == "Operationalizing Softgoals":
                    # Find all OperationalizingSoftgoalType subclasses
                    for name, obj in inspect.getmembers(metamodel):
                        if inspect.isclass(obj) and hasattr(metamodel, 'OperationalizingSoftgoalType'):
                            try:
                                if issubclass(obj, metamodel.OperationalizingSoftgoalType) and obj != metamodel.OperationalizingSoftgoalType:
                                    if not name.endswith('MetaClass') and 'Type' in name:
                                        examples.append((name, obj))
                            except TypeError:
                                pass
                
                elif category == "Functional Requirement Types":
                    # Find all FunctionalRequirementType subclasses
                    for name, obj in inspect.getmembers(metamodel):
                        if inspect.isclass(obj) and hasattr(metamodel, 'FunctionalRequirementType'):
                            try:
                                if issubclass(obj, metamodel.FunctionalRequirementType) and obj != metamodel.FunctionalRequirementType:
                                    if not name.endswith('MetaClass'):
                                        examples.append((name, obj))
                            except TypeError:
                                pass
                
                elif category == "Claim Softgoals":
                    # Find all ClaimSoftgoal instances
                    for name, obj in inspect.getmembers(metamodel):
                        if hasattr(metamodel, 'ClaimSoftgoal'):
                            if isinstance(obj, metamodel.ClaimSoftgoal):
                                examples.append((name, obj))
                
                elif category == "Decomposition Methods":
                    # Find all decomposition method instances
                    for name, obj in inspect.getmembers(metamodel):
                        if hasattr(metamodel, 'NFRDecompositionMethod'):
                            if isinstance(obj, metamodel.NFRDecompositionMethod):
                                examples.append((name, obj))
                        elif hasattr(metamodel, 'OperationalizationDecompositionMethod'):
                            if isinstance(obj, metamodel.OperationalizationDecompositionMethod):
                                examples.append((name, obj))
                
                elif category == "Contribution Links (Relationships)":
                    # Find all Contribution instances
                    for name, obj in inspect.getmembers(metamodel):
                        if hasattr(metamodel, 'Contribution'):
                            if isinstance(obj, metamodel.Contribution):
                                examples.append((name, obj))
                
                elif category == "Correlation Links (Argumentation)":
                    # Find all Correlation instances
                    for name, obj in inspect.getmembers(metamodel):
                        if hasattr(metamodel, 'Correlation'):
                            if isinstance(obj, metamodel.Correlation):
                                examples.append((name, obj))
                
                # Store for detail lookup
                self.current_examples = examples
                
                # Format output
                if examples:
                    response = f"🔝 {category.upper()}\n\n"
                    response += f"Found {len(examples)} example(s):\n\n"
                    
                    for i, (name, obj) in enumerate(examples, 1):
                        # Format the name nicely
                        display_name = format_entity_name(name) if 'Type' in name else name
                        response += f"{i}. {display_name}\n"
                    
                    response += f"\n💡 Enter a number and click 'Show Details' to see more information."
                else:
                    response = f"â„¹ï¸ No examples found for {category}"
                
                return response
                
            except Exception as e:
                import traceback
                return f"❌ Error: {str(e)}\n\n{traceback.format_exc()}"
        
        # Run in thread
        def run_and_update():
            result = do_query()
            QMetaObject.invokeMethod(self.results_label, "setText", 
                                    Qt.QueuedConnection, Q_ARG(str, result))
        
        thread = threading.Thread(target=run_and_update, daemon=True)
        thread.start()

    def show_details(self):
        try:
            num = int(self.detail_input.text().strip())
            if num < 1 or num > len(self.current_examples):
                self.details_label.setText(f"❌ Please enter a number between 1 and {len(self.current_examples)}")
                return
            
            name, obj = self.current_examples[num - 1]
            from nfr_queries import getDecompositionsFor, getEntityName, format_entity_name as fmt_name
            import metamodel
            import inspect
            
            # Get type classification
            classification = "Unknown"
            if inspect.isclass(obj):
                try:
                    if hasattr(metamodel, 'NFRSoftgoalType') and issubclass(obj, metamodel.NFRSoftgoalType):
                        classification = "NFR (Non-Functional Requirement)"
                    elif hasattr(metamodel, 'FunctionalRequirementType') and issubclass(obj, metamodel.FunctionalRequirementType):
                        classification = "Functional Requirement"
                    elif hasattr(metamodel, 'OperationalizingSoftgoalType') and issubclass(obj, metamodel.OperationalizingSoftgoalType):
                        classification = "Operationalizing Softgoal"
                    elif hasattr(metamodel, 'OperationalizingType') and issubclass(obj, metamodel.OperationalizingType):
                        classification = "Operationalizing Softgoal"
                except (TypeError, AttributeError):
                    pass
            
            # Get all decomposition methods
            decomp_info = ""
            if inspect.isclass(obj):
                decomps = getDecompositionsFor(obj)
                if decomps:
                    decomp_info = f"\n\nHas {len(decomps)} decomposition method(s):\n\n"
                    for i, decomp in enumerate(decomps, 1):
                        decomp_name = getattr(decomp, 'name', f'Decomposition {i}')
                        decomp_info += f"{i}. {decomp_name}\n"
                        if hasattr(decomp, 'offspring') and decomp.offspring:
                            offspring_names = [fmt_name(o.__name__) for o in decomp.offspring]
                            decomp_info += f"   Offspring: {', '.join(offspring_names)}\n"
                        decomp_info += "\n"
            
            # Combine context
            combined_context = f"Type: {classification}{decomp_info}"
            
            # Pass through MenuLLM
            self.details_label.setText("⏳ Generating explanation...")
            QApplication.processEvents()

            # Use QTimer to allow UI update before LLM generation
            def _generate_and_update():
                if self.menu_llm:
                    try:
                        # DEBUG: Print context
                        print()
                        print("="*70)
                        print("BROWSE EXAMPLES (ExamplesWindow) - LLM INPUT DEBUG")
                        print("="*70)
                        print("Action Type: browse_entity")
                        print("User Input:", name)
                        print()
                        print("Context being sent to LLM:")
                        print("-"*70)
                        print(combined_context)
                        print("-"*70)
                        
                        llm_response = self.menu_llm.respond(
                            action_type="browse_entity",
                            user_input=name,
                            metamodel_context=combined_context
                        )
                        self.details_label.setText(llm_response)
                    except Exception:
                        # Fallback to raw context on LLM error
                        fallback = f"📋 {name}\n{'='*60}\n\n{combined_context}"
                        self.details_label.setText(fallback)
                else:
                    fallback = f"📋 {name}\n{'='*60}\n\n{combined_context}"
                    self.details_label.setText(fallback)
            
            QTimer.singleShot(50, _generate_and_update)
        except ValueError:
            self.details_label.setText("❌ Please enter a valid number")
        except Exception as e:
            import traceback
            self.details_label.setText(f"❌ Error: {str(e)}\n\n{traceback.format_exc()}")


class NFRTypesWindow(ModuleWindow):
    """Sub-menu window for browsing NFR Types"""
    
    def setup_content(self):
        # Initialize MenuLLM for AI-powered responses
        self.menu_llm = MenuLLM() if MENU_LLM_AVAILABLE else None

        from PySide6.QtWidgets import QLabel, QPushButton, QTextEdit, QLineEdit, QHBoxLayout
        
        # Title
        title = QLabel("NFR Type Examples")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #1565C0; margin-bottom: 10px;")
        self.content_layout.addWidget(title)
        
        # Description
        desc = QLabel("Browse all Non-Functional Requirement types in the metamodel")
        desc.setStyleSheet("font-size: 12pt; color: #666; margin-bottom: 20px;")
        self.content_layout.addWidget(desc)
        
        # Load button
        load_btn = QPushButton("📋 Load NFR Types")
        load_btn.setMinimumHeight(50)
        load_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-size: 14pt;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 12px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        load_btn.setCursor(Qt.PointingHandCursor)
        load_btn.clicked.connect(self.load_examples)
        self.content_layout.addWidget(load_btn)
        
        # Results area
        self.results_label = QTextEdit()
        self.results_label.setReadOnly(True)
        self.results_label.setPlaceholderText("Click 'Load NFR Types' to see examples...")
        self.results_label.setMinimumHeight(250)
        self.results_label.setStyleSheet("""
            QTextEdit {
                font-size: 13pt;
                padding: 15px;
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 15px;
            }
        """)
        self.results_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        self.content_layout.addWidget(self.results_label, stretch=1)
        
        # Details section
        details_layout = QHBoxLayout()
        details_label = QLabel("Enter number for details:")
        details_label.setStyleSheet("font-size: 12pt; color: #333;")
        details_layout.addWidget(details_label)
        
        self.detail_input = QLineEdit()
        self.detail_input.setPlaceholderText("e.g., 1")
        self.detail_input.setMaximumWidth(100)
        self.detail_input.setMinimumHeight(35)
        self.detail_input.setStyleSheet("""
            QLineEdit {
                font-size: 12pt;
                padding: 5px;
                border: 2px solid #ddd;
                border-radius: 5px;
            }
        """)
        details_layout.addWidget(self.detail_input)
        
        detail_btn = QPushButton("🔝 Show Details")
        detail_btn.setMinimumHeight(35)
        detail_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 11pt;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        detail_btn.setCursor(Qt.PointingHandCursor)
        detail_btn.clicked.connect(self.show_details)
        details_layout.addWidget(detail_btn)
        details_layout.addStretch()
        self.content_layout.addLayout(details_layout)
        
        # Details display
        self.details_label = QTextEdit()
        self.details_label.setReadOnly(True)
        self.details_label.setPlaceholderText("Details will appear here...")
        self.details_label.setMinimumHeight(150)
        self.details_label.setStyleSheet("""
            QTextEdit {
                font-size: 12pt;
                padding: 15px;
                background-color: #f5f5f5;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
            }
        """)
        self.details_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        self.content_layout.addWidget(self.details_label, stretch=1)
        
        self.current_examples = []
    
    def load_examples(self):
        self.results_label.setText("⏳ Loading NFR Types...")
        QApplication.processEvents()
        
        def do_query():
            try:
                import metamodel
                import inspect
                from nfr_queries import format_entity_name
                
                examples = []
                for name, obj in inspect.getmembers(metamodel):
                    if inspect.isclass(obj) and hasattr(metamodel, 'NFRSoftgoalType'):
                        try:
                            if issubclass(obj, metamodel.NFRSoftgoalType) and obj != metamodel.NFRSoftgoalType:
                                if not name.endswith('MetaClass') and 'Type' in name:
                                    examples.append((name, obj))
                        except TypeError:
                            pass
                
                self.current_examples = examples
                
                if examples:
                    response = f"🔝 NFR TYPES\n\nFound {len(examples)} NFR type(s):\n\n"
                    for i, (name, obj) in enumerate(examples, 1):
                        display_name = format_entity_name(name)
                        response += f"{i}. {display_name}\n"
                    response += "\n💡 Enter a number and click 'Show Details'"
                else:
                    response = "â„¹ï¸ No NFR types found"
                
                return response
            except Exception as e:
                import traceback
                return f"❌ Error: {str(e)}\n\n{traceback.format_exc()}"
        
        def run_and_update():
            result = do_query()
            QMetaObject.invokeMethod(self.results_label, "setText", Qt.QueuedConnection, Q_ARG(str, result))
        
        thread = threading.Thread(target=run_and_update, daemon=True)
        thread.start()
    
    def show_details(self):
        try:
            num = int(self.detail_input.text().strip())
            if num < 1 or num > len(self.current_examples):
                self.details_label.setText(f"❌ Please enter a number between 1 and {len(self.current_examples)}")
                return
            
            name, obj = self.current_examples[num - 1]
            from nfr_queries import whatIs, format_entity_name
            
            # Use whatIs() - same as "What is X?" - no docstrings!
            self.details_label.setText("⏳ Looking up information...")
            QApplication.processEvents()
            
            # Get classification and all decomposition methods
            from nfr_queries import getDecompositionsFor, getEntityName, format_entity_name as fmt_name
            import metamodel
            import inspect
            
            # Get type classification
            classification = "Unknown"
            if inspect.isclass(obj):
                try:
                    if hasattr(metamodel, 'NFRSoftgoalType') and issubclass(obj, metamodel.NFRSoftgoalType):
                        classification = "NFR (Non-Functional Requirement)"
                    elif hasattr(metamodel, 'FunctionalRequirementType') and issubclass(obj, metamodel.FunctionalRequirementType):
                        classification = "Functional Requirement"
                    elif hasattr(metamodel, 'OperationalizingSoftgoalType') and issubclass(obj, metamodel.OperationalizingSoftgoalType):
                        classification = "Operationalizing Softgoal"
                    elif hasattr(metamodel, 'OperationalizingType') and issubclass(obj, metamodel.OperationalizingType):
                        classification = "Operationalizing Softgoal"
                except (TypeError, AttributeError):
                    pass
            
            # Get all decomposition methods (not just union of children)
            decomp_info = ""
            if inspect.isclass(obj):
                decomps = getDecompositionsFor(obj)
                if decomps:
                    decomp_info = f"\n\nHas {len(decomps)} decomposition method(s):\n\n"
                    for i, decomp in enumerate(decomps, 1):
                        decomp_name = getattr(decomp, 'name', f'Decomposition {i}')
                        decomp_info += f"{i}. {decomp_name}\n"
                        if hasattr(decomp, 'offspring') and decomp.offspring:
                            offspring_names = [fmt_name(o.__name__) for o in decomp.offspring]
                            decomp_info += f"   Offspring: {', '.join(offspring_names)}\n"
                        decomp_info += "\n"
            
            # Combine context
            combined_context = f"Type: {classification}{decomp_info}"
            
            # Use MenuLLM to generate natural explanation
            def _generate_and_update():
                if self.menu_llm:
                    try:
                        # DEBUG: Print context and action_type
                        print("="*70)
                        print("BROWSE EXAMPLES - LLM INPUT DEBUG")
                        print("="*70)
                        print("Action Type: browse_entity")
                        print("User Input:", format_entity_name(name))
                        print()
                        print("Context being sent to LLM:")
                        print("-"*70)
                        print(combined_context)
                        print("-"*70)
                        
                        llm_response = self.menu_llm.respond(
                            action_type="browse_entity",
                            user_input=format_entity_name(name),
                            metamodel_context=combined_context
                        )
                        
                        print()
                        print("LLM Response:")
                        print("-"*70)
                        print(llm_response)
                        print("="*70)
                        
                        self.details_label.setText(llm_response)
                    except Exception:
                        # Fallback to raw info on LLM error
                        fallback = f"📋 {format_entity_name(name)}\n{'='*60}\n\n{combined_context}"
                        self.details_label.setText(fallback)
                else:
                    fallback = f"📋 {format_entity_name(name)}\n{'='*60}\n\n{combined_context}"
                    self.details_label.setText(fallback)
            
            QTimer.singleShot(50, _generate_and_update)
        except ValueError:
            self.details_label.setText("❌ Please enter a valid number")
        except Exception as e:
            import traceback
            self.details_label.setText(f"❌ Error: {str(e)}\n\n{traceback.format_exc()}")


class OperationalizingSoftgoalsWindow(ModuleWindow):
    """Sub-menu window for browsing Operationalizing Softgoals"""
    
    def setup_content(self):
        # Initialize MenuLLM for AI-powered responses
        self.menu_llm = MenuLLM() if MENU_LLM_AVAILABLE else None

        from PySide6.QtWidgets import QLabel, QPushButton, QTextEdit, QLineEdit, QHBoxLayout
        
        title = QLabel("Operationalizing Softgoal Examples")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #1565C0; margin-bottom: 10px;")
        self.content_layout.addWidget(title)
        
        desc = QLabel("Browse all Operationalizing Softgoal types in the metamodel")
        desc.setStyleSheet("font-size: 12pt; color: #666; margin-bottom: 20px;")
        self.content_layout.addWidget(desc)
        
        load_btn = QPushButton("📋 Load Operationalizing Softgoals")
        load_btn.setMinimumHeight(50)
        load_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                font-size: 14pt;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 12px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        load_btn.setCursor(Qt.PointingHandCursor)
        load_btn.clicked.connect(self.load_examples)
        self.content_layout.addWidget(load_btn)
        
        self.results_label = QTextEdit()
        self.results_label.setReadOnly(True)
        self.results_label.setPlaceholderText("Click 'Load Operationalizing Softgoals' to see examples...")
        self.results_label.setMinimumHeight(250)
        self.results_label.setStyleSheet("""
            QTextEdit {
                font-size: 13pt;
                padding: 15px;
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 15px;
            }
        """)
        self.results_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        self.content_layout.addWidget(self.results_label, stretch=1)
        
        details_layout = QHBoxLayout()
        details_label = QLabel("Enter number for details:")
        details_label.setStyleSheet("font-size: 12pt; color: #333;")
        details_layout.addWidget(details_label)
        
        self.detail_input = QLineEdit()
        self.detail_input.setPlaceholderText("e.g., 1")
        self.detail_input.setMaximumWidth(100)
        self.detail_input.setMinimumHeight(35)
        self.detail_input.setStyleSheet("""
            QLineEdit {
                font-size: 12pt;
                padding: 5px;
                border: 2px solid #ddd;
                border-radius: 5px;
            }
        """)
        details_layout.addWidget(self.detail_input)
        
        detail_btn = QPushButton("🔝 Show Details")
        detail_btn.setMinimumHeight(35)
        detail_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 11pt;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        detail_btn.setCursor(Qt.PointingHandCursor)
        detail_btn.clicked.connect(self.show_details)
        details_layout.addWidget(detail_btn)
        details_layout.addStretch()
        self.content_layout.addLayout(details_layout)
        
        self.details_label = QTextEdit()
        self.details_label.setReadOnly(True)
        self.details_label.setPlaceholderText("Details will appear here...")
        self.details_label.setMinimumHeight(150)
        self.details_label.setStyleSheet("""
            QTextEdit {
                font-size: 12pt;
                padding: 15px;
                background-color: #f5f5f5;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
            }
        """)
        self.details_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        self.content_layout.addWidget(self.details_label, stretch=1)
        
        self.current_examples = []
    
    def load_examples(self):
        self.results_label.setText("⏳ Loading Operationalizing Softgoals...")
        QApplication.processEvents()
        
        def do_query():
            try:
                import metamodel
                import inspect
                from nfr_queries import format_entity_name
                
                examples = []
                for name, obj in inspect.getmembers(metamodel):
                    if inspect.isclass(obj) and hasattr(metamodel, 'OperationalizingSoftgoalType'):
                        try:
                            if issubclass(obj, metamodel.OperationalizingSoftgoalType) and obj != metamodel.OperationalizingSoftgoalType:
                                if not name.endswith('MetaClass') and 'Type' in name:
                                    examples.append((name, obj))
                        except TypeError:
                            pass
                
                self.current_examples = examples
                
                if examples:
                    response = f"🔝 OPERATIONALIZING SOFTGOALS\n\nFound {len(examples)} operationalizing softgoal(s):\n\n"
                    for i, (name, obj) in enumerate(examples, 1):
                        display_name = format_entity_name(name)
                        response += f"{i}. {display_name}\n"
                    response += "\n💡 Enter a number and click 'Show Details'"
                else:
                    response = "â„¹ï¸ No operationalizing softgoals found"
                
                return response
            except Exception as e:
                import traceback
                return f"❌ Error: {str(e)}\n\n{traceback.format_exc()}"
        
        def run_and_update():
            result = do_query()
            QMetaObject.invokeMethod(self.results_label, "setText", Qt.QueuedConnection, Q_ARG(str, result))
        
        thread = threading.Thread(target=run_and_update, daemon=True)
        thread.start()
    
    def show_details(self):
        try:
            num = int(self.detail_input.text().strip())
            if num < 1 or num > len(self.current_examples):
                self.details_label.setText(f"❌ Please enter a number between 1 and {len(self.current_examples)}")
                return
            
            name, obj = self.current_examples[num - 1]
            from nfr_queries import whatIs, format_entity_name
            
            # Use whatIs() - same as "What is X?" - no docstrings!
            self.details_label.setText("⏳ Looking up information...")
            QApplication.processEvents()
            
            # Get classification and all decomposition methods
            from nfr_queries import getDecompositionsFor, getEntityName, format_entity_name as fmt_name
            import metamodel
            import inspect
            
            # Get type classification
            classification = "Unknown"
            if inspect.isclass(obj):
                try:
                    if hasattr(metamodel, 'NFRSoftgoalType') and issubclass(obj, metamodel.NFRSoftgoalType):
                        classification = "NFR (Non-Functional Requirement)"
                    elif hasattr(metamodel, 'FunctionalRequirementType') and issubclass(obj, metamodel.FunctionalRequirementType):
                        classification = "Functional Requirement"
                    elif hasattr(metamodel, 'OperationalizingSoftgoalType') and issubclass(obj, metamodel.OperationalizingSoftgoalType):
                        classification = "Operationalizing Softgoal"
                    elif hasattr(metamodel, 'OperationalizingType') and issubclass(obj, metamodel.OperationalizingType):
                        classification = "Operationalizing Softgoal"
                except (TypeError, AttributeError):
                    pass
            
            # Get all decomposition methods (not just union of children)
            decomp_info = ""
            if inspect.isclass(obj):
                decomps = getDecompositionsFor(obj)
                if decomps:
                    decomp_info = f"\n\nHas {len(decomps)} decomposition method(s):\n\n"
                    for i, decomp in enumerate(decomps, 1):
                        decomp_name = getattr(decomp, 'name', f'Decomposition {i}')
                        decomp_info += f"{i}. {decomp_name}\n"
                        if hasattr(decomp, 'offspring') and decomp.offspring:
                            offspring_names = [fmt_name(o.__name__) for o in decomp.offspring]
                            decomp_info += f"   Offspring: {', '.join(offspring_names)}\n"
                        decomp_info += "\n"
            
            # Combine context
            combined_context = f"Type: {classification}{decomp_info}"
            
            # Use MenuLLM to generate natural explanation
            def _generate_and_update():
                if self.menu_llm:
                    try:
                        # DEBUG: Print context and action_type
                        print("="*70)
                        print("BROWSE EXAMPLES - LLM INPUT DEBUG")
                        print("="*70)
                        print("Action Type: browse_entity")
                        print("User Input:", format_entity_name(name))
                        print()
                        print("Context being sent to LLM:")
                        print("-"*70)
                        print(combined_context)
                        print("-"*70)
                        
                        llm_response = self.menu_llm.respond(
                            action_type="browse_entity",
                            user_input=format_entity_name(name),
                            metamodel_context=combined_context
                        )
                        
                        print()
                        print("LLM Response:")
                        print("-"*70)
                        print(llm_response)
                        print("="*70)
                        
                        self.details_label.setText(llm_response)
                    except Exception:
                        # Fallback to raw info on LLM error
                        fallback = f"📋 {format_entity_name(name)}\n{'='*60}\n\n{combined_context}"
                        self.details_label.setText(fallback)
                else:
                    fallback = f"📋 {format_entity_name(name)}\n{'='*60}\n\n{combined_context}"
                    self.details_label.setText(fallback)
            
            QTimer.singleShot(50, _generate_and_update)
        except ValueError:
            self.details_label.setText("❌ Please enter a valid number")
        except Exception as e:
            import traceback
            self.details_label.setText(f"❌ Error: {str(e)}\n\n{traceback.format_exc()}")


class ClaimSoftgoalsWindow(ModuleWindow):
    """Sub-menu window for browsing Claim Softgoals"""
    
    def setup_content(self):
        # Initialize MenuLLM for AI-powered responses
        self.menu_llm = MenuLLM() if MENU_LLM_AVAILABLE else None

        from PySide6.QtWidgets import QLabel, QPushButton, QTextEdit, QLineEdit, QHBoxLayout
        
        title = QLabel("Claim Softgoal Examples")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #1565C0; margin-bottom: 10px;")
        self.content_layout.addWidget(title)
        
        desc = QLabel("Browse all Claim Softgoal instances in the metamodel")
        desc.setStyleSheet("font-size: 12pt; color: #666; margin-bottom: 20px;")
        self.content_layout.addWidget(desc)
        
        load_btn = QPushButton("📋 Load Claim Softgoals")
        load_btn.setMinimumHeight(50)
        load_btn.setStyleSheet("""
            QPushButton {
                background-color: #00BCD4;
                color: white;
                font-size: 14pt;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 12px;
            }
            QPushButton:hover {
                background-color: #00ACC1;
            }
        """)
        load_btn.setCursor(Qt.PointingHandCursor)
        load_btn.clicked.connect(self.load_examples)
        self.content_layout.addWidget(load_btn)
        
        self.results_label = QTextEdit()
        self.results_label.setReadOnly(True)
        self.results_label.setPlaceholderText("Click 'Load Claim Softgoals' to see examples...")
        self.results_label.setMinimumHeight(250)
        self.results_label.setStyleSheet("""
            QTextEdit {
                font-size: 13pt;
                padding: 15px;
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 15px;
            }
        """)
        self.results_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        self.content_layout.addWidget(self.results_label, stretch=1)
        
        details_layout = QHBoxLayout()
        details_label = QLabel("Enter number for details:")
        details_label.setStyleSheet("font-size: 12pt; color: #333;")
        details_layout.addWidget(details_label)
        
        self.detail_input = QLineEdit()
        self.detail_input.setPlaceholderText("e.g., 1")
        self.detail_input.setMaximumWidth(100)
        self.detail_input.setMinimumHeight(35)
        self.detail_input.setStyleSheet("""
            QLineEdit {
                font-size: 12pt;
                padding: 5px;
                border: 2px solid #ddd;
                border-radius: 5px;
            }
        """)
        details_layout.addWidget(self.detail_input)
        
        detail_btn = QPushButton("🔝 Show Details")
        detail_btn.setMinimumHeight(35)
        detail_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 11pt;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        detail_btn.setCursor(Qt.PointingHandCursor)
        detail_btn.clicked.connect(self.show_details)
        details_layout.addWidget(detail_btn)
        details_layout.addStretch()
        self.content_layout.addLayout(details_layout)
        
        self.details_label = QTextEdit()
        self.details_label.setReadOnly(True)
        self.details_label.setPlaceholderText("Details will appear here...")
        self.details_label.setMinimumHeight(150)
        self.details_label.setStyleSheet("""
            QTextEdit {
                font-size: 12pt;
                padding: 15px;
                background-color: #f5f5f5;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
            }
        """)
        self.details_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        self.content_layout.addWidget(self.details_label, stretch=1)
        
        self.current_examples = []
    
    def load_examples(self):
        self.results_label.setText("⏳ Loading Claim Softgoals...")
        QApplication.processEvents()
        
        def do_query():
            try:
                import metamodel
                import inspect
                
                examples = []
                for name, obj in inspect.getmembers(metamodel):
                    if hasattr(metamodel, 'ClaimSoftgoal'):
                        if isinstance(obj, metamodel.ClaimSoftgoal):
                            examples.append((name, obj))
                
                self.current_examples = examples
                
                if examples:
                    response = f"🔝 CLAIM SOFTGOALS\n\nFound {len(examples)} claim softgoal(s):\n\n"
                    for i, (name, obj) in enumerate(examples, 1):
                        response += f"{i}. {name}\n"
                    response += "\n💡 Enter a number and click 'Show Details'"
                else:
                    response = "â„¹ï¸ No claim softgoals found"
                
                return response
            except Exception as e:
                import traceback
                return f"❌ Error: {str(e)}\n\n{traceback.format_exc()}"
        
        def run_and_update():
            result = do_query()
            QMetaObject.invokeMethod(self.results_label, "setText", Qt.QueuedConnection, Q_ARG(str, result))
        
        thread = threading.Thread(target=run_and_update, daemon=True)
        thread.start()
    
    def show_details(self):
        try:
            num = int(self.detail_input.text().strip())
            if num < 1 or num > len(self.current_examples):
                self.details_label.setText(f"❌ Please enter a number between 1 and {len(self.current_examples)}")
                return
            
            name, obj = self.current_examples[num - 1]
            from nfr_queries import getDecompositionsFor, getEntityName, format_entity_name as fmt_name
            import metamodel
            import inspect
            
            # Get type classification
            classification = "Unknown"
            if inspect.isclass(obj):
                try:
                    if hasattr(metamodel, 'NFRSoftgoalType') and issubclass(obj, metamodel.NFRSoftgoalType):
                        classification = "NFR (Non-Functional Requirement)"
                    elif hasattr(metamodel, 'FunctionalRequirementType') and issubclass(obj, metamodel.FunctionalRequirementType):
                        classification = "Functional Requirement"
                    elif hasattr(metamodel, 'OperationalizingSoftgoalType') and issubclass(obj, metamodel.OperationalizingSoftgoalType):
                        classification = "Operationalizing Softgoal"
                    elif hasattr(metamodel, 'OperationalizingType') and issubclass(obj, metamodel.OperationalizingType):
                        classification = "Operationalizing Softgoal"
                except (TypeError, AttributeError):
                    pass
            
            # Get all decomposition methods
            decomp_info = ""
            if inspect.isclass(obj):
                decomps = getDecompositionsFor(obj)
                if decomps:
                    decomp_info = f"\n\nHas {len(decomps)} decomposition method(s):\n\n"
                    for i, decomp in enumerate(decomps, 1):
                        decomp_name = getattr(decomp, 'name', f'Decomposition {i}')
                        decomp_info += f"{i}. {decomp_name}\n"
                        if hasattr(decomp, 'offspring') and decomp.offspring:
                            offspring_names = [fmt_name(o.__name__) for o in decomp.offspring]
                            decomp_info += f"   Offspring: {', '.join(offspring_names)}\n"
                        decomp_info += "\n"
            
            # Combine context
            combined_context = f"Type: {classification}{decomp_info}"
            
            # Pass through MenuLLM
            self.details_label.setText("⏳ Generating explanation...")
            QApplication.processEvents()

            # Use QTimer to allow UI update before LLM generation
            def _generate_and_update():
                if self.menu_llm:
                    try:
                        # DEBUG: Print context
                        print()
                        print("="*70)
                        print("BROWSE EXAMPLES (ExamplesWindow) - LLM INPUT DEBUG")
                        print("="*70)
                        print("Action Type: browse_entity")
                        print("User Input:", name)
                        print()
                        print("Context being sent to LLM:")
                        print("-"*70)
                        print(combined_context)
                        print("-"*70)
                        
                        llm_response = self.menu_llm.respond(
                            action_type="browse_entity",
                            user_input=name,
                            metamodel_context=combined_context
                        )
                        self.details_label.setText(llm_response)
                    except Exception:
                        # Fallback to raw context on LLM error
                        fallback = f"📋 {name}\n{'='*60}\n\n{combined_context}"
                        self.details_label.setText(fallback)
                else:
                    fallback = f"📋 {name}\n{'='*60}\n\n{combined_context}"
                    self.details_label.setText(fallback)
            
            QTimer.singleShot(50, _generate_and_update)
        except ValueError:
            self.details_label.setText("❌ Please enter a valid number")
        except Exception as e:
            import traceback
            self.details_label.setText(f"❌ Error: {str(e)}\n\n{traceback.format_exc()}")


class SideEffectsWindow(ModuleWindow):
    """Window for showing contribution side effects with pipeline navigation"""
    
    def __init__(self, module_name: str, parent_home_screen, initial_entity: str = None, came_from: list = None):
        self.initial_entity = initial_entity
        self.current_entity = None
        self.came_from = came_from or []  # List of (WindowClass, entity_name) tuples for back navigation history
        super().__init__(module_name, parent_home_screen)
        
        if self.initial_entity:
            self.op_input.setText(self.initial_entity)
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, self.find_side_effects)
    
    def setup_content(self):
        # Initialize MenuLLM for AI-powered responses
        self.menu_llm = MenuLLM() if MENU_LLM_AVAILABLE else None

        from PySide6.QtWidgets import QLineEdit, QLabel, QTextEdit
        
        # Back button (if came from somewhere in pipeline)
        self.back_btn = QPushButton("â† Back")
        self.back_btn.setMinimumHeight(40)
        self.back_btn.setMaximumWidth(100)
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: #78909C;
                color: white;
                font-size: 11pt;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #607D8B;
            }
            QPushButton:pressed {
                background-color: #546E7A;
            }
        """)
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.clicked.connect(self.go_back)
        self.back_btn.setVisible(bool(self.came_from))
        self.content_layout.addWidget(self.back_btn)
        
        # Instruction label
        instruction = QLabel("Enter an operationalization to see which NFRs it affects:")
        instruction.setStyleSheet("font-size: 14pt; font-weight: bold; color: #333; margin-bottom: 10px;")
        self.content_layout.addWidget(instruction)
        
        # Single-line input
        self.op_input = QLineEdit()
        self.op_input.setPlaceholderText("Example: Indexing, Caching, Encryption...")
        self.op_input.setMinimumHeight(60)
        self.op_input.setStyleSheet("""
            QLineEdit {
                font-size: 14pt;
                padding: 15px;
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #00BCD4;
            }
        """)
        self.content_layout.addWidget(self.op_input)
        
        # Search button
        search_btn = QPushButton("⚡ Show Side Effects")
        search_btn.setMinimumHeight(50)
        search_btn.setStyleSheet("""
            QPushButton {
                background-color: #00BCD4;
                color: white;
                font-size: 14pt;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 15px;
            }
            QPushButton:hover {
                background-color: #00ACC1;
            }
            QPushButton:pressed {
                background-color: #0097A7;
            }
        """)
        search_btn.setCursor(Qt.PointingHandCursor)
        search_btn.clicked.connect(self.find_side_effects)
        self.content_layout.addWidget(search_btn)
        
        # Results area
        self.results_label = QTextEdit()
        self.results_label.setReadOnly(True)
        self.results_label.setPlaceholderText("Results will appear here...")
        self.results_label.setMinimumHeight(320)
        self.results_label.setStyleSheet("""
            QTextEdit {
                font-size: 14pt;
                padding: 20px;
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 20px;
            }
        """)
        self.results_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        self.content_layout.addWidget(self.results_label, stretch=1)
        
        # Pipeline info label - shows completion message
        self.pipeline_info = QLabel("✅ Pipeline complete! You've explored: What is it? â†’ Decompositions â†’ Operationalizations â†’ Side Effects")
        self.pipeline_info.setStyleSheet("""
            QLabel {
                font-size: 11pt;
                color: #2E7D32;
                background-color: #E8F5E9;
                padding: 12px;
                border-radius: 8px;
                margin-top: 10px;
            }
        """)
        self.pipeline_info.setWordWrap(True)
        self.pipeline_info.setVisible(False)
        self.content_layout.addWidget(self.pipeline_info)
        
        # Optional: Button to see claims/justifications
        self.claims_btn = QPushButton("ðŸ“š See claims & justifications â†’")
        self.claims_btn.setMinimumHeight(45)
        self.claims_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                font-size: 12pt;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #8E24AA;
            }
            QPushButton:pressed {
                background-color: #7B1FA2;
            }
        """)
        self.claims_btn.setCursor(Qt.PointingHandCursor)
        self.claims_btn.clicked.connect(self.go_to_claims)
        self.claims_btn.setVisible(False)
        self.content_layout.addWidget(self.claims_btn)
    
    def find_side_effects(self):
        """Show which NFRs an operationalization negatively affects (HURT/BREAK only) - synchronous"""
        text = self.op_input.text().strip()
        if not text:
            self.results_label.setText("⚠ï¸ Please enter an operationalization")
            return
        
        self.pipeline_info.setVisible(False)
        self.claims_btn.setVisible(False)
        self.results_label.setText("⏳ Searching for side effects...")
        QApplication.processEvents()
        
        try:
            from nfr_queries import getEntity, getEntityName
            import metamodel
            import inspect
            
            # Use fuzzy matching helper
            matched_name, suggestion = fuzzy_match_entity(text)
            if not matched_name:
                self.results_label.setText(suggestion)
                return
            
            entity = getEntity(matched_name)
            entity_name = getEntityName(entity)
            search_name = entity_name.replace('Type', '').replace('Softgoal', '')
            
            # Find contributions by this operationalization
            contributions = []
            for name, obj in inspect.getmembers(metamodel):
                if isinstance(obj, metamodel.Contribution):
                    if obj.source.lower() == search_name.lower():
                        contributions.append((obj.target, obj.type.value))
            
            response = suggestion
            
            # Filter for NEGATIVE effects only (HURT/BREAK)
            negative = []
            positive = []
            for target, contrib_type in contributions:
                formatted_target = format_entity_name(target)
                if contrib_type in ['HURT', 'BREAK']:
                    negative.append((formatted_target, contrib_type))
                elif contrib_type in ['HELP', 'MAKE']:
                    positive.append((formatted_target, contrib_type))
            
            formatted_search = format_entity_name(search_name)
            
            if negative:
                response += f"⚡ Side effects of using {formatted_search}:\n\n"
                response += f"This technique has {len(negative)} NEGATIVE effect(s):\n"
                response += "=" * 60 + "\n\n"
                
                response += "⚠ï¸ NEGATIVE EFFECTS:\n\n"
                for target, effect in negative:
                    response += f"   • {target} ({effect})\n"
                response += "\n"
                
                if positive:
                    response += "\n✅ But it also HELPS:\n\n"
                    for target, effect in positive:
                        response += f"   • {target} ({effect})\n"
                    response += "\n"
                
                response += "=" * 60 + "\n"
                response += f"💡 These are trade-offs to consider when using {formatted_search}."
            else:
                if contributions:
                    response += f"✅ {formatted_search} has no negative side effects!\n\n"
                    response += f"This technique only has positive or neutral effects.\n\n"
                    if positive:
                        response += "It positively contributes to:\n"
                        for target, effect in positive:
                            response += f"   • {target} ({effect})\n"
                else:
                    response += f"â„¹ï¸ {formatted_search} has no defined contributions in the metamodel.\n\n"
                    response += "The metamodel currently defines contributions for:\n"
                    response += "• Indexing, Caching, Encryption"
            
            # Pass through MenuLLM for natural language response
            if self.menu_llm:
                try:
                    llm_response = self.menu_llm.respond(
                        action_type="analyze_contributions",
                        user_input=search_name,
                        metamodel_context=response
                    )
                    self.results_label.setText(llm_response)
                except Exception:
                    self.results_label.setText(response)
            else:
                self.results_label.setText(response)
            
            self.current_entity = matched_name
            self.pipeline_info.setVisible(True)
            self.claims_btn.setVisible(True)
            
        except ImportError:
            self.results_label.setText("❌ Error: nfr_queries.py not found")
        except Exception as e:
            import traceback
            self.results_label.setText(f"❌ Error: {str(e)}\n\n{traceback.format_exc()}")
    
    def go_to_claims(self):
        """Navigate to Claims/Argumentation window"""
        if self.current_entity:
            # Clean up entity name for display
            clean_name = self.current_entity.replace('Type', '').replace('Softgoal', '')
            
            # Build navigation history
            history = self.came_from + [('SideEffectsWindow', clean_name)]
            
            # Set flag to prevent homescreen from showing on close
            self._navigating_pipeline = True
            self.hide()
            self.claims_window = AttributionWindow(
                "What is the justification? (Claim)", 
                self.parent_home_screen,
                initial_entity=clean_name,
                came_from=history
            )
            self.claims_window.show()
            self.close()
    
    def go_back(self):
        """Navigate back to previous window in history"""
        if self.came_from:
            # Pop the last window from history
            window_type, entity = self.came_from[-1]
            remaining_history = self.came_from[:-1]
            
            self._navigating_pipeline = True
            self.hide()
            
            if window_type == 'OperationalizationDecompositionWindow':
                self.back_window = OperationalizationDecompositionWindow(
                    "Operationalization Decompositions", self.parent_home_screen,
                    initial_entity=entity,
                    came_from=remaining_history
                )
            elif window_type == 'NFRDecompositionWindow':
                self.back_window = NFRDecompositionWindow(
                    "NFR Decompositions", self.parent_home_screen,
                    initial_entity=entity,
                    came_from=remaining_history
                )
            elif window_type == 'WhatsThisWindow':
                self.back_window = WhatsThisWindow(
                    "What is this?", self.parent_home_screen,
                    initial_entity=entity,
                    came_from=remaining_history
                )
            else:
                self.parent_home_screen.show()
                self.close()
                return
            
            self.back_window.show()
            self.close()




class WhatsThisWindow(ModuleWindow):
    """Window for What's This? - entity information lookup with pipeline navigation"""
    
    def __init__(self, module_name: str, parent_home_screen, initial_entity: str = None, came_from: list = None):
        self.initial_entity = initial_entity
        self.current_entity = None  # Store matched entity for pipeline navigation
        self.came_from = came_from or []  # List of (WindowClass, entity_name) tuples for back navigation history
        super().__init__(module_name, parent_home_screen)
        
        # If initial entity provided, auto-fill and search
        if self.initial_entity:
            self.text_input.setText(self.initial_entity)
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, self.show_info)
    
    def setup_content(self):
        # Initialize MenuLLM for AI-powered responses
        self.menu_llm = MenuLLM() if MENU_LLM_AVAILABLE else None

        from PySide6.QtWidgets import QLineEdit, QLabel, QHBoxLayout, QWidget
        
        # Back button (if came from somewhere)
        self.back_btn = QPushButton("â† Back")
        self.back_btn.setMinimumHeight(40)
        self.back_btn.setMaximumWidth(100)
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: #78909C;
                color: white;
                font-size: 11pt;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #607D8B;
            }
            QPushButton:pressed {
                background-color: #546E7A;
            }
        """)
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.clicked.connect(self.go_back)
        self.back_btn.setVisible(bool(self.came_from))
        self.content_layout.addWidget(self.back_btn)
        
        # Instruction label
        instruction = QLabel("Enter an entity to learn more about it:")
        instruction.setStyleSheet("font-size: 14pt; font-weight: bold; color: #333; margin-bottom: 10px;")
        self.content_layout.addWidget(instruction)
        
        # Single-line input
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Example: Performance, Encryption, Security, Indexing...")
        self.text_input.setMinimumHeight(60)
        self.text_input.setStyleSheet("""
            QLineEdit {
                font-size: 14pt;
                padding: 15px;
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
            }
        """)
        self.content_layout.addWidget(self.text_input)
        
        # What's This button
        whatsthis_btn = QPushButton("❓ What's This?")
        whatsthis_btn.setMinimumHeight(50)
        whatsthis_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF5722;
                color: white;
                font-size: 14pt;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 15px;
            }
            QPushButton:hover {
                background-color: #F4511E;
            }
            QPushButton:pressed {
                background-color: #E64A19;
            }
        """)
        whatsthis_btn.setCursor(Qt.PointingHandCursor)
        whatsthis_btn.clicked.connect(self.show_info)
        self.content_layout.addWidget(whatsthis_btn)
        
        # Results area
        from PySide6.QtWidgets import QTextEdit
        self.results_label = QTextEdit()
        self.results_label.setReadOnly(True)
        self.results_label.setPlaceholderText("Results will appear here...")
        self.results_label.setMinimumHeight(320)
        self.results_label.setStyleSheet("""
            QTextEdit {
                font-size: 14pt;
                padding: 20px;
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 20px;
            }
        """)
        self.results_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
        )
        self.content_layout.addWidget(self.results_label, stretch=1)
        
        # Pipeline Navigation Button - Initially hidden
        self.next_step_btn = QPushButton("🌳 What does [X] mean? â†’")
        self.next_step_btn.setMinimumHeight(50)
        self.next_step_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 13pt;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.next_step_btn.setCursor(Qt.PointingHandCursor)
        self.next_step_btn.clicked.connect(self.go_to_decomposition)
        self.next_step_btn.setVisible(False)
        self.content_layout.addWidget(self.next_step_btn)
    
    def show_info(self):
        """Show comprehensive information about the entity (synchronous - fast lookup)"""
        text = self.text_input.text().strip()
        if not text:
            self.results_label.setText("⚠ï¸ Please enter an entity name first")
            return
        
        self.next_step_btn.setVisible(False)
        self.results_label.setText("⏳ Looking up information...")
        QApplication.processEvents()
        
        try:
            from nfr_queries import getEntity, whatIs, getEntityName
            import metamodel
            import inspect
            
            matched_name, suggestion = fuzzy_match_entity(text)
            if not matched_name:
                self.results_label.setText(suggestion)
                return
            
            entity = getEntity(matched_name)
            if not entity:
                self.results_label.setText(f"❌ Could not find entity: {text}\n\nTry: Softgoal, Performance, Security, Indexing, etc.")
                return
            
            info = whatIs(entity, verbose=True)
            
            # DEBUG: Print context for "What is X?"
            print()
            print("="*70)
            print("WHAT IS X (WhatsThisWindow) - LLM INPUT DEBUG")
            print("="*70)
            print("Action Type: define_entity")
            print("User Input:", text)
            print()
            print("Context being sent to LLM:")
            print("-"*70)
            print(info)
            print("-"*70)
            
            # Pass through MenuLLM for natural language response
            if self.menu_llm:
                llm_response = self.menu_llm.respond(
                    action_type="define_entity",
                    user_input=text,
                    metamodel_context=info
                )
                final_response = suggestion + llm_response
            else:
                final_response = suggestion + info
            
            self.results_label.setText(final_response)
            
            # Detect entity type: NFR vs Operationalization
            self.current_entity = matched_name
            self.is_operationalization = False
            
            if inspect.isclass(entity):
                try:
                    # Check if it's an Operationalization (not an NFR)
                    if hasattr(metamodel, 'OperationalizingSoftgoalType'):
                        if issubclass(entity, metamodel.OperationalizingSoftgoalType):
                            self.is_operationalization = True
                    if hasattr(metamodel, 'OperationalizingType'):
                        if issubclass(entity, metamodel.OperationalizingType):
                            self.is_operationalization = True
                except TypeError:
                    pass
            
            # Show appropriate pipeline button based on entity type
            formatted_name = format_entity_name(matched_name)
            if self.is_operationalization:
                self.next_step_btn.setText(f"🔧 How does {formatted_name} work? â†’")
            else:
                self.next_step_btn.setText(f"🌳 What does {formatted_name} mean? â†’")
            self.next_step_btn.setVisible(True)
            
        except ImportError:
            self.results_label.setText("❌ Error: nfr_queries.py not found\n\nMake sure the queries module is in the project directory.")
        except Exception as e:
            import traceback
            self.results_label.setText(f"❌ Error: {str(e)}\n\n{traceback.format_exc()}")
    
    def go_to_decomposition(self):
        """Navigate to appropriate decomposition window based on entity type"""
        if self.current_entity:
            # Clean up entity name for display (remove Type/Softgoal suffix)
            clean_name = self.current_entity.replace('Type', '').replace('Softgoal', '')
            
            # Build navigation history - add current window to the stack
            history = self.came_from + [('WhatsThisWindow', clean_name)]
            
            # Set flag to prevent homescreen from showing on close
            self._navigating_pipeline = True
            self.hide()
            
            # Route to appropriate window based on entity type
            if getattr(self, 'is_operationalization', False):
                # For operationalizations, go to Operationalization Decomposition / Side Effects
                self.decomp_window = OperationalizationDecompositionWindow(
                    "Operationalization Decompositions", 
                    self.parent_home_screen,
                    initial_entity=clean_name,
                    came_from=history
                )
            else:
                # For NFRs, go to NFR Decomposition
                self.decomp_window = NFRDecompositionWindow(
                    "NFR Decompositions", 
                    self.parent_home_screen,
                    initial_entity=clean_name,
                    came_from=history
                )
            
            self.decomp_window.show()
            self.close()
    
    def go_back(self):
        """Navigate back to previous window in history"""
        if self.came_from:
            # Pop the last window from history
            window_type, entity = self.came_from[-1]
            remaining_history = self.came_from[:-1]
            
            self._navigating_pipeline = True
            self.hide()
            
            # Import and create the appropriate window with remaining history
            if window_type == 'NFRDecompositionWindow':
                self.back_window = NFRDecompositionWindow(
                    "NFR Decompositions", self.parent_home_screen,
                    initial_entity=entity,
                    came_from=remaining_history
                )
            elif window_type == 'OperationalizationDecompositionWindow':
                self.back_window = OperationalizationDecompositionWindow(
                    "Operationalization Decompositions", self.parent_home_screen,
                    initial_entity=entity,
                    came_from=remaining_history
                )
            else:
                # Default - go to homescreen
                self.parent_home_screen.show()
                self.close()
                return
            
            self.back_window.show()
            self.close()



# ============================================================================
# SPECIALIZED DECOMPOSITION WINDOWS
# ============================================================================

class NFRDecompositionWindow(ModuleWindow):
    """Window for NFR-to-NFR decompositions with pipeline navigation"""
    
    def __init__(self, module_name: str, parent_home_screen, initial_entity: str = None, came_from: list = None):
        self.initial_entity = initial_entity
        self.current_entity = None
        self.current_offspring = []  # Store offspring for navigation
        self.came_from = came_from or []  # List of (WindowClass, entity_name) tuples for back navigation history
        super().__init__(module_name, parent_home_screen)
        
        # If initial entity provided, auto-fill and search
        if self.initial_entity:
            self.text_input.setText(self.initial_entity)
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, self.show_nfr_decompositions)
    
    def setup_content(self):
        # Initialize MenuLLM for AI-powered responses
        self.menu_llm = MenuLLM() if MENU_LLM_AVAILABLE else None

        # Back button (if came from somewhere in pipeline)
        self.back_btn = QPushButton("â† Back")
        self.back_btn.setMinimumHeight(40)
        self.back_btn.setMaximumWidth(100)
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: #78909C;
                color: white;
                font-size: 11pt;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #607D8B;
            }
            QPushButton:pressed {
                background-color: #546E7A;
            }
        """)
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.clicked.connect(self.go_back)
        self.back_btn.setVisible(bool(self.came_from))
        self.content_layout.addWidget(self.back_btn)
        
        # Title
        title = QLabel("NFR Decompositions")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #1565C0; margin-bottom: 10px;")
        self.content_layout.addWidget(title)
        
        # Description
        desc = QLabel("Decompose an NFR into its sub-NFRs (refinement types)")
        desc.setStyleSheet("font-size: 12pt; color: #666; margin-bottom: 20px;")
        self.content_layout.addWidget(desc)
        
        # Example
        example = QLabel("💡 Example: Security â†’ Confidentiality, Integrity, Availability")
        example.setStyleSheet("font-size: 11pt; color: #0288D1; margin-bottom: 15px; padding: 10px; background-color: #E1F5FE; border-radius: 5px;")
        self.content_layout.addWidget(example)
        
        # Input
        input_label = QLabel("Enter an NFR type:")
        input_label.setStyleSheet("font-size: 13pt; font-weight: bold; color: #333; margin-top: 10px;")
        self.content_layout.addWidget(input_label)
        
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Example: Security, Performance, Usability...")
        self.text_input.setMinimumHeight(50)
        self.text_input.setStyleSheet("""
            QLineEdit {
                font-size: 13pt;
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
            }
        """)
        self.content_layout.addWidget(self.text_input)
        
        # Button
        decompose_btn = QPushButton("🌳 Show NFR Decompositions")
        decompose_btn.setMinimumHeight(50)
        decompose_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 13pt;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        decompose_btn.setCursor(Qt.PointingHandCursor)
        decompose_btn.clicked.connect(self.show_nfr_decompositions)
        self.content_layout.addWidget(decompose_btn)
        
        # Results
        self.results_label = QTextEdit()
        self.results_label.setReadOnly(True)
        self.results_label.setPlaceholderText("NFR decomposition results will appear here...")
        self.results_label.setMinimumHeight(280)
        self.results_label.setStyleSheet("""
            QTextEdit {
                font-size: 13pt;
                padding: 15px;
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 15px;
            }
        """)
        self.results_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
        )
        self.content_layout.addWidget(self.results_label, stretch=1)
        
        # Pipeline Navigation Button - Initially hidden
        self.next_step_btn = QPushButton("🔧 How to achieve [X]? â†’")
        self.next_step_btn.setMinimumHeight(50)
        self.next_step_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-size: 13pt;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 12px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:pressed {
                background-color: #E65100;
            }
        """)
        self.next_step_btn.setCursor(Qt.PointingHandCursor)
        self.next_step_btn.clicked.connect(self.go_to_operationalization)
        self.next_step_btn.setVisible(False)
        self.content_layout.addWidget(self.next_step_btn)
        
        # Claims button - Initially hidden
        self.claims_btn = QPushButton("ðŸ“š See claims & justifications â†’")
        self.claims_btn.setMinimumHeight(45)
        self.claims_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                font-size: 12pt;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #8E24AA;
            }
            QPushButton:pressed {
                background-color: #7B1FA2;
            }
        """)
        self.claims_btn.setCursor(Qt.PointingHandCursor)
        self.claims_btn.clicked.connect(self.go_to_claims)
        self.claims_btn.setVisible(False)
        self.content_layout.addWidget(self.claims_btn)
    
    def show_nfr_decompositions(self):
        """Show NFR-to-NFR decompositions (synchronous - fast lookup)"""
        text = self.text_input.text().strip()
        if not text:
            self.results_label.setText("⚠ï¸ Please enter an NFR type first")
            return
        
        self.next_step_btn.setVisible(False)
        self.claims_btn.setVisible(False)
        self.results_label.setText("⏳ Searching for NFR decompositions...")
        QApplication.processEvents()
        
        try:
            from nfr_queries import getEntity, getDecompositionsFor, getEntityName
            import metamodel
            
            # Fuzzy match
            matched_name, suggestion = fuzzy_match_entity(text)
            if not matched_name:
                self.results_label.setText(suggestion)
                return
            
            entity = getEntity(matched_name)
            entity_name = getEntityName(entity)
            
            # Get all decompositions
            all_decomps = getDecompositionsFor(entity)
            
            # Filter for NFRDecompositionMethod only
            nfr_decomps = []
            all_offspring = []
            for decomp in all_decomps:
                if hasattr(metamodel, 'NFRDecompositionMethod'):
                    if isinstance(decomp, metamodel.NFRDecompositionMethod):
                        nfr_decomps.append(decomp)
                        if hasattr(decomp, 'offspring') and decomp.offspring:
                            for o in decomp.offspring:
                                all_offspring.append(o.__name__)
            
            response = suggestion
            formatted_name = format_entity_name(entity_name)
            
            if nfr_decomps:
                response += f"✅ **NFR Decompositions for {formatted_name}**\n\n"
                response += f"Found {len(nfr_decomps)} NFR decomposition method(s):\n\n"
                response += "="*50 + "\n\n"
                
                for i, decomp in enumerate(nfr_decomps, 1):
                    response += f"**{i}. {decomp.name}**\n"
                    if hasattr(decomp, 'description') and decomp.description:
                        response += f"   🔝 {decomp.description}\n"
                    if hasattr(decomp, 'offspring') and decomp.offspring:
                        offspring_names = [format_entity_name(o.__name__) for o in decomp.offspring]
                        response += f"   🌿 Sub-NFRs: {', '.join(offspring_names)}\n"
                    response += "\n"
                
                response += "="*50 + "\n"
                response += f"\n💡 **Interpretation**: {formatted_name} can be refined into the sub-NFRs shown above."
            else:
                response += f"â„¹ï¸ No NFR decomposition methods found for {formatted_name}.\n\n"
                response += f"This might mean:\n"
                response += f"• {formatted_name} is a leaf-level NFR (cannot be decomposed further)\n"
                response += f"• Only operationalization or claim decompositions are defined for it\n"
            
            # Pass through MenuLLM for natural language response
            if self.menu_llm:
                try:
                    llm_response = self.menu_llm.respond(
                        action_type="decompose",
                        user_input=text,
                        metamodel_context=response
                    )
                    self.results_label.setText(llm_response)
                except Exception:
                    # Fallback to raw response on LLM error
                    self.results_label.setText(response)
            else:
                self.results_label.setText(response)
            
            # Show pipeline button
            self.current_entity = matched_name
            self.current_offspring = all_offspring
            formatted_name = format_entity_name(matched_name)
            self.next_step_btn.setText(f"🔧 How to achieve {formatted_name}? â†’")
            self.next_step_btn.setVisible(True)
            
            # Show claims button
            self.claims_btn.setVisible(True)
            
        except Exception as e:
            import traceback
            self.results_label.setText(f"❌ Error: {str(e)}\n\n{traceback.format_exc()}")
    
    def go_to_operationalization(self):
        """Navigate to Operationalization window with current entity"""
        if self.current_entity:
            # Clean up entity name for display
            clean_name = self.current_entity.replace('Type', '').replace('Softgoal', '')
            
            # Build navigation history
            history = self.came_from + [('NFRDecompositionWindow', clean_name)]
            
            # Set flag to prevent homescreen from showing on close
            self._navigating_pipeline = True
            self.hide()
            self.op_window = OperationalizationDecompositionWindow(
                "Operationalization Decompositions", 
                self.parent_home_screen,
                initial_entity=clean_name,
                came_from=history
            )
            self.op_window.show()
            self.close()
    
    def go_to_claims(self):
        """Navigate to Claims/Argumentation window"""
        if self.current_entity:
            clean_name = self.current_entity.replace('Type', '').replace('Softgoal', '')
            
            # Build navigation history
            history = self.came_from + [('NFRDecompositionWindow', clean_name)]
            
            self._navigating_pipeline = True
            self.hide()
            self.claims_window = AttributionWindow(
                "What is the justification? (Claim)", 
                self.parent_home_screen,
                initial_entity=clean_name,
                came_from=history
            )
            self.claims_window.show()
            self.close()
    
    def go_back(self):
        """Navigate back to previous window in history"""
        if self.came_from:
            # Pop the last window from history
            window_type, entity = self.came_from[-1]
            remaining_history = self.came_from[:-1]
            
            self._navigating_pipeline = True
            self.hide()
            
            if window_type == 'WhatsThisWindow':
                self.back_window = WhatsThisWindow(
                    "What is this?", self.parent_home_screen,
                    initial_entity=entity,
                    came_from=remaining_history
                )
            else:
                self.parent_home_screen.show()
                self.close()
                return
            
            self.back_window.show()
            self.close()

class OperationalizationDecompositionWindow(ModuleWindow):
    """Window for operationalization decompositions with pipeline navigation"""
    
    def __init__(self, module_name: str, parent_home_screen, initial_entity: str = None, came_from: list = None):
        self.initial_entity = initial_entity
        self.current_entity = None
        self.found_operationalizations = []  # Store ops for side effects navigation
        self.came_from = came_from or []  # List of (WindowClass, entity_name) tuples for back navigation history
        super().__init__(module_name, parent_home_screen)
        
        if self.initial_entity:
            self.text_input.setText(self.initial_entity)
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, self.show_op_details)
    
    def setup_content(self):
        # Initialize MenuLLM for AI-powered responses
        self.menu_llm = MenuLLM() if MENU_LLM_AVAILABLE else None

        from PySide6.QtWidgets import QComboBox, QHBoxLayout, QWidget
        
        # Back button (if came from somewhere in pipeline)
        self.back_btn = QPushButton("â† Back")
        self.back_btn.setMinimumHeight(40)
        self.back_btn.setMaximumWidth(100)
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: #78909C;
                color: white;
                font-size: 11pt;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #607D8B;
            }
            QPushButton:pressed {
                background-color: #546E7A;
            }
        """)
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.clicked.connect(self.go_back)
        self.back_btn.setVisible(bool(self.came_from))
        self.content_layout.addWidget(self.back_btn)
        
        # Title
        title = QLabel("Operationalization Decompositions")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #1565C0; margin-bottom: 10px;")
        self.content_layout.addWidget(title)
        
        # Description
        desc = QLabel("Bidirectional: NFRâ†’Operationalizations OR Operationalizationâ†’Types & NFRs it helps")
        desc.setStyleSheet("font-size: 12pt; color: #666; margin-bottom: 20px;")
        self.content_layout.addWidget(desc)
        
        # Example
        example = QLabel("💡 Examples: Securityâ†’Encryption, Authorization | Encryptionâ†’Types + helps Security")
        example.setStyleSheet("font-size: 11pt; color: #0288D1; margin-bottom: 15px; padding: 10px; background-color: #E1F5FE; border-radius: 5px;")
        self.content_layout.addWidget(example)
        
        # Input
        input_label = QLabel("Enter an NFR or Operationalization:")
        input_label.setStyleSheet("font-size: 13pt; font-weight: bold; color: #333; margin-top: 10px;")
        self.content_layout.addWidget(input_label)
        
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Example: Security, Performance, Encryption, Authorization...")
        self.text_input.setMinimumHeight(50)
        self.text_input.setStyleSheet("""
            QLineEdit {
                font-size: 13pt;
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
            }
        """)
        self.content_layout.addWidget(self.text_input)
        
        # Button
        decompose_btn = QPushButton("🔧 Show Operationalization Details")
        decompose_btn.setMinimumHeight(50)
        decompose_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-size: 13pt;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 12px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:pressed {
                background-color: #E65100;
            }
        """)
        decompose_btn.setCursor(Qt.PointingHandCursor)
        decompose_btn.clicked.connect(self.show_op_details)
        self.content_layout.addWidget(decompose_btn)
        
        # Results
        self.results_label = QTextEdit()
        self.results_label.setReadOnly(True)
        self.results_label.setPlaceholderText("Results will appear here...")
        self.results_label.setMinimumHeight(250)
        self.results_label.setStyleSheet("""
            QTextEdit {
                font-size: 13pt;
                padding: 15px;
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 15px;
            }
        """)
        self.results_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
        )
        self.content_layout.addWidget(self.results_label, stretch=1)
        
        # Pipeline Navigation - Container for dropdown and button
        self.pipeline_container = QWidget()
        pipeline_layout = QHBoxLayout(self.pipeline_container)
        pipeline_layout.setContentsMargins(0, 10, 0, 0)
        
        # Dropdown for selecting operationalization
        self.op_dropdown = QComboBox()
        self.op_dropdown.setMinimumHeight(45)
        self.op_dropdown.setStyleSheet("""
            QComboBox {
                font-size: 12pt;
                padding: 10px;
                padding-right: 35px;
                border: 2px solid #00BCD4;
                border-radius: 8px;
                background-color: white;
            }
            QComboBox:hover {
                border-color: #00ACC1;
                background-color: #E0F7FA;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: right center;
                width: 30px;
                border-left: 1px solid #00BCD4;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
                background-color: #E0F7FA;
            }
            QComboBox::down-arrow {
                width: 0;
                height: 0;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 8px solid #00838F;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #00BCD4;
                border-radius: 4px;
                background-color: white;
                selection-background-color: #B2EBF2;
            }
        """)
        pipeline_layout.addWidget(self.op_dropdown, stretch=1)
        
        # Side effects button
        self.next_step_btn = QPushButton("⚡ Side Effects â†’")
        self.next_step_btn.setMinimumHeight(45)
        self.next_step_btn.setMinimumWidth(160)
        self.next_step_btn.setStyleSheet("""
            QPushButton {
                background-color: #00BCD4;
                color: white;
                font-size: 12pt;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #00ACC1;
            }
            QPushButton:pressed {
                background-color: #0097A7;
            }
        """)
        self.next_step_btn.setCursor(Qt.PointingHandCursor)
        self.next_step_btn.clicked.connect(self.go_to_side_effects)
        pipeline_layout.addWidget(self.next_step_btn)
        
        self.pipeline_container.setVisible(False)
        self.content_layout.addWidget(self.pipeline_container)
        
        # Claims button - Initially hidden
        self.claims_btn = QPushButton("ðŸ“š See claims & justifications â†’")
        self.claims_btn.setMinimumHeight(45)
        self.claims_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                font-size: 12pt;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #8E24AA;
            }
            QPushButton:pressed {
                background-color: #7B1FA2;
            }
        """)
        self.claims_btn.setCursor(Qt.PointingHandCursor)
        self.claims_btn.clicked.connect(self.go_to_claims)
        self.claims_btn.setVisible(False)
        self.content_layout.addWidget(self.claims_btn)
    
    def show_op_details(self):
        """Bidirectional: NFRâ†’Operationalizations OR Operationalizationâ†’Types & contributions (synchronous)"""
        text = self.text_input.text().strip()
        if not text:
            self.results_label.setText("⚠ï¸ Please enter an NFR or operationalization")
            return
        
        self.pipeline_container.setVisible(False)
        self.claims_btn.setVisible(False)
        self.results_label.setText("⏳ Searching...")
        QApplication.processEvents()
        
        try:
            from nfr_queries import getEntity, getDecompositionsFor, getEntityName, getChildren
            import metamodel
            import inspect
            
            # Fuzzy match
            matched_name, suggestion = fuzzy_match_entity(text)
            if not matched_name:
                self.results_label.setText(suggestion)
                return
            
            entity = getEntity(matched_name)
            entity_name = getEntityName(entity)
            formatted_name = format_entity_name(entity_name)
            search_name = entity_name.replace('Type', '').replace('Softgoal', '')
            
            # Determine if it's an NFR or Operationalization
            is_nfr = False
            
            if inspect.isclass(entity):
                try:
                    if hasattr(metamodel, 'NFRSoftgoalType'):
                        if issubclass(entity, metamodel.NFRSoftgoalType):
                            is_nfr = True
                    
                    if is_nfr and hasattr(metamodel, 'OperationalizingSoftgoalType'):
                        if issubclass(entity, metamodel.OperationalizingSoftgoalType):
                            is_nfr = False
                    elif is_nfr and hasattr(metamodel, 'OperationalizingType'):
                        if issubclass(entity, metamodel.OperationalizingType):
                            is_nfr = False
                except TypeError:
                    pass
            
            response = suggestion
            found_ops = []
            
            # CASE 1: Input is an NFR â†’ Show operationalizations that help it
            if is_nfr:
                response += f"🎯 How to achieve {formatted_name}\n\n"
                response += "=" * 60 + "\n\n"
                
                search_targets = [search_name]
                
                try:
                    children = getChildren(entity)
                    for child in children:
                        child_name = getEntityName(child).replace('Type', '').replace('Softgoal', '')
                        if child_name not in search_targets:
                            search_targets.append(child_name)
                except:
                    pass
                
                try:
                    decomps = getDecompositionsFor(entity)
                    for decomp in decomps:
                        if hasattr(decomp, 'offspring'):
                            for offspring in decomp.offspring:
                                offspring_name = getEntityName(offspring).replace('Type', '').replace('Softgoal', '')
                                if offspring_name not in search_targets:
                                    search_targets.append(offspring_name)
                except:
                    pass
                
                # STRATEGY: Include operationalizations with at least one positive contribution,
                # but show ALL their contributions (positive and negative) for complete context
                positive_types = ['MAKE', 'HELP', 'SOME+']
                
                # Step 1: Find operationalizations that have at least one positive contribution
                ops_with_positive = set()
                all_contributions = []
                
                for name, obj in inspect.getmembers(metamodel):
                    if isinstance(obj, metamodel.Contribution):
                        target_match = any(obj.target.lower() == t.lower() for t in search_targets)
                        if target_match:
                            all_contributions.append((obj.source, obj.target, obj.type.value))
                            # Track if this operationalization has at least one positive
                            if obj.type.value in positive_types:
                                ops_with_positive.add(obj.source)
                
                # Step 2: Include ALL contributions from operationalizations that have at least one positive
                contributions = []
                for source, target, effect in all_contributions:
                    if source in ops_with_positive:
                        contributions.append((source, target, effect))
                        if source not in found_ops:
                            found_ops.append(source)
                
                if contributions:
                    response += f"Found {len(contributions)} operationalization(s):\n\n"
                    
                    from collections import defaultdict
                    by_source = defaultdict(list)
                    for source, target, effect in contributions:
                        by_source[source].append((target, effect))
                    
                    for source in sorted(by_source.keys()):
                        formatted_source = format_entity_name(source)
                        response += f"{formatted_source} helps achieve:\n\n"
                        
                        for target, effect in by_source[source]:
                            formatted_target = format_entity_name(target)
                            response += f"   • {formatted_target} ({effect})\n"
                        response += "\n"
                    
                    response += "=" * 60 + "\n"
                    response += "\n💡 These techniques can help satisfy this NFR."
                else:
                    response += f"â„¹ï¸ No operationalizations found for {formatted_name}.\n\n"
                    response += "Try: Indexingâ†’Performance, Encryptionâ†’Security, etc."
            
            # CASE 2: Input is an Operationalization â†’ Show types & NFRs it helps
            else:
                found_ops.append(search_name)
                response += f"✅ Details for {formatted_name}\n\n"
                response += "=" * 60 + "\n\n"
                
                # Types & Decompositions
                subclasses = []
                try:
                    children = getChildren(entity)
                    if children:
                        subclasses = [format_entity_name(getEntityName(child)) for child in children]
                except:
                    pass
                
                all_decomps = getDecompositionsFor(entity)
                op_decomps = []
                for decomp in all_decomps:
                    if hasattr(metamodel, 'OperationalizationDecompositionMethod'):
                        if isinstance(decomp, metamodel.OperationalizationDecompositionMethod):
                            op_decomps.append(decomp)
                
                if subclasses or op_decomps:
                    response += f"🔧 TYPES & DECOMPOSITIONS\n\n"
                    
                    if subclasses:
                        response += f"📌 **Types of {formatted_name}** (via isA):\n"
                        for subclass in subclasses:
                            response += f"   • {subclass}\n"
                        response += "\n"
                    
                    if op_decomps:
                        response += f"🌳 **Decomposition Methods**:\n"
                        for i, decomp in enumerate(op_decomps, 1):
                            response += f"   {i}. {decomp.name}\n"
                            if hasattr(decomp, 'offspring') and decomp.offspring:
                                offspring_names = [format_entity_name(o.__name__) for o in decomp.offspring]
                                response += f"      â””â”€ {', '.join(offspring_names)}\n"
                        response += "\n"
                else:
                    response += f"🔧 No subclasses or decompositions found.\n\n"
                
                # Positive Contributions
                response += "=" * 60 + "\n\n"
                response += f"✅ POSITIVE CONTRIBUTIONS (NFRs this helps)\n\n"
                
                positive_contribs = []
                for name, obj in inspect.getmembers(metamodel):
                    if isinstance(obj, metamodel.Contribution):
                        if obj.source.lower() == search_name.lower():
                            if obj.type.value in ['HELP', 'MAKE']:
                                formatted_target = format_entity_name(obj.target)
                                positive_contribs.append((formatted_target, obj.type.value))
                
                if positive_contribs:
                    response += f"{formatted_name} helps achieve:\n\n"
                    for target, effect in positive_contribs:
                        response += f"   • {target} ({effect})\n"
                    response += "\n"
                else:
                    response += f"No positive contributions defined for {formatted_name}.\n"
                    response += f"This might mean it's not in the metamodel yet.\n\n"
                
                response += "=" * 60 + "\n"
                response += f"\n💡 Select an operationalization below to see its side effects."
            
            # Update UI - pass through MenuLLM for natural language response
            if self.menu_llm:
                try:
                    llm_response = self.menu_llm.respond(
                        action_type="show_operationalizations" if is_nfr else "analyze_contributions",
                        user_input=text,
                        metamodel_context=response
                    )
                    self.results_label.setText(llm_response)
                except Exception:
                    # Fallback to raw response on LLM error
                    self.results_label.setText(response)
            else:
                self.results_label.setText(response)
            
            # Show pipeline controls if we found operationalizations
            if found_ops:
                self.current_entity = matched_name
                self.found_operationalizations = found_ops
                
                # Populate dropdown with operationalizations
                self.op_dropdown.clear()
                for op in found_ops:
                    formatted_op = format_entity_name(op)
                    self.op_dropdown.addItem(f"⚡ {formatted_op}", op)
                
                self.pipeline_container.setVisible(True)
            else:
                self.pipeline_container.setVisible(False)
            
            # Always show claims button if entity was found
            self.claims_btn.setVisible(True)
                
        except Exception as e:
            import traceback
            self.results_label.setText(f"❌ Error: {str(e)}\n\n{traceback.format_exc()}")
    
    def go_to_side_effects(self):
        """Navigate to Side Effects window with selected operationalization"""
        # Get selected operationalization from dropdown
        selected_op = self.op_dropdown.currentData()
        if selected_op:
            clean_name = selected_op.replace('Type', '').replace('Softgoal', '')
            # Store the NFR we came from for back navigation
            nfr_name = self.current_entity.replace('Type', '').replace('Softgoal', '') if self.current_entity else clean_name
            
            # Build navigation history
            history = self.came_from + [('OperationalizationDecompositionWindow', nfr_name)]
            
            # Set flag to prevent homescreen from showing on close
            self._navigating_pipeline = True
            self.hide()
            self.side_effects_window = SideEffectsWindow(
                "Possible side effects? (Contributions)", 
                self.parent_home_screen,
                initial_entity=clean_name,
                came_from=history
            )
            self.side_effects_window.show()
            self.close()
    
    def go_to_claims(self):
        """Navigate to Claims/Argumentation window"""
        if self.current_entity:
            clean_name = self.current_entity.replace('Type', '').replace('Softgoal', '')
            
            # Build navigation history
            history = self.came_from + [('OperationalizationDecompositionWindow', clean_name)]
            
            self._navigating_pipeline = True
            self.hide()
            self.claims_window = AttributionWindow(
                "What is the justification? (Claim)", 
                self.parent_home_screen,
                initial_entity=clean_name,
                came_from=history
            )
            self.claims_window.show()
            self.close()
    
    def go_back(self):
        """Navigate back to previous window in history"""
        if self.came_from:
            # Pop the last window from history
            window_type, entity = self.came_from[-1]
            remaining_history = self.came_from[:-1]
            
            self._navigating_pipeline = True
            self.hide()
            
            if window_type == 'NFRDecompositionWindow':
                self.back_window = NFRDecompositionWindow(
                    "NFR Decompositions", self.parent_home_screen,
                    initial_entity=entity,
                    came_from=remaining_history
                )
            elif window_type == 'WhatsThisWindow':
                self.back_window = WhatsThisWindow(
                    "What is this?", self.parent_home_screen,
                    initial_entity=entity,
                    came_from=remaining_history
                )
            else:
                self.parent_home_screen.show()
                self.close()
                return
            
            self.back_window.show()
            self.close()



class ArgumentationDecompositionWindow(ModuleWindow):
    """Window for claim/justification decompositions with pipeline support"""
    
    def __init__(self, module_name: str, parent_home_screen, initial_entity: str = None):
        self.initial_entity = initial_entity
        self.current_entity = None
        super().__init__(module_name, parent_home_screen)
        
        if self.initial_entity:
            self.text_input.setText(self.initial_entity)
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, self.show_claims)
    
    def setup_content(self):
        # Initialize MenuLLM for AI-powered responses
        self.menu_llm = MenuLLM() if MENU_LLM_AVAILABLE else None

        # Title
        title = QLabel("Argumentation / Claim Decompositions")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #1565C0; margin-bottom: 10px;")
        self.content_layout.addWidget(title)
        
        # Description
        desc = QLabel("See the justification and academic sources for decomposition approaches")
        desc.setStyleSheet("font-size: 12pt; color: #666; margin-bottom: 20px;")
        self.content_layout.addWidget(desc)
        
        # Example
        example = QLabel("💡 Example: Who proposed that Security decomposes into Confidentiality, Integrity, Availability?")
        example.setStyleSheet("font-size: 11pt; color: #0288D1; margin-bottom: 15px; padding: 10px; background-color: #E1F5FE; border-radius: 5px;")
        self.content_layout.addWidget(example)
        
        # Input
        input_label = QLabel("Enter an NFR type:")
        input_label.setStyleSheet("font-size: 13pt; font-weight: bold; color: #333; margin-top: 10px;")
        self.content_layout.addWidget(input_label)
        
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Example: Security, Performance, Usability...")
        self.text_input.setMinimumHeight(50)
        self.text_input.setStyleSheet("""
            QLineEdit {
                font-size: 13pt;
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
            }
        """)
        self.content_layout.addWidget(self.text_input)
        
        # Button
        decompose_btn = QPushButton("ðŸ“š Show Claims & Justifications")
        decompose_btn.setMinimumHeight(50)
        decompose_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                font-size: 13pt;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 12px;
            }
            QPushButton:hover {
                background-color: #8E24AA;
            }
            QPushButton:pressed {
                background-color: #7B1FA2;
            }
        """)
        decompose_btn.setCursor(Qt.PointingHandCursor)
        decompose_btn.clicked.connect(self.show_claims)
        self.content_layout.addWidget(decompose_btn)
        
        # Results
        self.results_label = QTextEdit()
        self.results_label.setReadOnly(True)
        self.results_label.setPlaceholderText("Claims and justifications will appear here...")
        self.results_label.setMinimumHeight(350)
        self.results_label.setStyleSheet("""
            QTextEdit {
                font-size: 13pt;
                padding: 15px;
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 15px;
            }
        """)
        self.results_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
        )
        self.content_layout.addWidget(self.results_label, stretch=1)
    
    def show_claims(self):
        """Show claims/justifications for decompositions"""
        text = self.text_input.text().strip()
        if not text:
            self.results_label.setText("⚠ï¸ Please enter an NFR type first")
            return
        
        self.results_label.setText("⏳ Searching for claims and justifications...")
        QApplication.processEvents()
        
        def do_search():
            try:
                from nfr_queries import getEntity, getDecompositionsFor, getEntityName
                import metamodel
                
                # Fuzzy match
                matched_name, suggestion = fuzzy_match_entity(text)
                if not matched_name:
                    return suggestion
                
                entity = getEntity(matched_name)
                entity_name = getEntityName(entity)
                formatted_name = format_entity_name(entity_name)
                
                # Get all decompositions
                all_decomps = getDecompositionsFor(entity)
                
                # Filter for ClaimDecompositionMethod
                claim_decomps = []
                for decomp in all_decomps:
                    if hasattr(metamodel, 'ClaimDecompositionMethod'):
                        if isinstance(decomp, metamodel.ClaimDecompositionMethod):
                            claim_decomps.append(decomp)
                
                response = suggestion
                response += f"✅ **Argumentation for {formatted_name} Decompositions**\n\n"
                response += "="*60 + "\n\n"
                
                if claim_decomps:
                    response += f"Found {len(claim_decomps)} claim/justification(s):\n\n"
                    
                    for i, claim in enumerate(claim_decomps, 1):
                        response += f"**ðŸ“š Claim {i}: {claim.name}**\n\n"
                        
                        
                        # Source (from claim argument)
                        if hasattr(claim, 'argument') and claim.argument:
                            response += f"   **Source**: {claim.argument}\n\n"
                        
                        # What it decomposes into
                        if hasattr(claim, 'offspring') and claim.offspring:
                            offspring_names = [format_entity_name(o.__name__) for o in claim.offspring]
                            response += f"   **Decomposes into**: {', '.join(offspring_names)}\n\n"
                        
                        response += "   " + "-"*50 + "\n\n"
                    
                    response += "="*60 + "\n"
                    response += f"\n💡 **Interpretation**: Each claim above represents a scholarly perspective on how {formatted_name} should be decomposed."
                else:
                    # Even if no claim decompositions, show NFR decompositions with attribution info
                    nfr_decomps = [d for d in all_decomps if hasattr(metamodel, 'NFRDecompositionMethod') and isinstance(d, metamodel.NFRDecompositionMethod)]
                    
                    if nfr_decomps:
                        response += f"No explicit claim decompositions found.\n\n"
                        response += f"However, {formatted_name} has {len(nfr_decomps)} NFR decomposition(s):\n\n"
                        
                        for i, decomp in enumerate(nfr_decomps, 1):
                            response += f"**{i}. {decomp.name}**\n"
                            if hasattr(decomp, 'description'):
                                response += f"   {decomp.description}\n"
                            if hasattr(decomp, 'offspring'):
                                offspring_names = [format_entity_name(o.__name__) for o in decomp.offspring]
                                response += f"   â””â”€ {', '.join(offspring_names)}\n"
                            response += "\n"
                        
                        response += "\n⚠ï¸ **Note**: Add source attribution for these decompositions in the metamodel for full argumentation support."
                    else:
                        response += f"â„¹ï¸ No decomposition methods (claim or NFR) found for {formatted_name}."
                
                # Pass through MenuLLM
                if hasattr(self, "menu_llm") and self.menu_llm:
                    try:
                        llm_response = self.menu_llm.respond("show_claims", text, response)
                        return llm_response
                    except:
                        return response
                else:
                    return response
                
            except Exception as e:
                import traceback
                return f"❌ Error: {str(e)}\n\n{traceback.format_exc()}"
        
        # Run in thread
        def run_and_update():
            result = do_search()
            QMetaObject.invokeMethod(self.results_label, "setText", 
                                    Qt.QueuedConnection, Q_ARG(str, result))
        
        thread = threading.Thread(target=run_and_update, daemon=True)
        thread.start()



class VerificationWindow(ModuleWindow):
    """Window for verifying natural language statements against the metamodel"""
    
    def setup_content(self):
        # Initialize MenuLLM for AI-powered parsing
        self.menu_llm = MenuLLM() if MENU_LLM_AVAILABLE else None

        from PySide6.QtWidgets import QLineEdit, QLabel, QTextEdit
        
        # Instruction label
        instruction = QLabel("Enter a statement to verify against the NFR Framework:")
        instruction.setStyleSheet("font-size: 14pt; font-weight: bold; color: #333; margin-bottom: 10px;")
        self.content_layout.addWidget(instruction)
        
        # Examples label
        examples = QLabel("Examples:\n  • Performance is an NFR\n  • Performance is decomposed into Time and Space\n  • Caching is an operationalization for Performance")
        examples.setStyleSheet("font-size: 11pt; color: #666; margin-bottom: 10px;")
        self.content_layout.addWidget(examples)
        
        # Text input - larger for natural language
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Example: Performance is decomposed into Time Performance and Space Performance")
        self.text_input.setMinimumHeight(100)
        self.text_input.setMaximumHeight(120)
        self.text_input.setStyleSheet("""
            QTextEdit {
                font-size: 13pt;
                padding: 15px;
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: white;
            }
            QTextEdit:focus {
                border: 2px solid #2196F3;
            }
        """)
        self.content_layout.addWidget(self.text_input)
        
        # Verify button
        verify_btn = QPushButton("🔍 Verify Statement")
        verify_btn.setMinimumHeight(50)
        verify_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14pt;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 15px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
            QPushButton:pressed {
                background-color: #2E7D32;
            }
        """)
        verify_btn.setCursor(Qt.PointingHandCursor)
        verify_btn.clicked.connect(self.verify_statement)
        self.content_layout.addWidget(verify_btn)
        
        # Results area
        self.results_label = QTextEdit()
        self.results_label.setReadOnly(True)
        self.results_label.setPlaceholderText("Verification results will appear here...\n\nYou can verify statements like:\n  • Classification: 'X is an NFR/FR/Operationalization'\n  • Decomposition: 'X is decomposed into Y and Z'\n  • Relationships: 'X contributes to Y'")
        self.results_label.setMinimumHeight(400)
        self.results_label.setStyleSheet("""
            QTextEdit {
                font-size: 13pt;
                padding: 20px;
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 20px;
            }
        """)
        self.results_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
        )
        self.content_layout.addWidget(self.results_label, stretch=1)
    
    def _build_metamodel_context(self, statement):
        """Build metamodel context to help LLM verify the statement"""
        from nfr_queries import (
            getAllNFRTypes, getAllOperationalizingTypes,
            getEntity, getDecompositionsFor, getEntityName, format_entity_name
        )
        from metamodel import NFRSoftgoalType, OperationalizingSoftgoalType
        
        context = "METAMODEL INFORMATION FOR VERIFICATION:\n\n"
        
        # Extract potential entity names (simple word extraction)
        words = statement.replace(',', ' ').replace('.', ' ').split()
        # Common words to ignore
        ignore_words = {'is', 'an', 'are', 'the', 'a', 'into', 'and', 'or', 'to', 'for', 
                       'of', 'in', 'on', 'with', 'by', 'from', 'as', 'at', 'nfr', 'fr',
                       'decomposed', 'operationalization', 'contributes', 'affects'}
        
        # Get potential entity names (capitalized words or longer words)
        potential_entities = [w for w in words if len(w) > 3 and w.lower() not in ignore_words]
        
        # Try to find matching entities in metamodel
        found_entities = []
        for potential_name in potential_entities:
            try:
                # Try fuzzy matching
                matched_name, _ = fuzzy_match_entity(potential_name)
                if matched_name:
                    entity = getEntity(matched_name)
                    found_entities.append((matched_name, entity))
            except:
                pass
        
        # Add information about found entities
        for entity_name, entity in found_entities:
            context += f"\n--- {format_entity_name(entity_name)} ---\n"
            
            # Check type
            if isinstance(entity, type) and issubclass(entity, NFRSoftgoalType):
                context += "Type: NFR Type\n"
            elif isinstance(entity, type) and issubclass(entity, OperationalizingSoftgoalType):
                context += "Type: Operationalizing Softgoal (Operationalization)\n"
            
            # Get decompositions
            try:
                decomps = getDecompositionsFor(entity)
                if decomps:
                    context += "Decomposition Methods:\n"
                    for decomp in decomps:
                        context += f"  - {decomp.name}\n"
                        if hasattr(decomp, 'offspring'):
                            offspring_names = [format_entity_name(o.__name__) for o in decomp.offspring]
                            context += f"    Offspring: {', '.join(offspring_names)}\n"
            except:
                pass
        
        # Add summary of all NFR types
        context += "\n--- ALL NFR TYPES IN METAMODEL ---\n"
        try:
            all_nfrs = getAllNFRTypes()  # Returns list of string names
            context += ", ".join(all_nfrs[:20])  # First 20
            if len(all_nfrs) > 20:
                context += f", ... ({len(all_nfrs)} total)"
            context += "\n"
        except:
            pass
        
        # Add summary of operationalizations
        context += "\n--- ALL OPERATIONALIZATIONS IN METAMODEL ---\n"
        try:
            all_ops = getAllOperationalizingTypes()
            op_names = [format_entity_name(op) for op in all_ops]
            context += ", ".join(op_names[:15])  # First 15
            if len(op_names) > 15:
                context += f", ... ({len(op_names)} total)"
            context += "\n"
        except:
            pass
        
        return context
    
    def verify_statement(self):
        """Verify the natural language statement against the metamodel"""
        text = self.text_input.toPlainText().strip()
        if not text:
            self.results_label.setText("⚠️ Please enter a statement to verify")
            return
        
        # Show loading
        self.results_label.setText("⏳ Analyzing your statement against the metamodel...")
        QApplication.processEvents()
        
        try:
            # Build metamodel context
            context = self._build_metamodel_context(text)
            
            # Use LLM to verify the statement
            if self.menu_llm:
                result = self.menu_llm.respond(
                    action_type="verify",
                    user_input=text,
                    metamodel_context=context
                )
                self.results_label.setText(result)
            else:
                self.results_label.setText("❌ LLM not available. Cannot parse natural language statements.\n\nPlease ensure Ollama is running and a model is available.")
                
        except Exception as e:
            import traceback
            self.results_label.setText(f"❌ Error during verification:\n\n{str(e)}\n\n{traceback.format_exc()}")



class ChatWindow(ModuleWindow):
    """Free-form chat window for asking questions about the NFR Framework"""
    
    def setup_content(self):
        # Initialize MenuLLM
        self.menu_llm = MenuLLM() if MENU_LLM_AVAILABLE else None
        self.chat_history = []  # Store conversation history

        from PySide6.QtWidgets import QTextEdit, QLabel, QVBoxLayout, QPushButton, QHBoxLayout
        
        # Instruction label
        instruction = QLabel("Ask any question about the NFR Framework:")
        instruction.setStyleSheet("font-size: 14pt; font-weight: bold; color: #333; margin-bottom: 10px;")
        self.content_layout.addWidget(instruction)
        
        # Chat display area - shows conversation history
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setPlaceholderText("Your conversation will appear here...\n\nAsk questions like:\n  • What NFR types are in the framework?\n  • How does Performance relate to Time and Space?\n  • What operationalizations help with Security?")
        self.chat_display.setMinimumHeight(300)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                font-size: 13pt;
                padding: 20px;
                background-color: #f5f5f5;
                border: 2px solid #ddd;
                border-radius: 8px;
            }
        """)
        self.content_layout.addWidget(self.chat_display, stretch=2)
        
        # Input area label
        input_label = QLabel("Your message:")
        input_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #555; margin-top: 15px; margin-bottom: 5px;")
        self.content_layout.addWidget(input_label)
        
        # Text input for user message
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Type your question here...")
        self.text_input.setMinimumHeight(80)
        self.text_input.setMaximumHeight(100)
        self.text_input.setStyleSheet("""
            QTextEdit {
                font-size: 13pt;
                padding: 15px;
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: white;
            }
            QTextEdit:focus {
                border: 2px solid #2196F3;
            }
        """)
        self.content_layout.addWidget(self.text_input)
        
        # Buttons row
        button_layout = QHBoxLayout()
        
        # Send button
        send_btn = QPushButton("💬 Send Message")
        send_btn.setMinimumHeight(50)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 14pt;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 15px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        send_btn.setCursor(Qt.PointingHandCursor)
        send_btn.clicked.connect(self.send_message)
        button_layout.addWidget(send_btn, stretch=3)
        
        # Clear button
        clear_btn = QPushButton("🗑️ Clear Chat")
        clear_btn.setMinimumHeight(50)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                font-size: 12pt;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 15px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
            QPushButton:pressed {
                background-color: #424242;
            }
        """)
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.clicked.connect(self.clear_chat)
        button_layout.addWidget(clear_btn, stretch=1)
        
        self.content_layout.addLayout(button_layout)
    
    def send_message(self):
        """Send user message and get AI response"""
        user_message = self.text_input.toPlainText().strip()
        if not user_message:
            return
        
        # Add user message to chat
        self.add_to_chat("You", user_message, "#2196F3")
        
        # Clear input
        self.text_input.clear()
        
        # Show thinking indicator
        self.chat_display.append("\n💭 Claude is thinking...\n")
        QApplication.processEvents()
        
        try:
            # Get AI response using MenuLLM
            if self.menu_llm:
                response = self.menu_llm.respond(
                    action_type="default",
                    user_input=user_message,
                    metamodel_context="Free-form chat about the NFR Framework. Answer questions naturally and helpfully."
                )
                
                # Remove thinking indicator and add response
                current_text = self.chat_display.toPlainText()
                if "💭 Claude is thinking..." in current_text:
                    current_text = current_text.replace("\n💭 Claude is thinking...\n", "")
                    self.chat_display.setPlainText(current_text)
                
                self.add_to_chat("Claude", response, "#4CAF50")
            else:
                self.add_to_chat("System", "❌ LLM not available. Please ensure Ollama is running.", "#f44336")
                
        except Exception as e:
            self.add_to_chat("System", f"❌ Error: {str(e)}", "#f44336")
    
    def add_to_chat(self, sender, message, color):
        """Add a message to the chat display"""
        self.chat_history.append((sender, message))
        
        # Format message with HTML for styling
        formatted = f'<div style="margin-bottom: 15px;">'
        formatted += f'<b style="color: {color}; font-size: 14pt;">{sender}:</b><br>'
        formatted += f'<span style="color: #333; font-size: 13pt;">{message.replace(chr(10), "<br>")}</span>'
        formatted += '</div>'
        
        self.chat_display.append(formatted)
        
        # Scroll to bottom
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_chat(self):
        """Clear the chat history"""
        self.chat_history = []
        self.chat_display.clear()
        self.chat_display.setPlaceholderText("Chat cleared. Ask me anything about the NFR Framework!")