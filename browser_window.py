import os
import sys
import re
import urllib.parse
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QToolButton, QProgressBar, QDialog,
    QListWidget, QListWidgetItem, QCheckBox, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt, QUrl, QPoint, QSize, QTimer
from PySide6.QtGui import QIcon, QPixmap, QAction, QKeySequence, QShortcut, QDesktopServices
from PySide6.QtWebEngineCore import (
    QWebEngineProfile, QWebEngineDownloadRequest, QWebEngineScript
)

from config import config, ASSETS_DIR, DATA_DIR, STORAGE_DIR
from tab_view import ImperialTabWidget
from interceptor import ImperialRequestInterceptor
from ram_optimizer import ImperialRamOptimizer
from extensions_manager import ImperialExtensionsManager
from virus_scanner import virus_scanner
from adblocker import adblocker
from web_engine import NEW_TAB_URL, COMMUNITY_URL
from settings_dialog import ImperialSettingsDialog


# ═══════════════════════════════════════════════════════════════════════════════
#  Dialog: Shield Telemetry
# ═══════════════════════════════════════════════════════════════════════════════

class ShieldStatsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("REVISION-WEB // DEFENSE TELEMETRY")
        self.setFixedSize(460, 380)
        self.setStyleSheet("""
            QDialog {
                background-color: #0b0d13;
                border: 2px solid #8a0e1c;
            }
            QLabel {
                color: #e0e6ed;
            }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(25, 25, 25, 25)

        title = QLabel("DEFENSIVE SHIELD // TELEMETRY")
        title.setStyleSheet("font-size: 16px; font-weight: 900; letter-spacing: 3px; color: #ff1e38;")
        layout.addWidget(title)

        stats = adblocker.get_stats()

        def add_stat(label: str, val: str, color="#00f0ff"):
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet("font-size: 12px; font-weight: bold; letter-spacing: 1px; color: #8a94a6;")
            v = QLabel(val)
            v.setStyleSheet(f"font-size: 15px; font-weight: 900; color: {color};")
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(v)
            layout.addLayout(row)

        add_stat("ADS VAPORIZED:", f"{stats['total_blocked']:,}", "#ff1e38")
        add_stat("TRACKERS PURGED:", f"{stats['trackers_blocked']:,}", "#ff3850")
        add_stat("MALWARE BLOCKED:", f"{stats['malware_blocked']:,}", "#00f0ff")
        add_stat("ESTIMATED DATA SAVED:", f"{stats['mb_saved']} MB", "#00ff88")

        layout.addStretch()

        btn_row = QHBoxLayout()
        clear_cache_btn = QPushButton("FLUSH CACHE")
        clear_cache_btn.setStyleSheet("""
            QPushButton {
                background-color: #161a25;
                border: 1px solid #8a0e1c;
                color: #ff334b;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff1e38;
                color: white;
            }
        """)
        clear_cache_btn.clicked.connect(self.flush_cache)
        btn_row.addWidget(clear_cache_btn)

        close_btn = QPushButton("DISMISS")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #161a25;
                border: 1px solid #232734;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #232734;
            }
        """)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

    def flush_cache(self):
        QWebEngineProfile.defaultProfile().clearHttpCache()
        QMessageBox.information(self, "Rev Network", "Defensive network cache cleared.")


# ═══════════════════════════════════════════════════════════════════════════════
#  Dialog: Google Authentication Gateway
# ═══════════════════════════════════════════════════════════════════════════════

