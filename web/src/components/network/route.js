// The branching network: the nodes of each stage column, and each case's route through them.
// One place for both stored cases (GET /api/cases rows) and live runs (lib/runner.js facts).
//
// Every node is a kind of result the stage really reports, and every line is a real flow:
//   case → document type          the documents the case contains (Load reads them)
//   document type → extraction    one per observation: the type of the document it was quoted from
//   extraction → timeline         one per observation: how resauce/timeline.py sorted it
//   timeline → rules engine       the engine receives every group of the sorted timeline (engine.py
//                                 _Engine builds it with timeline.select). Solid from the groups it may
//                                 use as evidence for onset and grade; dashed from the groups it reads
//                                 only for flags and checks (§6.3–6.5, §7.10)
//   extraction → out of scope     the §5 scope check reads the notes' mentions directly, before any
//                                 timeline; drawn only when a mention was the reason (case.json age and
//                                 a record of Grade 5 come from no node, so they draw no line)
//   rules engine → destination    the field whose §7 category sent the case there (lib/outcome.js)
// Extraction nodes group the extractor's observation kinds (resauce/extract.py KINDS) by the
// grading domains of docs/clinical-methods.md §3.3; the inspector lists the kinds in each group.
//
// The network shape is only a way of drawing the pipeline: ReSauce applies fixed rules.

import { NOTE_TYPES, OBS_KINDS } from '../../lib/format.js'

const doc = (key, label) => ({ key, label, name: NOTE_TYPES[key], about: `Documents of the type “${NOTE_TYPES[key]}” that the Load stage read.` })

export const COLUMNS = [
  {
    key: 'load', title: 'Load', sub: 'Document types', unit: 'document',
    nodes: [
      doc('physician_progress_note', 'Progress note'),
      doc('nursing_note', 'Nursing note'),
      doc('neurology_consult', 'Neurology consult'),
      doc('ice_assessment', 'ICE assessment'),
      doc('eeg_report', 'EEG report'),
      doc('imaging_report', 'Imaging report'),
      doc('discharge_summary', 'Discharge summary'),
      { key: 'other', label: 'Other document', name: 'Other document', about: 'Documents of the type “Other” that the Load stage read.' },
    ],
  },
  {
    key: 'extraction', title: 'Extraction', sub: 'What the notes say', unit: 'observation',
    nodes: [
      { key: 'ice', label: 'ICE score', kinds: ['ice_total', 'ice_partial'],
        about: 'ICE scores quoted from the notes. ICE is a 10-point bedside screen and one of the five grading domains, but on its own it is not the grade (§3.2, §3.3).' },
      { key: 'consciousness', label: 'Consciousness', kinds: ['consciousness'],
        about: 'Statements about the level of consciousness, a grading domain (§3.3).' },
      { key: 'seizure', label: 'Seizure and EEG', kinds: ['seizure', 'eeg_finding'],
        about: 'Seizures and EEG findings. Seizures seen on EEG belong to the seizure domain; EEG slowing alone is not a seizure (§3.3).' },
      { key: 'motor', label: 'Motor findings', kinds: ['motor_finding'],
        about: 'Motor findings such as deep focal weakness, a grading domain (§3.3). Weakness from deconditioning is excluded (§4.2).' },
      { key: 'icp', label: 'Raised ICP / edema', kinds: ['icp_sign', 'text_only_icp_sign'],
        about: 'Signs of raised intracranial pressure or cerebral edema, a grading domain (§3.3). Signs listed in the grading source’s text but not in its Table 6 are flagged for review (§3.3).' },
      { key: 'context', label: 'Grading context', kinds: ['not_assessable', 'competing_cause', 'attribution', 'assessment_barrier'],
        about: 'Statements that change how a finding can be graded: “not assessable” periods, assessment barriers, competing causes and clinician attribution (§3.4, §4.1).' },
      { key: 'other', label: 'Excluded and other', kinds: ['excluded_symptom', 'ungradeable_symptom', 'out_of_scope_mention', 'unrecognised'],
        about: 'Symptoms excluded from ICANS grading (§4.2), symptoms that cannot be graded, mentions that put a case out of scope (§5), and neurological wording the extractor could not parse, which is reported rather than guessed.' },
    ],
  },
  {
    key: 'timeline', title: 'Timeline', sub: 'How each was sorted', unit: 'observation',
    nodes: [
      { key: 'used', label: 'Used', evidence: true,
        about: 'From the current signed version of a note, not copied forward, and dated inside the observation window: the content the rules use for onset and grade (§6.2–6.5).' },
      { key: 'undated', label: 'Time unresolved', evidence: true,
        about: 'The extractor could not resolve when it happened, so the timeline gives it no date. The rules engine still weighs it, and lists it for human review.' },
      { key: 'context_only', label: 'Context only', evidence: true,
        about: 'From a current signed note but dated outside the observation window, and not a finding listed in the “outside observation window” flag (for example a negated finding or a competing cause). The rules engine reads competing causes, attribution, assessment barriers and intracranial hemorrhage from current notes at any date.' },
      { key: 'outside_window', label: 'Outside window', evidence: false,
        about: 'A finding dated outside the observation window. It is not used for any §7 category; the rules engine lists it in the extra flag “outside observation window” (§6.5, §7.10).' },
      { key: 'copied_forward', label: 'Copied forward', evidence: false,
        about: 'From a note that repeats an earlier note apart from dates, times or formatting. It is not treated as new evidence (§6.4); the rules engine lists the copy for review.' },
      { key: 'not_current_version', label: 'Not current version', evidence: false,
        about: 'From an earlier signed version or from unsigned content. The latest signed version of each note is current and unsigned content is never used for onset or grade; the rules engine still checks whether the record matches an earlier version, and flags unsigned versions (§6.3, §7.10).' },
    ],
  },
  {
    key: 'verdict', title: 'Rules engine', sub: 'Fields checked', unit: null,
    nodes: [
      { key: 'onset', label: 'Onset date',
        about: 'The record’s onset date, compared with the onset derived from the documents (§6.2) and given a §7 category.' },
      { key: 'max_grade', label: 'Maximum grade',
        about: 'The record’s maximum grade, compared with the highest grade derived from the documents (§3.4, §6.2) and given a §7 category.' },
      { key: 'oos', label: 'Out of scope',
        about: 'The case is outside the scope of this proof of concept (§5): age under 18, a CAPD assessment, a record of Grade 5, a documented death or documented baseline developmental delay. It gets the flag “out of scope (reason)” and no §7 category for either field. The check reads the case, the record and the notes’ mentions directly, before any timeline; a line comes in only when a mention was the reason.' },
    ],
  },
]

