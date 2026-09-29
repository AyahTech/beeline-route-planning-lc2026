import { MapContainer, TileLayer, Polyline, CircleMarker, Marker, Tooltip } from 'react-leaflet'
import L from 'leaflet'

function numIcon(seq, color) {
  return L.divIcon({
    className: '',
    html: '<div style="background:' + color + ';color:#fff;width:22px;height:22px;border-radius:50%;' +
          'display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;' +
          'border:2px solid #fff;box-shadow:0 1px 3px rgba(0,0,0,.5)">' + seq + '</div>',
    iconSize: [22, 22], iconAnchor: [11, 11],
  })
}

export default function MapView({ plan, engIndex, onSelect }) {
  const unassigned = plan.unassigned || []
  return (
    <MapContainer center={[55.70, 37.75]} zoom={10} className="h-full">
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                 attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' />
      {plan.routes.map((r, i) => {
        const color = ['#ff5a7a','#5ce08a','#7ba0ff','#ffb14d','#c08bff','#5ad7f2','#ff7ae0','#4ddbc0',
                       '#e0a35c','#ff6b6b','#63e6be','#a3b3ff','#ffd28c','#87f5a5'][i % 14]
        return (
          <div key={r.engineer_id}>
            <Polyline positions={r.path.map((p) => [p.lat, p.lon])} color={color} weight={4} opacity={0.8} />
            <CircleMarker center={[r.path[0].lat, r.path[0].lon]} radius={7}
                          pathOptions={{ color: '#fff', fillColor: color, fillOpacity: 1 }}>
              <Tooltip>{r.engineer_name} — старт</Tooltip>
            </CircleMarker>
            {r.stops.map((s) => (
              <Marker key={s.ticket_id} position={[r.path[s.seq].lat, r.path[s.seq].lon]}
                      icon={numIcon(s.seq, color)}
                      eventHandlers={{ click: () => onSelect({
                        kind: 'ticket', id: s.ticket_id,
                        explanation: plan.assignments[s.ticket_id]?.explanation,
                        engineer: r.engineer_name, seq: s.seq,
                        start: s.start_min, end: s.end_min }) }}>
                <Tooltip>#{s.seq} · заявка {s.ticket_id}<br/>{r.engineer_name}</Tooltip>
              </Marker>
            ))}
          </div>
        )
      })}
      {unassigned.map((u) => (
        <CircleMarker key={u.ticket.id} center={[u.ticket.lat, u.ticket.lon]} radius={8}
                      pathOptions={{ color: '#dc2626', fillColor: 'transparent', fillOpacity: 0, weight: 3 }}
                      eventHandlers={{ click: () => onSelect({ kind: 'unassigned', id: u.ticket.id,
                        explanation: u.reason, address: u.ticket.address }) }}>
          <Tooltip>✕ {u.ticket.id} — не назначена (нажмите для причины)</Tooltip>
        </CircleMarker>
      ))}
    </MapContainer>
  )
}
