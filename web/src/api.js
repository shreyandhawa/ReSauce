// Calls to the Python server (app/server.py). Every number on screen comes from here.

async function request(path, options) {
  const response = await fetch(path, options)
  let body
  try {
    body = await response.json()
  } catch {
    throw new Error(`The server sent an unreadable reply (${response.status}).`)
  }
  if (!response.ok) throw new Error(body.error || `Request failed (${response.status}).`)
  return body
}

const cache = new Map()
function cached(path) {
  if (!cache.has(path)) cache.set(path, request(path).catch((e) => { cache.delete(path); throw e }))
  return cache.get(path)
}

export const api = {
  summary: () => cached('/api/summary'),
  cases: () => cached('/api/cases'),
  caseDetail: (id) => cached(`/api/cases/${encodeURIComponent(id)}`),
  run: (id) => request(`/api/cases/${encodeURIComponent(id)}/run`, { method: 'POST' }),
}
