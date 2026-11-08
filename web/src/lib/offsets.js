// Evidence offsets from the Python core are 0-based, end-exclusive indices into Unicode
// code points (Python str indices). JavaScript strings index UTF-16 code units, which differ
// for characters outside the Basic Multilingual Plane. Everything here works on code points.

/** The text between two code-point offsets. */
export function sliceCodePoints(text, start, end) {
  return Array.from(text).slice(start, end).join('')
}

/**
 * Split a text into runs for rendering highlights.
 * marks: [{ key, start, end, ... }] with code-point offsets; they may overlap.
 * Returns [{ text, start, end, marks: [mark, ...] }] covering the whole text, in order.
 */
export function segments(text, marks) {
  const points = Array.from(text)
  const valid = marks.filter((m) => m.start >= 0 && m.end <= points.length && m.start < m.end)
  const cuts = new Set([0, points.length])
  for (const m of valid) {
    cuts.add(m.start)
    cuts.add(m.end)
  }
  const sorted = [...cuts].sort((a, b) => a - b)
  const out = []
  for (let i = 0; i < sorted.length - 1; i++) {
    const start = sorted[i]
    const end = sorted[i + 1]
    out.push({
      text: points.slice(start, end).join(''),
      start,
      end,
      marks: valid.filter((m) => m.start <= start && m.end >= end),
    })
  }
  return out
}
