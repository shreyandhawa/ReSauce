import { memo, useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { OUTCOMES, matchesFilter } from '../../lib/outcome.js'
import { PATH, onHop } from '../../lib/runner.js'
import { springTo } from '../../lib/spring.js'
import { reducedMotion } from '../../lib/motion.js'
import { plural, signedDay } from '../../lib/format.js'
import Icon from '../Icon.jsx'
import { NODE_R, PILL_PAD, hopPaths } from './layout.js'
import { COLUMN, NODE_INFO } from './route.js'
import { Beacon, Gate, Mark, Socket } from './parts.jsx'
import { createSignals } from './signals.js'

const GROUPS = ['input', 'discrepancy', 'review', 'clear', 'error']
/** Whether a line has one end at this node (a line goes from fromCol into the column named by its band). */
const touches = (ln, column, key) => (ln.band === column && ln.to === key) || (ln.fromCol === column && ln.from === key)
const pct = (v, total) => `${(v / total) * 100}%`

/**
 * The pipeline stage. Everything drawn is a real record, a real stage, a real kind of stage result
 * or a real outcome: `layout` (called L inside) comes from layout.js; place(id) says where the display
 * has a record now. A line is drawn only once a record the display has moved along it took it.
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
  const view = useRef({ k: 1, s: 1, x: 0, y: 0, bx: 0 })
  const springHandle = useRef({})
  const [frame, setFrame] = useState({ w: 0, h: 0, k: 1 })
  const [zoomed, setZoomed] = useState(false)
  const [hover, setHover] = useState(null)
  const [focusKey, setFocusKey] = useState({})
  layoutRef.current = L

  // -- size: the world keeps the layout's proportions; a wide stage is capped to most of the viewport height.
  useLayoutEffect(() => {
    const el = viewRef.current
    if (!el) return
    const measure = () => {
      const w = el.clientWidth
      const cap = L.orientation === 'h' ? Math.max(480, window.innerHeight * 0.8) : Infinity
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
    if (view.current.s <= 1.01 || e.button !== 0 || e.target.closest('.node, .cn, button, a, .ov-hit')) return
    e.currentTarget.setPointerCapture(e.pointerId)
    cancelAnimationFrame(springHandle.current.raf)
    drag.current = { x: e.clientX - view.current.x, y: e.clientY - view.current.y }
  }
  const onPointerMove = (e) => {
    if (!drag.current) return
    apply(clamp({ ...view.current, x: e.clientX - drag.current.x, y: e.clientY - drag.current.y }))
  }
  const onPointerUp = () => { drag.current = null }

  // -- signals: one canvas, fed by the run's hops. A record's signal splits into one dot per line it
  //    really takes into the next column (connect cause and effect), and the node it reaches flashes.
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
      const toColumn = to !== 'outcome'
      for (const pts of hopPaths(lay, id, from, to)) sig.add(pts, ms, toColumn ? 'signal' : outcome, 0, toColumn)
      // A clean record's signal carries on down its wire into the socket.
      const wire = to === 'outcome' && outcome === 'clear' ? lay.nodeOf.outcome[id]?.toSocket?.pts : null
      if (wire) sig.add(wire, ms * 0.8, 'clear', ms)
    })
    return () => { off(); sig.destroy(); mq.removeEventListener('change', readColors); themeWatch.disconnect() }
  }, [])

  // -- which records have really passed where (the display's place, never ahead of the real run)
  const total = Math.max(1, records.size)
  const litIds = useCallback((ln) => ln.ids.filter((id) => {
    const p = place(id)
    return ln.band === 'outcome' ? p.landed : p.passed >= PATH.indexOf(ln.band)
  }), [place])

  const lit = useMemo(() => {
    const lines = new Map()
    for (const ln of L.lines) {
      const ids = litIds(ln)
      if (ids.length) lines.set(ln.key, ids)
    }
    // per column node: the cases the display has taken through it, and what they carried there
    const nodes = {}
    for (const col of L.columns) {
      nodes[col.key] = {}
      for (const n of col.nodes) nodes[col.key][n.key] = { ids: [], items: 0 }
    }
    for (const [id, rec] of records) {
      const passed = place(id).passed
      for (const col of L.columns) {
        if (passed < col.index) continue
        for (const [key, count] of rec.route?.nodes[col.key] || []) {
          const slot = nodes[col.key][key]
          if (slot) { slot.ids.push(id); slot.items += count }
        }
      }
    }
    return { lines, nodes }
  }, [L, records, place, litIds])

  // -- what is lit, traced, dimmed
  const selectedId = selected?.type === 'case' ? selected.id : null
  const focusNode = hover?.node || (selected?.type === 'node' ? { column: selected.column, key: selected.key } : null)
  const focusIds = focusNode ? new Set(lit.nodes[focusNode.column]?.[focusNode.key]?.ids || []) : null
  const tracing = Boolean(selectedId || focusNode)
  const matches = (id) => matchesFilter(place(id).pending ? null : records.get(id), filter)
  const filtering = filter.outcome !== 'all' || Boolean(filter.hub)

  const lineTraced = (ln, ids) => (selectedId ? ids.includes(selectedId) : focusNode ? touches(ln, focusNode.column, focusNode.key) : false)
  // a node stays bright on a trace when the traced case went through it, or a drawn line joins it to the focused node
  const nodeOnTrace = (col, key) => {
    if (selectedId) return lit.nodes[col][key].ids.includes(selectedId)
    if (!focusNode) return true
    if (col === focusNode.column && key === focusNode.key) return true
    return L.lines.some((ln) => lit.lines.has(ln.key) && touches(ln, focusNode.column, focusNode.key) && touches(ln, col, key))
  }

  const nodesOf = useMemo(() => {
    const landedIn = (name) => L.clusters[name].nodes.filter((n) => n.ids.some((id) => place(id).landed))
    return {
      input: L.input.nodes,
      discrepancy: landedIn('discrepancy'),
      review: landedIn('review'),
      clear: landedIn('clear'),
      error: L.clusters.error.nodes.filter((n) => place(n.ids[0]).landed),
      ...Object.fromEntries(L.columns.map((c) => [`col:${c.key}`, c.nodes])),
    }
  }, [L, place])

  const pick = (group, node, el) => {
    const rect = el?.getBoundingClientRect()
    if (node.ids.length === 1) onSelect({ type: 'case', id: node.ids[0], group }, rect)
    else onSelect({ type: 'group', ids: node.ids, group }, rect)
  }
  const pickNode = (n, el) => onSelect({ type: 'node', column: n.column, key: n.key }, el?.getBoundingClientRect())

  // Roving focus inside each group of marks and each stage column: arrows move, Home/End jump.
  const onKeys = (group, node, e, choose) => {
    const list = nodesOf[group]
    const i = list.findIndex((n) => n.key === node.key)
    const step = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key]
    if (step || e.key === 'Home' || e.key === 'End') {
      e.preventDefault()
      const next = e.key === 'Home' ? list[0] : e.key === 'End' ? list[list.length - 1] : list[Math.max(0, Math.min(list.length - 1, i + step))]
      if (next) {
        setFocusKey((f) => ({ ...f, [group]: next.key }))
        requestAnimationFrame(() => document.getElementById(`n-${group.replace(':', '-')}-${next.key}`)?.focus())
      }
    } else if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      choose(e.currentTarget)
    }
  }

  const tipAt = (el) => {
    const v = viewRef.current?.getBoundingClientRect()
    const r = el.getBoundingClientRect()
    return v ? { x: r.left + r.width / 2 - v.left, y: r.top - v.top } : null
  }
  const showTip = (group, node, el) => {
    const at = tipAt(el)
    if (at) setHover({ key: node.key, ids: node.ids, group, pending: place(node.ids[0]).pending, ...at })
  }
  const showNodeTip = (n, el) => {
    const at = tipAt(el)
    if (at) setHover({ key: `${n.column}:${n.key}`, node: { column: n.column, key: n.key }, ...at })
  }

  const ordered = (group) => {
    const list = nodesOf[group]
    const current = focusKey[group]
    return list.some((n) => n.key === current) ? current : list[0]?.key
  }

  const renderMark = (group, node, r, extra = {}) => {
    const id = node.ids[0]
    const rec = records.get(id)
    const multi = node.ids.length > 1
    const outcome = group === 'input' ? null : rec?.outcome
    const isSel = selectedId && node.ids.includes(selectedId)
    const dim = (filtering && !node.ids.some(matches)) || (selectedId && !isSel) || (focusIds && !node.ids.some((x) => focusIds.has(x)))
    const inputWord = place(id).pending ? 'being verified' : rec?.outcome === 'not_run' ? 'not verified yet' : `verified, ${OUTCOMES[rec?.outcome]?.word || ''}`
    const label = multi ? `${node.ids.length} cases` : `${id}: ${group === 'input' ? inputWord : OUTCOMES[outcome]?.word}`
    const cls = ['node', `node-${group}`, dim && 'is-dim', isSel && 'is-selected', extra.cls].filter(Boolean).join(' ')
    return (
      <g key={node.key} id={`n-${group}-${node.key}`} className={cls} transform={`translate(${node.x} ${node.y})`} style={extra.style}
        tabIndex={ordered(group) === node.key ? 0 : -1} role="button" aria-label={label} aria-pressed={isSel || undefined}
        onMouseEnter={(e) => showTip(group, node, e.currentTarget)} onMouseLeave={() => setHover(null)}
        onFocus={(e) => showTip(group, node, e.currentTarget)} onBlur={() => setHover(null)}
        onClick={(e) => pick(group, node, e.currentTarget)} onKeyDown={(e) => onKeys(group, node, e, (el) => pick(group, node, el))}>
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

  // A finding-type hub shows once a record of the current display has landed on it (during a re-run,
  // hubs that only the previous run reached stay hidden).
  const hubLanded = (name, key) => nodesOf[name].some((n) => n.hub === key) ||
    L.clusters[name].extra.some((x) => x.hub === key && place(x.id).landed)

  const W = L.W, H = L.H
  const h = L.orientation === 'h'
  const empty = L.input.nodes.length === 0
  const tracedRec = selectedId ? records.get(selectedId) : null

  return (
    <div className={`stage-view${zoomed ? ' is-zoomed' : ''}`} ref={viewRef} style={{ height: frame.h || undefined }}
      onPointerDown={onPointerDown} onPointerMove={onPointerMove} onPointerUp={onPointerUp} onPointerCancel={onPointerUp}
      onDoubleClick={(e) => { if (!e.target.closest('.node, .cn, button, a')) { const r = viewRef.current.getBoundingClientRect(); zoomAt(2, e.clientX - r.left, e.clientY - r.top) } }}>
      <div className="world" ref={worldRef} style={{ width: W * frame.k, height: H * frame.k, '--k': frame.k }}>
        <svg className={`net net-${L.orientation}${tracing ? ' is-tracing' : ''}${intro ? ' is-intro' : ''}`} viewBox={`0 0 ${W} ${H}`} width="100%" height="100%"
          role="group" aria-label="Pipeline network: imported cases branch through the document types read, what the notes say, how the timeline sorted it and the fields the rules engine checked, to one of three destinations.">
          <Links L={L} lit={lit} total={total} place={place} selectedId={selectedId} tracedRec={tracedRec} intro={intro}
            gateStats={gateStats} lineTraced={lineTraced} filtering={filtering} matches={matches} />
          <Socket socket={L.clusters.clear.socket} orientation={L.orientation} state={socketState} />
          {L.gates.map((g, i) => (
            <g key={g.key} className="col-head" style={intro ? { '--c': i } : undefined}>
              <Gate gate={g} {...gateStats[i]} />
              <text className="col-sub" x={g.sub[0]} y={g.sub[1]} textAnchor={h ? 'middle' : 'start'} dominantBaseline="middle">{L.columns[i].sub}</text>
            </g>
          ))}
          {L.columns.map((col, ci) => {
            const group = `col:${col.key}`
            return (
              <g key={col.key} role="group" aria-label={`${col.title}: ${col.sub.toLowerCase()}`} className="col" style={intro ? { '--c': ci } : undefined}>
                {col.nodes.map((n) => {
                  const slot = lit.nodes[col.key][n.key]
                  const on = slot.ids.length > 0
                  const focused = focusNode?.column === col.key && focusNode.key === n.key
                  const dim = (tracing && !nodeOnTrace(col.key, n.key)) || (filtering && !slot.ids.some(matches))
                  const cls = ['cn', on && 'is-lit', dim && 'is-dim', focused && 'is-focus'].filter(Boolean).join(' ')
                  return (
                    <g key={n.key} id={`n-col-${col.key}-${n.key}`} className={cls} transform={`translate(${n.x} ${n.y})`}
                      tabIndex={ordered(group) === n.key ? 0 : -1} role="button"
                      aria-label={`${col.title}, ${NODE_INFO[col.key][n.key].name || n.label}: ${on ? plural(slot.ids.length, 'case') : 'no case yet'}`}
                      aria-pressed={(selected?.type === 'node' && focused) || undefined}
                      onMouseEnter={(e) => showNodeTip(n, e.currentTarget)} onMouseLeave={() => setHover(null)}
                      onFocus={(e) => showNodeTip(n, e.currentTarget)} onBlur={() => setHover(null)}
                      onClick={(e) => pickNode(n, e.currentTarget)} onKeyDown={(e) => onKeys(group, n, e, (el) => pickNode(n, el))}>
                      {n.w ? (
                        <>
                          <rect className="cn-pill" x={-PILL_PAD} y={-12} width={n.w} height={24} rx={12} />
                          <circle className="cn-dot" r={4.5} />
                          <text className="cn-label" x={10} y={0.5} dominantBaseline="middle">{n.label}</text>
                          {numbers && on && <text className="cn-num" x={n.w - PILL_PAD - 4} y={-19} textAnchor="end">{slot.ids.length}</text>}
                        </>
                      ) : (
                        <>
                          <circle className="hit" r={16} />
                          <circle className="cn-dot" r={NODE_R} />
                          {focused && <circle className="sel-ring" r={NODE_R * 2} />}
                        </>
                      )}
                    </g>
                  )
                })}
              </g>
            )
          })}
          {['discrepancy', 'review'].map((name) => L.clusters[name].hubs.filter((hb) => hubLanded(name, hb.key)).map((hb) => (
            <g key={`${name}-${hb.key}`} className={`hub hub-${name}${filter.hub === hb.key ? ' is-on' : ''}${filter.hub && filter.hub !== hb.key ? ' is-dim' : ''}`}>
              <circle cx={hb.x} cy={hb.y} r={4.5} />
              <text x={hb.labelAt[0]} y={hb.labelAt[1]} className="hub-label" onClick={() => onHub(name, hb.key)}>{hb.label}</text>
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
                    return renderMark(group, node, r, { waiting: p.input === 'waiting', cls: fresh ? 'node-arrive' : undefined, style: fresh ? { '--i': Math.min(i, 90) } : undefined })
                  }
                  const cls = landing ? 'node-land' : intro ? 'node-intro' : undefined
                  return renderMark(group, node, r, { cls, style: intro ? { '--i': Math.min(i, 40) } : undefined })
                })}
              </g>
            )
          })}
        </svg>

        <div className="overlay">
          <div className="ov-label ov-input" style={{ left: pct(L.input.label[0], W), top: pct(L.input.label[1], H) }}>
            <span className="ov-title">Imported cases</span>
            <span className="ov-sub">One mark per case</span>
            {numbers && <span className="ov-num">{stats.input.cases} cases · {stats.input.waiting} not verified</span>}
          </div>
          {empty && (
            <div className="ov-empty" style={{ left: pct(L.input.box.x, W), top: pct(L.input.box.y + L.input.box.h * 0.3, H), width: pct(L.input.box.w + 60, W) }}>
              <p>No cases yet. Bring synthetic cases into the workspace to begin.</p>
              {emptyAction}
            </div>
          )}
          {numbers && L.gates.map((g, i) => (
            <span key={g.key} className={`ov-num ov-gate${h ? '' : ' is-row'}`} style={{ left: pct(h ? g.x : g.sub[0], W), top: pct(g.sub[1] + (h ? 16 : 14), H) }}>
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
                {!nodesOf[name].length && <span className="ov-none">None so far</span>}
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

      {hover && <Tip hover={hover} records={records} lit={lit} />}

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

/**
 * The lines. Between stage columns a line's weight grows with the share of all cases that have
 * passed along it (show progress, no number); a line no record has taken yet is not drawn.
 */
const Links = memo(function Links({ L, lit, total, place, selectedId, tracedRec, intro, gateStats, lineTraced, filtering, matches }) {
  const weight = (n) => Math.sqrt(n / total)
  return (
    <g className="links">
      {L.spine.map((s, i) => <path key={s.key} d={s.d} className={`ln ln-spine${gateStats[i].count > 0 ? ' is-lit' : ''}`} />)}
      {L.lines.map((ln) => {
        const ids = lit.lines.get(ln.key)
        if (!ids) return null
        const traced = lineTraced(ln, ids)
        const dim = filtering && !ids.some(matches)
        const target = ln.band === 'outcome' ? ` ln-${ln.cluster}` : ''
        // a dashed line cannot be drawn in by its dash offset, so on arrival it fades in instead
        const arrive = intro ? (ln.aside ? ' ln-fade' : ' ln-draw') : ''
        const cls = `ln ln-${ln.band === 'load' ? 'in' : 'flow'}${target}${ln.aside ? ' ln-aside' : ''} is-lit${traced ? ' is-traced' : ''}${dim ? ' is-dim' : ''}${arrive}`
        const w = weight(ids.length)
        const style = ln.band === 'load'
          ? (intro ? { '--b': 0 } : undefined)
          : { '--w': `${(0.7 + 2.8 * w).toFixed(2)}px`, '--o': (0.26 + 0.56 * w).toFixed(3), '--b': PATH.indexOf(ln.band) - 1 }
        return <path key={ln.key} d={ln.d} pathLength={intro && !ln.aside ? 1 : undefined} className={cls} style={style} />
      })}
      {['discrepancy', 'review'].map((name) => {
        const c = L.clusters[name]
        return (
          <g key={name} className={`cluster-links cl-${name}`}>
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
      {tracedRec?.outcome === 'clear' && L.nodeOf.outcome[selectedId]?.fromEntry && place(selectedId).landed && (
        <path d={L.nodeOf.outcome[selectedId].fromEntry.d} className="ln ln-flow ln-clear is-lit is-traced" />
      )}
    </g>
  )
})

function Tip({ hover, records, lit }) {
  if (hover.node) {
    const { column, key } = hover.node
    const info = NODE_INFO[column][key]
    const slot = lit.nodes[column][key]
    const unit = COLUMN[column].unit
    return (
      <div className="tip on-light" style={{ left: hover.x, top: hover.y }} role="tooltip">
        <span className="tip-id tip-node">{info.name || info.label}</span>
        <span className="tip-rec">
          {slot.ids.length ? `${plural(slot.ids.length, 'case')}${unit ? ` · ${plural(slot.items, unit)}` : ''}` : 'No case has reached it yet'}
        </span>
      </div>
    )
  }
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
