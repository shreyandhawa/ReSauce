import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { api } from '../api.js'
import { Loading, Problem, Sign, findingSign } from '../components/Bits.jsx'
import Icon from '../components/Icon.jsx'
import { FIELD_NAMES, citation, signedDay, valueText } from '../lib/format.js'
import { useLoad, useSessionValue } from '../lib/hooks.js'
import { animate, setOrigin } from '../lib/motion.js'
import { sliceCodePoints } from '../lib/offsets.js'

const CHOICES = [
  ['confirm', 'Confirm discrepancy', 'c'], // on a flag or out-of-scope item it confirms that item instead (below)
  ['dismiss', 'Dismiss', 'd'],
  ['clinician', 'Needs clinician', 'l'],
]
const TIERS = ['Discrepancy alerts (7.1, 7.2, 7.3, 7.8)', 'Needs review (7.4, 7.5, “review: …”)', 'Other flags and out-of-scope results']
// Connect cause and effect: each decision leaves in its own direction.
const EXIT = { confirm: 'translateX(48px)', dismiss: 'translateX(-48px)', clinician: 'translateY(-28px)' }
const CONFIRM = { out_of_scope: 'Confirm out of scope', flag: 'Confirm flag' } // §5: no discrepancy category there
const CONTEXT = 160 // characters of text shown either side of a quote

export default function ReviewQueue({ caseFilter, onChanged }) {
  const queue = useLoad(() => api.queue(), [])
  const [removed, setRemoved] = useState(() => new Set())
  const [activeKey, setActiveKey] = useState(null)
  const [leaving, setLeaving] = useState(null)
  const [reviewer, setReviewer] = useSessionValue('resauce-reviewer')
  const [docs, setDocs] = useState({}) // case_id -> documents, for quotes in context
  const nameDialog = useRef(null)

  const items = useMemo(() => (queue.data?.items || [])
    .filter((i) => !removed.has(keyOf(i)) && (!caseFilter || i.case_id === caseFilter)), [queue.data, removed, caseFilter])
  const active = items.find((i) => keyOf(i) === activeKey) || items[0]

  useEffect(() => {
    if (!active || docs[active.case_id]) return
    api.caseDetail(active.case_id).then((d) => setDocs((m) => ({ ...m, [active.case_id]: d.documents || [] }))).catch(() => {})
  }, [active, docs])

  useEffect(() => { if (!reviewer && items.length) nameDialog.current?.showModal?.() }, [reviewer, items.length])

  const move = useCallback((step) => {
    if (!items.length) return
    const i = Math.max(0, items.findIndex((x) => keyOf(x) === keyOf(active)))
    const next = items[Math.min(items.length - 1, Math.max(0, i + step))]
    setActiveKey(keyOf(next))
    document.getElementById(`q-${keyOf(next)}`)?.scrollIntoView({ block: 'nearest' })
  }, [items, active])

  const decided = (item, decision) => {
    const i = items.findIndex((x) => keyOf(x) === keyOf(item))
    const next = items[i + 1] || items[i - 1]
    setLeaving({ item, decision })
    setRemoved((s) => new Set(s).add(keyOf(item)))
    setActiveKey(next ? keyOf(next) : null)
    onChanged?.()
  }

  if (queue.error) return <div className="page"><Problem title="The review queue could not be loaded" error={queue.error} /></div>
  if (!queue.data) return <div className="page"><Loading label="Loading the review queue" /></div>

  const q = queue.data
  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Review</h1>
          <p className="sub">
            {/* No count-up: the number simply changes when a decision is saved. */}
            <strong>{items.length}</strong> open finding{items.length === 1 ? '' : 's'}{caseFilter ? <> in <span className="mono">{caseFilter}</span> · <a href="#/queue">show all cases</a></> : ''} · {q.cases_verified} of {q.cases_total} cases verified. The pipeline output is never edited; each decision is added to the audit log beside it.
          </p>
        </div>
      </div>
      <p className="reviewer-line">
        Reviewing as <strong>{reviewer || 'no name yet'}</strong>
        <button type="button" className="btn btn-quiet btn-sm" onClick={() => nameDialog.current?.showModal()}>Change</button>
      </p>

      {items.length === 0 && !leaving ? (
        <div className="panel empty">
          <h2>{q.cases_verified ? 'No open findings' : 'Nothing verified yet'}</h2>
          <p>{q.cases_verified ? 'Every finding in the verified cases has a decision. They are listed in the audit trail.' : 'Verify cases on the pipeline first; their findings appear here, most serious first.'}</p>
          <a className="btn" href={q.cases_verified ? '#/audit' : '#/pipeline'}>{q.cases_verified ? 'Open the audit trail' : 'Go to the pipeline'}</a>
        </div>
      ) : (
        <div className="queue">
          <ol className="q-list" aria-label="Open findings, most serious first">
            {items.map((item, i) => (
              <li key={keyOf(item)}>
                {(i === 0 || items[i - 1].tier !== item.tier) && <div className="q-group">{TIERS[item.tier]}</div>}
                <button type="button" id={`q-${keyOf(item)}`} className="q-item" aria-current={keyOf(item) === keyOf(active)} onClick={() => setActiveKey(keyOf(item))}>
                  <span className="q-case">{item.case_id}{item.field ? ` · ${FIELD_NAMES[item.field] || item.field}` : ''}</span>
                  <Sign kind={findingSign(item)}>{shortLabel(item)}</Sign>
                </button>
              </li>
            ))}
          </ol>
          <div className="q-stage">
            {active && <Card key={keyOf(active)} item={active} documents={docs[active.case_id]} reviewer={reviewer}
              askName={() => nameDialog.current?.showModal()} onDecided={decided} onMove={move} entering={Boolean(leaving)} />}
            {leaving && <Leaving key={`l-${keyOf(leaving.item)}`} {...leaving} documents={docs[leaving.item.case_id]} onDone={() => setLeaving(null)} />}
          </div>
        </div>
      )}

      <dialog className="modal" ref={nameDialog} aria-labelledby="name-h" onCancel={(e) => { if (!reviewer) e.preventDefault() }}>
        <NameForm initial={reviewer} onSave={(v) => { setReviewer(v); nameDialog.current?.close() }} />
      </dialog>
    </div>
  )
}

