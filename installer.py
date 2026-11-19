"""
Rev Network // Imperial Installer Setup
Autonomous installer for Rev Network Browser.
Packaged with payload.zip and compiles to a standalone Rev-Network-Setup.exe.
"""

import os
import sys
import time
import shutil
import zipfile
import threading
import subprocess
import winreg
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ─── Configuration & Theme ───
APP_NAME = "Revision-Web"
APP_VERSION = "2.0.0"
PUBLISHER = "Project Revision"
EXE_NAME = "Revision-Web.exe"

# Colors (Imperial Dark Theme)
BG_DARK = "#0b0c12"
PANEL_BG = "#131520"
CARD_BG = "#181a28"
BORDER_COLOR = "#2c2e42"
ACCENT_RED = "#e01122"
ACCENT_HOVER = "#ff253a"
TEXT_WHITE = "#f5f6fa"
TEXT_MUTED = "#8d90a5"
TEXT_DIM = "#56596e"
SUCCESS_GREEN = "#00e676"

def get_bundle_dir():
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent

def get_default_install_dir():
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "Programs" / "Rev-Network"
    return Path.home() / "Rev-Network"

def create_windows_shortcut(target_path, link_path, icon_path=None, work_dir=None, description=APP_NAME):
    target = str(target_path).replace('"', '`"')
    link = str(link_path).replace('"', '`"')
    wdir = str(work_dir or Path(target_path).parent).replace('"', '`"')
    desc = str(description).replace('"', '`"')
    
    ps_script = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{link}")
