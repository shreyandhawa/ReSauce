import { memo, useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { OUTCOMES, matchesFilter } from '../../lib/outcome.js'
import { onHop } from '../../lib/runner.js'
import { springTo } from '../../lib/spring.js'
import { reducedMotion } from '../../lib/motion.js'
import { signedDay } from '../../lib/format.js'
import Icon from '../Icon.jsx'
import { hopPoints } from './layout.js'
import { Beacon, Gate, Mark, Socket } from './parts.jsx'
import { createSignals } from './signals.js'

const GROUPS = ['input', 'discrepancy', 'review', 'clear', 'error']
const pct = (v, total) => `${(v / total) * 100}%`

/**
 * The pipeline stage. Everything drawn is a real record, a real stage or a real outcome:
 * `layout` (called L inside) comes from layout.js; place(id) says where the display has a record now.
 */
export default function Network({
  layout: L, records, place, gateStats, stats, numbers, filter, selected, onSelect, onHub,
  intro, arrivals, landing, beacon, socketState, emptyAction,
}) {
  const viewRef = useRef(null)
  const worldRef = useRef(null)
  const canvasRef = useRef(null)
  const signals = useRef(null)
  const layoutRef = useRef(L)
  const recordsRef = useRef(records)
  const view = useRef({ k: 1, s: 1, x: 0, y: 0, bx: 0 })
  const springHandle = useRef({})
  const [frame, setFrame] = useState({ w: 0, h: 0, k: 1 })
  const [zoomed, setZoomed] = useState(false)
  const [hover, setHover] = useState(null)
  const [focusKey, setFocusKey] = useState({})
  layoutRef.current = L
  recordsRef.current = records

  // -- size: the world keeps the layout's proportions; a wide stage is capped to the viewport height.
  useLayoutEffect(() => {
    const el = viewRef.current
    if (!el) return
    const measure = () => {
      const w = el.clientWidth
      const cap = L.orientation === 'h' ? Math.max(440, window.innerHeight * 0.68) : Infinity
      const k = Math.min(w / L.W, cap / L.H)
      setFrame({ w, h: L.H * k, k })
    }
    measure()
    const ro = new ResizeObserver(measure)
    ro.observe(el)
    window.addEventListener('resize', measure)
    return () => { ro.disconnect(); window.removeEventListener('resize', measure) }
  }, [L.W, L.H, L.orientation])

  const apply = useCallback((v) => {
    view.current = { ...view.current, ...v }
    const { s, x, y } = view.current
    if (worldRef.current) worldRef.current.style.transform = `translate(${x}px, ${y}px) scale(${s})`
    signals.current?.setView(view.current)
  }, [])

  const clamp = useCallback((v) => {
    const { w, h, k } = frame
    const cw = L.W * k * v.s, ch = L.H * k * v.s
    const x = cw <= w ? (w - cw) / 2 : Math.min(0, Math.max(w - cw, v.x))
    const y = ch <= h ? (h - ch) / 2 : Math.min(0, Math.max(h - ch, v.y))
    return { ...v, x, y }
  }, [frame, L.W, L.H])

  // Orient: fitting the stage (and every later zoom) moves on a critically damped spring.
  const goTo = useCallback((target, instant) => {
    const next = clamp(target)
    setZoomed(next.s > 1.01)
    if (instant || reducedMotion()) { cancelAnimationFrame(springHandle.current.raf); apply(next); return }
    const { s, x, y } = view.current
    springTo(springHandle.current, { s, x, y }, { s: next.s, x: next.x, y: next.y }, apply)
  }, [apply, clamp])

  useLayoutEffect(() => {
    view.current.k = frame.k
    goTo({ s: 1, x: 0, y: 0 }, true)
  }, [frame, goTo])

  const zoomAt = useCallback((factor, px, py) => {
    const { s, x, y } = view.current
    const ns = Math.min(4, Math.max(1, s * factor))
    goTo({ s: ns, x: px - (px - x) * (ns / s), y: py - (py - y) * (ns / s) })
  }, [goTo])

  // Pinch (or Ctrl/⌘ + wheel) zooms around the pointer; a plain wheel keeps scrolling the page.
  useEffect(() => {
    const el = viewRef.current
    if (!el) return
    const onWheel = (e) => {
      if (!e.ctrlKey && !e.metaKey) return
      e.preventDefault()
      const r = el.getBoundingClientRect()
      const { s, x, y } = view.current
      const ns = Math.min(4, Math.max(1, s * Math.exp(-e.deltaY * 0.01)))
      const px = e.clientX - r.left, py = e.clientY - r.top
      cancelAnimationFrame(springHandle.current.raf)
      const next = clamp({ s: ns, x: px - (px - x) * (ns / s), y: py - (py - y) * (ns / s) })
      setZoomed(next.s > 1.01)
      apply(next) // direct manipulation: 1:1 with the gesture, no easing
    }
    el.addEventListener('wheel', onWheel, { passive: false })
    return () => el.removeEventListener('wheel', onWheel)
  }, [apply, clamp])

  // Drag the background to pan while zoomed in (pointer capture keeps it going past the edge).
  const drag = useRef(null)
  const onPointerDown = (e) => {
    if (view.current.s <= 1.01 || e.button !== 0 || e.target.closest('.node, button, a, .ov-hit')) return
    e.currentTarget.setPointerCapture(e.pointerId)
    cancelAnimationFrame(springHandle.current.raf)
    drag.current = { x: e.clientX - view.current.x, y: e.clientY - view.current.y }
  }
  const onPointerMove = (e) => {
    if (!drag.current) return
    apply(clamp({ ...view.current, x: e.clientX - drag.current.x, y: e.clientY - drag.current.y }))
  }
  const onPointerUp = () => { drag.current = null }

  // -- signals: one canvas, fed by the run's hops.
  useEffect(() => {
    const sig = createSignals(canvasRef.current)
    signals.current = sig
    sig.setView(view.current)
    const readColors = () => {
      const cs = getComputedStyle(viewRef.current)
      sig.setColors({
        signal: cs.getPropertyValue('--stage-ink').trim(),
        discrepancy: cs.getPropertyValue('--red-vivid').trim(),
        review: cs.getPropertyValue('--amber-vivid').trim(),
        clear: cs.getPropertyValue('--green-vivid').trim(),
      })
    }
    readColors()
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    mq.addEventListener('change', readColors)
    const themeWatch = new MutationObserver(readColors)
    themeWatch.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
    const off = onHop(({ id, from, to, ms, outcome }) => {
      const lay = layoutRef.current
      sig.add(hopPoints(lay, id, from, to), ms, to === 'outcome' ? outcome : 'signal')
      // Connect cause and effect: a clean record's signal carries on down its wire into the socket.
      const wire = to === 'outcome' && outcome === 'clear' ? lay.nodeOf.outcome[id]?.toSocket?.pts : null
      if (wire) sig.add(wire, ms * 0.8, 'clear', ms)
    })
    return () => { off(); sig.destroy(); mq.removeEventListener('change', readColors); themeWatch.disconnect() }
  }, [])

  // -- what is lit, traced, dimmed
  const selectedId = selected?.type === 'case' ? selected.id : null
  const tracing = Boolean(selectedId)
  const matches = (id) => matchesFilter(place(id).pending ? null : records.get(id), filter)
  const filtering = filter.outcome !== 'all' || Boolean(filter.hub)

  const nodesOf = useMemo(() => {
    const landedIn = (name) => L.clusters[name].nodes.filter((n) => n.ids.some((id) => place(id).landed))
    return {
      input: L.input.nodes,
      discrepancy: landedIn('discrepancy'),
      review: landedIn('review'),
      clear: landedIn('clear'),
      error: L.clusters.error.nodes.filter((n) => place(n.ids[0]).landed),
    }
  }, [L, place])

  const pick = (group, node, el) => {
    const rect = el?.getBoundingClientRect()
    if (node.ids.length === 1) onSelect({ type: 'case', id: node.ids[0], group }, rect)
    else onSelect({ type: 'group', ids: node.ids, group }, rect)
  }

  const onNodeKey = (group, node, e) => {
    const list = nodesOf[group]
    const i = list.findIndex((n) => n.key === node.key)
    const step = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key]
    if (step || e.key === 'Home' || e.key === 'End') {
      e.preventDefault()
      const next = e.key === 'Home' ? list[0] : e.key === 'End' ? list[list.length - 1] : list[Math.max(0, Math.min(list.length - 1, i + step))]
      if (next) {
        setFocusKey((f) => ({ ...f, [group]: next.key }))
        requestAnimationFrame(() => document.getElementById(`n-${group}-${next.key}`)?.focus())
      }
    } else if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      pick(group, node, e.currentTarget)
    }
  }

  const showTip = (group, node, el) => {
    const v = viewRef.current?.getBoundingClientRect()
    const r = el.getBoundingClientRect()
    if (!v) return
    setHover({ key: node.key, ids: node.ids, group, pending: place(node.ids[0]).pending, x: r.left + r.width / 2 - v.left, y: r.top - v.top })
  }

  const ordered = (group) => {
    const list = nodesOf[group]
    const current = focusKey[group]
    return list.some((n) => n.key === current) ? current : list[0]?.key
  }

  const renderNode = (group, node, r, extra = {}) => {
    const id = node.ids[0]
    const rec = records.get(id)
    const multi = node.ids.length > 1
    const outcome = group === 'input' ? null : rec?.outcome
    const isSel = selectedId && node.ids.includes(selectedId)
    const dim = (filtering && !node.ids.some(matches)) || (tracing && !isSel)
    const inputWord = place(id).pending ? 'being verified' : rec?.outcome === 'not_run' ? 'not verified yet' : `verified, ${OUTCOMES[rec?.outcome]?.word || ''}`
    const label = multi ? `${node.ids.length} cases` : `${id}: ${group === 'input' ? inputWord : OUTCOMES[outcome]?.word}`
    const cls = ['node', `node-${group}`, dim && 'is-dim', isSel && 'is-selected', extra.cls].filter(Boolean).join(' ')
    return (
      <g key={node.key} id={`n-${group}-${node.key}`} className={cls} transform={`translate(${node.x} ${node.y})`} style={extra.style}
        tabIndex={ordered(group) === node.key ? 0 : -1} role="button" aria-label={label} aria-pressed={isSel || undefined}
        onMouseEnter={(e) => showTip(group, node, e.currentTarget)} onMouseLeave={() => setHover(null)}
        onFocus={(e) => showTip(group, node, e.currentTarget)} onBlur={() => setHover(null)}
        onClick={(e) => pick(group, node, e.currentTarget)} onKeyDown={(e) => onNodeKey(group, node, e)}>
        <g className="node-inner">
          <circle className="hit" r={Math.max(r * 2.4, 8)} />
          <Mark outcome={outcome} r={multi ? r * 1.35 : r} waiting={extra.waiting}
            decided={rec && rec.outcome === 'discrepancy' ? rec.openAlerts === 0 : rec?.outcome === 'review' ? rec.open === 0 : false}
            annotated={rec?.annotated} />
          {isSel && <circle className="sel-ring" r={r * 2.5} />}
        </g>
      </g>
    )
  }

  const W = L.W, H = L.H
  const empty = L.input.nodes.length === 0
  const branchLit = (name) => stats[name]?.cases > 0
  const tracedRec = selectedId ? records.get(selectedId) : null

  return (
    <div className={`stage-view${zoomed ? ' is-zoomed' : ''}`} ref={viewRef} style={{ height: frame.h || undefined }}
      onPointerDown={onPointerDown} onPointerMove={onPointerMove} onPointerUp={onPointerUp} onPointerCancel={onPointerUp}
      onDoubleClick={(e) => { if (!e.target.closest('.node, button, a')) { const r = viewRef.current.getBoundingClientRect(); zoomAt(2, e.clientX - r.left, e.clientY - r.top) } }}>
      <div className="world" ref={worldRef} style={{ width: W * frame.k, height: H * frame.k, '--k': frame.k }}>
        <svg className={`net${tracing ? ' is-tracing' : ''}${intro ? ' is-intro' : ''}`} viewBox={`0 0 ${W} ${H}`} width="100%" height="100%"
          role="group" aria-label="Pipeline network: imported cases on the left travel through Load, Extraction, Timeline and the Rules engine to one of three destinations.">
          <Links L={L} records={records} place={place} stats={stats} selectedId={selectedId} tracedRec={tracedRec} intro={intro} arrivals={arrivals} gateStats={gateStats} branchLit={branchLit} />
          <Socket socket={L.clusters.clear.socket} orientation={L.orientation} state={socketState} />
          {L.gates.map((g, i) => <Gate key={g.key} gate={g} {...gateStats[i]} />)}
          {['discrepancy', 'review'].map((name) => L.clusters[name].hubs.map((h) => (
            <g key={`${name}-${h.key}`} className={`hub hub-${name}${filter.hub === h.key ? ' is-on' : ''}${filter.hub && filter.hub !== h.key ? ' is-dim' : ''}`}>
              <circle cx={h.x} cy={h.y} r={4.5} />
              <text x={h.labelAt[0]} y={h.labelAt[1]} className="hub-label" onClick={() => onHub(name, h.key)}>{h.label}</text>
            </g>
          )))}
          {GROUPS.map((group) => {
            const list = nodesOf[group]
            if (!list.length) return null
            const r = group === 'input' ? L.input.r : group === 'error' ? L.r : L.clusters[group].r
            return (
              <g key={group} role="group" aria-label={group === 'input' ? 'Imported cases' : OUTCOMES[group].word}>
                {list.map((node, i) => {
                  if (group === 'input') {
                    const p = place(node.ids[0])
                    const fresh = intro || node.ids.some((id) => arrivals?.has(id))
                    return renderNode(group, node, r, { waiting: p.input === 'waiting', cls: fresh ? 'node-arrive' : undefined, style: fresh ? { '--i': Math.min(i, 90) } : undefined })
                  }
                  const cls = landing ? 'node-land' : intro ? 'node-intro' : undefined
                  return renderNode(group, node, r, { cls, style: intro ? { '--i': Math.min(i, 40) } : undefined })
                })}
              </g>
            )
          })}
        </svg>

        <div className="overlay">
          <div className="ov-label ov-input" style={{ left: pct(L.input.label[0], W), top: pct(L.input.label[1], H) }}>
            <span className="ov-title">Imported cases</span>
            <span className="ov-sub">One mark per case, as imported</span>
            {numbers && <span className="ov-num">{stats.input.cases} cases · {stats.input.waiting} not verified</span>}
          </div>
          {empty && (
            <div className="ov-empty" style={{ left: pct(L.input.box.x, W), top: pct(L.input.box.y + L.input.box.h * 0.36, H), width: pct(L.input.box.w, W) }}>
              <p>No cases yet. Bring synthetic cases into the workspace to begin.</p>
              {emptyAction}
            </div>
          )}
          {numbers && L.gates.map((g, i) => (
            <span key={g.key} className="ov-num ov-gate" style={{ left: pct(g.x, W), top: pct(g.y + (L.orientation === 'h' ? 34 : 0), H), marginLeft: L.orientation === 'v' ? 70 : undefined }}>
              {gateStats[i].count} passed{gateStats[i].failed ? ` · ${gateStats[i].failed} stopped` : ''}
              {gateStats[i].seconds != null && <span className="ov-gate-ms">{(gateStats[i].seconds * 1000).toFixed(1)} ms this run</span>}
            </span>
          ))}
          {['discrepancy', 'review'].map((name) => {
            const c = L.clusters[name]
            return (
              <button key={name} type="button" className={`ov-label ov-hit ov-${name}`} style={{ left: pct(c.title[0], W), top: pct(c.title[1], H) }}
                onClick={(e) => onSelect({ type: 'cluster', name }, e.currentTarget.getBoundingClientRect())}>
                <span className="ov-title"><Shape outcome={name} />{OUTCOMES[name].word}{name === 'discrepancy' && beacon.on && <Beacon spinning={beacon.spinning} />}</span>
                <span className="ov-sub">{name === 'discrepancy' ? 'Record and documents disagree' : 'Uncertain evidence or out of scope'}</span>
                {numbers && <span className="ov-num">{name === 'discrepancy' ? `${stats.discrepancy.cases} cases · ${stats.discrepancy.items} discrepancies` : `${stats.review.cases} cases`}</span>}
                {!c.hubs.length && <span className="ov-none">None so far</span>}
              </button>
            )
          })}
          <button type="button" className="ov-label ov-hit ov-clear" style={{ left: pct(L.clusters.clear.label[0], W), top: pct(L.clusters.clear.label[1], H) }}
            onClick={(e) => onSelect({ type: 'cluster', name: 'clear' }, e.currentTarget.getBoundingClientRect())}>
            <span className="ov-title"><Shape outcome="clear" />No discrepancy detected</span>
            <span className="ov-sub">Both fields agree (§7.6/7.7)</span>
            {numbers && <span className="ov-num">{stats.clear.cases} cases{stats.clear.annotated ? ` · ${stats.clear.annotated} with flags` : ''}</span>}
          </button>
        </div>
      </div>

      <canvas className="signals" ref={canvasRef} aria-hidden="true" />

      {hover && <Tip hover={hover} records={records} />}

      <div className="zoom" role="group" aria-label="Zoom">
        <button type="button" className="icon-btn" aria-label="Zoom in" onClick={() => zoomAt(1.5, frame.w / 2, frame.h / 2)}><Icon name="zoomin" size={18} /></button>
        <button type="button" className="icon-btn" aria-label="Zoom out" onClick={() => zoomAt(1 / 1.5, frame.w / 2, frame.h / 2)} disabled={!zoomed}><Icon name="zoomout" size={18} /></button>
        <button type="button" className="icon-btn" aria-label="Show the whole pipeline" onClick={() => goTo({ s: 1, x: 0, y: 0 })} disabled={!zoomed}><Icon name="fit" size={18} /></button>
      </div>
    </div>
  )
}

