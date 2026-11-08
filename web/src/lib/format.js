// Labels and formatting. Category names are the headings of docs/clinical-methods.md §7;
// classes follow docs/evaluation-spec.md §3. No numbers are produced here.

export const CATEGORY_NAMES = {
  '7.1': 'Onset date mismatch',
  '7.2': 'Maximum grade mismatch',
  '7.3': 'Grade not supported by documented evidence',
  '7.4': 'Insufficient evidence',
  '7.5': 'Ambiguous evidence',
  '7.6': 'Legitimate revision',
  '7.7': 'No discrepancy',
  '7.8': 'Missing recorded value',
}

export const FIELD_NAMES = { onset: 'Onset date', max_grade: 'Maximum grade' }
export const FIELDS = ['onset', 'max_grade']

const ALERTS = ['7.1', '7.2', '7.3', '7.8']
const REVIEW_FLAGS = ['7.4', '7.5']

/** The leading 7.x code of a category, e.g. "7.5 (attribution)" -> "7.5". */
export function code(category) {
  const m = /^\s*(7\.[1-9])(?=$|[\s(])/.exec(category || '')
  return m ? m[1] : null
}

/** How a category reads: alert, flag (7.4/7.5), clear (7.6/7.7), review ("review: …"), oos, error. */
export function categoryKind(category) {
  if (!category) return 'none'
  if (category === 'error') return 'error'
  const c = code(category)
  if (ALERTS.includes(c)) return 'alert'
  if (REVIEW_FLAGS.includes(c)) return 'flag'
  if (c === '7.6' || c === '7.7') return 'clear'
  if (category.startsWith('review:')) return 'review'
  if (category.startsWith('out of scope')) return 'oos'
  return 'none'
}

export const KIND_TEXT = {
  alert: 'Discrepancy alert',
  flag: 'Review flag',
  clear: 'No alert',
  review: 'Needs human review',
  oos: 'Out of scope',
  error: 'Error',
  none: '',
}

/** Short label for a category cell: "7.1", "Needs review", "Out of scope". */
export function shortCategory(category) {
  const kind = categoryKind(category)
  if (kind === 'review') return 'Needs review'
  if (kind === 'oos') return 'Out of scope'
  return code(category) || category
}

export function rateValue(r) {
  return r && r.value != null ? r.value.toFixed(2) : 'undefined'
}

export function signedDay(day) {
  if (day == null) return ''
  if (day === 0) return 'Day 0'
  return day > 0 ? `Day +${day}` : `Day −${Math.abs(day)}`
}

/** A signed difference in days: "+1 day", "−3 days". */
export function days(n) {
  if (n == null) return ''
  const sign = n > 0 ? '+' : n < 0 ? '−' : ''
  return `${sign}${Math.abs(n)} ${Math.abs(n) === 1 ? 'day' : 'days'}`
}

export function ms(seconds) {
  if (seconds == null) return '—'
  const v = seconds * 1000
  return v < 1 ? `${v.toFixed(2)} ms` : `${v.toFixed(1)} ms`
}

export function documentShort(documentId) {
  const m = /-(D\d+)$/.exec(documentId || '')
  return m ? m[1] : documentId
}

/** "D03 v1 · 356–372": a citation in the style of an apparatus entry. */
export function citation(ref) {
  if (!ref) return ''
  if (ref.start == null) return `${ref.document_id}${ref.version != null ? ` v${ref.version}` : ''}`
  return `${documentShort(ref.document_id)} v${ref.version} · ${ref.start}–${ref.end}`
}

export const NOTE_TYPES = {
  physician_progress_note: 'Physician progress note',
  nursing_note: 'Nursing note',
  neurology_consult: 'Neurology consult',
  ice_assessment: 'ICE assessment',
  eeg_report: 'EEG report',
  imaging_report: 'Imaging report',
  discharge_summary: 'Discharge summary',
  other: 'Other',
}

export const ROLES = {
  attending_physician: 'attending physician',
  resident_physician: 'resident physician',
  advanced_practice_provider: 'advanced practice provider',
  nurse: 'nurse',
  neurologist: 'neurologist',
  radiologist: 'radiologist',
  other: 'other',
}

// Observation kinds as the extractor names them (resauce/extract.py KINDS), in plain words.
export const OBS_KINDS = {
  ice_total: 'ICE total',
  ice_partial: 'ICE, partial',
  consciousness: 'Level of consciousness',
  seizure: 'Seizure',
  eeg_finding: 'EEG finding',
  motor_finding: 'Motor finding',
  icp_sign: 'Raised-ICP sign',
  text_only_icp_sign: 'ICP sign, text only',
  excluded_symptom: 'Excluded symptom',
  ungradeable_symptom: 'Ungradeable symptom',
  not_assessable: 'Not assessable',
  competing_cause: 'Competing cause',
  attribution: 'Attribution',
  assessment_barrier: 'Assessment barrier',
  out_of_scope_mention: 'Out-of-scope mention',
  unrecognised: 'Unrecognised text',
}

export const TIME_SOURCES = {
  in_text: 'time stated in the text',
  relative: 'relative phrase',
  note_header: 'note header',
  documented_at: 'documentation time used',
  unresolved: 'unresolved',
}

/** A documented or record value in words. */
export function valueText(value) {
  if (value == null) return '—'
  if (typeof value !== 'object') return String(value)
  if (value.undetermined) return 'Undetermined'
  if (value.date) return `${value.date} · ${signedDay(value.study_day)}`
  if (value.range) {
    const [a, b] = value.range
    if (typeof a === 'number') return `Grade ${a}–${b}`
    const days = value.study_days ? ` · ${signedDay(value.study_days[0])} to ${signedDay(value.study_days[1])}` : ''
    return `${a} to ${b}${days}`
  }
  if (value.grade != null) return `Grade ${value.grade}`
  return JSON.stringify(value)
}
