"""
carbon_calculator.py
---------------------
Core calculation engine.

Takes route legs (mode + distance) and computes:
  - CO2e per leg
  - Total journey CO2e
  - Return trip CO2e
  - Hotel stay CO2e
  - Summary report
"""

from typing import List, Dict, Optional
from datetime import datetime

from modules.emission_factors import (
    TRANSPORT_FACTORS,
    get_hotel_factor,
    get_transport_factor,
)
from modules.route_planner import (
    haversine_km,
    resolve_location,
    optimise_route,
    query_tim_api,
    MAJOR_CITIES,
)


# ---------------------------------------------------------------------------
# LEG CALCULATION
# ---------------------------------------------------------------------------

def calculate_leg_emissions(mode: str, distance_km: float) -> Dict:
    """
    Calculate emissions for a single transport leg.

    Returns:
        dict with mode, distance_km, factor, co2_kg, source, label
    """
    factor_info = get_transport_factor(mode)
    co2_kg = factor_info["factor"] * distance_km
    return {
        "mode": mode,
        "distance_km": round(distance_km, 2),
        "emission_factor": factor_info["factor"],
        "co2_kg": round(co2_kg, 3),
        "unit": factor_info["unit"],
        "source": factor_info["source"],
        "notes": factor_info.get("notes", ""),
    }


# ---------------------------------------------------------------------------
# JOURNEY CALCULATION
# ---------------------------------------------------------------------------

def calculate_journey(
    origin_str: str,
    destination_str: str,
    cabin_class: str = "economy",
    return_trip: bool = True,
    nights_at_destination: int = 0,
    tim_api_key: str = None,
    preferred_mode: str = None,   # If set, force this mode key
    custom_legs: List[Dict] = None,  # Override with manual legs
) -> Dict:
    """
    Full journey calculation from origin to destination.

    Parameters
    ----------
    origin_str : str
        City name (dropdown) or free-text address
    destination_str : str
        City name (dropdown) or free-text address
    cabin_class : str
        'economy', 'business', 'first'
    return_trip : bool
        If True, doubles the transport CO2 (assumes symmetric return)
    nights_at_destination : int
        Number of hotel nights at destination
    tim_api_key : str
        Google TIM API key (optional)
    preferred_mode : str
        Force a specific transport mode key (overrides optimisation)
    custom_legs : list
        Manual list of leg dicts [{mode, distance_km, label}, ...]

    Returns
    -------
    dict : Full journey result with legs, totals, hotel, and metadata
    """
    timestamp = datetime.now().isoformat()

    # 1. Resolve locations
    origin = resolve_location(origin_str)
    destination = resolve_location(destination_str)

    if not origin:
        raise ValueError(f"Could not resolve origin: '{origin_str}'")
    if not destination:
        raise ValueError(f"Could not resolve destination: '{destination_str}'")

    total_dist_km = haversine_km(
        origin["lat"], origin["lon"],
        destination["lat"], destination["lon"]
    )

    # 2. Build route options
    if custom_legs:
        # Manual legs provided
        route_options = [{
            "name": "Custom Route",
            "legs": custom_legs,
            "total_km": sum(l["distance_km"] for l in custom_legs),
            "total_co2_kg": None,
            "recommended": True,
        }]
        selected_option = route_options[0]
    else:
        route_options = optimise_route(
            origin, destination,
            cabin_class=cabin_class
        )
        if not route_options:
            raise ValueError("No viable route found between these locations.")

        # Select preferred mode or default to recommended (lowest CO2)
        selected_option = route_options[0]  # lowest CO2 by default
        if preferred_mode:
            for opt in route_options:
                if any(leg["mode"] == preferred_mode for leg in opt["legs"]):
                    selected_option = opt
                    break

    # 3. Calculate emissions per leg
    calculated_legs = []
    for leg in selected_option["legs"]:
        leg_result = calculate_leg_emissions(leg["mode"], leg["distance_km"])
        leg_result["label"] = leg.get("label", leg["mode"])
        calculated_legs.append(leg_result)

    # 4. TIM API enhancement for flight legs (if API key provided)
    tim_result = None
    for leg in calculated_legs:
        if "flight" in leg["mode"] and tim_api_key:
            origin_iata = origin.get("iata")
            dest_iata = destination.get("iata")
            if origin_iata and dest_iata:
                tim_result = query_tim_api(origin_iata, dest_iata, tim_api_key)
                if tim_result:
                    cabin_key = f"{cabin_class}_g_per_pax"
                    g_per_pax = tim_result.get(cabin_key) or tim_result.get("economy_g_per_pax")
                    if g_per_pax:
                        leg["co2_kg"] = round(g_per_pax / 1000, 3)
                        leg["source"] = "Google TIM API"
                        leg["notes"] = f"TIM typical flight emissions ({cabin_class} class)"

    # 5. Totals
    one_way_transport_co2 = sum(l["co2_kg"] for l in calculated_legs)
    multiplier = 2 if return_trip else 1
    total_transport_co2 = one_way_transport_co2 * multiplier

    # 6. Hotel emissions
    hotel_co2 = 0.0
    hotel_factor_info = None
    dest_country = destination.get("country", "")
    if nights_at_destination > 0:
        hotel_factor_info = get_hotel_factor(country_code=dest_country)
        hotel_co2 = hotel_factor_info["factor"] * nights_at_destination

    # 7. Grand total
    grand_total_co2 = total_transport_co2 + hotel_co2

    return {
        # Metadata
        "timestamp": timestamp,
        "origin": origin_str,
        "destination": destination_str,
        "origin_resolved": origin["display_name"],
        "destination_resolved": destination["display_name"],
        "origin_coords": (origin["lat"], origin["lon"]),
        "destination_coords": (destination["lat"], destination["lon"]),
        "origin_country": origin.get("country", ""),
        "destination_country": destination.get("country", ""),
        "origin_iata": origin.get("iata", ""),
        "destination_iata": destination.get("iata", ""),

        # Route
        "route_name": selected_option["name"],
        "total_distance_km": round(total_dist_km, 1),
        "cabin_class": cabin_class,
        "return_trip": return_trip,

        # Legs (one-way)
        "legs": calculated_legs,

        # CO2 breakdown
        "one_way_transport_co2_kg": round(one_way_transport_co2, 3),
        "transport_multiplier": multiplier,
        "total_transport_co2_kg": round(total_transport_co2, 3),

        # Hotel
        "nights_at_destination": nights_at_destination,
        "hotel_factor": hotel_factor_info,
        "hotel_co2_kg": round(hotel_co2, 3),

        # Grand total
        "grand_total_co2_kg": round(grand_total_co2, 3),

        # All route options for comparison
        "all_route_options": route_options,

        # TIM API data if used
        "tim_data": tim_result,
    }


