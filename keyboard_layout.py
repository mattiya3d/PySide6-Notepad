from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QComboBox, QLabel, QPushButton
from PySide6.QtCore import QSettings

#  Safe Private Use Area token (Never typed by a user, safe from layout corruption)
PLACEHOLDER_LA = "\uE000"

# ==========================================
# 1. ⌨️ HARDWARE DICTIONARIES (Strictly Tokenized & Aligned)
# ==========================================
KEYS_ENGLISH_US = {
    "normal": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "=", "q", "w", "e", "r", "t", "y", "u", "i", "o", "p", "[", "]", "a", "s", "d", "f", "g", "h", "j", "k", "l", ";", "'", "z", "x", "c", "v", "b", "n", "m", ",", ".", "/", "`", "\\"],
    "shift":  ["!", "@", "#", "$", "%", "^", "&", "*", "(", ")", "_", "+", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "{", "}", "A", "S", "D", "F", "G", "H", "J", "K", "L", ":", "\"", "Z", "X", "C", "V", "B", "N", "M", "<", ">", "?", "~", "|"]
}

KEYS_ARABIC_101 = {
    "normal": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "=", "ض", "ص", "ث", "ق", "ف", "غ", "ع", "ه", "خ", "ح", "ج", "د", "ش", "س", "ي", "ب", "ل", "ا", "ت", "ن", "م", "ك", "ط", "ئ", "ء", "ؤ", "ر", PLACEHOLDER_LA, "ى", "ة", "و", "ز", "ظ", "ذ", "\\"],
    "shift":  ["!", "@", "#", "$", "%", "^", "&", "*", "(", ")", "_", "+", "َ", "ً", "ُ", "ٌ", "لإ", "إ", "‘", "÷", "×", "؛", "<", ">", "ِ", "ٍ", "]", "[", "لأ", "أ", "ـ", "،", "/", ":", "\"", "~", "ْ", "{", "}", "لآ", "آ", "’", ",", ".", "؟", "ّ", "|"]
}

KEYS_ARABIC_102 = {
    "normal": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "=", "ض", "ص", "ث", "ق", "ف", "غ", "ع", "ه", "خ", "ح", "ج", "د", "ش", "س", "ي", "ب", "ل", "ا", "ت", "ن", "م", "ك", "ط", "ئ", "ء", "ؤ", "ر", PLACEHOLDER_LA, "ى", "ة", "و", "ذ", "ظ", "\\", "`"],
    "shift":  ["!", "@", "#", "$", "%", "^", "&", "*", "(", ")", "_", "+", "َ", "ً", "ُ", "ٌ", "لإ", "إ", "‘", "÷", "×", "؛", "<", ">", "ِ", "ٍ", "]", "[", "لأ", "أ", "ـ", "،", "/", ":", "\"", "~", "ْ", "{", "}", "لآ", "آ", "’", ",", ".", "ظ", "ّ", "|"]
}

KEYS_ARABIC_MAC = {
    "normal": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "=", "ض", "ص", "ث", "ق", "ف", "غ", "ع", "ه", "خ", "ح", "ج", "د", "ش", "س", "ي", "ب", "ل", "ا", "ت", "ن", "م", "ك", "ط", "ئ", "ء", "ؤ", "ر", PLACEHOLDER_LA, "ى", "ة", "و", "ز", "ظ", "ذ", "\\"],
    "shift":  ["!", "@", "#", "$", "%", "^", "&", "*", "(", ")", "_", "+", "]", "}", "[", "لإ", "إ", "`", "÷", "×", "؛", "<", ">", "ِ", "ٍ", "ْ", "{", "لأ", "أ", "ـ", "ك", "م", "ا", "ن", "/", "~", "ْ", " ", " ", "لآ", "آ", "’", ",", ".", "؟", "ّ", "|"]
}

KEYS_RUSSIAN = {
    "normal": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "=", "й", "ц", "у", "к", "е", "н", "г", "ш", "щ", "з", "х", "ъ", "ф", "ы", "в", "а", "п", "р", "о", "л", "д", "ж", "э", "я", "ч", "с", "м", "и", "т", "ь", "б", "ю", ".", "ё", "\\"],
    "shift":  ["!", "\"", "№", ";", "%", ":", "?", "*", "(", ")", "_", "+", "Й", "Ц", "У", "К", "Е", "Н", "Г", "Ш", "Щ", "З", "Х", "Ъ", "А", "Ы", "В", "А", "П", "Р", "О", "Л", "Д", "Ж", "Э", "Я", "Ч", "С", "М", "И", "Т", "Ь", "Б", "Ю", ",", "Ё", "/"]
}

