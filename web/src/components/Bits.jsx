import Icon from './Icon.jsx'
import { citation } from '../lib/format.js'

// The fixed severity ramp: one symbol, one word and at most one colour per state.
const FINDING_SIGNS = {
  alert: ['discrepancy', 'Discrepancy'],
  flag: ['review', 'Needs review'],
  review: ['review', 'Needs human review'],
  review_item: ['review', 'Needs human review'],
  other: ['flag', 'Flag'],
  oos: ['flag', 'Out of scope'],
  clear: ['clear', 'No alert'],
}

/** A finding's sign: from its tier and kind. */
export function findingSign(f) {
  if (f.kind === 'field') return f.category_kind === 'alert' ? 'alert' : f.category_kind === 'review' ? 'review' : 'flag'
  if (f.kind === 'review_item') return 'review_item'
  if (f.kind === 'out_of_scope') return 'oos'
  return 'other'
}

export function Sign({ kind, children }) {
  const [icon, word] = FINDING_SIGNS[kind] || FINDING_SIGNS.other
  const cls = kind === 'alert' ? 'alert' : kind === 'clear' ? 'clear' : kind === 'other' || kind === 'oos' ? 'flag' : 'review'
  return (
    <span className={`sign sign-${cls}`}>
      <Icon name={icon} size={16} />
      {children ?? word}
    </span>
  )
}

const STATUS = {
  not_run: ['notrun', 'Not run', 'none'],
  no_findings: ['clear', 'No findings', 'clear'],
  to_review: ['review', 'Findings to review', 'review'],
  reviewed: ['reviewed', 'Reviewed', 'reviewed'],
  error: ['error', 'Run failed', 'error'],
  invalid: ['error', 'Invalid case folder', 'invalid'],
}

export function StatusSign({ status, alerts = 0 }) {
  const [icon, word, cls] = STATUS[status] || STATUS.not_run
  const showAlert = status === 'to_review' && alerts > 0
  return (
    <span className={`sign sign-${showAlert ? 'alert' : cls}`}>
      <Icon name={showAlert ? 'discrepancy' : icon} size={16} />
      {showAlert ? 'Discrepancy to review' : word}
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
  return <p className="note" role="status">{label}…</p>
}

/** A clickable evidence citation: jumps to the quote in its document. */
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
