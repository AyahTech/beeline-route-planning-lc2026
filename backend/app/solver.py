"""Solver: OR-Tools VRPTW (primary) with a greedy-insertion + local-search
fallback (spec explicitly accepts "a ready-made library, a simple heuristic,
or your own clear logic").

Objective is lexicographic, matching the two mandatory metrics:
  1. fewest engineers used   (fixed cost per used vehicle >> any mileage)
  2. minimal total mileage

Model notes: transit time includes the ORIGIN node's service time; a ticket's
cumul window is [window_start, window_end]. All real windows here are >= 120
min and max duration is 120 min, so every OR-Tools-feasible route also passes
the stricter timeline simulation in route.py (build_plan re-checks and drops
anything that does not, with an explicit reason).
"""
from .constraints import engineer_can_take
from .route import simulate, route_distance_m


def solve(tickets, engineers, max_seconds=10):
    try:
        return solve_ortools(tickets, engineers, max_seconds)
    except Exception:
        return solve_greedy(tickets, engineers)


# ---------------------------------------------------------------- greedy fallback
def solve_greedy(tickets, engineers):
    tickets_by_id = {t.id: t for t in tickets}
    routes = {e.id: [] for e in engineers}
    unassigned, attempts = [], {}

    order = sorted(tickets,
                   key=lambda t: (0 if t.priority == 'urgent' else 1,
                                  t.window_start, -t.duration_min, t.arrival_order))
    for tk in order:
        best = None  # (added_m, engineer, pos)
        attempts[tk.id] = {}
        for e in engineers:
            ok, _, reason = engineer_can_take(e, tk)
            if not ok:
                attempts[tk.id][e.name] = reason
                continue
            base_d = route_distance_m(e, routes[e.id], tickets_by_id) if routes[e.id] else 0.0
            feasible = False
            for pos in range(len(routes[e.id]) + 1):
                cand = routes[e.id][:pos] + [tk.id] + routes[e.id][pos:]
                if simulate(e, cand, tickets_by_id) is None:
                    continue
                feasible = True
                added = route_distance_m(e, cand, tickets_by_id) - base_d
                if best is None or added < best[0]:
                    best = (added, e, pos)
            if not feasible:
                attempts[tk.id][e.name] = (
                    'не хватает времени на дорогу/работу в рамках окна и смены')
        if best:
            _, e, pos = best
            routes[e.id] = routes[e.id][:pos] + [tk.id] + routes[e.id][pos:]
        else:
            unassigned.append(tk)

    _local_search(tickets_by_id, engineers, routes)
    _reduce_engineers(tickets_by_id, tickets, engineers, routes)
    _local_search(tickets_by_id, engineers, routes)
    from .baseline import build_plan
    return build_plan('solver (greedy)', tickets, engineers, routes, unassigned, attempts)


def _local_search(tickets_by_id, engineers, routes, max_passes=4):
    improved = True
    passes = 0
    while improved and passes < max_passes:
        improved = False
        passes += 1
        used = [e for e in engineers if routes[e.id]]
        for e1 in used:
            for i, tid in enumerate(list(routes[e1.id])):
                moved = False
                for e2 in engineers:
                    r2 = routes[e2.id]
                    positions = range(len(r2) + 1) if e2 is not e1 else range(len(r2))
                    for pos in positions:
                        c1 = routes[e1.id][:i] + routes[e1.id][i + 1:]
                        c2 = r2[:pos] + [tid] + r2[pos:]
                        affected = [e1] if e2 is e1 else [e1, e2]
                        cand = {e1.id: c1 if e2 is not e1 else c2}
                        if e2 is not e1:
                            cand[e2.id] = c2
                        if not all(simulate(e, cand[e.id], tickets_by_id) is not None
                                   for e in affected):
                            continue
                        before = route_distance_m(e1, routes[e1.id], tickets_by_id) +                             (0 if e2 is e1 else route_distance_m(e2, r2, tickets_by_id))
                        after = route_distance_m(e1, cand[e1.id], tickets_by_id) +                             (0 if e2 is e1 else route_distance_m(e2, cand[e2.id], tickets_by_id))
                        if after < before - 1e-6:
                            routes[e1.id] = cand[e1.id]
                            if e2 is not e1:
                                routes[e2.id] = cand[e2.id]
                            improved = True
                            moved = True
                            break
                    if moved:
                        break
                if moved:
                    break
            if improved:
                break