const keyOf = (i) => `${i.case_id}:${i.finding_id}:${i.output_sha256.slice(0, 8)}`
const shortLabel = (i) => (i.kind === 'review_item' && i.detail ? `Needs human review: ${i.detail.slice(0, 70)}${i.detail.length > 70 ? '…' : ''}` : i.label)

function NameForm({ initial, onSave }) {
  const [name, setName] = useState(initial || '')
  return (
    <form onSubmit={(e) => { e.preventDefault(); if (name.trim()) onSave(name.trim()) }}>
      <h2 id="name-h">Who is reviewing?</h2>
      <p>Your name is written with each decision in the audit log. It is asked once per browser session.</p>
      <div className="field"><label htmlFor="reviewer-name">Reviewer name</label><input id="reviewer-name" className="input" value={name} onChange={(e) => setName(e.target.value)} autoFocus /></div>
      <div className="row"><button type="submit" className="btn btn-primary" disabled={!name.trim()}>Start reviewing</button></div>
    </form>
  )
}

function Card({ item, documents, reviewer, askName, onDecided, onMove, entering }) {
  const ref = useRef(null)
  const noteRef = useRef(null)
  const [choice, setChoice] = useState(null)
  const [note, setNote] = useState('')
  const [problems, setProblems] = useState({})
  const [busy, setBusy] = useState(false)

  // Connect cause and effect: the next item takes the decided one's place.
  useLayoutEffect(() => {
    if (entering) animate(ref.current, [{ opacity: 0, transform: 'translateY(8px)' }, { opacity: 1, transform: 'none' }], { dur: 'base' })
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const submit = async () => {
    if (busy) return
    const local = {}
    if (!choice) local.decision = 'Choose a decision.'
    if (!note.trim()) local.note = 'A note is required for every decision.'
    if (!reviewer) { askName(); return }
    if (Object.keys(local).length) { setProblems(local); return }
    setBusy(true)
    try {
      await api.decide({ case_id: item.case_id, finding_id: item.finding_id, run_id: item.run_id, decision: choice, note, reviewer })
      onDecided(item, choice)
    } catch (error) {
      setProblems(Object.fromEntries((error.problems || [{ key: 'form', message: error.message }]).map((p) => [p.key, p.message])))
      setBusy(false)
    }
  }

  useEffect(() => {
    const onKey = (e) => {
      const typing = e.target.closest?.('input, textarea, select, [contenteditable]') || document.querySelector('dialog[open]')
      if (e.target === noteRef.current && e.key === 'Enter' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); submit(); return }
      if (e.target === noteRef.current && e.key === 'Escape') { noteRef.current.blur(); return }
      if (typing || e.metaKey || e.ctrlKey || e.altKey) return
      if (e.key === 'j' || e.key === 'ArrowDown') { e.preventDefault(); onMove(1) }
      else if (e.key === 'k' || e.key === 'ArrowUp') { e.preventDefault(); onMove(-1) }
      else {
        const c = CHOICES.find(([, , k]) => k === e.key.toLowerCase())
        if (c) { e.preventDefault(); setChoice(c[0]); noteRef.current?.focus() }
      }
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  })

  return (
    <article className="q-card" ref={ref} aria-labelledby="q-title">
      <div className="q-body"><FindingBody item={item} documents={documents} titleId="q-title" /></div>
      <div className="decide">
        <div className="decide-choices" role="radiogroup" aria-label="Decision" aria-describedby={problems.decision ? 'dec-p' : undefined}>
          {CHOICES.map(([value, label0, key]) => {
            const label = value === 'confirm' ? CONFIRM[item.kind] || label0 : label0
            return (
            <label key={value} className={`choice${value === 'confirm' ? ' btn-confirm' : ''}`}>
              <input type="radio" name="decision" value={value} checked={choice === value} onChange={() => setChoice(value)} />
              {value === 'confirm' && !CONFIRM[item.kind] && <Icon name="discrepancy" size={14} />}{label} <kbd>{key.toUpperCase()}</kbd>
            </label>
          )})}
        </div>
        {problems.decision && <span id="dec-p" className="problem-text problem-in"><Icon name="error" size={14} />{problems.decision}</span>}
        <div className="field" data-problem={problems.note ? '' : undefined}>
          <label htmlFor="q-note">Note (required)</label>
          <textarea id="q-note" ref={noteRef} className="textarea" style={{ minHeight: 80 }} value={note} onChange={(e) => setNote(e.target.value)} aria-invalid={problems.note ? true : undefined} aria-describedby={problems.note ? 'note-p' : undefined} />
          {problems.note && <span id="note-p" className="problem-text problem-in"><Icon name="error" size={14} />{problems.note}</span>}
        </div>
        {problems.form && <span className="problem-text problem-in"><Icon name="error" size={14} />{problems.form}</span>}
        <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
          <button type="button" className="btn btn-primary" onClick={submit} disabled={busy}>{busy ? 'Saving…' : 'Record decision'} <kbd>⌘/Ctrl Enter</kbd></button>
          <span className="shortcuts"><span><kbd>J</kbd> <kbd>K</kbd> next, previous</span><span><kbd>C</kbd> <kbd>D</kbd> <kbd>L</kbd> choose, then type the note</span><span><kbd>Esc</kbd> leave the note</span></span>
        </div>
      </div>
    </article>
  )
}

function Leaving({ item, decision, documents, onDone }) {
  const ref = useRef(null)
  useLayoutEffect(() => {
    // Connect cause and effect: the decided item leaves in its decision's direction (fast, ease-out:
    // a slow start would delay the very moment the reviewer is watching).
    const a = animate(ref.current, [{ opacity: 1, transform: 'none' }, { opacity: 0, transform: EXIT[decision] }], { dur: 'fast', ease: 'out', fill: 'forwards' })
    if (!a) { onDone(); return }
    a.finished.then(onDone, () => {})
    return () => a.cancel() // interruptible: a newer decision replaces this one at once
  }, []) // eslint-disable-line react-hooks/exhaustive-deps
  return <article className="q-card leaving" ref={ref} aria-hidden="true"><div className="q-body"><FindingBody item={item} documents={documents} /></div></article>
}

function FindingBody({ item, documents, titleId }) {
  return (
    <>
      <div className="q-head">
        <span className="mono">{item.case_id}</span>
        {item.field && <span className="plate-field">{FIELD_NAMES[item.field] || item.field}</span>}
        <a href={`#/case/${encodeURIComponent(item.case_id)}`} onClick={(e) => setOrigin(e.currentTarget.closest('.q-card')?.getBoundingClientRect())} style={{ marginLeft: 'auto', fontSize: 'var(--text-sm)' }}>Open case</a>
      </div>
      <h2 id={titleId} className="q-label"><Sign kind={findingSign(item)}>{item.label}</Sign></h2>
      {(item.record_value != null || item.documented_value != null) && (
        <div className="vals">
          <span>Record<b className="mono">{item.record_value == null ? 'empty' : item.field === 'max_grade' ? `Grade ${item.record_value}` : item.record_value}</b></span>
          <span>Documented<b className="mono">{valueText(item.documented_value)}</b></span>
          {item.signed_difference_days != null && <span>Difference<b>{item.signed_difference_days > 0 ? '+' : ''}{item.signed_difference_days} d</b></span>}
        </div>
      )}
      {item.detail && <p className="detail">{item.detail}{item.rule ? ` (${item.rule})` : ''}</p>}
      {item.readings?.length > 0 && <ol className="detail" style={{ paddingLeft: '1.1rem' }}>{item.readings.map((r, i) => <li key={i}>{r.category}: {r.reading}</li>)}</ol>}
      {item.evidence.length === 0 ? <p className="note">No quoted evidence for this item.</p> : item.evidence.map((ev, i) => <InContext key={i} ev={ev} documents={documents} />)}
    </>
  )
}

function InContext({ ev, documents }) {
  const doc = documents?.find((d) => d.document_id === ev.document_id && d.version === ev.version)
  const head = <p className="ev-ref"><span className="mono">{citation(ev)}</span>{ev.role ? ` · ${ev.role}` : ''}{doc ? ` · ${doc.note_type.replace(/_/g, ' ')}, documented ${doc.documented_at.replace('T', ' ')} (${signedDay(doc.documented_day)})` : ''}</p>
  if (!doc || ev.start == null) return <div>{head}<p className="context">{ev.quote}</p></div>
  const length = Array.from(doc.text).length
  const from = Math.max(0, ev.start - CONTEXT)
  const to = Math.min(length, ev.end + CONTEXT)
  return (
    <div>
      {head}
      <p className="context">
        {from > 0 && <span className="gap">… </span>}{sliceCodePoints(doc.text, from, ev.start)}
        <mark>{sliceCodePoints(doc.text, ev.start, ev.end)}</mark>
        {sliceCodePoints(doc.text, ev.end, to)}{to < length && <span className="gap"> …</span>}
      </p>
    </div>
  )
}
