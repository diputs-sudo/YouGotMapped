from ping3 import ping
import statistics


FIBER_SPEED_KM_PER_MS = 200 # physical upper bound
REAL_WORLD_FACTOR = 0.5 # routing + overhead penalty
EFFECTIVE_SPEED = FIBER_SPEED_KM_PER_MS * REAL_WORLD_FACTOR


def estimate_distance_km(rtt_ms: float) -> tuple[int, int, int]:
    one_way_ms = rtt_ms / 2

    estimated = one_way_ms * EFFECTIVE_SPEED

    min_km = int(estimated * 0.7)
    max_km = int(estimated * 1.3)

    return int(min_km), int(estimated), int(max_km)


def classify_latency(rtt_ms: float) -> str:
    if rtt_ms < 1:
        return "Loopback or same-host"
    if rtt_ms < 5:
        return "Local network / same building"
    if rtt_ms < 20:
        return "Metro or nearby region"
    if rtt_ms < 50:
        return "Regional / same country"
    if rtt_ms < 100:
        return "Inter-country"
    if rtt_ms < 200:
        return "Intercontinental"
    return "Very distant or routed via relay/VPN"


def ping_target(host: str, count: int = 5, timeout: float = 1.0) -> dict:
    latencies = []

    for _ in range(count):
        try:
            delay = ping(host, timeout=timeout)
            if delay is not None:
                latencies.append(delay * 1000)  # ms
        except Exception:
            continue

    sent = count
    received = len(latencies)
    lost = sent - received

    if received == 0:
        return {
            "reachable": False,
            "sent": sent,
            "received": 0,
            "packet_loss_percent": 100.0,
        }

    min_rtt = round(min(latencies), 2)
    avg_rtt = round(statistics.mean(latencies), 2)
    med_rtt = round(statistics.median(latencies), 2)
    max_rtt = round(max(latencies), 2)

    min_km, est_km, max_km = estimate_distance_km(med_rtt)

    return {
        "reachable": True,
        "sent": sent,
        "received": received,
        "packet_loss_percent": round((lost / sent) * 100, 1),
        "rtt_ms": {
            "min": min_rtt,
            "avg": avg_rtt,
            "median": med_rtt,
            "max": max_rtt,
        },
        "distance_km": {
            "estimated": est_km,
            "min": min_km,
            "max": max_km,
        },
        "classification": classify_latency(med_rtt),
    }


def format_ping_result(result: dict) -> None:
    if not result.get("reachable"):
        print("Host unreachable (100% packet loss)")
        return

    print(f"Packets: sent={result['sent']} received={result['received']}")
    print(f"Packet loss: {result['packet_loss_percent']}%")

    rtt = result["rtt_ms"]
    print(
        f"RTT (ms): min={rtt['min']} avg={rtt['avg']} "
        f"median={rtt['median']} max={rtt['max']}"
    )

    dist = result["distance_km"]
    print(
        f"Estimated distance: ~{dist['estimated']} km "
        f"(range {dist['min']}–{dist['max']} km)"
    )

    print(f"Inference: {result['classification']}")
