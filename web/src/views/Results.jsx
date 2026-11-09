import { api } from '../api.js'
import { Loading, Problem } from '../components/Bits.jsx'
import Icon from '../components/Icon.jsx'
import { useLoad } from '../lib/hooks.js'

// Only the headline percentages, from the stored evaluation runs (results/*.json via /api/summary).
// Each value is the stored rate × 100, rounded to a whole percent; the exact fractions are one
// click away. The caveats are required with every result (CLAUDE.md), so each split keeps one line.
const MEASURES = [
  ['precision', 'Precision', 'Of the alerts raised, the share that the reference answers also mark as discrepancies.', 'detections ÷ (detections + false alerts)'],
  ['recall', 'Recall', 'Of the discrepancies in the reference answers, the share that were caught.', 'detections ÷ positive fields'],
  ['exact_agreement_all_fields', 'Exact agreement', 'Fields whose category matched the reference answer exactly.', 'category equals the reference, all in-scope fields'],
]
const METHODS = ['resauce', 'baseline_a']
const SPLIT_LINES = {
  dev: 'Used to build the pipeline, so expected to be optimistic.',
}

const pct = (r) => (r && r.value != null ? `${Math.round(r.value * 100)}%` : '—')

export default function Results() {
  const loaded = useLoad(() => api.summary(), [])
  const s = loaded.data
  if (loaded.error) return <div className="page"><Problem title="The stored results could not be loaded" error={loaded.error} /></div>
  if (!s) return <div className="page"><Loading label="Loading results" /></div>
  const names = s.methods

  return (
    <div className="page results">
      <header className="page-hero">
        <h1>Results</h1>
        <p className="lede">How often the frozen pipeline agreed with the reference answers, beside a simpler method (Baseline A) measured on the same cases.</p>
        <p className="caveat">Synthetic data. Not clinical validation. Reference answers: {s.reference_label}.</p>
      </header>

      {s.splits.map((split, si) => {
        const m = (method) => split.metrics?.[method]?.fields?.combined || {}
        return (
          <section key={split.name} className="split" aria-labelledby={`split-${split.name}`} style={{ '--si': si }}>
            <div className="split-head">
              <h2 id={`split-${split.name}`}>{split.title}</h2>
              <p className="caveat">{[SPLIT_LINES[split.name], ...split.disclosures].filter(Boolean).join(' ')}</p>
            </div>
            <div className="measures">
              {MEASURES.map(([key, label, plain], mi) => (
                <div key={key} className="measure" style={{ '--mi': mi }}>
                  <h3>{label}</h3>
                  <p className="measure-plain">{plain}</p>
                  <div className="pair-pct">
                    {METHODS.map((method) => {
                      const r = m(method)[key]
                      return (
                        <figure key={method} className={`pct pct-${method}`}>
                          <span className="pct-value">{pct(r)}</span>
                          <figcaption>{names[method]}</figcaption>
                          <span className="pct-bar" aria-hidden="true"><span style={{ '--v': r?.value ?? 0 }} /></span>
                        </figure>
                      )
                    })}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )
      })}

      <details className="measured">
        <summary><Icon name="chevron" size={18} />How these were measured</summary>
        <div className="measured-body">
          <p>Each in-scope case has two fields, onset date and maximum grade; both are counted. Splits are reported separately and never pooled. Values are rounded to a whole percent; the exact fractions are below.</p>
          <table className="data">
            <thead><tr><th scope="col">Split</th><th scope="col">Measure</th>{METHODS.map((x) => <th key={x} scope="col">{names[x]}</th>)}</tr></thead>
            <tbody>
              {s.splits.flatMap((split) => MEASURES.map(([key, label, , formula]) => (
                <tr key={split.name + key}>
                  <td>{split.title}</td>
                  <td>{label}<span className="muted"> · {formula}</span></td>
                  {METHODS.map((method) => {
                    const r = split.metrics?.[method]?.fields?.combined?.[key]
                    return <td key={method} className="mono">{r ? `${r.n}/${r.d}${r.value == null ? ' (undefined)' : ''}` : '—'}</td>
                  })}
                </tr>
              )))}
            </tbody>
          </table>
          <p>Baseline A is conventional validation on the same extracted observations: no event-time reconstruction, attribution, observation window or record history (evaluation-spec §4).</p>
          <ul className="measured-list">{s.limitations.map((l) => <li key={l}>{l}</li>)}</ul>
          <p className="muted">From {s.splits.map((x) => x.results_file).join(' and ')}.</p>
        </div>
      </details>
    </div>
  )
}
