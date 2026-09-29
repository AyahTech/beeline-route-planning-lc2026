"""FastAPI backend: datasets, planning, replanning, baseline comparison.

Endpoints
  GET  /api/meta                     regions, depots, dataset stats
  GET  /api/tickets                  all tickets (optionally ?region=)
  GET  /api/engineers                all engineers
  POST /api/plan                     {region?, algorithm: solver|baseline}
  POST /api/replan                   {region?, algorithm?, event: {...}}
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .data_loader import load_tickets, load_engineers, load_depots
from .baseline import run_baseline
from .solver import solve
from .metrics import compare
from .replan import apply_event, diff_plans

app = FastAPI(title='Beeline Route Planning', version='1.0.0')
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])

_tickets = load_tickets()
_engineers = load_engineers()
_depots = load_depots()
_regions = sorted({t.region for t in _tickets})


def _select(region):
    ts = [t for t in _tickets if region in (None, '', 'all') or t.region == region]
    # engineers are region-agnostic crew; keep all (documented assumption)
    return ts, list(_engineers)


@app.get('/api/meta')
def meta():
    return {
        'regions': _regions,
        'depots': _depots,
        'stats': {
            'tickets': len(_tickets),
            'engineers': len(_engineers),
            'districts': len({t.district for t in _tickets}),
        },
    }


@app.get('/api/tickets')
def tickets(region: str = None):
    ts, _ = _select(region)
    return [t.__dict__ for t in ts]


@app.get('/api/engineers')
def engineers():
    return [{**e.__dict__, 'skills': '|'.join(e.skills)} for e in _engineers]


@app.post('/api/plan')
def plan(body: dict):
    region = body.get('region')
    algorithm = body.get('algorithm', 'solver')
    ts, es = _select(region)
    if not ts:
        raise HTTPException(404, 'region not found or has no tickets')
    if algorithm == 'baseline':
        result = run_baseline(ts, es)
        result['comparison'] = None
        return result
    result = solve(ts, es)
    base = run_baseline(ts, es)
    result['comparison'] = compare(result['metrics'], base['metrics'])
    result['baseline_metrics'] = base['metrics']
    return result


@app.post('/api/replan')
def replan(body: dict):
    region = body.get('region')
    algorithm = body.get('algorithm', 'solver')
    event = body.get('event')
    if not event:
        raise HTTPException(400, 'event is required')
    ts, es = _select(region)
    old = solve(ts, es) if algorithm != 'baseline' else run_baseline(ts, es)
    try:
        ts2, es2, note = apply_event(ts, es, event)
    except (ValueError, KeyError) as ex:
        raise HTTPException(400, str(ex))
    new = solve(ts2, es2) if algorithm != 'baseline' else run_baseline(ts2, es2)
    new['comparison'] = compare(new['metrics'],
                                run_baseline(ts2, es2)['metrics'])
    return {'note': note, 'plan': new, 'diff': diff_plans(old, new)}


@app.get('/healthz')
def healthz():
    return {'ok': True}
