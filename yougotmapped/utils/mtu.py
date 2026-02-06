import platform
import subprocess


def _ping_df(host: str, payload_size: int, timeout: int = 1) -> bool:

    system = platform.system()

    if system == "Windows":
        cmd = [
            "ping",
            "-n", "1",
            "-f",
            "-l", str(payload_size),
            host,
        ]
    else:
        cmd = [
            "ping",
            "-c", "1",
            "-M", "do",
            "-s", str(payload_size),
            host,
        ]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
        )
        return result.returncode == 0
    except Exception:
        return False


def discover_mtu(host: str) -> dict:
    low = 1200
    high = 1472  # Ethernet MTU (1500)
    best = None

    while low <= high:
        mid = (low + high) // 2

        if _ping_df(host, mid):
            best = mid
            low = mid + 1
        else:
            high = mid - 1

    if best is None:
        return {
            "reachable": False,
        }

    mtu = best + 28  # add IP (20) + ICMP (8)

    if mtu >= 1500:
        path_type = "standard"
    elif mtu >= 1400:
        path_type = "pppoe / light tunneling"
    else:
        path_type = "vpn / heavy tunneling"

    return {
        "reachable": True,
        "mtu": mtu,
        "payload_size": best,
        "path_type": path_type,
    }


def format_mtu_result(result: dict) -> None:
    if not result.get("reachable"):
        print("MTU discovery failed (host unreachable or blocked).")
        return

    print(f"Path MTU: {result['mtu']} bytes")
    print(f"Payload Size: {result['payload_size']} bytes")
    print(f"Inference: {result['path_type'].upper()}")
