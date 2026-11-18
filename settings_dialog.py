"""
Rev Network // Imperial Core Configuration & Settings Dialog
"""

import os
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QComboBox, QTabWidget, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtWebEngineCore import QWebEngineProfile
from config import config, DATA_DIR
from adblocker import adblocker

class ImperialSettingsDialog(QDialog):
    settings_updated = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("REV NETWORK // CORE CONFIGURATION")
        self.setFixedSize(620, 520)
        self.setStyleSheet("""
            QDialog {
                background-color: #0b0c13;
                border: 2px solid #8a0e1c;
            }
            QLabel {
                color: #e0e6ed;
                font-size: 12px;
            }
            QTabWidget::pane {
                border: 1px solid #232838;
                background-color: #10121c;
                top: -1px;
            }
            QTabBar::tab {
                background-color: #0d0f17;
                color: #8d94a5;
                font-weight: bold;
                font-size: 11px;
                padding: 10px 18px;
                border: 1px solid #232838;
                border-bottom: none;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #10121c;
                color: #ff2d46;
                border-top: 2px solid #ff1e38;
            }
            QTabBar::tab:hover {
                color: #ffffff;
            }
            QCheckBox {
                color: #e0e6ed;
                font-size: 12px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #ff1e38;
                background-color: #0b0d14;
                border-radius: 2px;
            }
            QCheckBox::indicator:checked {
                background-color: #ff1e38;
                image: none;
            }
            QComboBox {
                background-color: #151824;
                border: 1px solid #8a0e1c;
                color: #ffffff;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 2px;
            }
            QLineEdit {
                background-color: #151824;
                border: 1px solid #282d3e;
                color: #ffffff;
                padding: 6px 10px;
                font-size: 11px;
                border-radius: 2px;
            }
            QLineEdit:focus {
                border: 1px solid #ff1e38;
            }
            QPushButton {
                background-color: #181c2b;
                border: 1px solid #8a0e1c;
                color: #ffffff;
                font-weight: bold;
                font-size: 11px;
                padding: 8px 18px;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #ff1e38;
                color: #ffffff;
            }
        """)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # Header Title
        title_box = QHBoxLayout()
        icon_lbl = QLabel("⚙️")
        icon_lbl.setStyleSheet("font-size: 18px;")
        title_box.addWidget(icon_lbl)

        title = QLabel("SYSTEM CONFIGURATION // PREFERENCES")
        title.setStyleSheet("font-size: 15px; font-weight: 900; letter-spacing: 2px; color: #ff1e38;")
        title_box.addWidget(title)
        title_box.addStretch()
        main_layout.addLayout(title_box)

        # Tab Widget
        tabs = QTabWidget(self)

        # ── Tab 1: General & Search ──
        tab_general = QWidget()
        gen_layout = QVBoxLayout(tab_general)
        gen_layout.setContentsMargins(18, 18, 18, 18)
        gen_layout.setSpacing(14)

        gen_layout.addWidget(QLabel("PRIMARY SEARCH ENGINE:"))
        self.search_combo = QComboBox()
        for eng in ["Google", "DuckDuckGo", "Brave", "Bing", "Startpage"]:
            self.search_combo.addItem(eng)
        curr_eng = config.get("search_engine", "Google")
        idx = self.search_combo.findText(curr_eng)
        if idx >= 0:
            self.search_combo.setCurrentIndex(idx)
        gen_layout.addWidget(self.search_combo)

        gen_layout.addWidget(QLabel("DEFAULT COMMAND DECK (HOMEPAGE):"))
        self.home_input = QLineEdit(config.get("homepage", "imperial://newtab"))
        gen_layout.addWidget(self.home_input)

        gen_layout.addStretch()
        tabs.addTab(tab_general, "🌐 GENERAL")

        # ── Tab 2: Imperial Shield & Defense ──
        tab_defense = QWidget()
        def_layout = QVBoxLayout(tab_defense)
        def_layout.setContentsMargins(18, 18, 18, 18)
        def_layout.setSpacing(12)

        self.chk_adblock = QCheckBox("Enable Imperial AdBlock Shield (100+ Network Blacklist)")
        self.chk_adblock.setChecked(config.get("adblock_enabled", True))
        def_layout.addWidget(self.chk_adblock)

        self.chk_cosmetic = QCheckBox("Enable Cosmetic Ad Filtering (Remove Empty Ad Frames)")
        self.chk_cosmetic.setChecked(config.get("cosmetic_filtering", True))
        def_layout.addWidget(self.chk_cosmetic)

        self.chk_trackers = QCheckBox("Block Invasive Telemetry & Tracking Pixels")
        self.chk_trackers.setChecked(config.get("tracker_blocking", True))
        def_layout.addWidget(self.chk_trackers)

        self.chk_defender = QCheckBox("Scan Incoming Downloads with Windows Defender (MpCmdRun)")
        self.chk_defender.setChecked(config.get("windows_defender_scan", True))
        def_layout.addWidget(self.chk_defender)

        def_layout.addStretch()
        tabs.addTab(tab_defense, "🛡️ DEFENSE")

        # ── Tab 3: RAM & Hardware Optimization ──
        tab_perf = QWidget()
        perf_layout = QVBoxLayout(tab_perf)
        perf_layout.setContentsMargins(18, 18, 18, 18)
        perf_layout.setSpacing(14)

        self.chk_ram_saver = QCheckBox("Enable Auto-RAM Saver (WorkingSet Memory Purge)")
        self.chk_ram_saver.setChecked(config.get("ram_saver_enabled", True))
        perf_layout.addWidget(self.chk_ram_saver)

        perf_layout.addWidget(QLabel("INACTIVE TAB HIBERNATION TIMEOUT:"))
        self.hib_combo = QComboBox()
        self.hib_combo.addItem("2 Minutes", 2)
        self.hib_combo.addItem("5 Minutes", 5)
        self.hib_combo.addItem("10 Minutes", 10)
        self.hib_combo.addItem("30 Minutes", 30)
        self.hib_combo.addItem("Never (Keep All Tabs Active)", 999999)
        curr_min = config.get("tab_hibernation_minutes", 5)
        for i in range(self.hib_combo.count()):
            if self.hib_combo.itemData(i) == curr_min:
                self.hib_combo.setCurrentIndex(i)
                break
        perf_layout.addWidget(self.hib_combo)

        perf_layout.addWidget(QLabel("MAX CHROMIUM RENDERER PROCESSES:"))
        self.proc_combo = QComboBox()
        self.proc_combo.addItem("1 (Ultra-Low Memory Footprint)", 1)
        self.proc_combo.addItem("2 (Balanced Tactical Profile)", 2)
        self.proc_combo.addItem("3 (Standard Imperial Default)", 3)
        self.proc_combo.addItem("5 (High Performance Workstation)", 5)
        curr_procs = config.get("max_renderer_processes", 3)
        for i in range(self.proc_combo.count()):
            if self.proc_combo.itemData(i) == curr_procs:
                self.proc_combo.setCurrentIndex(i)
                break
        perf_layout.addWidget(self.proc_combo)

        perf_layout.addStretch()
        tabs.addTab(tab_perf, "⚡ HARDWARE & RAM")

        # ── Tab 4: Privacy & Cache Purge ──
        tab_privacy = QWidget()
        priv_layout = QVBoxLayout(tab_privacy)
        priv_layout.setContentsMargins(18, 18, 18, 18)
        priv_layout.setSpacing(14)

        lbl_desc = QLabel("Tactical storage actions to purge caches, cookies, and telemetry records:")
        lbl_desc.setStyleSheet("color: #8d94a5; font-size: 11px;")
        priv_layout.addWidget(lbl_desc)

        btn_clear_cache = QPushButton("FLUSH HTTP DISK & MEMORY CACHE")
        btn_clear_cache.clicked.connect(self.clear_cache)
        priv_layout.addWidget(btn_clear_cache)

        btn_clear_cookies = QPushButton("PURGE BROWSER COOKIES & SESSION TOKENS")
        btn_clear_cookies.clicked.connect(self.clear_cookies)
        priv_layout.addWidget(btn_clear_cookies)

        btn_reset_ad_stats = QPushButton("RESET DEFENSIVE SHIELD COUNTERS")
        btn_reset_ad_stats.clicked.connect(self.reset_stats)
        priv_layout.addWidget(btn_reset_ad_stats)

        priv_layout.addStretch()
        tabs.addTab(tab_privacy, "🧹 PURGE DATA")

        main_layout.addWidget(tabs)

        # Bottom Buttons
        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("CANCEL")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_box.addStretch()

        btn_save = QPushButton("SAVE & APPLY CONFIGURATION")
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #ff1e38;
                color: #ffffff;
                font-weight: 900;
                padding: 9px 24px;
            }
            QPushButton:hover {
                background-color: #ff3850;
            }
        """)
        btn_save.clicked.connect(self.save_settings)
        btn_box.addWidget(btn_save)

        main_layout.addLayout(btn_box)

    def clear_cache(self):
        QWebEngineProfile.defaultProfile().clearHttpCache()
        QMessageBox.information(self, "Cache Cleared", "HTTP and shader cache flushed.")

    def clear_cookies(self):
        cookie_store = QWebEngineProfile.defaultProfile().cookieStore()
        cookie_store.deleteAllCookies()
        QMessageBox.information(self, "Cookies Purged", "All cookies and session tokens cleared.")

    def reset_stats(self):
        adblocker.blocked_ads = 0
        adblocker.blocked_trackers = 0
        adblocker.blocked_malware = 0
        adblocker.bytes_saved = 0
        QMessageBox.information(self, "Shield Counters Reset", "Shield telemetry set to 0.")

    def save_settings(self):
        config.set("search_engine", self.search_combo.currentText())
        config.set("homepage", self.home_input.text().strip() or "imperial://newtab")
        config.set("adblock_enabled", self.chk_adblock.isChecked())
        config.set("cosmetic_filtering", self.chk_cosmetic.isChecked())
        config.set("tracker_blocking", self.chk_trackers.isChecked())
        config.set("windows_defender_scan", self.chk_defender.isChecked())
        config.set("ram_saver_enabled", self.chk_ram_saver.isChecked())
        config.set("tab_hibernation_minutes", self.hib_combo.currentData())
        config.set("max_renderer_processes", self.proc_combo.currentData())

        adblocker.enabled = self.chk_adblock.isChecked()

        self.settings_updated.emit()
        self.accept()
