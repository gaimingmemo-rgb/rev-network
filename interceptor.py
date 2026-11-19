from PySide6.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo
from PySide6.QtCore import QObject, Signal, QUrl
from adblocker import adblocker

class InterceptorSignals(QObject):
    request_blocked = Signal(str, str)

class ImperialRequestInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.signals = InterceptorSignals()

    def interceptRequest(self, info: QWebEngineUrlRequestInfo):
        qurl = info.requestUrl()
        url_str = qurl.toString()
        host = qurl.host().lower()
        port = qurl.port()

        # Seamless local loopback mapping for rev-network.ddns.net:8000
        # Prevents router NAT loopback / hairpinning timeouts on host PC
        if host == "rev-network.ddns.net" and (port == 8000 or port == -1):
            target = QUrl(qurl)
            target.setHost("127.0.0.1")
            target.setPort(8000)
            target.setScheme("http")
            info.redirect(target)
            return

        # Global Privacy Control headers
        info.setHttpHeader(b"DNT", b"1")
        info.setHttpHeader(b"Sec-GPC", b"1")

        # Adblock & Tracker inspection
        if adblocker.should_block(url_str):
            info.block(True)
            self.signals.request_blocked.emit(url_str, "AD/TRACKER")
            return
