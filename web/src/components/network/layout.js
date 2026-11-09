// Where everything on the pipeline stage goes. A pure function of the records and the orientation:
// no React, no DOM. Input → Load → Extraction → Timeline → Rules engine → three destinations.
// Horizontal on wide screens; on narrow screens the same flow runs top to bottom.
//
// Each node is one case. Above MAX_NODES cases per area, nodes become groups of cases (aggregation)
// so a large dataset stays legible; a group opens as a list in the inspector.

import { STAGES } from '../../lib/runner.js'
import { HUBS } from '../../lib/outcome.js'

const MAX_NODES = 400
const GATE_W = 116
const GATE_H = 44

const BOXES = {
  h: {
    W: 1250, H: 690, flow: [1, 0],
    input: { x: 40, y: 118, w: 236, h: 470 }, inputLabel: [40, 64],
    gates: [410, 575, 740, 905].map((u) => [u, 352]),
    discrepancy: { x: 1004, y: 8, w: 236, h: 256 },
    review: { x: 1004, y: 424, w: 236, h: 260 },
    clear: { x: 1012, y: 340, w: 104, h: 50 }, clearLabel: [1004, 272],
    socket: [1210, 352],
    errorStep: [0, 13], errorFrom: [0, 48],
  },
  v: {
    W: 420, H: 1330, flow: [0, 1],
    input: { x: 28, y: 96, w: 364, h: 196 }, inputLabel: [28, 22],
    gates: [372, 462, 552, 642].map((u) => [210, u]),
    discrepancy: { x: 8, y: 712, w: 196, h: 344 },
    review: { x: 216, y: 712, w: 196, h: 344 },
    clear: { x: 118, y: 1150, w: 184, h: 50 }, clearLabel: [118, 1076],
    socket: [210, 1280],
    errorStep: [13, 0], errorFrom: [74, 0],
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
 * records: [{ id, outcome, hubs, failedStage }] in display order.
 */
export function layout(records, orientation = 'h') {
  const B = BOXES[orientation]
  const f = B.flow
  const size = Math.max(1, Math.ceil(records.length / MAX_NODES))
  const half = orientation === 'h' ? GATE_W / 2 : GATE_H / 2

  // Gates, with the points where a path enters and leaves each one.
  const gates = STAGES.map(([key, label], i) => {
    const c = B.gates[i]
    return { key, label, x: c[0], y: c[1], w: GATE_W, h: GATE_H, in: add(c, f, -half), out: add(c, f, half) }
  })
  const first = gates[0]
  const last = gates[gates.length - 1]

  // Input: every case, as imported.
  const inputGroups = groups(records.map((r) => r.id), size, 'in')
  const g = grid(inputGroups.length, B.input)
  // The label sits just above the grid it names (the grid is centred in its box).
  const gridTop = g.pts.length ? Math.min(...g.pts.map((p) => p[1])) : B.input.y + B.input.h * 0.3
  const input = { box: B.input, label: [B.inputLabel[0], Math.max(B.inputLabel[1], gridTop - 84)], r: g.r, nodes: [] }
  const nodeOf = { outcome: {} }
  const inputCurves = {}
  inputGroups.forEach((grp, i) => {
    const p = g.pts[i]
    input.nodes.push({ ...grp, x: p[0], y: p[1] })
    const reach = Math.abs((first.in[0] - p[0]) * f[0] + (first.in[1] - p[1]) * f[1])
    const curve = cubic(p, add(p, f, reach * 0.42), add(first.in, f, -reach * 0.5), first.in)
    for (const id of grp.ids) inputCurves[id] = curve
    inputCurves[grp.key] = curve
  })

  const gateLinks = gates.slice(1).map((gate, i) => ({ key: `${gates[i].key}-${gate.key}`, from: gates[i].key, to: gate.key, ...line(gates[i].out, gate.in) }))

  // Destinations.
  const by = (o) => records.filter((r) => r.outcome === o)
  const clusters = {
    discrepancy: hubCluster('discrepancy', by('discrepancy'), B.discrepancy, size, orientation),
    review: hubCluster('review', by('review'), B.review, size, orientation),
  }
  const branches = {}
  for (const name of ['discrepancy', 'review']) {
    const c = clusters[name]
    const reach = Math.abs((c.port[0] - last.out[0]) * f[0] + (c.port[1] - last.out[1]) * f[1])
    branches[name] = cubic(last.out, add(last.out, f, reach * 0.55), add(c.port, f, -reach * 0.45), c.port, 22)
  }

  // No discrepancy: a compact grid on the main line, every node wired to the socket.
  const socket = { x: B.socket[0], y: B.socket[1], in: add(B.socket, f, -60) } // the wires end at the back of the plug
  const clearGroups = groups(by('clear').map((r) => r.id), size, 'clear')
  const cg = grid(clearGroups.length, B.clear, 14)
  const clearEntry = orientation === 'h' ? [B.clear.x - 6, last.out[1]] : [last.out[0], B.clear.y - 6]
  branches.clear = line(last.out, clearEntry)
  const clear = { box: B.clear, r: cg.r, entry: clearEntry, socket, label: B.clearLabel, nodes: [] }
  clearGroups.forEach((grp, i) => {
    const p = cg.pts[i]
    const node = { ...grp, x: p[0], y: p[1], toSocket: cubic(p, add(p, f, 14), add(socket.in, f, -18), socket.in, 10), fromEntry: line(clearEntry, p) }
    clear.nodes.push(node)
    for (const id of grp.ids) nodeOf.outcome[id] = node
  })
  clusters.clear = clear
  for (const name of ['discrepancy', 'review']) for (const n of clusters[name].nodes) for (const id of n.ids) nodeOf.outcome[id] = n

  // Could not run: stacked beside the stage that stopped.
  const error = { nodes: [] }
  const stacks = {}
  for (const r of by('error')) {
    const gate = gates.find((x) => x.key === r.failedStage) || first
    const k = (stacks[gate.key] = (stacks[gate.key] || 0) + 1) - 1
    const p = add(add([gate.x, gate.y], B.errorFrom), B.errorStep, k)
    const node = { key: `err:${r.id}`, ids: [r.id], x: p[0], y: p[1], gate: gate.key }
    error.nodes.push(node)
    nodeOf.outcome[r.id] = node
  }
  clusters.error = error

  return { W: B.W, H: B.H, orientation, gates, input, inputCurves, gateLinks, branches, clusters, nodeOf, r: Math.min(g.r, 4.5) }
}

/** A destination with a bus, a hub per finding type and each case fanned out from its hub. */
function hubCluster(name, records, box, size, orientation) {
  const titleH = 70 // room for the title, its line and, when asked for, the numbers
  const busX = box.x + 7
  const present = HUBS[name].filter(([key]) => records.some((r) => r.hubs[0] === key))
  const members = present.map(([key, label]) => ({ key, label, ids: records.filter((r) => r.hubs[0] === key).map((r) => r.id) }))
  const gridX = box.x + 30
  const gridW = box.x + box.w - gridX
  let step = 16
  const fit = () => members.reduce((h, m) => h + 18 + Math.ceil(Math.ceil(m.ids.length / size) / Math.max(1, Math.floor(gridW / step))) * step + 8, 0)
  while (step > 7 && fit() > box.h - titleH) step -= 1
  const cols = Math.max(1, Math.floor(gridW / step))
  let y = box.y + titleH
  const hubs = []
  const nodes = []
  const extra = []
  for (const m of members) {
    const grps = groups(m.ids, size, `${name}:${m.key}`)
    const rows = Math.ceil(grps.length / cols)
    const top = y + 18
    const hub = { key: m.key, label: m.label, x: busX, y: top + ((rows - 1) * step) / 2, labelAt: [gridX - step * 0.3, y + 9] }
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
      const hub = hubs.find((h) => h.key === key)
      const node = nodes.find((n) => n.ids.includes(r.id))
      if (hub && node) extra.push({ key: `${r.id}-${key}`, id: r.id, ...cubic([hub.x, hub.y], [hub.x + 14, hub.y], [node.x - 14, node.y], [node.x, node.y], 8) })
    }
  }
  const busTop = hubs.length ? hubs[0].y : box.y + titleH + 20
  const busBottom = hubs.length ? hubs[hubs.length - 1].y : busTop
  const port = orientation === 'h' ? [busX, (busTop + busBottom) / 2] : [busX, busTop]
  return {
    name, box, hubs, nodes, extra, port, step, r: Math.max(2, Math.min(4.5, step * 0.28)),
    bus: hubs.length > 1 ? line([busX, busTop], [busX, busBottom]) : null,
    title: [box.x, box.y],
  }
}

/** The points a signal follows for one hop of one case. */
export function hopPoints(L, id, from, to) {
  if (from === 'input') return L.inputCurves[id]?.pts || null
  const link = L.gateLinks.find((x) => x.from === from && x.to === to)
  if (link) return link.pts
  if (to !== 'outcome') return null
  const node = L.nodeOf.outcome[id]
  if (!node) return null
  const last = L.gates[L.gates.length - 1]
  if (node.spoke) {
    const cluster = L.clusters[node.cluster]
    const hub = cluster.hubs.find((h) => h.key === node.hub)
    return [...L.branches[cluster.name].pts, [cluster.port[0], cluster.port[1]], [hub.x, hub.y], ...node.spoke.pts]
  }
  if (node.fromEntry) return [last.out, ...node.fromEntry.pts]
  return null
}
