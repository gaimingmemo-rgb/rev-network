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

MESSAGES_FILE = DATA_DIR / "community_messages.json"
FRIENDS_FILE = DATA_DIR / "community_friends.json"

class RevNodeState:
    def __init__(self):
        self.lock = threading.Lock()
        self.port = 8765
        self.local_ip = self._get_local_ip()
        self.active_peers = {} # ip -> dict(ip, username, last_seen, rank)
        self.messages = self._load_messages()
        self.friends = self._load_friends()
        self.pending_requests = [] # list of dict(from_user, from_ip, timestamp)

        # Register self as the first active peer
        self.register_peer("127.0.0.1", "ZarTo (Host)", "Commander")

    def _get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def register_peer(self, ip, username, rank="Pilot"):
        with self.lock:
            now = time.time()
            self.active_peers[ip] = {
                "ip": ip,
                "username": username or f"Peer_{ip.replace('.', '_')}",
                "rank": rank,
                "last_seen": now,
                "is_self": ip in ["127.0.0.1", self.local_ip]
            }

    def cleanup_peers(self):
        with self.lock:
            now = time.time()
            to_del = []
            for ip, p in self.active_peers.items():
                if not p.get("is_self") and (now - p["last_seen"]) > 90:
                    to_del.append(ip)
            for ip in to_del:
                del self.active_peers[ip]

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

    def add_message(self, sender, text, rank="Pilot", ip="127.0.0.1"):
        with self.lock:
            msg = {
                "id": str(int(time.time() * 1000)),
                "sender": sender,
                "text": text,
                "rank": rank,
                "ip": ip,
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
                if f["username"].lower() == username.lower():
                    return False
            self.friends.append({
                "username": username,
                "ip": ip,
                "added_at": time.strftime("%Y-%m-%d %H:%M"),
                "status": "Online // Ally"
            })
            self.save_friends()
            return True

node_state = RevNodeState()

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

        # Track active peer
        node_state.register_peer(client_ip, f"User_{client_ip.split('.')[-1]}")
        node_state.cleanup_peers()

        if path == "/api/status":
            with node_state.lock:
                peers_list = list(node_state.active_peers.values())
                active_count = len(peers_list)
            self._send_json({
                "local_ip": node_state.local_ip,
                "port": node_state.port,
                "active_peers_count": active_count,
                "peers": peers_list
            })

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

        else:
            # Fallback 404
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
            from_user = body.get("from_user", "Techdudesigmaboy").strip()
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
                node_state.pending_requests = [r for r in node_state.pending_requests if r["from_user"] != from_user]
                if accepted and from_user:
                    node_state.add_friend(from_user, client_ip)
            self._send_json({"status": "OK"})

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Silent logging to prevent console spam
        pass


def _heartbeat_to_origin():
    import ssl
    ssl_unverified = ssl._create_unverified_context()
    origin_url = os.environ.get("REV_ORIGIN_URL", "https://rev-network.ddns.net:8000")
    node_id = f"rev-node-{int(time.time()*1000) % 100000}"
    endpoint = f"{origin_url.rstrip('/')}/api/register-node"
    while True:
        try:
            from urllib.request import Request, urlopen
            payload = json.dumps({
                "node_id": node_id,
                "app": "Rev Network",
                "port": 8765,
                "role": "Community Mesh Relay"
            }).encode("utf-8")
            req = Request(endpoint, data=payload, headers={"Content-Type": "application/json"})
            with urlopen(req, timeout=5, context=ssl_unverified) as resp:
                pass
        except Exception:
            pass
        time.sleep(20)
class RevNetworkServer:
    def __init__(self, port=8765):
        self.port = port
        self.server = None
        self.thread = None

    def start(self):
        try:
            self.server = ThreadingHTTPServer(("0.0.0.0", self.port), RevNodeHTTPHandler)
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            print(f"[REV NETWORK NODE] Live peer server active on port {self.port} (Local IP: {node_state.local_ip})")
            threading.Thread(target=_heartbeat_to_origin, daemon=True).start()
        except Exception as e:
            print(f"[REV NETWORK NODE ERROR] Failed starting on port {self.port}: {e}")

    def stop(self):
        if self.server:
            self.server.shutdown()

rev_server = RevNetworkServer()
