# Ingress Geography Finder

from yougotmapped.utils.network import get_hop_location


def find_ingress_geography(trace_result: dict, target_asn: int | None) -> dict:
    
    if not trace_result or not target_asn:
        return {
            "available": False,
            "reason": "missing_data",
        }

    hops = trace_result.get("hops", [])
    previous_asn = None

    for hop in hops:
        if hop.get("private"):
            continue

        hop_asn = hop.get("asn")
        hop_ip = hop.get("ip")

        if hop_asn is None:
            previous_asn = hop_asn
            continue

        if previous_asn != hop_asn and hop_asn == target_asn:
            loc = get_hop_location(hop_ip)
            if not loc:
                return {
                    "available": False,
                    "reason": "geo_lookup_failed",
                }

            lat, lon = loc

            return {
                "available": True,
                "ingress_hop": hop["hop"],
                "ip": hop_ip,
                "asn": hop_asn,
                "latitude": lat,
                "longitude": lon,
            }

        previous_asn = hop_asn

    return {
        "available": False,
        "reason": "ingress_not_detected",
    }


def format_ingress_result(result: dict) -> None:
    
    if not result.get("available"):
        print("Ingress geography could not be determined.")
        return

    print("Ingress Geography:")
    print(f"  Hop:        {result['ingress_hop']}")
    print(f"  IP:         {result['ip']}")
    print(f"  ASN:        AS{result['asn']}")
    print(
        f"  Coordinates:{result['latitude']:.3f}, {result['longitude']:.3f}"
    )
