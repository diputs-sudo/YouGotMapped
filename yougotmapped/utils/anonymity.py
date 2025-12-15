# yougotmapped/utils/anonymity.py

import requests
from functools import lru_cache

TOR_EXIT_LIST_URL = "https://check.torproject.org/torbulkexitlist"

VPN_KEYWORDS = {
    "vpn", "proxy", "tor", "hosting", "cloud", "server", "colo",
    "digitalocean", "linode", "ovh", "vultr", "hetzner", "leaseweb",
    "m247", "nord", "express", "surfshark", "proton", "fastly",
    "akamai", "cloudflare", "google", "amazon", "aws", "azure"
}

@lru_cache(maxsize=1)
def _get_tor_exit_nodes() -> set[str]:
    try:
        resp = requests.get(TOR_EXIT_LIST_URL, timeout=10)
        resp.raise_for_status()
        return set(
            line.strip()
            for line in resp.text.splitlines()
            if line and not line.startswith("#")
        )
    except Exception:
        return set()


def is_tor_exit_node(ip: str) -> bool:
    if not ip:
        return False
    return ip in _get_tor_exit_nodes()

def _contains_vpn_keyword(value: str | None) -> bool:
    if not value:
        return False
    value = value.lower()
    return any(keyword in value for keyword in VPN_KEYWORDS)

def detect_anonymity(ip_data: dict) -> dict:
    ip = ip_data.get("ip")
    hostname = ip_data.get("hostname")
    org = ip_data.get("org")
    raw = ip_data.get("raw", {})

    tor = is_tor_exit_node(ip)

    # ipwho.is connection hints
    connection = raw.get("connection", {})
    isp = connection.get("isp")
    domain = connection.get("domain")
    asn = connection.get("asn")

    vpn = any([
        _contains_vpn_keyword(org),
        _contains_vpn_keyword(hostname),
        _contains_vpn_keyword(isp),
        _contains_vpn_keyword(domain),
    ])

    return {
        "ip": ip,
        "tor": tor,
        "vpn": vpn,
        "hostname": hostname,
        "org": org,
        "isp": isp,
        "asn": asn,
        "confidence": _confidence_score(tor, vpn),
    }

def _confidence_score(tor: bool, vpn: bool) -> str:
    if tor:
        return "very high"
    if vpn:
        return "high"
    return "low"


def format_anonymity_result(result: dict) -> None:
    print(f"IP: {result.get('ip')}")
    print(f"Hostname: {result.get('hostname') or 'N/A'}")
    print(f"Org / ISP: {result.get('org') or result.get('isp') or 'N/A'}")

    print(f"Tor Exit Node: {'YES' if result['tor'] else 'No'}")
    print(f"VPN / Proxy Suspected: {'YES' if result['vpn'] else 'No'}")
    print(f"Confidence: {result.get('confidence', 'unknown').upper()}")
