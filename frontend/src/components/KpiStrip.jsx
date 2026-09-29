export default function KpiStrip({ metrics, comparison }) {
  const cards = [
    ['Инженеров задействовано', metrics.engineers_used,
      comparison ? `baseline: ${comparison.engineers_used.baseline} (${comparison.engineers_used.delta})` : null],
    ['Заявок назначено', `${metrics.tickets_assigned} / ${metrics.tickets_assigned + metrics.tickets_unassigned}`,
      comparison ? `baseline назначил: ${comparison.assigned.baseline}` : null],
    ['Не назначено', metrics.tickets_unassigned,
      comparison ? `baseline: ${comparison.unassigned.baseline}` : null],
    ['Суммарный пробег', `${metrics.total_distance_km} км`,
      comparison ? `baseline: ${comparison.total_distance_km.baseline} км (Δ ${comparison.total_distance_km.delta})` : null],
  ]
  return (
    <div className="px-4 pt-3 grid grid-cols-2 lg:grid-cols-4 gap-3">
      {cards.map(([label, value, sub]) => (
        <div key={label} className="glass rounded-xl p-3">
          <div className="text-xs text-white/60 uppercase tracking-wide">{label}</div>
          <div className="text-2xl font-bold">{value}</div>
          {sub && <div className="text-xs text-white/50 mt-1">{sub}</div>}
        </div>
      ))}
    </div>
  )
}
