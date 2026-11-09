import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { api } from '../api.js'
import { EvidenceList, Loading, OutcomeSign, Problem, Sign, findingSign } from './Bits.jsx'
import Icon from './Icon.jsx'
import { CATEGORY_NAMES, FIELDS, FIELD_NAMES, code, days, plural, valueText } from '../lib/format.js'
import { useLoad } from '../lib/hooks.js'
import { animate, duration, reducedMotion } from '../lib/motion.js'
import { HUBS, HUB_NAMES, OUTCOMES, failedStage } from '../lib/outcome.js'
import { PATH, STAGES } from '../lib/runner.js'
import { COLUMN, NODE_INFO, groupOf, kindName } from './network/route.js'

const MEANING = {
  discrepancy: 'At least one field came out 7.1, 7.2, 7.3 or 7.8 (clinical-methods §7). Each is a potential discrepancy for a person to review, never a verdict.',
  review: 'No alert, but at least one field is 7.4 (insufficient evidence), 7.5 (ambiguous evidence) or a “review: …” result the rules could not decide, or the case is out of scope (§5) and gets no category.',
  clear: 'What was checked: the onset date and the maximum grade in the research record, against the quoted documents, under the frozen rules of clinical-methods §7. Both fields came out 7.6 (legitimate revision) or 7.7 (no discrepancy).',
}
const CAVEAT = 'Not proof that a record is correct: the data are synthetic, the rules have not been reviewed by a clinician, and results on synthetic data are not clinical validation.'

const narrow = () => window.matchMedia('(max-width: 760px)').matches
const centre = (r) => [r.left + r.width / 2, r.top + r.height / 2]

/** A mark-sized ghost flying between two places on screen (the shared element of the open and the close). */
function fly(from, to, outcome, [s0, s1]) {
  const ghost = document.createElement('span')
  ghost.className = `flight flight-${outcome}`
  document.body.appendChild(ghost)
  const a = ghost.animate([
    { transform: `translate(${from[0]}px, ${from[1]}px) scale(${s0})`, opacity: 1 },
    { opacity: 1, offset: 0.7 },
    { transform: `translate(${to[0]}px, ${to[1]}px) scale(${s1})`, opacity: 0 },
  ], { duration: duration('spring-move'), easing: getComputedStyle(document.documentElement).getPropertyValue('--ease-in-out').trim() })
  a.finished.then(() => ghost.remove(), () => ghost.remove())
  return ghost
}

/**
 * The inspector: a sheet beside the stage (a bottom sheet on phones) with one selection in detail.
 * Parallel, non-blocking: no scrim, the stage stays usable. Enters from the side it lives on and
 * leaves the same way; on phones it can be dragged down to dismiss.
 */
