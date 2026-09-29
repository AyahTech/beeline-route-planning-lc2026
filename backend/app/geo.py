"""Distance & travel-time model.

Assumption (documented in README): coordinates come from the cached geocoding
pipeline (scripts/build_data.py). Distances are haversine x ROAD_FACTOR (1.35),
travel time = distance / vehicle speed. This simplified model is explicitly
allowed by the case spec.
"""
import math

ROAD_FACTOR = 1.35
SPEEDS_KMH = {
    'car': 30.0,
    'bicycle': 15.0,
    'public transport': 25.0,
    'pedestrian': 5.0,
}
DEFAULT_SPEED_KMH = 30.0


def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def travel_m(lat1, lon1, lat2, lon2):
    """Road-adjusted distance in metres."""
    return haversine_m(lat1, lon1, lat2, lon2) * ROAD_FACTOR


def travel_min(lat1, lon1, lat2, lon2, vehicle='car'):
    """Travel time in minutes for a given vehicle type."""
    km = travel_m(lat1, lon1, lat2, lon2) / 1000.0
    return km / SPEEDS_KMH.get(vehicle, DEFAULT_SPEED_KMH) * 60.0
