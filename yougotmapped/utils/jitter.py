# Jitter Utilities

from ping3 import ping
import statistics


def jitter_test(host: str, count: int = 20, timeout: float = 1.0) -> dict:

    rtts = []

    for _ in range(count):
        try:
            delay = ping(host, timeout=timeout)
            if delay is not None:
                rtts.append(delay * 1000)  # ms
        except Exception:
            continue

    sent = count
    received = len(rtts)
    lost = sent - received

    if received < 2:
        return {
            "reachable": False,
            "sent": sent,
            "received": received,
            "packet_loss_percent": round((lost / sent) * 100, 1),
        }

    median_rtt = statistics.median(rtts)

    jitter_ms = statistics.mean(abs(rtt - median_rtt) for rtt in rtts)

    min_rtt = round(min(rtts), 2)
    max_rtt = round(max(rtts), 2)
    median_rtt = round(median_rtt, 2)
    jitter_ms = round(jitter_ms, 2)

    if jitter_ms < 3:
        stability = "stable"
    elif jitter_ms < 10:
        stability = "moderate"
    else:
        stability = "unstable"

    return {
        "reachable": True,
        "sent": sent,
        "received": received,
        "packet_loss_percent": round((lost / sent) * 100, 1),
        "rtt_ms": {
            "min": min_rtt,
            "median": median_rtt,
            "max": max_rtt,
        },
        "jitter_ms": jitter_ms,
        "stability": stability,
    }


def format_jitter_result(result: dict) -> None:
    
    if not result.get("reachable"):
        print("Jitter test failed (insufficient replies).")
        return

    print(f"Packets: sent={result['sent']} received={result['received']}")
    print(f"Packet loss: {result['packet_loss_percent']}%")

    rtt = result["rtt_ms"]
    print(
        f"RTT (ms): min={rtt['min']} "
        f"median={rtt['median']} max={rtt['max']}"
    )

    print(f"Jitter: {result['jitter_ms']} ms")
    print(f"Stability: {result['stability'].upper()}")
