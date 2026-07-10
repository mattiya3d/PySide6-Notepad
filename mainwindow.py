# ==========================================
# 1. STANDARD PYTHON LIBRARIES
# ==========================================
import time
import chardet
import sys
# For security reasons, I didn't import the whole os
from os import path, makedirs, listdir, remove, access, W_OK, name
import logging
import resources_rc
# ==========================================
# 2. PYSIDE6 / QT FRAMEWORK INTERFACES
# ==========================================
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QTextEdit, QMessageBox, QLabel, QFileDialog, 
    QDialog,QApplication, QTabWidget, QToolBar, QToolButton
)
from PySide6.QtCore import Qt, QStandardPaths, QDateTime, QSettings, QTimer, QUrl, QSize
from PySide6.QtGui import (
    QAction, QKeySequence, QIcon, QTextCursor, QColor, QPalette, QPainter, 
    QFontDatabase, QActionGroup, QGuiApplication, QDesktopServices, QTextDocument
)
from PySide6.QtPrintSupport import QPageSetupDialog, QPrintDialog, QPrinter

# ==========================================
# 3. STATIC AND STRUCTURAL UTILITIES
# ==========================================
from keyboard_layout import convert_string_layout

# ==========================================
# 4. ENCAPSULATED RE-FABRICATED MODULES
# ==========================================
from editor_utilities import (
    CodeHighlighter,
    calculate_text_metrics,
    detect_line_endings_logic,
    encrypt_payload,
    decrypt_payload,
    open_and_decode_file_logic,
    save_and_encode_file_logic,
    execute_auto_backup_logic,
    clean_individual_file_backup,
    change_icon_color_logic,
    apply_highlighter_to_editor
)
from ui_dialogs import FindReplaceDialog, CustomFontDialog, GoToDialog, LayoutSettingsDialog, ThemeManager


# ==========================================
# 5. LINE NUMBER AREA GRAPHICAL PAINTBOX
# ==========================================
class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)
        

# ==========================================
# 6. ENHANCED TEXT WRITER INSTANCE
# ==========================================
class ZoomableTextEdit(QTextEdit):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.line_number_area = LineNumberArea(self)
        self.tab_zoom_percentage = 100
        
        # Geometry alignments signals
        self.document().blockCountChanged.connect(self.update_line_number_area_width)
        self.verticalScrollBar().valueChanged.connect(lambda: self.line_number_area.update())
        self.textChanged.connect(lambda: self.line_number_area.update())
        self.cursorPositionChanged.connect(lambda: self.line_number_area.update())
        
        self.set_line_numbers_visible(False)
        self.update_line_number_area_width()

    def line_number_area_width(self):
        digits = 1
        max_blocks = max(1, self.document().blockCount())
        while max_blocks >= 10:
            max_blocks /= 10
            digits += 1
        space = 15 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self):
        if self.line_number_area.isVisible():
            self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
        else:
            self.setViewportMargins(0, 0, 0, 0)

    def set_line_numbers_visible(self, visible):
        self.line_number_area.setVisible(visible)
        self.update_line_number_area_width()
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.update_line_number_area_width()
        self.line_number_area.setGeometry(cr.left(), cr.top(), self.line_number_area_width(), cr.height())

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        bg_color = self.palette().color(QPalette.ColorRole.Window)
        text_color = self.palette().color(QPalette.ColorRole.WindowText)
        
        muted_text_color = QColor(text_color)
        muted_text_color.setAlpha(110)
        painter.fillRect(event.rect(), bg_color)

        block = self.document().begin()
        block_number = block.blockNumber()
        top = round(self.document().documentLayout().blockBoundingRect(block).top())
        bottom = top + round(self.document().documentLayout().blockBoundingRect(block).height())
        scroll_offset = self.verticalScrollBar().value()
        
        while block.isValid():
            if block.isVisible():
                line_top = top - scroll_offset
                if line_top >= event.rect().bottom():
                    break
                if line_top + (bottom - top) >= event.rect().top():
                    number_str = str(block_number + 1)
                    painter.setPen(muted_text_color)
                    painter.setFont(self.font())
                    painter.drawText(0, line_top, self.line_number_area_width() - 8, self.fontMetrics().height(),
                                     Qt.AlignmentFlag.AlignRight, number_str)

            block = block.next()
            top = bottom
            bottom = top + round(self.document().documentLayout().blockBoundingRect(block).height())
            block_number += 1

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.main_window.zoom_in()
            elif delta < 0:
                self.main_window.zoom_out()
            self.main_window.label_zoom.setText(f"{self.tab_zoom_percentage}%")
            self.line_number_area.update()
            self.update_line_number_area_width()
            event.accept()
            return
        super().wheelEvent(event)

    def dragEnterEvent(self, event):
        event.ignore()

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        actions = menu.actions()
        
        for action in actions:
            if action.text() == "&Paste" or "Paste" in action.text():
                paste_plain_action = QAction("Paste as Plain Te&xt", self)
                paste_plain_action.setShortcut("Ctrl+Shift+V")
                
                if action.icon() and not action.icon().isNull():
                    paste_plain_action.setIcon(action.icon())
                else:
                    standard_icon = self.style().standardIcon(self.style().StandardPixmap.SP_FileDialogContentsView)
                    paste_plain_action.setIcon(standard_icon)
                
                paste_plain_action.triggered.connect(self.main_window.paste_as_plain_text)
                idx = actions.index(action)
                if idx + 1 < len(actions):
                    menu.insertAction(actions[idx + 1], paste_plain_action)
                else:
                    menu.addAction(paste_plain_action)
                break
                
        cursor = self.textCursor()
        if cursor.hasSelection():
            menu.addSeparator()
            menu.addAction(self.main_window.action_convert_now)
            
        menu.exec(event.globalPos())


