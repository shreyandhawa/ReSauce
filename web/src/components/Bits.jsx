import { CATEGORY_NAMES, KIND_TEXT, categoryKind, citation, code, shortCategory } from '../lib/format.js'

export function Problem({ title, error }) {
  return (
    <div className="problem" role="alert">
      <h2>{title}</h2>
      <p>{String(error?.message || error)}</p>
      <p className="muted">Check that the server is running (<code>python -m app</code>) and reload the page.</p>
    </div>
  )
}

export function Loading({ label = 'Loading' }) {
  return <p className="loading" role="status">{label}…</p>
}

/** A category as a compact tag; the full name is in the title and for screen readers. */
export function CategoryTag({ category, against }) {
  if (category && typeof category === 'object') category = 'error'
  const kind = categoryKind(category)
  const differs = against !== undefined && category !== against
  const name = CATEGORY_NAMES[code(category)] || category || 'no result'
  return (
    <span className={`cat cat-${kind}${differs ? ' cat-differs' : ''}`} title={`${name}${KIND_TEXT[kind] ? ` (${KIND_TEXT[kind]})` : ''}`}>
      {shortCategory(category) || '—'}
      <span className="sr-only">: {name}{differs ? ', differs from the reference' : ''}</span>
    </span>
  )
}

/** Category code plus its §7 name, as a heading-sized verdict. */
export function CategoryName({ category }) {
  const kind = categoryKind(category)
  const c = code(category)
  if (kind === 'review') {
    return <span className="verdict verdict-review"><span className="verdict-code">Needs human review</span><span className="verdict-name">{category.replace(/^review:\s*/, '')}</span></span>
  }
  if (kind === 'oos') {
    return <span className="verdict verdict-oos"><span className="verdict-code">Out of scope</span><span className="verdict-name">{category.replace(/^out of scope\s*/, '').replace(/^\(|\)$/g, '')}</span></span>
  }
  return (
    <span className={`verdict verdict-${kind}`}>
      <span className="verdict-code">§{c || category}</span>
      <span className="verdict-name">{CATEGORY_NAMES[c] || category}</span>
    </span>
  )
}

/** A clickable evidence citation: jumps to the quote in its document. */
export function Cite({ evidence, onCite, showQuote = true }) {
  const clickable = onCite && evidence.start != null
  const body = (
    <>
      <span className="cite-ref">{citation(evidence)}</span>
      {evidence.role && <span className="cite-role">{evidence.role}</span>}
      {showQuote && evidence.quote && <q className="cite-quote">{evidence.quote}</q>}
    </>
  )
  return clickable ? (
    <button type="button" className="cite" onClick={() => onCite(evidence)}>{body}</button>
  ) : (
    <span className="cite cite-static">{body}</span>
  )
}

export function Segmented({ label, options, value, onChange }) {
  return (
    <div className="segmented" role="group" aria-label={label}>
      {options.map(([v, text]) => (
        <button key={v} type="button" aria-pressed={value === v} onClick={() => onChange(v)}>
          {text}
        </button>
      ))}
    </div>
  )
}
