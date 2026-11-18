import os
from pathlib import Path
from PySide6.QtWebEngineCore import QWebEngineScript, QWebEngineProfile
from adblocker import COSMETIC_AD_BLOCK_CSS
from config import SCRIPTS_DIR, config

# Tactical JavaScript Modules
IMPERIAL_DARK_ENABLE_JS = """
(function() {
    let el = document.getElementById('imperial-dark-force-style');
    if (!el) {
        el = document.createElement('style');
        el.id = 'imperial-dark-force-style';
        el.textContent = `
            html {
                background-color: #0b0c10 !important;
                filter: invert(90%) hue-rotate(180deg) contrast(1.1) !important;
            }
            img, video, iframe, canvas, svg, [style*="background-image"] {
                filter: invert(100%) hue-rotate(180deg) !important;
            }
        `;
        (document.head || document.documentElement).appendChild(el);
    }
})();
"""

IMPERIAL_DARK_DISABLE_JS = """
(function() {
    const el = document.getElementById('imperial-dark-force-style');
    if (el) el.remove();
})();
"""

AD_VAPORIZER_JS = f"""
(function() {{
    function injectShield() {{
        let el = document.getElementById('imperial-ad-vaporizer-css');
        if (!el) {{
            el = document.createElement('style');
            el.id = 'imperial-ad-vaporizer-css';
            el.textContent = `{COSMETIC_AD_BLOCK_CSS.replace("`", "'")}`;
            (document.head || document.documentElement).appendChild(el);
        }}
    }}
    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', injectShield);
    }} else {{
        injectShield();
    }}
}})();
"""

VIDEO_AD_DEFLECTOR_JS = """
(function() {
    if (window.__imperial_video_skipper) return;
    window.__imperial_video_skipper = true;

    setInterval(() => {
        // Find standard video skip buttons (YouTube, etc.)
        const skipButtons = document.querySelectorAll(
            '.ytp-ad-skip-button, .ytp-ad-skip-button-modern, .videoAdUiSkipButton, [id^="skip-button"], button.ytp-ad-skip-button-modern'
        );
        skipButtons.forEach(btn => {
            if (btn && typeof btn.click === 'function') {
                btn.click();
            }
        });

        // Fast-forward video ad if currently playing
        const adContainers = document.querySelectorAll('.ad-showing, .ad-interrupting, .ytp-ad-player-overlay');
        if (adContainers.length > 0) {
            const videos = document.querySelectorAll('video');
            videos.forEach(v => {
                try {
                    v.muted = true;
                    v.playbackRate = 16.0;
                    if (v.duration && !isNaN(v.duration)) {
                        v.currentTime = v.duration - 0.1;
                    }
                } catch(e) {}
            });
        }
    }, 400);
})();
"""

GHOST_PROTOCOL_JS = """
(function() {
    if (window.__imperial_ghost_active) return;
    window.__imperial_ghost_active = true;

    // Deflect beacon tracking
    if (navigator.sendBeacon) {
        navigator.sendBeacon = function() { return true; };
    }

    // Micro-noise for Canvas Fingerprinting
    const origToDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function() {
        const ctx = this.getContext('2d');
        if (ctx) {
            try {
                const imgData = ctx.getImageData(0, 0, Math.min(10, this.width), Math.min(10, this.height));
                if (imgData.data.length > 2) imgData.data[0] = (imgData.data[0] + 1) % 255;
                ctx.putImageData(imgData, 0, 0);
            } catch (e) {}
        }
        return origToDataURL.apply(this, arguments);
    };

    // Strip tracker params from URL
    const trackers = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'fbclid', 'gclid', '_ga'];
    if (window.location && window.location.search) {
        const u = new URL(window.location.href);
        let changed = false;
        trackers.forEach(t => {
            if (u.searchParams.has(t)) {
                u.searchParams.delete(t);
                changed = true;
            }
        });
        if (changed) {
            window.history.replaceState({}, document.title, u.toString());
        }
    }
})();
"""

