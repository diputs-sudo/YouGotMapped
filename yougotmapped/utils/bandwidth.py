# yougotmapped/utils/bandwidth.py

import math


DEFAULT_MSS_BYTES = 1460  # Ethernet MTU 1500 - IP/TCP headers


def estimate_bandwidth(ping_result: dict, mss_bytes: int = DEFAULT_MSS_BYTES) -> dict:
    if not ping_result or not ping_result.get("reachable"):
        return {
            "available": False,
            "reason": "no_ping_data",
        }

    rtt_ms = ping_result["rtt_ms"]["median"]
    loss_percent = ping_result.get("packet_loss_percent", 0.0)

    rtt_sec = rtt_ms / 1000.0
    loss = loss_percent / 100.0

    if rtt_sec <= 0:
        return {
            "available": False,
            "reason": "invalid_rtt",
        }

    if loss == 0:
        throughput_bps = (mss_bytes * 8) / rtt_sec
        limiting_factor = "latency"
    else:
        throughput_bps = (mss_bytes * 8) / (rtt_sec * math.sqrt(loss))
        limiting_factor = "packet_loss"

    throughput_mbps = round(throughput_bps / 1_000_000, 2)

    return {
        "available": True,
        "estimated_mbps": throughput_mbps,
        "rtt_ms": rtt_ms,
        "packet_loss_percent": loss_percent,
        "limiting_factor": limiting_factor,
        "model": "tcp_mathis",
    }


def format_bandwidth_result(result: dict) -> None:
    if not result.get("available"):
        print("Bandwidth estimation unavailable.")
        return

    print(f"Estimated Throughput: ~{result['estimated_mbps']} Mbps")
    print(f"Limiting Factor: {result['limiting_factor'].replace('_', ' ').title()}")
    print("Model: TCP Mathis approximation")
