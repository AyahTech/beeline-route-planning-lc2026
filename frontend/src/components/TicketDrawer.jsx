function hm(m) { return String(Math.floor(m / 60)).padStart(2, '0') + ':' + String(Math.round(m % 60)).padStart(2, '0') }

export default function TicketDrawer({ selected, plan }) {
  if (!selected) {
    return (
      <div className="glass rounded-xl p-4 text-sm text-white/60">
        <b className="text-white">Объяснения.</b> Кликните по точке на карте: для назначенной заявки — почему этот инженер и какие
        ограничения сработали; для красной пустой точки — явная причина, почему заявку разместить не удалось.
      </div>
    )
  }
  return (
    <div className={'glass rounded-xl p-4 text-sm space-y-2 border-l-4 ' +
      (selected.kind === 'ticket' ? 'border-l-white/60' : 'border-l-red-400/80')}>
      <div className="font-bold">Заявка {selected.id}</div>
      {selected.kind === 'ticket' ? (
        <>
          <div>Инженер: <b>{selected.engineer}</b>, остановка #{selected.seq}, визит {hm(selected.start)}–{hm(selected.end)}</div>
          <div className="text-white/70 italic">{selected.explanation}</div>
        </>
      ) : (
        <>
          <div className="text-red-300 font-semibold">Не назначена</div>
          <div>{selected.address}</div>
          <div className="text-white/70 italic">{selected.explanation}</div>
        </>
      )}
    </div>
  )
}