# ========================================================
# 7. MAIN ENGINE DESKTOP ARCHITECTURE (Lean & Clean)
# ========================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 Notepad")
        self.org_name = "Mattiya3D"
        self.app_name = "PySide6Notepad"
        self.printer = QPrinter()
        self.current_theme = "system"
        # Initialize parent search state variables to support F3 / Shift+F3 repeat functions
        self.last_search_term = ""
        self.last_search_flags = QTextDocument.FindFlag(0)
        QGuiApplication.styleHints().colorSchemeChanged.connect(self._on_os_theme_changed)

        # Track the last successfully accessed directory to improve UX during File I/O
        self.last_opened_directory = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)

        if len(sys.argv) > 1:
            target_file_path = sys.argv[1]
            if path.isfile(target_file_path):
                # Safely trigger the programmatic loader for the passed CLI path
                self.open_file_from_cli_path(target_file_path)

        # Status Bar components setup
        self.status_bar = self.statusBar()
        self.label_left_status = QLabel()
        self.label_lines_words = QLabel("Lines: 0, Words: 0")
        self.label_cursor_location = QLabel(f"Ln {1}, Col {1}")
        self.label_zoom = QLabel("100%")
        self.label_encoder = QLabel("UTF-8 | CRLF" if name == 'nt' else "UTF-8 | LF")

        self.status_bar.addWidget(self.label_left_status, 1)
        self.status_bar.addPermanentWidget(self.label_lines_words)
        self.status_bar.addPermanentWidget(self.label_cursor_location)
        self.status_bar.addPermanentWidget(self.label_zoom)
        self.status_bar.addPermanentWidget(self.label_encoder)
        self.status_bar.showMessage("Ready", 5000)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)

        self.current_zoom_percentage = 100
        self._base_font_size = 12

        self.tabs.currentChanged.connect(self.sync_status_bar_with_tab)
        self.setCentralWidget(self.tabs)
        
        self.button_add_tab = QToolButton(self)
        self.button_add_tab.setToolTip("Open a new tab (Ctrl+N)")
        self.button_add_tab.setIconSize(QSize(16, 16))
        
        self.button_add_tab.setStyleSheet("""
            QToolButton {
                border: 1px solid rgba(128, 128, 128, 60);
                border-bottom: none; 
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                background-color: rgba(128, 128, 128, 20); 
                min-width: 28px;
                max-width: 28px;
                min-height: 24px;
                max-height: 24px;
                margin-top: 3px; 
                margin-right: 6px;
                margin-bottom: 2px;
                padding: 0px;
            }
            QToolButton:hover {
                background-color: rgba(128, 128, 128, 50);
                border-color: rgba(128, 128, 128, 100);
            }
            QToolButton:pressed {
                background-color: rgba(128, 128, 128, 80);
            }
        """)
        self.button_add_tab.clicked.connect(self.add_new_tab)
        self.tabs.setCornerWidget(self.button_add_tab, Qt.Corner.TopRightCorner)
        
        current_editor = self.get_current_editor()
        if current_editor:
            current_editor.cursorPositionChanged.connect(self.update_cursor_location)
            
            if name == 'nt':
                palette = current_editor.palette()
                palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Highlight, QColor("#0078d7"))
                palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
                palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Highlight, QColor("#0078d7"))
                palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
                current_editor.setPalette(palette)

        settings = QSettings(self.org_name, self.app_name)
        saved_geometry = settings.value("window_geometry")
        saved_state = settings.value("window_state")
        
        if saved_geometry is not None:
            self.restoreGeometry(saved_geometry)
        else:
            self.resize(900, 650)
            
        if saved_state is not None:
            self.restoreState(saved_state)

        saved_theme = settings.value("theme_mode", "system")

        fallback_default_font = QApplication.font()
        default_system_size = fallback_default_font.pointSize()
        if default_system_size <= 0:
            default_system_size = 12

        settings.beginGroup("FontSettings")
        self.saved_font_name = settings.value("font_name", "")
        self.saved_font_style = settings.value("font_style", "Regular")
        saved_size = settings.value("font_size", str(default_system_size))
        settings.endGroup()
        
        startup_font_size = default_system_size
        if str(saved_size).isdigit():
            startup_font_size = int(saved_size)
                
        if self.saved_font_name:
            startup_font = QFontDatabase.font(self.saved_font_name, self.saved_font_style, startup_font_size)
        else:
            startup_font = fallback_default_font
            startup_font.setPointSize(startup_font_size)

        if current_editor:
            current_editor.setFont(startup_font)
            
        self._base_font_size = startup_font_size
        self.current_zoom_percentage = 100

        # Actions initialization
        self.action_new = QAction("&New", self)
        self.action_new.setShortcut(QKeySequence.StandardKey.New)
        self.action_new.triggered.connect(self.new)

        self.action_newWindow = QAction("New &Window", self)
        self.action_newWindow.setShortcut("Ctrl+Shift+N")
        self.action_newWindow.triggered.connect(self.new_window)

        self.action_open = QAction("&Open...", self)
        self.action_open.setShortcut(QKeySequence.StandardKey.Open)
        self.action_open.triggered.connect(self.open_file)

        self.action_recover = QAction("Recover &Backup...", self)
        self.action_recover.triggered.connect(self.open_backup_directory)
        
        self.action_restore_session = QAction("Restore &Last Session", self)
        self.action_restore_session.triggered.connect(self.restore_last_session_logic)

        self.action_save = QAction("&Save", self)
        self.action_save.setShortcut(QKeySequence.StandardKey.Save)
        self.action_save.triggered.connect(self.save)

        self.action_saveAs = QAction("Save &As..", self)
        self.action_saveAs.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.action_saveAs.triggered.connect(self.saveAs)

        self.action_pageSetup = QAction("Page Set&up...", self)
        self.action_pageSetup.triggered.connect(self.pageSetup)

        self.action_print = QAction("&Print", self)
        self.action_print.setShortcut(QKeySequence.StandardKey.Print)
        self.action_print.triggered.connect(self.printing)

        self.action_exit = QAction("E&xit", self)
        self.action_exit.setShortcut("Ctrl+Q")
        self.action_exit.triggered.connect(self.exit_application)

        self.action_undo =QAction("&Undo", self)
        self.action_undo.setShortcut(QKeySequence.StandardKey.Undo)
        self.action_undo.triggered.connect(self.undoing)

        self.action_redo = QAction("R&edo", self)
        self.action_redo.setShortcut(QKeySequence.StandardKey.Redo)
        self.action_redo.triggered.connect(self.redoing)

        self.action_cut = QAction("Cu&t", self)
        self.action_cut.setShortcut(QKeySequence.StandardKey.Cut)
        self.action_cut.triggered.connect(self.cutting)

        self.action_copy = QAction("&Copy", self)
        self.action_copy.setShortcut(QKeySequence.StandardKey.Copy)
        self.action_copy.triggered.connect(self.copying)

        self.action_paste = QAction("&Paste", self)
        self.action_paste.setShortcut(QKeySequence.StandardKey.Paste)
        self.action_paste.triggered.connect(self.pasting)

        self.action_paste_plain = QAction("Paste as Plain Te&xt", self)
        self.action_paste_plain.setIcon(self.action_paste.icon())
        self.action_paste_plain.setShortcut("Ctrl+Shift+V")
        self.action_paste_plain.setStatusTip("Paste clipboard text without formatting")
        self.action_paste_plain.triggered.connect(self.paste_as_plain_text)

        self.action_delete = QAction("De&lete", self)
        self.action_delete.setShortcut(QKeySequence.StandardKey.Delete)
        self.action_delete.triggered.connect(self.deleting)
        
        self.action_convert_now = QAction("Invert &Keyboard Layout", self)
        self.action_convert_now.setShortcut("Ctrl+Shift+K")
        self.action_convert_now.triggered.connect(self.invert_text_layout)
        self.addAction(self.action_convert_now)

        self.action_layout_settings = QAction("Layout &Settings...", self)
        self.action_layout_settings.triggered.connect(self.show_layout_converter_settings_dialog)

        self.action_find = QAction("&Find...", self)
        self.action_find.setShortcut(QKeySequence.StandardKey.Find)
        self.action_find.triggered.connect(lambda: self.show_find_replace_dialog(0))
        
        self.action_replace = QAction("&Replace...", self)
        self.action_replace.setShortcut(QKeySequence.StandardKey.Replace)
        self.action_replace.triggered.connect(lambda: self.show_find_replace_dialog(1))
        
        self.action_goTo = QAction("&Go to line...", self)
        self.action_goTo.setShortcut("Ctrl+G")
        self.action_goTo.setEnabled(True)
        self.action_goTo.triggered.connect(self.goTo_dialog)

        self.action_selectAll = QAction("Select &All", self)
        self.action_selectAll.setShortcut(QKeySequence.StandardKey.SelectAll)
        self.action_selectAll.triggered.connect(self.select_all)
        
        self.action_timeDate = QAction("Time/&Date", self)
        self.action_timeDate.setShortcut("F5")
        self.action_timeDate.triggered.connect(self.date_time)

        self.action_wordWrap = QAction("&Word Wrap", self)
        self.action_wordWrap.setCheckable(True)
        self.action_wordWrap.setChecked(True)
        self.action_wordWrap.triggered.connect(self.word_wrap)

        self.action_font = QAction("&Font...", self)
        self.action_font.triggered.connect(self.font_dialog)

        self.action_statusBar = QAction("&Status Bar", self)
        self.action_statusBar.setCheckable(True)
        self.action_statusBar.setChecked(True)
        self.action_statusBar.triggered.connect(self.toggle_status_bar)

        self.action_line_numbers = QAction("&Line Number Bar", self)
        self.action_line_numbers.setCheckable(True)
        self.action_line_numbers.setChecked(False)
        self.action_line_numbers.triggered.connect(self.toggle_line_numbers_bar_visibility)
        
        self.action_zoomIn = QAction("Zoom &In", self)
        self.action_zoomIn.setShortcut(QKeySequence.StandardKey.ZoomIn)
        self.action_zoomIn.triggered.connect(self.zoom_in)
 
        self.action_zoomOut = QAction("Zoom &Out", self)
        self.action_zoomOut.setShortcut(QKeySequence.StandardKey.ZoomOut)
        self.action_zoomOut.triggered.connect(self.zoom_out)

        self.action_zoom_default = QAction("&Restore Default Zoom", self)
        self.action_zoom_default.setShortcut("Ctrl+0")
        self.action_zoom_default.triggered.connect(self.zoom_default)

        self.action_theme_light = QAction("&Light Mode", self)
        self.action_theme_light.setCheckable(True)
        self.action_theme_light.triggered.connect(lambda: self.theme_change("light"))

        self.action_theme_dark = QAction("&Dark Mode", self)
        self.action_theme_dark.setCheckable(True)
        self.action_theme_dark.triggered.connect(lambda: self.theme_change("dark"))

        self.action_theme_system = QAction("&System Theme", self)
        self.action_theme_system.setCheckable(True)
        self.action_theme_system.setChecked(True)
        self.action_theme_system.triggered.connect(lambda: self.theme_change("system"))
        
        self.action_about = QAction("&About", self)
        self.action_about.triggered.connect(self.about)

        self.action_aboutQt = QAction("About &Qt", self)
        self.action_aboutQt.triggered.connect(self.aboutQt)

        self.action_theme_group = QActionGroup(self)
        self.action_theme_group.addAction(self.action_theme_light)
        self.action_theme_group.addAction(self.action_theme_dark)
        self.action_theme_group.addAction(self.action_theme_system)
        self.action_theme_group.setExclusive(True)

        if saved_theme == "dark":
            self.action_theme_dark.setChecked(True)
        elif saved_theme == "light":
            self.action_theme_light.setChecked(True)
        else:
            self.action_theme_system.setChecked(True)
        
        # Menu Bar construction
        menubar = self.menuBar()
        menu_file = menubar.addMenu("&File")
        
        menu_file.addAction(self.action_new)
        menu_file.addAction(self.action_newWindow)
        menu_file.addAction(self.action_open)
        self.menu_recent = menu_file.addMenu("Open &Recent")
        self.MAX_RECENT_FILES = 5
        
        menu_file.addAction(self.action_restore_session)
        menu_file.addAction(self.action_recover)
        menu_file.addSeparator()
        
        menu_file.addAction(self.action_save)
        menu_file.addAction(self.action_saveAs)
        menu_file.addSeparator()

        menu_file.insertAction(self.action_exit, self.action_restore_session) 
        
        menu_file.addAction(self.action_pageSetup)
        menu_file.addAction(self.action_print)
        menu_file.addSeparator()
        
        menu_file.addAction(self.action_exit)

        menu_edit = menubar.addMenu("&Edit")
        menu_edit.addActions([self.action_undo, self.action_redo])
        menu_edit.addSeparator()
        menu_edit.addActions([self.action_cut, self.action_copy, self.action_paste,self.action_paste_plain ,self.action_delete])
        menu_edit.addSeparator()

        self.menu_convert_layout = menu_edit.addMenu("Con&vert Layout")
        self.menu_convert_layout.addAction(self.action_convert_now)
        self.menu_convert_layout.addAction(self.action_layout_settings)
        menu_edit.addSeparator()
        
        menu_edit.addActions([self.action_find, self.action_replace, self.action_goTo])
        menu_edit.addSeparator()
        menu_edit.addActions([self.action_selectAll, self.action_timeDate])

        menu_format = menubar.addMenu("F&ormat")
        menu_format.addActions([self.action_wordWrap, self.action_font])

        menu_view =menubar.addMenu("&View")
        menu_zoom = menu_view.addMenu("&Zoom")
        menu_zoom.addActions([self.action_zoomIn, self.action_zoomOut, self.action_zoom_default])
        menu_theme = menu_view.addMenu("&Theme")
        menu_theme.addActions([self.action_theme_light, self.action_theme_dark, self.action_theme_system])
        menu_view.addAction(self.action_statusBar)
        menu_view.addAction(self.action_line_numbers)

        menu_help = menubar.addMenu("&Help")
        menu_help.addAction(self.action_about)
        menu_help.addAction(self.action_aboutQt)

        self.update_recent_files_menu()

        # Toolbar setup
        toolbar = self.addToolBar("My ToolBar")
        toolbar.setFloatable(True)
        toolbar.setIconSize(QSize(32,32))
        
        self.button_new= toolbar.addAction(QIcon(":images/new-file.svg"), "")
        self.button_new.triggered.connect(self.new)
        self.button_new.setToolTip("Create a New document")

        self.button_open =toolbar.addAction(QIcon(":images/open.svg"), "")
        self.button_open.triggered.connect(self.open_file)
        self.button_open.setToolTip("Open a document")
        
        self.button_save =toolbar.addAction(QIcon(":images/save.svg"), "")
        self.button_save.triggered.connect(self.save)
        self.button_save.setToolTip("Save the document")
        
        self.button_saveAs = toolbar.addAction(QIcon(":images/saveAs.svg"), "")
        self.button_saveAs.triggered.connect(self.saveAs)
        self.button_saveAs.setToolTip("Save the document as a new file")

        self.button_print =toolbar.addAction(QIcon(":images/print.svg"), "")
        self.button_print.triggered.connect(self.printing)
        self.button_print.setToolTip("Print the document")

        toolbar.addSeparator()
        
        self.button_undo = toolbar.addAction(QIcon(":images/undo.svg"), "")
        self.button_undo.triggered.connect(self.undoing)
        self.button_undo.setToolTip("Undo the last action")
        
        self.button_redo =toolbar.addAction(QIcon(":images/redo.svg"), "")
        self.button_redo.triggered.connect(self.redoing)
        self.button_redo.setToolTip("Redo the last action")

        toolbar.addSeparator()
        
        self.button_copy =toolbar.addAction(QIcon(":images/copy.svg"), "")
        self.button_copy.triggered.connect(self.copying)
        self.button_copy.setToolTip("Copy the selected text")

        self.button_cut= toolbar.addAction(QIcon(":images/cut.svg"), "")
        self.button_cut.triggered.connect(self.cutting)
        self.button_cut.setToolTip("Cut the selected text")
        
        self.button_paste= toolbar.addAction(QIcon(":images/paste.svg"), "")
        self.button_paste.triggered.connect(self.pasting)
        self.button_paste.setToolTip("Paste the text from clipboard")

        toolbar.addSeparator()
        
        self.button_find= toolbar.addAction(QIcon(":images/find.svg"), "")
        self.button_find.triggered.connect(lambda: self.show_find_replace_dialog(0))
        self.button_find.setToolTip("Find text in the document")
        
        self.button_zoomIn= toolbar.addAction(QIcon(":images/zoomIn.svg"), "")
        self.button_zoomIn.triggered.connect(self.zoom_in)
        self.button_zoomIn.setToolTip("Zoom in the document")

        self.button_zoomOut= toolbar.addAction(QIcon(":images/zoomOut.svg"), "")
        self.button_zoomOut.triggered.connect(self.zoom_out)
        self.button_zoomOut.setToolTip("Zoom out the document")
        
        toolbar.addSeparator()
        
        self.button_about= toolbar.addAction(QIcon(":images/about.svg"), "")
        self.button_about.triggered.connect(self.about)
        self.button_about.setToolTip("About this application")
        
        self.button_exit= toolbar.addAction(QIcon(":images/close.svg"), "")
        self.button_exit.triggered.connect(self.exit_application)
        self.button_exit.setToolTip("Exit the application")

        self.add_new_tab()

        self.load_saved_line_numbers_preference()
        self.load_saved_interface_preferences()

        self.update_window_title()
        self.theme_change(saved_theme)

        self.setAcceptDrops(True)
        find_toolbar = self.findChild(QToolBar)
        if find_toolbar:
            find_toolbar.setObjectName("main_toolbar")

        self.backup_dir = path.join(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation), "Backups")
        if not path.exists(self.backup_dir):
            makedirs(self.backup_dir, exist_ok=True)

        self.registry = QSettings(self.org_name, self.app_name)
        
        self.registry.beginGroup("Vault")
        self._old_crypto_key = self.registry.value("ActiveToken", "")
        self._crypto_key = f"Session_{int(time.time())}"
        self.registry.setValue("ActiveToken", self._crypto_key)
        self.registry.endGroup()

        self.backup_timer = QTimer(self)
        self.backup_timer.timeout.connect(self.execute_auto_backup_logic)
        self.backup_timer.start(60000)

        settings_session = QSettings("Mattiya3D", "PySide6Notepad")
        saved_tabs = settings_session.value("Session/OpenedFiles", [])
        
        if saved_tabs is None:
            saved_tabs = []
        self.action_restore_session.setEnabled(len(saved_tabs) > 0)
        self.load_saved_line_numbers_preference()

    @property
    def text_edit(self):
        if hasattr(self, 'tabs') and self.tabs is not None:
            return self.tabs.currentWidget()
        return None

    def get_current_editor(self):
        if hasattr(self, 'tabs') and self.tabs is not None:
            return self.tabs.currentWidget()
        return None
    
    def change_icon_color(self, image_path):
        #Color calculations delegated completely to editor_utilities logic.#
        current_text_color = QGuiApplication.palette().color(QPalette.ColorRole.WindowText)
        return change_icon_color_logic(image_path, current_text_color)

    # ========================================================
    # CLEAN LOGICAL BACKEND BRIDGE LINKS (editor_utilities.py)
    # ========================================================

    def _encrypt_payload(self, text_content):
        return encrypt_payload(text_content)

    def _decrypt_payload(self, binary_payload):
        return decrypt_payload(binary_payload)

    def detect_line_endings_logic(self, file_content_raw):
        return detect_line_endings_logic(file_content_raw)

    def clean_individual_file_backup(self, file_path_or_tab_name):
        clean_individual_file_backup(file_path_or_tab_name, self.backup_dir)

    def execute_auto_backup_logic(self):
        if hasattr(self, 'tabs') and hasattr(self, 'backup_dir'):
            execute_auto_backup_logic(self.tabs, self.backup_dir)

    def update_text_lines_words_logic(self, *args):
        if args and isinstance(args[0], QWidget):
            editor = args[0]
        else:
            editor = self.get_current_editor()

        if not editor:
            self.label_lines_words.setText("Lines: 0, Words: 0, Spaces: 0")
            return

        total_lines, word_count, total_spaces = calculate_text_metrics(editor)
        self.label_lines_words.setText(f"Lines: {total_lines}, Words: {word_count}, Spaces: {total_spaces}")

    # ========================================================
    # MODULAR USER INTERFACE DIALOG BRIDGES (ui_dialogs.py)
    # ========================================================

    def show_find_replace_dialog(self, start_tab=0):
        active_editor = self.get_current_editor()
        if active_editor:
            dialog = FindReplaceDialog(self, active_editor, mode=start_tab)
            dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose) #Cleaning up the Memory
            dialog.show()

    def font_dialog(self):
        active_editor = self.get_current_editor()
        if active_editor:
            dialog = CustomFontDialog(self, active_editor.font())
            if dialog.exec() == QDialog.DialogCode.Accepted:
                f_name, f_style, f_size = dialog.get_chosen_font_metrics()
                self.update_text_edit_font(f_name, f_style, int(f_size))

    def update_text_edit_font(self, font_name=None, font_style=None, font_size=None):
        if font_name is None:
            font_name = self.saved_font_name
        if font_style is None:
            font_style = self.saved_font_style
        if font_size is None:
            font_size = self._base_font_size

        if isinstance(font_size, str) and font_size.isdigit():
            font_size_corrected = int(font_size)
        else:
            font_size_corrected = int(font_size) if isinstance(font_size, int) else 12

        text_edit_font = QFontDatabase.font(font_name, font_style, font_size_corrected)
        if self.text_edit:
            self.text_edit.setFont(text_edit_font)

        self.saved_font_name = font_name
        self.saved_font_style = font_style
        self._base_font_size = font_size_corrected
        
        settings = QSettings(self.org_name, self.app_name)
        settings.beginGroup("FontSettings")
        settings.setValue("font_name", font_name)
        settings.setValue("font_style", font_style)
        settings.setValue("font_size", str(font_size_corrected))
        settings.endGroup()

    def goTo_dialog(self):
        active_editor = self.get_current_editor()
        if active_editor:
            max_lines = active_editor.document().blockCount()
            dialog = GoToDialog(self, max_lines)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                cursor = active_editor.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.Start)
                for _ in range(dialog.target_line - 1):
                    cursor.movePosition(QTextCursor.MoveOperation.Down)
                active_editor.setTextCursor(cursor)

    def show_layout_converter_settings_dialog(self):
        dialog = LayoutSettingsDialog(self, self.org_name, self.app_name)
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        dialog.exec()

    # ========================================================
    # BASIC UTILITY EDIT OPERATIONS & FILE IO
    # ========================================================
    
    def is_it_saved(self):
        active_editor = self.get_current_editor()
        if not active_editor:
            return True

        has_no_path = not hasattr(active_editor, "file_path") or active_editor.file_path is None
        is_untitled_with_text = has_no_path and active_editor.toPlainText() != ""
        
        if active_editor.document().isModified() or is_untitled_with_text:
            msg = f"Do you want to save changes to\n{active_editor.file_path}?" if not has_no_path else "Do you want to save this Untitled document?"

            question_close = QMessageBox.question(
                self, "Save changes", msg,
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )
            
            if question_close == QMessageBox.StandardButton.Save:
                return self.save()
            elif question_close == QMessageBox.StandardButton.Discard:
                active_editor.document().setModified(False)
                return True
            return False
                
        return True
    
    def add_new_tab(self, file_path=None, content=""):
        editor = ZoomableTextEdit(self)
        editor.setPlainText(content)
        editor.file_path = file_path
        editor.tab_encoding = "UTF-8"
        
        editor.cursorPositionChanged.connect(self.update_cursor_location)
        editor.textChanged.connect(self.update_text_lines_words_logic)
        
        if hasattr(self, 'tabs') and self.tabs.count() > 0 and self.tabs.currentWidget():
            editor.setFont(self.tabs.currentWidget().font())
        else:
            if hasattr(self, 'saved_font_name') and self.saved_font_name:
                editor.setFont(QFontDatabase.font(self.saved_font_name, self.saved_font_style, self._base_font_size))
            else:
                editor.setFont(QApplication.font())
                
            if hasattr(self, '_base_font_size'):
                f = editor.font()
                f.setPointSize(self._base_font_size)
                editor.setFont(f)
            
        tab_title = path.basename(file_path) if file_path else "Untitled"
        index = self.tabs.addTab(editor, tab_title)
        self.tabs.setCurrentIndex(index)

        self.handle_modification(editor, editor.document().isModified())
        editor.document().modificationChanged.connect(lambda modified, ed=editor: self.handle_modification(ed, modified))
        
        apply_highlighter_to_editor(editor, file_path, self.current_theme)
        
        self.update_window_title()
        editor.set_line_numbers_visible(self.action_line_numbers.isChecked())
        return editor
    
    def new(self):
        self.add_new_tab()
        self.status_bar.showMessage("New document created in a new tab", 3000)

    def handle_modification(self, editor, modified):
        index = self.tabs.indexOf(editor)
        if index != -1:
            base_name = path.basename(editor.file_path) if editor.file_path else "Untitled"
            ro_label = ""
            if editor.file_path and path.exists(editor.file_path) and not access(editor.file_path, W_OK):
                ro_label = " (Read Only)"
                
            title = f"{base_name}*{ro_label}" if modified else f"{base_name}{ro_label}"
            self.tabs.setTabText(index, title)
        self.update_window_title()

    def new_window(self):
        self.another_new_window = MainWindow()
        self.another_new_window.show()
        self.status_bar.showMessage("New window opened successfully", 3000)

    def update_window_title(self):
        active_editor = self.text_edit
        if active_editor:
            file_name = path.basename(active_editor.file_path) if active_editor.file_path else "Untitled"
            asterisk = "*" if active_editor.document().isModified() else ""
            ro_label = ""
            if hasattr(active_editor, "file_path") and active_editor.file_path and path.exists(active_editor.file_path):
                if not access(active_editor.file_path, W_OK):
                    ro_label = " (Read Only)"
            
            self.setWindowTitle(f"{file_name}{asterisk}{ro_label} - PySide6 Notepad")
        else:
            self.setWindowTitle("PySide6 Notepad")
    
    def close_tab(self, index):
        # Safely closes a tab after checking for unsaved changes.
        editor = self.tabs.widget(index)
        if not editor:
            return
        
        # Temporarily switch focus to the tab being closed so the save dialog can evaluate it
        self.tabs.setCurrentIndex(index)
        
        if self.is_it_saved():
            self.tabs.removeTab(index)
            # If no tabs are left open, refresh the title back to default application name
            if self.tabs.count() == 0:
                self.update_window_title()

    def update_recent_files_menu(self):
        #Dynamically clears and repopulates the Open Recent sub-menu with tracked file paths.#
        self.menu_recent.clear()
        
        settings = QSettings(self.org_name, self.app_name)
        recent_files = settings.value("recent_files_list", [])
        
        if not recent_files:
            # Show a clean disabled placeholder if history is completely empty
            no_recent_action = self.menu_recent.addAction("No Recent Files")
            no_recent_action.setDisabled(True)
            return
            
        # Build individual actions for each file path stored in settings
        for index, file_path in enumerate(recent_files):
            if path.exists(file_path):
                # Format text with index (e.g., &1. filename.txt) for clear layout visibility
                action_text = f"&{index + 1}. {path.basename(file_path)}"
                action = self.menu_recent.addAction(action_text)
                
                # Attach the raw absolute path string directly into the action data field
                action.setData(file_path)
                action.triggered.connect(self.open_recent_file_logic)

    def add_to_recent_files(self, file_path):
        #Appends a valid file path to the history list on disk, capped at the max limit.#
        if not file_path:
            return
            
        settings = QSettings(self.org_name, self.app_name)
        recent_files = settings.value("recent_files_list", [])
        
        # Force cast to a real Python list if QSettings returns a stray string on fresh Linux environments
        if isinstance(recent_files, str):
            recent_files = [recent_files] if recent_files else []
        elif recent_files is None:
            recent_files = []
        else:
            recent_files = list(recent_files) # Ensure it's a mutable list
        
        # Remove the file path if it already exists to avoid duplicates and bring it to the top Safely
        if file_path in recent_files:
            recent_files.remove(file_path)
            
        # Insert the fresh file path at the very beginning of the list
        recent_files.insert(0, file_path)
        
        # Enforce maximum boundary constraints
        if len(recent_files) > self.MAX_RECENT_FILES:
            recent_files = recent_files[:self.MAX_RECENT_FILES]
            
        settings.setValue("recent_files_list", recent_files)
        
        # Instant UI synchronization to display updated list
        self.update_recent_files_menu()

    def open_recent_file_logic(self):
        #Triggered directly by recent menu actions. Loads the selected file with proper encoding and line ending metrics.#
        action = self.sender()
        if not action:
            return
            
        chosen_path = action.data()
        if path.exists(chosen_path):
            try:
                # Default platform-standard line ending fallback layout
                line_ending = "CRLF" if name == 'nt' else "LF"
                
                # Read raw bytes into a defined chunk variable to predict encoding and capture line endings cleanly
                with open(chosen_path, "rb") as raw_file:
                    raw_data = raw_file.read(1000)
                    
                    if b'\r\n' in raw_data:
                        line_ending = "CRLF"
                    elif b'\n' in raw_data:
                        line_ending = "LF"
                        
                    predict_encoding = chardet.detect(raw_data)
                    python_encoding = predict_encoding['encoding'] or "utf-8"
                    
                with open(chosen_path, "r", encoding=python_encoding, errors="ignore") as file:
                    file_content = file.read()
                    
                current_editor = self.get_current_editor()
                
                # Smart Document Tab Reuse checks: If the active tab is completely empty, reuse it
                if current_editor and not current_editor.file_path and current_editor.toPlainText() == "":
                    current_editor.setPlainText(file_content)
                    current_editor.file_path = chosen_path
                    index = self.tabs.currentIndex()
                    self.tabs.setTabText(index, path.basename(chosen_path))
                    current_editor.document().setModified(False)
                else:
                    # Otherwise, allocate a fresh new tab layout context cleanly
                    self.add_new_tab(file_path=chosen_path, content=file_content)
                    
                # Synchronize structural text layout tracking string properties straight to the editor instance
                display_string = f"{python_encoding.upper()} | {line_ending}"
                self.get_current_editor().tab_encoding = display_string
                
                # Refresh layout indicators, status bar matrix counts, and window titles instantly
                self.add_to_recent_files(chosen_path)
                self.update_window_title()

                #Pass the re-fetched active editor immediately
                self.update_text_lines_words_logic(self.get_current_editor())
                
                self.status_bar.showMessage(f"Opened Recent: {chosen_path}", 3000)
                
            except Exception as e:
                QMessageBox.critical(self, "Error Opening Recent File", f"Could not read file.\nError: {str(e)}")
        else:
            self.status_bar.showMessage("The selected file no longer exists on disk", 4000)

    def open_file(self):
        #Opens an existing file from disk into the ideal tab safely.
        #Detects encoding and line endings, and applies simplified filter 
        #patterns to ensure full compatibility with both KDE and Ubuntu (GTK).
                
        # Simplified and GTK-compatible filter patterns to prevent Ubuntu's dialogue from freezing
        filters = [
            "All Supported Formats (*.py *.cpp *.c *.h *.cs *.java *.js *.ts *.php *.html *.css *.sql *.json *.xml *.yaml *.ini *.sh *.txt)",
            "Text Files (*.txt)",
            "Python Files (*.py)",
            "Web Files (*.html *.css *.js *.ts *.php)",
            "Code Files (*.cpp *.c *.h *.cs *.java *.sh)",
            "Data/Config Files (*.json *.xml *.yaml *.ini)",
            "All Files (*)"  # Fallback option, must be last
        ]
        
        file_filter = ";;".join(filters)
        
        # Determine the starting directory (fallback to Home directory if no file was opened yet)
        start_dir = self.last_opened_directory if self.last_opened_directory else str(QStandardPaths.writableLocation(QStandardPaths.HomeLocation))
        
        # Trigger the native file dialogue
        file_path, selected_filter = QFileDialog.getOpenFileName(
            self, 
            "Open File", 
            start_dir, 
            file_filter
        )
        
        if file_path:
            try:
                #  Save the parent directory path of the selected file for the next File I/O call
                self.last_opened_directory = path.dirname(file_path)

                # Proactive check: Decrypt on-the-fly if opening a backup file
                _, ext = path.splitext(file_path)
                if ext.lower() == ".pynp" or path.basename(file_path).startswith("RECOVERY_"):
                    with open(file_path, "rb") as f:
                        raw_bytes = f.read()
                    file_content = decrypt_payload(raw_bytes)
                    python_encoding = "UTF-8"
                    line_ending = "LF" if "\n" in file_content and "\r\n" not in file_content else "CRLF"
                else:
                    # Standard decoding logic for normal text/code documents
                    file_content, python_encoding, line_ending = open_and_decode_file_logic(file_path)

                # Grab current editor reference
                current_editor = self.get_current_editor()

                # Handle Empty Editor reuse to keep UI clean
                if current_editor and not current_editor.file_path and current_editor.toPlainText() == "":
                    current_editor.setPlainText(file_content)
                    current_editor.file_path = file_path
                    index = self.tabs.currentIndex()
                    self.tabs.setTabText(index, path.basename(file_path))
                    current_editor.document().setModified(False)
                else:
                    current_editor = self.add_new_tab(file_path=file_path, content=file_content)

                # Sync encoding interface tracking labels
                display_string = f"{python_encoding.upper()} | {line_ending}"
                self.label_encoder.setText(display_string)
                current_editor.tab_encoding = display_string

                self.add_to_recent_files(file_path)
                self.update_window_title()
                self.update_text_lines_words_logic(current_editor)
                
                # Apply structural syntax highlighters through utility module
                apply_highlighter_to_editor(current_editor, file_path, self.current_theme)

                self.status_bar.showMessage(f"Opened: {file_path} Successfully", 3000)

            except Exception as e:
                QMessageBox.critical(self, "Error Opening File", f"Could not read file.\nError: {str(e)}")
    
    def open_file_from_cli_path(self, file_path):
        #Programmatically loads a validated file path into the workspace at boot time.#
        
        try:
            file_content, python_encoding, line_ending = open_and_decode_file_logic(file_path) #
            current_editor = self.get_current_editor() #
            
            if current_editor and not current_editor.file_path and current_editor.toPlainText() == "":
                current_editor.setPlainText(file_content)
                current_editor.file_path = file_path
                self.tabs.setTabText(self.tabs.currentIndex(), path.basename(file_path))
                current_editor.document().setModified(False)
            else:
                current_editor = self.add_new_tab(file_path=file_path, content=file_content) #

            display_string = f"{python_encoding.upper()} | {line_ending}"
            self.label_encoder.setText(display_string)
            current_editor.tab_encoding = display_string
            
            self.add_to_recent_files(file_path)
            self.update_window_title()
            apply_highlighter_to_editor(current_editor, file_path, self.current_theme) #
        except Exception as e:
            print(f"CLI Boot Error: Could not read target path execution payload. Raw: {str(e)}")

    def save(self):
        #Saves the plain text content of the active tab strictly to its mapped file path using robust encoding logic.#
        active_editor = self.get_current_editor()
        if not active_editor:
            return False
        
        # BLENDER-STYLE PROTECTION: Enforce 'Save As' if the file path is a temporary backup
        if active_editor.file_path and path.basename(active_editor.file_path).startswith("RECOVERY_") and active_editor.file_path.endswith(".pynp"):
            QMessageBox.warning(
                self, 
                "Protected Backup File", 
                "This is an auto-saved recovery file. You cannot overwrite it directly.\n\nPlease choose a different location to save your clean copy."
            )
            self.saveAs()
            return True

        if not hasattr(active_editor, "file_path") or active_editor.file_path is None:
            my_documents = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
            default_path = path.join(my_documents, "Untitled.txt")
            file_filters = "Plain Text (*.txt);;HTML (*.html);;Markdown (*.md);;All Files (*.*)"
            file_path, _ = QFileDialog.getSaveFileName(self, "Save File", default_path, file_filters)
        
            if file_path:
                active_editor.file_path = file_path
                index = self.tabs.currentIndex()
                self.tabs.setTabText(index, path.basename(file_path))
                
                # Apply Highlighter instantly
                _, ext = path.splitext(file_path)
                active_editor.highlighter = CodeHighlighter(active_editor.document())
                is_dark_now = (self.current_theme == "dark" or (self.current_theme == "system" and QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark))
                active_editor.highlighter.set_theme_mode(is_dark_now)
                active_editor.highlighter.set_active_extension(ext)
            else:
                return False
            
        if path.exists(active_editor.file_path) and not access(active_editor.file_path, W_OK):
            QMessageBox.warning(
                self, "Read-Only File",
                f"The file:\n{active_editor.file_path}\nis marked as Read-Only.\n\nPlease use 'Save As' to save changes with a new name.",
                QMessageBox.StandardButton.Ok
            )
            return self.saveAs()
            
        try:
            content = active_editor.toPlainText()
            # Determine current active encoding/line_ending properties or default them
            current_encoding = getattr(active_editor, "tab_encoding", "UTF-8").split(" | ")[0]
            current_line_ending = "CRLF" if "CRLF" in getattr(active_editor, "tab_encoding", "") else "LF"
            
            # Delegate file saving & encoding logic to utility module
            resolved_encoding = save_and_encode_file_logic(active_editor.file_path, content, current_encoding, current_line_ending)
            
            active_editor.document().setModified(False)
            self.label_encoder.setText(f"{resolved_encoding.upper()} | {current_line_ending}")
            
            # Housekeeping backup removal
            self.clean_individual_file_backup(active_editor.file_path)

            self.add_to_recent_files(active_editor.file_path)
            self.update_window_title()
            self.status_bar.showMessage("Document saved successfully", 3000)
            return True
        
        except Exception as e:
            QMessageBox.critical(self, "Error Saving File", f"Could not save file.\nError: {str(e)}")
            return False

    def saveAs(self):
        active_editor = self.get_current_editor()
        if not active_editor:
            return False

        my_documents = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
        default_path = path.join(my_documents, "Untitled")
        file_filters = "Plain Text (*.txt);;HTML (*.html);;Markdown (*.md);;All Files (*.*)"
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", default_path, file_filters)

        if file_path:
            if path.exists(file_path) and not access(file_path, W_OK):
                QMessageBox.warning(
                    self, "Read-Only File",
                    f"The target file:\n{file_path}\nis marked as Read-Only.\n\nYou cannot overwrite it.",
                    QMessageBox.StandardButton.Ok
                )
                return False

            active_editor.file_path = file_path
            index = self.tabs.currentIndex()
            self.tabs.setTabText(index, path.basename(file_path))
            
            _, ext = path.splitext(file_path)
            if hasattr(active_editor, 'highlighter') and active_editor.highlighter:
                active_editor.highlighter.set_active_extension(ext)
                is_dark_now = (self.current_theme == "dark" or (self.current_theme == "system" and QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark))
                active_editor.highlighter.set_theme_mode(is_dark_now)

            active_editor.highlighter.set_active_extension(ext)
            return self.save()
            
        return False

    def update_recent_files_list(self):
        self.update_recent_files_menu()

    def pageSetup(self):
        pageSetup_dialog = QPageSetupDialog(self.printer, self)
        if pageSetup_dialog.exec():
            self.status_bar.showMessage("Page setup updated", 3000)

    def printing(self):
        print_dialog = QPrintDialog(self.printer, self)
        if print_dialog.exec():
            self.text_edit.print_(self.printer)
            self.status_bar.showMessage("Printing completed or sent to printer", 3000)
        else:
            self.status_bar.showMessage("Printing canceled", 3000)

    def undoing(self):
        if self.text_edit:
            self.text_edit.undo()

    def redoing(self):
        if self.text_edit:
            self.text_edit.redo()

    def copying(self):
        if self.text_edit:
            self.text_edit.copy()

    def cutting(self):
        if self.text_edit:
            self.text_edit.cut()

    def pasting(self):
        if self.text_edit:
            self.text_edit.paste()

    def deleting(self):
        if self.text_edit:
            remove_highlighted = self.text_edit.textCursor()
            remove_highlighted.deleteChar()

    def select_all(self):
        #Selects all text in the active editor.#
        if self.text_edit:
            self.text_edit.selectAll()

    def word_wrap(self):
        #Toggles word wrap mode on the active text edit.#
        if self.text_edit:
            if self.action_wordWrap.isChecked():
                self.text_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
                self.action_goTo.setEnabled(False)
            else:
                self.text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
                self.action_goTo.setEnabled(True)
        
        settings = QSettings(self.org_name, self.app_name)
        settings.setValue("word_wrap_enabled", self.action_wordWrap.isChecked())

    def paste_as_plain_text(self):
        #Retrieves clipboard contents as pure unformatted text and inserts it safely.#
        clipboard = QApplication.clipboard()
        plain_text = clipboard.text()
        if self.text_edit:
            self.text_edit.insertPlainText(plain_text)

    def date_time(self):
        #Inserts the current system date and time at the current cursor position.#
        now = QDateTime.currentDateTime()
        date_time_format = now.toString("hh:mm:ss AP dddd, MMMM d, yyyy")
        if self.text_edit:
            self.text_edit.insertPlainText(date_time_format)

    def find_window_logic(self):
        #Repeats the last active search term using stored global search parameters.#
        editor = self.get_current_editor()
        if not editor or not hasattr(self, 'last_search_term') or not self.last_search_term:
            return

        flags = self.last_search_flags
        sender = self.sender()
        if sender == self.action_findPrevious:
            flags |= QTextDocument.FindFlag.FindBackward
        elif sender == self.action_findNext:
            flags &= ~QTextDocument.FindFlag.FindBackward

        found = editor.find(self.last_search_term, flags)
        if not found:
            # Wrap around logic fallback
            cursor = editor.textCursor()
            if sender == self.action_findPrevious:
                cursor.movePosition(QTextCursor.MoveOperation.End)
            else:
                cursor.movePosition(QTextCursor.MoveOperation.Start)
            editor.setTextCursor(cursor)
            found = editor.find(self.last_search_term, flags)

        if found:
            editor.setFocus()
        else:
            self.status_bar.showMessage("Text not found", 3000)

    def finding_next(self):
        #Checks if there's an active search term and enables the Find Next menu item.#
        has_text = bool(self.last_search_term)
        self.action_findNext.setEnabled(has_text)

    def finding_previous(self):
        #Triggers the find previous repeat logic safely.#
        self.find_window_logic()

    def zoom_in(self):
        active_editor = self.get_current_editor()
        if not active_editor:
            return
            
        if not hasattr(active_editor, 'tab_zoom_percentage'):
            active_editor.tab_zoom_percentage = 100
            
        if active_editor.tab_zoom_percentage >= 500:
            self.status_bar.showMessage("You can't zoom more than 500%", 3000)
            return
            
        active_editor.tab_zoom_percentage += 10
        active_editor.zoomIn(1)
        self.label_zoom.setText(f"{active_editor.tab_zoom_percentage}%")

    def zoom_out(self):
        active_editor = self.get_current_editor()
        if not active_editor:
            return
            
        if not hasattr(active_editor, 'tab_zoom_percentage'):
            active_editor.tab_zoom_percentage = 100
            
        if active_editor.tab_zoom_percentage <= 10:
            self.status_bar.showMessage("You can't zoom less than 10%", 3000)
            return
            
        active_editor.tab_zoom_percentage -= 10
        active_editor.zoomOut(1)
        self.label_zoom.setText(f"{active_editor.tab_zoom_percentage}%")

    def zoom_default(self):
        active_editor = self.get_current_editor()
        if not active_editor:
            return
            
        active_editor.tab_zoom_percentage = 100
        font = active_editor.font()
        if hasattr(self, '_base_font_size'):
            font.setPointSize(self._base_font_size)
            active_editor.setFont(font)
        self.label_zoom.setText("100%")

    def theme_change(self, theme_type):
        self.current_theme = theme_type
        
        # Call in the new manager to do all the hard work instead of MainWindow
        ThemeManager.apply_theme(theme_type, self.tabs, self.status_bar)

        # Save user preferences as usual
        settings = QSettings(self.org_name, self.app_name)
        settings.setValue("theme_mode", theme_type)

        # Icons updated to match the new brightness
        self.update_all_toolbar_icons()
        
    def _on_os_theme_changed(self, scheme):
        if self.current_theme == "system":
            # Automatically update colors when changing the Windows/Linux system theme
            ThemeManager.apply_theme("system", self.tabs)
            self.update_all_toolbar_icons()

    def sync_status_bar_with_tab(self, index):
        self.update_window_title()
        active_editor = self.get_current_editor()
        if not active_editor:
            return

        cursor = active_editor.textCursor()
        line = cursor.blockNumber() + 1
        column = cursor.columnNumber() + 1
        self.label_cursor_location.setText(f"Ln {line}, Col {column}")
        
        if hasattr(active_editor, 'tab_zoom_percentage'):
            self.label_zoom.setText(f"{active_editor.tab_zoom_percentage}%")
        else:
            active_editor.tab_zoom_percentage = 100
            self.label_zoom.setText("100%")
            
        if hasattr(self, 'label_encoder'):
            current_encoding = getattr(active_editor, 'tab_encoding', "UTF-8")
            self.label_encoder.setText(current_encoding)

        self.update_text_lines_words_logic()

    def update_all_toolbar_icons(self):
        self.button_new.setIcon(self.change_icon_color(":images/new-file.svg"))
        self.button_open.setIcon(self.change_icon_color(":images/open.svg"))
        self.button_save.setIcon(self.change_icon_color(":images/save.svg"))
        self.button_saveAs.setIcon(self.change_icon_color(":images/saveAs.svg"))
        self.button_print.setIcon(self.change_icon_color(":images/print.svg"))
        self.button_undo.setIcon(self.change_icon_color(":images/undo.svg"))
        self.button_redo.setIcon(self.change_icon_color(":images/redo.svg"))
        self.button_copy.setIcon(self.change_icon_color(":images/copy.svg"))
        self.button_cut.setIcon(self.change_icon_color(":images/cut.svg"))
        self.button_paste.setIcon(self.change_icon_color(":images/paste.svg"))
        self.button_find.setIcon(self.change_icon_color(":images/find.svg"))
        self.button_zoomIn.setIcon(self.change_icon_color(":images/zoomIn.svg"))
        self.button_zoomOut.setIcon(self.change_icon_color(":images/zoomOut.svg"))
        self.button_about.setIcon(self.change_icon_color(":images/about.svg"))
        self.button_exit.setIcon(self.change_icon_color(":images/close.svg"))

        if hasattr(self, 'button_add_tab') and self.button_add_tab is not None:
            self.button_add_tab.setIcon(self.change_icon_color(":images/addTab.svg"))

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()

            for url in event.mimeData().urls():
                local_file_path = url.toLocalFile()
                
                if path.isfile(local_file_path):
                    try:
                        # 1. Read raw data first as bytes (Binary Data)
                        with open(local_file_path, "rb") as f:
                            raw_bytes = f.read()
                        
                        # 2. Smart Check: Is this file an encrypted backup of the application?
                        _, ext = path.splitext(local_file_path)
                        if ext.lower() == ".pynp" or path.basename(local_file_path).startswith("RECOVERY_"):
                            # Decrypting Base64 byte content into readable text
                            file_content = decrypt_payload(raw_bytes)
                            python_encoding = "UTF-8"
                            line_ending = "LF" if "\n" in file_content and "\r\n" not in file_content else "CRLF"
                        else:
                            # If it is a regular file (program or text), we use the traditional intelligent read and decode logic beforehand.
                            file_content, python_encoding, line_ending = open_and_decode_file_logic(local_file_path)
                        
                        # 3. Create the new tab and inject clean text into it
                        editor = self.add_new_tab(local_file_path, file_content)
                        
                        # 4. Enable code colorization based on the actual extension of the editor
                        apply_highlighter_to_editor(editor, local_file_path, self.current_theme)
                        
                        setattr(editor, 'tab_encoding', f"{python_encoding.upper()} | {line_ending}")
                        editor.document().setModified(False)
                        
                        self.update_window_title()
                        if hasattr(self, 'label_encoder'):
                            self.label_encoder.setText(f"{python_encoding.upper()} | {line_ending}")
                            
                    except Exception as e:
                        QMessageBox.critical(self, "Error Loading File", f"Could not parse or open the dropped file:\n{str(e)}")
        else:
            event.ignore()

    def closeEvent(self, event):
        for index in range(self.tabs.count() - 1, -1, -1):
            self.tabs.setCurrentIndex(index)
            editor = self.tabs.widget(index)
            
            if editor and editor.document().isModified():
                res = QMessageBox.question(
                    self, "Unsaved Changes",
                    f"The file '{self.tabs.tabText(index)}' has been modified.\nDo you want to save changes?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
                )
                
                if res == QMessageBox.StandardButton.Yes:
                    self.save()
                elif res == QMessageBox.StandardButton.Cancel:
                    event.ignore()
                    return

        try:
            if hasattr(self, 'registry'):
                self.registry.beginGroup("Vault")
                self.registry.remove("ActiveToken")
                self.registry.endGroup()
                
            if path.exists(self.backup_dir):
                for filename in listdir(self.backup_dir):
                    if filename.startswith("RECOVERY_") and filename.endswith(".pynp"):
                        remove(path.join(self.backup_dir, filename))
        except (IOError, PermissionError) as e:
            logging.error(f"Failed to process file backup: {e}")

        settings = QSettings(self.org_name, self.app_name)
        settings.setValue("window_geometry", self.saveGeometry())
        settings.setValue("window_state", self.saveState())

        opened_files = []
        try:
            for index in range(self.tabs.count()):
                editor = self.tabs.widget(index)
                if editor and hasattr(editor, 'file_path') and editor.file_path and path.exists(editor.file_path):
                    opened_files.append(editor.file_path)
            
            settings.beginGroup("Session")
            settings.setValue("OpenedFiles", opened_files)
            settings.endGroup()
        except (IOError, PermissionError) as e:
            logging.error(f"Failed to process file backup: {e}")
        
        event.accept()

    def exit_application(self):
        self.close()

    def update_cursor_location(self):
        if self.text_edit:
            cursor = self.text_edit.textCursor()
            line = cursor.blockNumber() + 1
            column = cursor.columnNumber() + 1
            self.label_cursor_location.setText(f"Ln {line}, Col {column}")

    def toggle_status_bar(self, visible):
        if visible:
            self.status_bar.show()
        else:
            self.status_bar.hide()
        settings = QSettings(self.org_name, self.app_name)
        settings.setValue("status_bar_visible", visible)

    def about(self):
        about_text = (
            "<h2 style='color: #41bf59; margin-bottom: 5px;'>PySide6 Notepad</h2>"
            "<p style='font-size: 13px; margin-top: 0;'>Version 1.0</p>"
            "<hr>"
            "<p style='font-size: 14px; line-height: 1.5;'>"
            "This application was made by:<br>"
            "<b>Muhammad Attiya (mattiya3d)</b>"
            "</p>"
            "<p style='font-size: 14px; line-height: 1.5;'>"
            "Built with 🐍 <b>Python</b> and 💻 <b>PySide6</b>.<br>"
            "Check out my portfolio and my other projects here:<br>"
            "<a style='color: #3498db; text-decoration: none;' href='https://github.com/mattiya3d'> github.com/mattiya3d</a>"
            "</p>"
        )
        QMessageBox.about(self, "About PySide6 Notepad", about_text) 

    def aboutQt(self):
        QMessageBox.aboutQt(self)

    def open_backup_directory(self):
        if path.exists(self.backup_dir):
            files = [f for f in listdir(self.backup_dir) if f.startswith("RECOVERY_") and f.endswith(".pynp")]
            if not files:
                QMessageBox.information(self, "Recover Backup", "Your recovery vault is empty. No backup files found!")
                return
                
            folder_url = QUrl.fromLocalFile(self.backup_dir)
            QDesktopServices.openUrl(folder_url)
        else:
            QMessageBox.warning(self, "Error", "Backup directory layout is unreachable.")

    def restore_last_session_logic(self):
        settings_session = QSettings(self.org_name, self.app_name)
        settings_session.beginGroup("Session")
        saved_tabs = settings_session.value("OpenedFiles", [])
        settings_session.endGroup()

        if not saved_tabs:
            QMessageBox.information(self, "Restore Session", "No previous session layout was discovered! 😊")
            return

        opened_count = 0
        for file_path in saved_tabs:
            if path.exists(file_path):
                already_open = False
                for index in range(self.tabs.count()):
                    editor = self.tabs.widget(index)
                    if editor and hasattr(editor, 'file_path') and editor.file_path == file_path:
                        already_open = True
                        break
                
                if already_open:
                    continue

                try:
                    file_content, python_encoding, line_ending = open_and_decode_file_logic(file_path)

                    editor = self.add_new_tab(file_path=file_path, content=file_content)
                    
                    display_string = f"{python_encoding.upper()} | {line_ending}"
                    editor.tab_encoding = display_string
                    editor.document().setModified(False)
                    opened_count += 1

                except (IOError, PermissionError) as e:
                    logging.error(f"Failed to process file backup: {e}")
        
        if opened_count > 0:
            self.action_restore_session.setEnabled(False)
            self.update_text_lines_words_logic(self.get_current_editor())
            self.status_bar.showMessage(f"Restored {opened_count} tabs from your last session!", 4000)
        else:
            QMessageBox.warning(self, "Restore Session", "Could not restore any files. They might have been moved or deleted.")

        self.sync_status_bar_with_tab(self.tabs.currentIndex())

        QApplication.processEvents()
        if self.get_current_editor():
            self.get_current_editor().update_line_number_area_width()


    def toggle_line_numbers_bar_visibility(self, visible):
        for i in range(self.tabs.count()):
            editor = self.tabs.widget(i)
            if editor and hasattr(editor, 'set_line_numbers_visible'):
                editor.set_line_numbers_visible(visible)
                
        settings = QSettings(self.org_name, self.app_name)
        settings.setValue("show_line_numbers", visible)

    def load_saved_line_numbers_preference(self):
        settings = QSettings(self.org_name, self.app_name)
        saved_state = settings.value("show_line_numbers", "false")
        
        is_checked = (str(saved_state).lower() == 'true')
        self.action_line_numbers.setChecked(is_checked)
        self.toggle_line_numbers_bar_visibility(is_checked)
    
    def load_saved_interface_preferences(self):
        settings = QSettings(self.org_name, self.app_name)
        
        saved_wrap = settings.value("word_wrap_enabled", "true")
        is_wrap_checked = (str(saved_wrap).lower() == 'true')
        self.action_wordWrap.setChecked(is_wrap_checked)
        self.word_wrap()
        
        saved_status = settings.value("status_bar_visible", "true")
        is_status_visible = (str(saved_status).lower() == 'true')
        self.action_statusBar.setChecked(is_status_visible)
        self.toggle_status_bar(is_status_visible)

    def invert_text_layout(self):
        cursor = self.text_edit.textCursor()
        if not cursor.hasSelection():
            return
            
        selected_text = cursor.selectedText()
        new_text = convert_string_layout(selected_text, org_name=self.org_name, app_name=self.app_name)
        cursor.insertText(new_text)
