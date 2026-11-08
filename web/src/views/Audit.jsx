import { Fragment, useMemo, useState } from 'react'
import { api } from '../api.js'
import { Loading, Problem, Segmented } from '../components/Bits.jsx'
import Icon from '../components/Icon.jsx'
import { FIELD_NAMES } from '../lib/format.js'
import { useLoad } from '../lib/hooks.js'
import { setOrigin } from '../lib/motion.js'

const TYPES = [['all', 'All'], ['run', 'Verification runs'], ['decision', 'Decisions']]

export default function Audit() {
  const audit = useLoad(() => api.audit(), [])
  const [type, setType] = useState('all')
  const [caseQ, setCaseQ] = useState('')
  const [reviewer, setReviewer] = useState('')
  const [open, setOpen] = useState(null)

  const entries = useMemo(() => {
    const all = (audit.data?.entries || []).map((e, i) => ({ ...e, line: i + 1 })).reverse()
    return all.filter((e) => (type === 'all' || e.type === type)
      && (!caseQ.trim() || (e.case_id || '').includes(caseQ.trim().toUpperCase()))
      && (!reviewer.trim() || (e.reviewer || '').toLowerCase().includes(reviewer.trim().toLowerCase())))
  }, [audit.data, type, caseQ, reviewer])

  if (audit.error) return <div className="page"><Problem title="The audit log could not be read" error={audit.error} /></div>
  if (!audit.data) return <div className="page"><Loading label="Reading the audit log" /></div>
  const reviewers = [...new Set(audit.data.entries.map((e) => e.reviewer).filter(Boolean))]

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Audit trail</h1>
          <p className="sub">Every verification run and review decision, newest first. Append-only, one JSON object per line in <span className="mono">{audit.data.path}</span>. Entries are never changed; a later decision on the same finding is added below the earlier one.</p>
        </div>
      </div>
      <div className="toolbar">
        <Segmented label="Entry type" options={TYPES} value={type} onChange={setType} />
        <div className="search"><Icon name="search" size={16} /><input className="input" type="search" placeholder="Case ID" aria-label="Filter by case ID" value={caseQ} onChange={(e) => setCaseQ(e.target.value)} /></div>
        <div className="search"><Icon name="search" size={16} /><input className="input" type="search" list="reviewers" placeholder="Reviewer" aria-label="Filter by reviewer" value={reviewer} onChange={(e) => setReviewer(e.target.value)} /></div>
        <datalist id="reviewers">{reviewers.map((r) => <option key={r} value={r} />)}</datalist>
        <span className="note">{entries.length} of {audit.data.entries.length} entries</span>
      </div>
      <div className="table-wrap">
        <table className="data">
          <thead><tr><th>Time</th><th>Entry</th><th>Reviewer</th><th>Case</th><th>Field</th><th>Decision or result</th><th>Note</th><th>Pipeline</th></tr></thead>
          <tbody>
            {entries.length === 0 && <tr><td colSpan={8} className="muted">{audit.data.entries.length ? 'No entry matches these filters.' : 'Nothing logged yet. Verify a case to add the first entry.'}</td></tr>}
            {entries.map((e) => (
              <Entry key={e.line} e={e} open={open === e.line} onToggle={() => setOpen(open === e.line ? null : e.line)} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function Entry({ e, open, onToggle }) {
  if (e.type === 'unreadable') return <tr><td colSpan={8} className="match-no">Line {e.line} could not be read: <span className="mono">{e.text.slice(0, 120)}</span></td></tr>
  const p = e.pipeline || {}
  const result = e.type === 'run'
    ? (e.error ? `Error: ${e.error}` : e.out_of_scope ? `Out of scope (${e.out_of_scope})` : e.categories ? `onset ${e.categories.onset} · grade ${e.categories.max_grade} · ${e.findings} finding(s)` : '')
    : e.decision_label
  return (
    <>
      <tr>
        <td className="mono" style={{ whiteSpace: 'nowrap' }}>{e.time?.replace('T', ' ').slice(0, 19)}</td>
        <td className="nowrap"><button type="button" className="linkish" aria-expanded={open} onClick={onToggle}>{e.type === 'run' ? 'Verification run' : 'Decision'}</button></td>
        <td>{e.reviewer || <span className="muted">–</span>}</td>
        <td className="mono">{e.case_id ? <a href={`#/case/${encodeURIComponent(e.case_id)}`} onClick={(ev) => setOrigin(ev.currentTarget.closest('tr')?.getBoundingClientRect())}>{e.case_id}</a> : ''}</td>
        <td>{e.field ? FIELD_NAMES[e.field] || e.field : e.type === 'decision' ? <span className="muted">{e.finding_id}</span> : ''}</td>
        <td>{e.type === 'decision' ? <><strong>{result}</strong><div className="muted">{e.finding}</div></> : result}</td>
        <td>{e.note || ''}</td>
        <td className="mono" style={{ whiteSpace: 'nowrap' }}>{p.tag} {(p.tag_commit || '').slice(0, 7)} <span className={`sign ${p.frozen_files_match ? 'sign-reviewed' : 'sign-alert'}`} style={{ fontWeight: 400 }}><Icon name={p.frozen_files_match ? 'clear' : 'error'} size={14} />{p.frozen_files_match ? 'frozen' : 'changed'}</span></td>
      </tr>
      {open && (
        <tr><td colSpan={8} style={{ background: 'var(--surface-2)' }}>
          <dl className="facts-list">
            <dt>Run</dt><dd className="mono">{e.run_id}</dd>
            <dt>Output SHA-256</dt><dd className="mono">{e.output_sha256 || 'none'}</dd>
            {e.type === 'run' && <><dt>Matches stored</dt><dd>{e.matches_stored ? Object.entries(e.matches_stored).map(([m, v]) => `${m}: ${v === true ? 'yes' : v === false ? 'NO' : 'n/a'}`).join(' · ') : 'no stored result for this case folder'}</dd></>}
            <dt>Pipeline commit</dt><dd className="mono">{p.tag_commit || 'unknown'} (HEAD {p.head_commit?.slice(0, 7) || 'unknown'})</dd>
            {Object.entries(p.frozen_files || {}).map(([f, h]) => <Fragment key={f}><dt className="mono">{f}</dt><dd className="mono">{h}</dd></Fragment>)}
          </dl>
        </td></tr>
      )}
    </>
  )
}
