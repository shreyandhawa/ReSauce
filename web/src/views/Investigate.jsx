import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../api.js'
import { CategoryTag, Loading, Problem } from '../components/Bits.jsx'
import DocumentReader, { observationLabel } from '../components/DocumentReader.jsx'
import Timeline from '../components/Timeline.jsx'
import Verdict from '../components/Verdict.jsx'
import { FIELDS, FIELD_NAMES, OBS_KINDS, TIME_SOURCES, citation, days, ms, signedDay, valueText } from '../lib/format.js'
import { useLoad, useReducedMotion } from '../lib/hooks.js'

const STAGES = [
  ['extraction', 'Extraction'],
  ['timeline', 'Timeline'],
  ['comparison', 'Comparison'],
  ['verdict', 'Verdict'],
  ['contrast', 'Baseline A and reference'],
]
const STAGE_PACE_MS = 1700 // reveal pacing for the audience; not processing time

export default function Investigate({ caseId, summary }) {
  const detail = useLoad(() => api.caseDetail(caseId), [caseId])
  const [run, setRun] = useState({ status: 'idle' })
  const [stage, setStage] = useState(0) // 0 = not run; 1..5 = stages revealed
  const [auto, setAuto] = useState(false)
  const [activeDoc, setActiveDoc] = useState(null)
  const [focus, setFocus] = useState(null)
  const reduced = useReducedMotion()
  const focusToken = useRef(0)
  const pipelineRef = useRef(null)

  // Keep the revealed stage in view (the document reader beside it stays in place).
  useEffect(() => {
    if (stage > 0 && pipelineRef.current) pipelineRef.current.scrollIntoView({ block: 'start', behavior: reduced ? 'auto' : 'smooth' })
  }, [stage, reduced])

  useEffect(() => {
    if (!auto || stage === 0 || stage >= STAGES.length) return
    const t = setTimeout(() => setStage((s) => s + 1), STAGE_PACE_MS)
    return () => clearTimeout(t)
  }, [auto, stage])

  const start = async () => {
    setRun({ status: 'running' })
    setStage(0)
    setFocus(null)
    try {
      const data = await api.run(caseId)
      setRun({ status: 'done', data })
      setStage(reduced ? STAGES.length : 1)
      setAuto(!reduced)
    } catch (error) {
      setRun({ status: 'error', error })
    }
  }

  const docs = detail.data?.documents || []
  const current = docs.find((d) => d.version_id === activeDoc) ? activeDoc : docs[0]?.version_id

  const cite = useCallback((ev) => {
    const versionId = `${ev.document_id}.v${ev.version}`
    focusToken.current += 1
    setActiveDoc(versionId)
    setFocus({ version_id: versionId, start: ev.start, end: ev.end, token: focusToken.current })
  }, [])

  const result = run.data
  const marks = useMemo(() => {
    if (!result || stage < 1) return []
    const list = result.observations.map((o) => ({
      key: `o${o.id}`, kind: 'obs', obsId: o.id, status: o.status,
      version_id: `${o.evidence.document_id}.v${o.evidence.version}`, start: o.evidence.start, end: o.evidence.end,
      label: observationLabel(o),
    }))
    if (stage >= 4 && result.resauce?.output) {
      for (const ev of collectEvidence(result.resauce.output)) {
        if (ev.start == null) continue
        list.push({ key: `c${ev.document_id}${ev.start}`, kind: 'cite', version_id: `${ev.document_id}.v${ev.version}`, start: ev.start, end: ev.end, label: ev.role })
      }
    }
    return list
  }, [result, stage])

  if (detail.error) return <Problem title={`Case ${caseId} could not be loaded`} error={detail.error} />
  if (detail.loading || !detail.data) return <Loading label={`Loading ${caseId}`} />
  const d = detail.data
  const record = d.record.versions[d.record.versions.length - 1]
  const pickObservation = (id) => {
    const o = result?.observations.find((x) => x.id === id)
    if (o) cite(o.evidence)
  }

  return (
    <div className="page investigate">
      <header className="case-head">
        <div>
          <p className="case-crumb"><a href="#/cases">Cases</a> / <span className="mono">{d.split_title}</span></p>
          <h1 className="mono case-id">{d.case_id}</h1>
          <p className="case-facts">
            Age at infusion {d.facts.age_at_infusion} · infusion (Day 0) {d.facts.infusion_date} · observation window {signedDay(d.window.start_day)} to {signedDay(d.window.end_day)} · {docs.length} document versions
          </p>
          <p className="fictional">{d.fictional_notice}</p>
        </div>
        <div className="run-box">
          <button type="button" className="button button-primary run-button" onClick={start} disabled={run.status === 'running'}>
            {run.status === 'running' ? 'Running…' : run.status === 'done' ? 'Run ReSauce again' : 'Run ReSauce'}
          </button>
          <p className="run-note">Runs the frozen pipeline live on this case folder.</p>
        </div>
      </header>

      <div className="workbench">
        <DocumentReader
          documents={docs}
          activeId={current}
          onSelect={(id) => { setActiveDoc(id); setFocus(null) }}
          marks={marks}
          focus={focus}
          onMarkPick={pickObservation}
          sweep={stage >= 1 && !reduced}
        />

        <div className="side">
          <RecordPanel record={d.record} />

          {run.status === 'error' && <Problem title="The live run failed" error={run.error} />}
          {run.status === 'idle' && (
            <p className="side-hint">
              Read the documents and the record, then press <strong>Run ReSauce</strong>. The result is revealed stage by stage:
              extraction, timeline, comparison, verdict, then Baseline A and the reference answer.
            </p>
          )}
          {result?.error && <Problem title="The pipeline stopped with an error" error={result.error} />}

          {result && !result.error && stage > 0 && (
            <section className="pipeline" aria-label="Pipeline result">
              <RunFacts result={result} />
              <ol className="stages" aria-label="Stages" ref={pipelineRef}>
                {STAGES.map(([key, label], i) => (
                  <li key={key}>
                    <button
                      type="button"
                      className="stage-tab"
                      aria-current={stage === i + 1 ? 'step' : undefined}
                      data-done={stage > i + 1 || undefined}
                      onClick={() => { setAuto(false); setStage(i + 1) }}
                    >
                      <span className="stage-n">{i + 1}</span>{label}
                    </button>
                  </li>
                ))}
              </ol>
              <div className="stage-controls">
                {auto && stage < STAGES.length ? (
                  <button type="button" className="button" onClick={() => setAuto(false)}>Pause</button>
                ) : stage < STAGES.length ? (
                  <button type="button" className="button" onClick={() => setStage(stage + 1)}>Next: {STAGES[stage][1]}</button>
                ) : null}
                {stage < STAGES.length && <button type="button" className="button button-quiet" onClick={() => { setAuto(false); setStage(STAGES.length) }}>Show all</button>}
              </div>

              <div className="stage-panel" key={stage}>
                {stage === 1 && <Extraction observations={result.observations} onCite={cite} />}
                {stage === 2 && (
                  <>
                  <h3 className="stage-title">Event time against documentation time</h3>
                  <p className="stage-note">Each observation sits where it happened; the hairline runs to when the note was written. Select a mark to open its quote.</p>
                  <Timeline
                    observations={result.observations}
                    window={d.window}
                    recordOnsetDay={record.onset_day}
                    documentedOnset={result.resauce?.output?.out_of_scope ? null : result.resauce?.output?.fields?.onset?.documented_value}
                    onPick={(o) => cite(o.evidence)}
                  />
                  </>
                )}
                {stage === 3 && <Comparison output={result.resauce?.output} record={record} />}
                {stage === 4 && (
                  <>
                    <h3 className="stage-title">ReSauce verdict</h3>
                    <Verdict output={result.resauce?.output || result.resauce} onCite={cite} recordValues={record} />
                  </>
                )}
                {stage === 5 && <Contrast result={result} reference={d.reference} referenceLabel={d.reference_label} onCite={cite} record={record} summary={summary} />}
              </div>
            </section>
          )}
        </div>
      </div>
    </div>
  )
}

