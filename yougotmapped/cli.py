import argparse
from pathlib import Path
from datetime import datetime

from yougotmapped.utils.dependencies import check_dependencies
from yougotmapped.utils.network import get_public_ip, get_geolocation
from yougotmapped.utils.ping import ping_target, format_ping_result
from yougotmapped.utils.jitter import jitter_test, format_jitter_result
from yougotmapped.utils.mss import discover_mss, format_mss_result
from yougotmapped.utils.bandwidth import estimate_bandwidth, format_bandwidth_result
from yougotmapped.utils.trace import run_traceroute, format_traceroute
from yougotmapped.utils.anonymity import detect_anonymity, format_anonymity_result
from yougotmapped.utils.mapping import (
    plot_ip_location,
    plot_multiple_ip_locations,
    plot_traceroute_path,
    save_map,
)
from yougotmapped.utils.output import write_output

def parse_args():
    parser = argparse.ArgumentParser(
        description="Geolocate IPs/domains, analyze network paths, and visualize routing."
    )

    parser.add_argument("-i", "--ip", nargs="*", help="IP addresses or domains")
    parser.add_argument("-f", "--file", help="File with IPs/domains (one per line)")

    parser.add_argument("-p", "--ping", action="store_true", help="Ping test")
    parser.add_argument("-j", "--jitter", action="store_true", help="Jitter analysis")
    parser.add_argument("-m", "--mtu", action="store_true", help="MTU/MSS discovery")
    parser.add_argument("-b", "--bandwidth", action="store_true", help="Bandwidth estimate")
    parser.add_argument("-t", "--trace", action="store_true", help="Traceroute")

    parser.add_argument("-c", "--hidecheck", action="store_true", help="Anonymity detection")
    parser.add_argument("-a", "--all", action="store_true", help="Run all modules")

    parser.add_argument("--no-map", action="store_true", help="Disable map output")
    parser.add_argument(
        "-o",
        "--output",
        help="Output file or shorthand (f:json, f:csv, f:normal)",
    )

    return parser.parse_args()


def collect_targets(args) -> list[str]:
    targets: list[str] = []

    if args.ip:
        targets.extend(args.ip)

    if args.file:
        try:
            with open(args.file, "r") as f:
                targets.extend(line.strip() for line in f if line.strip())
        except FileNotFoundError:
            print(f"File not found: {args.file}")

    if not targets:
        print("No input provided. Defaulting to public IP.")
        public_ip = get_public_ip()
        if public_ip:
            targets.append(public_ip)

    return targets


def print_geo_rich(geo: dict) -> None:
    raw = geo.get("raw", {})
    connection = raw.get("connection", {})
    timezone = raw.get("timezone", {})

    print("\n[ GEOLOCATION ]")
    print(f"IP:            {raw.get('ip')}")
    print(f"Type:          {raw.get('type')}")
    print(f"ASN:           AS{connection.get('asn')}" if connection.get("asn") else "ASN:           N/A")
    print(f"ISP / Org:     {connection.get('org') or connection.get('isp') or 'N/A'}")
    print(f"Domain:        {connection.get('domain') or 'N/A'}")

    print("\n[ LOCATION ]")
    print(f"Continent:     {raw.get('continent')} ({raw.get('continent_code')})")
    print(f"Country:       {raw.get('country')} ({raw.get('country_code')})")
    print(f"Region:        {raw.get('region')} ({raw.get('region_code')})")
    print(f"City:          {raw.get('city')}")
    print(f"Postal Code:   {raw.get('postal') or ''}")
    print(f"Latitude:      {raw.get('latitude')}")
    print(f"Longitude:     {raw.get('longitude')}")
    print(f"Capital:       {raw.get('capital')}")
    print(f"Borders:       {raw.get('borders')}")

    print("\n[ TIMEZONE ]")
    print(f"Zone:          {timezone.get('id')}")
    print(f"Abbreviation:  {timezone.get('abbr')}")
    print(f"UTC Offset:    {timezone.get('utc')}")
    print(f"DST Active:    {timezone.get('is_dst')}")
    print(f"Local Time:    {timezone.get('current_time')}")


def main():
    args = parse_args()
    check_dependencies()

    if args.all:
        args.ping = True
        args.jitter = True
        args.mtu = True
        args.bandwidth = True
        args.trace = True
        args.hidecheck = True

    targets = collect_targets(args)
    if not targets:
        print("No valid targets to process.")
        return

    results = []
    geos_for_map = []
    last_trace_result = None

    for target in targets:
        print(f"\nTarget: {target}")

        geo = get_geolocation(target)
        if not geo:
            print("Failed to retrieve geolocation data.")
            continue

        results.append(geo)
        geos_for_map.append(geo)

        print_geo_rich(geo)

        ping_result = None
        trace_result = None

        if args.ping:
            print("\n[ PING ]")
            ping_result = ping_target(target)
            format_ping_result(ping_result)
            geo["ping"] = ping_result

            if not ping_result.get("reachable"):
                print("Stopping analysis: host unreachable.")
                continue

        if args.jitter:
            print("\n[ JITTER ]")
            jitter_result = jitter_test(target)
            format_jitter_result(jitter_result)
            geo["jitter"] = jitter_result

        if args.mtu:
            print("\n[ MSS ]")
            mss_result = discover_mss(target)
            format_mss_result(mss_result)
            geo["mss"] = mss_result

        if args.bandwidth:
            print("\n[ BANDWIDTH ]")
            bandwidth_result = estimate_bandwidth(ping_result)
            format_bandwidth_result(bandwidth_result)
            geo["bandwidth"] = bandwidth_result

        if args.trace:
            print("\n[ TRACEROUTE ]")
            trace_result = run_traceroute(target)
            format_traceroute(trace_result)
            geo["traceroute"] = trace_result
            last_trace_result = trace_result

        if args.hidecheck:
            print("\n[ ANONYMITY ]")
            anonymity = detect_anonymity(geo)
            format_anonymity_result(anonymity)
            geo["anonymity"] = anonymity


    map_path = None
    if geos_for_map and not args.no_map:
        if len(geos_for_map) == 1:
            m = plot_ip_location(geos_for_map[0])
            if m and args.trace and last_trace_result:
                plot_traceroute_path(last_trace_result, m)
        else:
            m = plot_multiple_ip_locations(geos_for_map)

        if m:
            map_path = save_map(m, "ip_geolocation_map.html")


    output_path = None
    if args.output:
        Path("logs").mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%m-%d-%y--%H-%M")

        if args.output.startswith("f:"):
            fmt = args.output[2:].lower()
            ext = "json" if fmt == "json" else "csv" if fmt == "csv" else "txt"
            name = targets[0].replace(":", "-").replace("/", "-")
            filename = f"{name}--{timestamp}--YouGotMapped.{ext}"
        else:
            filename = args.output
            fmt = filename.split(".")[-1].lower()

        output_path = write_output(results, Path("logs") / filename, fmt=fmt)

    if map_path or output_path:
        print("\nOutput Summary")
        if map_path:
            print(f"  Map: file://{map_path}")
        if output_path:
            print(f"  Log: file://{output_path}")


if __name__ == "__main__":
    main()
