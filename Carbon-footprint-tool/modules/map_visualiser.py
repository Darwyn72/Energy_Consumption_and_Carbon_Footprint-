"""
map_visualiser.py
-----------------
Creates interactive world maps using Folium.

Features:
  - Plot origin → destination great-circle routes (curved arcs)
  - Colour-code by CO2 level (green → yellow → red)
  - Popup markers with journey details
  - Supports multiple routes on one map
  - Save to HTML or display in Jupyter
"""

import math
from typing import List, Dict, Optional

try:
    import folium
    from folium import plugins
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False
    print("Warning: folium not installed. Run: pip install folium")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


def _co2_to_colour(co2_kg: float) -> str:
    """Map CO2 kg to a hex colour: low=green, medium=orange, high=red."""
    if co2_kg < 50:
        return "#2ecc71"    # Green
    elif co2_kg < 200:
        return "#f39c12"    # Orange
    elif co2_kg < 500:
        return "#e67e22"    # Dark orange
    elif co2_kg < 1000:
        return "#e74c3c"    # Red
    else:
        return "#8e44ad"    # Purple (very high)


def _co2_label(co2_kg: float) -> str:
    """Human-readable CO2 label with comparison."""
    if co2_kg < 10:
        return f"{co2_kg:.1f} kg CO₂e (very low)"
    elif co2_kg < 100:
        return f"{co2_kg:.1f} kg CO₂e (low)"
    elif co2_kg < 500:
        return f"{co2_kg:.0f} kg CO₂e (moderate)"
    elif co2_kg < 1500:
        return f"{co2_kg:.0f} kg CO₂e (high)"
    else:
        return f"{co2_kg:.0f} kg CO₂e (very high)"


def _great_circle_points(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
    n_points: int = 50
) -> List[tuple]:
    """
    Generate intermediate points along a great-circle arc.
    Returns list of (lat, lon) tuples.
    """
    if not NUMPY_AVAILABLE:
        # Simple linear interpolation fallback
        points = []
        for i in range(n_points + 1):
            t = i / n_points
            points.append((lat1 + t * (lat2 - lat1), lon1 + t * (lon2 - lon1)))
        return points

    import numpy as np

    # Convert to radians
    lat1_r, lon1_r = math.radians(lat1), math.radians(lon1)
    lat2_r, lon2_r = math.radians(lat2), math.radians(lon2)

    # Convert to Cartesian
    x1 = math.cos(lat1_r) * math.cos(lon1_r)
    y1 = math.cos(lat1_r) * math.sin(lon1_r)
    z1 = math.sin(lat1_r)
    x2 = math.cos(lat2_r) * math.cos(lon2_r)
    y2 = math.cos(lat2_r) * math.sin(lon2_r)
    z2 = math.sin(lat2_r)

    dot = min(1.0, max(-1.0, x1*x2 + y1*y2 + z1*z2))
    angle = math.acos(dot)

    if angle < 1e-6:
        return [(lat1, lon1), (lat2, lon2)]

    points = []
    for i in range(n_points + 1):
        t = i / n_points
        if angle > 1e-6:
            sin_angle = math.sin(angle)
            a = math.sin((1 - t) * angle) / sin_angle
            b = math.sin(t * angle) / sin_angle
        else:
            a, b = 1 - t, t
        x = a * x1 + b * x2
        y = a * y1 + b * y2
        z = a * z1 + b * z2
        lat = math.degrees(math.atan2(z, math.sqrt(x**2 + y**2)))
        lon = math.degrees(math.atan2(y, x))
        points.append((lat, lon))
    return points