$Shortcut.TargetPath = "{target}"
$Shortcut.WorkingDirectory = "{wdir}"
$Shortcut.Description = "{desc}"
'''
    if icon_path and Path(icon_path).exists():
        icon = str(icon_path).replace('"', '`"')
        ps_script += f'$Shortcut.IconLocation = "{icon},0"\n'
    ps_script += '$Shortcut.Save()\n'

    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-NonInteractive", "-Command", ps_script],
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
            check=True
        )
        return True
    except Exception as e:
        print(f"Error creating shortcut {link_path}: {e}")
        return False

def register_uninstall(install_dir):
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\RevNetwork"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, APP_VERSION)
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, PUBLISHER)
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(install_dir))
            exe_path = install_dir / EXE_NAME
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, str(exe_path))
            uninst_bat = install_dir / "uninstall.bat"
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'cmd.exe /c "{uninst_bat}"')
            winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
    except Exception as e:
        print(f"Failed to write registry uninstall key: {e}")

def create_uninstall_script(install_dir, desktop_lnk, startmenu_lnk):
    uninst_content = f"""@echo off
title Revision-Web Uninstaller
cls
echo ========================================================
echo         REVISION-WEB // SYSTEM REMOVAL
echo ========================================================
echo.
echo Removing Revision-Web shortcuts...
if exist "{desktop_lnk}" del /f /q "{desktop_lnk}"
if exist "{startmenu_lnk}" del /f /q "{startmenu_lnk}"

echo Removing registry entries...
reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\RevisionWeb" /f >nul 2>&1

echo Purging installed application files...
cd /d "%TEMP%"
start /b "" cmd /c "timeout /t 2 /nobreak >nul & rmdir /s /q \\"{install_dir}\\""
echo Uninstallation completed successfully.
exit
"""
    try:
        with open(install_dir / "uninstall.bat", "w", encoding="utf-8") as f:
            f.write(uninst_content)
    except Exception as e:
        print(f"Failed to create uninstall script: {e}")

class ImperialInstallerApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Revision-Web // Tactical Setup")
        self.geometry("640x510")
        self.resizable(False, False)
        self.configure(bg=BG_DARK)

        # Try to set window icon
        bundle_dir = get_bundle_dir()
        icon_path = bundle_dir / "rev_network.ico"
        if not icon_path.exists():
            icon_path = bundle_dir / "assets" / "icon.ico"
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except Exception:
                pass

        # Center on screen
        self.center_window(640, 510)

        # State
        self.install_dir_var = tk.StringVar(value=str(get_default_install_dir()))
        self.desktop_shortcut_var = tk.BooleanVar(value=True)
        self.startmenu_shortcut_var = tk.BooleanVar(value=True)
        self.launch_browser_var = tk.BooleanVar(value=True)

        self.setup_ui()

    def center_window(self, width, height):
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def setup_ui(self):
        # ── Header Banner ──
        header = tk.Frame(self, bg=PANEL_BG, height=80, relief="flat", highlightthickness=1, highlightbackground=BORDER_COLOR)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        title_box = tk.Frame(header, bg=PANEL_BG)
        title_box.pack(side="left", padx=24, pady=12)

        lbl_title = tk.Label(
            title_box,
            text="⚡ REVISION-WEB // INSTALLATION DECK",
            font=("Segoe UI", 14, "bold"),
            fg=ACCENT_RED,
            bg=PANEL_BG
        )
        lbl_title.pack(anchor="w")

        lbl_sub = tk.Label(
            title_box,
            text="Imperial High-Performance Web Browser & Live Community Matrix",
            font=("Segoe UI", 9),
            fg=TEXT_MUTED,
            bg=PANEL_BG
        )
        lbl_sub.pack(anchor="w", pady=(2, 0))

        # ── Main Content Area ──
        self.content_frame = tk.Frame(self, bg=BG_DARK)
        self.content_frame.pack(fill="both", expand=True, padx=24, pady=20)

        self.show_config_step()

    def show_config_step(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Destination card
        dest_card = tk.LabelFrame(
            self.content_frame,
            text=" 📁 INSTALLATION DIRECTORY ",
            font=("Segoe UI", 9, "bold"),
            fg=ACCENT_RED,
            bg=CARD_BG,
            relief="solid",
            bd=1,
            padx=16,
            pady=14
        )
        dest_card.pack(fill="x", pady=(0, 16))

        dest_row = tk.Frame(dest_card, bg=CARD_BG)
        dest_row.pack(fill="x")

        self.ent_path = tk.Entry(
            dest_row,
            textvariable=self.install_dir_var,
            font=("Consolas", 9),
            bg="#0f1018",
            fg=TEXT_WHITE,
            insertbackground=TEXT_WHITE,
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER_COLOR
        )
        self.ent_path.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))

        btn_browse = tk.Button(
            dest_row,
            text="BROWSE...",
            font=("Segoe UI", 8, "bold"),
            bg="#222538",
            fg=TEXT_WHITE,
            activebackground=BORDER_COLOR,
            activeforeground=TEXT_WHITE,
            relief="flat",
            padx=12,
            pady=4,
            command=self.browse_directory,
            cursor="hand2"
        )
        btn_browse.pack(side="right")

        lbl_req = tk.Label(
            dest_card,
            text="Space required: ~580 MB | Full Chromium engine & Imperial AdBlock suite included",
            font=("Segoe UI", 8),
            fg=TEXT_DIM,
            bg=CARD_BG
        )
        lbl_req.pack(anchor="w", pady=(8, 0))

        # Options card
        opt_card = tk.LabelFrame(
            self.content_frame,
            text=" ⚙️ INSTALLATION OPTIONS ",
            font=("Segoe UI", 9, "bold"),
            fg=ACCENT_RED,
            bg=CARD_BG,
            relief="solid",
            bd=1,
            padx=16,
            pady=14
        )
        opt_card.pack(fill="x", pady=(0, 20))

        def make_chk(parent, text, var):
            chk = tk.Checkbutton(
                parent,
                text=text,
                variable=var,
                font=("Segoe UI", 9),
                fg=TEXT_WHITE,
                bg=CARD_BG,
                activebackground=CARD_BG,
                activeforeground=TEXT_WHITE,
                selectcolor="#0f1018",
                relief="flat",
                cursor="hand2"
            )
            chk.pack(anchor="w", pady=3)
            return chk

        make_chk(opt_card, "Create Revision-Web Desktop Shortcut", self.desktop_shortcut_var)
        make_chk(opt_card, "Create Start Menu Program Entry", self.startmenu_shortcut_var)
        make_chk(opt_card, "Launch Revision-Web immediately after installation", self.launch_browser_var)

        # Bottom Action Bar
        bottom_bar = tk.Frame(self.content_frame, bg=BG_DARK)
        bottom_bar.pack(fill="x", side="bottom")

        btn_install = tk.Button(
            bottom_bar,
            text="EXECUTE INSTALLATION",
            font=("Segoe UI", 11, "bold"),
            bg=ACCENT_RED,
            fg="white",
            activebackground=ACCENT_HOVER,
            activeforeground="white",
            relief="flat",
            padx=28,
            pady=10,
            cursor="hand2",
            command=self.start_installation
        )
        btn_install.pack(side="right")

        btn_cancel = tk.Button(
            bottom_bar,
            text="CANCEL",
            font=("Segoe UI", 9),
            bg="#181a28",
            fg=TEXT_MUTED,
            activebackground="#222538",
            activeforeground=TEXT_WHITE,
            relief="flat",
            padx=18,
            pady=10,
            cursor="hand2",
            command=self.destroy
        )
        btn_cancel.pack(side="right", padx=(0, 12))

    def browse_directory(self):
        chosen = filedialog.askdirectory(initialdir=self.install_dir_var.get())
        if chosen:
            self.install_dir_var.set(chosen)

    def start_installation(self):
        install_path = Path(self.install_dir_var.get().strip())
        if not install_path:
            messagebox.showerror("Error", "Please specify a valid installation directory.")
            return

        # Switch to Progress UI
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Progress title
        lbl_status_title = tk.Label(
            self.content_frame,
            text="INSTALLING REV NETWORK...",
            font=("Segoe UI", 12, "bold"),
            fg=TEXT_WHITE,
            bg=BG_DARK
        )
        lbl_status_title.pack(anchor="w", pady=(15, 6))

        self.lbl_substatus = tk.Label(
            self.content_frame,
            text="Extracting runtime packages...",
            font=("Segoe UI", 9),
            fg=TEXT_MUTED,
            bg=BG_DARK
        )
        self.lbl_substatus.pack(anchor="w", pady=(0, 14))

        # Custom Canvas Progress Bar
        self.canvas_prog = tk.Canvas(
            self.content_frame,
            width=590,
            height=16,
            bg="#141624",
            highlightthickness=1,
            highlightbackground=BORDER_COLOR
        )
        self.canvas_prog.pack(fill="x", pady=(0, 10))
        self.prog_rect = self.canvas_prog.create_rectangle(0, 0, 0, 16, fill=ACCENT_RED, width=0)

        self.lbl_percent = tk.Label(
            self.content_frame,
            text="0%",
            font=("Segoe UI", 10, "bold"),
            fg=ACCENT_RED,
            bg=BG_DARK
        )
        self.lbl_percent.pack(anchor="e")

        # Terminal / Extraction detail log box
        self.log_box = tk.Text(
            self.content_frame,
            height=10,
            font=("Consolas", 8),
            bg="#0d0e17",
            fg=TEXT_MUTED,
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            padx=10,
            pady=8
        )
        self.log_box.pack(fill="both", expand=True, pady=(10, 0))
        self.log_box.insert("end", "[IMPERIAL SETUP] Initializing installation sequence...\n")
        self.log_box.configure(state="disabled")

        # Run extraction in background thread
        thread = threading.Thread(target=self.run_install_worker, args=(install_path,), daemon=True)
        thread.start()

    def update_progress(self, current, total, filename=""):
        if total <= 0:
            pct = 0
        else:
            pct = min(100, int((current / total) * 100))

        bar_width = int(590 * (pct / 100))
        self.canvas_prog.coords(self.prog_rect, 0, 0, bar_width, 16)
        self.lbl_percent.config(text=f"{pct}%")
        if filename:
            self.lbl_substatus.config(text=f"Extracting: {filename}")
            self.log_box.configure(state="normal")
            self.log_box.insert("end", f"> {filename}\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")

    def run_install_worker(self, install_path):
        try:
            install_path.mkdir(parents=True, exist_ok=True)
            bundle_dir = get_bundle_dir()

            payload_path = bundle_dir / "payload.zip"
            if not payload_path.exists():
                # Check root directory or current directory
                payload_path = Path.cwd() / "payload.zip"

            if not payload_path.exists():
                raise FileNotFoundError(f"Installation payload not found at: {payload_path}")

            with zipfile.ZipFile(payload_path, "r") as zf:
                members = zf.infolist()
                total = len(members)

                for idx, member in enumerate(members):
                    zf.extract(member, install_path)
                    # Update every 5 items or last
                    if idx % 5 == 0 or idx == total - 1:
                        self.after(0, self.update_progress, idx + 1, total, member.filename)

            # Copy icon to install directory if not present
            exe_path = install_path / EXE_NAME
            icon_file = install_path / "rev_network.ico"
            if not icon_file.exists():
                src_icon = bundle_dir / "rev_network.ico"
                if src_icon.exists():
                    shutil.copy2(src_icon, icon_file)

            # Desktop Shortcut
            desktop_dir = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"
            desktop_lnk = desktop_dir / f"{APP_NAME}.lnk"
            if self.desktop_shortcut_var.get() and exe_path.exists():
                create_windows_shortcut(
                    target_path=exe_path,
                    link_path=desktop_lnk,
                    icon_path=icon_file if icon_file.exists() else exe_path,
                    work_dir=install_path,
                    description=f"{APP_NAME} - Imperial Web Browser"
                )

            # Start Menu Shortcut
            appdata_roaming = os.environ.get("APPDATA")
            startmenu_lnk = None
            if appdata_roaming:
                startmenu_dir = Path(appdata_roaming) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
                startmenu_lnk = startmenu_dir / f"{APP_NAME}.lnk"
                if self.startmenu_shortcut_var.get() and exe_path.exists():
                    create_windows_shortcut(
                        target_path=exe_path,
                        link_path=startmenu_lnk,
                        icon_path=icon_file if icon_file.exists() else exe_path,
                        work_dir=install_path,
                        description=f"{APP_NAME} - Imperial Web Browser"
                    )

            # Register Uninstall in Windows Registry & write uninstaller script
            create_uninstall_script(install_path, desktop_lnk, startmenu_lnk or "")
            register_uninstall(install_path)

            self.after(0, self.show_completed_step, install_path)

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Installation Error", f"Installation failed:\n{e}"))
            self.after(0, self.show_config_step)

    def show_completed_step(self, install_path):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        done_box = tk.Frame(self.content_frame, bg=CARD_BG, relief="solid", bd=1, padx=24, pady=30)
        done_box.pack(fill="both", expand=True, pady=10)

        lbl_check = tk.Label(
            done_box,
            text="✔",
            font=("Segoe UI", 48, "bold"),
            fg=SUCCESS_GREEN,
            bg=CARD_BG
        )
        lbl_check.pack(pady=(0, 10))

        lbl_title = tk.Label(
            done_box,
            text="REVISION-WEB READY FOR FLIGHT",
            font=("Segoe UI", 14, "bold"),
            fg=TEXT_WHITE,
            bg=CARD_BG
        )
        lbl_title.pack(pady=(0, 6))

        lbl_desc = tk.Label(
            done_box,
            text=f"Installation successfully completed to:\n{install_path}\n\nDesktop shortcut, Imperial AdBlocker, and Community Node are deployed.",
            font=("Segoe UI", 9),
            fg=TEXT_MUTED,
            bg=CARD_BG,
            justify="center"
        )
        lbl_desc.pack(pady=(0, 20))

        bottom_bar = tk.Frame(self.content_frame, bg=BG_DARK)
        bottom_bar.pack(fill="x", side="bottom", pady=(15, 0))

        btn_finish = tk.Button(
            bottom_bar,
            text="FINISH & LAUNCH BROWSER",
            font=("Segoe UI", 11, "bold"),
            bg=ACCENT_RED,
            fg="white",
            activebackground=ACCENT_HOVER,
            activeforeground="white",
            relief="flat",
            padx=28,
            pady=10,
            cursor="hand2",
            command=lambda: self.finish_and_launch(install_path)
        )
        btn_finish.pack(side="right")

    def finish_and_launch(self, install_path):
        exe_path = install_path / EXE_NAME
        if self.launch_browser_var.get() and exe_path.exists():
            try:
                subprocess.Popen([str(exe_path)], cwd=str(install_path))
            except Exception as e:
                print(f"Could not launch browser: {e}")
        self.destroy()

if __name__ == "__main__":
    app = ImperialInstallerApp()
    app.mainloop()
