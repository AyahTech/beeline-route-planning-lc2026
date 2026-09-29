function hm(m) { return String(Math.floor(m / 60)).padStart(2, '0') + ':' + String(Math.round(m % 60)).padStart(2, '0') }

export default function RouteTable({ plan, engColor }) {
  const ticketInfo = {}
  ;(plan.unassigned || []).forEach((u) => { ticketInfo[u.ticket.id] = u.ticket })
  return (
    <div className="space-y-4">
      {plan.routes.map((r) => (
        <div key={r.engineer_id} className="glass rounded-xl p-4">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="w-4 h-4 rounded-full ring-2 ring-white/30" style={{ background: engColor(r.engineer_id) }} />
            <b>{r.engineer_name}</b>
            <span className="text-sm text-white/60">{r.vehicle_type} · навыки: {r.skills} · пробег {(r.distance_m / 1000).toFixed(1)} км</span>
          </div>
          <table className="mt-2 w-full text-sm">
            <thead><tr className="text-left text-white/50">
              <th className="pr-2">#</th><th className="pr-2">Заявка</th><th className="pr-2">Визит</th>
              <th className="pr-2">Дорога, мин</th><th>Обоснование</th></tr></thead>
            <tbody>{r.stops.map((s) => (
              <tr key={s.ticket_id} className="border-t border-white/10">
                <td className="pr-2">{s.seq}</td><td className="pr-2">{s.ticket_id}</td>
                <td className="pr-2">{hm(s.start_min)}–{hm(s.end_min)}</td><td className="pr-2">{s.travel_min}</td>
                <td className="text-white/60 italic">{plan.assignments[s.ticket_id]?.explanation}</td>
              </tr>))}
            </tbody>
          </table>
        </div>
      ))}
      {!!plan.unassigned.length && (
        <div className="bg-red-500/15 border border-red-400/40 backdrop-blur-[15px] rounded-xl p-4 text-sm text-red-100">
          <b className="text-red-300">Не назначено ({plan.unassigned.length}):</b>
          <ul className="mt-1 space-y-1">{plan.unassigned.map((u) => (
            <li key={u.ticket.id}><b>{u.ticket.id}</b> {u.ticket.address} — {u.reason}</li>))}
          </ul>
        </div>
      )}
    </div>
  )
}
