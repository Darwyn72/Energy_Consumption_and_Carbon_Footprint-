"""
emission_factors.py
-------------------
Curated emission factors for transport and accommodation.

Sources:
  - DEFRA/DESNZ UK GHG Conversion Factors 2025
    https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2025
  - IPCC AR6 (2021) – aviation radiative forcing multiplier
  - EPA (US) Emission Factors for Greenhouse Gas Inventories (2024)
  - IEA (2023) – rail and electricity grid averages
  - EEA (2023) – European transport emission averages

All values are kg CO2e per passenger-kilometre (pkm) unless noted.
Hotel values are kg CO2e per room-night.
"""

# ---------------------------------------------------------------------------
# TRANSPORT EMISSION FACTORS  (kg CO2e / passenger-km)
# ---------------------------------------------------------------------------

TRANSPORT_FACTORS = {
    # ---- AVIATION (DEFRA 2025, economy class, with uplift / RFI) ----------
    # DEFRA applies a Radiative Forcing Index (RFI) uplift of ~2x for non-CO2
    # effects (contrails, NOx, etc.) on long-haul.
    "flight_economy_short_haul": {
        "factor": 0.2552,   # <3700 km, with RFI  (DEFRA 2025)
        "unit": "kg CO2e/pkm",
        "source": "DEFRA 2025",
        "notes": "Short-haul economy (<3700 km), includes RFI multiplier"
    },
    "flight_economy_long_haul": {
        "factor": 0.1956,   # ≥3700 km, with RFI  (DEFRA 2025)
        "unit": "kg CO2e/pkm",
        "source": "DEFRA 2025",
        "notes": "Long-haul economy (≥3700 km), includes RFI multiplier"
    },
    "flight_business_short_haul": {
        "factor": 0.3828,
        "unit": "kg CO2e/pkm",
        "source": "DEFRA 2025",
        "notes": "Short-haul business class, includes RFI multiplier"
    },
    "flight_business_long_haul": {
        "factor": 0.5847,
        "unit": "kg CO2e/pkm",
        "source": "DEFRA 2025",
        "notes": "Long-haul business class, includes RFI multiplier"
    },
    "flight_first_long_haul": {
        "factor": 0.7822,
        "unit": "kg CO2e/pkm",
        "source": "DEFRA 2025",
        "notes": "Long-haul first class, includes RFI multiplier"
    },

    # ---- RAIL (DEFRA 2025 / IEA 2023) ------------------------------------
    "train_uk_average": {
        "factor": 0.0376,   # UK national rail average (DEFRA 2025)
        "unit": "kg CO2e/pkm",
        "source": "DEFRA 2025"
    },
    "train_eurostar": {
        "factor": 0.0041,   # Eurostar (DEFRA 2025)
        "unit": "kg CO2e/pkm",
        "source": "DEFRA 2025",
        "notes": "High-speed rail on mostly renewable electricity"
    },
    "train_europe_average": {
        "factor": 0.0145,   # EEA 2023 EU average intercity rail
        "unit": "kg CO2e/pkm",
        "source": "EEA 2023"
    },
    "train_global_average": {
        "factor": 0.0410,   # IEA 2023 global average
        "unit": "kg CO2e/pkm",
        "source": "IEA 2023"
    },
    "high_speed_rail": {
        "factor": 0.0060,   # Typical HSR (TGV, Shinkansen style)
        "unit": "kg CO2e/pkm",
        "source": "IEA 2023 / EEA 2023",
        "notes": "High-speed rail using primarily low-carbon electricity"
    },

    # ---- BUS / COACH (DEFRA 2025 / EPA 2024) -----------------------------
    "bus_local_average": {
        "factor": 0.1025,   # UK local service bus (DEFRA 2025)
        "unit": "kg CO2e/pkm",
        "source": "DEFRA 2025"
    },
    "coach_long_distance": {
        "factor": 0.0274,   # UK long-distance coach (DEFRA 2025)
        "unit": "kg CO2e/pkm",
        "source": "DEFRA 2025",
        "notes": "National Express / long-distance intercity coach"
    },
    "bus_europe_average": {
        "factor": 0.0720,   # EEA EU average local bus
        "unit": "kg CO2e/pkm",
        "source": "EEA 2023"
    },
    "bus_global_average": {
        "factor": 0.0890,
        "unit": "kg CO2e/pkm",
        "source": "IEA 2023"
    },

    # ---- METRO / UNDERGROUND (DEFRA 2025 / IEA 2023) ---------------------
    "metro_london": {
        "factor": 0.0280,   # London Underground (DEFRA 2025)
        "unit": "kg CO2e/pkm",
        "source": "DEFRA 2025"
    },
    "metro_europe_average": {
        "factor": 0.0320,   # EEA 2023 European metro average
        "unit": "kg CO2e/pkm",
        "source": "EEA 2023"
    },
    "metro_global_average": {
        "factor": 0.0410,
        "unit": "kg CO2e/pkm",
        "source": "IEA 2023"
    },

    # ---- TAXI / RIDESHARE (DEFRA 2025) -----------------------------------
    "taxi_regular": {
        "factor": 0.1534,   # Petrol/diesel taxi (DEFRA 2025)
        "unit": "kg CO2e/pkm",
        "source": "DEFRA 2025",
        "notes": "Per passenger-km (assumes 1.5 average occupancy)"
    },
    "taxi_electric": {
        "factor": 0.0531,   # Electric taxi, UK grid (DEFRA 2025)
        "unit": "kg CO2e/pkm",
        "source": "DEFRA 2025"
    },
    "rideshare_pooled": {
        "factor": 0.0788,   # Shared rideshare (EPA 2024 / DEFRA)
        "unit": "kg CO2e/pkm",
        "source": "DEFRA 2025 / EPA 2024"
    },

    # ---- CAR (DEFRA 2025) ------------------------------------------------
    "car_petrol_average": {
        "factor": 0.1703,   # Average UK petrol car (DEFRA 2025)
        "unit": "kg CO2e/pkm",
        "source": "DEFRA 2025"
    },
    "car_diesel_average": {
        "factor": 0.1608,
        "unit": "kg CO2e/pkm",
        "source": "DEFRA 2025"
    },
    "car_electric_uk": {
        "factor": 0.0530,
        "unit": "kg CO2e/pkm",
        "source": "DEFRA 2025"
    },
    "car_rental_average": {
        "factor": 0.1730,
        "unit": "kg CO2e/pkm",
        "source": "DEFRA 2025"
    },

    # ---- FERRY (DEFRA 2025) -----------------------------------------------
    "ferry_foot_passenger": {
        "factor": 0.1872,
        "unit": "kg CO2e/pkm",
        "source": "DEFRA 2025"
    },
    "ferry_car_passenger": {
        "factor": 0.1295,
        "unit": "kg CO2e/pkm",
        "source": "DEFRA 2025"
    },
}

