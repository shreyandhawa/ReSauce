import { useMemo, useState } from 'react'
import { OutcomeSign, StatusSign } from './Bits.jsx'
import Icon from './Icon.jsx'
import { signedDay } from '../lib/format.js'
import { OUTCOMES, matchesFilter } from '../lib/outcome.js'
import { setOrigin } from '../lib/motion.js'

const REVIEW = [['all', 'Any review state'], ['to_review', 'Findings to review'], ['reviewed', 'Reviewed'], ['no_findings', 'Nothing to review'], ['not_run', 'Not verified yet']]

/** The pipeline as a list: the same records, outcomes and review state as the network, as a table. */
export default function CaseList({ rows, records, place, filter, onOpen }) {
  const [query, setQuery] = useState('')
  const [review, setReview] = useState('all')
  const list = useMemo(() => {
    const q = query.trim().toUpperCase()
    return rows.filter((r) => {
      if (q && !r.case_id.includes(q)) return false
      if (review !== 'all' && r.status !== review) return false
      return matchesFilter(place(r.case_id).pending ? null : records.get(r.case_id), filter)
    })
  }, [rows, records, place, filter, query, review])

  return (
    <div className="caselist">
      <div className="caselist-bar">
        <div className="search"><Icon name="search" size={16} /><input className="input" type="search" placeholder="Find a case ID" aria-label="Find a case ID" value={query} onChange={(e) => setQuery(e.target.value)} /></div>
        <select className="select" aria-label="Review state" value={review} onChange={(e) => setReview(e.target.value)}>
          {REVIEW.map(([v, text]) => <option key={v} value={v}>{text}</option>)}
        </select>
      </div>
      <div className="table-wrap">
        <table className="data">
          <thead>
            <tr><th scope="col">Case</th><th scope="col">Pipeline outcome</th><th scope="col">Record onset</th><th scope="col">Record grade</th><th scope="col">Review</th></tr>
          </thead>
          <tbody>
            {list.map((r) => {
              const rec = records.get(r.case_id)
              const href = `#/case/${encodeURIComponent(r.case_id)}`
              return (
                <tr key={r.case_id} className="row-link" onClick={(e) => { if (!e.target.closest('a')) { onOpen(r.case_id, e.currentTarget.getBoundingClientRect()) } }}>
                  <td><a className="case-link" href={href} onClick={(e) => setOrigin(e.currentTarget.closest('tr')?.getBoundingClientRect())}>{r.case_id}</a></td>
                  <td>{place(r.case_id).pending
                    ? <span className="muted">Being verified in this run</span>
                    : <OutcomeSign outcome={rec?.outcome || 'not_run'}>{rec?.outcome === 'error' && r.invalid ? 'Invalid case folder' : undefined}</OutcomeSign>}</td>
                  <td>{r.record?.onset_date ? <><span className="mono">{r.record.onset_date}</span> <span className="muted">{signedDay(r.record.onset_day)}</span></> : <span className="muted">{r.record ? (r.record.icans_reported ? 'empty' : 'no ICANS') : '—'}</span>}</td>
                  <td>{r.record?.max_grade != null ? `Grade ${r.record.max_grade}` : <span className="muted">{r.record ? (r.record.icans_reported ? 'empty' : 'no ICANS') : '—'}</span>}</td>
                  <td><StatusSign status={r.status} /></td>
                </tr>
              )
            })}
            {list.length === 0 && <tr><td colSpan={5} className="muted">No case matches {query ? `“${query}”` : 'this filter'}{filter.outcome !== 'all' ? ` in “${OUTCOMES[filter.outcome].word}”` : ''}.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}
