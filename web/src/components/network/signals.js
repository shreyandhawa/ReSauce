// Moving signals on the stage: one canvas above the SVG, so hundreds of dots stay cheap.
// A signal is one record travelling one line of one hop of its real path (lib/runner.js decides
// when; layout.js hopPaths gives one path per line the record took, so its signal splits).
// Show progress / connect cause and effect: the dot leaves when the real stage result is in and
// arrives where that result sends it. Position follows the strong ease-in-out curve (moving on
// screen); a short trail encodes direction and speed. Under reduced motion nothing travels.

import { reducedMotion } from '../../lib/motion.js'

function cubicBezier(p1x, p1y, p2x, p2y) {
  const cx = 3 * p1x, bx = 3 * (p2x - p1x) - cx, ax = 1 - cx - bx
  const cy = 3 * p1y, by = 3 * (p2y - p1y) - cy, ay = 1 - cy - by
  const sx = (t) => ((ax * t + bx) * t + cx) * t
  const sy = (t) => ((ay * t + by) * t + cy) * t
  const dx = (t) => (3 * ax * t + 2 * bx) * t + cx
  const solve = (x) => {
    let t = x
    for (let i = 0; i < 8; i++) {
      const e = sx(t) - x
      if (Math.abs(e) < 1e-5) return t
      const d = dx(t)
      if (Math.abs(d) < 1e-6) break
      t -= e / d
    }
    let lo = 0, hi = 1
    t = x
    while (hi - lo > 1e-6) {
      const v = sx(t)
      if (Math.abs(v - x) < 1e-5) return t
      if (x > v) lo = t; else hi = t
      t = (lo + hi) / 2
    }
    return t
  }
  return (x) => (x <= 0 ? 0 : x >= 1 ? 1 : sy(solve(x)))
}

const easeMove = cubicBezier(0.77, 0, 0.175, 1) // --ease-in-out in styles.css
const easeOut = cubicBezier(0.23, 1, 0.32, 1) // --ease-out
const MAX = 240 // signals drawn at once; past that a hop moves its mark without a signal (none is cut off mid-flight)
const TRAIL = 7
const RING_MS = 420 // a stage node flashes when a signal reaches it

export function createSignals(canvas) {
  const ctx = canvas.getContext('2d')
  const active = []
  const rings = []
  let view = { k: 1, s: 1, x: 0, y: 0 }
  let colors = { signal: '#fff' }
  let raf = 0
  let size = [0, 0, 1]

  const point = (sig, d) => {
    const { pts, lens } = sig
    if (d <= 0) return pts[0]
    let i = 1
    while (i < lens.length - 1 && lens[i] < d) i++
    const span = lens[i] - lens[i - 1] || 1
    const t = Math.min(1, (d - lens[i - 1]) / span)
    return [pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * t, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * t]
  }

  function fit() {
    const dpr = window.devicePixelRatio || 1
    const w = canvas.clientWidth, h = canvas.clientHeight
    if (w !== size[0] || h !== size[1] || dpr !== size[2]) {
      canvas.width = Math.round(w * dpr)
      canvas.height = Math.round(h * dpr)
      size = [w, h, dpr]
    }
    return dpr
  }

  function frame(now) {
    raf = 0
    const dpr = fit()
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    ctx.clearRect(0, 0, size[0], size[1])
    ctx.translate(view.x, view.y)
    ctx.scale(view.k * view.s, view.k * view.s)
    // Arrival: an expanding, fading ring where a signal reached a stage node (show progress).
    for (let n = rings.length - 1; n >= 0; n--) {
      const ring = rings[n]
      const p = (now - ring.t0) / RING_MS
      if (p >= 1) { rings.splice(n, 1); continue }
      const e = easeOut(p)
      ctx.globalAlpha = 0.75 * (1 - e)
      ctx.strokeStyle = colors[ring.kind] || colors.signal
      ctx.lineWidth = 1.6
      ctx.beginPath()
      ctx.arc(ring.x, ring.y, 7 + 9 * e, 0, Math.PI * 2)
      ctx.stroke()
    }
    for (let n = active.length - 1; n >= 0; n--) {
      const sig = active[n]
      const p = (now - sig.t0) / sig.ms
      if (p >= 1) {
        active.splice(n, 1)
        if (sig.ring && rings.length < MAX) { const end = sig.pts[sig.pts.length - 1]; rings.push({ x: end[0], y: end[1], t0: now, kind: sig.kind }) }
        continue
      }
      if (p < 0) continue // waiting for its delay
      const d = easeMove(Math.max(0, p)) * sig.total
      const speed = Math.min(1, Math.abs(easeMove(Math.min(1, p + 0.05)) - easeMove(p)) * 12) // trail grows with speed
      ctx.fillStyle = colors[sig.kind] || colors.signal
      for (let i = TRAIL; i >= 0; i--) {
        const q = point(sig, d - i * 2.6 * speed)
        ctx.globalAlpha = i === 0 ? 1 : 0.42 * (1 - i / (TRAIL + 1))
        ctx.beginPath()
        ctx.arc(q[0], q[1], i === 0 ? 3.2 : 2.6 * (1 - i / (TRAIL + 2)), 0, Math.PI * 2)
        ctx.fill()
      }
    }
    ctx.globalAlpha = 1
    if (active.length || rings.length) raf = requestAnimationFrame(frame)
  }

  return {
    /** pts: the path; ms: travel time; kind: colour; delay: ms before it leaves; ring: flash where it arrives. */
    add(pts, ms, kind, delay = 0, ring = false) {
      if (!pts || pts.length < 2 || active.length >= MAX || reducedMotion() || document.visibilityState !== 'visible') return
      const lens = [0]
      for (let i = 1; i < pts.length; i++) lens.push(lens[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
      active.push({ pts, lens, total: lens[lens.length - 1], t0: performance.now() + delay, ms, kind, ring })
      if (!raf) raf = requestAnimationFrame(frame)
    },
    setView(v) { view = v; if (!raf && (active.length || rings.length)) raf = requestAnimationFrame(frame) },
    setColors(c) { colors = c },
    destroy() { cancelAnimationFrame(raf); active.length = 0; rings.length = 0 },
  }
}
