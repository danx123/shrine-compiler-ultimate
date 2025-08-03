import sys
import os
import compileall
import shutil
import random
import string
import json
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QFileDialog, QTextEdit, QLabel, QListWidget, QMessageBox,
    QHBoxLayout, QComboBox, QCheckBox # Import QCheckBox
)
from PyQt6.QtCore import Qt, QUrl, QObject, QThread, pyqtSignal # Import QObject, QThread, pyqtSignal for multithreading
from PyQt6.QtGui import QIcon, QDesktopServices # Import QDesktopServices for opening folders

# Pastikan file GlyphWidget.py ada di direktori yang sama
# Jika GlyphWidget belum memiliki stop_loop(), tambahkan secara manual.
# from GlyphWidget import GlyphWidget 

# Dummy GlyphWidget for standalone testing if original not available or for mocking stop_loop
class GlyphWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFixedSize(100, 100)
        self.setStyleSheet("background-color: black;")
        self._is_animating = False # Track animation state

    def start_loop(self):
        if not self._is_animating:
            print("Glyph animation started (dummy)")
            # Add actual animation start logic here
            self._is_animating = True

    def stop_loop(self):
        if self._is_animating:
            print("Glyph animation stopped (dummy)")
            # Add actual animation stop logic here
            self._is_animating = False

# === Config & Language Paths ===
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
COMPILER_CONFIG_PATH = os.path.join(BASE_PATH, "compiler_config.json")
LANG_DIR = BASE_PATH # Language files are in the same directory as the script

def load_compiler_config(path):
    """Loads configuration for the compiler, creating a default if none exists."""
    if not os.path.exists(path):
        default_config = { 
            "language": "en", 
            "open_folder_after_convert": True 
        } 
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=2)
        return default_config
    with open(path, "r", encoding="utf-8") as f:
        config = json.load(f)
        # Ensure new keys exist if loading an old config
        if "open_folder_after_convert" not in config:
            config["open_folder_after_convert"] = True
        return config

