import os
import urllib.parse
from pathlib import Path
from PySide6.QtCore import QUrl, Signal, QObject, Qt, QSize
from PySide6.QtWidgets import (
    QMenu, QDialog, QVBoxLayout, QMessageBox
)
from PySide6.QtGui import QAction, QContextMenuEvent, QKeySequence, QShortcut
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import (
    QWebEnginePage, QWebEngineSettings, QWebEngineProfile
)
from config import config, ASSETS_DIR, STORAGE_DIR

NEW_TAB_URL = QUrl.fromLocalFile(str(ASSETS_DIR / "newtab.html"))
COMMUNITY_URL = QUrl.fromLocalFile(str(ASSETS_DIR / "community.html"))

class ImperialDevToolsDialog(QDialog):
    """Dedicated high-tech DevTools Inspector window."""
    def __init__(self, inspected_page: QWebEnginePage, parent=None):
        super().__init__(parent)
        self.setWindowTitle("REV NETWORK // INSPECT ELEMENT & CHROMIUM DEVTOOLS")
        self.resize(1020, 680)
        self.setStyleSheet("""
            QDialog {
                background-color: #0b0d13;
                border: 2px solid #8a0e1c;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.devtools_view = QWebEngineView(self)
        inspected_page.setDevToolsPage(self.devtools_view.page())
        layout.addWidget(self.devtools_view)

class ImperialWebPage(QWebEnginePage):
    def __init__(self, profile, parent=None, new_tab_callback=None, command_callback=None):
        super().__init__(profile, parent)
        self.new_tab_callback = new_tab_callback
        self.command_callback = command_callback

        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebRTCPublicInterfacesOnly, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.DnsPrefetchEnabled, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        # Allow file:// pages (community.html) to fetch from http://127.0.0.1:8765
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)

    def createWindow(self, window_type):
        if self.new_tab_callback:
            return self.new_tab_callback(window_type)
        return super().createWindow(window_type)

    def acceptNavigationRequest(self, url: QUrl, nav_type, is_main_frame: bool) -> bool:
        url_str = url.toString()

        if url.scheme() in ["imperial", "rev"]:
            if self.command_callback:
                self.command_callback(url)
            return False

        return super().acceptNavigationRequest(url, nav_type, is_main_frame)

class ImperialWebView(QWebEngineView):
    def __init__(self, profile, parent=None, new_tab_callback=None, command_callback=None, ext_manager=None):
        super().__init__(parent)
        self.ext_manager = ext_manager
        self.custom_page = ImperialWebPage(profile, self, new_tab_callback, command_callback)
        self.setPage(self.custom_page)
        self._devtools_dlg = None

        self.loadFinished.connect(self.on_load_finished)

        # Setup F12 and Ctrl+Shift+I shortcut for DevTools
        f12_shortcut = QShortcut(QKeySequence("F12"), self, activated=self.open_devtools)
        f12_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        
        inspect_shortcut = QShortcut(QKeySequence("Ctrl+Shift+I"), self, activated=self.open_devtools)
        inspect_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)

    def on_load_finished(self, ok: bool):
        if ok:
            if self.ext_manager:
                self.ext_manager.apply_to_view(self)

    def open_devtools(self):
        """Opens or focuses the Chromium DevTools Inspector for the current page."""
        if self._devtools_dlg is None or not self._devtools_dlg.isVisible():
            self._devtools_dlg = ImperialDevToolsDialog(self.page(), self.window())
            self._devtools_dlg.show()
        else:
            self._devtools_dlg.activateWindow()
            self._devtools_dlg.raise_()

    def view_source(self):
        """Views the HTML source of the active page."""
        curr_url = self.url().toString()
        if curr_url and not curr_url.startswith("view-source:"):
            self.load(QUrl(f"view-source:{curr_url}"))

    def contextMenuEvent(self, event: QContextMenuEvent):
        """Custom Imperial Context Menu with Inspect Element, Navigation, and Source."""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #0d0f17;
                border: 1px solid #8a0e1c;
                color: #e0e6ed;
                padding: 5px;
            }
            QMenu::item {
                padding: 7px 24px;
                font-weight: bold;
                font-size: 11px;
                border-radius: 2px;
            }
            QMenu::item:selected {
                background-color: #ff1e38;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background-color: #212636;
                margin: 4px 8px;
            }
        """)

        back_act = menu.addAction("◀   Back")
        back_act.setEnabled(self.history().canGoBack())
        back_act.triggered.connect(self.back)

        fwd_act = menu.addAction("▶   Forward")
        fwd_act.setEnabled(self.history().canGoForward())
        fwd_act.triggered.connect(self.forward)

        reload_act = menu.addAction("↻   Reload")
        reload_act.triggered.connect(self.reload)

        menu.addSeparator()

        copy_act = menu.addAction("📋   Copy Selection / Link")
        copy_act.triggered.connect(lambda: self.triggerPageAction(QWebEnginePage.WebAction.Copy))

        select_all_act = menu.addAction("📑   Select All")
        select_all_act.triggered.connect(lambda: self.triggerPageAction(QWebEnginePage.WebAction.SelectAll))

        menu.addSeparator()

        source_act = menu.addAction("📄   View Page Source")
        source_act.triggered.connect(self.view_source)

        inspect_act = menu.addAction("🔍   Inspect Element   (F12)")
        inspect_act.triggered.connect(self.open_devtools)

        menu.exec(event.globalPos())

    def load_target(self, target: str):
        target = target.strip()
        if not target or target in ["about:blank", "imperial://newtab", "rev://newtab"]:
            self.load(NEW_TAB_URL)
            return

        if target in ["imperial://community", "rev://community"]:
            self.load(COMMUNITY_URL)
            return

        if target in ["imperial://settings", "rev://settings"]:
            # Trigger settings dialog via command callback
            if self.custom_page.command_callback:
                self.custom_page.command_callback(QUrl("imperial://settings"))
            return

        # Smart routing for Revision Website / DDNS / VPN / Community
        lower_t = target.lower()
        if "rev-network.ddns.net" in lower_t:
            # Seamless loopback routing to Origin Server (bypasses router NAT loopback timeout)
            self.load(QUrl("http://127.0.0.1:8000"))
            return

        if lower_t in ["rev://website", "imperial://website", "website", "hub", "portal"]:
            self.load(QUrl("http://127.0.0.1:8000"))
            return

        if target.startswith("http://") or target.startswith("https://") or target.startswith("file://") or target.startswith("view-source:"):
            self.load(QUrl(target))
        elif ":" in target and not "/" in target:
            self.load(QUrl(f"http://{target}"))
        elif "." in target and not " " in target:
            self.load(QUrl(f"https://{target}"))
        else:
            engine = config.get("search_engine", "Google")
            template = config.get("search_engines", {}).get(engine, "https://www.google.com/search?q={query}")
            url_str = template.format(query=urllib.parse.quote_plus(target))
            self.load(QUrl(url_str))
