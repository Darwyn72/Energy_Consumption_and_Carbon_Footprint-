"""
route_planner.py
----------------
Handles:
  - Geocoding addresses / city names → (lat, lon) using Nominatim (free, OSM)
  - Great-circle distance calculation (haversine)
  - Airport IATA code lookup for flight legs
  - Route optimisation: selecting best transport mode combination
  - Google Travel Impact Model API calls for flight-specific emissions

No API keys required except:
  - Google TIM API key (optional – falls back to DEFRA factors if not provided)
  - Nominatim is free and requires only a valid User-Agent string
"""

import math
import time
import requests
from typing import Optional, Tuple, List, Dict

# ---------------------------------------------------------------------------
# MAJOR CITIES DATABASE  – (lat, lon, iata_airport, country_code)
# Used for dropdown selection
# ---------------------------------------------------------------------------
MAJOR_CITIES = {
    "London, UK":          {"lat": 51.5074,  "lon": -0.1278,  "iata": "LHR", "country": "GB"},
    "Paris, France":       {"lat": 48.8566,  "lon":  2.3522,  "iata": "CDG", "country": "FR"},
    "Berlin, Germany":     {"lat": 52.5200,  "lon": 13.4050,  "iata": "BER", "country": "DE"},
    "Madrid, Spain":       {"lat": 40.4168,  "lon": -3.7038,  "iata": "MAD", "country": "ES"},
    "Rome, Italy":         {"lat": 41.9028,  "lon": 12.4964,  "iata": "FCO", "country": "IT"},
    "Amsterdam, Netherlands": {"lat": 52.3676, "lon": 4.9041, "iata": "AMS", "country": "NL"},
    "Brussels, Belgium":   {"lat": 50.8503,  "lon":  4.3517,  "iata": "BRU", "country": "BE"},
    "Vienna, Austria":     {"lat": 48.2082,  "lon": 16.3738,  "iata": "VIE", "country": "AT"},
    "Zurich, Switzerland": {"lat": 47.3769,  "lon":  8.5417,  "iata": "ZRH", "country": "CH"},
    "Stockholm, Sweden":   {"lat": 59.3293,  "lon": 18.0686,  "iata": "ARN", "country": "SE"},
    "Oslo, Norway":        {"lat": 59.9139,  "lon": 10.7522,  "iata": "OSL", "country": "NO"},
    "Copenhagen, Denmark": {"lat": 55.6761,  "lon": 12.5683,  "iata": "CPH", "country": "DK"},
    "Helsinki, Finland":   {"lat": 60.1699,  "lon": 24.9384,  "iata": "HEL", "country": "FI"},
    "Warsaw, Poland":      {"lat": 52.2297,  "lon": 21.0122,  "iata": "WAW", "country": "PL"},
    "Prague, Czechia":     {"lat": 50.0755,  "lon": 14.4378,  "iata": "PRG", "country": "CZ"},
    "Budapest, Hungary":   {"lat": 47.4979,  "lon": 19.0402,  "iata": "BUD", "country": "HU"},
    "Lisbon, Portugal":    {"lat": 38.7223,  "lon": -9.1393,  "iata": "LIS", "country": "PT"},
    "Athens, Greece":      {"lat": 37.9838,  "lon": 23.7275,  "iata": "ATH", "country": "GR"},
    "Dublin, Ireland":     {"lat": 53.3498,  "lon": -6.2603,  "iata": "DUB", "country": "IE"},
    "Edinburgh, UK":       {"lat": 55.9533,  "lon": -3.1883,  "iata": "EDI", "country": "GB"},
    "Manchester, UK":      {"lat": 53.4808,  "lon": -2.2426,  "iata": "MAN", "country": "GB"},
    "New York, USA":       {"lat": 40.7128,  "lon": -74.0060, "iata": "JFK", "country": "US"},
    "Los Angeles, USA":    {"lat": 34.0522,  "lon": -118.2437,"iata": "LAX", "country": "US"},
    "Chicago, USA":        {"lat": 41.8781,  "lon": -87.6298, "iata": "ORD", "country": "US"},
    "Washington DC, USA":  {"lat": 38.9072,  "lon": -77.0369, "iata": "IAD", "country": "US"},
    "San Francisco, USA":  {"lat": 37.7749,  "lon": -122.4194,"iata": "SFO", "country": "US"},
    "Boston, USA":         {"lat": 42.3601,  "lon": -71.0589, "iata": "BOS", "country": "US"},
    "Toronto, Canada":     {"lat": 43.6532,  "lon": -79.3832, "iata": "YYZ", "country": "CA"},
    "Vancouver, Canada":   {"lat": 49.2827,  "lon": -123.1207,"iata": "YVR", "country": "CA"},
    "Montreal, Canada":    {"lat": 45.5017,  "lon": -73.5673, "iata": "YUL", "country": "CA"},
    "Mexico City, Mexico": {"lat": 19.4326,  "lon": -99.1332, "iata": "MEX", "country": "MX"},
    "São Paulo, Brazil":   {"lat": -23.5505, "lon": -46.6333, "iata": "GRU", "country": "BR"},
    "Buenos Aires, Argentina": {"lat": -34.6037, "lon": -58.3816, "iata": "EZE", "country": "AR"},
    "Bogotá, Colombia":    {"lat": 4.7110,   "lon": -74.0721, "iata": "BOG", "country": "CO"},
    "Santiago, Chile":     {"lat": -33.4489, "lon": -70.6693, "iata": "SCL", "country": "CL"},
    "Tokyo, Japan":        {"lat": 35.6762,  "lon": 139.6503, "iata": "NRT", "country": "JP"},
    "Beijing, China":      {"lat": 39.9042,  "lon": 116.4074, "iata": "PEK", "country": "CN"},
    "Shanghai, China":     {"lat": 31.2304,  "lon": 121.4737, "iata": "PVG", "country": "CN"},
    "Hong Kong":           {"lat": 22.3193,  "lon": 114.1694, "iata": "HKG", "country": "HK"},
    "Singapore":           {"lat": 1.3521,   "lon": 103.8198, "iata": "SIN", "country": "SG"},
    "Seoul, South Korea":  {"lat": 37.5665,  "lon": 126.9780, "iata": "ICN", "country": "KR"},
    "Mumbai, India":       {"lat": 19.0760,  "lon": 72.8777,  "iata": "BOM", "country": "IN"},
    "Delhi, India":        {"lat": 28.6139,  "lon": 77.2090,  "iata": "DEL", "country": "IN"},
    "Bangalore, India":    {"lat": 12.9716,  "lon": 77.5946,  "iata": "BLR", "country": "IN"},
    "Bangkok, Thailand":   {"lat": 13.7563,  "lon": 100.5018, "iata": "BKK", "country": "TH"},
    "Sydney, Australia":   {"lat": -33.8688, "lon": 151.2093, "iata": "SYD", "country": "AU"},
    "Melbourne, Australia":{"lat": -37.8136, "lon": 144.9631, "iata": "MEL", "country": "AU"},
    "Auckland, New Zealand":{"lat": -36.8485,"lon": 174.7633, "iata": "AKL", "country": "NZ"},
    "Johannesburg, S. Africa": {"lat": -26.2041,"lon": 28.0473,"iata": "JNB", "country": "ZA"},
    "Cape Town, S. Africa":{"lat": -33.9249, "lon": 18.4241,  "iata": "CPT", "country": "ZA"},
    "Nairobi, Kenya":      {"lat": -1.2921,  "lon": 36.8219,  "iata": "NBO", "country": "KE"},
    "Lagos, Nigeria":      {"lat": 6.5244,   "lon": 3.3792,   "iata": "LOS", "country": "NG"},
    "Cairo, Egypt":        {"lat": 30.0444,  "lon": 31.2357,  "iata": "CAI", "country": "EG"},
    "Dubai, UAE":          {"lat": 25.2048,  "lon": 55.2708,  "iata": "DXB", "country": "AE"},
    "Abu Dhabi, UAE":      {"lat": 24.4539,  "lon": 54.3773,  "iata": "AUH", "country": "AE"},
    "Riyadh, Saudi Arabia":{"lat": 24.6877,  "lon": 46.7219,  "iata": "RUH", "country": "SA"},
    "Doha, Qatar":         {"lat": 25.2854,  "lon": 51.5310,  "iata": "DOH", "country": "QA"},
    "Istanbul, Turkey":    {"lat": 41.0082,  "lon": 28.9784,  "iata": "IST", "country": "TR"},
    "Moscow, Russia":      {"lat": 55.7558,  "lon": 37.6173,  "iata": "SVO", "country": "RU"},
    "Kyiv, Ukraine":       {"lat": 50.4501,  "lon": 30.5234,  "iata": "KBP", "country": "UA"},
    "Casablanca, Morocco": {"lat": 33.5731,  "lon": -7.5898,  "iata": "CMN", "country": "MA"},
    "Kuala Lumpur, Malaysia": {"lat": 3.1390, "lon": 101.6869,"iata": "KUL", "country": "MY"},
    "Jakarta, Indonesia":  {"lat": -6.2088,  "lon": 106.8456, "iata": "CGK", "country": "ID"},
    "Manila, Philippines": {"lat": 14.5995,  "lon": 120.9842, "iata": "MNL", "country": "PH"},
}


