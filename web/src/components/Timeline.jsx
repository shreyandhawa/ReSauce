import { OBS_KINDS, TIME_SOURCES, signedDay } from '../lib/format.js'

const LANES = [
  ['ICE score', ['ice_total', 'ice_partial']],
  ['Consciousness', ['consciousness']],
  ['Seizure, EEG', ['seizure', 'eeg_finding']],
  ['Motor, raised ICP', ['motor_finding', 'icp_sign', 'text_only_icp_sign']],
  ['Other symptoms', ['excluded_symptom', 'ungradeable_symptom', 'unrecognised']],
  ['Context', ['competing_cause', 'attribution', 'assessment_barrier', 'not_assessable', 'out_of_scope_mention']],
]
const W = 760
const LEFT = 150
const RIGHT = W - 16
const LANE_H = 38
const TOP = 34

function hours(isoDateTime) {
  const m = /T(\d{2}):(\d{2})/.exec(isoDateTime || '')
  return m ? (Number(m[1]) + Number(m[2]) / 60) / 24 : 0.5
}
function timeFraction(hhmm) {
  if (!hhmm) return 0.5
  const [h, m] = hhmm.split(':').map(Number)
  return (h + m / 60) / 24
}

/**
 * Observations on the Day 0 … Day +N axis: a mark at the event time and a tick at the
 * documentation time, joined by a hairline, so the gap between them is visible.
 */
export default function Timeline({ observations, window: win, recordOnsetDay, documentedOnset, onPick }) {
  const start = win.start_day
  const end = win.end_day + 1
  const x = (d) => LEFT + ((Math.min(Math.max(d, start), end) - start) / (end - start)) * (RIGHT - LEFT)

  const unresolved = observations.filter((o) => o.event_day == null)
  const outside = observations.filter((o) => o.event_day != null && (o.event_day < win.start_day || o.event_day > win.end_day))
  const placed = observations.filter((o) => o.event_day != null && o.event_day >= win.start_day && o.event_day <= win.end_day)
  const lanes = LANES.map(([label, kinds]) => [label, placed.filter((o) => kinds.includes(o.kind))]).filter(([, list]) => list.length)
  const known = new Set(LANES.flatMap(([, k]) => k))
  const other = placed.filter((o) => !known.has(o.kind))
  if (other.length) lanes.push(['Other', other])

  const H = TOP + lanes.length * LANE_H + 52
  const ticks = []
  for (let d = start; d <= win.end_day; d++) ticks.push(d)
  const docOnset = documentedOnset?.study_day ?? documentedOnset?.study_days?.[0]
  const docOnsetEnd = documentedOnset?.study_days?.[1]
  let i = 0

  return (
    <figure className="timeline">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Timeline of ${placed.length} observations from ${signedDay(win.start_day)} to ${signedDay(win.end_day)}. Marks show event time, ticks documentation time.`}>
        {ticks.map((d) => (
          <g key={d} className={d % 7 === 0 ? 'tl-tick tl-tick-major' : 'tl-tick'}>
            <line x1={x(d)} x2={x(d)} y1={TOP - 6} y2={H - 48} />
            {(d % 7 === 0 || d === win.end_day) && <text x={x(d) + 3} y={TOP - 12}>{d === 0 ? 'Day 0' : `+${d}`}</text>}
          </g>
        ))}
        <line className="tl-axis" x1={LEFT} x2={RIGHT} y1={H - 48} y2={H - 48} pathLength="1" />

        {docOnset != null && (
          <g className="tl-onset tl-onset-doc">
            <rect x={x(docOnset)} width={Math.max(2, x((docOnsetEnd ?? docOnset) + 1) - x(docOnset))} y={TOP - 6} height={H - TOP - 42} />
            <text x={x(docOnset)} y={H - 28}>documented onset (ReSauce) {signedDay(docOnset)}</text>
          </g>
        )}
        {recordOnsetDay != null && (
          <g className="tl-onset tl-onset-record">
            <line x1={x(recordOnsetDay + 0.5)} x2={x(recordOnsetDay + 0.5)} y1={TOP - 6} y2={H - 48} />
            <text x={x(recordOnsetDay + 0.5)} y={H - 8}>record onset {signedDay(recordOnsetDay)}</text>
          </g>
        )}

        {lanes.map(([label, list], laneIndex) => {
          const y = TOP + laneIndex * LANE_H + LANE_H / 2
          return (
            <g key={label} className="tl-lane">
              <text className="tl-lane-label" x={0} y={y + 4}>{label}</text>
              <line className="tl-lane-rule" x1={LEFT} x2={RIGHT} y1={y + LANE_H / 2} y2={y + LANE_H / 2} />
              {list.map((o, k) => {
                const ex = x(o.event_day + (o.event_time ? timeFraction(o.event_time) : 0.5))
                const dx = x(o.documented_day + hours(o.documented_at))
                const jy = y + ((k % 3) - 1) * 7
                const range = o.event_day_end != null && o.event_day_end !== o.event_day
                const label2 = `${OBS_KINDS[o.kind] || o.kind}${o.value != null ? `: ${typeof o.value === 'object' ? JSON.stringify(o.value) : o.value}` : ''} — ${o.status}; event ${o.event_date}${o.event_time ? ' ' + o.event_time : ''} (${TIME_SOURCES[o.time_source] || o.time_source}); documented ${o.documented_at.replace('T', ' ')}`
                return (
                  <g
                    key={o.id}
                    className={`tl-obs tl-${o.status} tl-k-${o.kind}`}
                    style={{ '--i': i++ }}
                    tabIndex={0}
                    role="button"
                    aria-label={label2}
                    onClick={() => onPick(o)}
                    onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onPick(o) } }}
                  >
                    <title>{label2}</title>
                    <line className="tl-lag" x1={ex} x2={dx} y1={jy} y2={jy} />
                    <line className="tl-doc" x1={dx} x2={dx} y1={jy - 5} y2={jy + 5} />
                    {range ? (
                      <rect className="tl-mark" x={x(o.event_day)} width={x(o.event_day_end + 1) - x(o.event_day)} y={jy - 4} height={8} rx={4} />
                    ) : (
                      <circle className="tl-mark" cx={ex} cy={jy} r={5} />
                    )}
                  </g>
                )
              })}
            </g>
          )
        })}
      </svg>
      <figcaption>
        <span className="tl-key tl-key-present">present</span>
        <span className="tl-key tl-key-absent">absent</span>
        <span className="tl-key tl-key-uncertain">uncertain</span>
        <span className="tl-key tl-key-doc">documentation time</span>
        <span>Marks sit at the event time; the hairline runs to when it was written down.</span>
      </figcaption>
      {(unresolved.length > 0 || outside.length > 0) && (
        <ul className="tl-off">
          {unresolved.map((o) => (
            <li key={o.id}><button type="button" className="linkish" onClick={() => onPick(o)}>{OBS_KINDS[o.kind]}: event time unresolved</button> — documented {o.documented_at.replace('T', ' ')}</li>
          ))}
          {outside.map((o) => (
            <li key={o.id}><button type="button" className="linkish" onClick={() => onPick(o)}>{OBS_KINDS[o.kind]}: {signedDay(o.event_day)}</button> — event date outside the observation window (see the flags in the verdict)</li>
          ))}
        </ul>
      )}
    </figure>
  )
}
