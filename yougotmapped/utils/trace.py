import subprocess
import platform
import ipaddress
import re

from yougotmapped.utils.network import get_hop_location


IP_REGEX = re.compile(r"(\d{1,3}(?:\.\d{1,3}){3})")
RTT_REGEX = re.compile(r"(\d+(?:\.\d+)?)\s*ms")


def _is_private_ip(ip: str) -> bool:
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return False


def _build_traceroute_command(host: str, max_hops: int) -> list[str]:
    if platform.system() == "Windows":
        return ["tracert", "-h", str(max_hops), host]

    return ["traceroute", "-m", str(max_hops), "-w", "1", host]


def run_traceroute(
    host: str,
    max_hops: int = 30,
    timeout: int = 60,
) -> dict:
    cmd = _build_traceroute_command(host, max_hops)

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"error": "Traceroute timed out"}
    except FileNotFoundError:
        return {"error": "Traceroute command not found"}
    except Exception as exc:
        return {"error": str(exc)}

    hops = []

    for index, line in enumerate(proc.stdout.splitlines(), start=1):
        ips = IP_REGEX.findall(line)
        if not ips:
            continue

        ip = ips[0]
        private = _is_private_ip(ip)

        rtts = [float(x) for x in RTT_REGEX.findall(line)]
        rtt_ms = rtts if rtts else None

        hop_geo = None
        if not private:
            hop_geo = get_hop_location(ip)

        hops.append({
            "hop": index,
            "ip": ip,
            "private": private,
            "rtt_ms": rtt_ms,
            "latitude": hop_geo.get("latitude") if hop_geo else None,
            "longitude": hop_geo.get("longitude") if hop_geo else None,
        })

    return {
        "target": host,
        "hops": hops,
    }


def format_traceroute(result: dict) -> None:
    if "error" in result:
        print(f"Traceroute error: {result['error']}")
        return

    for hop in result.get("hops", []):
        hop_no = hop["hop"]
        ip = hop["ip"]
        label = "PRIVATE" if hop["private"] else "PUBLIC"

        rtt = hop["rtt_ms"]
        rtt_display = (
            f"{min(rtt):.1f} ms" if isinstance(rtt, list) else "*"
        )

        print(f"[{hop_no:>2}] {ip:<15} {label:<7} {rtt_display}")
