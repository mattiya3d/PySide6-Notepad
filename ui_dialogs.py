from os import name
import subprocess, platform
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QComboBox, QLabel, QPushButton, QLineEdit, 
                             QCheckBox, QGroupBox, QMessageBox, QListWidget,
                             QListWidgetItem, QAbstractItemView, QRadioButton, QTextEdit,
                             QApplication, QStyleFactory)
from PySide6.QtCore import QSettings, Qt, QUrl
from PySide6.QtGui import (QFont, QFontDatabase, QTextCursor, QTextDocument, QTextCharFormat, QColor, 
                           QPalette, QDesktopServices, QGuiApplication, QPalette)

# Static reference map imported clean for layout settings calculations
from keyboard_layout import LAYOUT_REGISTRY, KEYS_ARABIC_101, KEYS_ENGLISH_US

# Global static sample mapping for writing systems to match original specifications
SCRIPT_SAMPLES = {
    "western": "AaBbYyZz",
    "greek": "ααββψψωω",
    "cyrillic": "дджжщщъъ",
    "arabic": "أبجد هوز AaBbYyZz",
    "hebrew": "אבגד AaBb",
    "persian": "درود بر شما 018",
    "urdu": "آپ کیسے ہیں 909",
    "chinese_simplified": "你好吗 123",
    "chinese_traditional": "你好嗎 456",
    "japanese": "日本語 こんにちは 789",
    "korean": "안녕하세요 303",
    "devanagari": "नमस्ते 404",
    "bengali": "নमস্কার 505",
    "telugu": "నమస్కారం 606",
    "marathi": "शुभ प्रभात 707",
    "tamil": "வணக்கம் 808",
    "gujarati": "નમસ્તે 010",
    "kannada": "ನಮಸ್කාර 011",
    "malayalam": "നമസ്കാരം 012",
    "gurmukhi": "ਸਤِ Shrī Akāl 013",
    "thai": "กขคง AaBb",
    "vietnamese": "Xin chào 014",
    "myanmar": "မင်္ဂလာပါ 015",
    "khmer": "សួស្តី 016",
    "lao": "ສະบายດີ 017",
    "georgian": "გამარჯობა 019",
    "armenian": "Բարև ձեզ 020",
    "ethiopic": "ሰላም 021",
    "tifinagh": "ⵜⴰⵣⵉⵖⵜ 022"
}

def get_normalized_script_key(script_name):
    #Helper utility to normalize writing system names to matching script keys.#
    lookup_key = str(script_name).lower().strip().replace(" ", "_")
    if "chinesesimplified" in lookup_key or "simplified_chinese" in lookup_key:
        return "chinese_simplified"
    elif "chinesetraditional" in lookup_key or "traditional_chinese" in lookup_key:
        return "chinese_traditional"
    elif "korean_hangul" in lookup_key:
        return "korean"
    elif "burmese" in lookup_key:
        return "myanmar"
    elif "amharic" in lookup_key or "ge_ez" in lookup_key:
        return "ethiopic"
    elif "berber" in lookup_key:
        return "tifinagh"
    elif "punjabi" in lookup_key:
        return "gurmukhi"
    elif "hindi" in lookup_key:
        return "devanagari"
    return lookup_key