# ---------------------------------------------------------------------------
# HOTEL / ACCOMMODATION FACTORS  (kg CO2e per room-night)
# ---------------------------------------------------------------------------
# Source: DEFRA 2025 Conversion Factors – 'Hotel stays' category
# Values reflect full scope 1+2+3 emissions per room-night.

HOTEL_FACTORS = {
    "uk": {
        "factor": 20.8,    # UK average hotel (DEFRA 2025)
        "unit": "kg CO2e/room-night",
        "source": "DEFRA 2025"
    },
    "europe_average": {
        "factor": 22.0,
        "unit": "kg CO2e/room-night",
        "source": "DEFRA 2025 / Cornell Hotel Sustainability Benchmarking 2023",
        "notes": "Western European average"
    },
    "north_america": {
        "factor": 31.0,
        "unit": "kg CO2e/room-night",
        "source": "Cornell CHSB 2023",
        "notes": "US/Canada average"
    },
    "asia_pacific": {
        "factor": 28.5,
        "unit": "kg CO2e/room-night",
        "source": "Cornell CHSB 2023"
    },
    "latin_america": {
        "factor": 19.5,
        "unit": "kg CO2e/room-night",
        "source": "Cornell CHSB 2023"
    },
    "middle_east_africa": {
        "factor": 25.0,
        "unit": "kg CO2e/room-night",
        "source": "Cornell CHSB 2023"
    },
    "global_average": {
        "factor": 26.4,
        "unit": "kg CO2e/room-night",
        "source": "DEFRA 2025 / Cornell CHSB 2023",
        "notes": "Global average across all hotel categories"
    },
}

