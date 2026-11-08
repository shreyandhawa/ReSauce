import { useCallback, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { api } from '../api.js'
import { EvidenceList, Loading, Problem, Sign, StatusSign, findingSign } from '../components/Bits.jsx'
import DocumentReader, { observationLabel } from '../components/DocumentReader.jsx'
import Icon from '../components/Icon.jsx'
import Timeline from '../components/Timeline.jsx'
import { CATEGORY_NAMES, FIELDS, FIELD_NAMES, code, days, ms, signedDay, valueText } from '../lib/format.js'
import { useLoad } from '../lib/hooks.js'
import { animate, duration, takeOrigin } from '../lib/motion.js'

// Each stage lights when its own result arrives. The rules engine returns the comparison and
// the verdict from one call, so they are one stage here.
const STAGES = [
  ['extraction', 'Extraction', 'extraction'],
  ['timeline', 'Timeline', 'timeline'],
  ['verdict', 'Comparison and verdict', 'verdict'],
]

export default function CaseWorkspace({ caseId, onChanged }) {
  const detail = useLoad(() => api.caseDetail(caseId), [caseId])
  const [live, setLive] = useState(null) // the run in progress or just finished on this screen
  const [baseline, setBaseline] = useState(false)
  const [activeDoc, setActiveDoc] = useState(null)
  const [focus, setFocus] = useState(null)
  const [hot, setHot] = useState(null)
  const [revealing, setRevealing] = useState(false)
  const rootRef = useRef(null)
  const token = useRef(0)

  // Orient: the case opens out of the row that was clicked (a clip that grows to the full view).
  // The click position is taken at once; the expansion runs when the case has loaded and is drawn.
  const origin = useRef(takeOrigin())
  const ready = Boolean(detail.data && !detail.data.invalid)
  useLayoutEffect(() => {
    const from = origin.current
    const el = rootRef.current
    if (!ready || !from || !el) return
    origin.current = null
    const r = el.getBoundingClientRect()
    const inset = `inset(${Math.max(0, from.top - r.top)}px ${Math.max(0, r.right - from.left - from.width)}px ${Math.max(0, r.bottom - from.top - from.height)}px ${Math.max(0, from.left - r.left)}px round 8px)`
    animate(el, [{ clipPath: inset, opacity: 0.6 }, { clipPath: 'inset(0 0 0 0 round 0px)', opacity: 1 }], { dur: 'layout', ease: 'out', fill: 'none' })
  }, [ready])

  const cite = useCallback((ev) => {
    const versionId = `${ev.document_id}.v${ev.version}`
    token.current += 1
    setActiveDoc(versionId)
    setFocus({ version_id: versionId, start: ev.start, end: ev.end, token: token.current })
  }, [])

  const verify = async () => {
    setLive({ status: 'running', stages: {}, observations: [], timeline: null })
    setFocus(null)
    setRevealing(true)
    try {
      await api.verify(caseId, baseline, (e) => {
        if (e.event === 'stage') {
          setLive((l) => {
            const next = { ...l, stages: { ...l.stages, [e.stage]: e } }
            if (e.stage === 'extraction') next.observations = e.observations
            if (e.stage === 'timeline') next.timeline = e
            if (e.stage === 'error') next.error = e
            return next
          })
        } else if (e.event === 'done') {
          setLive((l) => ({ ...l, status: 'done', run: e.run, findings: e.findings, caseStatus: e.status }))
          onChanged?.()
        }
      })
    } catch (error) {
      setLive((l) => ({ ...l, status: 'failed', failure: error }))
    }
    // The entrance classes are removed once the marks have entered, so switching tabs later does not replay them.
    setTimeout(() => setRevealing(false), duration('slow') + 16 * duration('stagger') + 50)
  }

  const d = detail.data
  const run = live?.run ?? (live ? null : d?.run)
  const items = live?.findings ?? (live ? [] : d?.findings || [])
  const observations = live && !live.run ? live.observations : run?.observations || []
  const timeline = live && !live.run ? live.timeline : run?.timeline
  const output = run?.resauce?.output

  const marks = useMemo(() => {
    const list = observations.map((o) => ({
      key: `o${o.id}`, kind: 'obs', obsId: o.id, status: o.status,
      version_id: `${o.evidence.document_id}.v${o.evidence.version}`, start: o.evidence.start, end: o.evidence.end, label: observationLabel(o),
    }))
    for (const f of items) {
      for (const ev of f.evidence) {
        if (ev.start == null || !String(ev.document_id).includes('-D')) continue
        list.push({ key: `c${f.finding_id}${ev.document_id}${ev.start}`, kind: 'cite', version_id: `${ev.document_id}.v${ev.version}`, start: ev.start, end: ev.end, label: ev.role })
      }
    }
    return list
  }, [observations, items])

  if (detail.error) return <div className="page"><Problem title={`${caseId} could not be opened`} error={detail.error} /></div>
  if (!d) return <div className="page"><Loading label={`Opening ${caseId}`} /></div>
  if (d.invalid) {
    return (
      <div className="page">
        <div className="page-head"><h1 className="mono">{caseId}</h1></div>
        <div className="callout callout-alert"><p><strong>This case folder does not pass the data-format check, so it cannot be verified.</strong></p>
          <ul className="prose" style={{ marginTop: 8 }}>{d.problems.map((p, i) => <li key={i}><span className="mono">{p.source.split('/').slice(-2).join('/')}</span> · {p.field}: {p.message}</li>)}</ul></div>
      </div>
    )
  }

  const record = d.record.versions[d.record.versions.length - 1]
  const docs = d.documents
  const current = docs.find((x) => x.version_id === activeDoc) ? activeDoc : docs[0]?.version_id
  const running = live?.status === 'running'
  const pickObservation = (id) => { const o = observations.find((x) => x.id === id); if (o) cite(o.evidence) }
  const stageState = (event) => {
    const seen = live && !live.run ? live.stages : null
    if (seen) return seen[event] ? 'done' : seen.error?.stage === event ? 'error' : 'idle'
    if (run?.error?.stage === event) return 'error'
    return run?.timings_seconds?.[event] != null ? 'done' : 'idle'
  }
  const stageMs = (event) => live?.stages?.[event]?.seconds ?? run?.timings_seconds?.[event]
  const status = live?.caseStatus || (run ? statusOf(run, items) : 'not_run')
  const alerts = items.filter((i) => !i.decision && i.tier === 0).length

  return (
    <div className="ws" ref={rootRef}>
      <header className="ws-head">
        <div>
          <p className="crumb"><a href="#/cases">Cases</a></p>
          <h1>{d.case_id}</h1>
        </div>
        <div className="ws-facts">
          <StatusSign status={status} alerts={alerts} />
          <p className="facts">Age at infusion {d.facts.age_at_infusion} · infusion (Day 0) <span className="mono">{d.facts.infusion_date}</span> · {new Set(docs.map((x) => x.document_id)).size} documents, {docs.length} versions</p>
        </div>
        <div className="actions">
          <label className="check"><input type="checkbox" checked={baseline} onChange={(e) => setBaseline(e.target.checked)} /> Compare with simple baseline</label>
          <button type="button" className="btn btn-primary" onClick={verify} disabled={running}>
            <Icon name="play" size={16} />{running ? 'Verifying…' : run ? 'Verify again' : 'Verify'}
          </button>
        </div>
      </header>

      <div className="stages" aria-label="Pipeline stages" role="status">
        {[...STAGES, ...(baseline || run?.baseline_a ? [['baseline', 'Baseline A', 'baseline']] : [])].map(([key, label, event]) => (
          <span key={key} className="stage" data-state={stageState(event)}>
            <span className="dot" aria-hidden="true" />{label}
            {stageState(event) === 'done' && stageMs(event) != null && <span className="ms">{ms(stageMs(event))}</span>}
          </span>
        ))}
        <span className="stage-note">{run ? 'Measured run times' : running ? 'Running the frozen pipeline…' : 'Not verified yet'}</span>
      </div>

      <div className="ws-body">
        <DocumentReader documents={docs} activeId={current} onSelect={(id) => { setActiveDoc(id); setFocus(null) }}
          marks={marks} focus={focus} hot={hot} onHover={setHot} onMarkPick={pickObservation} revealing={revealing} />

        <div className="side">
          <section aria-labelledby="rec-h">
            <h2 id="rec-h">Research record · v{record.version}{d.record.versions.length > 1 ? ` of ${d.record.versions.length}` : ''}</h2>
            <div className="record-grid">
              <div>Onset<span className="big mono">{record.onset_date || (record.icans_reported ? 'empty' : 'no ICANS reported')}</span>{record.onset_day != null && <span className="muted">{signedDay(record.onset_day)}</span>}</div>
              <div>Maximum grade<span className="big">{record.max_grade != null ? `Grade ${record.max_grade}` : record.icans_reported ? 'empty' : 'no ICANS reported'}</span></div>
            </div>
            {d.record.versions.length > 1 && (
              <div className="record-hist">
                {d.record.versions.map((v) => (
                  <span key={v.version}>v{v.version} · <span className="mono">{v.recorded_at.replace('T', ' ')}</span> · {v.icans_reported ? `onset ${v.onset_date || 'empty'}, grade ${v.max_grade ?? 'empty'}` : 'no ICANS'}{v.change_reason ? ` · reason: ${v.change_reason}` : ''}</span>
                ))}
              </div>
            )}
          </section>

          {(timeline || run) && (
            <section aria-labelledby="tl-h">
              <h2 id="tl-h">Timeline · {signedDay((timeline || run.timeline).window.start_day)} to {signedDay((timeline || run.timeline).window.end_day)}</h2>
              <Timeline observations={observations} use={(timeline || run.timeline)?.use} window={(timeline || run.timeline).window}
                recordOnsetDay={record.onset_day} documentedOnset={output && !output.out_of_scope ? output.fields.onset.documented_value : null}
                hot={hot} onHover={setHot} onPick={(o) => cite(o.evidence)} revealing={revealing} />
            </section>
          )}

          {live?.failure && <Problem title="The run could not be completed" error={live.failure} />}
          {run?.error && <Problem title={`The pipeline stopped at ${run.error.stage}`} error={run.error.error} />}
          {run?.resauce?.error && <Problem title="The rules engine failed on this case" error={run.resauce.error} />}

          {!run && !running && !live?.failure && (
            <p className="note">Press <strong>Verify</strong> to run the frozen pipeline on this case folder. Observations are marked in the text as extraction finishes, events drop onto the timeline, then the record is compared field by field.</p>
          )}

          {output && <Findings output={output} items={items} record={record} onCite={cite} animate={revealing} caseId={d.case_id} />}

          {run?.baseline_a && output && <BaselineCompare run={run} />}
          {run && <RunFacts run={run} storedAvailable={d.stored_available} />}
        </div>
      </div>
    </div>
  )
}

function statusOf(run, items) {
  if (run.error || run.resauce?.error) return 'error'
  if (!items.length) return 'no_findings'
  return items.some((i) => !i.decision) ? 'to_review' : 'reviewed'
}

function fieldLabel(name, field, items) {
  const f = items.find((i) => i.finding_id === name)
  if (f) return f.label
  const c = code(field.category)
  return c ? `${CATEGORY_NAMES[c]} (${c})` : field.category
}

function recordText(name, value, record) {
  if (value == null) return record.icans_reported ? 'empty' : 'no ICANS reported'
  if (name === 'max_grade') return `Grade ${value}`
  return `${value}${record.onset_day != null ? ` · ${signedDay(record.onset_day)}` : ''}`
}

function Findings({ output, items, record, onCite, animate: reveal, caseId }) {
  const open = items.filter((i) => !i.decision).length
  const rest = items.filter((i) => i.kind !== 'field')
  let i = 0
  return (
    <section aria-labelledby="find-h">
      <h2 id="find-h">Findings · {items.length} ({open} open)</h2>
      {output.out_of_scope ? null : FIELDS.map((name) => {
        const field = output.fields[name]
        const finding = items.find((x) => x.finding_id === name)
        const kind = finding ? findingSign(finding) : 'clear'
        return (
          <article key={name} className={`plate${kind === 'alert' ? ' plate-alert' : ''}${reveal ? ' reveal-in' : ''}`} style={{ '--i': i++ }}>
            <div className="plate-head">
              <span className="plate-field">{FIELD_NAMES[name]}</span>
              {finding && <DecisionTag decision={finding.decision} />}
            </div>
            <Sign kind={kind}>{fieldLabel(name, field, items)}</Sign>
            <div className="vals">
              <span>Record<b className="mono">{recordText(name, field.record_value, record)}</b></span>
              <span>Documented<b className="mono">{valueText(field.documented_value)}</b></span>
              {field.signed_difference_days != null && <span>Difference<b>{days(field.signed_difference_days)}</b></span>}
            </div>
            {field.difference_note && <p className="detail">{field.difference_note}</p>}
            {field.documented_value?.undetermined && <p className="detail">{field.documented_value.undetermined}</p>}
            {field.readings?.length > 0 && (
              <ol className="detail" style={{ paddingLeft: '1.1rem' }}>
                {field.readings.map((r, k) => <li key={k}>{r.category}: {r.reading}</li>)}
              </ol>
            )}
            {field.record_history && <p className="detail">Record history (§7.6): {field.record_history.explanation}</p>}
            <EvidenceList evidence={field.evidence} onCite={onCite} />
          </article>
        )
      })}
      {rest.map((f) => (
        <article key={f.finding_id} className={`plate${reveal ? ' reveal-in' : ''}`} style={{ '--i': i++ }}>
          <div className="plate-head">
            <Sign kind={findingSign(f)}>{f.label}{f.field ? ` · ${FIELD_NAMES[f.field] || f.field}` : ''}</Sign>
            <DecisionTag decision={f.decision} />
          </div>
          {f.detail && <p className="detail">{f.detail}{f.rule ? ` (${f.rule})` : ''}</p>}
          <EvidenceList evidence={f.evidence} onCite={onCite} />
        </article>
      ))}
      {output.case_flags && <CaseFlags flags={output.case_flags} onCite={onCite} />}
      {open > 0 && <p style={{ marginTop: 12 }}><a className="btn" href={`#/queue?case=${encodeURIComponent(caseId)}`}>Review {open} open finding{open === 1 ? '' : 's'}</a></p>}
    </section>
  )
}

function DecisionTag({ decision }) {
  if (!decision) return <span className="decision-tag open">Open</span>
  return <span className="decision-tag" title={`${decision.reviewer}, ${decision.time}: ${decision.note}`}>{decision.label} · {decision.reviewer}</span>
}

function CaseFlags({ flags, onCite }) {
  const days = flags.unassessed_period?.days_without_gradeable_assessment || []
  const periods = flags.unassessed_period?.not_assessable_periods || []
  const ungradeable = flags.ungradeable_neurological_symptom || []
  return (
    <details className="disclose" style={{ marginTop: 12 }}>
      <summary><Icon name="chevron" size={14} />Case-level information (§7.10)</summary>
      <div className="disclose-body more-list">
        <p className="detail">Days in the window with no gradeable assessment: {days.length ? <span className="mono">{days.join(', ')}</span> : 'none'}. This list is long by design: each synthetic case holds only a few documents.</p>
        {periods.map((p, k) => <div key={k}><p className="detail">Documented “not assessable” period</p><EvidenceList evidence={p.evidence || (p.quote ? [p] : [])} onCite={onCite} /></div>)}
        {ungradeable.map((u, k) => <div key={k}><p className="detail">Ungradeable neurological symptom</p><EvidenceList evidence={u.evidence || (u.quote ? [u] : [])} onCite={onCite} /></div>)}
      </div>
    </details>
  )
}

function BaselineCompare({ run }) {
  const a = run.baseline_a
  const r = run.resauce.output
  return (
    <section aria-labelledby="ba-h">
      <h2 id="ba-h">Compared with Baseline A</h2>
      {a.error ? <p className="detail">Baseline A failed on this case: {a.error}</p> : (
        <table className="data">
          <thead><tr><th>Field</th><th>ReSauce</th><th>Baseline A</th></tr></thead>
          <tbody>
            {FIELDS.map((n) => (
              <tr key={n}><td>{FIELD_NAMES[n]}</td><td className="mono">{r.out_of_scope ? 'out of scope' : r.fields[n].category}</td><td className="mono">{a.output.fields[n].category}</td></tr>
            ))}
          </tbody>
        </table>
      )}
      <p className="note" style={{ marginTop: 6 }}>Baseline A: the same observations, the latest document versions, dated by documentation time; no attribution, window or record history (evaluation-spec §4). It cannot flag out of scope.</p>
    </section>
  )
}

function RunFacts({ run, storedAvailable }) {
  const p = run.pipeline
  const m = run.stored_comparison?.matches
  return (
    <section aria-labelledby="run-h">
      <h2 id="run-h">This run</h2>
      <dl className="facts-list">
        <dt>Run</dt><dd className="mono">{run.run_id}</dd>
        <dt>Started</dt><dd className="mono">{run.started_at}</dd>
        <dt>Pipeline</dt><dd><span className="mono">{p.tag}</span> · commit <span className="mono">{(p.tag_commit || 'unknown').slice(0, 7)}</span></dd>
        <dt>Frozen files</dt><dd className={p.frozen_files_match ? 'match-yes' : 'match-no'}>{p.frozen_files_match ? 'match docs/freeze.md' : 'DIFFER from docs/freeze.md'}</dd>
      </dl>
      <div style={{ marginTop: 10, display: 'grid', gap: 4 }}>
        {run.stored_comparison ? Object.entries(m || {}).map(([method, same]) => (
          <p key={method} className={`match ${same === true ? 'match-yes' : same === false ? 'match-no' : 'match-none'}`}>
            <Icon name={same === true ? 'clear' : same === false ? 'error' : 'notrun'} size={16} />
            <span>{method === 'resauce' ? 'ReSauce' : 'Baseline A'}: live output {same === true ? 'matches' : same === false ? 'differs from' : 'cannot be compared with'} the stored evaluation run (<span className="mono">{run.stored_comparison.results_file}</span>)</span>
          </p>
        )) : (
          <p className="match match-none"><Icon name="notrun" size={16} /><span>{storedAvailable === false ? 'No stored evaluation result for this exact case folder (a new or changed case), so there is nothing to compare with.' : 'Not compared with a stored run.'}</span></p>
        )}
      </div>
    </section>
  )
}
