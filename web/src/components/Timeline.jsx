import { OBS_KINDS, TIME_SOURCES, signedDay } from '../lib/format.js'

const LANES = [
  ['ICE score', ['ice_total', 'ice_partial']],
  ['Consciousness', ['consciousness']],
  ['Seizure, EEG', ['seizure', 'eeg_finding']],
  ['Motor, raised ICP', ['motor_finding', 'icp_sign', 'text_only_icp_sign']],
  ['Other symptoms', ['excluded_symptom', 'ungradeable_symptom', 'unrecognised']],
  ['Context', ['competing_cause', 'attribution', 'assessment_barrier', 'not_assessable', 'out_of_scope_mention']],
]
const W = 520
const LEFT = 104
const RIGHT = W - 8
const LANE_H = 30
const TOP = 22

const fraction = (hhmm) => {
  if (!hhmm) return 0.5
  const [h, m] = hhmm.split(':').map(Number)
  return (h + m / 60) / 24
}
const docFraction = (iso) => fraction((/T(\d{2}:\d{2})/.exec(iso || '') || [])[1])

/**
 * Observations on the observation window, always the same scale (Day 0 to the window end), so cases
 * compare at a glance. A mark sits at the event time; a short tick at the documentation time,
 * joined by a dotted line. Hovering links an event with its text; selecting jumps to its quote.
 */
