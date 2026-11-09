import Icon from './Icon.jsx'
import { citation } from '../lib/format.js'
import { OUTCOMES } from '../lib/outcome.js'

// The fixed status vocabulary: one shape, one word and at most one colour per state.
// Red is discrepancy only; amber is needs review only; green is no discrepancy only.
const FINDING_SIGNS = {
  alert: ['discrepancy', 'Discrepancy', 'alert'],
  flag: ['review', 'Needs review', 'review'],
  review: ['review', 'Needs human review', 'review'],
  review_item: ['review', 'Needs human review', 'review'],
  other: ['flag', 'Flag', 'flag'],
  oos: ['flag', 'Out of scope', 'flag'],
  clear: ['clear', 'No alert', 'clear'],
}

/** A finding's sign: from its tier and kind. */
export function findingSign(f) {
  if (f.kind === 'field') return f.category_kind === 'alert' ? 'alert' : f.category_kind === 'review' ? 'review' : 'flag'
  if (f.kind === 'review_item') return 'review_item'
  if (f.kind === 'out_of_scope') return 'oos'
  return 'other'
}

export function Sign({ kind, children }) {
  const [icon, word, cls] = FINDING_SIGNS[kind] || FINDING_SIGNS.other
  return (
    <span className={`sign sign-${cls}`}>
      <Icon name={icon} size={15} />
      {children ?? word}
    </span>
  )
}

/** Where the pipeline placed a case (lib/outcome.js). */
export function OutcomeSign({ outcome, children }) {
  return (
    <span className={`sign sign-o-${outcome}`}>
      <Icon name={OUTCOMES[outcome]?.icon || 'ring'} size={15} />
      {children ?? OUTCOMES[outcome]?.word}
    </span>
  )
}

// Review state is the reviewer's to-do list, not a finding about the data, so it is shown in ink:
// the colours stay with the pipeline outcome (OutcomeSign).
const STATUS = {
  not_run: ['notrun', 'Not verified yet', 'none'],
  no_findings: ['reviewed', 'Nothing to review', 'flag'],
  to_review: ['queue', 'Findings to review', 'flag'],
  reviewed: ['reviewed', 'Reviewed', 'flag'],
  error: ['error', 'Run failed', 'error'],
  invalid: ['error', 'Invalid case folder', 'error'],
}

/** The review state of a case (decisions), separate from its pipeline outcome. */
export function StatusSign({ status }) {
  const [icon, word, cls] = STATUS[status] || STATUS.not_run
  return (
    <span className={`sign sign-${cls}`}>
      <Icon name={icon} size={15} />
      {word}
    </span>
  )
}

export const STATUS_WORDS = Object.fromEntries(Object.entries(STATUS).map(([k, v]) => [k, v[1]]))

export function Problem({ title, error }) {
  return (
    <div className="callout callout-alert" role="alert">
      <p><strong>{title}</strong></p>
      <p>{String(error?.message || error)}</p>
    </div>
  )
}

export function Loading({ label = 'Loading' }) {
  return <p className="loading" role="status"><span className="loading-dot" aria-hidden="true" />{label}…</p>
}

/** An evidence citation: jumps to the quote in its document when that is possible. */
export function Evidence({ evidence, onCite }) {
  const clickable = onCite && evidence.start != null && evidence.document_id && evidence.document_id.includes('-D')
  const body = (
    <>
      <span className="ev-ref"><span className="mono">{citation(evidence)}</span>{evidence.role ? ` · ${evidence.role}` : ''}</span>
      {evidence.quote && <span className="ev-quote">{evidence.quote}</span>}
    </>
  )
  return clickable ? (
    <button type="button" className="ev" onClick={() => onCite(evidence)} aria-label={`Show in document: ${evidence.quote}`}>{body}</button>
  ) : (
    <span className="ev ev-static">{body}</span>
  )
}

export function EvidenceList({ evidence, onCite }) {
  if (!evidence?.length) return null
  return <div className="evidence">{evidence.map((e, i) => <Evidence key={i} evidence={e} onCite={onCite} />)}</div>
}

export function Segmented({ label, options, value, onChange }) {
  return (
    <div className="segmented" role="group" aria-label={label}>
      {options.map(([v, text]) => (
        <button key={v} type="button" aria-pressed={value === v} onClick={() => onChange(v)}>{text}</button>
      ))}
    </div>
  )
}
