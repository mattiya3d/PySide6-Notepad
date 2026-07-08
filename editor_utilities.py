import base64
from chardet.universaldetector import UniversalDetector
from os import path, name, listdir, remove
import json
import re
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QRegularExpression
from PySide6.QtGui import QColor, QTextCharFormat, QFont, QGuiApplication, QPixmap, QPainter, QIcon, QSyntaxHighlighter

# ========================================================
# 1. PROFESSIONAL SYNTAX HIGHLIGHTER CLASS (Outsourced)
# ========================================================
class CodeHighlighter(QSyntaxHighlighter):
    # A professional, scalable custom syntax highlighter for 15+ programming languages.
    # Uses 'Lazy Evaluation' logic to apply styling rules based on the active file type.
    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_extension = "txt"
        self.styling_rules = []
        self.is_dark_mode = (QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark)
        self.refresh_palette()

    def set_theme_mode(self, is_dark):
        #Dynamically switches palette between light and dark modes and triggers redraw.#
        self.is_dark_mode = is_dark
        self.refresh_palette()      # Update Color tones
        self.load_language_rules()  # Rebuilding new colors' rules
        self.rehighlight()          # Forcing PySide6 to recolor the text

    def refresh_palette(self):
        #Defines two independent contrast-aware palettes for Dark and Light modes.#
        if self.is_dark_mode:
            # Dark Mode: Bright, pastel-ish colors that pop on dark/grey backgrounds
            self.color_keyword = QColor("#569CD6")   # Light Soft Blue
            self.color_builtin = QColor("#4EC9B0")   # Light Mint Teal
            self.color_string = QColor("#CE9178")    # Soft Salmon/Orange-Red
            self.color_comment = QColor("#6A9955")   # Muted Sage Green
            self.color_number = QColor("#B5CEA8")    # Pale Lime Green
            self.color_function = QColor("#DCDCAA")  # Warm Soft Yellow
            self.color_operator = QColor("#D4D4D4")  # Light Grey
            self.color_self = QColor("#C586C0")      # Soft Magenta/Pink
        else:
            # Light Mode: Deep, saturated, darker colors that contrast perfectly on white
            self.color_keyword = QColor("#0000FF")   # Deep Classic Blue
            self.color_builtin = QColor("#008080")   # Dark Corporate Teal
            self.color_string = QColor("#A31515")    # Deep Crimson Red
            self.color_comment = QColor("#008000")   # Forest Green
            self.color_number = QColor("#098658")    # Deep Olive Green
            self.color_function = QColor("#795CB2")  # Deep Royal Purple
            self.color_operator = QColor("#333333")  # Charcoal Dark Grey
            self.color_self = QColor("#A52A2A")      # Brown/Auburn

    def set_active_extension(self, ext):
        #Sets the current file extension and dynamically loads the matching rules.#
        self.file_extension = ext.lower().strip(".")
        self.load_language_rules()
        self.rehighlight()

    def load_language_rules(self):
        #Compiles regex patterns based on the active language extension.#
        self.styling_rules.clear()
        ext = self.file_extension
        
        # 1. PYTHON
        if ext in ["py", "pyw"]:
            keywords = ["False", "None", "True", "and", "as", "assert", "async", "await", 
                        "break", "class", "continue", "def", "del", "elif", "else", "except", 
                        "finally", "for", "from", "global", "if", "import", "in", "is", 
                        "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try", 
                        "while", "with", "yield"]
            builtins = ["print", "len", "range", "str", "int", "dict", "list", "set", "tuple", "open"]
            self.add_keyword_rules(keywords, self.color_keyword)
            self.add_keyword_rules(builtins, self.color_builtin)
            self.add_basic_rules(r'"[^"\\]*(\\.[^"\\]*)*"', self.color_string)
            self.add_basic_rules(r"'[^'\\]*(\\.[^'\\]*)*'", self.color_string)
            self.add_basic_rules(r"#[^\n]*", self.color_comment)
            
        # 2. C++ / C / C#.NET
        elif ext in ["cpp", "h", "c", "cs"]:
            keywords = ["break", "case", "class", "const", "continue", "default", "delete", "do", 
                        "else", "enum", "extern", "for", "friend", "goto", "if", "inline", "new", 
                        "namespace", "operator", "private", "protected", "public", "return", "sizeof", 
                        "static", "struct", "switch", "template", "this", "throw", "try", "typedef", 
                        "union", "using", "virtual", "void", "while", "volatile", "interface", "get", "set"]
            builtins = ["int", "long", "short", "char", "float", "double", "bool", "string", "object", "vector"]
            self.add_keyword_rules(keywords, self.color_keyword)
            self.add_keyword_rules(builtins, self.color_builtin)
            self.add_basic_rules(r'"[^"\\]*(\\.[^"\\]*)*"', self.color_string)
            self.add_basic_rules(r"//[^\n]*", self.color_comment)
            
        # 3. JAVA
        elif ext == "java":
            keywords = ["abstract", "assert", "break", "case", "catch", "class", "const", "continue", 
                        "default", "do", "else", "enum", "extends", "final", "finally", "for", "goto", 
                        "if", "implements", "import", "instanceof", "interface", "native", "new", 
                        "package", "private", "protected", "public", "return", "static", "strictfp", 
                        "super", "switch", "synchronized", "this", "throw", "throws", "transient", 
                        "try", "void", "volatile", "while"]
            builtins = ["int", "double", "float", "long", "short", "boolean", "char", "byte", "String", "System"]
            self.add_keyword_rules(keywords, self.color_keyword)
            self.add_keyword_rules(builtins, self.color_builtin)
            self.add_basic_rules(r'"[^"\\]*(\\.[^"\\]*)*"', self.color_string)
            self.add_basic_rules(r"//[^\n]*", self.color_comment)

        # 4. JAVASCRIPT / TYPESCRIPT
        elif ext in ["js", "ts"]:
            keywords = ["break", "case", "catch", "class", "const", "continue", "debugger", "default", 
                        "delete", "do", "else", "export", "extends", "finally", "for", "function", 
                        "if", "import", "in", "instanceof", "new", "return", "super", "switch", "this", 
                        "throw", "try", "typeof", "var", "void", "while", "with", "yield", "let", "await"]
            builtins = ["window", "document", "console", "arguments", "require", "module", "exports"]
            self.add_keyword_rules(keywords, self.color_keyword)
            self.add_keyword_rules(builtins, self.color_builtin)
            self.add_basic_rules(r'"[^"\\]*(\\.[^"\\]*)*"', self.color_string)
            self.add_basic_rules(r"'[^'\\]*(\\.[^'\\]*)*'", self.color_string)
            self.add_basic_rules(r"//[^\n]*", self.color_comment)

        # 5. PHP
        elif ext == "php":
            keywords = ["abstract", "and", "array", "as", "break", "case", "catch", "class", "clone", 
                        "const", "continue", "declare", "default", "die", "do", "echo", "else", "elseif", 
                        "empty", "enddeclare", "endfor", "endforeach", "endif", "endswitch", "endwhile", 
                        "eval", "exit", "extends", "final", "for", "foreach", "function", "global", "if", 
                        "implements", "include", "include_once", "instanceof", "insteadof", "interface", 
                        "isset", "list", "namespace", "new", "or", "print", "private", "protected", 
                        "public", "require", "require_once", "return", "static", "switch", "throw", 
                        "trait", "try", "unset", "use", "var", "while", "xor", "yield"]
            self.add_keyword_rules(keywords, self.color_keyword)
            self.add_basic_rules(r'"[^"\\]*(\\.[^"\\]*)*"', self.color_string)
            self.add_basic_rules(r"//[^\n]*", self.color_comment)
            self.add_basic_rules(r"#[^\n]*", self.color_comment)

        # 6. HTML
        elif ext in ["html", "htm"]:
            self.add_basic_rules(r"<\!?[A-Za-z0-9\-]+", self.color_keyword)
            self.add_basic_rules(r"</[A-Za-z0-9\-]+>", self.color_keyword)
            self.add_basic_rules(r"[A-Za-z0-9\-]+=", self.color_builtin)
            self.add_basic_rules(r'"[^"]*"', self.color_string)
            self.add_basic_rules(r"<\!--[\s\S]*?-->", self.color_comment)

        # 7. CSS
        elif ext == "css":
            self.add_basic_rules(r"[\.\#]?[A-Za-z0-9\-\_]+(?=\s*\{)", self.color_keyword)
            self.add_basic_rules(r"[A-Za-z\-]+(?=\s*\:)", self.color_builtin)
            self.add_basic_rules(r"\:[^\;\n]+", self.color_string)
            self.add_basic_rules(r"/\*[\s\S]*?\*/", self.color_comment)

        # 8. SQL
        elif ext == "sql":
            keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "FROM", "WHERE", "JOIN", "LEFT", 
                        "RIGHT", "INNER", "OUTER", "ON", "GROUP", "BY", "ORDER", "HAVING", "LIMIT", 
                        "CREATE", "TABLE", "DROP", "ALTER", "INDEX", "VIEW", "DATABASE", "INTO", 
                        "VALUES", "SET", "AND", "OR", "NOT", "IN", "ANY", "ALL", "EXISTS", "LIKE", "AS"]
            builtins = ["INT", "VARCHAR", "CHAR", "TEXT", "DATE", "DATETIME", "TIMESTAMP", "FLOAT", "DOUBLE"]
            self.add_keyword_rules(keywords, self.color_keyword, case_sensitive=False)
            self.add_keyword_rules(builtins, self.color_builtin, case_sensitive=False)
            self.add_basic_rules(r"'[^']*'", self.color_string)
            self.add_basic_rules(r"--[^\n]*", self.color_comment)

        # 9. VBA / VB.NET
        elif ext in ["vba", "vb"]:
            keywords = ["AddHandler", "AddressOf", "Alias", "And", "AndAlso", "As", "Boolean", "ByRef", 
                        "ByVal", "Byte", "Call", "Case", "Catch", "Char", "Class", "Const", "Continue", 
                        "Date", "Decimal", "Declare", "Default", "Delegate", "Dim", "DirectCast", "Do", 
                        "Double", "Each", "Else", "ElseIf", "End", "EndIf", "Enum", "Erase", "Error", 
                        "Event", "Exit", "False", "Finally", "For", "Friend", "From", "Function", "Get", 
                        "GetType", "GetXMLNamespace", "Global", "GoSub", "GoTo", "Handles", "If", 
                        "Implements", "Imports", "In", "Inherits", "Integer", "Interface", "Is", "IsNot", 
                        "Let", "Lib", "Like", "Long", "Loop", "Me", "Mod", "Module", "MustInherit", 
                        "MustOverride", "MyBase", "MyClass", "Namespace", "Narrowing", "New", "Next", 
                        "Not", "Nothing", "NotInheritable", "NotOverridable", "Object", "Of", "On", 
                        "Operator", "Option", "Optional", "Or", "OrElse", "Out", "Overloads", 
                        "Overridable", "Overrides", "ParamArray", "Partial", "Private", "Property", 
                        "Protected", "Public", "RaiseEvent", "ReadOnly", "ReDim", "REM", "RemoveHandler", 
                        "Resume", "Return", "SByte", "Select", "Set", "Shadows", "Shared", "Short", 
                        "Single", "Static", "Step", "Stop", "String", "Structure", "Sub", "SyncLock", 
                        "Then", "Throw", "To", "True", "Try", "TryCast", "TypeOf", "UInteger", "ULong", 
                        "UShort", "Using", "Variant", "Wend", "While", "Widening", "With", "WithEvents", 
                        "WriteOnly", "Xor"]
            self.add_keyword_rules(keywords, self.color_keyword, case_sensitive=False)
            self.add_basic_rules(r'"[^"\n]*"', self.color_string)
            self.add_basic_rules(r"'[^\n]*", self.color_comment)

        # 10. JSON
        elif ext == "json":
            self.add_basic_rules(r'"[^"\\]*(\\.[^"\\]*)*"\s*(?=\:)', self.color_keyword)
            self.add_basic_rules(r"\:\s*\"[^\"\\]*(\\.[^\"\\]*)*\"", self.color_string)
            self.add_basic_rules(r"\b(true|false|null)\b", self.color_builtin)

        # 11. XML
        elif ext == "xml":
            self.add_basic_rules(r"<\!?[A-Za-z0-9\-]+", self.color_keyword)
            self.add_basic_rules(r"</[A-Za-z0-9\-]+>", self.color_keyword)
            self.add_basic_rules(r"[A-Za-z0-9\-]+=", self.color_builtin)
            self.add_basic_rules(r'"[^"]*"', self.color_string)
            self.add_basic_rules(r"<\!--[\s\S]*?-->", self.color_comment)

        # 12. YAML
        elif ext in ["yaml", "yml"]:
            self.add_basic_rules(r"^[A-Za-z0-9\-\_\s]+(?=\:)", self.color_keyword)
            self.add_basic_rules(r"\:\s*[^\n]+", self.color_string)
            self.add_basic_rules(r"#[^\n]*", self.color_comment)

        # 13. INI / CONF
        elif ext in ["ini", "conf"]:
            self.add_basic_rules(r"^\[[A-Za-z0-9\-\_\s]+\]", self.color_builtin)
            self.add_basic_rules(r"^[A-Za-z0-9\-\_\s]+(?=\=)", self.color_keyword)
            self.add_basic_rules(r"\=[^\n]*", self.color_string)
            self.add_basic_rules(r"[;#][^\n]*", self.color_comment)

        # 14. BASH
        elif ext == "sh":
            keywords = ["if", "then", "else", "elif", "fi", "case", "esac", "for", "while", 
                        "until", "do", "done", "in", "function", "return", "exit", "local"]
            self.add_keyword_rules(keywords, self.color_keyword)
            self.add_basic_rules(r'"[^"\\]*(\\.[^"\\]*)*"', self.color_string)
            self.add_basic_rules(r"'[^']*'", self.color_string)
            self.add_basic_rules(r"#[^\n]*", self.color_comment)

        # 15. POWERSHELL / BATCH
        elif ext in ["ps1", "bat"]:
            keywords = ["if", "else", "elseif", "switch", "foreach", "for", "while", "do", 
                        "until", "function", "filter", "param", "return", "continue", "break"]
            self.add_keyword_rules(keywords, self.color_keyword, case_sensitive=False)
            self.add_basic_rules(r'"[^"\\]*(\\.[^"\\]*)*"', self.color_string)
            self.add_basic_rules(r"#[^\n]*", self.color_comment)
            self.add_basic_rules(r"(?i)\brem\b[^\n]*", self.color_comment)

        if ext != "txt":
            self.add_keyword_rules(["self", "this"], self.color_self)
            self.add_basic_rules(r"\b[A-Za-z0-9\-\_]+(?=\s*\()", self.color_function)
            self.add_basic_rules(r"[\+\-\*\/\=\!\<\>\&\|\^]", self.color_operator)

    def add_keyword_rules(self, keyword_list, color, case_sensitive=True):
        #Helper to create word-bounded rules for language keywords.#
        flags = QRegularExpression.PatternOption.NoPatternOption
        if not case_sensitive:
            flags = QRegularExpression.PatternOption.CaseInsensitiveOption
            
        text_format = QTextCharFormat()
        text_format.setForeground(color)
        text_format.setFontWeight(QFont.Weight.Bold)
        
        for word in keyword_list:
            pattern = r"\b" + re.escape(word) + r"\b"
            regex = QRegularExpression(pattern, flags)
            self.styling_rules.append((regex, text_format))

    def add_basic_rules(self, pattern, color):
        #Helper to map a basic raw regex pattern to a designated syntax color.#
        text_format = QTextCharFormat()
        text_format.setForeground(color)
        regex = QRegularExpression(pattern)
        self.styling_rules.append((regex, text_format))

    def highlightBlock(self, text):
        #Overrides the base Qt method to paint matched syntax highlights onto current text block.#
        for regex, text_format in self.styling_rules:
            match_iterator = regex.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                start_index = match.capturedStart()
                match_length = match.capturedLength()
                self.setFormat(start_index, match_length, text_format)