export const NODE_INFO = Object.fromEntries(COLUMNS.map((c) => [c.key, Object.fromEntries(c.nodes.map((n) => [n.key, n]))]))
export const COLUMN = Object.fromEntries(COLUMNS.map((c) => [c.key, c]))
const GROUP_OF_KIND = Object.fromEntries(COLUMN.extraction.nodes.flatMap((g) => g.kinds.map((k) => [k, g.key])))
const DOC_TYPES = new Set(COLUMN.load.nodes.map((n) => n.key))

/** The extraction node of an observation kind. A kind this view does not know goes to "Excluded and other". */
export const groupOf = (kind) => GROUP_OF_KIND[kind] || 'other'
export const kindName = (kind) => OBS_KINDS[kind] || kind
/** Whether the rules engine may use a timeline group as evidence for onset and grade (else: flags and checks only). */
export const isEvidence = (use) => NODE_INFO.timeline[use]?.evidence !== false

/**
 * A case's route. Every argument may be missing: a live run fills them stage by stage, and a
 * stage that has not reported adds nothing.
 *   noteTypes     { document_id: note_type }
 *   observations  [[document_id, kind], ...]       (extraction)
 *   use           [timeline group per observation] (timeline; the six groups of app/pipeline.py)
 *   scope         'fields' | 'oos' | null          (rules engine)
 *   scopeByMention  whether an out-of-scope result came from a mention in the notes
 *   outcome, fieldHubs                              (lib/outcome.js classify)
 * Returns per column the nodes the case reached (with counts), and per band (the column a line
 * goes into) the lines it took: key → { fromCol, from, to, cluster?, hub? }.
 */
export function routeOf({ noteTypes, observations, use, scope, scopeByMention, outcome, fieldHubs } = {}) {
  const nodes = { load: new Map(), extraction: new Map(), timeline: new Map(), verdict: new Map() }
  const lines = { load: new Map(), extraction: new Map(), timeline: new Map(), verdict: new Map(), outcome: new Map() }
  const kinds = new Map()
  const bump = (map, key) => map.set(key, (map.get(key) || 0) + 1)
  const link = (band, fromCol, from, to, extra) => lines[band].set(`${from}>${to}`, { fromCol, from, to, ...extra })
  const typeOf = (id) => {
    const t = noteTypes?.[id]
    return t == null ? null : DOC_TYPES.has(t) ? t : 'other'
  }

  for (const id of Object.keys(noteTypes || {})) {
    const t = typeOf(id)
    bump(nodes.load, t)
    link('load', 'input', null, t)
  }
  ;(observations || []).forEach(([documentId, kind], i) => {
    const group = groupOf(kind)
    bump(nodes.extraction, group)
    bump(kinds, kind)
    const t = typeOf(documentId)
    if (t) link('extraction', 'load', t, group)
    const u = use?.[i]
    if (u && NODE_INFO.timeline[u]) { // app/pipeline.py _timeline_summary gives only these six groups
      bump(nodes.timeline, u)
      link('timeline', 'extraction', group, u)
    }
  })
  if (scope === 'oos') {
    nodes.verdict.set('oos', 1)
    if (scopeByMention) link('verdict', 'extraction', groupOf('out_of_scope_mention'), 'oos')
  } else if (scope === 'fields') {
    for (const f of ['onset', 'max_grade']) {
      nodes.verdict.set(f, 1)
      for (const u of nodes.timeline.keys()) link('verdict', 'timeline', u, f, { aside: !isEvidence(u) })
    }
  }
  if (outcome && fieldHubs) {
    for (const [field, hub] of Object.entries(fieldHubs)) {
      if (outcome === 'clear') link('outcome', 'verdict', field, 'clear', { cluster: 'clear' })
      else link('outcome', 'verdict', field, `${outcome}:${hub}`, { cluster: outcome, hub })
    }
  }
  return { nodes, lines, kinds }
}

/** The raw facts of a stored case row (app/workstation.py cases(), field "route"). */
export function rowFacts(row) {
  return {
    noteTypes: row.route?.note_types || null,
    observations: row.route?.observations || null,
    use: row.route?.use || null,
    scope: row.out_of_scope ? 'oos' : row.categories ? 'fields' : null,
    scopeByMention: Boolean(row.route?.out_of_scope_by_mention),
  }
}