def save_compiler_config(config_data, path):
    """Saves the current compiler configuration."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)

# === Worker Thread for Compilation ===
class CompilerWorker(QObject):
    finished = pyqtSignal(list) # Emits list of successful output folders
    error = pyqtSignal(str) # Emits error messages
    log_message = pyqtSignal(str) # Emits log messages to be displayed in UI
    
    def __init__(self, folders, manifest_path):
        super().__init__()
        self.folders = folders
        self.manifest_path = manifest_path
        self._is_running = True

    def random_name(self, length=6):
        return "gy_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=length)) + ".pyc"

    def stop(self):
        self._is_running = False

    def run_compilation(self):
        successful_output_folders = []
        try:
            with open(self.manifest_path, "a", encoding="utf-8") as manifest:
                manifest.write(f"\n=== [{datetime.now()}] ===\n")

                for folder in self.folders:
                    if not self._is_running: # Allow stopping the process
                        self.log_message.emit("Kompilasi dibatalkan.")
                        break

                    self.log_message.emit(f"📦 Shrine: {folder}")
                    
                    try:
                        compileall.compile_dir(folder, force=True, legacy=True, quiet=1)
                    except Exception as e:
                        self.log_message.emit(f"❌ Error compiling {folder}: {e}")
                        continue # Skip to next folder if compilation fails

                    pycache_path = os.path.join(folder, "__pycache__")
                    cloak_folder = os.path.join(folder, ".glyphs")
                    os.makedirs(cloak_folder, exist_ok=True)
                    
                    # Ensure pycache_path exists before walking
                    if not os.path.exists(pycache_path):
                        self.log_message.emit(f"⚠️ Warning: No __pycache__ found for {folder}. Skipping glyphification.")
                        continue

                    files_found = False
                    for root, _, files in os.walk(pycache_path):
                        for file in files:
                            if file.endswith(".pyc"):
                                files_found = True
                                original_path = os.path.join(root, file)
                                glyph_name = self.random_name()
                                renamed_path = os.path.join(cloak_folder, glyph_name)

                                try:
                                    shutil.copy2(original_path, renamed_path)
                                    self.log_message.emit(f"✅ Glyphified: {glyph_name}")
                                    manifest.write(f"{renamed_path}\n")
                                except FileNotFoundError:
                                    self.log_message.emit(f"❌ Error: Source file not found - {original_path}")
                                except PermissionError:
                                    self.log_message.emit(f"❌ Error: Permission denied for {original_path} or {renamed_path}")
                                except Exception as e:
                                    self.log_message.emit(f"❌ General Error glyphifying {file}: {e}")
                    
                    if files_found:
                        successful_output_folders.append(cloak_folder)
                    else:
                        self.log_message.emit(f"⚠️ No .pyc files found in {pycache_path} for glyphification.")

            self.log_message.emit("🧘‍♂️ Ritual selesai. Semua glyph disimpan.")
            self.finished.emit(successful_output_folders)

        except Exception as e:
            self.error.emit(f"Terjadi kesalahan fatal selama kompilasi: {e}")
            self.finished.emit([]) # Emit finished with empty list on fatal error

class ShrineCompiler(QWidget):
    def __init__(self):
        super().__init__()

        self.config = load_compiler_config(COMPILER_CONFIG_PATH)
        self.current_language = self.config.get("language", "en")
        self.translations = {}
        self._load_language_data(self.current_language)

        self.setWindowTitle(self.tr("app_title"))
        self.setMinimumSize(520, 450)
        
        if hasattr(sys, "_MEIPASS"): 
            icon_path = os.path.join(sys._MEIPASS, "compiler.ico")
        else:
            icon_path = "compiler.ico"

        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.folder_list = QListWidget()
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.manifest_path = os.path.join(os.getcwd(), "manifest_glyph.txt")

        # Worker thread for compilation
        self.thread = None
        self.worker = None

        self.setup_ui()

        # Signals
        self.btn_add.clicked.connect(self.add_folder)
        self.btn_clear.clicked.connect(self.clear_all)
        self.btn_convert.clicked.connect(self.start_compilation)

    def _load_language_data(self, lang_code):
        """Loads translations from a JSON file."""
        lang_file = os.path.join(LANG_DIR, f"{lang_code}_compiler.json")
        try:
            with open(lang_file, "r", encoding="utf-8") as f:
                self.translations = json.load(f)
            self.current_language = lang_code
            self.config["language"] = lang_code
            save_compiler_config(self.config, COMPILER_CONFIG_PATH)
        except FileNotFoundError:
            print(f"Error: Language file '{lang_file}' not found. Using default or English.")
            if lang_code != "en":
                self._load_language_data("en")
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from '{lang_file}'.")
            if lang_code != "en":
                self._load_language_data("en")

    def tr(self, key):
        """Translation helper function."""
        return self.translations.get(key, key) 

    def setup_ui(self):
        """Sets up the UI elements and applies translations."""
        main_layout = QVBoxLayout() 

        # Language Selection
        lang_layout = QHBoxLayout()
        self.lang_label = QLabel(self.tr("language_selection")) # Make QLabel an attribute
        lang_layout.addWidget(self.lang_label)

        self.lang_combo = QComboBox(self)
        self.lang_combo.addItem("English", "en")
        self.lang_combo.addItem("Bahasa Indonesia", "id")
        
        index = self.lang_combo.findData(self.current_language)
        if index != -1:
            self.lang_combo.setCurrentIndex(index)
        
        self.lang_combo.currentIndexChanged.connect(self.change_language)
        lang_layout.addWidget(self.lang_combo)
        lang_layout.addStretch(1) 
        main_layout.addLayout(lang_layout)

        # UI Buttons
        self.btn_add = QPushButton(self.tr("add_folder_button"))
        self.btn_convert = QPushButton(self.tr("convert_button"))
        self.btn_clear = QPushButton(self.tr("clear_list_button"))

        self.folder_list_label = QLabel(self.tr("folder_list_label")) # Make QLabel an attribute
        main_layout.addWidget(self.folder_list_label)
        main_layout.addWidget(self.folder_list)
        main_layout.addWidget(self.btn_add)
        main_layout.addWidget(self.btn_clear)

        self.checkbox_open_folder = QCheckBox(self.tr("open_folder_checkbox"))
        self.checkbox_open_folder.setChecked(self.config.get("open_folder_after_convert", True))
        self.checkbox_open_folder.stateChanged.connect(self._save_open_folder_setting)
        main_layout.addWidget(self.checkbox_open_folder)

        main_layout.addWidget(self.btn_convert)

        self.log_manifest_label = QLabel(self.tr("log_manifest_label")) # Make QLabel an attribute
        main_layout.addWidget(self.log_manifest_label)
        main_layout.addWidget(self.log_area)

        self.glyph_animator = GlyphWidget() 
        # main_layout.addWidget(self.glyph_animator) # Uncomment if GlyphWidget is part of layout

        self.setLayout(main_layout)
        self.update_ui_language()

    def update_ui_language(self):
        """Updates all UI elements with current language translations."""
        self.setWindowTitle(self.tr("app_title"))
        self.lang_label.setText(self.tr("language_selection"))
        self.btn_add.setText(self.tr("add_folder_button"))
        self.btn_convert.setText(self.tr("convert_button"))
        self.btn_clear.setText(self.tr("clear_list_button"))
        self.checkbox_open_folder.setText(self.tr("open_folder_checkbox"))
        self.folder_list_label.setText(self.tr("folder_list_label")) # Direct update
        self.log_manifest_label.setText(self.tr("log_manifest_label")) # Direct update

    def change_language(self, index):
        """Handles language change from the QComboBox."""
        lang_code = self.lang_combo.itemData(index)
        if lang_code != self.current_language:
            self._load_language_data(lang_code)
            self.update_ui_language()

    def _save_open_folder_setting(self, state):
        """Saves the state of the open folder checkbox to config."""
        self.config["open_folder_after_convert"] = self.checkbox_open_folder.isChecked()
        save_compiler_config(self.config, COMPILER_CONFIG_PATH)

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, self.tr("select_folder_dialog_title"))
        if folder and folder not in [self.folder_list.item(i).text() for i in range(self.folder_list.count())]:
            self.folder_list.addItem(folder)

    def clear_all(self):
        self.folder_list.clear()
        self.log_area.clear()

    def log(self, message):
        self.log_area.append(message)

    def start_compilation(self):
        folders = [self.folder_list.item(i).text() for i in range(self.folder_list.count())]
        if not folders:
            QMessageBox.warning(self, self.tr("empty_folders_warning_title"), self.tr("empty_folders_warning_message"))
            return
        
        # Disable buttons during compilation
        self.btn_add.setEnabled(False)
        self.btn_clear.setEnabled(False)
        self.btn_convert.setEnabled(False)
        self.lang_combo.setEnabled(False)
        self.checkbox_open_folder.setEnabled(False)

        self.log_area.clear() # Clear log before new compilation
        self.log(f"{self.tr('compilation_start_log')} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.glyph_animator.start_loop() # Start animation

        # Setup worker thread
        self.thread = QThread()
        self.worker = CompilerWorker(folders, self.manifest_path)
        self.worker.moveToThread(self.thread)

        # Connect signals
        self.thread.started.connect(self.worker.run_compilation)
        self.worker.finished.connect(self.on_compilation_finished)
        self.worker.error.connect(self.on_compilation_error)
        self.worker.log_message.connect(self.log)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.error.connect(self.worker.deleteLater) # Also delete worker on error completion

        # Start the thread
        self.thread.start()

    def on_compilation_finished(self, output_folders):
        self.glyph_animator.stop_loop() # Stop animation

        # Re-enable buttons
        self.btn_add.setEnabled(True)
        self.btn_clear.setEnabled(True)
        self.btn_convert.setEnabled(True)
        self.lang_combo.setEnabled(True)
        self.checkbox_open_folder.setEnabled(True)

        QMessageBox.information(self, self.tr("success_message_box_title"), self.tr("success_message_box_message"))

        if self.checkbox_open_folder.isChecked():
            for folder_path in output_folders:
                if os.path.exists(folder_path):
                    QDesktopServices.openUrl(QUrl.fromLocalFile(folder_path))
                else:
                    self.log(f"Warning: Output folder not found: {folder_path}")
        
        # Clean up thread
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait() # Wait for thread to finish cleanly

    def on_compilation_error(self, message):
        self.glyph_animator.stop_loop() # Stop animation on error

        # Re-enable buttons
        self.btn_add.setEnabled(True)
        self.btn_clear.setEnabled(True)
        self.btn_convert.setEnabled(True)
        self.lang_combo.setEnabled(True)
        self.checkbox_open_folder.setEnabled(True)

        QMessageBox.critical(self, "Error Kompilasi", message)
        
        # Clean up thread
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    compiler = ShrineCompiler()
    compiler.show()
    sys.exit(app.exec())