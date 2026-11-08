import { useState } from 'react'
import { Loading, Segmented } from '../components/Bits.jsx'
import { rateValue } from '../lib/format.js'

// Split notes taken from docs/evaluation-spec.md §1 (dev) and from the API (held-out).
const SPLIT_NOTES = { dev: 'Used to build and debug the pipeline (evaluation-spec §1), so these numbers are expected to be optimistic.' }
const METHODS = ['resauce', 'baseline_a']
const FIELD_OPTIONS = [['combined', 'Both fields'], ['onset', 'Onset date'], ['max_grade', 'Maximum grade']]

const RATE_ROWS = [
  ['precision', 'Precision', 'detections ÷ (detections + false alerts)'],
  ['recall', 'Recall', 'detections ÷ positive fields'],
  ['f1', 'F1', '2·detections ÷ (2·detections + false alerts + misses)'],
  ['exact_agreement_all_fields', 'Exact agreement', 'category equals the reference, all in-scope fields'],
  ['exact_agreement_positive_fields', 'Exact agreement, positive fields', 'the same, positive fields only'],
]
const COUNT_ROWS = [
  ['positive', 'Positive fields', 'reference 7.1, 7.2, 7.3 or 7.8'],
  ['negative', 'Negative fields', 'reference 7.6 or 7.7'],
  ['review', 'Review fields', 'reference 7.4 or 7.5'],
  ['detections', 'Detections', 'an alert on a positive field'],
  ['misses', 'Misses', 'a positive field with no alert'],
  ['false_alerts', 'False alerts', 'an alert on a negative field'],
  ['alerts_on_review_fields', 'Alerts on review fields', 'counted as neither'],
  ['review_results', '“review: …” results', 'the method could not decide'],
]