# ---------------------------------------------------------------------------
# HAVERSINE DISTANCE
# ---------------------------------------------------------------------------

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance in km between two (lat, lon) pairs."""
    R = 6371.0  # Earth radius km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ---------------------------------------------------------------------------
# GEOCODING  (Nominatim – free, no API key required)
# ---------------------------------------------------------------------------

def geocode_address(address: str, user_agent: str = "CarbonFootprintTool/1.0") -> Optional[Dict]:
    """
    Geocode an address string using Nominatim (OpenStreetMap).
    Returns dict with lat, lon, display_name, country_code.
    Returns None if not found.
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json",
        "limit": 1,
        "addressdetails": 1
    }
    headers = {"User-Agent": user_agent}
    try:
        time.sleep(1.1)  # Nominatim rate limit: 1 req/sec
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        results = response.json()
        if results:
            r = results[0]
            country_code = r.get("address", {}).get("country_code", "").upper()
            return {
                "lat": float(r["lat"]),
                "lon": float(r["lon"]),
                "display_name": r.get("display_name", address),
                "country_code": country_code,
                "iata": None  # Will be populated separately if needed
            }
    except Exception as e:
        print(f"Geocoding error for '{address}': {e}")
    return None


def resolve_location(location_str: str, use_dropdown: bool = True) -> Optional[Dict]:
    """
    Resolve a location string to coordinates.
    Checks MAJOR_CITIES dict first (exact match or partial), then geocodes.
    Returns dict: {lat, lon, display_name, country_code, iata}
    """
    # Exact match in city database
    if location_str in MAJOR_CITIES:
        city = MAJOR_CITIES[location_str].copy()
        city["display_name"] = location_str
        return city

    # Partial match (case-insensitive)
    location_lower = location_str.lower()
    for city_name, city_data in MAJOR_CITIES.items():
        if location_lower in city_name.lower() or city_name.lower().split(",")[0] in location_lower:
            result = city_data.copy()
            result["display_name"] = city_name
            return result

    # Fall back to geocoding
    print(f"'{location_str}' not in city database – geocoding via Nominatim...")
    geocoded = geocode_address(location_str)
    if geocoded:
        # Try to find nearest city IATA code
        geocoded["iata"] = _find_nearest_iata(geocoded["lat"], geocoded["lon"])
    return geocoded