KEYS_PORTUGUESE = {
    "normal": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "=", "q", "w", "e", "r", "t", "y", "u", "i", "o", "p", "´", "[", "a", "s", "d", "f", "g", "h", "j", "k", "l", "ç", "~", "z", "x", "c", "v", "b", "n", "m", ",", ".", "-", "'", "\\"],
    "shift":  ["!", "@", "#", "$", "%", "¨", "&", "*", "(", ")", "_", "+", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "`", "{", "A", "S", "D", "F", "G", "H", "J", "K", "L", "Ç", "^", "Z", "X", "C", "V", "B", "N", "M", "<", ">", "_", "\"", "|"]
}

KEYS_HINDI_INSCRIPT = {
    "normal": ["१", "२", "३", "४", "५", "६", "७", "८", "९", "०", "-", "ृ", "ौ", "ै", "ा", "ी", "ू", "ब", "ह", "ग", "द", "ज", "ड", "ृ", "ो", "े", "ा", "ि", "ु", "प", "र", "क", "त", "च", "ट", "े", "ं", "م", "न", "व", "防", "स", "य", ".", "ध", "ॉ", "श्र"],
    "shift":  ["इ", "ॅ", "्र", "र्", "ज्ञ", "त्र", "क्ष", "श्र", "(", ")", "ः", "ऋ", "औ", "ऐ", "आ", "ई", "ऊ", "भ", "ङ", "घ", "ध", "झ", "ढ", "ञ", "ओ", "ए", "अ", "इ", "उ", "फ", "ऱ", "ख", "थ", "छ", "ठ", "ऑ", "ँ", "ण", "न", "श", "ळ", "ष", "य", "ष", "घ", "ो", "।"]
}

#  ADDED: Spanish International Layout (Ñ Key included)
KEYS_SPANISH = {
    "normal": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "'", "¡", "q", "w", "e", "r", "t", "y", "u", "i", "o", "p", "`", "+", "a", "s", "d", "f", "g", "h", "j", "k", "l", "ñ", "{", "z", "x", "c", "v", "b", "n", "m", ",", ".", "-", "º", "ç"],
    "shift":  ["!", "\"", "·", "$", "%", "&", "/", "(", ")", "=", "?", "¿", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "^", "*", "A", "S", "D", "F", "G", "H", "J", "K", "L", "Ñ", "}", "Z", "X", "C", "V", "B", "N", "M", ";", ":", "_", "ª", "Ç"]
}

#  ADDED: French Standard Layout (AZERTY Physical Mapping)
KEYS_FRENCH = {
    "normal": ["&", "é", "\"", "'", "(", "-", "è", "_", "ç",_la := "à", ")", "=", "a", "z", "e", "r", "t", "y", "u", "i", "o", "p", "^", "$", "q", "s", "d", "f", "g", "h", "j", "k", "l", "m", "ù", "w", "x", "c", "v", "b", "n", ",", ";", ":", "!", "²", "*"],
    "shift":  ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "°", "+", "A", "Z", "E", "R", "T", "Y", "U", "I", "O", "P", "¨", "£", "Q", "S", "D", "F", "G", "H", "J", "K", "L", "M", "%", "W", "X", "C", "V", "B", "N", "?", ".", "/", "§", "²", "µ"]
}

