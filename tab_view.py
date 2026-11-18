from datetime import datetime
from PySide6.QtWidgets import (
    QTabWidget, QWidget, QVBoxLayout, QLabel, QPushButton, QTabBar,
    QMenu, QMessageBox
)
from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineProfile
from web_engine import ImperialWebView, NEW_TAB_URL

class HibernatedTabWidget(QWidget):
    """Ultra-low RAM placeholder for hibernated inactive tabs."""
    awaken_requested = Signal()

    def __init__(self, title: str, url: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.url = url
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(15)

        icon_label = QLabel("⚡")
        icon_label.setStyleSheet("font-size: 48px; color: #ff1e38;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel("TAB HIBERNATED // RAM PRESERVED")
        title_label.setStyleSheet("font-size: 16px; font-weight: 900; letter-spacing: 2px; color: #ffffff;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        desc_label = QLabel(f"Target: {self.url}\nRenderer thread terminated to maintain ultra-low memory footprint.")
        desc_label.setStyleSheet("font-size: 12px; color: #8a94a6; text-align: center;")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        wake_btn = QPushButton("RE-AWAKEN SYSTEM")
        wake_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff1e38;
                color: #ffffff;
                font-weight: 800;
                font-size: 12px;
                letter-spacing: 2px;
                padding: 10px 24px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #ff3850;
            }
        """)
        wake_btn.clicked.connect(self.awaken_requested.emit)

        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addWidget(wake_btn)

class ImperialTabWidget(QTabWidget):
    url_changed = Signal(QUrl)
    title_changed = Signal(str)
    loading_progress = Signal(int)

    def __init__(self, profile: QWebEngineProfile, parent=None, command_callback=None, ext_manager=None):
        super().__init__(parent)
        self.profile = profile
        self.command_callback = command_callback
        self.ext_manager = ext_manager
        self.tab_metadata = {}

        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDocumentMode(True)

        self.tabCloseRequested.connect(self.close_tab)
        self.currentChanged.connect(self.on_current_changed)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def add_imperial_tab(self, url: QUrl = None, activate: bool = True) -> int:
        if url is None:
            url = NEW_TAB_URL

        web_view = ImperialWebView(
            self.profile,
            self,
            new_tab_callback=self.handle_popup_tab,
            command_callback=self.command_callback,
            ext_manager=self.ext_manager
        )
        web_view.load(url)

        index = self.addTab(web_view, "Imperial Core")
        self.tab_metadata[index] = {
            "title": "Imperial Core",
            "url": url.toString(),
            "hibernated": False,
            "last_active": datetime.now(),
            "webview": web_view
        }

        # Connect signals
        web_view.titleChanged.connect(lambda t, idx=index: self.on_tab_title_changed(idx, t))
        web_view.urlChanged.connect(lambda u, idx=index: self.on_tab_url_changed(idx, u))
        web_view.loadProgress.connect(lambda p, idx=index: self.on_tab_progress(idx, p))

        if activate:
            self.setCurrentIndex(index)

        return index

    def handle_popup_tab(self, window_type):
        new_idx = self.add_imperial_tab(NEW_TAB_URL, activate=True)
        return self.tab_metadata[new_idx]["webview"].page()

    def on_tab_title_changed(self, idx: int, title: str):
        if idx in self.tab_metadata:
            self.tab_metadata[idx]["title"] = title
            display_title = title if len(title) <= 22 else title[:20] + "..."
            self.setTabText(idx, display_title)
            self.setTabToolTip(idx, title)
            if idx == self.currentIndex():
                self.title_changed.emit(title)

    def on_tab_url_changed(self, idx: int, url: QUrl):
        if idx in self.tab_metadata:
            self.tab_metadata[idx]["url"] = url.toString()
            if idx == self.currentIndex():
                self.url_changed.emit(url)

    def on_tab_progress(self, idx: int, progress: int):
        if idx == self.currentIndex():
            self.loading_progress.emit(progress)

    def on_current_changed(self, index: int):
        if index < 0 or index not in self.tab_metadata:
            return

        meta = self.tab_metadata[index]
        meta["last_active"] = datetime.now()

        if meta.get("hibernated", False):
            self.awaken_tab(index)

        current_view = meta.get("webview")
        if current_view and isinstance(current_view, QWebEngineView):
            self.url_changed.emit(current_view.url())
            self.title_changed.emit(current_view.title())

    def hibernate_tab(self, index: int):
        if index == self.currentIndex() or index not in self.tab_metadata:
            return

        meta = self.tab_metadata[index]
        if meta.get("hibernated", False):
            return

        url_str = meta["url"]
        title = meta["title"]

        old_view = meta.get("webview")
        if old_view:
            old_view.deleteLater()

        meta["webview"] = None
        meta["hibernated"] = True

        placeholder = HibernatedTabWidget(title, url_str)
        placeholder.awaken_requested.connect(lambda idx=index: self.awaken_tab(idx))

        self.removeTab(index)
        self.insertTab(index, placeholder, f"[Zzz] {title[:16]}")
        self.tab_metadata[index]["placeholder"] = placeholder

    def awaken_tab(self, index: int):
        if index not in self.tab_metadata:
            return
        meta = self.tab_metadata[index]
        if not meta.get("hibernated", False):
            return

        url_to_restore = meta["url"]
        meta["hibernated"] = False

        placeholder = meta.get("placeholder")
        if placeholder:
            placeholder.deleteLater()
            meta["placeholder"] = None

        new_view = ImperialWebView(
            self.profile,
            self,
            new_tab_callback=self.handle_popup_tab,
            command_callback=self.command_callback,
            ext_manager=self.ext_manager
        )
        new_view.load(QUrl(url_to_restore))
        meta["webview"] = new_view

        new_view.titleChanged.connect(lambda t, idx=index: self.on_tab_title_changed(idx, t))
        new_view.urlChanged.connect(lambda u, idx=index: self.on_tab_url_changed(idx, u))
        new_view.loadProgress.connect(lambda p, idx=index: self.on_tab_progress(idx, p))

        self.removeTab(index)
        self.insertTab(index, new_view, meta["title"][:20])
        self.setCurrentIndex(index)

    def close_tab(self, index: int):
        if self.count() <= 1:
            if 0 in self.tab_metadata and self.tab_metadata[0].get("webview"):
                self.tab_metadata[0]["webview"].load(NEW_TAB_URL)
            return

        meta = self.tab_metadata.pop(index, None)
        if meta:
            view = meta.get("webview")
            if view:
                view.deleteLater()

        self.removeTab(index)

        new_meta = {}
        for i in range(self.count()):
            widget = self.widget(i)
            for old_idx, m in list(self.tab_metadata.items()):
                if m.get("webview") == widget or m.get("placeholder") == widget:
                    new_meta[i] = m
                    break
        self.tab_metadata = new_meta

    def current_webview(self) -> ImperialWebView:
        idx = self.currentIndex()
        if idx in self.tab_metadata and not self.tab_metadata[idx].get("hibernated", False):
            return self.tab_metadata[idx].get("webview")
        return None

    def get_tab_data(self, idx: int) -> dict:
        return self.tab_metadata.get(idx)

    def show_context_menu(self, pos):
        idx = self.tabBar().tabAt(pos)
        if idx < 0:
            return

        menu = QMenu(self)
        reload_act = menu.addAction("Reload Sector")
        hibernate_act = menu.addAction("Hibernate Tab (Save RAM)")
        close_act = menu.addAction("Close Sector")
        close_others_act = menu.addAction("Close Other Sectors")

        action = menu.exec(self.mapToGlobal(pos))
        if action == reload_act:
            view = self.current_webview()
            if view:
                view.reload()
        elif action == hibernate_act:
            self.hibernate_tab(idx)
        elif action == close_act:
            self.close_tab(idx)
        elif action == close_others_act:
            for i in reversed(range(self.count())):
                if i != idx:
                    self.close_tab(i)
