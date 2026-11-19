import os
import sys
import json
import time
import socket
import threading
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from config import DATA_DIR, ASSETS_DIR
from vpn_manager import detect_vpn_interface

MESSAGES_FILE = DATA_DIR / "community_messages.json"
FRIENDS_FILE = DATA_DIR / "community_friends.json"
USERS_FILE = DATA_DIR / "community_users.json"
SHARED_CATALOG_FILE = DATA_DIR / "shared_catalog.json"
UDP_DISCOVERY_PORT = 8769

class RevNodeState:
    def __init__(self, app_name="Revision-Web", default_port=8765):
        self.lock = threading.Lock()
        self.app_name = app_name
        self.port = default_port
        self.vpn_info = detect_vpn_interface()
        self.vpn_active = self.vpn_info.get("active", False)
        self.vpn_ip = self.vpn_info.get("ip")
        self.local_ip = self.vpn_ip if self.vpn_active else self._get_local_ip()
        self.node_id = f"rev-{self.app_name.lower().replace(' ', '-')}-{int(time.time()*1000) % 100000}"
        self.start_time = time.time()
        self.power_score = self._compute_power_score()
        self.active_peers = {} # ip_port -> dict(ip, port, username, app, last_seen, rank, is_self, power)
        self.messages = self._load_messages()
        self.friends = self._load_friends()
        self.pending_requests = []
        self.shared_hydra_sources = self._load_shared_catalog()

        # Register self
        self.register_peer("127.0.0.1", "ZarTo (Host)", "Commander", port=self.port, app=self.app_name, is_self=True)
        if self.vpn_active:
            self.register_peer(self.vpn_ip, f"ZarTo [VPN Shielded]", "Commander", port=self.port, app=self.app_name, is_self=True)

    def _get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def _compute_power_score(self):
        try:
            cores = os.cpu_count() or 4
            return round(cores * 2.5 + 10.0, 1)
        except Exception:
            return 15.0

    def register_peer(self, ip, username, rank="Pilot", port=8765, app="Revision-App", is_self=False, power=15.0):
        with self.lock:
            now = time.time()
            key = f"{ip}:{port}"
            self.active_peers[key] = {
                "ip": ip,
                "port": port,
                "app": app,
                "username": username or f"Pilot_{ip.replace('.', '_')}",
                "rank": rank,
                "power": power,
                "last_seen": now,
                "is_self": is_self or (ip in ["127.0.0.1", self.local_ip] and port == self.port)
            }

    def cleanup_peers(self):
        with self.lock:
            now = time.time()
            to_del = []
            for key, p in self.active_peers.items():
                if not p.get("is_self") and (now - p["last_seen"]) > 60:
                    to_del.append(key)
            for key in to_del:
                del self.active_peers[key]

    def _load_messages(self):
        if MESSAGES_FILE.exists():
            try:
                with open(MESSAGES_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def save_messages(self):
        try:
            with open(MESSAGES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.messages[-100:], f, indent=2)
        except Exception:
            pass

    def add_message(self, sender, text, rank="Pilot", ip="127.0.0.1", source="p2p"):
        with self.lock:
            msg = {
                "id": str(int(time.time() * 1000)),
                "sender": sender,
                "text": text,
                "rank": rank,
                "ip": ip,
                "source": source,
                "time": time.strftime("%H:%M")
            }
            self.messages.append(msg)
            self.save_messages()
            return msg

    def _load_friends(self):
        if FRIENDS_FILE.exists():
            try:
                with open(FRIENDS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def save_friends(self):
        try:
            with open(FRIENDS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.friends, f, indent=2)
        except Exception:
            pass

    def add_friend(self, username, ip="Unknown"):
        with self.lock:
            for f in self.friends:
                if f.get("username", "").lower() == username.lower():
                    return False
            self.friends.append({
                "username": username,
                "ip": ip,
                "added_at": time.strftime("%Y-%m-%d %H:%M"),
                "status": "Online // Ally"
            })
            self.save_friends()
            return True

    def _load_shared_catalog(self):
        if SHARED_CATALOG_FILE.exists():
            try:
                with open(SHARED_CATALOG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def save_shared_catalog(self, catalog):
        with self.lock:
            self.shared_hydra_sources = catalog
            try:
                with open(SHARED_CATALOG_FILE, "w", encoding="utf-8") as f:
                    json.dump(self.shared_hydra_sources, f, indent=2)
            except Exception:
                pass

node_state = RevNodeState(app_name="Revision-Web", default_port=8765)

class RevNodeHTTPHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        client_ip = self.client_address[0]
        parsed = urlparse(self.path)
        path = parsed.path

        node_state.register_peer(client_ip, f"User_{client_ip.split('.')[-1]}", port=8765)
        node_state.cleanup_peers()

        if path in ["/api/status", "/api/network/status"]:
            with node_state.lock:
                peers_list = list(node_state.active_peers.values())
                uptime_sec = int(time.time() - node_state.start_time)
                active_count = len(peers_list)
            self._send_json({
                "app": node_state.app_name,
                "node_id": node_state.node_id,
                "local_ip": node_state.local_ip,
                "vpn_ip": node_state.vpn_ip,
                "vpn_active": node_state.vpn_active,
                "ddos_shield": "ACTIVE" if node_state.vpn_active else "STANDBY",
                "port": node_state.port,
                "uptime": uptime_sec,
                "power_score": node_state.power_score,
                "active_peers_count": active_count,
                "peers": peers_list,
                "role": "Decentralized P2P Mesh Relay"
            })

        elif path in ["/api/peers", "/api/network/peers"]:
            with node_state.lock:
                peers_list = list(node_state.active_peers.values())
            self._send_json({"count": len(peers_list), "peers": peers_list})

        elif path == "/api/messages":
            with node_state.lock:
                msgs = list(node_state.messages)
            self._send_json({"messages": msgs})

        elif path == "/api/friends":
            with node_state.lock:
                friends = list(node_state.friends)
            self._send_json({"friends": friends})

        elif path == "/api/pending-requests":
            with node_state.lock:
                reqs = list(node_state.pending_requests)
            self._send_json({"requests": reqs})

        elif path in ["/api/ecosystem/apps", "/api/apps"]:
            # Check local Revision apps connectivity
            status_map = {
                "Revision-Web": {"port": 8765, "online": _check_local_port(8765)},
                "Revision-Ai": {"port": 8766, "online": _check_local_port(8766)},
                "Rev-Launcher": {"port": 8767, "online": _check_local_port(8767)},
                "Rev-Website-Origin": {"port": 8000, "online": _check_local_port(8000)}
            }
            self._send_json({"status": "OK", "ecosystem": status_map})

        elif path in ["/api/hydra/catalog", "/api/catalog"]:
            with node_state.lock:
                catalog = list(node_state.shared_hydra_sources)
            self._send_json({"status": "OK", "catalog": catalog})

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        client_ip = self.client_address[0]
        parsed = urlparse(self.path)
        path = parsed.path

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length)
            body = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except Exception:
            body = {}

        if path == "/api/send":
            sender = body.get("sender", "Anonymous").strip() or "Anonymous"
            text = body.get("text", "").strip()
            rank = body.get("rank", "Pilot")
            if text:
                msg = node_state.add_message(sender, text, rank, client_ip)
                node_state.register_peer(client_ip, sender, rank)
                self._send_json({"status": "OK", "message": msg})
            else:
                self._send_json({"status": "ERROR", "error": "Empty message"}, 400)

        elif path == "/api/register-user":
            username = body.get("username", "").strip()
            rank = body.get("rank", "Commander")
            if username:
                node_state.register_peer(client_ip, username, rank)
                self._send_json({"status": "OK"})
            else:
                self._send_json({"status": "ERROR"}, 400)

        elif path == "/api/friend-request":
            from_user = body.get("from_user", "Pilot").strip()
            with node_state.lock:
                node_state.pending_requests.append({
                    "from_user": from_user,
                    "from_ip": client_ip,
                    "timestamp": time.strftime("%H:%M")
                })
            self._send_json({"status": "OK"})

        elif path == "/api/respond-request":
            from_user = body.get("from_user", "").strip()
            accepted = body.get("accepted", True)
            with node_state.lock:
                node_state.pending_requests = [r for r in node_state.pending_requests if r.get("from_user") != from_user]
                if accepted and from_user:
                    node_state.add_friend(from_user, client_ip)
            self._send_json({"status": "OK"})

        elif path in ["/api/community/auth/register", "/api/register"]:
            username = body.get("username", "").strip()
            password = body.get("password", "").strip()
            if username:
                node_state.register_peer(client_ip, username, rank="Commander")
                self._send_json({"status": "ok", "message": "Callsign reserved successfully across local node!", "username": username})
            else:
                self._send_json({"error": "Empty callsign"}, 400)

        elif path in ["/api/community/auth/login", "/api/login"]:
            username = body.get("username", "").strip()
            password = body.get("password", "").strip()
            if username:
                node_state.register_peer(client_ip, username, rank="Commander")
                self._send_json({"status": "ok", "message": "Verified. Loading pilot profile...", "username": username})
            else:
                self._send_json({"error": "Empty callsign"}, 400)

        elif path in ["/api/ecosystem/launch", "/api/launch"]:
            target_app = body.get("app", "").strip()
            launched = _launch_ecosystem_app(target_app)
            self._send_json({"status": "OK" if launched else "ERROR", "launched": target_app})

        elif path in ["/api/hydra/catalog", "/api/catalog"]:
            new_sources = body.get("sources", [])
            if isinstance(new_sources, list):
                node_state.save_shared_catalog(new_sources)
                self._send_json({"status": "OK", "count": len(new_sources)})
            else:
                self._send_json({"status": "ERROR"}, 400)

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

def _check_local_port(port: int) -> bool:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.3)
        res = s.connect_ex(("127.0.0.1", port))
        s.close()
        return res == 0
    except Exception:
        return False

def _launch_ecosystem_app(target_app: str) -> bool:
    import subprocess
    target_app_lower = target_app.lower()
    base_projects = Path(r"C:\Users\ZarTo\Desktop\Projects")
    try:
        if "web" in target_app_lower:
            script = base_projects / "Rev-Network" / "main.py"
            subprocess.Popen([sys.executable, str(script)], cwd=str(script.parent))
            return True
        elif "ai" in target_app_lower:
            script = base_projects / "Revision-Ai" / "main.py"
            subprocess.Popen([sys.executable, str(script)], cwd=str(script.parent))
            return True
        elif "launcher" in target_app_lower:
            script = base_projects / "Rev-Launcher" / "main.py"
            if script.exists():
                subprocess.Popen([sys.executable, str(script)], cwd=str(script.parent))
                return True
    except Exception as e:
        print(f"[ECOSYSTEM LAUNCH ERROR] Failed to start {target_app}: {e}")
    return False

# ─── P2P UDP LAN Broadcast & Discovery ─────────────────────────────────────
def _run_udp_broadcast(port: int, app_name: str):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    while True:
        try:
            msg = json.dumps({
                "magic": "REV_P2P_V2",
                "app": app_name,
                "node_id": node_state.node_id,
                "port": port,
                "power_score": node_state.power_score,
                "time": time.time()
            }).encode("utf-8")
            s.sendto(msg, ("<broadcast>", UDP_DISCOVERY_PORT))
        except Exception:
            pass
        time.sleep(8)

def _run_udp_listener(my_port: int):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except Exception:
        pass
    try:
        s.bind(("", UDP_DISCOVERY_PORT))
        while True:
            try:
                data, addr = s.recvfrom(2048)
                payload = json.loads(data.decode("utf-8"))
                if payload.get("magic") == "REV_P2P_V2":
                    peer_ip = addr[0]
                    peer_port = payload.get("port", 8765)
                    peer_app = payload.get("app", "Revision-App")
                    peer_power = payload.get("power_score", 15.0)
                    if not (peer_ip in ["127.0.0.1", node_state.local_ip] and peer_port == my_port):
                        node_state.register_peer(
                            ip=peer_ip,
                            username=f"{peer_app} Pilot",
                            rank="Ally",
                            port=peer_port,
                            app=peer_app,
                            is_self=False,
                            power=peer_power
                        )
            except Exception:
                pass
    except Exception as e:
        pass

# ─── Heartbeat to Origin Server (DDNS / Localhost) ─────────────────────────
def _heartbeat_to_origin():
    import ssl
    ssl_unverified = ssl._create_unverified_context()
    origin_url = os.environ.get("REV_ORIGIN_URL", "https://rev-network.ddns.net:8000")
    endpoint = f"{origin_url.rstrip('/')}/api/register-node"
    
    # Try localhost first, then DDoS-shielded VPN, then DDNS
    endpoints = [
        "http://127.0.0.1:8000/api/register-node",
        "http://26.68.132.89:8000/api/register-node",
        endpoint
    ]

    while True:
        payload = json.dumps({
            "node_id": node_state.node_id,
            "app": node_state.app_name,
            "port": node_state.port,
            "vpn_ip": node_state.vpn_ip,
            "ddos_shield": node_state.vpn_active,
            "role": "DDoS-Shielded Community Mesh Relay",
            "power_score": node_state.power_score
        }).encode("utf-8")

        for ep in endpoints:
            try:
                from urllib.request import Request, urlopen
                req = Request(ep, data=payload, headers={"Content-Type": "application/json"})
                with urlopen(req, timeout=4, context=ssl_unverified if ep.startswith("https") else None) as resp:
                    if resp.status == 200:
                        break
            except Exception:
                pass
        time.sleep(20)

class RevNetworkServer:
    def __init__(self, port=8765, app_name="Revision-Web"):
        self.port = port
        self.app_name = app_name
        self.server = None
        self.thread = None

    def start(self):
        try:
            self.server = ThreadingHTTPServer(("0.0.0.0", self.port), RevNodeHTTPHandler)
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            print(f"[REV-NETWORK P2P] Active peer node server online on port {self.port} (IP: {node_state.local_ip})")
            
            # Start background P2P threads
            threading.Thread(target=_heartbeat_to_origin, daemon=True).start()
            threading.Thread(target=_run_udp_broadcast, args=(self.port, self.app_name), daemon=True).start()
            threading.Thread(target=_run_udp_listener, args=(self.port,), daemon=True).start()
        except Exception as e:
            print(f"[REV-NETWORK P2P ERROR] Failed starting on port {self.port}: {e}")

    def stop(self):
        if self.server:
            self.server.shutdown()

rev_server = RevNetworkServer(port=8765, app_name="Revision-Web")