export default function Timeline({ observations, use, window: win, recordOnsetDay, documentedOnset, hot, onHover, onPick, revealing }) {
  const start = win.start_day
  const end = win.end_day + 1
  const x = (d) => LEFT + ((Math.min(Math.max(d, start), end) - start) / (end - start)) * (RIGHT - LEFT)
  const inWindow = (o) => o.event_day != null && o.event_day >= win.start_day && o.event_day <= win.end_day
  const placed = observations.filter(inWindow)
  const unresolved = observations.filter((o) => o.event_day == null)
  const outside = observations.filter((o) => o.event_day != null && !inWindow(o))

  const known = new Set(LANES.flatMap(([, k]) => k))
  const lanes = LANES.map(([label, kinds]) => [label, placed.filter((o) => kinds.includes(o.kind))]).filter(([, l]) => l.length)
  const other = placed.filter((o) => !known.has(o.kind))
  if (other.length) lanes.push(['Other', other])

  // Show progress: the drop-in order follows event time, earliest first.
  const order = new Map([...placed].sort((a, b) => (a.event_day + fraction(a.event_time)) - (b.event_day + fraction(b.event_time))).map((o, i) => [o.id, i]))
  const H = TOP + Math.max(lanes.length, 1) * LANE_H + 34
  const ticks = []
  for (let d = start; d <= win.end_day; d++) ticks.push(d)
  const docOnset = documentedOnset?.study_day ?? documentedOnset?.study_days?.[0]
  const docOnsetEnd = documentedOnset?.study_days?.[1]

  const label = (o) => `${OBS_KINDS[o.kind] || o.kind}${o.value != null ? `: ${typeof o.value === 'object' ? JSON.stringify(o.value) : o.value}` : ''}, ${o.status}; event ${o.event_date}${o.event_time ? ' ' + o.event_time : ''} (${TIME_SOURCES[o.time_source] || o.time_source}); documented ${o.documented_at.replace('T', ' ')}${use && use[o.id] !== 'used' ? `; not used by the rules (${(use[o.id] || '').replace(/_/g, ' ')})` : ''}`

  return (
    <figure className={`timeline${revealing ? ' revealing' : ''}`}>
      <svg viewBox={`0 0 ${W} ${H}`} role="group" aria-label={`Timeline, ${signedDay(win.start_day)} to ${signedDay(win.end_day)}: ${placed.length} observations. Marks are event time; ticks are documentation time.`}>
        {ticks.map((d) => (
          <g key={d} className={d % 7 === 0 ? 'tl-tick tl-tick-major' : 'tl-tick'}>
            <line x1={x(d)} x2={x(d)} y1={TOP - 4} y2={H - 30} />
            {(d % 7 === 0 || d === win.end_day) && <text x={x(d) + 2} y={TOP - 9}>{d === 0 ? 'Day 0' : `+${d}`}</text>}
          </g>
        ))}
        <line className="tl-axis" x1={LEFT} x2={RIGHT} y1={H - 30} y2={H - 30} />
        {docOnset != null && (
          <g className="tl-doc-onset">
            <rect x={x(docOnset)} width={Math.max(2, x((docOnsetEnd ?? docOnset) + 1) - x(docOnset))} y={TOP - 4} height={H - TOP - 26} />
            <text className="tl-label" x={x(docOnset)} y={H - 16}>documented onset {signedDay(docOnset)}</text>
          </g>
        )}
        {recordOnsetDay != null && (
          <g className="tl-record">
            <line x1={x(recordOnsetDay + 0.5)} x2={x(recordOnsetDay + 0.5)} y1={TOP - 4} y2={H - 30} />
            <text className="tl-label" x={x(recordOnsetDay + 0.5)} y={H - 3}>record onset {signedDay(recordOnsetDay)}</text>
          </g>
        )}
        {lanes.map(([name, list], laneIndex) => {
          const y = TOP + laneIndex * LANE_H + LANE_H / 2
          return (
            <g key={name}>
              <text className="tl-lane-label" x={0} y={y + 4}>{name}</text>
              {list.map((o, k) => {
                const ex = x(o.event_day + (o.event_time ? fraction(o.event_time) : 0.5))
                const dx = x(o.documented_day + docFraction(o.documented_at))
                const jy = y + ((k % 3) - 1) * 6
                const range = o.event_day_end != null && o.event_day_end !== o.event_day
                return (
                  <g key={o.id} className={`tl-obs tl-${o.status}${hot === o.id ? ' is-hot' : ''}`} style={{ '--t': order.get(o.id) }}
                    tabIndex={0} role="button" aria-label={label(o)}
                    onMouseEnter={() => onHover(o.id)} onMouseLeave={() => onHover(null)}
                    onFocus={() => onHover(o.id)} onBlur={() => onHover(null)}
                    onClick={() => onPick(o)} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onPick(o) } }}>
                    <title>{label(o)}</title>
                    <line className="tl-lag" x1={ex} x2={dx} y1={jy} y2={jy} />
                    <line className="tl-doc" x1={dx} x2={dx} y1={jy - 4} y2={jy + 4} />
                    {range
                      ? <rect className="tl-mark" x={x(o.event_day)} width={x(o.event_day_end + 1) - x(o.event_day)} y={jy - 3.5} height={7} rx={3.5} />
                      : <circle className="tl-mark" cx={ex} cy={jy} r={4.5} />}
                  </g>
                )
              })}
            </g>
          )
        })}
      </svg>
      <figcaption className="tl-key">
        <span><svg width="10" height="10" aria-hidden="true"><circle cx="5" cy="5" r="4" fill="var(--mark-obs-line)" /></svg>present</span>
        <span><svg width="10" height="10" aria-hidden="true"><circle cx="5" cy="5" r="4" fill="none" stroke="var(--ink-3)" strokeWidth="1.5" /></svg>absent</span>
        <span><svg width="10" height="10" aria-hidden="true"><circle cx="5" cy="5" r="4" fill="var(--ink-3)" /></svg>uncertain</span>
        <span><svg width="14" height="10" aria-hidden="true"><path d="M1 5h8M11 1v8" stroke="var(--ink-2)" strokeWidth="1.5" strokeDasharray="2 2" /></svg>to documentation time</span>
        <span><svg width="10" height="12" aria-hidden="true"><path d="M5 0v12" stroke="var(--ink)" strokeWidth="1.5" strokeDasharray="3 3" /></svg>record onset</span>
      </figcaption>
      {(unresolved.length > 0 || outside.length > 0) && (
        <ul className="tl-off">
          {unresolved.map((o) => (
            <li key={o.id}><button type="button" className="linkish" onClick={() => onPick(o)}>{OBS_KINDS[o.kind] || o.kind}</button>: event time unresolved; documented {o.documented_at.replace('T', ' ')}</li>
          ))}
          {outside.map((o) => (
            <li key={o.id}><button type="button" className="linkish" onClick={() => onPick(o)}>{OBS_KINDS[o.kind] || o.kind}</button>: {signedDay(o.event_day)}, outside the observation window</li>
          ))}
        </ul>
      )}
    </figure>
  )
}
