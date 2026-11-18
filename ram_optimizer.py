import os
import gc
import ctypes
import psutil
from datetime import datetime
from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWebEngineCore import QWebEngineProfile
from config import config

class RamOptimizerSignals(QObject):
    telemetry_updated = Signal(float, float, str)  # process_mb, system_pct, status_text
    memory_purged = Signal(float)                  # mb_freed
    tab_hibernated = Signal(int)                   # tab_index

class ImperialRamOptimizer(QObject):
    def __init__(self, tab_manager=None, parent=None):
        super().__init__(parent)
        self.tab_manager = tab_manager
        self.signals = RamOptimizerSignals()
        self.process = psutil.Process(os.getpid())

        # Timer for telemetry updates every 2 seconds
        self.telemetry_timer = QTimer(self)
        self.telemetry_timer.timeout.connect(self.update_telemetry)
        self.telemetry_timer.start(2000)

        # Tab hibernation check every 60 seconds
        self.hibernation_timer = QTimer(self)
        self.hibernation_timer.timeout.connect(self.check_tab_hibernation)
        self.hibernation_timer.start(60000)

    def get_memory_usage_mb(self) -> float:
        try:
            total_bytes = self.process.memory_info().rss
            for child in self.process.children(recursive=True):
                try:
                    total_bytes += child.memory_info().rss
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return round(total_bytes / (1024 * 1024), 1)
        except Exception:
            return 0.0

    def get_system_ram_pct(self) -> float:
        try:
            return psutil.virtual_memory().percent
        except Exception:
            return 0.0

    def update_telemetry(self):
        proc_mb = self.get_memory_usage_mb()
        sys_pct = self.get_system_ram_pct()

        if proc_mb < 250:
            status = "OPTIMAL"
        elif proc_mb < 500:
            status = "NOMINAL"
        elif proc_mb < 800:
            status = "ELEVATED"
        else:
            status = "CRITICAL"

        self.signals.telemetry_updated.emit(proc_mb, sys_pct, status)

    def check_tab_hibernation(self):
        if not config.get("ram_saver_enabled", True) or not self.tab_manager:
            return

        hibernation_minutes = config.get("tab_hibernation_minutes", 5)
        now = datetime.now()

        for idx in range(self.tab_manager.count()):
            if idx == self.tab_manager.currentIndex():
                continue

            tab_item = self.tab_manager.get_tab_data(idx)
            if not tab_item or tab_item.get("hibernated", False):
                continue

            last_active = tab_item.get("last_active", now)
            delta = (now - last_active).total_seconds() / 60.0

            if delta >= hibernation_minutes:
                self.tab_manager.hibernate_tab(idx)
                self.signals.tab_hibernated.emit(idx)

    def purge_memory(self) -> float:
        """
        Tactical RAM purge:
        1. Clears WebEngine HTTP cache
        2. Force-hibernates inactive tabs
        3. Invokes Windows EmptyWorkingSet on parent and all Chromium renderers
        4. Invokes Python GC
        """
        before_mb = self.get_memory_usage_mb()

        # 1. Clear WebEngine Profile HTTP cache
        try:
            profile = QWebEngineProfile.defaultProfile()
            profile.clearHttpCache()
        except Exception:
            pass

        # 2. Hibernate inactive background tabs
        if self.tab_manager:
            for idx in range(self.tab_manager.count()):
                if idx != self.tab_manager.currentIndex():
                    self.tab_manager.hibernate_tab(idx)

        # 3. Windows Kernel Working Set Trim
        try:
            ctypes.windll.psapi.EmptyWorkingSet(ctypes.windll.kernel32.GetCurrentProcess())
            for child in self.process.children(recursive=True):
                try:
                    # PROCESS_SET_QUOTA (0x0100) | PROCESS_QUERY_INFORMATION (0x0400) = 0x0500
                    h = ctypes.windll.kernel32.OpenProcess(0x0500, False, child.pid)
                    if h:
                        ctypes.windll.psapi.EmptyWorkingSet(h)
                        ctypes.windll.kernel32.CloseHandle(h)
                except Exception:
                    pass
        except Exception:
            pass

        # 4. Python garbage collection
        gc.collect()

        after_mb = self.get_memory_usage_mb()
        freed = max(0.0, round(before_mb - after_mb, 1))

        self.signals.memory_purged.emit(freed)
        self.update_telemetry()
        return freed
