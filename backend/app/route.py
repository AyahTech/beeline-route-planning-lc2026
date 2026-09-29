"""Route timeline simulation: the core time-feasibility check.

A route starts at the engineer's start point at shift start (no return leg,
per the spec). For each stop: travel, then wait until the ticket window opens.
The visit must START inside the ticket window; the work must END inside the
engineer's shift.
"""
from .geo import travel_min


def simulate(engineer, stop_ids, tickets_by_id):
    """Return list of per-stop dicts, or None if the route is infeasible."""
    now = engineer.shift_start
    lat, lon = engineer.start_lat, engineer.start_lon
    out = []
    for seq, tid in enumerate(stop_ids, start=1):
        tk = tickets_by_id[tid]
        arr = now + travel_min(lat, lon, tk.lat, tk.lon, engineer.vehicle_type)
        start = max(arr, tk.window_start)
        if start > tk.window_end:
            return None
        end = start + tk.duration_min
        if end > engineer.shift_end:
            return None
        out.append({
            'ticket_id': tid, 'seq': seq,
            'travel_min': round(arr - now, 1),
            'arrival_min': round(arr, 1),
            'start_min': round(start, 1),
            'end_min': round(end, 1),
        })
        now, lat, lon = end, tk.lat, tk.lon
    return out


def route_distance_m(engineer, stop_ids, tickets_by_id):
    """Depot -> stops -> (no return leg), in metres."""
    lat, lon = engineer.start_lat, engineer.start_lon
    total = 0.0
    from .geo import travel_m
    for tid in stop_ids:
        tk = tickets_by_id[tid]
        total += travel_m(lat, lon, tk.lat, tk.lon)
        lat, lon = tk.lat, tk.lon
    return total
