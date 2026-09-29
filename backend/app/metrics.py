"""The two mandatory metrics (+ supporting counts), computed identically
for the baseline and the solver:
  (a) fewest unique engineers used
  (b) mileage per engineer + total
"""
from collections import Counter


def compute_metrics(route_objs, unassigned):
    per_engineer = [
        {'engineer_id': r['engineer_id'], 'engineer_name': r['engineer_name'],
         'stops': len(r['stops']), 'distance_m': r['distance_m'],
         'distance_km': round(r['distance_m'] / 1000.0, 1)}
        for r in sorted(route_objs, key=lambda r: r['engineer_id'])
    ]
    return {
        'engineers_used': len(route_objs),
        'tickets_assigned': sum(len(r['stops']) for r in route_objs),
        'tickets_unassigned': len(unassigned),
        'total_distance_m': sum(r['distance_m'] for r in route_objs),
        'total_distance_km': round(sum(r['distance_m'] for r in route_objs) / 1000.0, 1),
        'per_engineer': per_engineer,
    }


def compare(solver_metrics, baseline_metrics):
    """Side-by-side of the two mandatory metrics, solver vs baseline."""
    return {
        'engineers_used': {
            'solver': solver_metrics['engineers_used'],
            'baseline': baseline_metrics['engineers_used'],
            'delta': solver_metrics['engineers_used'] - baseline_metrics['engineers_used'],
        },
        'total_distance_km': {
            'solver': solver_metrics['total_distance_km'],
            'baseline': baseline_metrics['total_distance_km'],
            'delta': round(solver_metrics['total_distance_km']
                           - baseline_metrics['total_distance_km'], 1),
        },
        'assigned': {
            'solver': solver_metrics['tickets_assigned'],
            'baseline': baseline_metrics['tickets_assigned'],
        },
        'unassigned': {
            'solver': solver_metrics['tickets_unassigned'],
            'baseline': baseline_metrics['tickets_unassigned'],
        },
        'per_engineer': {
            'solver': solver_metrics['per_engineer'],
            'baseline': baseline_metrics['per_engineer'],
        },
    }