def _find_nearest_iata(lat: float, lon: float) -> Optional[str]:
    """Find IATA code of nearest major city airport."""
    min_dist = float("inf")
    nearest_iata = None
    for city_data in MAJOR_CITIES.values():
        d = haversine_km(lat, lon, city_data["lat"], city_data["lon"])
        if d < min_dist:
            min_dist = d
            nearest_iata = city_data["iata"]
    return nearest_iata


# ---------------------------------------------------------------------------
# ROUTE OPTIMISATION
# ---------------------------------------------------------------------------

# Distance thresholds (km) for mode selection heuristics
THRESHOLDS = {
    "metro_max":  30,     # Taxi/metro for very short legs
    "bus_max":   150,     # Bus/coach viable
    "train_max": 800,     # Train preferred over short-haul flight
    "short_haul_max": 3700,  # Short-haul flight threshold (DEFRA/ICAO)
}

# Mode display names for readable output
MODE_LABELS = {
    "metro_global_average": "Metro/Underground",
    "bus_local_average": "Local Bus",
    "coach_long_distance": "Long-distance Coach",
    "train_uk_average": "Train (UK)",
    "train_europe_average": "Train (Europe)",
    "train_global_average": "Train (Global avg.)",
    "high_speed_rail": "High-speed Rail",
    "taxi_regular": "Taxi",
    "taxi_electric": "Taxi (Electric)",
    "flight_economy_short_haul": "Flight – Economy Short-haul",
    "flight_economy_long_haul": "Flight – Economy Long-haul",
    "flight_business_short_haul": "Flight – Business Short-haul",
    "flight_business_long_haul": "Flight – Business Long-haul",
}


