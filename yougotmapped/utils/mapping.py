from pathlib import Path
import folium

DEFAULT_GEO_RADIUS_KM = 40  # IP geolocation uncertainty radius


def plot_ip_location(geo: dict):

    lat = geo.get("latitude")
    lon = geo.get("longitude")

    if lat is None or lon is None:
        return None

    m = folium.Map(location=[lat, lon], zoom_start=6)

    # Destination marker
    folium.Marker(
        location=[lat, lon],
        popup=f"IP: {geo.get('ip')}",
        icon=folium.Icon(color="red", icon="info-sign"),
    ).add_to(m)

    # Uncertainty circle 
    folium.Circle(
        location=[lat, lon],
        radius=DEFAULT_GEO_RADIUS_KM * 1000,  # meters
        color="red",
        fill=True,
        fill_color="red",
        fill_opacity=0.15,
        popup="Approximate IP geolocation",
    ).add_to(m)

    return m


def plot_multiple_ip_locations(geos: list[dict]):

    coords = [
        (g.get("latitude"), g.get("longitude"))
        for g in geos
        if g.get("latitude") is not None and g.get("longitude") is not None
    ]

    if not coords:
        return None

    avg_lat = sum(lat for lat, _ in coords) / len(coords)
    avg_lon = sum(lon for _, lon in coords) / len(coords)

    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=3)

    for geo in geos:
        lat = geo.get("latitude")
        lon = geo.get("longitude")
        if lat is None or lon is None:
            continue

        folium.Marker(
            location=[lat, lon],
            popup=f"IP: {geo.get('ip')}",
            icon=folium.Icon(color="red", icon="info-sign"),
        ).add_to(m)

        folium.Circle(
            location=[lat, lon],
            radius=DEFAULT_GEO_RADIUS_KM * 1000,
            color="red",
            fill=True,
            fill_color="red",
            fill_opacity=0.15,
        ).add_to(m)

    return m


def plot_traceroute_path(trace_result: dict, m):

    hops = trace_result.get("hops", [])
    prev = None

    for hop in hops:
        lat = hop.get("latitude")
        lon = hop.get("longitude")

        if lat is None or lon is None:
            continue

        point = [lat, lon]

        # Hop marker (no circle)
        folium.CircleMarker(
            location=point,
            radius=4,
            color="blue",
            fill=True,
            fill_opacity=0.9,
            popup=f"Hop {hop.get('hop')} ({hop.get('ip')})",
        ).add_to(m)

        if prev:
            folium.PolyLine(
                locations=[prev, point],
                color="blue",
                weight=2,
                opacity=0.6,
            ).add_to(m)

        prev = point


def save_map(m, filename: str) -> str:
    
    path = Path(filename).resolve()
    m.save(str(path))
    return str(path)
