# -*- mode: python ; coding: utf-8 -*-
# Rev Network Browser - PyInstaller Spec
# Generated for PySide6 + QtWebEngine on Windows

import sys
from pathlib import Path

block_cipher = None

# Source root
SRC = Path(r"C:\Users\ZarTo\.gemini\antigravity\scratch\imperial-browser")

a = Analysis(
    [str(SRC / "main.py")],
    pathex=[str(SRC)],
    binaries=[],
    datas=[
        # HTML, QSS, icons, SVG
        (str(SRC / "assets" / "newtab.html"),    "assets"),
        (str(SRC / "assets" / "community.html"), "assets"),
        (str(SRC / "assets" / "style.qss"),      "assets"),
        (str(SRC / "assets" / "icon.ico"),        "assets"),
        (str(SRC / "assets" / "icon.png"),        "assets"),
        (str(SRC / "assets" / "imperial_logo.svg"), "assets"),
        # Settings (data dir skeleton)
        (str(SRC / "data" / "settings.json"),    "data"),
        # Root ICO for window icon
        (str(SRC / "rev_network.ico"),           "."),
    ],
    hiddenimports=[
        # PySide6 WebEngine
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineQuick",
        "PySide6.QtWebChannel",
        "PySide6.QtNetwork",
        "PySide6.QtPrintSupport",
        "PySide6.QtMultimedia",
        # stdlib - http.server full dependency chain
        "http.server",
        "http.client",
        "http.cookies",
        "email",
        "email.parser",
        "email.message",
        "email.feedparser",
        "email.headerregistry",
        "email.contentmanager",
        "email.charset",
        "email.encoders",
        "email.errors",
        "email.generator",
        "email.header",
        "email.iterators",
        "email.policy",
        "email.quoprimime",
        "email.base64mime",
        "email.utils",
        "email._header_value_parser",
        "email._encoded_words",
        "email._parseaddr",
        "html",
        "html.parser",
        "urllib",
        "urllib.parse",
        "urllib.request",
        "threading",
        "hashlib",
        "socket",
        "json",
        "ctypes",
        "ctypes.wintypes",
        "subprocess",
        "psutil",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Save size / RAM
        "matplotlib",
        "numpy",
        "PIL",
        "tkinter",
        "unittest",
        "pydoc",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,     # onedir keeps DLLs alongside exe (required by QtWebEngine)
    name="Rev-Network",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                  # compress where possible
    console=False,             # no console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(SRC / "rev_network.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Rev-Network",
)
