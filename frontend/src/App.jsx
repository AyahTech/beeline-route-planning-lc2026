import { useEffect, useMemo, useState } from 'react'
import { getMeta, runPlan, runReplan, engColor } from './api.js'
import MapView from './components/MapView.jsx'
import KpiStrip from './components/KpiStrip.jsx'
import ComparePanel from './components/ComparePanel.jsx'
import Replanner from './components/Replanner.jsx'
import TicketDrawer from './components/TicketDrawer.jsx'
import RouteTable from './components/RouteTable.jsx'

export default function App() {
  const [meta, setMeta] = useState(null)
  const [region, setRegion] = useState('all')
  const [algorithm, setAlgorithm] = useState('solver')
  const [plan, setPlan] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selected, setSelected] = useState(null)   // {kind: 'ticket'|'unassigned', data, explanation}
  const [replanDiff, setReplanDiff] = useState(null)
  const [tab, setTab] = useState('map')

  useEffect(() => { getMeta().then(setMeta).catch((e) => setError(String(e))) }, [])

  const engIndex = useMemo(() => {
    const m = {}
    ;(plan?.routes || []).forEach((r, i) => { m[r.engineer_id] = i })
    return m
  }, [plan])

  async function run() {
    setLoading(true); setError(null); setReplanDiff(null); setSelected(null)
    try { setPlan(await runPlan(region, algorithm)) }
    catch (e) { setError(String(e)) }
    setLoading(false)
  }

  async function onReplan(event) {
    setLoading(true); setError(null)
    try {
      const res = await runReplan(region, algorithm, event)
      setPlan(res.plan); setReplanDiff(res.diff)
    } catch (e) { setError(String(e)) }
    setLoading(false)
  }

  return (
    <div className="min-h-screen text-white pt-4">
      <header className="glass rounded-xl mx-4 px-4 py-3 flex items-center gap-4 flex-wrap">
        <h1 className="text-lg font-bold">Beeline Route Planning</h1>
        <span className="text-white/60 text-sm">автоматическое распределение заявок по бригадам · кейс «Контрольное распределение»</span>
      </header>

      <div className="glass rounded-xl mx-4 mt-3 px-4 py-3 flex items-center gap-3 flex-wrap">
        <label className="text-sm font-medium text-white/80">Регион:</label>
        <select value={region} onChange={(e) => setRegion(e.target.value)}
                className="glass-input rounded-lg px-2 py-1 text-sm">
          <option value="all">Все регионы</option>
          {(meta?.regions || []).map((r) => <option key={r} value={r}>{r}</option>)}
        </select>
        <label className="text-sm font-medium text-white/80">Алгоритм:</label>
        <select value={algorithm} onChange={(e) => setAlgorithm(e.target.value)}
                className="glass-input rounded-lg px-2 py-1 text-sm">
          <option value="solver">Солвер (OR-Tools / жадный)</option>
          <option value="baseline">Базовая линия (naive first-fit)</option>
        </select>
        <button onClick={run} disabled={loading}
                className="bg-yellow-400 hover:bg-yellow-300 disabled:opacity-50 text-slate-900 font-semibold px-4 py-1.5 rounded-lg text-sm shadow-lg shadow-yellow-400/20">
          {loading ? 'Считаем…' : '▶ Запустить планирование'}
        </button>
        {plan && <span className="text-sm text-white/60">план: <b className="text-white">{plan.algorithm}</b></span>}
        {error && <span className="text-sm text-red-300">{error}</span>}
      </div>

      {plan && <KpiStrip metrics={plan.metrics} comparison={plan.comparison} />}

      {plan && replanDiff && (
        <div className="px-4 pt-3">
          <div className="bg-amber-400/15 border border-amber-300/40 backdrop-blur-[15px] rounded-xl p-3 text-sm text-amber-100">
            <b>Изменения после перепланирования:</b>{' '}
            вновь назначено: {replanDiff.newly_assigned.length}, отменено: {replanDiff.newly_unassigned.length},
            сменили инженера: {replanDiff.changed_engineer.length}, изменился порядок: {replanDiff.order_changed.length},
            инженеров: {replanDiff.engineers_used.before} → {replanDiff.engineers_used.after},
            пробег: {replanDiff.total_distance_km.before} → {replanDiff.total_distance_km.after} км
          </div>
        </div>
      )}

      {plan && (
        <div className="px-4 pt-3 flex gap-2 text-sm">
          {[['map', 'Карта'], ['routes', 'Маршруты'], ['compare', 'Сравнение с baseline']].map(([k, label]) => (
            <button key={k} onClick={() => setTab(k)}
                    className={tab === k
                      ? 'px-3 py-1 rounded-lg bg-yellow-400 text-slate-900 font-semibold shadow-lg shadow-yellow-400/20'
                      : 'px-3 py-1 rounded-lg glass-btn'}>
              {label}
            </button>
          ))}
        </div>
      )}

      <main className="p-4">
        {!plan && (
          <div className="glass rounded-xl p-8 text-center text-white/60">
            Выберите регион и нажмите «Запустить планирование». Набор данных: {meta?.stats?.tickets ?? '…'} заявок,
            {' '}{meta?.stats?.engineers ?? '…'} инженеров, {meta?.stats?.districts ?? '…'} районов.
          </div>
        )}

        {plan && tab === 'map' && (
          <div className="relative grid grid-cols-1 gap-4">
            <div className="h-[560px] glass rounded-xl overflow-hidden">
              <MapView plan={plan} engIndex={engIndex} onSelect={setSelected} />
            </div>
            <div className="lg:absolute lg:top-4 lg:right-4 lg:w-80 z-[500] space-y-4 lg:max-h-[528px] lg:overflow-y-auto lg:pr-1">
              <Replanner plan={plan} onReplan={onReplan} disabled={loading} />
              <TicketDrawer selected={selected} plan={plan} engColor={(id) => engColor(engIndex[id] ?? 0)} />
            </div>
          </div>
        )}

        {plan && tab === 'routes' && <RouteTable plan={plan} engColor={(id) => engColor(engIndex[id] ?? 0)} />}
        {plan && tab === 'compare' && <ComparePanel plan={plan} />}
      </main>
    </div>
  )
}