class ImperialExtensionsManager:
    def __init__(self, profile: QWebEngineProfile = None, window=None):
        self.profile = profile or QWebEngineProfile.defaultProfile()
        self.window = window
        self.available_extensions = {
            "ad_vaporizer": {
                "name": "Imperial Ad Vaporizer",
                "description": "Cosmetically strips ad banners and floating popups",
                "code": AD_VAPORIZER_JS,
                "enabled": True,
                "injection_point": QWebEngineScript.InjectionPoint.DocumentReady
            },
            "video_ad_deflector": {
                "name": "Tactical Video Ad Skipper",
                "description": "Auto-skips & accelerates video stream ads (YouTube, etc.)",
                "code": VIDEO_AD_DEFLECTOR_JS,
                "enabled": True,
                "injection_point": QWebEngineScript.InjectionPoint.DocumentReady
            },
            "ghost_protocol": {
                "name": "Ghost Protocol (Anti-Tracker)",
                "description": "Deflects canvas fingerprinting & strips URL trackers",
                "code": GHOST_PROTOCOL_JS,
                "enabled": True,
                "injection_point": QWebEngineScript.InjectionPoint.DocumentCreation
            },
            "imperial_dark": {
                "name": "Imperial Dark Force",
                "description": "Forces sleek high-contrast dark mode on any light website",
                "code": IMPERIAL_DARK_ENABLE_JS,
                "enabled": config.get("dark_mode_forced", False),
                "injection_point": QWebEngineScript.InjectionPoint.DocumentReady
            }
        }
        self.apply_all_active()

    def apply_all_active(self):
        scripts_collection = self.profile.scripts()
        scripts_collection.clear()

        for ext_id, ext_data in self.available_extensions.items():
            if ext_data["enabled"]:
                self._inject_script(ext_id, ext_data)

    def _inject_script(self, script_id: str, data: dict):
        script = QWebEngineScript()
        script.setName(script_id)
        script.setSourceCode(data["code"])
        script.setInjectionPoint(data["injection_point"])
        # MainWorld gives full DOM access
        script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        script.setRunsOnSubFrames(True)
        self.profile.scripts().insert(script)

    def toggle_extension(self, ext_id: str, state: bool):
        if ext_id in self.available_extensions:
            self.available_extensions[ext_id]["enabled"] = state
            if ext_id == "imperial_dark":
                config.set("dark_mode_forced", state)
            self.apply_all_active()

            # Apply live to open tabs
            if self.window and hasattr(self.window, "tab_widget"):
                current_view = self.window.tab_widget.current_webview()
                if current_view:
                    if ext_id == "imperial_dark":
                        js = IMPERIAL_DARK_ENABLE_JS if state else IMPERIAL_DARK_DISABLE_JS
                        current_view.page().runJavaScript(js)
                    elif ext_id == "ad_vaporizer" and state:
                        current_view.page().runJavaScript(AD_VAPORIZER_JS)
                    elif ext_id == "video_ad_deflector" and state:
                        current_view.page().runJavaScript(VIDEO_AD_DEFLECTOR_JS)

    def apply_to_view(self, webview):
        """Called on page loadFinished to guarantee active scripts run."""
        if not webview or not webview.page():
            return

        if self.is_enabled("ad_vaporizer"):
            webview.page().runJavaScript(AD_VAPORIZER_JS)

        if self.is_enabled("video_ad_deflector"):
            webview.page().runJavaScript(VIDEO_AD_DEFLECTOR_JS)

        if self.is_enabled("imperial_dark"):
            webview.page().runJavaScript(IMPERIAL_DARK_ENABLE_JS)

        if self.is_enabled("ghost_protocol"):
            webview.page().runJavaScript(GHOST_PROTOCOL_JS)

    def is_enabled(self, ext_id: str) -> bool:
        return self.available_extensions.get(ext_id, {}).get("enabled", False)

    def get_extensions_list(self):
        return [
            {
                "id": k,
                "name": v["name"],
                "description": v["description"],
                "enabled": v["enabled"]
            }
            for k, v in self.available_extensions.items()
        ]
