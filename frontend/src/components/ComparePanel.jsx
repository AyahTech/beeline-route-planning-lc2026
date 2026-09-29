export default function ComparePanel({ plan }) {
  const c = plan.comparison
  if (!c) return <div className="glass rounded-xl p-6 text-sm text-white/60">Сравнение доступно при запуске солвера (baseline считается автоматически).</div>
  const Row = ({ label, s, b }) => (
    <tr className="border-t border-white/10">
      <td className="py-2 pr-4">{label}</td>
      <td className="font-bold">{s}</td><td className="text-white/60">{b}</td>
      <td className={s <= b ? 'text-green-300 font-semibold' : 'text-red-300'}>
        {(typeof s === 'number' && typeof b === 'number') ? (s - b).toFixed(1) : ''}</td>
    </tr>)
  return (
    <div className="glass rounded-xl p-6">
      <h2 className="font-bold text-lg mb-3">Солвер vs базовая линия (два обязательных метрики)</h2>
      <table className="text-sm w-full max-w-2xl">
        <thead><tr className="text-left text-white/50"><th>Метрика</th><th>Солвер</th><th>Baseline</th><th>Δ</th></tr></thead>
        <tbody>
          <Row label="Инженеров задействовано" s={c.engineers_used.solver} b={c.engineers_used.baseline} />
          <Row label="Суммарный пробег, км" s={c.total_distance_km.solver} b={c.total_distance_km.baseline} />
          <Row label="Назначено заявок" s={c.assigned.solver} b={c.assigned.baseline} />
          <Row label="Не назначено" s={c.unassigned.solver} b={c.unassigned.baseline} />
        </tbody>
      </table>
      <p className="mt-4 text-sm text-white/70 max-w-2xl">
        Baseline (по спецификации): заявки в порядке поступления → первый подходящий инженер в порядке ввода,
        порядок визитов = порядок назначения, без оптимизации. В Docker-окружении солвер — OR-Tools VRPTW
        (минимум инженеров через фиксированную стоимость, затем минимум километров); без OR-Tools автоматически
        включается жадная вставка + локальный поиск.
      </p>
    </div>
  )
}
