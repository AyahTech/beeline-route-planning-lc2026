const BASE = (import.meta.env.VITE_API_URL || '') + '/api'
async function post(path, body) {
  const r = await fetch(BASE + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body || {}),
  })
  if (!r.ok) throw new Error((await r.json()).detail || r.statusText)
  return r.json()
}

export const getMeta = () => fetch(BASE + '/meta').then((r) => r.json())
export const getTickets = (region) =>
  fetch(BASE + '/tickets' + (region ? '?region=' + encodeURIComponent(region) : '')).then((r) => r.json())
export const getEngineers = () => fetch(BASE + '/engineers').then((r) => r.json())
export const runPlan = (region, algorithm) => post('/plan', { region, algorithm })
export const runReplan = (region, algorithm, event) =>
  post('/replan', { region, algorithm, event })

export const PALETTE = [
  '#e6194b', '#3cb44b', '#4363d8', '#f58231', '#911eb4', '#42d4f4', '#f032e6',
  '#bfef45', '#469990', '#9a6324', '#800000', '#aaffc3', '#808000', '#000075',
  '#e6beff', '#008080', '#ffd8b1', '#000000', '#a9a9a9', '#fabed4', '#ff8c69',
]
export const engColor = (idx) => PALETTE[idx % PALETTE.length]