def _make_popup_html(result: Dict) -> str:
    """Build HTML for a route popup card."""
    colour = _co2_to_colour(result["grand_total_co2_kg"])
    return f"""
    <div style="font-family: Arial, sans-serif; min-width: 260px; max-width: 320px;">
      <h4 style="margin:0 0 8px; color: #2c3e50;">
        ✈ {result['origin_resolved']} → {result['destination_resolved']}
      </h4>
      <table style="width:100%; border-collapse:collapse; font-size:13px;">
        <tr><td style="padding:3px 0;"><b>Route:</b></td>
            <td>{result.get('route_name','')}</td></tr>
        <tr><td><b>Distance:</b></td>
            <td>{result['total_distance_km']:,} km</td></tr>
        <tr><td><b>Cabin:</b></td>
            <td>{result.get('cabin_class','economy').title()}</td></tr>
        <tr><td><b>Return trip:</b></td>
            <td>{'Yes' if result['return_trip'] else 'No'}</td></tr>
        <tr><td><b>Transport CO₂:</b></td>
            <td>{result['total_transport_co2_kg']:.1f} kg CO₂e</td></tr>
        <tr><td><b>Hotel ({result['nights_at_destination']} nights):</b></td>
            <td>{result['hotel_co2_kg']:.1f} kg CO₂e</td></tr>
        <tr style="background:#f8f9fa;">
            <td><b>Total CO₂:</b></td>
            <td><b style="color:{colour};">{_co2_label(result['grand_total_co2_kg'])}</b></td></tr>
      </table>
      <p style="margin:6px 0 0; font-size:11px; color:#777;">
        Source: DEFRA 2025 / Google TIM
      </p>
    </div>
    """


