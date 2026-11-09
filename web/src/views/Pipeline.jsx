import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../api.js'
import { Loading, OutcomeSign, Problem } from '../components/Bits.jsx'
import CaseList from '../components/CaseList.jsx'
import Icon from '../components/Icon.jsx'
import Inspector from '../components/Inspector.jsx'
import Network from '../components/network/Network.jsx'
import { layout } from '../components/network/layout.js'
import { useLoad, useMedia } from '../lib/hooks.js'
import { HUB_NAMES, OUTCOMES, fromRow } from '../lib/outcome.js'
import { PATH, STAGES, pause, resume, showNow, start, useRunner } from '../lib/runner.js'

const FILTERS = [['all', 'All'], ['discrepancy', 'Discrepancy'], ['review', 'Needs review'], ['clear', 'No discrepancy'], ['not_run', 'Not verified']]
const remembered = { view: 'network', filter: { outcome: 'all', hub: null } }
let visited = false

function useNumbers() {
  const [on, setOn] = useState(() => { try { return localStorage.getItem('resauce-numbers') === '1' } catch { return false } })
  const toggle = useCallback(() => setOn((v) => {
    try { localStorage.setItem('resauce-numbers', v ? '0' : '1') } catch { /* storage blocked: lasts for this visit */ }
    return !v
  }), [])
  return [on, toggle]
}