# ========================================================
# 1. 🔍 FIND & REPLACE INDEPENDENT DIALOG (With Dual-Blue Engine)
# ========================================================
class FindReplaceDialog(QDialog):
    def __init__(self, parent=None, editor=None, mode=1):
        super().__init__(parent)
        self.editor = editor
        self.mode = mode # 0 = Find Mode, 1 = Replace Mode
        self.setWindowTitle("Find" if mode == 0 else "Replace")
        self.setFixedSize(465, 170 if mode == 0 else 205)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.init_ui()

    def init_ui(self):
        layout_main = QHBoxLayout(self)
        layout_main.setContentsMargins(15, 15, 15, 15)
        layout_main.setSpacing(15)

        layout_left = QVBoxLayout()
        layout_left.setSpacing(10)

        grid_inputs = QGridLayout()
        grid_inputs.setHorizontalSpacing(10)
        grid_inputs.setVerticalSpacing(8)

        label_find = QLabel("Fi&nd what:")
        self.lineEdit_find = QLineEdit()
        label_find.setBuddy(self.lineEdit_find)
        grid_inputs.addWidget(label_find, 0, 0)
        grid_inputs.addWidget(self.lineEdit_find, 0, 1)

        self.label_replace = QLabel("Re&place with:")
        self.lineEdit_replace = QLineEdit()
        self.label_replace.setBuddy(self.lineEdit_replace)
        grid_inputs.addWidget(self.label_replace, 1, 0)
        grid_inputs.addWidget(self.lineEdit_replace, 1, 1)

        layout_left.addLayout(grid_inputs)
        layout_left.addStretch()

        layout_options_container = QHBoxLayout()
        
        layout_checkboxes = QVBoxLayout()
        self.checkbox_matchCase = QCheckBox("Match &case")
        self.checkbox_matchWhole = QCheckBox("Match &whole word only")
        self.checkbox_wrapAround = QCheckBox("W&rap around")
        self.checkbox_wrapAround.setChecked(True)

        layout_checkboxes.addWidget(self.checkbox_matchCase)
        layout_checkboxes.addWidget(self.checkbox_matchWhole)
        layout_checkboxes.addWidget(self.checkbox_wrapAround)
        layout_options_container.addLayout(layout_checkboxes)

        self.group_direction = QGroupBox("Direction")
        layout_direction = QHBoxLayout(self.group_direction)
        self.radioButton_up = QRadioButton("U&p")
        self.radioButton_down = QRadioButton("Do&wn")
        self.radioButton_down.setChecked(True)
        
        layout_direction.addWidget(self.radioButton_up)
        layout_direction.addWidget(self.radioButton_down)
        layout_options_container.addWidget(self.group_direction)

        layout_left.addLayout(layout_options_container)

        layout_right = QVBoxLayout()
        layout_right.setSpacing(6)

        self.button_find = QPushButton("&Find Next")
        self.button_replace = QPushButton("&Replace")
        self.button_replaceAll = QPushButton("Replace &All")
        self.button_cancel = QPushButton("Cancel")

        self.button_find.setDefault(True)

        layout_right.addWidget(self.button_find)
        layout_right.addWidget(self.button_replace)
        layout_right.addWidget(self.button_replaceAll)
        layout_right.addWidget(self.button_cancel)
        layout_right.addStretch()

        layout_main.addLayout(layout_left)
        layout_main.addLayout(layout_right)

        if self.mode == 0:
            self.label_replace.hide()
            self.lineEdit_replace.hide()
            self.button_replace.hide()
            self.button_replaceAll.hide()
            self.group_direction.show()
        else:
            self.group_direction.hide()

        self.button_find.clicked.connect(self.find_next)
        self.button_replace.clicked.connect(self.replace_current_occurrence)
        self.button_replaceAll.clicked.connect(self.replace_all_occurrences)
        self.button_cancel.clicked.connect(self.reject)

        self.lineEdit_find.textChanged.connect(self.highlight_all_matches)
        self.checkbox_matchCase.stateChanged.connect(self.highlight_all_matches)
        self.checkbox_matchWhole.stateChanged.connect(self.highlight_all_matches)
        self.radioButton_up.toggled.connect(self.highlight_all_matches)
        self.radioButton_down.toggled.connect(self.highlight_all_matches)

    def get_search_flags(self):
        flags = QTextDocument.FindFlag(0)
        if self.checkbox_matchCase.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        if self.checkbox_matchWhole.isChecked():
            flags |= QTextDocument.FindFlag.FindWholeWords
        if self.radioButton_up.isChecked() and self.mode == 0:
            flags |= QTextDocument.FindFlag.FindBackward
        return flags

    def find_next(self):
        # Executes the next text match search and forces Windows selection palette constraints.
        # Grab the active editor via the parent (MainWindow) interface safely
        if hasattr(self, 'parent') and self.parent():
            current_editor = self.parent().get_current_editor()
        else:
            current_editor = None
        # FORCE BLUE HIGHLIGHT: Override selection colors right before executing the search lookup
        if name == 'nt':
            palette = current_editor.palette()
            
            # Active Highlight (focused word)
            palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Highlight, QColor("#0078d7"))
            palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
            
            # Inactive Highlight (in case the Find Dialog takes focus away from editor)
            palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Highlight, QColor("#0078d7"))
            palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
            
            current_editor.setPalette(palette)

        search_term = self.lineEdit_find.text()
        if not search_term: 
            return

        found = self.editor.find(search_term, self.get_search_flags())
        if not found and self.checkbox_wrapAround.isChecked():
            cursor = self.editor.textCursor()
            if self.radioButton_up.isChecked() and self.mode == 0:
                cursor.movePosition(QTextCursor.MoveOperation.End)
            else:
                cursor.movePosition(QTextCursor.MoveOperation.Start)
            self.editor.setTextCursor(cursor)
            found = self.editor.find(search_term, self.get_search_flags())
        
        if found:
            self.editor.setFocus()
            self.highlight_all_matches()
        else:
            QMessageBox.information(self, "Find", f"Cannot find '{search_term}'")

    def replace_current_occurrence(self):
        if not self.editor: 
            return
        cursor = self.editor.textCursor()
        if cursor.selectedText() == self.lineEdit_find.text():
            cursor.insertText(self.lineEdit_replace.text())
            self.editor.setTextCursor(cursor)
        self.find_next()

    def replace_all_occurrences(self):
        if not self.editor: 
            return
        search_term = self.lineEdit_find.text()
        if not search_term: 
            return
        replace_term = self.lineEdit_replace.text()

        cursor = self.editor.textCursor()
        cursor.beginEditBlock()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.editor.setTextCursor(cursor)

        count = 0
        while self.editor.find(search_term, self.get_search_flags()):
            self.editor.textCursor().insertText(replace_term)
            count += 1

        cursor.endEditBlock()
        self.highlight_all_matches()
        QMessageBox.information(self, "Replace All", f"All done! Replaced {count} occurrences.")

    def highlight_all_matches(self):
        if not self.editor:
            return
        search_term = self.lineEdit_find.text()
        if not search_term:
            self.editor.setExtraSelections([])
            return

        extra_selections = []
        document = self.editor.document()
        flags = self.get_search_flags()

        all_matches_format = QTextCharFormat()
        is_dark = self.editor.palette().color(QPalette.ColorRole.Window).value() < 128
        if is_dark:
            all_matches_format.setBackground(QColor(0, 120, 215, 60))
        else:
            all_matches_format.setBackground(QColor(0, 120, 215, 35))

        current_match_format = QTextCharFormat()
        current_match_format.setBackground(QColor("#0078d7"))
        current_match_format.setForeground(QColor("#ffffff"))

        current_cursor = self.editor.textCursor()
        current_start = current_cursor.selectionStart()
        current_end = current_cursor.selectionEnd()

        search_cursor = QTextCursor(document)
        while True:
            search_cursor = document.find(search_term, search_cursor, flags)
            if search_cursor.isNull():
                break
            
            selection = QTextEdit.ExtraSelection()
            selection.cursor = search_cursor
            
            if search_cursor.selectionStart() == current_start and search_cursor.selectionEnd() == current_end:
                selection.format = current_match_format
            else:
                selection.format = all_matches_format
                
            extra_selections.append(selection)

        self.editor.setExtraSelections(extra_selections)

    def closeEvent(self, event):
        if self.editor:
            self.editor.setExtraSelections([])
        event.accept()