# ========================================================
# 2. LIVE METRICS & COUNTERS CALCULATOR
# ========================================================
def calculate_text_metrics(editor):
    #Calculates pure line, word, and space counts from the active editor.#
    if not editor:
        return 0, 0, 0

    QApplication.processEvents()

    total_lines = editor.document().blockCount()
    raw_text = editor.toPlainText()
    word_count = len(raw_text.split()) if raw_text.strip() else 0
    total_spaces = raw_text.count(' ')

    return total_lines, word_count, total_spaces


# ========================================================
# 3. LINE ENDINGS DETECTOR LOGIC
# ========================================================
def detect_line_endings_logic(file_content_raw):
    #Analyzes raw binary file data to instantly detect Windows (CRLF) or Linux (LF) markers.#
    if b'\r\n' in file_content_raw:
        return "CRLF"
    elif b'\n' in file_content_raw:
        return "LF"
    else:
        return "CRLF" if name == 'nt' else "LF"


# ========================================================
# 4. PURE BASE64 CRYPTO VAULT
# ========================================================
def encrypt_payload(text_content):
    #Converts multi-language text safely into an unreadable Base64 string.#
    try:
        return base64.b64encode(text_content.encode('utf-8'))
    except Exception:
        return text_content.encode('utf-8')


def decrypt_payload(binary_payload):
    #Reverses Base64 payloads back into pristine multi-language text.#
    try:
        return base64.b64decode(binary_payload).decode('utf-8')
    except Exception:
        return binary_payload.decode('utf-8', errors='ignore')


