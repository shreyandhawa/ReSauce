// Calls to the local Python server (app/server.py). Every value on screen comes from here.

async function request(path, options) {
  const response = await fetch(path, options)
  let body
  try {
    body = await response.json()
  } catch {
    throw new Error(`The server sent an unreadable reply (${response.status}).`)
  }
  if (!response.ok) {
    const error = new Error(body.error || `Request failed (${response.status}).`)
    error.problems = body.problems || []
    throw error
  }
  return body
}

function post(path, body) {
  // JSON content type: the server only accepts changes sent this way from its own page.
  return request(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body || {}) })
}

/** POST and read one JSON object per line as the server sends it (a live pipeline run). */
async function stream(path, onEvent) {
  const response = await fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' })
  if (!response.ok) {
    let message = `Request failed (${response.status}).`
    try { message = (await response.json()).error || message } catch { /* keep the status text */ }
    throw new Error(message)
  }
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  for (;;) {
    const { value, done } = await reader.read()
    if (value) buffer += decoder.decode(value, { stream: true })
    let cut
    while ((cut = buffer.indexOf('\n')) >= 0) {
      const line = buffer.slice(0, cut).trim()
      buffer = buffer.slice(cut + 1)
      if (line) onEvent(JSON.parse(line))
    }
    if (done) break
  }
}

let summary = null
const id = (caseId) => encodeURIComponent(caseId)
// The reviewer named in this session (asked in the review queue) is written into run entries too.
const who = () => { try { return encodeURIComponent(sessionStorage.getItem('resauce-reviewer') || '') } catch { return '' } }

export const api = {
  workspace: () => request('/api/workspace'),
  loadExamples: () => post('/api/workspace/examples'),
  importFolder: (path) => post('/api/workspace/import', { path }),
  cases: () => request('/api/cases'),
  caseDetail: (caseId) => request(`/api/cases/${id(caseId)}`),
  createCase: (body) => post('/api/cases', body),
  verify: (caseId, baseline, onEvent) => stream(`/api/cases/${id(caseId)}/verify?baseline=${baseline ? 1 : 0}&reviewer=${who()}`, onEvent),
  verifyAll: (baseline, onEvent) => stream(`/api/verify-all?baseline=${baseline ? 1 : 0}&reviewer=${who()}`, onEvent),
  queue: () => request('/api/queue'),
  decide: (body) => post('/api/decisions', body),
  audit: () => request('/api/audit'),
  exportCase: (caseId) => post(`/api/export/case/${id(caseId)}`),
  exportCsv: () => post('/api/export/csv'),
  summary: () => (summary ||= request('/api/summary').catch((e) => { summary = null; throw e })),
}