export default function Inspector({ selection, origin, records, place, onClose, onSelect, onHub }) {
  const ref = useRef(null)
  const headRef = useRef(null)
  const returnFocus = useRef(null)
  const closing = useRef(false)
  const outcome = selection.type === 'case' ? records.get(selection.id)?.outcome : selection.name || 'group'

  // Spatial consistency: the sheet enters from its edge as a material (blur, scale and offset together).
  useLayoutEffect(() => {
    returnFocus.current = document.activeElement
    const from = narrow() ? 'translateY(100%) scale(0.96)' : 'translateX(104%) scale(0.96)'
    animate(ref.current, [{ transform: from, filter: 'blur(8px)', opacity: 0.4 }, { transform: 'none', filter: 'blur(0px)', opacity: 1 }], { dur: 'spring-sheet', ease: 'spring-sheet' })
    headRef.current?.focus({ preventScroll: true })
  }, [])

  // Spatial consistency: a record flies from its mark on the stage into the sheet's heading.
  const headMark = () => ref.current?.querySelector('.insp-head .sign svg')?.getBoundingClientRect()
  useLayoutEffect(() => {
    const target = headMark()
    if (!origin || !target || reducedMotion()) return
    const ghost = fly(centre(origin), centre(target), outcome, [1, 1.6])
    return () => ghost.remove()
  }, [selection]) // eslint-disable-line react-hooks/exhaustive-deps

  // ...and back into its mark when the sheet closes, unless the mark it came from was inside the sheet.
  const flyBack = () => {
    const from = headMark()
    const sheet = ref.current?.getBoundingClientRect()
    if (!origin || !from || !sheet || reducedMotion()) return
    const [ox, oy] = centre(origin)
    if (ox >= sheet.left && ox <= sheet.right && oy >= sheet.top && oy <= sheet.bottom) return
    fly(centre(from), [ox, oy], outcome, [1.6, 1])
  }

  const finish = () => { onClose(); returnFocus.current?.focus?.({ preventScroll: true }) }
  const leave = (from) => {
    if (closing.current) return
    closing.current = true
    flyBack()
    const to = narrow() ? 'translateY(100%)' : 'translateX(104%)'
    const a = animate(ref.current, [{ transform: from, opacity: 1 }, { transform: to, opacity: 0.6 }], { dur: 'base', ease: 'out', fill: 'forwards' })
    if (a) a.finished.then(finish, finish); else finish()
  }
  const close = () => leave(getComputedStyle(ref.current).transform)

  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape' && !document.querySelector('dialog[open]')) close() }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  })

  // Drag to dismiss (phones): 1:1 with the finger, a flick or a long pull closes, otherwise it springs back.
  const drag = useRef(null)
  const onGrab = (e) => {
    if (!narrow()) return
    e.currentTarget.setPointerCapture(e.pointerId)
    drag.current = { y0: e.clientY, t0: performance.now(), dy: 0 }
  }
  const onDrag = (e) => {
    if (!drag.current) return
    const dy = e.clientY - drag.current.y0
    drag.current.dy = dy
    // Past the top the sheet resists (rubber band) instead of stopping dead.
    ref.current.style.transform = `translateY(${dy > 0 ? dy : (dy * 0.55 * 300) / (300 + 0.55 * Math.abs(dy))}px)`
  }
  const onDrop = () => {
    if (!drag.current) return
    const { dy, t0 } = drag.current
    drag.current = null
    const velocity = dy / (performance.now() - t0)
    if (dy > 90 || velocity > 0.5) { ref.current.style.transform = ''; leave(`translateY(${dy}px)`); return }
    animate(ref.current, [{ transform: `translateY(${dy}px)` }, { transform: 'none' }], { dur: 'spring-sheet', ease: 'spring-sheet', fill: 'none' })
    ref.current.style.transform = ''
  }

  return (
    <aside className="inspector" ref={ref} aria-labelledby="insp-title">
      <div className="insp-grab" onPointerDown={onGrab} onPointerMove={onDrag} onPointerUp={onDrop} onPointerCancel={onDrop} aria-hidden="true"><span /></div>
      <button type="button" className="icon-btn insp-close" onClick={close} aria-label="Close the inspector"><Icon name="close" size={18} /></button>
      <div className="insp-scroll">
        <div key={selection.type + (selection.id || selection.name || selection.ids?.[0] || `${selection.column}:${selection.key}`)} className="insp-body">
          {selection.type === 'case' && <CaseDetail id={selection.id} rec={records.get(selection.id)} headRef={headRef} />}
          {selection.type === 'group' && <GroupDetail ids={selection.ids} records={records} headRef={headRef} onSelect={onSelect} />}
          {selection.type === 'cluster' && <ClusterDetail name={selection.name} records={records} place={place} headRef={headRef} onSelect={onSelect} onHub={onHub} />}
          {selection.type === 'node' && <NodeDetail column={selection.column} nodeKey={selection.key} records={records} place={place} headRef={headRef} onSelect={onSelect} />}
        </div>
      </div>
    </aside>
  )
}