# ========================================================
# 5. ADVANCED FILE I/O CORE ENGINE (Open & Save)
# ========================================================
def open_and_decode_file_logic(file_path):
    # Opens a file from disk, automatically detects encoding, and resolves line endings.
    with open(file_path, "rb") as f:
        raw_data = f.read()

    if not raw_data:
        return "", "utf-8", "LF"

    # Dynamic line endings detection via utility function
    line_ending = detect_line_endings_logic(raw_data)

    # Robust encoding detection layer optimized for compiled environments (Nuitka/PyInstaller)
    try:
        detector = UniversalDetector()
        # Feed the raw binary data into the streaming detector
        detector.feed(raw_data)
        detector.close()
        
        # Fallback to utf-8 if chardet returns None or an invalid string
        encoding = detector.result.get("encoding") if detector.result.get("encoding") else "utf-8"
    except Exception:
        # Fail-safe mechanism: If chardet internal model.bin is missing post-compilation, gracefully fallback to utf-8
        encoding = "utf-8"

    # Decode payload into text view layer strings securely
    try:
        text_content = raw_data.decode(encoding)
    except Exception:
        # Final fallback line to prevent crash on heavily corrupted formatting character arrays
        text_content = raw_data.decode("utf-8", errors="replace")
        encoding = "utf-8"

    return text_content, encoding, line_ending


