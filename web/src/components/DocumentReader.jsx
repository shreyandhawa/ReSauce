import { useEffect, useMemo, useRef } from 'react'
import { segments } from '../lib/offsets.js'
import { NOTE_TYPES, OBS_KINDS, ROLES, documentShort, signedDay } from '../lib/format.js'

/**
 * Source documents, one version at a time, with highlights at exact code-point offsets.
 * marks: [{ key, version_id, start, end, kind: 'obs' | 'cite', status?, obsId?, label }]
 * focus: { version_id, start, end, token } — scrolled to and pulsed when it changes.
 */
export default function DocumentReader({ documents, activeId, onSelect, marks, focus, onMarkPick, sweep }) {
  const doc = documents.find((d) => d.version_id === activeId) || documents[0]
  const textRef = useRef(null)
  const counts = useMemo(() => {
    const n = {}
    for (const m of marks) if (m.kind === 'obs') n[m.version_id] = (n[m.version_id] || 0) + 1
    return n
  }, [marks])

  const docMarks = useMemo(() => {
    const own = marks.filter((m) => m.version_id === doc.version_id)
    if (focus && focus.version_id === doc.version_id) own.push({ key: 'focus', kind: 'focus', start: focus.start, end: focus.end })
    return own
  }, [marks, focus, doc.version_id])

  const runs = useMemo(() => segments(doc.text, docMarks), [doc.text, docMarks])

  useEffect(() => {
    if (!focus || focus.version_id !== doc.version_id || !textRef.current) return
    const el = textRef.current.querySelector('.m-focus')
    if (el) el.scrollIntoView({ block: 'center', behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' })
  }, [focus, doc.version_id])

  const onTabKey = (e) => {
    const i = documents.findIndex((d) => d.version_id === doc.version_id)
    const step = e.key === 'ArrowRight' || e.key === 'ArrowDown' ? 1 : e.key === 'ArrowLeft' || e.key === 'ArrowUp' ? -1 : 0
    if (!step) return
    e.preventDefault()
    const next = documents[(i + step + documents.length) % documents.length]
    onSelect(next.version_id)
    requestAnimationFrame(() => document.getElementById(`tab-${next.version_id}`)?.focus())
  }

  let markIndex = 0
  return (
    <section className="reader" aria-label="Source documents">
      <div className="reader-tabs" role="tablist" aria-label="Documents" onKeyDown={onTabKey}>
        {documents.map((d) => {
          const selected = d.version_id === doc.version_id
          return (
            <button
              key={d.version_id}
              id={`tab-${d.version_id}`}
              type="button"
              role="tab"
              aria-selected={selected}
              aria-controls="doc-panel"
              tabIndex={selected ? 0 : -1}
              className="reader-tab"
              onClick={() => onSelect(d.version_id)}
            >
              <span className="tab-id">{documentShort(d.document_id)}{d.version > 1 || documents.some((o) => o.document_id === d.document_id && o.version !== d.version) ? ` v${d.version}` : ''}</span>
              <span className="tab-day">{signedDay(d.documented_day)}</span>
              {counts[d.version_id] ? <span className="tab-count" aria-label={`${counts[d.version_id]} observations`}>{counts[d.version_id]}</span> : null}
            </button>
          )
        })}
      </div>

      <article id="doc-panel" role="tabpanel" aria-labelledby={`tab-${doc.version_id}`} className="doc">
        <header className="doc-head">
          <h2 className="doc-title">{NOTE_TYPES[doc.note_type] || doc.note_type}</h2>
          <p className="doc-meta mono">
            {doc.version_id} · {ROLES[doc.author_role] || doc.author_role} · documented {doc.documented_at.replace('T', ' ')} ({signedDay(doc.documented_day)}) ·{' '}
            <span className={doc.status === 'signed' ? '' : 'unsigned'}>{doc.status}</span>
          </p>
          {doc.amendment_reason && <p className="doc-amend">Amended: {doc.amendment_reason}</p>}
        </header>
        <div className={`doc-text${sweep ? ' sweep' : ''}`} ref={textRef}>
          {runs.map((r) => {
            if (!r.marks.length) return <span key={r.start}>{r.text}</span>
            const obs = r.marks.filter((m) => m.kind === 'obs')
            const cls = ['m']
            if (obs.length) cls.push('m-obs', `m-${obs[0].status}`)
            if (r.marks.some((m) => m.kind === 'cite')) cls.push('m-cite')
            if (r.marks.some((m) => m.kind === 'focus')) cls.push('m-focus', `pulse-${focus?.token % 2}`)
            const first = obs[0]
            const label = r.marks.map((m) => m.label).filter(Boolean).join('; ')
            return (
              <mark
                key={r.start}
                className={cls.join(' ')}
                style={{ '--i': markIndex++ }}
                title={label || undefined}
                onClick={first && onMarkPick ? () => onMarkPick(first.obsId) : undefined}
              >
                {r.text}
              </mark>
            )
          })}
        </div>
      </article>
    </section>
  )
}

export function observationLabel(o) {
  const value = o.value == null ? '' : typeof o.value === 'object' ? JSON.stringify(o.value) : String(o.value)
  return `${OBS_KINDS[o.kind] || o.kind}${value ? `: ${value}` : ''} (${o.status})`
}
