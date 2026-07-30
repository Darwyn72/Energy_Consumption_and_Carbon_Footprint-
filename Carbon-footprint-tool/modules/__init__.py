# Carbon Footprint Tool – modules package
from modules.emission_factors import TRANSPORT_FACTORS, HOTEL_FACTORS, get_transport_factor, get_hotel_factor
from modules.route_planner import MAJOR_CITIES, haversine_km, resolve_location, optimise_route
from modules.carbon_calculator import calculate_journey, calculate_multi_journey, results_to_dataframe, multi_results_to_dataframe
from modules.map_visualiser import create_map, plot_route_comparison
from modules.data_exporter import export_journey_csv, export_journey_xlsx, export_multi_journey_csv, export_multi_journey_xlsx, create_download_link

__all__ = [
    "TRANSPORT_FACTORS", "HOTEL_FACTORS", "MAJOR_CITIES",
    "get_transport_factor", "get_hotel_factor",
    "haversine_km", "resolve_location", "optimise_route",
    "calculate_journey", "calculate_multi_journey",
    "results_to_dataframe", "multi_results_to_dataframe",
    "create_map", "plot_route_comparison",
    "export_journey_csv", "export_journey_xlsx",
    "export_multi_journey_csv", "export_multi_journey_xlsx",
    "create_download_link",
]
