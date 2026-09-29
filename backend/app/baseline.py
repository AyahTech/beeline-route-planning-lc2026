"""The spec-defined baseline (this is what our metrics are scored against):

  * tickets processed in arrival order
  * assigned to the FIRST engineer in input order who satisfies the constraints
  * visit order = assignment order
  * no global optimisation
"""
from .constraints import engineer_can_take
from .route import simulate, route_distance_m


def run_baseline(tickets, engineers):
    tickets_by_id = {t.id: t for t in tickets}
    routes = {e.id: [] for e in engineers}
    attempts = {}   # ticket_id -> {engineer_name: reason}
    unassigned = []

    for tk in sorted(tickets, key=lambda t: t.arrival_order):
        placed = False
        attempts[tk.id] = {}
        for e in engineers:
            ok, failed, reason = engineer_can_take(e, tk)
            if not ok:
                attempts[tk.id][e.name] = reason
                continue
            cand = routes[e.id] + [tk.id]
            if simulate(e, cand, tickets_by_id) is None:
                attempts[tk.id][e.name] = (
                    'не успевает: не хватает времени на дорогу/работу в рамках окна и смены')
                continue
            routes[e.id] = cand
            placed = True
            break
        if not placed:
            unassigned.append(tk)

    return build_plan('baseline', tickets, engineers, routes, unassigned, attempts)


def build_plan(algorithm, tickets, engineers, routes, unassigned, attempts):
    from .metrics import compute_metrics
    from .explain import explain_assignment, explain_unassigned
    tickets_by_id = {t.id: t for t in tickets}

    # safety net: any route that fails strict simulation has its last
    # infeasible stop dropped to unassigned (explicitly reported)
    extra_unassigned = []
    for e in engineers:
        while routes[e.id] and simulate(e, routes[e.id], tickets_by_id) is None:
            bad = routes[e.id].pop()
            extra_unassigned.append(tickets_by_id[bad])

    route_objs = []
    for e in engineers:
        stops = routes[e.id]
        if not stops:
            continue
        sim = simulate(e, stops, tickets_by_id)
        route_objs.append({
            'engineer_id': e.id,
            'engineer_name': e.name,
            'vehicle_type': e.vehicle_type,
            'skills': e.skills,
            'stops': sim,
            'distance_m': round(route_distance_m(e, stops, tickets_by_id)),
            'path': [{'lat': e.start_lat, 'lon': e.start_lon, 'kind': 'start'}] +
                    [{'lat': tickets_by_id[tid].lat, 'lon': tickets_by_id[tid].lon,
                      'kind': 'ticket', 'ticket_id': tid, 'seq': s['seq']}
                     for tid, s in zip(stops, sim)],
        })
    all_unassigned = list(unassigned) + extra_unassigned
    plan = {
        'algorithm': algorithm,
        'routes': route_objs,
        'unassigned': [
            {'ticket': tickets_by_id[t.id].__dict__.copy(),
             'reason': explain_unassigned(tickets_by_id[t.id],
                                          attempts.get(t.id, {}))}
            for t in all_unassigned
        ],
        'assignments': {
            tid: {'engineer_id': e.id, 'engineer_name': e.name,
                  'explanation': explain_assignment(e, tickets_by_id[tid])}
            for e in engineers for tid in routes[e.id]
        },
        'metrics': compute_metrics(route_objs, all_unassigned),
    }
    return plan
