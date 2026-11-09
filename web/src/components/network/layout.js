// Where everything on the pipeline stage goes. A pure function of the records and the orientation:
// no React, no DOM. Imported cases → four stage columns of real nodes (route.js) → three destinations.
// Horizontal on wide screens; on narrow screens the same flow runs top to bottom (columns become rows).
//
// Each input mark is one case. Above MAX_NODES cases, marks become groups of cases (aggregation)
// so a large dataset stays legible; a group opens as a list in the inspector.
//
// A line here is geometry plus the cases that took it (`ids`). Whether it is drawn, and how heavy,
// depends on how far the display has taken each of those cases (Network.jsx).

import { PATH, STAGES } from '../../lib/runner.js'
import { HUBS } from '../../lib/outcome.js'
import { COLUMNS } from './route.js'

const MAX_NODES = 400
const GATE_W = 120
const GATE_H = 40
export const NODE_R = 6.5
export const PILL_PAD = 12 // from a pill's left edge to its dot

const BOXES = {
  h: {
    W: 1620, H: 800, flow: [1, 0],
    input: { x: 28, y: 150, w: 180, h: 590 }, inputLabel: [28, 22],
    // Each node is a pill (dot + label) whose lines enter on its left and leave on its right, so no line
    // crosses a label. Widths fit the widest label of the column at 13px (measured: 126, 122, 122, 101px)
    // with room for wider system fonts.
    columns: [312, 582, 852, 1122], pill: [170, 166, 166, 144], // left edge and width of each column's pills
    mid: 450, span: 560, gap: [78, 84, 84, 104], // nodes centre on `mid`; spacing shrinks to fit `span`
    head: 46, sub: 82, // y of the column heads and of their subtitles
    discrepancy: { x: 1362, y: 16, w: 244, h: 330 },
    review: { x: 1362, y: 500, w: 244, h: 296 },
    clear: { x: 1376, y: 427, w: 110, h: 46 }, clearLabel: [1362, 340],
    socket: [1578, 450],
  },
  v: {
    // Phones: the stage pills form a rail on the left, level with their row; the network runs to the right
    // of it, so no line crosses a stage name.
    W: 420, H: 1700, flow: [0, 1],
    input: { x: 152, y: 96, w: 248, h: 230 }, inputLabel: [16, 22],
    columns: [440, 590, 740, 890], pill: [0, 0, 0, 0], // y of each stage row; plain dots, no labels on phones
    mid: 278, span: 236, gap: [46, 54, 64, 112],
    head: 72, sub: 14, // x of the rail's pills (centre) and of their subtitles (start)
    discrepancy: { x: 8, y: 1000, w: 196, h: 344 },
    review: { x: 216, y: 1000, w: 196, h: 344 },
    // the clean records' lines run down the gap between the two clusters; the title sits under the socket
    clear: { x: 118, y: 1446, w: 184, h: 50 }, clearLabel: [104, 1628], clearVia: [210, 988],
    socket: [210, 1566],
  },
}

const fmt = (n) => Math.round(n * 10) / 10
const add = (a, b, k = 1) => [a[0] + b[0] * k, a[1] + b[1] * k]

function cubic(p0, p1, p2, p3, n = 18) {
  const pts = []
  for (let i = 0; i <= n; i++) {
    const t = i / n, u = 1 - t
    pts.push([
      u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0],
      u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1],
    ])
  }
  return { d: `M${fmt(p0[0])} ${fmt(p0[1])}C${fmt(p1[0])} ${fmt(p1[1])} ${fmt(p2[0])} ${fmt(p2[1])} ${fmt(p3[0])} ${fmt(p3[1])}`, pts }
}

const line = (a, b) => ({ d: `M${fmt(a[0])} ${fmt(a[1])}L${fmt(b[0])} ${fmt(b[1])}`, pts: [a, b] })

/** A curve that leaves and arrives along the flow (the edges of a layered network). */
function flowCurve(a, b, f, n) {
  const reach = Math.abs((b[0] - a[0]) * f[0] + (b[1] - a[1]) * f[1])
  return cubic(a, add(a, f, reach * 0.48), add(b, f, -reach * 0.48), b, n)
}

/** Split ids into groups of at most `size` (size 1 almost always). */
function groups(ids, size, prefix) {
  const out = []
  for (let i = 0; i < ids.length; i += size) out.push({ key: size === 1 ? ids[i] : `${prefix}:${i}`, ids: ids.slice(i, i + size) })
  return out
}