export function Shape({ outcome, size = 14 }) {
  return <span className={`shape shape-${outcome}`}><Icon name={OUTCOMES[outcome]?.icon || 'ring'} size={size} /></span>
}

/** The paths: imported cases fan into the first stage, stages chain, the run branches. */
const Links = memo(function Links({ L, records, place, selectedId, tracedRec, intro, arrivals, gateStats, branchLit }) {
  const tracedNode = selectedId ? L.nodeOf.outcome[selectedId] : null
  return (
    <g className="links">
      {L.input.nodes.map((n, i) => {
        const left = n.ids.some((id) => place(id).input === 'left')
        const traced = selectedId && n.ids.includes(selectedId)
        const fresh = intro || n.ids.some((id) => arrivals?.has(id))
        return <path key={n.key} pathLength="1" d={L.inputCurves[n.key].d}
          className={`ln ln-in${left ? ' is-lit' : ''}${traced ? ' is-traced' : ''}${fresh ? ' ln-draw' : ''}`} style={fresh ? { '--i': Math.min(i, 90) } : undefined} />
      })}
      {L.gateLinks.map((g, i) => <path key={g.key} d={g.d} className={`ln ln-gate${gateStats[i + 1].count > 0 ? ' is-lit' : ''}${tracedRec ? ' is-traced' : ''}`} />)}
      {['discrepancy', 'review', 'clear'].map((name) => (
        <path key={name} d={L.branches[name].d} className={`ln ln-branch ln-${name}${branchLit(name) ? ' is-lit' : ''}${tracedRec?.outcome === name ? ' is-traced' : ''}`} />
      ))}
      {['discrepancy', 'review'].map((name) => {
        const c = L.clusters[name]
        return (
          <g key={name} className={`cluster-links cl-${name}`}>
            {c.bus && <path d={c.bus.d} className={`ln ln-bus ln-${name} is-lit`} />}
            {c.nodes.map((n) => n.ids.some((id) => place(id).landed) && (
              <path key={n.key} d={n.spoke.d} className={`ln ln-spoke ln-${name}${n.ids.includes(selectedId) ? ' is-traced' : ''}`} />
            ))}
            {c.extra.map((x) => place(x.id).landed && <path key={x.key} d={x.d} className={`ln ln-spoke ln-extra ln-${name}${x.id === selectedId ? ' is-traced' : ''}`} />)}
          </g>
        )
      })}
      {L.clusters.clear.nodes.map((n) => n.ids.some((id) => place(id).landed) && (
        <path key={n.key} d={n.toSocket.d} className={`ln ln-socket${n.ids.includes(selectedId) ? ' is-traced' : ''}`} />
      ))}
      {tracedNode?.fromEntry && <path d={tracedNode.fromEntry.d} className="ln ln-branch ln-clear is-lit is-traced" />}
    </g>
  )
})

function Tip({ hover, records }) {
  const multi = hover.ids.length > 1
  const rec = records.get(hover.ids[0])
  const r = rec?.record
  const outcome = rec?.outcome
  return (
    <div className="tip on-light" style={{ left: hover.x, top: hover.y }} role="tooltip">
      {multi ? (
        <span className="tip-id">{hover.ids.length} cases · {hover.ids[0]} to {hover.ids[hover.ids.length - 1]}</span>
      ) : (
        <>
          <span className="tip-id">{hover.ids[0]}</span>
          {hover.pending
            ? <span className="tip-out"><Shape outcome="not_run" size={12} />Being verified in this run</span>
            : <span className="tip-out"><Shape outcome={outcome} size={12} />{OUTCOMES[outcome]?.word}</span>}
          {r && <span className="tip-rec">Record: {r.icans_reported ? `onset ${r.onset_date || 'empty'}${r.onset_day != null ? ` (${signedDay(r.onset_day)})` : ''}, ${r.max_grade != null ? `grade ${r.max_grade}` : 'grade empty'}` : 'no ICANS reported'}</span>}
        </>
      )}
    </div>
  )
}
