import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
SCRIPTS_DIR = DATA_DIR / "user_scripts"
STORAGE_DIR = DATA_DIR / "web_storage"
SETTINGS_FILE = DATA_DIR / "settings.json"

DEFAULT_SETTINGS = {
    "homepage": "imperial://newtab",
    "search_engine": "Google",
    "search_engines": {
        "Google": "https://www.google.com/search?q={query}",
        "DuckDuckGo": "https://duckduckgo.com/?q={query}",
        "Brave": "https://search.brave.com/search?q={query}",
        "Bing": "https://www.bing.com/search?q={query}",
        "Startpage": "https://www.startpage.com/sp/search?query={query}"
    },
    "adblock_enabled": True,
    "cosmetic_filtering": True,
    "tracker_blocking": True,
    "malware_protection": True,
    "virus_scan_downloads": True,
    "windows_defender_scan": True,
    "ram_saver_enabled": True,
    "tab_hibernation_minutes": 5,
    "max_renderer_processes": 3,
    "dark_mode_forced": False,
    "sound_effects": True,
    "theme": "Rev_Imperial_Crimson",
    "window_width": 1360,
    "window_height": 860
}

class ConfigManager:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        self.settings = self.load_settings()

    def load_settings(self):
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    merged = dict(DEFAULT_SETTINGS)
                    merged.update(data)
                    return merged
            except Exception:
                pass
        return dict(DEFAULT_SETTINGS)

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"[IMPERIAL CONFIG ERROR] Failed to save settings: {e}")

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self.save_settings()

config = ConfigManager()
