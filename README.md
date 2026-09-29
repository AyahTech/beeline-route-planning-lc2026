# Beeline Route Planning — Field Service Dispatch Prototype

Full stack: FastAPI + OR-Tools (VRPTW) backend, React + Leaflet frontend, and processed data from three regions (205 service requests, 34 engineers). Case: “Control Allocation.”

## Quick Start

    docker compose up --build        # backend :8000, frontend :5173

Or run locally (two terminals):

    cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload
    cd frontend && npm install && npm run dev        # proxy /api -> :8000

## Demo Scenario (5–7 minutes)

1. Load the dataset (all regions / one region).
2. Click “Run Planning” → assignments appear on the map.
3. Map: each engineer’s route has its own color, numbered stop markers, and starting-point markers.
4. Click a point → an explanation of why this engineer was assigned and which constraints applied.
5. Replanning: ⚡ urgent request / ✕ cancellation / 🚫 engineer unavailable → changes are highlighted.
6. “Comparison with Baseline” tab — the two required metrics are shown side by side.

## Three Groups of Constraints (Implemented in `app/constraints.py`)

- Qualifications: the skill required by the request is among the engineer’s skills (`local` / `connection` / `emergency`).
- Time: travel and work fit within the engineer’s shift; the visit starts within the request’s time window.
- Resources: if a request requires a transport type, it must match the engineer’s transport type (`null` = “no restriction”).

## Two Required Metrics (`app/metrics.py`)

1. Minimum number of engineers used.
2. Distance traveled per engineer and in total, compared with the baseline (arrival order, first-fit).

## Assumptions (Explicitly Stated)

| Assumption | Rationale |
|---|---|
| Coordinates | Geocoding cache: `scripts/build_data.py --geocode` (Nominatim + address normalization); fallback — district centroid + deterministic jitter, with the `coord_approx` flag. |
| Distance/time | Haversine × 1.35 road factor; speeds: car 30, public transport 25, bicycle 15, walking 5 km/h. |
| Engineers | No engineer file is available → synthesized from 34 historical crews in the control files: skills from the types of their requests, shifts = time slots ±2 hours, start = home district. |
| Depots | Office addresses from the footer rows of the source files. |
| Duration/priority | Mapped from the HD type (Emergency: 90 min → `urgent`); time windows from the Start/End columns. |
| Route | Starts at the engineer’s location; no return is required (according to the case specification). |

## API

    GET  /api/meta
    GET  /api/tickets?region=
    GET  /api/engineers
    POST /api/plan     {region, algorithm: solver|baseline}
    POST /api/replan   {region, algorithm, event: {type: new_urgent_ticket|cancel_ticket|engineer_unavailable, ...}}

## Structure

    backend/app/          solver (OR-Tools + greedy fallback), baseline, metrics, explain, replan
    backend/data/         processed (tickets/engineers/depots/coords) + raw (6 original CSV files)
    frontend/src/         React SPA: map, KPIs, tables, replanning, comparison
    scripts/build_data.py reproducible pipeline from raw -> processed