# ========================================================
# 2. 🔤 CUSTOM ARCHITECTURAL FONT WINDOW DIALOG (Fully Restored Design)
# ========================================================
class CustomFontDialog(QDialog):
    def __init__(self, parent=None, current_font=None):
        super().__init__(parent)
        self.selected_font = current_font if current_font else QFont()
        self.setWindowTitle("Font")
        self.setFixedSize(440, 560) # Re-pinned exactly to your native size
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.init_ui()

    def init_ui(self):
        layout_main = QGridLayout(self)
        layout_main.setContentsMargins(15, 15, 15, 15)
        layout_main.setHorizontalSpacing(15)
        layout_main.setVerticalSpacing(8)

        # Column 0: Font (Segoe UI original width 172px)
        label_font = QLabel("Font:")
        self.lineEdit_font_name = QLineEdit()
        self.lineEdit_font_name.setFixedWidth(172)
        self.list_font_name = QListWidget()
        self.list_font_name.setFixedWidth(172)
        self.list_font_name.setFixedHeight(160)
        self.list_font_name.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list_font_name.addItems(QFontDatabase.families())
        
        layout_main.addWidget(label_font, 0, 0)
        layout_main.addWidget(self.lineEdit_font_name, 1, 0)
        layout_main.addWidget(self.list_font_name, 2, 0)

        # Column 1: Font style (Original width 130px)
        label_style = QLabel("Font style:")
        self.lineEdit_font_style = QLineEdit()
        self.lineEdit_font_style.setFixedWidth(130)
        self.list_font_style = QListWidget()
        self.list_font_style.setFixedWidth(130)
        self.list_font_style.setFixedHeight(160)
        self.list_font_style.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        layout_main.addWidget(label_style, 0, 1)
        layout_main.addWidget(self.lineEdit_font_style, 1, 1)
        layout_main.addWidget(self.list_font_style, 2, 1)

        # Column 2: Size (Original width 64px)
        label_size = QLabel("Size:")
        self.lineEdit_font_size = QLineEdit()
        self.lineEdit_font_size.setFixedWidth(64)
        self.list_font_size = QListWidget()
        self.list_font_size.setFixedWidth(64)
        self.list_font_size.setFixedHeight(160)
        self.list_font_size.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list_font_size.addItems(["8", "9", "10", "11", "12", "14", "16", "18", "20", "22", "24", "26", "28", "36", "48", "72"])

        layout_main.addWidget(label_size, 0, 2)
        layout_main.addWidget(self.lineEdit_font_size, 1, 2)
        layout_main.addWidget(self.list_font_size, 2, 2)

        # Column 1 & 2 Combined width is 130 (Style) + 15 (Spacing) + 64 (Size) = 209px
        # Sample box spans columns 1 and 2 perfectly aligned
        self.groupBox_font_preview = QGroupBox("Sample")
        self.groupBox_font_preview.setFixedWidth(209)
        layout_preview = QVBoxLayout(self.groupBox_font_preview)
        self.label_font_preview = QLabel("AaBbYyZz")
        self.label_font_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_font_preview.setMinimumHeight(75)
        layout_preview.addWidget(self.label_font_preview)
        layout_main.addWidget(self.groupBox_font_preview, 3, 1, 1, 2)

        # Script dropdown spans columns 1 and 2 perfectly aligned
        label_script = QLabel("Script:")
        self.list_font_script = QComboBox()
        self.list_font_script.setFixedWidth(209)
        
        layout_main.addWidget(label_script, 4, 1, 1, 2)
        layout_main.addWidget(self.list_font_script, 5, 1, 1, 2)

        # Left bottom "Show more fonts" link aligned
        self.button_show_more = QPushButton("Show more fonts")
        self.button_show_more.setFlat(True)
        self.button_show_more.setStyleSheet("color: #0066cc; text-decoration: underline; text-align: left; background: transparent; border: none; font-size: 11px;")
        self.button_show_more.clicked.connect(self.show_more_fonts_logic)
        layout_main.addWidget(self.button_show_more, 6, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft)

        # Bottom right OK & Cancel buttons layout spanning columns 1 and 2
        layout_buttons = QHBoxLayout()
        layout_buttons.addStretch()
        button_font_ok = QPushButton("OK")
        button_font_ok.setDefault(True)
        button_font_ok.clicked.connect(self.accept)
        
        button_font_cancel = QPushButton("Cancel")
        button_font_cancel.clicked.connect(self.reject)
        
        layout_buttons.addWidget(button_font_ok)
        layout_buttons.addWidget(button_font_cancel)
        layout_main.addLayout(layout_buttons, 6, 1, 1, 2, Qt.AlignmentFlag.AlignBottom)

        # Connect list triggers to update edits and preview font
        self.list_font_name.itemSelectionChanged.connect(self.update_preview_font)
        self.list_font_style.itemSelectionChanged.connect(self.update_preview_font)
        self.list_font_size.itemSelectionChanged.connect(self.update_preview_font)

        # Connect text changes for live search filtering
        self.lineEdit_font_name.textChanged.connect(self.update_preview_font)
        self.lineEdit_font_style.textChanged.connect(self.update_preview_font)
        self.lineEdit_font_size.textChanged.connect(self.update_preview_font)
        self.list_font_script.currentTextChanged.connect(self.update_preview_sample_text)

        # Populate current setup
        system_font_name = self.selected_font.family()
        system_font_size = self.selected_font.pointSize()
        
        self.lineEdit_font_name.setText(system_font_name)
        self.lineEdit_font_size.setText(str(system_font_size))
        
        if self.selected_font.bold() and self.selected_font.italic():
            self.lineEdit_font_style.setText("Bold Italic")
        elif self.selected_font.bold():
            self.lineEdit_font_style.setText("Bold")
        elif self.selected_font.italic():
            self.lineEdit_font_style.setText("Italic")
        else:
            self.lineEdit_font_style.setText("Regular")

        # Select corresponding elements
        item_font = self.list_font_name.findItems(system_font_name, Qt.MatchFlag.MatchExactly)
        if item_font:
            self.list_font_name.setCurrentItem(item_font[0])
            self.list_font_name.scrollToItem(item_font[0])
            
        item_size = self.list_font_size.findItems(str(system_font_size), Qt.MatchFlag.MatchExactly)
        if item_size:
            self.list_font_size.setCurrentItem(item_size[0])
            self.list_font_size.scrollToItem(item_size[0])

        self.update_preview_font()

    def update_preview_font(self):
        preview_font_name = self.lineEdit_font_name.text()
        preview_font_style = self.lineEdit_font_style.text()
        preview_font_size = self.lineEdit_font_size.text()

        if not preview_font_name or preview_font_name.strip() == "":
            return

        sender = self.sender()

        # Input searching filters matching lists
        if sender == self.lineEdit_font_name and preview_font_name:
            items = self.list_font_name.findItems(preview_font_name, Qt.MatchFlag.MatchStartsWith)
            if items:
                self.list_font_name.blockSignals(True)
                self.list_font_name.setCurrentItem(items[0])
                self.list_font_name.scrollToItem(items[0])
                self.list_font_name.blockSignals(False)
                preview_font_name = items[0].text()

        if sender == self.lineEdit_font_style and preview_font_style:
            items = self.list_font_style.findItems(preview_font_style, Qt.MatchFlag.MatchStartsWith)
            if items:
                self.list_font_style.blockSignals(True)
                self.list_font_style.setCurrentItem(items[0])
                self.list_font_style.blockSignals(False)
                preview_font_style = items[0].text()

        if sender == self.lineEdit_font_size and preview_font_size:
            items = self.list_font_size.findItems(preview_font_size, Qt.MatchFlag.MatchExactly)
            if not items:
                items = self.list_font_size.findItems(preview_font_size, Qt.MatchFlag.MatchStartsWith)
            if items:
                self.list_font_size.blockSignals(True)
                self.list_font_size.setCurrentItem(items[0])
                self.list_font_size.scrollToItem(items[0])
                self.list_font_size.blockSignals(False)
                preview_font_size = items[0].text()

        # Update input text indicators when selections shift
        if sender != self.lineEdit_font_name and self.list_font_name.currentItem():
            self.lineEdit_font_name.blockSignals(True)
            self.lineEdit_font_name.setText(self.list_font_name.currentItem().text())
            self.lineEdit_font_name.blockSignals(False)
            preview_font_name = self.lineEdit_font_name.text()

        if sender != self.lineEdit_font_style and self.list_font_style.currentItem():
            self.lineEdit_font_style.blockSignals(True)
            self.lineEdit_font_style.setText(self.list_font_style.currentItem().text())
            self.lineEdit_font_style.blockSignals(False)
            preview_font_style = self.lineEdit_font_style.text()
            
        if sender != self.lineEdit_font_size and self.list_font_size.currentItem():
            self.lineEdit_font_size.blockSignals(True)
            self.lineEdit_font_size.setText(self.list_font_size.currentItem().text())
            self.lineEdit_font_size.blockSignals(False)
            preview_font_size = self.lineEdit_font_size.text()

        size_corrected = int(preview_font_size) if preview_font_size.isdigit() else 12
        preview_font = QFontDatabase.font(preview_font_name, preview_font_style, size_corrected)
        self.label_font_preview.setFont(preview_font)

        # Repopulate script dropdown dynamically matching chosen family
        self.list_font_script.blockSignals(True)
        current_script = self.list_font_script.currentText()
        self.list_font_script.clear()
        
        for system_id in QFontDatabase.writingSystems(preview_font_name):
            script_name = QFontDatabase.writingSystemName(system_id)
            self.list_font_script.addItem(script_name)
        
        index = self.list_font_script.findText(current_script)
        if index != -1:
            self.list_font_script.setCurrentIndex(index)
        else:
            self.list_font_script.setCurrentIndex(0)
        self.list_font_script.blockSignals(False)

        # Populate supported style subsets
        if sender != self.lineEdit_font_style:
            self.list_font_style.blockSignals(True)
            self.list_font_style.clear()
            
            supported_styles = QFontDatabase.styles(preview_font_name)
            for style_name in supported_styles:
                item = QListWidgetItem(style_name)
                item_font = QFontDatabase.font(preview_font_name, style_name, 10)
                item.setFont(item_font)
                self.list_font_style.addItem(item)
            
            style_found = self.list_font_style.findItems(preview_font_style, Qt.MatchFlag.MatchExactly)
            if style_found:
                self.list_font_style.setCurrentItem(style_found[0])
            elif self.list_font_style.count() > 0:
                self.list_font_style.setCurrentRow(0)
                self.lineEdit_font_style.setText(self.list_font_style.currentItem().text())

            self.list_font_style.blockSignals(False)
            
        self.update_preview_sample_text(self.list_font_script.currentText())

    def update_preview_sample_text(self, script_name):
        lookup_key = get_normalized_script_key(script_name)
        sample_text = SCRIPT_SAMPLES.get(lookup_key, "AaBbYyZz")
        self.label_font_preview.setText(sample_text)

    def get_chosen_font_metrics(self):
        return self.lineEdit_font_name.text(), self.lineEdit_font_style.text(), self.lineEdit_font_size.text()

    def show_more_fonts_logic(self):
        # Launches the native system fonts management utility depending on the host platform.
        # Supports Windows Settings, Linux System Settings (KDE/GNOME), and falls back to Google Fonts.


        # Check if the host platform is Windows
        if name == 'nt':
            # Windows platform: Launch the modern native URI font settings
            QDesktopServices.openUrl(QUrl("ms-settings:fonts"))
        
        # Check if the platform is Linux using the robust platform module
        elif platform.system().lower() == 'linux':
            # Linux platform: Proactively try running standard desktop font managers
            try:
                # Target KDE Plasma configuration module for system fonts
                subprocess.Popen(["kcmshell6", "kcm_fonts"])
            except FileNotFoundError:
                try:
                    # Target GNOME desktop system font manager as a secondary fallback
                    subprocess.Popen(["gnome-control-center", "fonts"])
                except FileNotFoundError:
                    # Desktop agnostic fallback to localized font configuration folder
                    QDesktopServices.openUrl(QUrl.fromLocalFile("/usr/share/fonts/"))
        else:
            # macOS and other UNIX platforms: Open browser fallback interface
            QDesktopServices.openUrl(QUrl("https://fonts.google.com"))


