import { useState } from 'react'
import { api } from '../api.js'
import { Loading } from '../components/Bits.jsx'
import Icon from '../components/Icon.jsx'
import { useLoad } from '../lib/hooks.js'

export default function Export() {
  const cases = useLoad(() => api.cases(), [])
  const [caseId, setCaseId] = useState('')
  const [report, setReport] = useState(null)
  const [csv, setCsv] = useState(null)
  const [busy, setBusy] = useState(null)

  const run = async (kind) => {
    setBusy(kind)
    try {
      if (kind === 'report') {
        const r = await api.exportCase(caseId || cases.data.cases[0].case_id)
        setReport({ ok: true, ...r })
        window.open(r.url, '_blank', 'noopener')
      } else {
        const r = await api.exportCsv()
        setCsv({ ok: true, ...r })
        const a = document.createElement('a'); a.href = r.url; a.download = ''; a.click()
      }
    } catch (error) {
      ;(kind === 'report' ? setReport : setCsv)({ ok: false, message: error.message })
    }
    setBusy(null)
  }

  if (!cases.data) return <div className="page"><Loading label="Reading the workspace" /></div>
  const list = cases.data.cases
  return (
    <div className="page">
      <div className="page-head">
        <div><p className="crumb"><a href="#/audit"><Icon name="back" size={14} />Audit</a></p><h1>Export</h1><p className="sub">Files are written into the workspace’s <span className="mono">exports/</span> folder and opened from there. Each carries the pipeline version it was made with.</p></div>
      </div>
      {list.length === 0 ? <p className="note">The workspace has no cases yet.</p> : (
        <div className="export-grid">
          <section className="panel" aria-labelledby="ex-r">
            <h2 id="ex-r">Case report</h2>
            <p className="note">A printable page: case summary, the record, each finding with its evidence quotes, the decisions and their history, and the pipeline version with the frozen-file hashes. Use the browser’s Print to make a PDF.</p>
            <div className="field">
              <label htmlFor="ex-case">Case</label>
              <select id="ex-case" className="select" value={caseId || list[0].case_id} onChange={(e) => setCaseId(e.target.value)}>
                {list.map((c) => <option key={c.case_id} value={c.case_id}>{c.case_id}{c.status === 'not_run' ? ' (not verified)' : ''}</option>)}
              </select>
            </div>
            <div><button type="button" className="btn btn-primary" onClick={() => run('report')} disabled={busy === 'report'}><Icon name="print" size={16} />{busy === 'report' ? 'Writing…' : 'Write and open report'}</button></div>
            {report && <p className={`written ${report.ok ? 'match-yes' : 'match-no'}`} role="status">{report.ok ? <>Written to <span className="mono">{report.file}</span> · <a href={report.url} target="_blank" rel="noopener">open again</a></> : report.message}</p>}
          </section>
          <section className="panel" aria-labelledby="ex-c">
            <h2 id="ex-c">All findings and decisions (CSV)</h2>
            <p className="note">One row per finding of each case’s latest run, with its category, values, evidence, decision, note, reviewer and pipeline version. Cases not verified, or with no findings, get one row saying so.</p>
            <div><button type="button" className="btn" onClick={() => run('csv')} disabled={busy === 'csv'}><Icon name="export" size={16} />{busy === 'csv' ? 'Writing…' : 'Write and download CSV'}</button></div>
            {csv && <p className={`written ${csv.ok ? 'match-yes' : 'match-no'}`} role="status">{csv.ok ? <>Written to <span className="mono">{csv.file}</span> · <a href={csv.url}>download again</a></> : csv.message}</p>}
          </section>
        </div>
      )}
    </div>
  )
}
