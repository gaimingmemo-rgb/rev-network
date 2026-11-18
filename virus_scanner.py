import os
import hashlib
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Optional, Tuple

HIGH_RISK_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".scr", ".pif", ".vbs", ".vbe", ".js", ".jse",
    ".wsf", ".wsh", ".ps1", ".ps1xml", ".ps2", ".psc1", ".msh", ".msi",
    ".msp", ".hta", ".cpl", ".jar", ".reg", ".dll", ".sys"
}

MEDIUM_RISK_EXTENSIONS = {
    ".zip", ".rar", ".7z", ".tar", ".gz", ".iso", ".img", ".apk", ".bin"
}

# Known signature hashes (demo / standard test viruses like EICAR test string hash)
KNOWN_MALWARE_HASHES = {
    # EICAR standard antivirus test file SHA-256
    "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f": "EICAR-Standard-AV-Test-Signature",
    "44d88612fea8a8f36de82e1278abb02f": "W32/Malware-Sample"
}

# Suspicious domain indicators
MALICIOUS_TLDS = {".xyz", ".top", ".buzz", ".work", ".stream", ".gq", ".ml", ".cf", ".tk", ".ga"}

class ImperialVirusScanner:
    def __init__(self, quarantine_dir: Optional[Path] = None):
        if quarantine_dir is None:
            self.quarantine_dir = Path(__file__).resolve().parent / "data" / "quarantine"
        else:
            self.quarantine_dir = quarantine_dir
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)
        self.mpcmdrun_path = self._locate_defender()

    def _locate_defender(self) -> Optional[str]:
        # Check standard paths
        candidates = [
            r"C:\Program Files\Windows Defender\MpCmdRun.exe",
            r"C:\Program Files (x86)\Windows Defender\MpCmdRun.exe"
        ]
        for c in candidates:
            if os.path.exists(c):
                return c

        platform_dir = Path(r"C:\ProgramData\Microsoft\Windows Defender\Platform")
        if platform_dir.exists():
            for exe in platform_dir.rglob("MpCmdRun.exe"):
                if exe.is_file():
                    return str(exe)
        return None

    def assess_url(self, url: str) -> Dict[str, any]:
        """Performs pre-navigation heuristic threat evaluation."""
        threat_level = "SAFE"
        reasons = []

        url_lower = url.lower()

        # Check for deceptive double extensions
        if any(f".{ext}.exe" in url_lower for ext in ["pdf", "jpg", "png", "docx", "mp4"]):
            threat_level = "CRITICAL"
            reasons.append("Deceptive double-extension payload detected")

        # Check for raw IP downloads
        import re
        if re.search(r"https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", url_lower):
            if any(url_lower.endswith(ext) for ext in HIGH_RISK_EXTENSIONS):
                threat_level = "HIGH"
                reasons.append("Direct binary payload from raw IP address")

        return {
            "threat_level": threat_level,
            "reasons": reasons,
            "is_malicious": threat_level in ["CRITICAL", "HIGH"]
        }

    def evaluate_file_risk(self, filename: str) -> Tuple[str, str]:
        ext = os.path.splitext(filename)[1].lower()
        if ext in HIGH_RISK_EXTENSIONS:
            return "CRITICAL", f"High-risk executable binary ({ext})"
        elif ext in MEDIUM_RISK_EXTENSIONS:
            return "WARNING", f"Archive/Container file may conceal executables ({ext})"
        return "SAFE", "Standard media/document format"

    def calculate_sha256(self, filepath: str) -> str:
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def scan_file(self, filepath: str) -> Dict[str, any]:
        """
        Scans a downloaded file using:
        1. SHA-256 hash database check
        2. Microsoft Defender engine (MpCmdRun) if available
        3. Heuristic extension analysis
        """
        if not os.path.exists(filepath):
            return {"status": "ERROR", "message": "File not found"}

        file_size = os.path.getsize(filepath)
        filename = os.path.basename(filepath)
        file_hash = self.calculate_sha256(filepath)
        risk_level, risk_desc = self.evaluate_file_risk(filename)

        # 1. Hash signature match
        if file_hash in KNOWN_MALWARE_HASHES:
            threat_name = KNOWN_MALWARE_HASHES[file_hash]
            return {
                "status": "INFECTED",
                "engine": "Imperial Signature DB",
                "threat": threat_name,
                "file_hash": file_hash,
                "risk_level": "CRITICAL"
            }

        # 2. Windows Defender Engine scan
        if self.mpcmdrun_path and os.path.exists(self.mpcmdrun_path):
            try:
                cmd = [self.mpcmdrun_path, "-Scan", "-ScanType", "3", "-File", filepath, "-DisableRemediation"]
                # Run scan with timeout
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                # MpCmdRun returns:
                # 0 = No threat found
                # 2 = Threat detected
                if proc.returncode == 2:
                    return {
                        "status": "INFECTED",
                        "engine": "Windows Defender",
                        "threat": "Trojan/Malware detected by Defender Engine",
                        "file_hash": file_hash,
                        "risk_level": "CRITICAL",
                        "output": proc.stdout
                    }
                elif proc.returncode == 0:
                    return {
                        "status": "CLEAN",
                        "engine": "Windows Defender",
                        "file_hash": file_hash,
                        "risk_level": risk_level,
                        "description": risk_desc
                    }
            except Exception as e:
                # Fallback to heuristic
                pass

        return {
            "status": "CLEAN",
            "engine": "Imperial Heuristic Core",
            "file_hash": file_hash,
            "risk_level": risk_level,
            "description": risk_desc
        }

    def quarantine_file(self, filepath: str) -> str:
        """Moves file to the Imperial Quarantine Vault and locks it."""
        try:
            filename = os.path.basename(filepath)
            dest = self.quarantine_dir / f"QUARANTINED_{filename}.locked"
            shutil.move(filepath, dest)
            return str(dest)
        except Exception as e:
            return f"Error quarantining: {e}"

virus_scanner = ImperialVirusScanner()