# ========================================================
# 3.  GO TO SPECIFIC LINE POPUP DIALOG
# ========================================================
class GoToDialog(QDialog):
    def __init__(self, parent=None, max_lines=1):
        super().__init__(parent)
        self.max_lines = max_lines
        self.target_line = -1
        self.setWindowTitle("Go To Line")
        self.setFixedSize(280, 110)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.init_ui()

    def init_ui(self):
        layout_main = QVBoxLayout(self)
        
        self.label_info = QLabel(f"Line number (1 - {self.max_lines}):")
        layout_main.addWidget(self.label_info)

        self.edit_line = QLineEdit()
        layout_main.addWidget(self.edit_line)

        layout_buttons = QHBoxLayout()
        btn_ok = QPushButton("Go To")
        btn_ok.clicked.connect(self.validate_and_accept_line)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        
        layout_buttons.addWidget(btn_ok)
        layout_buttons.addWidget(btn_cancel)
        layout_main.addLayout(layout_buttons)

    def validate_and_accept_line(self):
        input_text = self.edit_line.text()
        if input_text.isdigit():
            val = int(input_text)
            if 1 <= val <= self.max_lines:
                self.target_line = val
                self.accept()
                return
        QMessageBox.warning(self, "Error", f"Please enter a valid line number between 1 and {self.max_lines}.")