/** A grid of n points filling a box, centred; returns points and a node radius. */
function grid(n, box, maxStep = 22) {
  if (!n) return { pts: [], step: maxStep, r: 4 }
  let step = Math.min(maxStep, Math.sqrt((box.w * box.h) / n))
  const cols = Math.max(1, Math.min(n, Math.floor(box.w / step)))
  const rows = Math.ceil(n / cols)
  step = Math.min(step, box.h / rows, box.w / cols)
  const x0 = box.x + (box.w - (cols - 1) * step) / 2
  const y0 = box.y + (box.h - (rows - 1) * step) / 2
  const pts = []
  for (let i = 0; i < n; i++) pts.push([x0 + (i % cols) * step, y0 + Math.floor(i / cols) * step])
  return { pts, step, r: Math.max(2, Math.min(5, step * 0.27)) }
}

/**
 * records: [{ id, outcome, hubs, fieldHubs, failedStage, route }] in display order.
 */
export function layout(records, orientation = 'h') {
  const B = BOXES[orientation]
  const f = B.flow
  const h = orientation === 'h'
  const at = (along, across) => (h ? [along, across] : [across, along]) // along the flow, across it
  const size = Math.max(1, Math.ceil(records.length / MAX_NODES))
  const byId = new Map(records.map((r) => [r.id, r]))
  const routeOf = (id) => byId.get(id)?.route

  // Stage columns: a head (the stage pill) and one node per kind of result the stage reports.
  const columns = COLUMNS.map((col, i) => {
    const n = col.nodes.length
    const gap = Math.min(B.gap[i], B.span / Math.max(1, n - 1))
    const start = B.mid - (gap * (n - 1)) / 2
    const w = B.pill[i]
    const nodes = col.nodes.map((def, j) => {
      const p = at(B.columns[i] + (w ? PILL_PAD : 0), start + j * gap) // the dot
      const left = w ? add(p, f, -PILL_PAD) : add(p, f, -NODE_R)
      const right = w ? add(left, f, w) : add(p, f, NODE_R)
      return { key: def.key, label: def.label, column: col.key, x: p[0], y: p[1], w, in: left, out: right }
    })
    return { key: col.key, index: PATH.indexOf(col.key), title: col.title, sub: col.sub, nodes }
  })
  const node = Object.fromEntries(columns.map((c) => [c.key, Object.fromEntries(c.nodes.map((n) => [n.key, n]))]))

  const half = h ? GATE_W / 2 : GATE_H / 2
  const gates = STAGES.map(([key, label], i) => {
    const centre = B.columns[i] + B.pill[i] / 2
    const c = h ? [centre, B.head] : [B.head, B.columns[i]]
    return { key, label, x: c[0], y: c[1], w: GATE_W, h: GATE_H, in: add(c, f, -half), out: add(c, f, half),
      sub: h ? [centre, B.sub] : [B.sub, B.columns[i] + 36] }
  })
  // The spine: the stage order, joining the heads (a record with no line to follow moves along it).
  const inputEnd = h ? [B.input.x + B.input.w, B.head] : [B.head, B.inputLabel[1] + 70]
  const spine = [
    { key: 'input-load', from: 'input', to: 'load', ...line(inputEnd, gates[0].in) },
    ...gates.slice(1).map((g, i) => ({ key: `${gates[i].key}-${g.key}`, from: gates[i].key, to: g.key, ...line(gates[i].out, g.in) })),
  ]

  // Input: every case, as imported.
  const inputGroups = groups(records.map((r) => r.id), size, 'in')
  const g = grid(inputGroups.length, B.input)
  const input = { box: B.input, label: B.inputLabel, r: g.r, nodes: [] }
  inputGroups.forEach((grp, i) => input.nodes.push({ ...grp, x: g.pts[i][0], y: g.pts[i][1] }))

  // Destinations.
  const by = (o) => records.filter((r) => r.outcome === o)
  const clusters = {
    discrepancy: hubCluster('discrepancy', by('discrepancy'), B.discrepancy, size),
    review: hubCluster('review', by('review'), B.review, size),
  }
  const nodeOf = { outcome: {} }

  // No discrepancy: a compact grid on the main line, every mark wired to the socket.
  const socket = { x: B.socket[0], y: B.socket[1], in: add(B.socket, f, -60) } // the wires end at the back of the plug
  const clearGroups = groups(by('clear').map((r) => r.id), size, 'clear')
  const cg = grid(clearGroups.length, B.clear, 14)
  const clearEntry = h ? [B.clear.x - 8, B.mid] : [B.socket[0], B.clear.y - 8]
  const clear = { box: B.clear, r: cg.r, entry: clearEntry, socket, label: B.clearLabel, nodes: [] }
  clearGroups.forEach((grp, i) => {
    const p = cg.pts[i]
    const n = { ...grp, x: p[0], y: p[1], toSocket: cubic(p, add(p, f, 14), add(socket.in, f, -18), socket.in, 10), fromEntry: line(clearEntry, p) }
    clear.nodes.push(n)
    for (const id of grp.ids) nodeOf.outcome[id] = n
  })
  clusters.clear = clear
  for (const name of ['discrepancy', 'review']) for (const n of clusters[name].nodes) for (const id of n.ids) nodeOf.outcome[id] = n

  // Lines. Each distinct pair of nodes is one line, carrying the ids of the cases that took it.
  // A line knows the columns it joins (fromCol → band), so a trace can find its two ends.
  const lineMap = new Map()
  const byCase = {}
  const addLine = (band, fromCol, from, to, ids, extra, geometry) => {
    const key = `${band}:${from}>${to}`
    let ln = lineMap.get(key)
    if (!ln) {
      ln = { key, band, fromCol, from, to, ids: [], ...extra, ...geometry() }
      lineMap.set(key, ln)
    }
    for (const id of ids) {
      ln.ids.push(id)
      const mine = (byCase[id] ||= {})
      ;(mine[band] ||= []).push(ln)
    }
  }
  // case → the document types it contains (one line per input mark and type)
  for (const grp of input.nodes) {
    const types = new Map()
    for (const id of grp.ids) for (const { to } of routeOf(id)?.lines.load.values() || []) types.set(to, [...(types.get(to) || []), id])
    for (const [t, ids] of types) {
      const target = node.load[t]
      if (target) addLine('load', 'input', grp.key, t, ids, {}, () => flowCurve([grp.x, grp.y], target.in, f, 16))
    }
  }
  // between stage columns (a skip line jumps a column), and from the rules engine to the destinations
  const toClear = (from) => {
    if (!B.clearVia) return flowCurve(from.out, clearEntry, f, 16)
    const c = flowCurve(from.out, B.clearVia, f, 16)
    return { d: `${c.d}L${fmt(clearEntry[0])} ${fmt(clearEntry[1])}`, pts: [...c.pts, clearEntry] }
  }
  for (const r of records) {
    if (!r.route) continue
    for (const band of ['extraction', 'timeline', 'verdict']) {
      for (const ln of r.route.lines[band].values()) {
        const na = node[ln.fromCol]?.[ln.from], nb = node[band][ln.to]
        if (na && nb) addLine(band, ln.fromCol, ln.from, ln.to, [r.id], { aside: Boolean(ln.aside) }, () => flowCurve(na.out, nb.in, f, 16))
      }
    }
    for (const ln of r.route.lines.outcome.values()) {
      const from = node.verdict[ln.from]
      if (!from) continue
      if (ln.cluster === 'clear') { addLine('outcome', 'verdict', ln.from, ln.to, [r.id], { cluster: 'clear' }, () => toClear(from)); continue }
      const hub = clusters[ln.cluster]?.hubs.find((x) => x.key === ln.hub)
      if (hub) addLine('outcome', 'verdict', ln.from, ln.to, [r.id], { cluster: ln.cluster, hub: ln.hub }, () => flowCurve(from.out, [hub.x - 4.5, hub.y], f, 16))
    }
  }
  const lines = [...lineMap.values()]

  // Could not run: stacked after the last node of the stage that stopped.
  const error = { nodes: [] }
  const stacks = {}
  for (const r of by('error')) {
    const gate = gates.find((x) => x.key === r.failedStage) || gates[0]
    const col = columns.find((c) => c.key === gate.key)
    const last = col.nodes[col.nodes.length - 1]
    const k = (stacks[gate.key] = (stacks[gate.key] || 0) + 1) - 1
    const p = h ? [last.x, last.y + 34 + k * 13] : [last.x + 30 + k * 13, last.y]
    const n = { key: `err:${r.id}`, ids: [r.id], x: p[0], y: p[1], gate: gate.key }
    error.nodes.push(n)
    nodeOf.outcome[r.id] = n
  }
  clusters.error = error

  return { W: B.W, H: B.H, orientation, gates, spine, columns, node, input, lines, byCase, clusters, nodeOf, r: Math.min(g.r, 4.5) }
}