def select_flight_mode(distance_km: float, cabin: str = "economy") -> str:
    """Return appropriate flight emission factor key."""
    cabin = cabin.lower()
    if distance_km <= THRESHOLDS["short_haul_max"]:
        return f"flight_{cabin}_short_haul" if cabin != "first" else "flight_business_short_haul"
    else:
        return f"flight_{cabin}_long_haul"


def optimise_route(
    origin: Dict,
    destination: Dict,
    prefer_low_carbon: bool = True,
    cabin_class: str = "economy",
    include_flight: bool = True,
    include_rail: bool = True,
    include_coach: bool = True,
) -> List[Dict]:
    """
    Generate a list of route options between two locations.
    Each option is a list of legs: {mode, distance_km, label}.

    Returns a list of route alternatives sorted by total kg CO2e (ascending).
    """
    from modules.emission_factors import TRANSPORT_FACTORS

    origin_lat, origin_lon = origin["lat"], origin["lon"]
    dest_lat, dest_lon = destination["lat"], destination["lon"]
    total_dist = haversine_km(origin_lat, origin_lon, dest_lat, dest_lon)

    options = []

    # --- FLIGHT option ---------------------------------------------------
    if include_flight and total_dist > 100:
        flight_mode = select_flight_mode(total_dist, cabin_class)
        # Add taxi legs to/from airports (~30 km each end as representative)
        taxi_dist = 35.0
        legs = [
            {"mode": "taxi_regular", "distance_km": taxi_dist,
             "label": f"Taxi to departure airport (~{taxi_dist:.0f} km)"},
            {"mode": flight_mode, "distance_km": total_dist,
             "label": f"Flight {origin.get('iata','?')} → {destination.get('iata','?')} ({total_dist:.0f} km)"},
            {"mode": "taxi_regular", "distance_km": taxi_dist,
             "label": f"Taxi from arrival airport (~{taxi_dist:.0f} km)"},
        ]
        options.append({"name": f"✈  Flight ({cabin_class.title()} class)", "legs": legs})

    # --- RAIL option  (if distance allows) --------------------------------
    if include_rail and total_dist <= THRESHOLDS["train_max"]:
        # Determine best rail type by region
        origin_country = origin.get("country", "")
        dest_country = destination.get("country", "")
        same_country = origin_country and origin_country == dest_country

        if total_dist <= 600 and origin_country in ("FR", "DE", "ES", "IT", "BE", "NL", "CH"):
            rail_mode = "high_speed_rail"
            rail_label = "High-speed Rail"
        elif origin_country == "GB" and dest_country == "GB":
            rail_mode = "train_uk_average"
            rail_label = "UK National Rail"
        elif origin_country in ("GB",) and dest_country in ("FR", "BE", "NL"):
            rail_mode = "train_eurostar"
            rail_label = "Eurostar"
        elif origin_country in ("FR","DE","ES","IT","BE","NL","CH","AT","SE","NO","DK","FI","PL","CZ","HU"):
            rail_mode = "train_europe_average"
            rail_label = "European Intercity Rail"
        else:
            rail_mode = "train_global_average"
            rail_label = "Rail (Global avg.)"

        taxi_dist = 5.0
        legs = [
            {"mode": "taxi_regular", "distance_km": taxi_dist,
             "label": f"Taxi to station (~{taxi_dist:.0f} km)"},
            {"mode": rail_mode, "distance_km": total_dist,
             "label": f"{rail_label} ({total_dist:.0f} km)"},
            {"mode": "taxi_regular", "distance_km": taxi_dist,
             "label": f"Taxi from station (~{taxi_dist:.0f} km)"},
        ]
        options.append({"name": f"🚆  {rail_label}", "legs": legs})

    # --- COACH option (medium distances) ----------------------------------
    if include_coach and 50 <= total_dist <= THRESHOLDS["bus_max"]:
        legs = [
            {"mode": "coach_long_distance", "distance_km": total_dist,
             "label": f"Long-distance Coach ({total_dist:.0f} km)"},
        ]
        options.append({"name": "🚌  Long-distance Coach", "legs": legs})

    # --- LOCAL TRANSPORT ONLY (very short distances) ----------------------
    if total_dist <= THRESHOLDS["metro_max"]:
        legs = [
            {"mode": "metro_global_average", "distance_km": total_dist,
             "label": f"Metro/Underground ({total_dist:.0f} km)"},
        ]
        options.append({"name": "🚇  Metro/Underground", "legs": legs})

        legs_taxi = [
            {"mode": "taxi_regular", "distance_km": total_dist,
             "label": f"Taxi ({total_dist:.0f} km)"},
        ]
        options.append({"name": "🚕  Taxi", "legs": legs_taxi})

    # --- Score options by CO2 ---
    from modules.emission_factors import TRANSPORT_FACTORS as TF
    for opt in options:
        opt["total_km"] = sum(leg["distance_km"] for leg in opt["legs"])
        opt["total_co2_kg"] = sum(
            TF[leg["mode"]]["factor"] * leg["distance_km"]
            for leg in opt["legs"]
        )

    # Sort by CO2 ascending (lowest first = recommended)
    options.sort(key=lambda x: x["total_co2_kg"])

    # Tag the lowest-CO2 option
    if options:
        options[0]["recommended"] = True

    return options


