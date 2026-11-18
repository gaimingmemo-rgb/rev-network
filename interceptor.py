from PySide6.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo
from PySide6.QtCore import QObject, Signal
from adblocker import adblocker

class InterceptorSignals(QObject):
    request_blocked = Signal(str, str)

class ImperialRequestInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.signals = InterceptorSignals()

    def interceptRequest(self, info: QWebEngineUrlRequestInfo):
        url_str = info.requestUrl().toString()

        # Global Privacy Control headers
        info.setHttpHeader(b"DNT", b"1")
        info.setHttpHeader(b"Sec-GPC", b"1")

        # Adblock & Tracker inspection
        if adblocker.should_block(url_str):
            info.block(True)
            self.signals.request_blocked.emit(url_str, "AD/TRACKER")
            return