/** A destination with a hub per finding type and each case fanned out from its hub. */
function hubCluster(name, records, box, size) {
  const titleH = 84 // room for the title, its line and, when asked for, the numbers
  const hubX = box.x + 7
  // A hub for every finding type any case here has (also a second type, reached by its own line).
  const present = HUBS[name].filter(([key]) => records.some((r) => r.hubs.includes(key)))
  const members = present.map(([key, label]) => ({ key, label, ids: records.filter((r) => r.hubs[0] === key).map((r) => r.id) }))
  const gridX = box.x + 30
  const gridW = box.x + box.w - gridX
  let step = 16
  const rowsOf = (m, cols) => Math.max(1, Math.ceil(Math.ceil(m.ids.length / size) / cols))
  const fit = () => members.reduce((sum, m) => sum + 18 + rowsOf(m, Math.max(1, Math.floor(gridW / step))) * step + 8, 0)
  while (step > 7 && fit() > box.h - titleH) step -= 1
  const cols = Math.max(1, Math.floor(gridW / step))
  let y = box.y + titleH
  const hubs = []
  const nodes = []
  const extra = []
  for (const m of members) {
    const grps = groups(m.ids, size, `${name}:${m.key}`)
    const rows = rowsOf(m, cols)
    const top = y + 18
    const hub = { key: m.key, label: m.label, x: hubX, y: top + ((rows - 1) * step) / 2, labelAt: [gridX - step * 0.3, y + 9] }
    hubs.push(hub)
    grps.forEach((grp, i) => {
      const p = [gridX + (i % cols) * step + step / 2, top + Math.floor(i / cols) * step]
      const spoke = cubic([hub.x, hub.y], [hub.x + 14, hub.y], [p[0] - 14, p[1]], p, 8)
      nodes.push({ ...grp, x: p[0], y: p[1], hub: m.key, cluster: name, spoke })
    })
    y = top + rows * step + 8
  }
  // A case whose two fields fall under different finding types is also wired to its second hub.
  for (const r of records) {
    for (const key of r.hubs.slice(1)) {
      const hub = hubs.find((x) => x.key === key)
      const n = nodes.find((x) => x.ids.includes(r.id))
      if (hub && n) extra.push({ key: `${r.id}-${key}`, id: r.id, hub: key, ...cubic([hub.x, hub.y], [hub.x + 14, hub.y], [n.x - 14, n.y], [n.x, n.y], 8) })
    }
  }
  return { name, box, hubs, nodes, extra, step, r: Math.max(2, Math.min(4.5, step * 0.28)), title: [box.x, box.y] }
}