def create_map(
    journey_results: List[Dict],
    map_title: str = "Conference Carbon Footprint Map",
    save_path: str = None,
    zoom_start: int = 2,
    show_legend: bool = True,
) -> Optional[object]:
    """
    Create an interactive Folium map with journey routes.

    Parameters
    ----------
    journey_results : list
        List of journey dicts from calculate_journey()
    map_title : str
        Title shown on the map
    save_path : str
        If provided, saves HTML map to this path
    zoom_start : int
        Initial zoom level (2 = world view)
    show_legend : bool
        Whether to show CO2 colour legend

    Returns
    -------
    folium.Map object (can be displayed in Jupyter)
    """
    if not FOLIUM_AVAILABLE:
        print("Error: folium not installed. Run: pip install folium")
        return None

    if not journey_results:
        print("No journey results to plot.")
        return None

    # Centre map on mean of all locations
    all_lats = []
    all_lons = []
    for r in journey_results:
        all_lats.extend([r["origin_coords"][0], r["destination_coords"][0]])
        all_lons.extend([r["origin_coords"][1], r["destination_coords"][1]])

    centre_lat = sum(all_lats) / len(all_lats)
    centre_lon = sum(all_lons) / len(all_lons)

    m = folium.Map(
        location=[centre_lat, centre_lon],
        zoom_start=zoom_start,
        tiles="CartoDB positron",
        attr="© OpenStreetMap contributors, CartoDB"
    )

    # Add title
    title_html = f"""
    <div style="position: fixed; top: 10px; left: 50%; transform: translateX(-50%);
                z-index: 9999; background-color: white; padding: 8px 18px;
                border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                font-family: Arial; font-size: 15px; font-weight: bold; color: #2c3e50;">
        🌍 {map_title}
    </div>
    """
    m.get_root().html.add_child(folium.Element(title_html))

    # Track unique cities to avoid duplicate markers
    plotted_cities = {}

    for result in journey_results:
        co2 = result["grand_total_co2_kg"]
        colour = _co2_to_colour(co2)
        popup_html = _make_popup_html(result)

        o_lat, o_lon = result["origin_coords"]
        d_lat, d_lon = result["destination_coords"]

        # Great-circle arc
        arc_points = _great_circle_points(o_lat, o_lon, d_lat, d_lon, n_points=80)

        folium.PolyLine(
            locations=arc_points,
            color=colour,
            weight=2.5,
            opacity=0.8,
            tooltip=f"{result['origin_resolved']} → {result['destination_resolved']}: {co2:.0f} kg CO₂e",
            popup=folium.Popup(popup_html, max_width=340)
        ).add_to(m)

        # Direction arrow at midpoint
        mid_idx = len(arc_points) // 2
        if mid_idx > 0:
            pass  # Arrow via CSS injection omitted for simplicity

        # City markers
        origin_key = result["origin_resolved"]
        dest_key = result["destination_resolved"]

        if origin_key not in plotted_cities:
            plotted_cities[origin_key] = True
            folium.CircleMarker(
                location=[o_lat, o_lon],
                radius=7,
                color="#2c3e50",
                fill=True,
                fill_color="#3498db",
                fill_opacity=0.9,
                tooltip=result["origin_resolved"],
                popup=folium.Popup(
                    f"<b>{result['origin_resolved']}</b><br>"
                    f"<small>{o_lat:.3f}°, {o_lon:.3f}°</small>",
                    max_width=200
                )
            ).add_to(m)

        if dest_key not in plotted_cities:
            plotted_cities[dest_key] = True
            folium.CircleMarker(
                location=[d_lat, d_lon],
                radius=9,
                color="#c0392b",
                fill=True,
                fill_color="#e74c3c",
                fill_opacity=0.9,
                tooltip=f"{result['destination_resolved']} (Destination)",
                popup=folium.Popup(
                    f"<b>{result['destination_resolved']} ⭐</b><br>"
                    f"Conference destination<br>"
                    f"<small>{d_lat:.3f}°, {d_lon:.3f}°</small>",
                    max_width=200
                )
            ).add_to(m)

    # Legend
    if show_legend:
        legend_html = """
        <div style="position: fixed; bottom: 30px; left: 20px; z-index: 9999;
                    background-color: white; padding: 12px 16px;
                    border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                    font-family: Arial; font-size: 12px;">
            <b>CO₂ Emission Level</b><br>
            <span style="color:#2ecc71;">●</span> &lt;50 kg – Very low<br>
            <span style="color:#f39c12;">●</span> 50–200 kg – Low<br>
            <span style="color:#e67e22;">●</span> 200–500 kg – Moderate<br>
            <span style="color:#e74c3c;">●</span> 500–1000 kg – High<br>
            <span style="color:#8e44ad;">●</span> &gt;1000 kg – Very high<br>
            <hr style="margin:6px 0;">
            <span style="color:#3498db;">●</span> Origin city<br>
            <span style="color:#e74c3c;">●</span> Conference venue
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))

    if save_path:
        m.save(save_path)
        print(f"Map saved to: {save_path}")

    return m


def plot_route_comparison(
    journey_results: List[Dict],
    figsize: tuple = (10, 6)
):
    """
    Create a matplotlib bar chart comparing CO2 across journeys.
    Useful as a static alternative to the interactive map.
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
    except ImportError:
        print("matplotlib not installed. Run: pip install matplotlib")
        return None

    labels = []
    transport_vals = []
    hotel_vals = []

    for r in journey_results:
        label = f"{r.get('attendee_label', r['origin_resolved'])}"
        labels.append(label)
        transport_vals.append(r["total_transport_co2_kg"])
        hotel_vals.append(r["hotel_co2_kg"])

    x = range(len(labels))
    fig, ax = plt.subplots(figsize=figsize)

    bars1 = ax.bar(x, transport_vals, label="Transport CO₂", color="#3498db", alpha=0.85)
    bars2 = ax.bar(x, hotel_vals, bottom=transport_vals, label="Hotel CO₂", color="#e74c3c", alpha=0.85)

    # Value labels
    for i, (tv, hv) in enumerate(zip(transport_vals, hotel_vals)):
        total = tv + hv
        ax.text(i, total + 5, f"{total:.0f} kg", ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=9)
    ax.set_ylabel("kg CO₂e")
    ax.set_title("Carbon Footprint by Journey", fontsize=13, fontweight="bold", pad=14)
    ax.legend(framealpha=0.9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_ylim(0, max(transport_vals[i] + hotel_vals[i] for i in range(len(labels))) * 1.2 + 10)

    plt.tight_layout()
    plt.show()
    return fig