function CaseDetail({ id, rec, headRef }) {
  // Read again when a new run of this case lands, so the times, findings and run ID belong together.
  const detail = useLoad(() => api.caseDetail(id), [id, rec?.runAt])
  const [report, setReport] = useState(null)
  const d = detail.data
  const run = d?.run
  const output = run?.resauce?.output
  const items = d?.findings || []
  const open = items.filter((i) => !i.decision).length
  const seconds = run?.timings_seconds || {}
  const stopped = failedStage(run)
  const path = [...STAGES, ...(run?.baseline_a || seconds.baseline != null ? [['baseline', 'Baseline A (comparison, beside the pipeline)']] : [])]

  const exportReport = async () => {
    setReport({ busy: true })
    try {
      const r = await api.exportCase(id)
      setReport(r)
      window.open(r.url, '_blank', 'noopener')
    } catch (error) { setReport({ error: error.message }) }
  }

  return (
    <>
      <header className="insp-head">
        <h2 id="insp-title" className="insp-id" ref={headRef} tabIndex={-1}>{id}</h2>
        {rec && <OutcomeSign outcome={rec.outcome} />}
      </header>
      {rec && <p className="insp-lead">{rec.outcome === 'error' ? `The pipeline stopped at ${STAGES.find(([k]) => k === rec.failedStage)?.[1] || rec.failedStage}.` : OUTCOMES[rec.outcome].line}</p>}
      {detail.error && <Problem title={`${id} could not be opened`} error={detail.error} />}
      {!d && !detail.error && <Loading label="Reading the case" />}
      {d?.invalid && <Problem title="This case folder does not pass the data-format check" error={d.invalid} />}

      {output && !output.out_of_scope && (
        <section className="insp-sec" aria-label="Fields">
          {FIELDS.map((name) => {
            const field = output.fields[name]
            const finding = items.find((x) => x.finding_id === name)
            const c = code(field.category)
            return (
              <div key={name} className={`insp-field${finding?.category_kind === 'alert' ? ' is-alert' : finding ? ' is-review' : ''}`}>
                <div className="insp-field-head">
                  <span className="insp-field-name">{FIELD_NAMES[name]}</span>
                  {finding ? <Sign kind={findingSign(finding)}>{finding.label}</Sign> : <span className="sign sign-clear"><Icon name="clear" size={15} />{c ? `${CATEGORY_NAMES[c]} (${c})` : field.category}</span>}
                </div>
                <dl className="pair">
                  <div><dt>Record</dt><dd className="mono">{field.record_value == null ? 'empty' : name === 'max_grade' ? `Grade ${field.record_value}` : field.record_value}</dd></div>
                  <div><dt>Documents</dt><dd className="mono">{valueText(field.documented_value)}</dd></div>
                  {field.signed_difference_days != null && <div><dt>Difference</dt><dd>{days(field.signed_difference_days)}</dd></div>}
                </dl>
                {field.difference_note && <p className="insp-note">{field.difference_note}</p>}
              </div>
            )
          })}
        </section>
      )}

      {run && (
        <section className="insp-sec" aria-labelledby="insp-path">
          <h3 id="insp-path">Path through the pipeline</h3>
          <ol className="insp-path">
            {path.map(([key, label]) => {
              const failed = stopped === key
              const ran = seconds[key] != null
              return (
                <li key={key} data-state={failed ? 'error' : ran ? 'done' : 'idle'}>
                  <span className="insp-step">{label}</span>
                  {ran && <span className="mono insp-ms">{(seconds[key] * 1000).toFixed(1)} ms</span>}
                  {failed && <span className="insp-ms">stopped here</span>}
                </li>
              )
            })}
          </ol>
          <p className="insp-fine">Measured times of the stored run <span className="mono">{run.run_id}</span>, pipeline <span className="mono">{run.pipeline?.tag}</span>{run.pipeline?.frozen_files_match ? '' : ' (frozen files changed)'}.</p>
        </section>
      )}

      {items.length > 0 && (
        <section className="insp-sec" aria-labelledby="insp-find">
          <h3 id="insp-find">Findings and evidence</h3>
          {items.map((f) => (
            <article key={f.finding_id} className={`insp-finding k-${findingSign(f)}`}>
              <div className="insp-finding-head">
                <Sign kind={findingSign(f)}>{f.kind === 'field' ? FIELD_NAMES[f.field] : f.label}</Sign>
                <span className={`decision${f.decision ? '' : ' is-open'}`}>{f.decision ? `${f.decision.label} · ${f.decision.reviewer}` : 'Open'}</span>
              </div>
              {f.kind === 'field' && <p className="insp-note">{f.label}</p>}
              {f.detail && f.kind !== 'field' && <p className="insp-note">{f.detail}{f.rule ? ` (${f.rule})` : ''}</p>}
              <EvidenceList evidence={f.evidence} />
            </article>
          ))}
        </section>
      )}

      {d && !d.invalid && (
        <div className="insp-actions">
          <a className="btn btn-primary" href={`#/case/${encodeURIComponent(id)}`}><Icon name="open" size={16} />Open case</a>
          {open > 0 && <a className="btn" href={`#/queue?case=${encodeURIComponent(id)}`}>Review findings</a>}
          {run && <button type="button" className="btn btn-quiet" onClick={exportReport} disabled={report?.busy}><Icon name="print" size={16} />{report?.busy ? 'Writing…' : 'Case report'}</button>}
          {report?.error && <p className="problem-text">{report.error}</p>}
          {report?.file && <p className="insp-fine">Written to <span className="mono">{report.file}</span></p>}
        </div>
      )}
    </>
  )
}

