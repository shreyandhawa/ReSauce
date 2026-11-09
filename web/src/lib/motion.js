// Motion helpers. Durations and curves are the tokens in styles.css (:root --dur-*, --ease-*) plus
// the springs that lib/spring.js writes onto :root (--ease-spring-*, --dur-spring-*), read here so
// CSS and the Web Animations API share one set. Every call site names its job in a comment.

const cssVar = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim()

export const reducedMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches
export const duration = (name) => parseFloat(cssVar(`--dur-${name}`)) || 0
export const easing = (name) => cssVar(`--ease-${name}`) || 'cubic-bezier(0.23, 1, 0.32, 1)'

const running = new WeakMap() // element -> its current animation, so a new one cancels the old

/**
 * Animate an element with the shared tokens. Interruptible: a new call on the same element
 * cancels the running one. Under reduced motion every transform, clip and blur (movement) is
 * dropped and only opacity or colour changes remain, shortened to the fast duration; a
 * movement-only animation is skipped.
 */
export function animate(el, keyframes, { dur = 'base', ease = 'out', delay = 0, fill = 'both' } = {}) {
  if (!el || typeof el.animate !== 'function') return null
  running.get(el)?.cancel()
  let frames = keyframes
  const reduced = reducedMotion()
  if (reduced) {
    frames = keyframes.map(({ transform, clipPath, filter, ...rest }) => rest) // eslint-disable-line no-unused-vars
    if (!frames.some((f) => Object.keys(f).some((k) => k !== 'offset' && k !== 'easing'))) return null
  }
  const animation = el.animate(frames, {
    duration: reduced ? Math.min(duration(dur), duration('fast')) : duration(dur),
    easing: reduced ? 'ease' : easing(ease),
    delay: reduced ? 0 : delay,
    fill,
  })
  running.set(el, animation)
  animation.finished.then(() => running.get(el) === animation && running.delete(el), () => {})
  return animation
}

// Where the last "open a case" click happened, so the case view can expand from it.
let origin = null
export const setOrigin = (rect) => { origin = rect ? { left: rect.left, top: rect.top, width: rect.width, height: rect.height } : null }
export const takeOrigin = () => { const o = origin; origin = null; return o }
export const hasOrigin = () => origin !== null
