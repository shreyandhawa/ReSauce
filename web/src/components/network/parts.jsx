import { memo } from 'react'

/**
 * One pipeline stage, at the head of its column. Its state comes from real results only: idle, active (records are inside
 * it now), done (every record of the run has passed it), error (a record stopped here).
 * The bar inside fills with the share of records that have passed (show progress, no number).
 */
export const Gate = memo(function Gate({ gate, state, progress, failed }) {
  const { w, h } = gate
  return (
    <g className="gate" data-state={state} transform={`translate(${gate.x} ${gate.y})`}>
      <rect className="gate-body" x={-w / 2} y={-h / 2} width={w} height={h} rx={h / 2} />
      <rect className="gate-bar" x={-w / 2 + 16} y={h / 2 - 9} width={w - 32} height={2.5} rx={1.25}
        style={{ transform: `scaleX(${Math.max(0, Math.min(1, progress))})` }} />
      <text className="gate-label" x={0} y={1} textAnchor="middle" dominantBaseline="middle">{gate.label}</text>
      {failed > 0 && (
        <g className="gate-fail" transform={`translate(${w / 2 - 4} ${-h / 2 + 4})`}>
          <circle r={8} />
          <path d="M-3 -3L3 3M3 -3L-3 3" />
        </g>
      )}
    </g>
  )
})

/** A record's mark: shape + colour per outcome (never colour alone). */
export function Mark({ outcome, r, decided, annotated, waiting }) {
  if (outcome === 'discrepancy') {
    const s = r * 1.3
    return <path className={`mark mark-discrepancy${decided ? ' is-decided' : ''}`} d={`M0 ${-s}L${s} 0L0 ${s}L${-s} 0Z`} />
  }
  if (outcome === 'review') {
    const s = r * 1.25
    return <path className={`mark mark-review${decided ? ' is-decided' : ''}`} d={`M0 ${-s}L${s * 0.95} ${s * 0.7}L${-s * 0.95} ${s * 0.7}Z`} />
  }
  if (outcome === 'clear') {
    return (
      <>
        <circle className="mark mark-clear" r={r} />
        {annotated && <circle className="mark-note" r={Math.max(1, r * 0.34)} />}
      </>
    )
  }
  if (outcome === 'error') {
    const s = r * 1.05
    return <path className="mark mark-error" d={`M${-s} ${-s}L${s} ${s}M${s} ${-s}L${-s} ${s}`} />
  }
  return <circle className={`mark mark-input${waiting ? ' is-waiting' : ''}`} r={r} />
}

/**
 * The grounded endpoint: a socket with a plug on the main line. Records without a detected
 * discrepancy converge into it; when the run is complete the plug seats (connect cause and effect).
 */
export function Socket({ socket, orientation, state }) {
  return (
    <g className="socket" data-state={state} transform={`translate(${socket.x} ${socket.y})`}>
      <circle className="socket-halo" r={34} />
      <g transform={orientation === 'v' ? 'rotate(90)' : undefined}>
        <g className="plug">
          <rect className="plug-body" x={-54} y={-9} width={18} height={18} rx={4} />
          <path className="plug-prong" d="M-36 -5H-20M-36 5H-20" />
        </g>
      </g>
      <rect className="socket-plate" x={-24} y={-24} width={48} height={48} rx={14} />
      <circle className="socket-face" r={14.5} />
      <rect className="socket-slot" x={-7} y={-7} width={3.2} height={9} rx={1.6} />
      <rect className="socket-slot" x={3.8} y={-7} width={3.2} height={9} rx={1.6} />
      <circle className="socket-slot" cy={7} r={2.2} />
    </g>
  )
}

/**
 * The red warning beacon. Turns slowly (a rotating light, no strobe: one sweep every 2.6 s) while
 * any discrepancy has no review decision yet; still once every one is decided, or when paused.
 */
export function Beacon({ spinning }) {
  return (
    <span className="beacon" data-spin={spinning ? '' : undefined} aria-hidden="true">
      <span className="beacon-sweep" />
      <span className="beacon-lamp" />
    </span>
  )
}