function GroupDetail({ ids, records, headRef, onSelect }) {
  return (
    <>
      <header className="insp-head">
        <h2 id="insp-title" className="insp-id" ref={headRef} tabIndex={-1}>{ids.length} cases</h2>
      </header>
      <p className="insp-lead">This mark stands for several cases, grouped so a large dataset stays readable. Choose one to inspect it.</p>
      <CaseChips ids={ids} records={records} onSelect={onSelect} />
    </>
  )
}

function ClusterDetail({ name, records, place, headRef, onSelect, onHub }) {
  // Only the cases the stage shows there now: during a run, a case counts once it has landed.
  const members = [...records.values()].filter((r) => r.outcome === name && place(r.id).landed)
  const items = members.reduce((n, r) => n + r.alerts, 0)
  const annotated = members.filter((r) => r.annotated).length
  return (
    <>
      <header className="insp-head">
        <h2 id="insp-title" className="insp-title" ref={headRef} tabIndex={-1}><OutcomeSign outcome={name} /></h2>
      </header>
      <p className="insp-lead">{MEANING[name]}</p>
      {name === 'clear' && <p className="insp-caveat">{CAVEAT}</p>}
      <p className="insp-count">
        {members.length} case{members.length === 1 ? '' : 's'}
        {name === 'discrepancy' && items !== members.length ? ` · ${items} discrepancies (a case can have one in each field)` : ''}
        {name === 'clear' && annotated ? ` · ${annotated} still carry flags or review items (marked with a dot)` : ''}
      </p>
      {HUBS[name] && (
        <ul className="insp-hubs">
          {HUBS[name].map(([key]) => {
            const n = members.filter((r) => r.hubs.includes(key)).length
            return n ? (
              <li key={key}><button type="button" className="linkish" onClick={() => onHub(name, key)}>{HUB_NAMES[key]}</button><span className="mono">{n}</span></li>
            ) : null
          })}
        </ul>
      )}
      <CaseChips ids={members.map((r) => r.id)} records={records} onSelect={onSelect} />
    </>
  )
}

/** A node of a stage column: what it means, what it groups, and the cases the stage has taken through it. */
function NodeDetail({ column, nodeKey, records, place, headRef, onSelect }) {
  const col = COLUMN[column]
  const info = NODE_INFO[column]?.[nodeKey]
  if (!col || !info) return null
  // Only the cases the stage shows there now: during a run, a case counts once it has passed this stage.
  const members = [...records.values()].filter((r) => place(r.id).passed >= PATH.indexOf(column) && r.route?.nodes[column].has(nodeKey))
  const items = members.reduce((n, r) => n + r.route.nodes[column].get(nodeKey), 0)
  const kindCount = (k) => members.reduce((n, r) => n + (r.route.kinds.get(k) || 0), 0)
  // the group's kinds, plus any kind the cases carry that this view does not know (it is counted here too)
  const kinds = info.kinds && [...new Set([...info.kinds, ...members.flatMap((r) => [...r.route.kinds.keys()].filter((k) => groupOf(k) === nodeKey))])]
  return (
    <>
      <header className="insp-head">
        <h2 id="insp-title" className="insp-title" ref={headRef} tabIndex={-1}>{info.name || info.label}</h2>
      </header>
      <p className="insp-count">
        {col.title} stage · {plural(members.length, 'case')}
        {col.unit && members.length ? ` · ${plural(items, col.unit)}` : ''}
      </p>
      <p className="insp-lead">{info.about}</p>
      {kinds && (
        <ul className="insp-hubs" aria-label="Observation kinds in this group">
          {kinds.map((k) => (
            <li key={k}><span>{kindName(k)}</span><span className="mono">{kindCount(k)}</span></li>
          ))}
        </ul>
      )}
      <CaseChips ids={members.map((r) => r.id)} records={records} onSelect={onSelect} />
    </>
  )
}

function CaseChips({ ids, records, onSelect }) {
  if (!ids.length) return <p className="insp-fine">No cases here yet.</p>
  return (
    <ul className="chips">
      {ids.map((id) => (
        <li key={id}>
          <button type="button" className={`chip chip-${records.get(id)?.outcome}`} onClick={(e) => onSelect({ type: 'case', id }, e.currentTarget.getBoundingClientRect())}>{id}</button>
        </li>
      ))}
    </ul>
  )
}
