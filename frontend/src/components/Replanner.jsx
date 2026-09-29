import { useState } from 'react'

const URGENT_POOL = [
  { district: 'Таганский', lat: 55.741, lon: 37.653, address: 'Город Москва, ул.Мясницкая, д. 13' },
  { district: 'Кузьминки', lat: 55.700, lon: 37.781, address: 'Город Москва, ул.Васильцовский Стан, д. 5' },
  { district: 'Даниловский', lat: 55.708, lon: 37.651, address: 'Город Москва, ул.Дубининская, д. 20' },
]

export default function Replanner({ plan, onReplan, disabled }) {
  const [last, setLast] = useState(0)
  const assigned = Object.keys(plan.assignments || {})

  const injectUrgent = () => {
    const p = URGENT_POOL[last % URGENT_POOL.length]; setLast(last + 1)
    onReplan({ type: 'new_urgent_ticket', ticket: {
      id: 'URG-' + Date.now().toString().slice(-6), region: 'Восток',
      type_bk: 'Локальная заявка', type_hd: 'Авария', required_skill: 'emergency',
      priority: 'urgent', window_start: 17 * 60, window_end: 19 * 60, duration_min: 90,
      district: p.district, address: p.address, lat: p.lat, lon: p.lon,
      coord_approx: true, required_vehicle: null, gigabit: 'Нет' } })
  }
  const cancelRandom = () => {
    const tid = assigned[Math.floor(Math.random() * assigned.length)]
    onReplan({ type: 'cancel_ticket', ticket_id: tid })
  }
  const dropEngineer = () => {
    const r = plan.routes[Math.floor(Math.random() * plan.routes.length)]
    onReplan({ type: 'engineer_unavailable', engineer_id: r.engineer_id })
  }

  return (
    <div className="glass rounded-xl p-4 text-sm space-y-2">
      <div className="font-bold">Перепланирование (событие → реплан → diff)</div>
      <div className="flex flex-col gap-2">
        <button disabled={disabled} onClick={injectUrgent}
          className="bg-red-500/80 hover:bg-red-500 text-white rounded-lg px-3 py-1.5 disabled:opacity-50 transition-colors">⚡ Срочная заявка (авария)</button>
        <button disabled={disabled || !assigned.length} onClick={cancelRandom}
          className="glass-btn rounded-lg px-3 py-1.5 disabled:opacity-50">✕ Отмена случайной заявки</button>
        <button disabled={disabled || !plan.routes.length} onClick={dropEngineer}
          className="glass-btn rounded-lg px-3 py-1.5 disabled:opacity-50">🚫 Инженер недоступен</button>
      </div>
    </div>
  )
}