# ---------------------------------------------------------------------------
# MULTI-JOURNEY BATCH CALCULATION
# ---------------------------------------------------------------------------

def calculate_multi_journey(
    journeys: List[Dict],
    return_trip: bool = True,
) -> Dict:
    """
    Calculate emissions for multiple journeys (e.g. all attendees travelling
    from different origins to the same conference city).

    journeys: list of dicts, each with keys matching calculate_journey() params
    """
    results = []
    total_co2 = 0.0
    errors = []

    for i, j in enumerate(journeys):
        try:
            result = calculate_journey(
                origin_str=j["origin"],
                destination_str=j["destination"],
                cabin_class=j.get("cabin_class", "economy"),
                return_trip=j.get("return_trip", return_trip),
                nights_at_destination=j.get("nights", 0),
                tim_api_key=j.get("tim_api_key"),
                preferred_mode=j.get("preferred_mode"),
            )
            result["journey_id"] = i + 1
            result["attendee_label"] = j.get("label", f"Journey {i+1}")
            results.append(result)
            total_co2 += result["grand_total_co2_kg"]
        except Exception as e:
            errors.append({"journey": j, "error": str(e)})

    return {
        "journeys": results,
        "total_co2_kg": round(total_co2, 3),
        "num_journeys": len(results),
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# RESULTS TABLE
# ---------------------------------------------------------------------------

def results_to_dataframe(result: Dict):
    """Convert a single journey result to a pandas DataFrame."""
    import pandas as pd

    rows = []
    multiplier = result["transport_multiplier"]

    for leg in result["legs"]:
        rows.append({
            "Journey": f"{result['origin_resolved']} → {result['destination_resolved']}",
            "Leg": leg["label"],
            "Transport Mode": leg["mode"].replace("_", " ").title(),
            "Distance (km)": leg["distance_km"],
            "Emission Factor (kg CO2e/pkm)": leg["emission_factor"],
            "One-way CO2 (kg)": leg["co2_kg"],
            f"{'Return' if multiplier==2 else 'Total'} CO2 (kg)": round(leg["co2_kg"] * multiplier, 3),
            "Source": leg["source"],
            "Notes": leg.get("notes", ""),
        })

    # Hotel row
    if result["nights_at_destination"] > 0 and result["hotel_factor"]:
        hf = result["hotel_factor"]
        rows.append({
            "Journey": f"{result['origin_resolved']} → {result['destination_resolved']}",
            "Leg": f"Hotel stay – {result['nights_at_destination']} night(s)",
            "Transport Mode": "Hotel",
            "Distance (km)": "-",
            "Emission Factor (kg CO2e/pkm)": f"{hf['factor']} per room-night",
            "One-way CO2 (kg)": "-",
            f"{'Return' if multiplier==2 else 'Total'} CO2 (kg)": result["hotel_co2_kg"],
            "Source": hf["source"],
            "Notes": hf.get("notes", ""),
        })

    df = pd.DataFrame(rows)
    return df


def multi_results_to_dataframe(multi_result: Dict):
    """Convert multi-journey results to a summary DataFrame."""
    import pandas as pd

    rows = []
    for r in multi_result["journeys"]:
        rows.append({
            "Journey ID": r["journey_id"],
            "Label": r.get("attendee_label", ""),
            "Origin": r["origin_resolved"],
            "Destination": r["destination_resolved"],
            "Route": r["route_name"],
            "Distance (km)": r["total_distance_km"],
            "Cabin Class": r.get("cabin_class", "economy"),
            "Return Trip": r["return_trip"],
            "Transport CO2 (kg)": r["total_transport_co2_kg"],
            "Hotel Nights": r["nights_at_destination"],
            "Hotel CO2 (kg)": r["hotel_co2_kg"],
            "Total CO2 (kg CO2e)": r["grand_total_co2_kg"],
        })

    df = pd.DataFrame(rows)
    return df