export default function Pipeline({ workspace, arrivals, onArrived, onChanged, onImport }) {
  const cases = useLoad(() => api.cases(), [])
  const runner = useRunner()
  const narrow = useMedia('(max-width: 760px)')
  const [numbers, toggleNumbers] = useNumbers()
  const [view, setView] = useState(remembered.view)
  const [filter, setFilter] = useState(remembered.filter)
  const [selected, setSelected] = useState(null)
  const [origin, setOriginRect] = useState(null)
  const [withBaseline, setWithBaseline] = useState(false)
  const [csv, setCsv] = useState(null)
  const [intro] = useState(() => !visited)
  const lastPhase = useRef(runner.phase)

  useEffect(() => { const t = setTimeout(() => { visited = true }, 1800); return () => clearTimeout(t) }, [])
  useEffect(() => { remembered.view = view; remembered.filter = filter }, [view, filter])
  useEffect(() => { if (arrivals?.size) { const t = setTimeout(onArrived, 1600); return () => clearTimeout(t) } }, [arrivals, onArrived])
  useEffect(() => { if (arrivals?.size) cases.reload() }, [arrivals]) // eslint-disable-line react-hooks/exhaustive-deps

  // When a run settles, read the stored state back (runs and decisions as the server now has them).
  useEffect(() => {
    if (lastPhase.current === 'running' && runner.phase !== 'running') { cases.reload(); onChanged?.() }
    lastPhase.current = runner.phase
  }, [runner.phase]) // eslint-disable-line react-hooks/exhaustive-deps

  // Show numbers: N (not while typing, not with a modifier, not over a dialog).
  useEffect(() => {
    const onKey = (e) => {
      if (e.key.toLowerCase() !== 'n' || e.metaKey || e.ctrlKey || e.altKey) return
      if (e.target.closest?.('input, textarea, select, [contenteditable]') || document.querySelector('dialog[open]')) return
      toggleNumbers()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [toggleNumbers])

  const rows = useMemo(() => cases.data?.cases || [], [cases.data])
  // A live result is shown until the server's row has caught up with that run (or a later one); from
  // then on the row wins, because it also carries the review decisions made since.
  const records = useMemo(() => {
    const m = new Map()
    for (const row of rows) {
      const live = runner.live[row.case_id]?.record
      const caughtUp = live && row.last_run && live.runAt && row.last_run >= live.runAt
      m.set(row.case_id, live && !caughtUp ? { ...live, record: row.record } : fromRow(row))
    }
    return m
  }, [rows, runner.version]) // eslint-disable-line react-hooks/exhaustive-deps

  const L = useMemo(() => layout([...records.values()], narrow ? 'v' : 'h'), [records, narrow])

  // Where the display has each case: `at` is its place on the path (x.5 while moving), `passed` the
  // last stage it really got through (a failed stage is not passed), `pending` a case in this run
  // that has not reached its destination on screen yet.
  const inRun = useCallback((id) => runner.phase !== 'idle' && runner.shown[id] != null, [runner.version]) // eslint-disable-line react-hooks/exhaustive-deps
  const place = useCallback((id) => {
    const rec = records.get(id)
    if (inRun(id)) {
      const at = runner.shown[id]
      const live = runner.live[id]
      const stop = live?.failedAt ? PATH.indexOf(live.failedAt) : -1
      const landed = at >= PATH.length - 1 || (stop > 0 && at >= stop && live.record != null)
      const passed = stop > 0 ? Math.min(Math.floor(at), stop - 1) : Math.floor(at)
      return { input: at > 0 ? 'left' : 'waiting', landed, at, passed, pending: !landed }
    }
    if (!rec || rec.outcome === 'not_run') return { input: 'waiting', landed: false, at: 0, passed: 0, pending: false }
    const passed = rec.outcome === 'error' ? Math.max(0, PATH.indexOf(rec.failedStage) - 1) : PATH.length - 1
    return { input: 'left', landed: true, at: PATH.length - 1, passed, pending: false }
  }, [records, inRun, runner.version]) // eslint-disable-line react-hooks/exhaustive-deps

  const ids = rows.map((r) => r.case_id)
  const running = runner.phase === 'running'

  const gateStats = useMemo(() => STAGES.map(([key], i) => {
    const idx = i + 1
    let count = 0, failed = 0, inside = 0
    for (const id of ids) {
      const p = place(id)
      const rec = records.get(id)
      if (p.passed >= idx) count++
      if (running && p.pending && p.at > idx - 1 && p.at <= idx) inside++
      if (p.landed && rec?.outcome === 'error' && rec.failedStage === key) failed++
    }
    const live = Object.values(runner.live).map((l) => l.seconds[key]).filter((s) => s != null)
    return {
      count, failed, progress: ids.length ? count / ids.length : 0,
      state: failed ? 'error' : inside ? 'active' : count ? 'done' : 'idle',
      seconds: live.length ? live.reduce((a, b) => a + b, 0) : null,
    }
  }), [ids.join(), place, records, runner.version]) // eslint-disable-line react-hooks/exhaustive-deps

  const stats = useMemo(() => {
    const s = { input: { cases: ids.length, waiting: 0 }, discrepancy: { cases: 0, items: 0 }, review: { cases: 0 }, clear: { cases: 0, annotated: 0 }, error: { cases: 0 }, open: 0 }
    for (const id of ids) {
      const p = place(id)
      const rec = records.get(id)
      if (p.input === 'waiting') s.input.waiting++
      if (!p.landed || !rec || !s[rec.outcome]) continue
      s[rec.outcome].cases++
      if (rec.outcome === 'discrepancy') { s.discrepancy.items += rec.alerts; s.open += rec.openAlerts }
      if (rec.outcome === 'clear' && rec.annotated) s.clear.annotated++
    }
    return s
  }, [ids.join(), place, records]) // eslint-disable-line react-hooks/exhaustive-deps

  const select = useCallback((sel, rect) => { setOriginRect(rect || null); setSelected(sel) }, [])
  const onHub = useCallback((name, key) => setFilter((f) => (f.hub === key ? { outcome: 'all', hub: null } : { outcome: name, hub: key })), [])

  const notRun = rows.filter((r) => r.status === 'not_run').map((r) => r.case_id)
  const verify = (list) => { setSelected(null); start(list, { withBaseline }) }

  const exportCsv = async () => {
    setCsv({ busy: true })
    try {
      const r = await api.exportCsv()
      setCsv(r)
      const a = document.createElement('a'); a.href = r.url; a.download = ''; a.click()
    } catch (error) { setCsv({ error: error.message }) }
  }

  if (cases.error) return <div className="page"><Problem title="The workspace could not be read" error={cases.error} /></div>
  if (!cases.data) return <div className="page"><Loading label="Reading the workspace" /></div>

  const empty = rows.length === 0
  const launchedId = running ? runner.ids[Math.max(0, runner.launched - 1)] : null
  const launchedAt = launchedId ? runner.shown[launchedId] : null
  const stageWord = launchedAt != null ? (STAGES[Math.min(STAGES.length - 1, Math.max(0, Math.ceil(launchedAt) - 1))]?.[1]) : null
  const liveRecords = Object.values(runner.live).map((l) => l.record).filter(Boolean)
  const differ = liveRecords.filter((r) => r.differs).length
  const stopped = liveRecords.some((r) => r.outcome === 'error')

  const status = runner.phase === 'failed' ? `Stopped: ${runner.error}`
    : running ? (runner.paused ? 'Paused' : launchedId ? `Verifying ${launchedId} · ${stageWord}` : 'Starting the run')
    : runner.phase === 'done' ? `Verification complete${stopped ? '. Some cases could not run (✕)' : ''}`
    : empty ? 'No cases in the workspace yet'
    : notRun.length === rows.length ? 'Ready to verify'
    : 'Showing the latest stored run of each case'
  const filters = stats.error.cases > 0 || filter.outcome === 'error' ? [...FILTERS, ['error', 'Could not run']] : FILTERS

  return (
    <div className={`pipeline${intro ? ' is-intro' : ''}`}>
      <header className="hero">
        <h1 className="hero-title">Watch every record meet its evidence.</h1>
        <p className="hero-lede">ReSauce checks clinical research records against the medical documents behind them. The current dataset covers ICANS after CAR-T therapy, with synthetic cases only. Import cases, run the frozen pipeline, and follow each record to its outcome.</p>
        <div className="hero-actions">
          {empty ? (
            <button type="button" className="btn btn-primary btn-lg" onClick={onImport}><Icon name="import" size={18} />Import data</button>
          ) : running ? (
            <>
              {runner.paused
                ? <button type="button" className="btn btn-primary btn-lg" onClick={resume}><Icon name="play" size={16} />Resume</button>
                : <button type="button" className="btn btn-primary btn-lg" onClick={pause}><Icon name="pause" size={16} />Pause</button>}
              <button type="button" className="btn btn-lg" onClick={showNow} disabled={runner.instant}><Icon name="skip" size={16} />Show result now</button>
            </>
          ) : (
            <>
              <button type="button" className="btn btn-primary btn-lg" onClick={() => verify(notRun.length ? notRun : ids)}>
                <Icon name="play" size={16} />{notRun.length && notRun.length < ids.length ? 'Verify new cases' : notRun.length ? 'Verify all cases' : 'Verify all again'}
              </button>
              {notRun.length > 0 && notRun.length < ids.length && <button type="button" className="btn btn-lg" onClick={() => verify(ids)}>Verify all again</button>}
              <label className="check"><input type="checkbox" checked={withBaseline} onChange={(e) => setWithBaseline(e.target.checked)} />Also run Baseline A, the simpler method</label>
            </>
          )}
        </div>
      </header>

      <section className="stage on-dark" aria-label="Pipeline">
        <div className="stage-bar">
          <p className="stage-status" role="status" aria-live="polite">
            <span className={`pulse${running && !runner.paused ? ' is-on' : ''}`} aria-hidden="true" />
            {status}
            {(running || runner.phase === 'done') && <span className="stage-paced" title="Each record moves only after its real stage result has arrived; the time is the sum of the measured stage times of the ReSauce pipeline (Baseline A not included).">Paced for viewing{numbers ? ` · pipeline time ${(runner.measured * 1000).toFixed(1)} ms` : ''}</span>}
            {differ > 0 && <span className="stage-differs"><Icon name="error" size={14} />{differ === 1 ? 'One case differs' : `${differ} cases differ`} from the stored evaluation run. Open the case to compare.</span>}
          </p>
          <div className="stage-tools">
            <div className="seg seg-dark" role="group" aria-label="Show">
              {filters.map(([v, text]) => (
                <button key={v} type="button" aria-pressed={filter.outcome === v} onClick={() => setFilter({ outcome: v, hub: null })}>
                  {v !== 'all' && <OutcomeSign outcome={v}>{''}</OutcomeSign>}{text}
                </button>
              ))}
            </div>
            {filter.hub && (
              <button type="button" className="chip-on" onClick={() => setFilter({ outcome: 'all', hub: null })} aria-label={`Remove the filter ${HUB_NAMES[filter.hub]}`}>
                {HUB_NAMES[filter.hub]}<Icon name="close" size={14} />
              </button>
            )}
            <button type="button" className={`tool${numbers ? ' is-on' : ''}`} aria-pressed={numbers} onClick={toggleNumbers} title="Show numbers (N)">
              <Icon name="numbers" size={16} />Numbers<kbd>N</kbd>
            </button>
            <div className="seg seg-dark" role="group" aria-label="View">
              <button type="button" aria-pressed={view === 'network'} onClick={() => setView('network')}><Icon name="network" size={16} />Network</button>
              <button type="button" aria-pressed={view === 'list'} onClick={() => setView('list')}><Icon name="list" size={16} />List</button>
            </div>
          </div>
        </div>

        {view === 'network' ? (
          <Network layout={L} records={records} place={place} gateStats={gateStats} stats={stats} numbers={numbers} filter={filter}
            selected={selected} onSelect={select} onHub={onHub} intro={intro && !empty} arrivals={arrivals} landing={running}
            beacon={{ on: stats.discrepancy.cases > 0, spinning: stats.open > 0 && !(running && runner.paused) }}
            socketState={stats.clear.cases === 0 ? 'idle' : running ? 'live' : 'seated'}
            emptyAction={<button type="button" className="btn btn-invert" onClick={onImport}><Icon name="import" size={16} />Import data</button>} />
        ) : (
          <div className="stage-list">
            <CaseList rows={rows} records={records} place={place} filter={filter} onOpen={(id, rect) => select({ type: 'case', id }, rect)} />
          </div>
        )}
      </section>

      <section className="legend" aria-label="What the marks mean">
        <ul className="legend-list">
          {['discrepancy', 'review', 'clear', 'not_run', 'error'].map((o) => (
            <li key={o}><OutcomeSign outcome={o} /><span>{OUTCOMES[o].line}</span></li>
          ))}
        </ul>
        <div className="legend-side">
          <p>Each mark is one case. A record moves only after its real stage result has arrived; the motion is slowed so it can be followed. Review decisions never move a record. Synthetic data; not clinical validation.</p>
          <p className="legend-links">
            <a href="#/about">How a case is checked</a>
            <button type="button" className="linkish" onClick={exportCsv} disabled={csv?.busy || empty}>{csv?.busy ? 'Writing…' : 'Export all findings (CSV)'}</button>
            {csv?.file && <span className="muted">Written to <span className="mono">{csv.file}</span></span>}
            {csv?.error && <span className="problem-text">{csv.error}</span>}
          </p>
        </div>
      </section>

      {selected && (
        <Inspector selection={selected} origin={origin} records={records} place={place}
          onClose={() => setSelected(null)} onSelect={select} onHub={onHub} />
      )}
    </div>
  )
}