function collectEvidence(node, out = []) {
  if (Array.isArray(node)) node.forEach((n) => collectEvidence(n, out))
  else if (node && typeof node === 'object') {
    for (const [k, v] of Object.entries(node)) {
      if (k === 'evidence' && Array.isArray(v)) out.push(...v)
      else collectEvidence(v, out)
    }
  }
  return out
}

function RecordPanel({ record }) {
  return (
    <section className="record" aria-labelledby="record-title">
      <h2 id="record-title">Research record <span className="mono muted">{record.record_id}</span></h2>
      <table className="record-table">
        <thead>
          <tr><th scope="col">Version</th><th scope="col">Recorded</th><th scope="col">ICANS</th><th scope="col">Onset</th><th scope="col">Max grade</th></tr>
        </thead>
        <tbody>
          {record.versions.map((v, i) => (
            <tr key={v.version} className={i === record.versions.length - 1 ? 'current' : 'superseded'}>
              <td className="mono">v{v.version}{i === record.versions.length - 1 ? ' (current)' : ''}</td>
              <td className="mono">{v.recorded_at.replace('T', ' ')}</td>
              <td>{v.icans_reported ? 'reported' : 'not reported'}</td>
              <td className="mono">{v.onset_date ? <>{v.onset_date} <span className="muted">{signedDay(v.onset_day)}</span></> : 'empty'}</td>
              <td className="mono">{v.max_grade != null ? `Grade ${v.max_grade}` : 'empty'}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {record.versions.filter((v) => v.change_reason).map((v) => (
        <p key={v.version} className="fv-note">v{v.version} change reason: {v.change_reason}</p>
      ))}
    </section>
  )
}

function RunFacts({ result }) {
  const t = result.timings_seconds
  const match = result.matches_stored
  const total = Object.values(t).reduce((a, b) => a + b, 0)
  return (
    <div className="run-facts" role="status">
      <p className="run-time">
        <strong>Measured on this run: {ms(total)}</strong>
        <span className="mono"> load {ms(t.load)} · extraction {ms(t.extract)} · ReSauce rules {ms(t.resauce)} · Baseline A {ms(t.baseline_a)}</span>
      </p>
      <p className="run-pace">The stage-by-stage reveal below is paced for reading; it is not processing time.</p>
      <ul className="match">
        {[['resauce', 'ReSauce'], ['baseline_a', 'Baseline A']].map(([m, label]) => (
          <li key={m} className={match?.[m] === true ? 'match-yes' : match?.[m] === false ? 'match-no' : 'match-none'}>
            {match?.[m] === true && <>{label}: live output matches the stored evaluation run <span className="mono">({result.stored_results_file})</span></>}
            {match?.[m] === false && <>{label}: live output <strong>differs</strong> from the stored evaluation run <span className="mono">({result.stored_results_file})</span></>}
            {match?.[m] == null && <>{label}: no stored output to compare with</>}
          </li>
        ))}
      </ul>
    </div>
  )
}

function Extraction({ observations, onCite }) {
  const byKind = new Map()
  for (const o of observations) {
    if (!byKind.has(o.kind)) byKind.set(o.kind, [])
    byKind.get(o.kind).push(o)
  }
  return (
    <div>
      <h3 className="stage-title">{observations.length} observations extracted</h3>
      <p className="stage-note">Each is highlighted in its document at its exact offsets. Select one to jump to it.</p>
      {[...byKind].map(([kind, list]) => (
        <div key={kind} className="obs-group">
          <h4>{OBS_KINDS[kind] || kind} <span className="muted">{list.length}</span></h4>
          <ul className="obs-list">
            {list.map((o) => (
              <li key={o.id}>
                <button type="button" className={`obs obs-${o.status}`} onClick={() => onCite(o.evidence)}>
                  <span className="obs-value">{o.value == null ? '—' : typeof o.value === 'object' ? JSON.stringify(o.value) : String(o.value)}</span>
                  <span className="obs-status">{o.status}</span>
                  <span className="obs-time mono">{o.event_date ? `${signedDay(o.event_day)}${o.event_time ? ' ' + o.event_time : ''}` : 'time unresolved'} · {TIME_SOURCES[o.time_source]}</span>
                  <span className="obs-cite mono">{citation(o.evidence)}</span>
                  <q className="obs-quote">{o.evidence.quote}</q>
                </button>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  )
}

function Comparison({ output, record }) {
  if (!output) return null
  if (output.out_of_scope) {
    return (
      <div>
        <h3 className="stage-title">No comparison: the case is out of scope</h3>
        <p className="stage-note">Reason: <strong>{output.out_of_scope.reason}</strong> ({output.out_of_scope.source}). Out-of-scope cases get no discrepancy category (clinical-methods §5).</p>
      </div>
    )
  }
  return (
    <div>
      <h3 className="stage-title">Record against documents</h3>
      <p className="stage-note">The current record version against the values ReSauce derived from the documents.</p>
      <table className="compare">
        <thead>
          <tr><th scope="col">Field</th><th scope="col">Research record (v{record.version})</th><th scope="col">Documents</th><th scope="col">Difference</th></tr>
        </thead>
        <tbody>
          {FIELDS.map((name) => {
            const f = output.fields[name]
            const recordValue = f.record_value == null ? (record.icans_reported ? 'empty' : 'no ICANS reported')
              : name === 'max_grade' ? `Grade ${f.record_value}` : `${f.record_value} · ${signedDay(record.onset_day)}`
            return (
              <tr key={name}>
                <th scope="row">{FIELD_NAMES[name]}</th>
                <td className="mono">{recordValue}</td>
                <td className="mono">{valueText(f.documented_value)}</td>
                <td>{f.signed_difference_days != null ? <span className="mono">{days(f.signed_difference_days)}</span> : f.difference_note || '—'}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

function Contrast({ result, reference, referenceLabel, onCite, record, summary }) {
  const methods = summary?.methods || { resauce: 'ReSauce', baseline_a: 'Baseline A' }
  const columns = [
    ['resauce', methods.resauce, result.resauce?.output],
    ['baseline_a', methods.baseline_a, result.baseline_a?.output],
    ['reference', 'Reference answer', reference],
  ]
  const categoryOf = (out, name) => {
    if (!out) return null
    if (out.out_of_scope) return `out of scope (${out.out_of_scope.reason})`
    return out.fields?.[name]?.category
  }
  return (
    <div>
      <h3 className="stage-title">Against Baseline A and the reference</h3>
      <table className="compare contrast">
        <thead>
          <tr><th scope="col">Field</th>{columns.map(([k, label]) => <th key={k} scope="col">{label}</th>)}</tr>
        </thead>
        <tbody>
          {FIELDS.map((name) => {
            const ref = categoryOf(reference, name)
            return (
              <tr key={name}>
                <th scope="row">{FIELD_NAMES[name]}</th>
                {columns.map(([k, , out]) => (
                  <td key={k}>
                    <CategoryTag category={categoryOf(out, name)} against={k === 'reference' ? undefined : ref} />
                    {out?.fields?.[name] && !out.out_of_scope && <span className="contrast-value mono">{valueText(out.fields[name].documented_value)}</span>}
                  </td>
                ))}
              </tr>
            )
          })}
        </tbody>
      </table>

      <details className="more">
        <summary>Baseline A in detail</summary>
        <p className="stage-note">Conventional validation on the same observations: latest document versions, dated by documentation time, no attribution, window or record history (evaluation-spec §4). It cannot flag out of scope or give a review flag.</p>
        <Verdict output={result.baseline_a?.output || result.baseline_a} onCite={onCite} recordValues={record} />
      </details>

      {reference ? (
        <details className="more" open>
          <summary>Reference answer in detail</summary>
          <p className="stage-note">{referenceLabel}. Display only; ReSauce never reads it.</p>
          {reference.scenario_label && <p className="fv-line">Case scenario (from the reference answer): {reference.scenario_label}</p>}
          <Verdict output={reference} onCite={onCite} recordValues={record} />
          {reference.ambiguity_notes?.length > 0 && (
            <div className="flag-group">
              <h4>Notes in the reference answer</h4>
              <ul>{reference.ambiguity_notes.map((n, i) => <li key={i}><p>{n}</p></li>)}</ul>
            </div>
          )}
        </details>
      ) : (
        <p className="stage-note">No reference answer is available for this case.</p>
      )}
    </div>
  )
}

