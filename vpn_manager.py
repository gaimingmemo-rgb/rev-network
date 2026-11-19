import socket
import json

def detect_vpn_interface() -> dict:
    """
    Detects virtual private network adapters (Radmin VPN, WireGuard, Tailscale, ZeroTier, OpenVPN).
    Returns VPN status, IP, and adapter name to shield host from DDoS attacks.
    """
    info = {
        "active": False,
        "ip": None,
        "name": None,
        "type": "None",
        "shield_active": False
    }

    try:
        import psutil
        adapters = psutil.net_if_addrs()
        for iface_name, addrs in adapters.items():
            name_lower = iface_name.lower()
            if any(k in name_lower for k in ["radmin", "vpn", "wireguard", "tailscale", "zerotier", "wg0", "tun"]):
                for addr in addrs:
                    if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                        info["active"] = True
                        info["ip"] = addr.address
                        info["name"] = iface_name
                        info["shield_active"] = True
                        if "radmin" in name_lower:
                            info["type"] = "Radmin VPN"
                        elif "wireguard" in name_lower or "wg" in name_lower:
                            info["type"] = "WireGuard"
                        elif "tailscale" in name_lower:
                            info["type"] = "Tailscale"
                        elif "zerotier" in name_lower:
                            info["type"] = "ZeroTier"
                        else:
                            info["type"] = "Virtual VPN"
                        return info
    except Exception:
        pass

    # Fallback check using socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("26.0.0.1", 80)) # Radmin gateway
        ip = s.getsockname()[0]
        s.close()
        if ip and ip.startswith("26."):
            info["active"] = True
            info["ip"] = ip
            info["name"] = "Radmin VPN Adapter"
            info["type"] = "Radmin VPN"
            info["shield_active"] = True
            return info
    except Exception:
        pass

    return info

vpn_info = detect_vpn_interface()
