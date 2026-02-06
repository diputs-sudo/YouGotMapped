import random
import time
from typing import Dict, Optional

try:
    from scapy.all import IP, TCP, sr1, conf
    SCAPY_AVAILABLE = True
    conf.verb = 0
except Exception:
    SCAPY_AVAILABLE = False

def _probe_mss(
    host: str,
    port: int,
    mss: int,
    timeout: float = 1.0,
) -> bool:
    sport = random.randint(1024, 65535)

    pkt = (
        IP(dst=host, flags="DF")
        / TCP(
            sport=sport,
            dport=port,
            flags="S",
            seq=1000,
            options=[("MSS", mss)],
        )
    )

    resp = sr1(pkt, timeout=timeout)
    if resp is None:
        return False

    if resp.haslayer(TCP):
        flags = resp[TCP].flags
        return (flags & 0x12) == 0x12  # SYN+ACK

    return False


def _estimate_mss(
    rtt_ms: Optional[float],
    traceroute_ok: bool,
) -> Dict:
    if rtt_ms is None or not traceroute_ok:
        return {
            "mss": 1360,
            "confidence": "low",
            "reason": "mobile_or_cgnat_likely",
        }

    if rtt_ms > 40:
        return {
            "mss": 1360,
            "confidence": "low",
            "reason": "high_rtt_path",
        }

    if rtt_ms > 20:
        return {
            "mss": 1420,
            "confidence": "medium",
            "reason": "possible_tunneling",
        }

    return {
        "mss": 1460,
        "confidence": "medium",
        "reason": "standard_ethernet_assumed",
    }

def discover_mss(
    host: str,
    port: int = 443,
    *,
    median_rtt_ms: Optional[float] = None,
    traceroute_ok: bool = True,
) -> Dict:
    MIN_MSS = 536
    MAX_MSS = 1460

    if SCAPY_AVAILABLE:
        try:
            if _probe_mss(host, port, MIN_MSS):
                low = MIN_MSS
                high = MAX_MSS
                best = MIN_MSS

                while low <= high:
                    mid = (low + high) // 2
                    if _probe_mss(host, port, mid):
                        best = mid
                        low = mid + 1
                    else:
                        high = mid - 1
                    time.sleep(0.05)

                return {
                    "reachable": True,
                    "method": "tcp-mss",
                    "mss": best,
                    "confidence": "high",
                }

        except PermissionError:
            pass
        except Exception:
            pass

    est = _estimate_mss(median_rtt_ms, traceroute_ok)

    return {
        "reachable": True,
        "method": "estimated",
        "mss": est["mss"],
        "confidence": est["confidence"],
        "reason": est["reason"],
    }


def format_mss_result(result: Dict) -> None:
    if not result.get("reachable"):
        print("MSS unavailable.")
        return

    print(f"TCP MSS:  {result['mss']} bytes")
    print(f"Method:   {result['method'].upper()}")
    print(f"Confidence: {result.get('confidence', 'unknown').upper()}")

    if result.get("method") == "estimated":
        print(f"Reason:   {result.get('reason')}")