def _reduce_engineers(tickets_by_id, tickets, engineers, routes):
    """Lexicographic objective for the greedy fallback: try to empty the
    least-loaded engineer by re-inserting all of their tickets elsewhere."""
    from .constraints import engineer_can_take
    import time as _time
    deadline = _time.monotonic() + 6.0
    changed = True
    while changed and _time.monotonic() < deadline:
        changed = False
        loaded = sorted((e for e in engineers if 0 < len(routes[e.id]) <= 6),
                        key=lambda e: len(routes[e.id]))
        for e1 in loaded:
            tids = list(routes[e1.id])
            others = [e for e in engineers if e is not e1]
            moved_all, new_routes = True, {}
            for tid in tids:
                tk = tickets_by_id[tid]
                best = None
                for e2 in others:
                    ok, _, _ = engineer_can_take(e2, tk)
                    if not ok:
                        continue
                    r2 = routes[e2.id] + [x for x in new_routes.get(e2.id, [])]
                    for pos in range(len(r2) + 1):
                        cand = r2[:pos] + [tid] + r2[pos:]
                        if simulate(e2, cand, tickets_by_id) is None:
                            continue
                        d = route_distance_m(e2, cand, tickets_by_id)
                        if best is None or d < best[0]:
                            best = (d, e2, cand)
                if best is None:
                    moved_all = False
                    break
                new_routes[best[1].id] = best[2]
            if moved_all and new_routes:
                routes[e1.id] = []
                for eid, r in new_routes.items():
                    routes[eid] = r
                changed = True
                break


# ---------------------------------------------------------------- OR-Tools VRPTW
def solve_ortools(tickets, engineers, max_seconds=10):
    from ortools.constraint_solver import pywrapcp, routing_enums_pb2
    from .geo import travel_min, travel_m

    T = list(tickets)
    if not T:
        from .baseline import build_plan
        return build_plan('solver (ortools)', tickets, engineers,
                          {e.id: [] for e in engineers}, [], {})

    manager = pywrapcp.RoutingIndexManager(len(T), len(engineers), 0)
    routing = pywrapcp.RoutingModel(manager)

    # per-vehicle transit callback: travel + ORIGIN service time, in seconds
    transit_indices = []
    for e in engineers:
        def make_cb(eng):
            def cb(from_i, to_i):
                a = T[manager.IndexToNode(from_i)]
                b = T[manager.IndexToNode(to_i)]
                t = travel_min(a.lat, a.lon, b.lat, b.lon, eng.vehicle_type) * 60.0
                return int(round(t + a.duration_min * 60))
            return cb
        transit_indices.append(routing.RegisterTransitCallback(make_cb(e)))
    routing.AddDimensionWithVehicleTransits(transit_indices, 0, 24 * 3600, False, 'Time')
    time_dim = routing.GetDimensionOrDie('Time')

    for i, tk in enumerate(T):
        idx = manager.NodeToIndex(i)
        time_dim.CumulVar(idx).SetRange(tk.window_start * 60, tk.window_end * 60)

    for v, e in enumerate(engineers):
        time_dim.CumulVar(routing.Start(v)).SetRange(
            e.shift_start * 60, e.shift_start * 60)
        time_dim.CumulVar(routing.End(v)).SetRange(
            e.shift_start * 60, e.shift_end * 60)

    # skill & vehicle eligibility
    for i, tk in enumerate(T):
        idx = manager.NodeToIndex(i)
        allowed = [v for v, e in enumerate(engineers) if engineer_can_take(e, tk)[0]]
        if allowed:
            routing.VehicleVar(idx).SetValues(allowed)

    # objective: fewest engineers, then mileage
    dist_indices = []
    for e in engineers:
        def make_dcb(eng):
            def cb(from_i, to_i):
                a = T[manager.IndexToNode(from_i)]
                b = T[manager.IndexToNode(to_i)]
                return int(round(travel_m(a.lat, a.lon, b.lat, b.lon)))
            return cb
        dist_indices.append(routing.RegisterTransitCallback(make_dcb(e)))
    for v in range(len(engineers)):
        routing.SetArcCostEvaluatorOfVehicle(dist_indices[v], v)
    try:
        routing.SetFixedCostOfAllVehicles(10 ** 9)
    except AttributeError:
        for v in range(len(engineers)):
            routing.SetFixedCostOfVehicle(10 ** 9, v)

    # unassigned tickets allowed but heavily penalised (reported explicitly)
    for i, tk in enumerate(T):
        routing.AddDisjunction([manager.NodeToIndex(i)], 10 ** 12)

    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    params.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    params.time_limit.FromSeconds(max_seconds)
    solution = routing.SolveWithParameters(params)

    from .baseline import build_plan
    if solution is None:
        return build_plan('solver (ortools)', tickets, engineers,
                          {e.id: [] for e in engineers}, T, {})

    routes = {e.id: [] for e in engineers}
    assigned = set()
    for v in range(len(engineers)):
        idx = routing.Start(v)
        while not routing.IsEnd(idx):
            node = manager.IndexToNode(idx)
            routes[engineers[v].id].append(T[node].id)
            assigned.add(node)
            idx = solution.Value(routing.NextVar(idx))
    unassigned = [T[i] for i in range(len(T)) if i not in assigned]
    attempts = {t.id: {} for t in unassigned}
    return build_plan('solver (ortools)', tickets, engineers, routes, unassigned, attempts)