export default function Overview({ summary }) {
  const [field, setField] = useState('combined')
  if (!summary) return <Loading label="Loading results" />
  const splits = summary.splits
  const title = summary.methods

  return (
    <div className="page overview">
      <section className="lede">
        <h1>Does the research record say what the clinical documents say?</h1>
        <div className="lede-text">
          <p>
            ReSauce reads the clinical notes behind a research record of ICANS after CAR-T therapy, extracts the
            neurological observations, each with its exact quoted source, and rebuilds the timeline from Day 0 to Day +28.
            It then compares the record’s onset date and maximum grade with what the documents show, and either flags
            the difference with its evidence or states plainly that a person must decide.
          </p>
          <p className="lede-actions">
            <a className="button button-primary" href="#/cases">Open a case and run it live</a>
            <a className="button" href="#/methods">How it is scored</a>
          </p>
        </div>
      </section>

      <aside className="disclosure" aria-label="Before reading these numbers">
        <p><strong>Synthetic data.</strong> All {splits.reduce((n, s) => n + s.case_count, 0)} cases shown are fictional. Results on synthetic data are not clinical validation.</p>
        <p><strong>Reference answers:</strong> {summary.reference_label}.</p>
        <p><strong>Baseline A</strong> is conventional validation on the same extracted observations: no event-time reconstruction, attribution, observation window or record history (evaluation-spec §4).</p>
      </aside>

      <section className="results" aria-labelledby="results-title">
        <div className="section-head">
          <h2 id="results-title">Measured results</h2>
          <Segmented label="Fields counted" options={FIELD_OPTIONS} value={field} onChange={setField} />
        </div>
        <p className="section-note">
          Each in-scope case has two fields, onset date and maximum grade. Splits are reported separately and never pooled.
          Every rate shows its counts.
        </p>

        <div className="table-scroll">
          <table className="collation">
            <thead>
              <tr>
                <th scope="col" rowSpan={2} className="measure-head">Measure</th>
                {splits.map((s, i) => (
                  <th key={s.name} scope="colgroup" colSpan={2} className="split-head">
                    <span className="split-name">{s.title}</span>
                    <span className="split-count">{s.case_count} cases</span>
                    <sup className="note-mark"><a href={`#note-${s.name}`} aria-label={`Note ${i + 1}`}>{i + 1}</a></sup>
                  </th>
                ))}
              </tr>
              <tr>
                {splits.flatMap((s) => METHODS.map((m) => (
                  <th key={s.name + m} scope="col" className={`method-head method-${m}`}>{title[m]}</th>
                )))}
              </tr>
            </thead>
            <tbody>
              <tr className="group-row"><th scope="rowgroup" colSpan={1 + splits.length * 2}>Rates</th></tr>
              {RATE_ROWS.map(([key, label, hint], rowIndex) => (
                <tr key={key}>
                  <th scope="row"><span className="row-label">{label}</span><span className="row-hint">{hint}</span></th>
                  {splits.flatMap((s) => METHODS.map((m) => {
                    const r = s.metrics?.[m]?.fields?.[field]?.[key]
                    return <RateCell key={s.name + m} r={r} method={m} delay={rowIndex} />
                  }))}
                </tr>
              ))}
              <tr className="group-row"><th scope="rowgroup" colSpan={1 + splits.length * 2}>Counts of fields</th></tr>
              {COUNT_ROWS.map(([key, label, hint]) => (
                <tr key={key}>
                  <th scope="row"><span className="row-label">{label}</span><span className="row-hint">{hint}</span></th>
                  {splits.flatMap((s) => METHODS.map((m) => (
                    <td key={s.name + m} className={`num method-${m}`}>{s.metrics?.[m]?.fields?.[field]?.counts?.[key] ?? '—'}</td>
                  )))}
                </tr>
              ))}
              <tr className="group-row"><th scope="rowgroup" colSpan={1 + splits.length * 2}>Whole cases</th></tr>
              <tr>
                <th scope="row"><span className="row-label">Out of scope, flagged</span><span className="row-hint">with the reference’s reason</span></th>
                {splits.flatMap((s) => METHODS.map((m) => {
                  const o = s.metrics?.[m]?.out_of_scope
                  return (
                    <td key={s.name + m} className={`num method-${m}`}>
                      {o ? <>{o.reason_matches} of {o.reference_cases}{o.in_scope_wrongly_flagged ? <span className="row-hint">{o.in_scope_wrongly_flagged} wrongly flagged</span> : null}</> : <span className="na">cannot flag</span>}
                    </td>
                  )
                }))}
              </tr>
              <tr>
                <th scope="row"><span className="row-label">Evidence-quote validity</span><span className="row-hint">quote equals the text at its offsets</span></th>
                {splits.flatMap((s) => METHODS.map((m) => {
                  const r = s.metrics?.[m]?.evidence_validity
                  return <td key={s.name + m} className={`num method-${m}`}>{rateValue(r)} <span className="counts">({r?.n}/{r?.d})</span></td>
                }))}
              </tr>
              <tr>
                <th scope="row"><span className="row-label">Cases with an error</span></th>
                {splits.flatMap((s) => METHODS.map((m) => (
                  <td key={s.name + m} className={`num method-${m}`}>{s.metrics?.[m]?.summary?.errors ?? '—'}</td>
                )))}
              </tr>
            </tbody>
          </table>
        </div>

        <ol className="notes">
          {splits.map((s) => (
            <li key={s.name} id={`note-${s.name}`}>
              <strong>{s.title}.</strong>{' '}
              {[SPLIT_NOTES[s.name], ...s.disclosures].filter(Boolean).join(' ')}{' '}
              {s.metrics?.resauce?.summary && <>In scope by the reference: {s.metrics.resauce.summary.in_scope} cases; out of scope: {s.metrics.resauce.summary.out_of_scope}.</>}
            </li>
          ))}
        </ol>
      </section>

      <MissFigure splits={splits} field={field} title={title} />

      <section className="provenance" aria-labelledby="prov-title">
        <h2 id="prov-title">Run record</h2>
        <div className="prov-grid">
          {splits.map((s) => <Provenance key={s.name} split={s} />)}
        </div>
      </section>
    </div>
  )
}

