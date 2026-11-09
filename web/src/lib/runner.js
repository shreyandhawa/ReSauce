// The pipeline run as the pipeline view shows it. Two clocks, kept apart on purpose:
//
//  1. The real run. Each case is verified with POST /api/cases/<id>/verify (the existing stream),
//     one after another, so every stage result is known the moment the server finishes it.
//     Each call stores a run and an audit entry, exactly as /api/verify-all does internally.
//  2. The display. The frozen pipeline finishes a case in milliseconds, too fast to follow, so the
//     view replays the real events at a watchable pace. A record never moves to a stage before
//     the real result for that stage has arrived; pacing only ever delays what is shown.
//     "Show result now" drops the pacing. The screen says the display is paced.
//
// The store lives outside React so a run continues while the researcher visits other pages.

import { useSyncExternalStore } from 'react'
import { api } from '../api.js'
import { brokenRun, fromRun } from './outcome.js'

export const STAGES = [
  ['load', 'Load'],
  ['extraction', 'Extraction'],
  ['timeline', 'Timeline'],
  ['verdict', 'Rules engine'],
]
export const PATH = ['input', ...STAGES.map(([k]) => k), 'outcome']
export const HOP_MS = 380 // one segment of the path on screen
const RUN_SPAN_MS = 9000 // launches are spread over about this long, whatever the number of cases

let state = blank()
let token = 0
let timer = null
let nextLaunch = 0
let transit = {} // id -> { to, at }: a record moving between two places on screen
const listeners = new Set()
const hopListeners = new Set()

function blank() {
  return {
    phase: 'idle', // idle | running | done | failed
    ids: [],
    withBaseline: false,
    paused: false,
    instant: false,
    live: {}, // id -> { reached: index into PATH, failedAt: stage | null, seconds: {stage: s}, facts, record }
    shown: {}, // id -> index into PATH the display has reached (x.5 while moving)
    launched: 0,
    measured: 0, // the sum of this run's measured ReSauce stage times, in seconds (Baseline A not included)
    realDone: false,
    error: null,
    version: 0,
  }
}

function emit() {
  state = { ...state, version: state.version + 1 }
  listeners.forEach((fn) => fn())
}

export function subscribe(fn) { listeners.add(fn); return () => listeners.delete(fn) }
export function getState() { return state }
export function useRunner() { return useSyncExternalStore(subscribe, getState) }
/** fn({ id, from, to, ms, outcome }) when a record sets off between two places on the path. */
export function onHop(fn) { hopListeners.add(fn); return () => hopListeners.delete(fn) }

export function start(ids, { withBaseline = false } = {}) {
  if (!ids.length || state.phase === 'running') return
  token += 1
  transit = {}
  nextLaunch = 0
  state = { ...blank(), phase: 'running', ids: [...ids], withBaseline, shown: Object.fromEntries(ids.map((id) => [id, 0])) }
  emit()
  realRun(token)
  schedule()
}

export function pause() { if (state.phase === 'running' && !state.paused) { state.paused = true; emit() } }
export function resume() { if (state.paused) { state.paused = false; emit(); schedule() } }
/** Stop pacing: show every record where the real run has got to, and keep up from now on. */
export function showNow() {
  if (state.phase !== 'running') return
  state.instant = true
  state.paused = false
  emit()
  schedule()
}

// -- the real run ------------------------------------------------------------------------------