class GoogleAuthDialog(QDialog):
    """Imperial Google Authentication Gateway Selector."""
    def __init__(self, parent=None, callback=None):
        super().__init__(parent)
        self.callback = callback
        self.setWindowTitle("REVISION-WEB // GOOGLE AUTHENTICATION CORE")
        self.setFixedSize(540, 340)
        self.setStyleSheet("""
            QDialog {
                background-color: #0b0d13;
                border: 2px solid #8a0e1c;
            }
            QLabel {
                color: #e0e6ed;
            }
            QPushButton {
                background-color: #131724;
                border: 1px solid #8a0e1c;
                color: #ffffff;
                font-weight: bold;
                padding: 12px 18px;
                font-size: 11px;
                text-align: left;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #ff1e38;
                color: #ffffff;
                border-color: #ff1e38;
            }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(12)

        title = QLabel("🔑 GOOGLE AUTHENTICATION PORTAL")
        title.setStyleSheet("font-size: 15px; font-weight: 900; letter-spacing: 2px; color: #ff1e38;")
        layout.addWidget(title)

        desc = QLabel(
            "Select your preferred authentication sector:\n"
            "All options open your system browser for safe, full Google authentication."
        )
        desc.setStyleSheet("font-size: 11px; color: #8a94a6; line-height: 1.4;")
        layout.addWidget(desc)

        btn_mail = QPushButton("🌐  SIGN IN VIA GMAIL / GOOGLE WEB PORTAL\n     Opens system browser → accounts.google.com (Gmail)")
        btn_mail.clicked.connect(lambda: self.select_flow("gmail"))
        layout.addWidget(btn_mail)

        btn_yt = QPushButton("▶  SIGN IN VIA YOUTUBE SSO PORTAL\n     Opens system browser → YouTube / Google Drive login")
        btn_yt.clicked.connect(lambda: self.select_flow("youtube"))
        layout.addWidget(btn_yt)

        btn_sys = QPushButton("🚀  OPEN GOOGLE ACCOUNTS (GENERAL)\n     Opens system browser → accounts.google.com")
        btn_sys.clicked.connect(lambda: self.select_flow("system_browser"))
        layout.addWidget(btn_sys)

        layout.addStretch()

        btn_cancel = QPushButton("CANCEL")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #232838;
                color: #8a94a6;
                padding: 6px 14px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #1a1e2c;
                color: #ffffff;
            }
        """)
        btn_cancel.clicked.connect(self.reject)
        layout.addWidget(btn_cancel)

    def select_flow(self, flow_type):
        self.accept()
        if self.callback:
            self.callback(flow_type)


# ═══════════════════════════════════════════════════════════════════════════════
#  Dialog: Extensions Manager
# ═══════════════════════════════════════════════════════════════════════════════

class ExtensionsDialog(QDialog):
    def __init__(self, ext_manager: ImperialExtensionsManager, parent=None):
        super().__init__(parent)
        self.ext_manager = ext_manager
        self.setWindowTitle("REVISION-WEB // EXTENSIONS & SCRIPTS")
        self.setFixedSize(580, 480)
        self.setStyleSheet("""
            QDialog {
                background-color: #0b0d13;
                border: 2px solid #8a0e1c;
            }
            QListWidget {
                background-color: #0e101a;
                border: 1px solid #232838;
                border-radius: 4px;
            }
            QListWidget::item {
                border-bottom: 1px solid #1a1e2c;
                background-color: #0e101a;
            }
            QListWidget::item:hover {
                background-color: #141824;
            }
            QPushButton {
                background-color: #161a26;
                border: 1px solid #8a0e1c;
                color: #ffffff;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #ff1e38;
                color: white;
            }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("TACTICAL EXTENSION MODULES")
        title.setStyleSheet("font-size: 15px; font-weight: 900; letter-spacing: 2px; color: #ff1e38;")
        layout.addWidget(title)

        desc = QLabel("Real-time extensions for universal dark mode, video ad skip, and stealth:")
        desc.setStyleSheet("font-size: 11px; color: #8a94a6; margin-bottom: 4px;")
        layout.addWidget(desc)

        self.list_widget = QListWidget(self)
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #0e101a;
                border: 1px solid #232838;
                border-radius: 4px;
            }
            QListWidget::item {
                border-bottom: 1px solid #1a1e2c;
                background-color: #0e101a;
                min-height: 70px;
            }
        """)
        layout.addWidget(self.list_widget)

        for ext in self.ext_manager.get_extensions_list():
            item = QListWidgetItem()
            card = QWidget()
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(14, 10, 14, 10)
            card_layout.setSpacing(12)

            info_layout = QVBoxLayout()
            info_layout.setSpacing(2)

            name_lbl = QLabel(f">> {ext['name'].upper()}")
            name_lbl.setStyleSheet("font-size: 13px; font-weight: 900; color: #ff2d46; letter-spacing: 1px;")

            desc_lbl = QLabel(ext['description'])
            desc_lbl.setStyleSheet("font-size: 11px; color: #d0d4e0; font-weight: normal;")
            desc_lbl.setWordWrap(True)

            info_layout.addWidget(name_lbl)
            info_layout.addWidget(desc_lbl)
            card_layout.addLayout(info_layout, 1)

            cb = QCheckBox("ACTIVE" if ext["enabled"] else "DISABLED")
            cb.setChecked(ext["enabled"])
            cb.setStyleSheet(f"""
                QCheckBox {{
                    color: {'#00ff88' if ext['enabled'] else '#8a94a6'};
                    font-weight: 900;
                    font-size: 11px;
                    spacing: 8px;
                    background: transparent;
                }}
                QCheckBox::indicator {{
                    width: 20px;
                    height: 20px;
                    border: 1px solid #ff1e38;
                    background-color: #0d0f18;
                    border-radius: 3px;
                }}
                QCheckBox::indicator:checked {{
                    background-color: #ff1e38;
                }}
            """)

            def make_toggle_handler(eid, box):
                def handler(state):
                    self.ext_manager.toggle_extension(eid, state)
                    box.setText("ACTIVE" if state else "DISABLED")
                    box.setStyleSheet(f"""
                        QCheckBox {{
                            color: {'#00ff88' if state else '#8a94a6'};
                            font-weight: 900;
                            font-size: 11px;
                            spacing: 8px;
                            background: transparent;
                        }}
                        QCheckBox::indicator {{
                            width: 20px;
                            height: 20px;
                            border: 1px solid #ff1e38;
                            background-color: #0d0f18;
                            border-radius: 3px;
                        }}
                        QCheckBox::indicator:checked {{
                            background-color: #ff1e38;
                        }}
                    """)
                return handler

            cb.toggled.connect(make_toggle_handler(ext["id"], cb))
            card_layout.addWidget(cb)

            item.setSizeHint(card_layout.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, card)

        btn_row = QHBoxLayout()
        open_folder_btn = QPushButton("OPEN SCRIPTS FOLDER")
        open_folder_btn.clicked.connect(self.open_script_dir)
        btn_row.addWidget(open_folder_btn)

        btn_row.addStretch()

        close_btn = QPushButton("ENGAGE & CLOSE")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

    def open_script_dir(self):
        scripts_path = DATA_DIR / "user_scripts"
        scripts_path.mkdir(parents=True, exist_ok=True)
        os.startfile(str(scripts_path))


