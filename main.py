import os
import sys
from pathlib import Path

# ── PyInstaller frozen-exe support ───────────────────────────────────────────
# When packaged by PyInstaller, __file__ is inside a temp _MEIPASS dir.
# We set CWD to _MEIPASS so all relative paths (assets/, data/) resolve OK.
if getattr(sys, "frozen", False):
    # Redirect stdout/stderr to a log file so errors are visible after launch
    _app_dir = Path(sys.executable).parent
    _log = open(_app_dir / "rev_network.log", "w", encoding="utf-8")
    sys.stdout = _log
    sys.stderr = _log
    # For --onefile: bundle dir is sys._MEIPASS; for --onedir: same as exe dir
    _bundle_dir = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    os.chdir(_bundle_dir)
# ─────────────────────────────────────────────────────────────────────────────

# Configure Chromium flags before QApplication initializes
# Use --disable-blink-features=AutomationControlled to ensure Google Auth / Cloudflare
# sees Rev Network as a standard native Chrome browser.
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--disable-blink-features=AutomationControlled "
    "--enable-features=WebContentsDiscarding "
    "--disk-cache-size=52428800 "
    "--disable-gpu-shader-disk-cache "
    "--no-default-browser-check"
)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from browser_window import ImperialBrowserWindow
from config import ASSETS_DIR
from rev_network_node import rev_server

def _ensure_origin_server():
    import socket, subprocess
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.2)
        res = s.connect_ex(("127.0.0.1", 8000))
        s.close()
        if res != 0:
            website_server = Path(r"C:\Users\ZarTo\Desktop\Projects\Website\server.py")
            if website_server.exists():
                subprocess.Popen([sys.executable, str(website_server)], cwd=str(website_server.parent))
    except Exception:
        pass

def main():
    # Ensure Website Origin Server on port 8000 is running
    _ensure_origin_server()

    # Start Rev-Network Interconnected P2P Node Server
    rev_server.start()

    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Revision-Web")
    app.setOrganizationName("RevisionWeb")

    # Load icon (.ico preferred for Windows compilation)
    icon_path = ASSETS_DIR / "icon.ico"
    if not icon_path.exists():
        icon_path = Path(__file__).resolve().parent / "rev_network.ico"
    if not icon_path.exists():
        icon_path = ASSETS_DIR / "imperial_logo.svg"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Load Imperial Theme QSS
    qss_path = ASSETS_DIR / "style.qss"
    if qss_path.exists():
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

    window = ImperialBrowserWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