#  ADDED: German Standard Layout (QWERTZ Physical Mapping)
KEYS_GERMAN = {
    "normal": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "ß", "´", "q", "w", "e", "r", "t", "z", "u", "i", "o", "p", "ü", "+", "a", "s", "d", "f", "g", "h", "j", "k", "l", "ö", "ä", "y", "x", "c", "v", "b", "n", "m", ",", ".", "-", "^", "#"],
    "shift":  ["!", "\"", "§", "$", "%", "&", "/", "(", ")", "=", "?", "`", "Q", "W", "E", "R", "T", "Z", "U", "I", "O", "P", "Ü", "*", "A", "S", "D", "F", "G", "H", "J", "K", "L", "Ö", "Ä", "Y", "X", "C", "V", "B", "N", "M", ";", ":", "_", "°", "'"]
}
# ADDED: Italian Standard Layout (QWERTY Physical Mapping with accented characters)
KEYS_ITALIAN = {
    "normal": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "ì", "'", "q", "w", "e", "r", "t", "y", "u", "i", "o", "p", "è", "+", "a", "s", "d", "f", "g", "h", "j", "k", "l", "ò", "à", "ù", "z", "x", "c", "v", "b", "n", "m", ",", ".", "-", "<"],
    "shift":  ["!", "\"", "£", "$", "%", "&", "/", "(", ")", "=", "^", "?", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "é", "*", "A", "S", "D", "F", "G", "H", "J", "K", "L", "Ç", "°", "§", "Z", "X", "C", "V", "B", "N", "M", ";", ":", "_", ">"]
}
# ==========================================
# 2.  MASTER REGISTRY MAP
# ==========================================
LAYOUT_REGISTRY = {
    "Standard US": KEYS_ENGLISH_US,
    "Arabic 101": KEYS_ARABIC_101,
    "Arabic 102": KEYS_ARABIC_102,
    "Mac Arabic": KEYS_ARABIC_MAC,
    "Russian Standard": KEYS_RUSSIAN,
    "Portuguese (Brazil)": KEYS_PORTUGUESE,
    "Hindi InScript": KEYS_HINDI_INSCRIPT,
    "Spanish Traditional": KEYS_SPANISH,
    "French AZERTY": KEYS_FRENCH,
    "German QWERTZ": KEYS_GERMAN,
    "Italian Standard": KEYS_ITALIAN
}

# ==========================================
# 3. ⚙️ OPTIMIZED LOGIC ENGINE
# ==========================================
def convert_string_layout(selected_text, org_name="Mattiya3D", app_name="PySide6Notepad"):
    #Advanced Dynamic Layout Inversion Engine with safe Multi-Language Index Mapping.#
    settings = QSettings(org_name, app_name)
    kb1_name = settings.value("layout_converter_kb_1", "Arabic 101")
    kb2_name = settings.value("layout_converter_kb_2", "Standard US")

    kb1 = LAYOUT_REGISTRY.get(kb1_name, KEYS_ARABIC_101)
    kb2 = LAYOUT_REGISTRY.get(kb2_name, KEYS_ENGLISH_US)

    INVARIANT_CHARS = set("0123456789")
    converted_chars = []

    text_to_process = selected_text.replace("لا", PLACEHOLDER_LA)
    text_to_process = text_to_process.replace("ل" + "ا", PLACEHOLDER_LA)

    for char in text_to_process:
        if char in INVARIANT_CHARS:
            converted_chars.append(char)
            continue

        found = False

        # PHASE 1: Prioritize Normal Keymaps First
        for kb_src, kb_dst in [(kb1, kb2), (kb2, kb1)]:
            if char in kb_src["normal"]:
                idx = kb_src["normal"].index(char)
                converted_chars.append(kb_dst["normal"][idx])
                found = True
                break

        # PHASE 2: Fallback to Shift Keymaps
        if not found:
            for kb_src, kb_dst in [(kb1, kb2), (kb2, kb1)]:
                if char in kb_src["shift"]:
                    idx = kb_src["shift"].index(char)
                    converted_chars.append(kb_dst["shift"][idx])
                    found = True
                    break

        if not found:
            converted_chars.append(char)

    result_text = "".join(converted_chars)
    result_text = result_text.replace(PLACEHOLDER_LA, "لا")
    
    return result_text

# ==========================================
# 4. 🖥️ SETTINGS DIALOG UI (With Smart Conflict Protection)
# ==========================================
class LayoutSettingsDialog(QDialog):
    def __init__(self, parent=None, org_name="Mattiya3D", app_name="PySide6Notepad"):
        super().__init__(parent)
        self.org_name = org_name
        self.app_name = app_name
        self.setWindowTitle("Layout Settings")
        self.setMinimumWidth(450)
        self.init_ui()

    def init_ui(self):
        layout_main = QVBoxLayout(self)

        self.combo_lang_1 = QComboBox()
        self.combo_kb_1 = QComboBox()
        self.combo_lang_2 = QComboBox()
        self.combo_kb_2 = QComboBox()

        #  Full International Trilateral Languages Fleet
        self.languages = ["Arabic", "English", "Spanish", "French", "German", "Russian", "Portuguese", "Hindi"]
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
        # PROTECTION: Dynamically strips Language 1 from Language 2 to completely block duplicates.#
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
        #Populates specific layouts safely preventing rogue cross-mappings.#
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