const MAX_PATHS = 6

/** Up to MAX_PATHS of a list, spread evenly. */
function spread(list) {
  if (list.length <= MAX_PATHS) return list
  return Array.from({ length: MAX_PATHS }, (_, i) => list[Math.round((i * (list.length - 1)) / (MAX_PATHS - 1))])
}

/**
 * The paths a signal follows for one hop of one case: one per line the case really took into
 * the next column. A hop with no line (nothing to carry, or a stage that stopped) follows the spine.
 */
export function hopPaths(L, id, from, to) {
  const band = to
  const refs = L.byCase[id]?.[band] || []
  if (band === 'outcome') {
    const n = L.nodeOf.outcome[id]
    if (!n || n.gate) return []
    return spread(refs.map((ln) => {
      if (ln.cluster === 'clear') return n.fromEntry ? [...ln.pts, ...n.fromEntry.pts] : ln.pts
      if (n.hub === ln.hub) return [...ln.pts, ...n.spoke.pts]
      const second = L.clusters[ln.cluster]?.extra.find((x) => x.id === id && x.hub === ln.hub)
      return second ? [...ln.pts, ...second.pts] : ln.pts
    }))
  }
  if (refs.length) return spread(refs.map((ln) => ln.pts))
  const s = L.spine.find((x) => x.from === from && x.to === to)
  return s ? [s.pts] : []
}
