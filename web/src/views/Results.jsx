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
// Baseline B appears only where a results file holds it (its answers are stored, evaluation-spec §5).
const ALL_METHODS = ['resauce', 'baseline_a', 'baseline_b']
const SPLIT_LINES = {
  dev: 'Used to build the pipeline, so expected to be optimistic.',
}

const pct = (r) => (r && r.value != null ? `${Math.round(r.value * 100)}%` : '—')
const methodsOf = (split) => ALL_METHODS.filter((m) => split.metrics?.[m])
const usd = (v) => `$${v.toFixed(2)}`

export default function Results() {
  const loaded = useLoad(() => api.summary(), [])
  const s = loaded.data
  if (loaded.error) return <div className="page"><Problem title="The stored results could not be loaded" error={loaded.error} /></div>
  if (!s) return <div className="page"><Loading label="Loading results" /></div>
  const names = s.methods
  const columns = ALL_METHODS.filter((m) => s.splits.some((x) => x.metrics?.[m]))
  const withB = columns.includes('baseline_b')
  const bModel = s.splits.find((x) => x.metrics?.baseline_b)?.metadata?.baseline_b?.settings?.model
  // Whether the AI model scores above ReSauce on any headline measure of any split (read from the stored
  // results, so the note below never claims more than the numbers show).
  const bAhead = withB && s.splits.some((split) => MEASURES.some(([key]) => {
    const b = split.metrics?.baseline_b?.fields?.combined?.[key]?.value
    const r = split.metrics?.resauce?.fields?.combined?.[key]?.value
    return b != null && r != null && b > r
  }))

  return (
    <div className="page results">
      <header className="page-hero">
        <h1>Results</h1>
        <p className="lede">
          {withB
            ? 'How often the frozen pipeline agreed with the reference answers, beside two other methods measured on the same cases: Baseline A, a simpler conventional check, and Baseline B, an AI model given the same written rules.'
            : 'How often the frozen pipeline agreed with the reference answers, beside a simpler method (Baseline A) measured on the same cases.'}
        </p>
        <p className="caveat">
          Synthetic data. Not clinical validation. Reference answers: {s.reference_label}.
        </p>
        {withB && (
          <p className="caveat-ai">
            <strong>{bAhead ? 'Why the AI model scores higher than ReSauce.' : 'Reading the AI model’s scores.'}</strong>{' '}
            Baseline B is {bModel ? <span className="mono">{bModel}</span> : 'an AI model'}, from the same AI model family (Claude) that wrote these synthetic cases and their reference answers, from the same rules text. That is most likely why it agrees with them so closely. Its scores show that it reproduces answers written the same way; they are not evidence that it would do better than ReSauce on real records, or that either is clinically right. Separately, ReSauce’s phrase lists were built from the 20 dev cases only, so it can miss wordings that appear only in the held-out cases; how many of its misses this explains was not measured. A fair comparison needs cases and answers written and checked independently, by clinicians.
          </p>
        )}
      </header>

      {s.splits.map((split, si) => {
        const m = (method) => split.metrics?.[method]?.fields?.combined || {}
        const methods = methodsOf(split)
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
                  <div className={`pair-pct n-${methods.length}`}>
                    {methods.map((method) => {
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
            <thead><tr><th scope="col">Split</th><th scope="col">Measure</th>{columns.map((x) => <th key={x} scope="col">{names[x]}</th>)}</tr></thead>
            <tbody>
              {s.splits.flatMap((split) => [
                ...MEASURES.map(([key, label, , formula]) => [key, label, formula, (method) => split.metrics?.[method]?.fields?.combined?.[key]]),
                ['evidence', 'Evidence quotes valid', 'quote equals the source text at its position', (method) => split.metrics?.[method]?.evidence_validity],
              ].map(([key, label, formula, get]) => (
                <tr key={split.name + key}>
                  <td>{split.title}</td>
                  <td>{label}<span className="muted"> · {formula}</span></td>
                  {columns.map((method) => {
                    const r = get(method)
                    return <td key={method} className="mono">{r ? `${r.n}/${r.d}${r.value == null ? ' (undefined)' : ''}` : '—'}</td>
                  })}
                </tr>
              )))}
            </tbody>
          </table>
          <p>Baseline A is conventional validation on the same extracted observations: no event-time reconstruction, attribution, observation window or record history (evaluation-spec §4).</p>
          {withB && (
            <p>
              Baseline B is an AI model (<span className="mono">{bModel}</span>) given the same written rules (clinical-methods §1–§9) and each case's files, answering once per case with quoted evidence. Its answers were collected once, stored and scored like the other methods; the model is not called by this app (evaluation-spec §5).
              {' '}Cost of collecting the answers: {s.splits.filter((x) => x.metrics?.baseline_b).map((x) => `${usd(x.metrics.baseline_b.cost_usd)} (${x.title})`).join(', ')}.
              {' '}{s.splits.map((x) => {
                const n = x.metrics?.baseline_b?.errors?.length
                return n ? `${n} answer${n === 1 ? '' : 's'} in ${x.title} could not be used and count as errors.` : null
              }).filter(Boolean).join(' ')}
            </p>
          )}
          <ul className="measured-list">{s.limitations.map((l) => <li key={l}>{l}</li>)}</ul>
          <p className="muted">From {s.splits.map((x) => x.results_file).join(' and ')}.</p>
        </div>
      </details>
    </div>
  )
}