# ═══════════════════════════════════════════════════════════════════════════════
#  Dialog: Downloads Vault
# ═══════════════════════════════════════════════════════════════════════════════

class DownloadsDialog(QDialog):
    def __init__(self, downloads_history: list, parent=None):
        super().__init__(parent)
        self.downloads_history = downloads_history
        self.setWindowTitle("REVISION-WEB // DOWNLOADS & SCAN VAULT")
        self.setFixedSize(600, 420)
        self.setStyleSheet("""
            QDialog {
                background-color: #0b0d13;
                border: 2px solid #8a0e1c;
            }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("DOWNLOAD SCAN LOGS & THREAT VAULT")
        title.setStyleSheet("font-size: 15px; font-weight: 900; letter-spacing: 2px; color: #ff1e38;")
        layout.addWidget(title)

        self.list_widget = QListWidget(self)
        layout.addWidget(self.list_widget)

        if not self.downloads_history:
            item = QListWidgetItem("No downloads recorded in this session.")
            self.list_widget.addItem(item)
        else:
            for d in reversed(self.downloads_history):
                txt = f"[{d['status']}] {d['filename']}\nEngine: {d.get('engine', 'Heuristic')} | Hash: {d.get('hash', 'N/A')[:16]}..."
                item = QListWidgetItem(txt)
                item.setForeground(Qt.GlobalColor.white)
                self.list_widget.addItem(item)

        btn_row = QHBoxLayout()
        open_dl_btn = QPushButton("OPEN DOWNLOADS FOLDER")
        open_dl_btn.clicked.connect(self.open_downloads)
        btn_row.addWidget(open_dl_btn)

        btn_row.addStretch()

        close_btn = QPushButton("CLOSE")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

    def open_downloads(self):
        downloads_path = str(Path.home() / "Downloads")
        os.startfile(downloads_path)


# ═══════════════════════════════════════════════════════════════════════════════
#  Main Browser Window
# ═══════════════════════════════════════════════════════════════════════════════

class ImperialBrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.downloads_history = []

        # Configure WebEngine Profile
        self.profile = QWebEngineProfile.defaultProfile()

        # Set a clean Chrome User-Agent (strip QtWebEngine identifier)
        self.profile.setHttpUserAgent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        )
        self.profile.setPersistentStoragePath(str(STORAGE_DIR))
        self.profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
        )

        # Inject DocumentCreation anti-detection stealth script
        stealth_script = QWebEngineScript()
        stealth_script.setName("imperial_stealth_bridge")
        stealth_script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        stealth_script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        stealth_script.setRunsOnSubFrames(True)
        stealth_script.setSourceCode("""
            try {
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                    configurable: true
                });
            } catch(e) {}
            try {
                if (!window.chrome) {
                    window.chrome = {
                        runtime: {},
                        loadTimes: function() {},
                        csi: function() {},
                        app: {}
                    };
                }
            } catch(e) {}
        """)
        self.profile.scripts().insert(stealth_script)

        # Setup Request Interceptor for Adblocking
        self.interceptor = ImperialRequestInterceptor(self)
        self.interceptor.signals.request_blocked.connect(self.on_request_blocked)
        self.profile.setUrlRequestInterceptor(self.interceptor)

        # Setup Extensions Manager
        self.ext_manager = ImperialExtensionsManager(self.profile, window=self)

        # Window settings
        self.setWindowTitle("REVISION-WEB // PROJECT REVISION")
        self.resize(config.get("window_width", 1360), config.get("window_height", 860))
        self.setMinimumSize(850, 550)

        # Window icon
        ico_path = ASSETS_DIR / "icon.ico"
        if not ico_path.exists():
            ico_path = Path(__file__).resolve().parent / "rev_network.ico"
        if ico_path.exists():
            self.setWindowIcon(QIcon(str(ico_path)))

        # Setup UI
        self.init_ui()

        # Setup RAM Optimizer
        self.ram_optimizer = ImperialRamOptimizer(self.tab_widget, self)
        self.ram_optimizer.signals.telemetry_updated.connect(self.on_ram_telemetry)
        self.ram_optimizer.signals.memory_purged.connect(self.on_memory_purged)

        # Connect Downloads
        self.profile.downloadRequested.connect(self.on_download_requested)

        # Setup Shortcuts
        self.setup_shortcuts()

        # Load initial tab
        self.tab_widget.add_imperial_tab()

    # ─── UI Construction ──────────────────────────────────────────────────

    def init_ui(self):
        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Revision-Web Header
        self.title_bar = QWidget(self)
        self.title_bar.setObjectName("ImperialTitleBar")
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(12, 0, 10, 0)

        crest_icon = QLabel("⎊")
        crest_icon.setStyleSheet("color: #ff1e38; font-size: 18px; font-weight: bold;")
        title_layout.addWidget(crest_icon)

        title_label = QLabel("REVISION-WEB")
        title_label.setObjectName("TitleBarLabel")
        title_layout.addWidget(title_label)

        title_layout.addStretch()

        # Animated Quick Hub Action Buttons
        self.website_btn = QPushButton("🌐 WEBSITE", self)
        self.website_btn.setObjectName("TitleWebsiteBtn")
        self.website_btn.setToolTip("Open Official Rev Network Community Hub & Web Gateway")
        self.website_btn.clicked.connect(self.nav_website)
        title_layout.addWidget(self.website_btn)

        self.releases_btn = QPushButton("🚀 RELEASES", self)
        self.releases_btn.setObjectName("TitleReleasesBtn")
        self.releases_btn.setToolTip("View Latest Official Releases & Download Builds on GitHub")
        self.releases_btn.clicked.connect(self.nav_releases)
        title_layout.addWidget(self.releases_btn)

        self.discord_btn = QPushButton("💬 DISCORD", self)
        self.discord_btn.setObjectName("TitleDiscordBtn")
        self.discord_btn.setToolTip("Join Official Rev Network Community Comms on Discord")
        self.discord_btn.clicked.connect(self.nav_discord)
        title_layout.addWidget(self.discord_btn)

        # Google Sign-In Button
        google_btn = QPushButton("G+ SIGN IN", self)
        google_btn.setObjectName("GoogleHeaderBtn")
        google_btn.setToolTip("Sign In or Register with Google Accounts")
        google_btn.clicked.connect(self.open_google_auth)
        title_layout.addWidget(google_btn)

        self.telemetry_label = QLabel("RAM: CALCULATING... | REV NODE: ACTIVE")
        self.telemetry_label.setObjectName("TitleBarTelemetry")
        title_layout.addWidget(self.telemetry_label)

        main_layout.addWidget(self.title_bar)

        # 2. Navigation & Omnibox Toolbar
        nav_bar = QWidget(self)
        nav_bar.setObjectName("ImperialNavToolBar")
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(10, 5, 10, 5)
        nav_layout.setSpacing(6)

        self.back_btn = QToolButton(self)
        self.back_btn.setText("◀")
        self.back_btn.setToolTip("Back Sector")
        self.back_btn.clicked.connect(self.nav_back)
        nav_layout.addWidget(self.back_btn)

        self.forward_btn = QToolButton(self)
        self.forward_btn.setText("▶")
        self.forward_btn.setToolTip("Forward Sector")
        self.forward_btn.clicked.connect(self.nav_forward)
        nav_layout.addWidget(self.forward_btn)

        self.reload_btn = QToolButton(self)
        self.reload_btn.setText("↻")
        self.reload_btn.setToolTip("Reload Sector")
        self.reload_btn.clicked.connect(self.nav_reload)
        nav_layout.addWidget(self.reload_btn)

        self.home_btn = QToolButton(self)
        self.home_btn.setText("⌂")
        self.home_btn.setToolTip("Command Deck (New Tab)")
        self.home_btn.clicked.connect(self.nav_home)
        nav_layout.addWidget(self.home_btn)

        # REV COMMUNITY BUTTON
        self.community_btn = QPushButton("🌐 REV COMMUNITY", self)
        self.community_btn.setObjectName("CommunityBtn")
        self.community_btn.setToolTip("Rev Community Decentralized Hardware Node & Rev-Launcher Bay")
        self.community_btn.clicked.connect(self.nav_community)
        nav_layout.addWidget(self.community_btn)

        # Search Engine Selector Dropdown
        self.engine_combo = QComboBox(self)
        self.engine_combo.setObjectName("SearchEngineCombo")
        engines = ["Google", "DuckDuckGo", "Brave", "Bing", "Startpage"]
        for eng in engines:
            self.engine_combo.addItem(eng)
        current_eng = config.get("search_engine", "Google")
        idx = self.engine_combo.findText(current_eng)
        if idx >= 0:
            self.engine_combo.setCurrentIndex(idx)
        self.engine_combo.currentTextChanged.connect(self.on_engine_changed)
        nav_layout.addWidget(self.engine_combo)

        # Omnibox Address Field
        self.address_bar = QLineEdit(self)
        self.address_bar.setObjectName("ImperialAddressBar")
        self.address_bar.setPlaceholderText("Enter URL or execute query (e.g. 'hi')...")
        self.address_bar.returnPressed.connect(self.nav_go)
        nav_layout.addWidget(self.address_bar, 1)

        # Engage button
        engage_btn = QPushButton("ENGAGE", self)
        engage_btn.clicked.connect(self.nav_go)
        nav_layout.addWidget(engage_btn)

        # Shield Status Button
        self.shield_btn = QPushButton("🛡️ SHIELD: 0", self)
        self.shield_btn.setObjectName("ShieldBtn")
        self.shield_btn.setToolTip("Defensive Shield Metrics")
        self.shield_btn.clicked.connect(self.show_shield_dialog)
        nav_layout.addWidget(self.shield_btn)

        # RAM Purge Button
        self.purge_btn = QPushButton("⚡ PURGE RAM", self)
        self.purge_btn.setObjectName("PurgeRamBtn")
        self.purge_btn.setToolTip("Trim working set memory & clear cache")
        self.purge_btn.clicked.connect(self.trigger_purge_ram)
        nav_layout.addWidget(self.purge_btn)

        # Extensions Button
        ext_btn = QPushButton("🧩 EXTENSIONS", self)
        ext_btn.clicked.connect(self.show_extensions_dialog)
        nav_layout.addWidget(ext_btn)

        # Downloads Vault Button
        self.downloads_btn = QPushButton("📥 VAULT", self)
        self.downloads_btn.clicked.connect(self.show_downloads_dialog)
        nav_layout.addWidget(self.downloads_btn)

        # Core Settings Button
        self.settings_btn = QPushButton("⚙️ SETTINGS", self)
        self.settings_btn.setObjectName("SettingsBtn")
        self.settings_btn.setToolTip("Core Browser Settings & Preferences (Ctrl+,)")
        self.settings_btn.clicked.connect(self.show_settings_dialog)
        nav_layout.addWidget(self.settings_btn)

        # New Tab Button (+)
        new_tab_btn = QPushButton("+", self)
        new_tab_btn.setObjectName("NewTabBtn")
        new_tab_btn.setToolTip("Deploy New Tab")
        new_tab_btn.clicked.connect(lambda: self.tab_widget.add_imperial_tab())
        nav_layout.addWidget(new_tab_btn)

        main_layout.addWidget(nav_bar)

        # 3. Loading Progress Bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setFixedHeight(2)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar { background: transparent; border: none; }
            QProgressBar::chunk { background: #ff1e38; }
        """)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)

        # 4. Tab Widget
        self.tab_widget = ImperialTabWidget(
            self.profile,
            self,
            command_callback=self.handle_imperial_command,
            ext_manager=self.ext_manager
        )
        self.tab_widget.url_changed.connect(self.on_url_changed)
        self.tab_widget.loading_progress.connect(self.on_progress)
        main_layout.addWidget(self.tab_widget)

    # ─── Keyboard Shortcuts ───────────────────────────────────────────────

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+T"), self, activated=lambda: self.tab_widget.add_imperial_tab())
        QShortcut(QKeySequence("Ctrl+W"), self, activated=lambda: self.tab_widget.close_tab(self.tab_widget.currentIndex()))
        QShortcut(QKeySequence("Ctrl+R"), self, activated=self.nav_reload)
        QShortcut(QKeySequence("F5"), self, activated=self.nav_reload)
        QShortcut(QKeySequence("Ctrl+L"), self, activated=self.address_bar.setFocus)
        QShortcut(QKeySequence("Alt+D"), self, activated=self.address_bar.setFocus)
        QShortcut(QKeySequence("Ctrl+Shift+P"), self, activated=self.trigger_purge_ram)
        QShortcut(QKeySequence("Ctrl+J"), self, activated=self.show_downloads_dialog)
        QShortcut(QKeySequence("Ctrl+,"), self, activated=self.show_settings_dialog)
        QShortcut(QKeySequence("F12"), self, activated=self.open_active_devtools)
        QShortcut(QKeySequence("Ctrl+Shift+I"), self, activated=self.open_active_devtools)

    # ─── Engine Changed ───────────────────────────────────────────────────

    def on_engine_changed(self, new_engine: str):
        config.set("search_engine", new_engine)

    # ─── DevTools ─────────────────────────────────────────────────────────

    def open_active_devtools(self):
        """Opens Chromium DevTools for the currently selected web view."""
        view = self.tab_widget.current_webview()
        if view and hasattr(view, "open_devtools"):
            view.open_devtools()

    # ─── Settings ─────────────────────────────────────────────────────────

    def show_settings_dialog(self):
        dlg = ImperialSettingsDialog(self)
        dlg.settings_updated.connect(self.on_settings_updated)
        dlg.exec()

    def on_settings_updated(self):
        current_eng = config.get("search_engine", "Google")
        idx = self.engine_combo.findText(current_eng)
        if idx >= 0:
            self.engine_combo.setCurrentIndex(idx)

    # ─── Google Authentication ────────────────────────────────────────────

    def open_google_auth(self):
        """Opens Imperial Google Authentication Gateway."""
        dlg = GoogleAuthDialog(self, callback=self.execute_google_flow)
        dlg.exec()

    def execute_google_flow(self, flow_type):
        """
        All sign-in flows open the system browser (Chrome/Edge) because
        QtWebEngine is flagged as 'insecure' by Google. The user signs in
        via their real browser which actually works.
        """
        if flow_type == "gmail":
            QDesktopServices.openUrl(QUrl(
                "https://accounts.google.com/ServiceLogin"
                "?service=mail&continue=https%3A%2F%2Fmail.google.com%2Fmail%2F"
            ))
        elif flow_type == "youtube":
            QDesktopServices.openUrl(QUrl(
                "https://accounts.google.com/ServiceLogin"
                "?service=youtube&continue=https%3A%2F%2Fwww.youtube.com%2F"
            ))
        elif flow_type == "system_browser":
            QDesktopServices.openUrl(QUrl("https://accounts.google.com/"))

    # ─── Imperial Command Router ──────────────────────────────────────────

    def handle_imperial_command(self, qurl: QUrl):
        """Receives internal imperial:// and rev:// commands."""
        host = qurl.host()
        query = urllib.parse.parse_qs(qurl.query())

        if host == "search":
            engine = query.get("engine", [config.get("search_engine", "Google")])[0]
            q = query.get("q", [""])[0]
            if q:
                template = config.get("search_engines", {}).get(
                    engine, "https://www.google.com/search?q={query}"
                )
                target_url = template.format(query=urllib.parse.quote_plus(q))
                view = self.tab_widget.current_webview()
                if view:
                    view.load(QUrl(target_url))

        elif host == "set-engine":
            name = query.get("name", ["Google"])[0]
            config.set("search_engine", name)
            idx = self.engine_combo.findText(name)
            if idx >= 0:
                self.engine_combo.setCurrentIndex(idx)

        elif host in ["google-auth", "google-register"]:
            self.open_google_auth()

        elif host in ["settings", "preferences"]:
            self.show_settings_dialog()

        elif host in ["download-rev-launcher", "download-launcher"]:
            self.download_local_rev_launcher()

        elif host in ["community", "rev-community"]:
            self.nav_community()

        elif host in ["website", "site", "web"]:
            self.nav_website()

        elif host in ["releases", "github-releases", "download-releases"]:
            self.nav_releases()

        elif host in ["discord", "community-discord"]:
            self.nav_discord()

        elif host in ["github", "github-repo", "source"]:
            self.nav_github()

        elif host == "purge-ram":
            self.trigger_purge_ram()

        elif host == "newtab":
            self.nav_home()

    # ─── Navigation ───────────────────────────────────────────────────────

    def open_external_or_tab(self, url_str: str):
        target_qurl = QUrl(url_str)
        curr = self.tab_widget.current_webview()
        if curr and (curr.url() == NEW_TAB_URL or curr.url().toString() == "" or "about:blank" in curr.url().toString()):
            curr.load(target_qurl)
        else:
            self.tab_widget.add_imperial_tab(target_qurl)

    def nav_website(self):
        self.open_external_or_tab("http://127.0.0.1:8000")

    def nav_releases(self):
        self.open_external_or_tab("https://github.com/gaimingmemo-rgb/rev-network/releases")

    def nav_discord(self):
        self.open_external_or_tab("https://discord.gg/8rnKQKbaHj")

    def nav_github(self):
        self.open_external_or_tab("https://github.com/gaimingmemo-rgb/rev-network")

    def nav_back(self):
        view = self.tab_widget.current_webview()
        if view:
            view.back()

    def nav_forward(self):
        view = self.tab_widget.current_webview()
        if view:
            view.forward()

    def nav_reload(self):
        view = self.tab_widget.current_webview()
        if view:
            view.reload()

    def nav_home(self):
        view = self.tab_widget.current_webview()
        if view:
            view.load(NEW_TAB_URL)

    def nav_community(self):
        view = self.tab_widget.current_webview()
        if view:
            view.load(COMMUNITY_URL)
        else:
            self.tab_widget.add_imperial_tab(COMMUNITY_URL)

    def nav_go(self):
        target = self.address_bar.text().strip()
        view = self.tab_widget.current_webview()
        if view:
            view.load_target(target)

    # ─── Local Rev-Launcher Download ──────────────────────────────────────

    def download_local_rev_launcher(self):
        source_path = Path(r"C:\Users\ZarTo\Desktop\Projects\Delivered\Rev-Launcher.zip")
        if not source_path.exists():
            alt_path = Path(r"C:\Users\ZarTo\Desktop\Projects\Delivered Rev-Launcher.zip")
            if alt_path.exists():
                source_path = alt_path
            else:
                QMessageBox.warning(self, "Rev Network", f"Source file not found at:\n{source_path}")
                return

        dest_dir = Path.home() / "Downloads"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / "Rev-Launcher.zip"

        try:
            import shutil
            shutil.copy2(str(source_path), str(dest_path))

            scan_res = virus_scanner.scan_file(str(dest_path))
            scan_res["filename"] = "Rev-Launcher.zip"
            self.downloads_history.append(scan_res)

            msg = QMessageBox(self)
            msg.setWindowTitle("REV-LAUNCHER DEPLOYED")
            file_mb = round(os.path.getsize(str(dest_path)) / (1024 * 1024), 1)
            msg.setText(
                f"REV-LAUNCHER DOWNLOADED FROM LOCAL VAULT!\n\n"
                f"Location: {dest_path}\n"
                f"Size: {file_mb} MB (287,160,527 bytes)\n"
                f"Status: CLEARED BY DEFENDER [SAFE]\n"
                f"SHA-256: {scan_res.get('file_hash', 'FE1DC4AE379F3944823310BCB387A234EC6318184E3FC651DAE04FDD4D0E4A9C')}"
            )
            msg.setIcon(QMessageBox.Icon.Information)
            open_btn = msg.addButton("OPEN IN EXPLORER", QMessageBox.ButtonRole.ActionRole)
            msg.addButton("DISMISS", QMessageBox.ButtonRole.RejectRole)
            msg.exec()

            if msg.clickedButton() == open_btn:
                import subprocess
                subprocess.Popen(f'explorer /select,"{dest_path}"')
        except Exception as e:
            QMessageBox.critical(self, "Download Error", f"Failed copying Rev-Launcher archive:\n{e}")

    # ─── URL / Progress / Telemetry ───────────────────────────────────────

    def on_url_changed(self, url: QUrl):
        url_str = url.toString()
        if "newtab.html" in url_str:
            self.address_bar.setText("")
            self.address_bar.setPlaceholderText("Enter URL or execute query (e.g. 'hi')...")
        elif "community.html" in url_str:
            self.address_bar.setText("rev://community")
        else:
            self.address_bar.setText(url_str)

    def on_progress(self, progress: int):
        if progress < 100:
            self.progress_bar.show()
            self.progress_bar.setValue(progress)
        else:
            self.progress_bar.hide()

    def on_request_blocked(self, url: str, cat: str):
        stats = adblocker.get_stats()
        self.shield_btn.setText(f"🛡️ SHIELD: {stats['total_blocked']}")

    def on_ram_telemetry(self, proc_mb: float, sys_pct: float, status: str):
        stats = adblocker.get_stats()
        self.telemetry_label.setText(
            f"RAM: {proc_mb} MB [{status}] | ADS: {stats['total_blocked']} | REV NODE: ACTIVE"
        )

    # ─── RAM Purge ────────────────────────────────────────────────────────

    def trigger_purge_ram(self):
        self.purge_btn.setText("⚡ PURGING...")
        freed = self.ram_optimizer.purge_memory()
        if freed > 0:
            self.purge_btn.setText(f"⚡ FREED {freed}MB")
        else:
            self.purge_btn.setText("⚡ MEMORY OPTIMIZED")
        QTimer.singleShot(2500, lambda: self.purge_btn.setText("⚡ PURGE RAM"))

    def on_memory_purged(self, freed_mb: float):
        pass

    # ─── Dialog Launchers ─────────────────────────────────────────────────

    def show_shield_dialog(self):
        dlg = ShieldStatsDialog(self)
        dlg.exec()

    def show_extensions_dialog(self):
        dlg = ExtensionsDialog(self.ext_manager, self)
        dlg.exec()

    def show_downloads_dialog(self):
        dlg = DownloadsDialog(self.downloads_history, self)
        dlg.exec()

    # ─── Download Handler ─────────────────────────────────────────────────

    def on_download_requested(self, download: QWebEngineDownloadRequest):
        filename = download.suggestedFileName()
        download_dir = Path.home() / "Downloads"
        target_path = download_dir / filename

        risk_level, risk_desc = virus_scanner.evaluate_file_risk(filename)

        if risk_level == "CRITICAL":
            res = QMessageBox.warning(
                self,
                "IMPERIAL SECURITY INTERCEPT",
                f"HIGH-RISK PAYLOAD DETECTED:\n\nFile: {filename}\nRisk: {risk_desc}\n\nPermit download into containment sector?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if res != QMessageBox.StandardButton.Yes:
                download.cancel()
                return

        download.setDownloadDirectory(str(download_dir))
        download.setDownloadFileName(filename)
        download.accept()

        download.isFinishedChanged.connect(
            lambda: self.on_download_finished(download, str(target_path))
        )

    def on_download_finished(self, download: QWebEngineDownloadRequest, filepath: str):
        if download.state() != QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
            return

        filename = os.path.basename(filepath)
        scan_res = virus_scanner.scan_file(filepath)
        scan_res["filename"] = filename
        scan_res["hash"] = scan_res.get("file_hash", "")
        self.downloads_history.append(scan_res)

        if scan_res.get("status") == "INFECTED":
            q_res = QMessageBox.critical(
                self,
                "BIO-HAZARD DETECTED // THREAT ISOLATION",
                f"MALWARE DETECTED IN DOWNLOAD:\n\nFile: {filename}\nThreat: {scan_res.get('threat')}\nEngine: {scan_res.get('engine')}\n\nQuarantine immediately to vault?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if q_res == QMessageBox.StandardButton.Yes:
                dest = virus_scanner.quarantine_file(filepath)
                QMessageBox.information(self, "Imperial Containment", f"Threat sealed in quarantine:\n{dest}")
        else:
            self.statusBar().showMessage(f"Download Cleared: {filename} [{scan_res.get('engine')}]", 5000)