# ---------------------------------------------------------------------------
# REGION MAPPING  – maps country/region codes to hotel factors
# ---------------------------------------------------------------------------
COUNTRY_TO_HOTEL_REGION = {
    # UK & Ireland
    "GB": "uk", "IE": "europe_average",
    # Western Europe
    "FR": "europe_average", "DE": "europe_average", "ES": "europe_average",
    "IT": "europe_average", "NL": "europe_average", "BE": "europe_average",
    "AT": "europe_average", "CH": "europe_average", "SE": "europe_average",
    "NO": "europe_average", "DK": "europe_average", "FI": "europe_average",
    "PT": "europe_average", "GR": "europe_average", "PL": "europe_average",
    "CZ": "europe_average", "HU": "europe_average", "RO": "europe_average",
    # North America
    "US": "north_america", "CA": "north_america", "MX": "latin_america",
    # Latin America
    "BR": "latin_america", "AR": "latin_america", "CL": "latin_america",
    "CO": "latin_america", "PE": "latin_america",
    # Asia-Pacific
    "CN": "asia_pacific", "JP": "asia_pacific", "IN": "asia_pacific",
    "AU": "asia_pacific", "NZ": "asia_pacific", "SG": "asia_pacific",
    "KR": "asia_pacific", "TH": "asia_pacific", "VN": "asia_pacific",
    "ID": "asia_pacific", "MY": "asia_pacific", "PH": "asia_pacific",
    # Middle East & Africa
    "AE": "middle_east_africa", "SA": "middle_east_africa",
    "QA": "middle_east_africa", "ZA": "middle_east_africa",
    "KE": "middle_east_africa", "NG": "middle_east_africa",
    "EG": "middle_east_africa", "MA": "middle_east_africa",
}


def get_transport_factor(mode: str) -> dict:
    """Return the emission factor dict for a given transport mode key."""
    if mode not in TRANSPORT_FACTORS:
        raise KeyError(f"Transport mode '{mode}' not found. "
                       f"Available: {list(TRANSPORT_FACTORS.keys())}")
    return TRANSPORT_FACTORS[mode]


def get_hotel_factor(country_code: str = None, region: str = None) -> dict:
    """
    Return hotel emission factor.
    Priority: country_code lookup → region → global_average fallback.
    """
    if country_code:
        region_key = COUNTRY_TO_HOTEL_REGION.get(country_code.upper(), "global_average")
        return HOTEL_FACTORS[region_key]
    if region and region in HOTEL_FACTORS:
        return HOTEL_FACTORS[region]
    return HOTEL_FACTORS["global_average"]


def list_transport_modes() -> list:
    """Return list of all available transport mode keys."""
    return list(TRANSPORT_FACTORS.keys())


def get_all_factors_df():
    """Return all transport factors as a pandas DataFrame."""
    import pandas as pd
    rows = []
    for mode, info in TRANSPORT_FACTORS.items():
        rows.append({
            "mode": mode,
            "factor_kg_co2e_per_pkm": info["factor"],
            "unit": info["unit"],
            "source": info["source"],
            "notes": info.get("notes", "")
        })
    return pd.DataFrame(rows)
