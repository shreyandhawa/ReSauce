import { CategoryName, Cite } from './Bits.jsx'
import { FIELDS, FIELD_NAMES, days, signedDay, valueText } from '../lib/format.js'

/** One method's (or the reference's) output: per-field categories with evidence, then flags. */
export default function Verdict({ output, onCite, compact = false, recordValues }) {
  if (!output) return null
  if (output.error) return <p className="problem-inline">This method failed on the case: {output.error}</p>
  const oos = output.out_of_scope
  return (
    <div className={`verdict-block${compact ? ' compact' : ''}`}>
      {oos ? (
        <div className="field-verdict">
          <CategoryName category={`out of scope (${oos.reason})`} />
          {oos.source && <p className="fv-line">Source: <span className="mono">{oos.source}</span></p>}
          <EvidenceList evidence={oos.evidence} onCite={onCite} />
          <p className="fv-note">Out-of-scope cases get no discrepancy category (clinical-methods §5).</p>
        </div>
      ) : (
        FIELDS.map((name) => {
          const f = output.fields?.[name]
          if (!f) return null
          return (
            <div key={name} className="field-verdict">
              <h4 className="fv-field">{FIELD_NAMES[name]}</h4>
              <CategoryName category={f.category} />
              <p className="fv-line">
                <span>Record: <strong>{recordText(name, f.record_value, recordValues)}</strong></span>
                <span>Documented: <strong>{valueText(f.documented_value)}</strong></span>
                {f.signed_difference_days != null && <span>Difference: <strong>{days(f.signed_difference_days)}</strong></span>}
              </p>
              {f.difference_note && <p className="fv-note">{f.difference_note}</p>}
              {f.documented_value?.undetermined && !compact && <p className="fv-note">{f.documented_value.undetermined}</p>}
              {f.readings?.length > 0 && (
                <div className="readings">
                  <p className="fv-sub">Readings: the evidence can be read in {f.readings.length} ways</p>
                  <ol>
                    {f.readings.map((r, i) => (
                      <li key={i}>
                        <span className="mono">{r.category}</span> · {valueText(r.value)}
                        {!compact && <span className="reading-text">{r.reading}</span>}
                      </li>
                    ))}
                  </ol>
                </div>
              )}
              {f.record_history && !compact && (
                <p className="fv-note">Record history (§7.6): {f.record_history.explanation}</p>
              )}
              {!compact && <EvidenceList evidence={f.evidence} onCite={onCite} />}
              {compact && f.evidence?.length > 0 && <p className="fv-sub">{f.evidence.length} evidence quote{f.evidence.length > 1 ? 's' : ''}</p>}
            </div>
          )
        })
      )}
      {!compact && <Flags output={output} onCite={onCite} />}
    </div>
  )
}

function recordText(name, value, recordValues) {
  if (value == null) return recordValues?.icans_reported === false ? 'no ICANS reported' : 'empty'
  if (name === 'max_grade') return `Grade ${value}`
  return recordValues?.onset_day != null ? `${value} · ${signedDay(recordValues.onset_day)}` : String(value)
}

export function EvidenceList({ evidence, onCite }) {
  if (!evidence?.length) return null
  return (
    <ul className="evidence">
      {evidence.map((e, i) => <li key={i}><Cite evidence={e} onCite={onCite} /></li>)}
    </ul>
  )
}

function Flags({ output, onCite }) {
  const cf = output.case_flags
  const review = output.review_items || []
  const other = output.other_flags || []
  const ungradeable = cf?.ungradeable_neurological_symptom || []
  const unassessed = cf?.unassessed_period
  if (!cf && !review.length && !other.length) return null
  return (
    <div className="flags">
      {review.length > 0 && (
        <section className="flag-group flag-review">
          <h4>Needs human review</h4>
          <ul>
            {review.map((r, i) => (
              <li key={i}>
                <p>{r.detail}{r.rule ? <span className="muted"> ({r.rule})</span> : null}</p>
                <EvidenceList evidence={r.evidence} onCite={onCite} />
              </li>
            ))}
          </ul>
        </section>
      )}
      {other.length > 0 && (
        <section className="flag-group">
          <h4>Flags</h4>
          <ul>
            {other.map((f, i) => (
              <li key={i}>
                <p><strong>{f.flag}</strong>{f.field ? <span className="muted"> · {FIELD_NAMES[f.field] || f.field}</span> : null}{f.detail ? `: ${f.detail}` : ''}</p>
                <EvidenceList evidence={f.evidence} onCite={onCite} />
              </li>
            ))}
          </ul>
        </section>
      )}
      {unassessed && (
        <section className="flag-group">
          <h4>Unassessed period <span className="muted">(case-level, §7.10)</span></h4>
          <p>
            Days with no gradeable assessment:{' '}
            {unassessed.days_without_gradeable_assessment?.length ? <span className="mono">{unassessed.days_without_gradeable_assessment.join(', ')}</span> : 'none'}.
          </p>
          {unassessed.not_assessable_periods?.length > 0 && (
            <ul>
              {unassessed.not_assessable_periods.map((p, i) => <li key={i}><Generic item={p} onCite={onCite} /></li>)}
            </ul>
          )}
        </section>
      )}
      {ungradeable.length > 0 && (
        <section className="flag-group">
          <h4>Ungradeable neurological symptoms <span className="muted">(case-level)</span></h4>
          <ul>{ungradeable.map((u, i) => <li key={i}><Generic item={u} onCite={onCite} /></li>)}</ul>
        </section>
      )}
    </div>
  )
}

/** A flag entry whose exact keys vary: shows its fields as text and its evidence as citations. */
function Generic({ item, onCite }) {
  if (item == null || typeof item !== 'object') return <span>{String(item)}</span>
  const evidence = item.evidence || (item.quote && item.document_id ? [item] : null)
  const rest = Object.entries(item).filter(([k]) => !['evidence', 'quote', 'document_id', 'version', 'start', 'end', 'role'].includes(k))
  return (
    <>
      <p>{rest.map(([k, v]) => `${k.replace(/_/g, ' ')}: ${typeof v === 'object' ? JSON.stringify(v) : v}`).join(' · ')}</p>
      <EvidenceList evidence={evidence} onCite={onCite} />
    </>
  )
}
