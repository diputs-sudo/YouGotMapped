import requests
import socket
import ipaddress

def is_private_ip(ip: str) -> bool:
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return False


def is_valid_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False

def get_public_ip() -> str | None:
    try:
        r = requests.get("https://api.ipify.org", timeout=5)
        r.raise_for_status()
        return r.text.strip()
    except Exception:
        return None

def resolve_domain_to_ip(domain: str) -> str | None:
    try:
        return socket.gethostbyname(domain)
    except socket.gaierror:
        return None


def get_geolocation(target: str) -> dict | None:
    ip = target

    if not is_valid_ip(target):
        ip = resolve_domain_to_ip(target)
        if not ip:
            return None

    if is_private_ip(ip):
        return {
            "ip": ip,
            "private": True,
            "note": "Private / non-routable address",
        }

    try:
        r = requests.get(
            f"https://ipwho.is/{ip}",
            timeout=6,
        )
        data = r.json()
    except Exception:
        return None

    if not data.get("success", False):
        return None

    return {
        "ip": ip,
        "hostname": data.get("hostname"),
        "org": data.get("connection", {}).get("isp"),
        "country": data.get("country"),
        "region": data.get("region"),
        "city": data.get("city"),
        "postal": data.get("postal"),
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "timezone": data.get("timezone", {}).get("id"),
        "raw": data,
    }


def get_hop_location(ip: str) -> dict | None:
    if is_private_ip(ip):
        return None

    try:
        r = requests.get(
            f"http://ip-api.com/json/{ip}?fields=status,lat,lon",
            timeout=4,
        )
        data = r.json()
    except Exception:
        return None

    if data.get("status") != "success":
        return None

    return {
        "latitude": data.get("lat"),
        "longitude": data.get("lon"),
    }
