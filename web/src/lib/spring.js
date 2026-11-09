// Springs described the way Apple describes them (damping ratio + response in seconds, from
// "Designing Fluid Interfaces"), turned into CSS linear() easings so CSS transitions and the
// Web Animations API can use them without a motion library. A spring has no fixed duration:
// the duration below is the moment it has settled to within 0.1% of its target.

function position(damping, response) {
  const w0 = (2 * Math.PI) / response
  if (damping >= 1) return (t) => 1 - Math.exp(-w0 * t) * (1 + w0 * t)
  const wd = w0 * Math.sqrt(1 - damping * damping)
  return (t) => 1 - Math.exp(-damping * w0 * t) * (Math.cos(wd * t) + ((damping * w0) / wd) * Math.sin(wd * t))
}

/** { easing: 'linear(…)', duration: ms } for a step from 0 to 1 starting at rest. */
export function springCurve({ damping = 1, response = 0.4 } = {}) {
  const x = position(damping, response)
  let settle = 0
  for (let t = 0; t < 4; t += 1 / 240) if (Math.abs(1 - x(t)) > 0.001) settle = t
  settle += 1 / 240
  const n = 40
  const points = []
  for (let i = 0; i <= n; i++) points.push(i === n ? 1 : +x((settle * i) / n).toFixed(4))
  return { easing: `linear(${points.join(', ')})`, duration: Math.round(settle * 1000) }
}

// The house springs. Critically damped (no overshoot) unless the motion carries momentum.
export const SPRINGS = {
  ui: { damping: 1, response: 0.3 },      // controls, labels, nodes settling
  move: { damping: 1, response: 0.42 },   // things travelling across the stage, zoom and pan
  sheet: { damping: 0.86, response: 0.36 }, // the inspector sheet (a drawer: Apple ships 0.8 / 0.3)
  land: { damping: 0.84, response: 0.34 }, // a record landing in its destination: the one slight overshoot, because it arrives with momentum
}

/** Write each spring onto :root as --ease-spring-<name> and --dur-spring-<name> (CSS reads them too). */
export function installSprings() {
  const supported = typeof CSS !== 'undefined' && CSS.supports?.('transition-timing-function', 'linear(0, 1)')
  const root = document.documentElement.style
  for (const [name, config] of Object.entries(SPRINGS)) {
    const { easing, duration } = springCurve(config)
    root.setProperty(`--ease-spring-${name}`, supported ? easing : 'cubic-bezier(0.23, 1, 0.32, 1)')
    root.setProperty(`--dur-spring-${name}`, `${supported ? duration : 320}ms`)
  }
}

/**
 * Drive a value with a critically damped spring on requestAnimationFrame, for motion that a
 * gesture or a new target can interrupt (zoom, pan). A new call on the same handle starts from
 * the value on screen now, so a retarget never jumps.
 */
export function springTo(handle, from, to, onUpdate, { response = SPRINGS.move.response } = {}) {
  cancelAnimationFrame(handle.raf)
  const w0 = (2 * Math.PI) / response
  const start = performance.now()
  const keys = Object.keys(to)
  const step = (now) => {
    const t = (now - start) / 1000
    const k = 1 - Math.exp(-w0 * t) * (1 + w0 * t)
    const value = {}
    for (const key of keys) value[key] = from[key] + (to[key] - from[key]) * k
    onUpdate(value)
    if (1 - k > 0.0005) handle.raf = requestAnimationFrame(step)
    else onUpdate(to)
  }
  handle.raf = requestAnimationFrame(step)
}