# ========================================================
# 4. ⌨️ LAYOUT SETTINGS DIALOG (With Smart Conflict Protection)
# ========================================================
class LayoutSettingsDialog(QDialog):
    def __init__(self, parent=None, org_name="Mattiya3D", app_name="PySide6Notepad"):
        super().__init__(parent)
        self.org_name = org_name
        self.app_name = app_name
        self.setWindowTitle("Layout Settings")
        self.setMinimumWidth(450)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.init_ui()

    def init_ui(self):
        layout_main = QVBoxLayout(self)

        self.combo_lang_1 = QComboBox()
        self.combo_kb_1 = QComboBox()
        self.combo_lang_2 = QComboBox()
        self.combo_kb_2 = QComboBox()

        self.languages = ["Arabic", "English", "Spanish", "French", "German", "Russian", "Portuguese", "Hindi", "Italian"]
        self.combo_lang_1.addItems(self.languages)

        self.combo_lang_1.currentTextChanged.connect(self.update_secondary_language_list)
        self.combo_lang_2.currentTextChanged.connect(self.update_keyboards_lists)

        grid = QGridLayout()
        grid.addWidget(QLabel("First Language:"), 0, 0)
        grid.addWidget(self.combo_lang_1, 0, 1)
        grid.addWidget(QLabel("First Layout:"), 1, 0)
        grid.addWidget(self.combo_kb_1, 1, 1)
        grid.addWidget(QLabel("Second Language:"), 2, 0)
        grid.addWidget(self.combo_lang_2, 2, 1)
        grid.addWidget(QLabel("Second Layout:"), 3, 0)
        grid.addWidget(self.combo_kb_2, 3, 1)
        layout_main.addLayout(grid)

        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.save_converter_preferences)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout_main.addLayout(btn_layout)

        self.update_secondary_language_list()
        self.load_converter_preferences()

    def update_secondary_language_list(self):
        self.combo_lang_2.blockSignals(True)
        
        current_l2_selection = self.combo_lang_2.currentText()
        self.combo_lang_2.clear()
        
        selected_1 = self.combo_lang_1.currentText()
        filtered_list = [lang for lang in self.languages if lang != selected_1]
        self.combo_lang_2.addItems(filtered_list)
        
        idx = self.combo_lang_2.findText(current_l2_selection)
        if idx != -1:
            self.combo_lang_2.setCurrentIndex(idx)
        else:
            self.combo_lang_2.setCurrentIndex(0)
            
        self.combo_lang_2.blockSignals(False)
        self.update_keyboards_lists()

    def update_keyboards_lists(self):
        for combo, lang_combo in [(self.combo_kb_1, self.combo_lang_1), (self.combo_kb_2, self.combo_lang_2)]:
            combo.blockSignals(True)
            combo.clear()
            lang = lang_combo.currentText()
            
            if lang == "Arabic":
                combo.addItems(["Arabic 101", "Arabic 102", "Mac Arabic"])
            elif lang == "English":
                combo.addItems(["Standard US"])
            elif lang == "Spanish":
                combo.addItems(["Spanish Traditional", "Spanish Latin American"])
            elif lang == "French":
                combo.addItems(["French AZERTY", "French Mac"])
            elif lang == "German":
                combo.addItems(["German QWERTZ", "German IBM"])
            elif lang == "Russian":
                combo.addItems(["Russian Standard", "Russian Phonetic"])
            elif lang == "Portuguese":
                combo.addItems(["Portuguese (Brazil)", "Portuguese (Portugal)"])
            elif lang == "Hindi":
                combo.addItems(["Hindi InScript", "Hindi Phonetic"])
            elif lang == "Italian":
                combo.addItems(["Italian Standard"])
                
            combo.blockSignals(False)

    def save_converter_preferences(self):
        settings = QSettings(self.org_name, self.app_name)
        settings.setValue("layout_converter_lang_1", self.combo_lang_1.currentText())
        settings.setValue("layout_converter_kb_1", self.combo_kb_1.currentText())
        settings.setValue("layout_converter_lang_2", self.combo_lang_2.currentText())
        settings.setValue("layout_converter_kb_2", self.combo_kb_2.currentText())
        self.accept()

    def load_converter_preferences(self):
        settings = QSettings(self.org_name, self.app_name)
        saved_l1 = settings.value("layout_converter_lang_1", "Arabic")
        saved_k1 = settings.value("layout_converter_kb_1", "Arabic 101")
        saved_l2 = settings.value("layout_converter_lang_2", "English")
        saved_k2 = settings.value("layout_converter_kb_2", "Standard US")

        idx_l1 = self.combo_lang_1.findText(saved_l1)
        if idx_l1 != -1: 
            self.combo_lang_1.setCurrentIndex(idx_l1)
            
        self.update_secondary_language_list()
        
        idx_l2 = self.combo_lang_2.findText(saved_l2)
        if idx_l2 != -1: 
            self.combo_lang_2.setCurrentIndex(idx_l2)
            
        self.update_keyboards_lists()

        idx_k1 = self.combo_kb_1.findText(saved_k1)
        if idx_k1 != -1: self.combo_kb_1.setCurrentIndex(idx_k1)
        
        idx_k2 = self.combo_kb_2.findText(saved_k2)
        if idx_k2 != -1: self.combo_kb_2.setCurrentIndex(idx_k2)


