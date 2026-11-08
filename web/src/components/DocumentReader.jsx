import { useEffect, useLayoutEffect, useMemo, useRef } from 'react'
import { segments } from '../lib/offsets.js'
import { NOTE_TYPES, OBS_KINDS, ROLES, documentShort, signedDay } from '../lib/format.js'
import { animate, reducedMotion } from '../lib/motion.js'

/**
 * Source documents, one version at a time, with marks at exact code-point offsets.
 * marks: [{ key, version_id, start, end, kind: 'obs' | 'cite', status?, obsId?, label }]
 * focus: { version_id, start, end, token }: scrolled to, flashed once, then held as a steady mark.
 * hot: the observation ID hovered in the timeline (or here), shown linked in both places.
 */
export default function DocumentReader({ documents, activeId, onSelect, marks, focus, hot, onHover, onMarkPick, revealing }) {
  const doc = documents.find((d) => d.version_id === activeId) || documents[0]
  const scrollRef = useRef(null)
  const docRef = useRef(null)
  const tabsRef = useRef(null)
  const inkRef = useRef(null)
  const previousIndex = useRef(null)

  const counts = useMemo(() => {
    const n = {}
    for (const m of marks) if (m.kind === 'obs') n[m.version_id] = (n[m.version_id] || 0) + 1
    return n
  }, [marks])

  const runs = useMemo(() => {
    if (!doc) return []
    const own = marks.filter((m) => m.version_id === doc.version_id)
    if (focus && focus.version_id === doc.version_id) own.push({ key: 'focus', kind: 'focus', start: focus.start, end: focus.end })
    return segments(doc.text, own)
  }, [doc, marks, focus])

  const index = documents.findIndex((d) => d.version_id === doc?.version_id)

  // Orient: the tab underline moves from the previous tab to the selected one.
  useLayoutEffect(() => {
    const tab = tabsRef.current?.querySelector('[aria-selected="true"]')
    const ink = inkRef.current
    if (!tab || !ink) return
    const first = previousIndex.current === null
    if (first) ink.style.transition = 'none'
    ink.style.transform = `translateX(${tab.offsetLeft}px) scaleX(${tab.offsetWidth})`
    if (first) requestAnimationFrame(() => { ink.style.transition = '' })
  }, [index, documents.length])

  // Orient: a newly opened document slides in from the side of the tab that was chosen.
  useLayoutEffect(() => {
    const before = previousIndex.current
    previousIndex.current = index
    if (before === null || before === index || !docRef.current) return
    const dir = index > before ? 1 : -1
    animate(docRef.current, [{ opacity: 0.35, transform: `translateX(${dir * 14}px)` }, { opacity: 1, transform: 'none' }], { dur: 'base' })
  }, [index])

  // Guide attention: jump to the cited text, then flash it once and let it settle into a steady mark.
  useEffect(() => {
    if (!focus || focus.version_id !== doc?.version_id) return
    const box = scrollRef.current
    const first = box?.querySelector('mark.m-focus')
    if (!first) return
    const target = first.offsetTop - box.clientHeight / 2 + first.offsetHeight / 2
    const smooth = !reducedMotion() && Math.abs(box.scrollTop - target) > 4
    box.scrollTo({ top: Math.max(0, target), behavior: smooth ? 'smooth' : 'auto' })
    const flash = () => {
      const styles = getComputedStyle(document.documentElement)
      const from = styles.getPropertyValue('--mark-flash').trim()
      const to = styles.getPropertyValue('--mark-cite').trim()
      // Background colour on a short inline span: the one non-transform property here, kept small.
      box.querySelectorAll('mark.m-focus').forEach((el) => animate(el, [{ backgroundColor: from }, { backgroundColor: to }], { dur: 'layout', fill: 'none' }))
    }
    if (!smooth) { flash(); return }
    let done = false
    const finish = () => { if (!done) { done = true; flash() } }
    box.addEventListener('scrollend', finish, { once: true })
    const fallback = setTimeout(finish, 450) // browsers without scrollend
    return () => { done = true; clearTimeout(fallback); box.removeEventListener('scrollend', finish) }
  }, [focus, doc?.version_id])

  const onTabKey = (e) => {
    const step = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0
    if (!step) return
    e.preventDefault()
    const next = documents[(index + step + documents.length) % documents.length]
    onSelect(next.version_id)
    requestAnimationFrame(() => document.getElementById(`tab-${next.version_id}`)?.focus())
  }

  if (!doc) return <section className="docs"><p className="note" style={{ padding: 24 }}>This case has no documents.</p></section>

  const multi = (d) => documents.some((o) => o.document_id === d.document_id && o.version !== d.version)
  let markIndex = 0
  return (
    <section className="docs" aria-label="Source documents">
      <div className="tabs" role="tablist" aria-label="Documents and versions" ref={tabsRef} onKeyDown={onTabKey}>
        {documents.map((d) => {
          const selected = d.version_id === doc.version_id
          return (
            <button key={d.version_id} id={`tab-${d.version_id}`} type="button" role="tab" aria-selected={selected}
              aria-controls="doc-panel" tabIndex={selected ? 0 : -1} className="tab" onClick={() => onSelect(d.version_id)}>
              <span>{documentShort(d.document_id)}{multi(d) ? ` v${d.version}` : ''}</span>
              <span className="tab-day">{signedDay(d.documented_day)}</span>
              {counts[d.version_id] ? <span className="tab-n" aria-label={`${counts[d.version_id]} observations`}>{counts[d.version_id]}</span> : null}
            </button>
          )
        })}
        <span className="tab-ink" ref={inkRef} aria-hidden="true" />
      </div>
      <div className="doc-scroll" ref={scrollRef}>
        <article id="doc-panel" role="tabpanel" aria-labelledby={`tab-${doc.version_id}`} className="doc" ref={docRef}>
          <h2 className="doc-title">{NOTE_TYPES[doc.note_type] || doc.note_type}</h2>
          <p className="doc-meta">
            <span className="mono">{doc.version_id}</span> · {ROLES[doc.author_role] || doc.author_role} · documented{' '}
            <span className="mono">{doc.documented_at.replace('T', ' ')}</span> ({signedDay(doc.documented_day)}) ·{' '}
            <span className={doc.status === 'signed' ? '' : 'doc-unsigned'}>{doc.status}</span>
          </p>
          {doc.amendment_reason && <p className="doc-amend">Amendment reason: {doc.amendment_reason}</p>}
          <div className={`doc-text${revealing ? ' revealing' : ''}`} onMouseLeave={() => onHover?.(null)}>
            {runs.map((r) => {
              if (!r.marks.length) return <span key={r.start}>{r.text}</span>
              const obs = r.marks.filter((m) => m.kind === 'obs')
              const cls = ['m']
              if (obs.length) cls.push('m-obs', `m-${obs[0].status}`)
              if (r.marks.some((m) => m.kind === 'cite')) cls.push('m-cite')
              if (obs.some((m) => m.obsId === hot)) cls.push('m-hover')
              if (r.marks.some((m) => m.kind === 'focus')) cls.push('m-focus')
              const first = obs[0]
              const label = r.marks.map((m) => m.label).filter(Boolean).join('; ')
              return (
                <mark key={r.start} className={cls.join(' ')} style={{ '--i': markIndex++ }} title={label || undefined}
                  onMouseEnter={first ? () => onHover?.(first.obsId) : undefined}
                  onClick={first && onMarkPick ? () => onMarkPick(first.obsId) : undefined}>
                  {r.text}
                </mark>
              )
            })}
          </div>
        </article>
      </div>
    </section>
  )
}

export function observationLabel(o) {
  const value = o.value == null ? '' : typeof o.value === 'object' ? JSON.stringify(o.value) : String(o.value)
  return `${OBS_KINDS[o.kind] || o.kind}${value ? `: ${value}` : ''} (${o.status})`
}