# ---------------------------------------------------------------------------
# GOOGLE TRAVEL IMPACT MODEL (TIM) API  – flight-specific emissions
# ---------------------------------------------------------------------------

def query_tim_api(
    origin_iata: str,
    destination_iata: str,
    api_key: str,
    carrier_code: str = None,
    flight_number: int = None,
    departure_date: dict = None,
) -> Optional[Dict]:
    """
    Query the Google Travel Impact Model API for flight emissions.
    Falls back gracefully if no API key or flight details provided.

    Returns dict with economy/business emissions in grams per pax, or None.
    """
    if not api_key:
        return None

    # Use typical flight emissions if no specific flight provided
    url = "https://travelimpactmodel.googleapis.com/v1/flights:computeTypicalFlightEmissions"
    payload = {
        "markets": [
            {"origin": origin_iata, "destination": destination_iata}
        ]
    }
    try:
        response = requests.post(
            url,
            params={"key": api_key},
            json=payload,
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
        emissions = data.get("typicalFlightEmissions", [{}])[0]
        gpax = emissions.get("emissionsGramsPerPax", {})
        return {
            "economy_g_per_pax": gpax.get("economy"),
            "business_g_per_pax": gpax.get("business"),
            "first_g_per_pax": gpax.get("first"),
            "source": "Google TIM API (typical flight emissions)",
            "origin": origin_iata,
            "destination": destination_iata
        }
    except Exception as e:
        print(f"TIM API error: {e}")
        return None