class ThemeManager:
    @staticmethod
    def apply_theme(theme_type, tabs_widget, status_bar=None):
        #Full centralized control over the application theme (Light/Dark/System)
        #Automatically updates all active tabs and color-codes.
    

        # Set the style to Fusion to ensure color flexibility across systems
        QApplication.setStyle(QStyleFactory.create("Fusion"))

        if theme_type == "system":
            QGuiApplication.styleHints().unsetColorScheme()
            if status_bar: status_bar.showMessage("Following system color scheme", 3000)
        elif theme_type == "dark":
            QGuiApplication.styleHints().setColorScheme(Qt.ColorScheme.Dark)
            if status_bar: status_bar.showMessage("Theme changed to Dark Mode", 3000)
        elif theme_type == "light":
            QGuiApplication.styleHints().setColorScheme(Qt.ColorScheme.Light)
            if status_bar: status_bar.showMessage("Theme changed to Light Mode", 3000)

        # Bringing the new Palette after changing the system and applying it to the entire application
        palette = QGuiApplication.palette()
        QApplication.setPalette(palette)
        
        # Check if the system is currently in dark mode or not (to update the Highlighter)
        is_dark_now = (QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark) if theme_type == "system" else (theme_type == "dark")

        # Go through all open tabs to update their colors and the colors of their respective code colorizers
        if tabs_widget:
            for i in range(tabs_widget.count()):
                editor = tabs_widget.widget(i)
                if editor:
                    editor.setPalette(palette)
                    if hasattr(editor, 'highlighter') and editor.highlighter:
                        editor.highlighter.set_theme_mode(is_dark_now)