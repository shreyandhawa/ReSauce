// Where a verified case ends up in the pipeline view. Decided only from the frozen pipeline's own
// output: the category of each field (docs/clinical-methods.md §7, as app/findings.py labels them)
// and the §5 out-of-scope result. Review decisions never move a case; they only mark it.
//
//   discrepancy  either field is 7.1, 7.2, 7.3 or 7.8 (an alert, evaluation-spec §3)
//   clear        both fields are 7.6 or 7.7 ("No discrepancy detected"; flags may still be listed)
//   review       anything else: a field is 7.4 or 7.5, a "review: …" result, the case is out of
//                scope (§5), or a category this view does not recognise (never shown as clear)
//   error        the run stopped (the stage that failed is kept)
//   not_run      no run yet

import { FIELDS, categoryKind, code } from './format.js'

export const OUTCOMES = {
  discrepancy: { word: 'Discrepancy', icon: 'diamond', line: 'The record and its documents disagree.' },
  review: { word: 'Needs review', icon: 'triangle', line: 'The evidence is insufficient or ambiguous, the rules could not decide, or the case is out of scope.' },
  clear: { word: 'No discrepancy detected', icon: 'dot', line: 'Onset date and maximum grade agree with the documents under the frozen rules (§7.6/7.7).' },
  error: { word: 'Could not run', icon: 'cross', line: 'The pipeline stopped on this case.' },
  not_run: { word: 'Not verified yet', icon: 'ring', line: 'Waiting for its first run.' },
}

// Finding-type hubs inside each destination, in display order. Short names for the stage;
// the full §7 heading is shown in the inspector (lib/format.js CATEGORY_NAMES).
export const HUBS = {
  discrepancy: [['7.1', 'Onset date'], ['7.2', 'Higher grade'], ['7.3', 'Unsupported grade'], ['7.8', 'Missing value']],
  review: [['7.4', 'Insufficient'], ['7.5', 'Ambiguous'], ['rules', 'Rules undecided'], ['oos', 'Out of scope'], ['other', 'Unrecognised']],
}
export const HUB_NAMES = {
  '7.1': 'Onset date mismatch (§7.1)', '7.2': 'Maximum grade mismatch (§7.2)', '7.3': 'Grade not supported by documented evidence (§7.3)',
  '7.8': 'Missing recorded value (§7.8)', '7.4': 'Insufficient evidence (§7.4)', '7.5': 'Ambiguous evidence (§7.5)',
  rules: 'Needs human review: the rules could not decide', oos: 'Out of scope (§5): no discrepancy category',
  other: 'A result this view does not recognise: open the case',
}
const HUB_OF_KIND = { review: 'rules', oos: 'oos' }

/** The stage a stored run stopped at, or null (app/workstation.py keeps a stage error under run.error). */
export function failedStage(run) {
  return run?.error?.stage || (run?.resauce?.error ? 'verdict' : null)
}

/**
 * Classify from the field categories ({ onset, max_grade } or null) and the run state.
 * fieldHubs says which field sent the case to which hub (the pipeline view draws a line for each):
 * the alert fields of a discrepancy, the undecided fields of a review case, both fields of a clean one.
 */
export function classify({ verified, failed, outOfScope, categories }) {
  if (!verified) return { outcome: 'not_run', hubs: [], fieldHubs: {}, alerts: 0 }
  if (failed) return { outcome: 'error', hubs: [], fieldHubs: {}, alerts: 0 }
  if (outOfScope) return { outcome: 'review', hubs: ['oos'], fieldHubs: { oos: 'oos' }, alerts: 0 }
  const fields = FIELDS.map((f) => ({ field: f, category: categories?.[f], kind: categoryKind(categories?.[f]) }))
  const alerts = fields.filter((x) => x.kind === 'alert').map((x) => [x.field, code(x.category)])
  if (alerts.length) return { outcome: 'discrepancy', hubs: [...new Set(alerts.map(([, h]) => h))], fieldHubs: Object.fromEntries(alerts), alerts: alerts.length }
  if (fields.every((x) => x.kind === 'clear')) return { outcome: 'clear', hubs: [], fieldHubs: Object.fromEntries(FIELDS.map((f) => [f, 'clear'])), alerts: 0 }
  const open = fields.filter((x) => x.kind !== 'clear').map((x) => [x.field, x.kind === 'flag' ? code(x.category) : HUB_OF_KIND[x.kind] || 'other'])
  return { outcome: 'review', hubs: [...new Set(open.map(([, h]) => h))], fieldHubs: Object.fromEntries(open), alerts: 0 }
}

/** Whether a record passes the stage filter; a record without a settled outcome only passes "All". */
export function matchesFilter(rec, filter) {
  if (filter.outcome !== 'all' && rec?.outcome !== filter.outcome) return false
  if (filter.hub && !rec?.hubs.includes(filter.hub)) return false
  return true
}

/** A case row from GET /api/cases as a pipeline record. */
export function fromRow(row) {
  const invalid = row.status === 'invalid'
  const base = classify({
    verified: row.status !== 'not_run',
    failed: invalid || row.status === 'error',
    outOfScope: row.out_of_scope,
    categories: row.categories,
  })
  const tiers = row.tiers || {}
  return {
    id: row.case_id,
    ...base,
    failedStage: invalid ? 'load' : row.failed_stage || null,
    annotated: base.outcome === 'clear' && (tiers.review || 0) + (tiers.other || 0) > 0,
    openAlerts: row.open_alerts || 0,
    open: row.open || 0,
    runAt: row.last_run || null,
    record: row.record || null,
    invalid: row.invalid || null,
  }
}

/** The record of a case that has just finished a live run (the "done" event of /verify). */
export function fromRun(caseId, run, findings) {
  const output = run?.resauce?.output
  const stopped = failedStage(run)
  const categories = output && !output.out_of_scope ? Object.fromEntries(FIELDS.map((f) => [f, output.fields?.[f]?.category])) : null
  const base = classify({ verified: true, failed: Boolean(stopped), outOfScope: Boolean(output?.out_of_scope), categories })
  const extra = findings.filter((f) => f.tier !== 0 && f.kind !== 'field').length
  const matches = run?.stored_comparison?.matches
  return {
    id: caseId,
    ...base,
    failedStage: stopped,
    annotated: base.outcome === 'clear' && extra > 0,
    openAlerts: findings.filter((f) => f.tier === 0 && !f.decision).length,
    open: findings.filter((f) => !f.decision).length,
    runAt: run?.started_at || null,
    differs: Boolean(matches && Object.values(matches).includes(false)),
    record: null,
    invalid: null,
  }
}

/** A case whose run broke off on the server (a "failed" event): it could not run; nothing else is known. */
export function brokenRun(caseId, stage) {
  return { id: caseId, outcome: 'error', hubs: [], fieldHubs: {}, alerts: 0, failedStage: stage, annotated: false, openAlerts: 0, open: 0, runAt: null, differs: false, record: null, invalid: null }
}