def save_and_encode_file_logic(file_path, text_content, encoding, line_ending):
    #Encodes text content to target encoding and line endings, then flushes safely to disk.#
    if line_ending == "CRLF":
        normalized_text = text_content.replace("\r\n", "\n").replace("\n", "\r\n")
    else:
        normalized_text = text_content.replace("\r\n", "\n")

    try:
        binary_data = normalized_text.encode(encoding)
    except Exception:
        binary_data = normalized_text.encode("utf-8")
        encoding = "utf-8"

    with open(file_path, "wb") as f:
        f.write(binary_data)

    return encoding


# ========================================================
# 6. AUTOMATIC BACKGROUND BACKUP DAEMON
# ========================================================
def execute_auto_backup_logic(tabs_widget, backup_dir):
    #Background daemon that encrypts modified tabs into the backup directory.#
    if not path.exists(backup_dir):
        return

    for index in range(tabs_widget.count()):
        editor = tabs_widget.widget(index)
        if editor and editor.document().isModified():
            content = editor.toPlainText()
            if not content.strip():
                continue
            
            base = path.basename(editor.file_path) if editor.file_path else f"Unsaved_Tab_{index + 1}"
            backup_filename = f"RECOVERY_{base}.pynp"
            backup_full_path = path.join(backup_dir, backup_filename)
            
            try:
                encrypted = encrypt_payload(content)
                with open(backup_full_path, "wb") as f:
                    f.write(encrypted)
            except Exception:
                pass


