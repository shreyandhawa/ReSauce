import { useMemo, useRef, useState } from 'react'
import { api } from '../api.js'
import { Loading, Problem, STATUS_WORDS, Segmented, StatusSign } from '../components/Bits.jsx'
import Icon from '../components/Icon.jsx'
import { PIPELINES, signedDay } from '../lib/format.js'
import { useLoad } from '../lib/hooks.js'
import { setOrigin } from '../lib/motion.js'

// Kept between visits, so returning to the list restores the same search and filter.
const memory = { query: '', status: 'all' }
const FILTERS = [['all', 'All'], ['not_run', 'Not run'], ['to_review', 'To review'], ['no_findings', 'No findings'], ['reviewed', 'Reviewed']]

export default function Cases({ workspace, onChanged }) {
  const list = useLoad(() => api.cases(), [])
  const [query, setQuery] = useState(memory.query)
  const [status, setStatus] = useState(memory.status)
  const [batch, setBatch] = useState(null) // { done, total, current, failed }
  const [baseline, setBaseline] = useState(false)
  const [pipeline, setPipeline] = useState('v1')
  const [changed, setChanged] = useState({}) // case_id -> live status from the batch run
  const [opening, setOpening] = useState(false)
  const [loadingExamples, setLoadingExamples] = useState(false)
  const [message, setMessage] = useState(null)

  const rows = useMemo(() => {
    const all = (list.data?.cases || []).map((r) => (changed[r.case_id] ? { ...r, ...changed[r.case_id] } : r))
    const q = query.trim().toUpperCase()
    return all.filter((r) => (!q || r.case_id.includes(q)) && (status === 'all' || r.status === status))
  }, [list.data, changed, query, status])

  const total = list.data?.cases.length ?? 0
  const setQ = (v) => { memory.query = v; setQuery(v) }
  const setS = (v) => { memory.status = v; setStatus(v) }

  const verifyAll = async () => {
    setBatch({ done: 0, total, current: null })
    setChanged({})
    try {
      await api.verifyAll(baseline, (e) => {
        if (e.event === 'start') setBatch({ done: 0, total: e.total, current: null })
        if (e.event === 'case') {
          setBatch((b) => ({ ...b, done: e.index, current: e.case_id, mismatched: (b.mismatched || 0) + (e.matches_stored && Object.values(e.matches_stored).includes(false) ? 1 : 0) }))
          setChanged((c) => ({ ...c, [e.case_id]: { status: e.status, open: e.open, flash: true } }))
        }
        if (e.event === 'done') setBatch((b) => ({ ...b, finished: true }))
      }, pipeline)
    } catch (error) {
      setBatch((b) => ({ ...b, failed: error }))
    }
    list.reload()
    onChanged?.()
  }

  const loadExamples = async () => {
    setLoadingExamples(true)
    try {
      const r = await api.loadExamples()
      setMessage({ ok: true, text: `Copied ${r.copied.length} synthetic example cases from ${r.source} into the workspace.${r.skipped_existing.length ? ` ${r.skipped_existing.length} already there.` : ''}` })
      list.reload(); onChanged?.()
    } catch (error) { setMessage({ ok: false, text: error.message }) }
    setLoadingExamples(false)
  }

  if (list.error) return <div className="page"><Problem title="The workspace could not be read" error={list.error} /></div>
  if (!list.data) return <div className="page"><Loading label="Reading the workspace" /></div>

  const running = batch && !batch.finished && !batch.failed
  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Cases</h1>
          <p className="sub">Workspace <span className="mono">{workspace?.path}</span> · {total} case{total === 1 ? '' : 's'}</p>
        </div>
        <div className="actions">
          <a className="btn" href="#/new"><Icon name="plus" size={16} />New case</a>
          <button type="button" className="btn" onClick={() => setOpening((o) => !o)} aria-expanded={opening}><Icon name="folder" size={16} />Open folder…</button>
          {total > 0 && <button type="button" className="btn btn-primary" onClick={verifyAll} disabled={running}><Icon name="play" size={16} />{running ? 'Verifying…' : 'Verify all'}</button>}
        </div>
      </div>

      {opening && <OpenFolder onDone={(text, ok) => { setMessage({ ok, text }); list.reload(); onChanged?.() }} />}
      {message && <p className={`callout${message.ok ? '' : ' callout-alert'}`} role="status" style={{ marginBottom: 14 }}>{message.text}</p>}

      {total === 0 ? (
        <div className="panel empty">
          <h2>This workspace has no cases yet</h2>
          <p>Start with the {workspace?.example_count ?? ''} fictional example cases (copied from <span className="mono">data/dev-v1</span>; the originals are never changed), or enter a new synthetic case through the form.</p>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <button type="button" className="btn btn-primary" onClick={loadExamples} disabled={loadingExamples}>{loadingExamples ? 'Copying…' : 'Load the synthetic example cases'}</button>
            <a className="btn" href="#/new">New case</a>
          </div>
        </div>
      ) : (
        <>
          {batch && (
            <div className="progress" role="status" aria-live="polite">
              <div className="progress-track"><div className="progress-fill" style={{ '--p': batch.total ? batch.done / batch.total : 0 }} /></div>
              <p className="progress-text">
                {batch.failed ? `Stopped: ${batch.failed.message}` : batch.finished ? `Verified ${batch.done} of ${batch.total} cases.` : `Verifying ${batch.current || '…'} · ${batch.done} of ${batch.total}`}
                {batch.finished && batch.mismatched ? ` ${batch.mismatched} case(s) differ from the stored evaluation run.` : ''}
              </p>
            </div>
          )}
          <div className="toolbar">
            <div className="search"><Icon name="search" size={16} /><input className="input" type="search" placeholder="Find a case ID" aria-label="Find a case ID" value={query} onChange={(e) => setQ(e.target.value)} /></div>
            <Segmented label="Verification status" options={FILTERS} value={status} onChange={setS} />
            <Segmented label="Pipeline to verify with" options={PIPELINES} value={pipeline} onChange={setPipeline} />
            <label className="check" style={{ marginLeft: 'auto' }}><input type="checkbox" checked={baseline} onChange={(e) => setBaseline(e.target.checked)} /> Verify all with simple baseline too</label>
          </div>
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr><th>Case</th><th>Documents</th><th>Record onset</th><th>Record grade</th><th>Verification</th><th className="num">Open findings</th></tr>
              </thead>
              <tbody>
                {rows.map((r) => <Row key={r.case_id} r={r} />)}
                {rows.length === 0 && <tr><td colSpan={6} className="muted">No case matches {query ? `“${query}”` : 'this filter'}{status !== 'all' ? ` with status “${STATUS_WORDS[status]}”` : ''}.</td></tr>}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}

function Row({ r }) {
  const ref = useRef(null)
  const href = `#/case/${encodeURIComponent(r.case_id)}`
  // Orient: remember where the row is, so the case view can open out of it.
  const open = () => { setOrigin(ref.current?.getBoundingClientRect()); window.location.hash = href }
  if (r.invalid) {
    return <tr><td><a className="case-link" href={href}>{r.case_id}</a></td><td colSpan={3} className="muted">{r.invalid.slice(0, 140)}</td><td><StatusSign status="invalid" /></td><td /></tr>
  }
  const rec = r.record
  return (
    <tr ref={ref} className="row-link" onClick={(e) => { if (!e.target.closest('a')) open() }}>
      <td><a className="case-link" href={href} onClick={(e) => { e.preventDefault(); open() }}>{r.case_id}</a></td>
      <td>{r.documents} <span className="muted">({r.document_versions} versions)</span></td>
      <td>{rec.onset_date ? <><span className="mono">{rec.onset_date}</span> <span className="muted">{signedDay(rec.onset_day)}</span></> : <span className="muted">{rec.icans_reported ? 'empty' : 'no ICANS'}</span>}</td>
      <td>{rec.max_grade != null ? `Grade ${rec.max_grade}` : <span className="muted">{rec.icans_reported ? 'empty' : 'no ICANS'}</span>}</td>
      {/* Connect cause and effect: a status that the batch run just changed fades in once. */}
      <td><span key={r.status + (r.flash ? 'f' : '')} className={r.flash ? 'just-changed' : undefined}><StatusSign status={r.status} alerts={r.open_alerts} /></span></td>
      <td className="num">{r.status === 'not_run' ? <span className="muted">–</span> : r.open}</td>
    </tr>
  )
}

function OpenFolder({ onDone }) {
  const [path, setPath] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const submit = async (e) => {
    e.preventDefault()
    setBusy(true); setError(null)
    try {
      const r = await api.importFolder(path)
      const parts = [`Imported ${r.imported.length} case(s) from ${r.source}.`]
      if (r.skipped_existing.length) parts.push(`${r.skipped_existing.length} already in the workspace.`)
      if (r.invalid.length) parts.push(`${r.invalid.length} did not pass the data-format check and were not imported: ${r.invalid.map((x) => `${x.case} (${x.problems[0]})`).join('; ')}`)
      onDone(parts.join(' '), r.invalid.length === 0)
    } catch (err) { setError(err.message) }
    setBusy(false)
  }
  return (
    <form className="panel" onSubmit={submit} style={{ marginBottom: 14, display: 'grid', gap: 10 }}>
      <div className="field">
        <label htmlFor="folder-path">Folder to copy cases from</label>
        <input id="folder-path" className="input mono" value={path} onChange={(e) => setPath(e.target.value)} placeholder="e.g. data/dev-v1 or a case folder" />
        <span className="hint">A dataset folder (with cases/) or one case folder. In this proof of concept only folders inside the ReSauce folder can be opened. Valid cases are copied into the workspace; the source is only read.</span>
        {error && <span className="problem-text problem-in"><Icon name="error" size={14} />{error}</span>}
      </div>
      <div><button type="submit" className="btn" disabled={busy || !path.trim()}>{busy ? 'Copying…' : 'Copy cases into the workspace'}</button></div>
    </form>
  )
}