function RateCell({ r, method, delay }) {
  const value = r?.value
  return (
    <td className={`rate method-${method}`}>
      <span className="rate-value">{rateValue(r)}</span>
      <span className="counts">({r?.n}/{r?.d})</span>
      <span className="bar" aria-hidden="true">
        {value != null && <span className="bar-fill" style={{ '--w': value, '--i': delay }} />}
      </span>
    </td>
  )
}

// Figure: what happened to each positive field, and false alerts on negative fields.
function MissFigure({ splits, field, title }) {
  const parts = [
    ['detections', 'Detected'],
    ['misses_with_review_flag', 'Missed, review flag (7.4/7.5) instead'],
    ['misses_with_review_result', 'Missed, “review: …” result instead'],
    ['misses_from_out_of_scope', 'Missed, flagged out of scope'],
    ['misses_from_errors', 'Missed, method error'],
    ['misses_with_no_alert', 'Missed, no alert'],
  ]
  return (
    <section className="figure" aria-labelledby="fig1-title">
      <h2 id="fig1-title">Figure 1. Every positive field, and every false alert</h2>
      <p className="section-note">
        One square per field. Positive fields are those where the reference finds a discrepancy; a false alert is an alert on a field where the reference finds none.
      </p>
      <div className="fig-legend" aria-hidden="true">
        {parts.map(([key, label]) => <span key={key} className={`key key-${key}`}>{label}</span>)}
        <span className="key key-false">False alert</span>
      </div>
      <div className="fig-grid">
        {splits.map((s) => (
          <div key={s.name} className="fig-split">
            <h3>{s.title}</h3>
            {METHODS.map((m) => {
              const c = s.metrics?.[m]?.fields?.[field]?.counts
              if (!c) return null
              const squares = parts.flatMap(([key]) => Array.from({ length: c[key] || 0 }, () => key))
              const text = parts.filter(([key]) => c[key]).map(([key, label]) => `${label}: ${c[key]}`).join('; ')
              return (
                <div key={m} className={`fig-row method-${m}`}>
                  <span className="fig-method">{title[m]}</span>
                  <div className="squares" role="img" aria-label={`${title[m]}, ${c.positive} positive fields. ${text}. False alerts: ${c.false_alerts} of ${c.negative} negative fields.`}>
                    {squares.map((key, i) => <span key={i} className={`sq sq-${key}`} style={{ '--i': i }} />)}
                    <span className="sq-gap" />
                    {Array.from({ length: c.false_alerts }, (_, i) => <span key={`f${i}`} className="sq sq-false" style={{ '--i': squares.length + i }} />)}
                  </div>
                  <span className="fig-count">{c.detections}/{c.positive} detected · {c.false_alerts} false</span>
                </div>
              )
            })}
          </div>
        ))}
      </div>
    </section>
  )
}

function Provenance({ split }) {
  const md = split.metadata || {}
  const rt = split.runtime_seconds || {}
  return (
    <dl className="prov">
      <div className="prov-title">{split.title}</div>
      <dt>Results file</dt><dd className="mono">{split.results_file}</dd>
      <dt>Dataset</dt><dd className="mono">{md.dataset_id} v{md.dataset_version}</dd>
      <dt>Code commit</dt><dd className="mono">{md.code_commit?.slice(0, 7)}{md.uncommitted_changes_in_code_or_data ? ' (uncommitted changes: yes)' : ''}</dd>
      <dt>Reference commit</dt><dd className="mono">{md.reference_answer_commit?.slice(0, 7)}</dd>
      <dt>Run date</dt><dd className="mono">{md.date}</dd>
      <dt>Python</dt><dd className="mono">{md.python_version}</dd>
      <dt>Run time, summed</dt>
      <dd className="mono">extraction {rt.extract?.toFixed(3)} s · ReSauce rules {rt.resauce?.toFixed(3)} s · Baseline A {rt.baseline_a?.toFixed(3)} s</dd>
    </dl>
  )
}