# ========================================================
# 7. BACKUP HOUSEKEEPING UTILITY
# ========================================================
def clean_individual_file_backup(file_path_or_tab_name, backup_dir):
    #Deletes temporary session backups once a normal file save occurs.#
    try:
        base = path.basename(file_path_or_tab_name) if file_path_or_tab_name else ""
        if base and path.exists(backup_dir):
            for filename in listdir(backup_dir):
                if base in filename and filename.startswith("RECOVERY_"):
                    remove(path.join(backup_dir, filename))
    except Exception:
        pass


# ========================================================
# 8. SESSION STATE TRACKER METRIC MANAGER
# ========================================================
def load_session_files_logic(settings_instance):
    #Loads previous active session files safely from internal QSettings cache strings.#
    try:
        session_json = settings_instance.value("Session/OpenedFiles", "[]")
        return json.loads(session_json)
    except Exception:
        return []


def save_session_files_logic(settings_instance, session_data_list):
    #Flushes active editor file lists safely into QSettings cache strings.#
    try:
        session_json = json.dumps(session_data_list)
        settings_instance.setValue("Session/OpenedFiles", session_json)
    except Exception:
        pass


# ========================================================
# 9. GRAPHICAL COLOR CONVERSION ENGINE
# ========================================================
def change_icon_color_logic(image_path, text_color):
    #Tints SVG or PNG pixel data to contrast cleanly on light/dark themes.#
    pixmap = QPixmap(image_path)
    if pixmap.isNull():
        return QIcon()

    painter = QPainter(pixmap)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), text_color)
    painter.end()
    return QIcon(pixmap)

def apply_highlighter_to_editor(editor, file_path, current_theme):
    # It dynamically links the code highlighter to the editor
    #based on the file extension and the current theme state (dark or light).
    if not editor:
        return

    # Extract the extension to determine the programming language, or assume it is a plain text file
    _, ext = path.splitext(file_path) if file_path else ("", ".txt")
    
    # If the editor doesn't already have a Highlighter, we'll create one for it.
    if not hasattr(editor, 'highlighter') or not editor.highlighter:
        editor.highlighter = CodeHighlighter(editor.document())
        
    # Determine whether the editor should use dark or light mode colors
    is_dark_now = (current_theme == "dark" or (current_theme == "system" and QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark))
    
    # Update color mode, effective extension, and recolor instantly
    editor.highlighter.set_theme_mode(is_dark_now)
    editor.highlighter.set_active_extension(ext)