async function realRun(mine) {
  for (const id of state.ids) {
    if (mine !== token) return
    // facts: what each stage reported, kept as it arrives (the branching network draws only these;
    // components/network/route.js turns them into the case's route).
    const live = { reached: 0, failedAt: null, seconds: {}, facts: { observations: null, use: null, scope: null, scopeByMention: false }, record: null }
    state.live[id] = live
    try {
      await api.verify(id, state.withBaseline, (e) => {
        if (mine !== token) return
        if (e.event === 'stage') {
          // A failed stage arrives under its own name with an "error" field (app/pipeline.py and
          // app/workstation.py merge the payload over the event). Baseline A failing does not
          // stop the case: the ReSauce result still stands.
          const index = PATH.indexOf(e.stage)
          if (e.seconds != null) { live.seconds[e.stage] = e.seconds; if (index > 0) state.measured += e.seconds }
          if (index > 0) live.reached = Math.max(live.reached, index)
          if (e.error && e.stage !== 'baseline') live.failedAt = index > 0 ? e.stage : 'load'
          else if (e.stage === 'extraction') live.facts.observations = (e.observations || []).map((o) => [o.evidence?.document_id, o.kind])
          else if (e.stage === 'timeline') live.facts.use = e.use || []
          else if (e.stage === 'verdict' && e.output) {
            live.facts.scope = e.output.out_of_scope ? 'oos' : 'fields'
            live.facts.scopeByMention = Boolean(e.output.out_of_scope?.evidence?.length)
          }
          if (index > 0) emit() // the layout gains this stage's lines before any record is moved along them
        } else if (e.event === 'done') {
          live.record = fromRun(id, e.run, e.findings || [])
          if (!live.failedAt) live.reached = PATH.length - 1
          emit() // a destination is now known (the layout gives the record its place)
        } else if (e.event === 'failed') {
          // The server broke off part-way (app/server.py): the case stops at the stage after the last
          // one that finished, and is shown as "Could not run". The run may not have been stored.
          live.failedAt = PATH[Math.min(live.reached + 1, PATH.length - 2)]
          live.record = brokenRun(id, live.failedAt)
          emit()
        }
        schedule()
      })
    } catch (error) {
      if (mine !== token) return
      settleFailed(error.message)
      return
    }
  }
  if (mine === token) { state.realDone = true; schedule() }
}

/**
 * The run stopped (the server could not be reached). Cases with a real result are shown where it
 * put them; every other case leaves the run and is shown from its stored state again.
 */
function settleFailed(message) {
  clearTimeout(timer)
  timer = null
  transit = {}
  for (const id of state.ids) {
    if (state.live[id]?.record) state.shown[id] = target(id)
    else { delete state.shown[id]; delete state.live[id] }
  }
  state.phase = 'failed'
  state.error = message
  emit()
}

/** How far the display may take a record: as far as the real run has got (a failed stage is the end). */
function target(id) {
  const live = state.live[id]
  if (!live) return 0
  if (live.failedAt) return PATH.indexOf(live.failedAt)
  return live.reached
}

// -- the display clock -------------------------------------------------------------------------

function schedule() {
  if (timer || state.phase !== 'running') return
  if (state.paused && !Object.keys(transit).length) return
  timer = setTimeout(tick, 16)
}

function tick() {
  timer = null
  if (state.phase !== 'running') return
  const now = performance.now()
  let changed = false

  // Records in flight arrive when their signal gets there (also while paused: they finish their segment).
  for (const id of Object.keys(transit)) {
    if (now >= transit[id].at) { state.shown[id] = transit[id].to; delete transit[id]; changed = true }
  }

  if (state.instant) {
    transit = {}
    for (const id of state.ids) {
      const t = target(id)
      if (state.shown[id] !== t) { state.shown[id] = t; changed = true }
    }
    state.launched = state.ids.length
  } else if (!state.paused) {
    const gap = Math.max(20, Math.min(150, RUN_SPAN_MS / Math.max(1, state.ids.length)))
    // Launch the next record once its first real stage has arrived.
    const nextId = state.ids[state.launched]
    if (nextId && now >= nextLaunch && target(nextId) >= 1) {
      hop(nextId, now)
      state.launched += 1
      nextLaunch = now + gap
      changed = true
    }
    // Move each launched record one segment further when its real result allows it.
    for (let i = 0; i < state.launched; i++) {
      const id = state.ids[i]
      if (transit[id] || state.shown[id] === 0) continue
      if (state.shown[id] < target(id)) { hop(id, now); changed = true }
    }
  }

  if (state.realDone && !Object.keys(transit).length && state.ids.every((id) => state.shown[id] >= target(id))) {
    state.phase = 'done'
    changed = true
  }
  if (changed) emit()
  schedule()
}

function hop(id, now) {
  const from = Math.floor(state.shown[id])
  transit[id] = { to: from + 1, at: now + HOP_MS }
  state.shown[id] = from + 0.5
  const record = state.live[id]?.record
  hopListeners.forEach((fn) => fn({ id, from: PATH[from], to: PATH[from + 1], ms: HOP_MS, outcome: record?.outcome }))
}
