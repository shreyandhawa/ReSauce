import { api } from '../api.js'
import { useLoad } from '../lib/hooks.js'

// One plain line per category, written from docs/clinical-methods.md §7.1–7.9.
const CATEGORIES = [
  ['7.1', 'Onset date mismatch', 'The record’s onset date and the onset derived from the documents differ by one calendar day or more (tolerance 0 days); the signed difference is reported.'],
  ['7.2', 'Maximum grade mismatch', 'A quoted observation, not attributed to another cause, proves a grade higher than the record’s maximum grade.'],
  ['7.3', 'Grade not supported by documented evidence', 'The record’s grade is higher than anything the quoted documents support. Reported as unsupported, never as wrong, because missing notes do not prove absence.'],
  ['7.4', 'Insufficient evidence', 'The documents needed to confirm or refute the recorded value do not exist or could not be assessed. Absence of a finding is never treated as evidence that it was absent.'],
  ['7.5', 'Ambiguous evidence', 'The evidence can be read in more than one way and the readings lead to different categories; each reading is reported with its reason.'],
  ['7.6', 'Legitimate revision', 'The record changed between versions and a later document, written before the change, supports the new value. Information, not an error.'],
  ['7.7', 'No discrepancy', 'The record’s onset falls on the documented onset day (or inside its date range) and its maximum grade equals the documented maximum grade.'],
  ['7.8', 'Missing recorded value', 'The record reports ICANS but its onset date or maximum grade is empty; the documented value is shown alongside.'],
]

// Limitations recorded outside resauce/evaluate.py, each with where it is written down.
const MORE_LIMITATIONS = [
  ['The held-out split is in-repo and not sealed (same writer, same repository), and it is “seen”: the pipeline changed after the first held-out run.', 'evaluation-spec §6; handoff §0'],
  ['The dev split was used to build and debug the pipeline, so its numbers are expected to be optimistic.', 'evaluation-spec §1'],
  ['Agreement between the intended answers and the blind re-derivation (144 of 144 categories) is between two answer sets written by Claude models from the same rules text. It shows the rules are applied consistently, not that either is clinically right.', 'handoff, Step 5a entry'],
  ['A clinician has not yet reviewed the assumptions A1–A35 or the rule gaps 14 to 30 listed in reference/dev-v1/comparison.md §8.', 'handoff, Step 5a close-out and Step 6 entries'],
  ['Each case is a selection of 3 to 12 documents, so most days in the 29-day window have no documented assessment. The unassessed-period list is long by design.', 'handoff, Milestone 2 Step 4 part 2'],
  ['Partial copy-forward (a note repeating part of an earlier note) is not detected; only whole-note copies are.', 'handoff, session 4b'],
  ['Misspelt variants of competing-cause, attribution, barrier, hemorrhage and out-of-scope words are listed but never used, so a misspelt sedative can hide a competing cause.', 'handoff, session 4b'],
  ['CTCAE grading and Grade 5 are not built (out of scope for this proof of concept).', 'clinical-methods §8'],
  ['Adults only: patients under 18, CAPD assessments, developmental delay, a record of Grade 5 and a documented death are out of scope and get no category.', 'clinical-methods §5'],
  ['The locked set (written after the pipeline freeze, in a separate repository) has not been evaluated; no locked-set result exists yet.', 'handoff, Step 6 part 1'],
]

export default function About() {
  const summary = useLoad(() => api.summary(), [])
  const ws = useLoad(() => api.workspace(), [])
  const p = ws.data?.pipeline
  return (
    <div className="page">
      <header className="page-hero"><h1>About</h1><p className="lede">What ReSauce is, how a case is checked, and the limits of what it shows.</p></header>
      <div className="prose">
        <h2>What ReSauce is</h2>
        <p>A computational proof of concept. It reads the clinical documents behind a research record of ICANS after CAR-T therapy, extracts the neurological observations, each with its exact quoted source, rebuilds the timeline from Day 0 to Day +28 with event time kept apart from documentation time, and compares the record’s onset date and maximum grade with what the documents support. Each result is a potential discrepancy for a person to review, never a verdict (clinical-methods §7).</p>
        <h2>What it is not</h2>
        <ul>
          <li>Not a clinical decision tool, and not for patient care.</li>
          <li><strong>Synthetic data only.</strong> Every case is fictional. Do not load real patient records.</li>
          <li><strong>Not clinically validated.</strong> Results on synthetic data are not clinical validation. The rules have not been reviewed by a clinician.</li>
        </ul>

        <h2>What real-world use would require <span className="untested">untested</span></h2>
        <p>None of the following has been built or tried. They are listed so the gap is visible.</p>
        <ul>
          <li>Ethics approval and data-governance agreements for the site and the study.</li>
          <li>De-identification of every document before it reaches the tool, checked independently.</li>
          <li>An export adapter that turns the health record’s notes and the research database’s values into the ReSauce data format, keeping every version.</li>
          <li>Clinician review and sign-off of the rules and assumptions (A1–A35, and the rule gaps 14 to 30).</li>
          <li>Evaluation on real, consented, de-identified data, with the pipeline frozen before the data is seen.</li>
        </ul>

        <h2>How a case is verified</h2>
        <ol>
          <li><strong>Load</strong> the case folder and check it against the data format (docs/data-format.md).</li>
          <li><strong>Extract</strong> observations from the text with fixed phrase rules, each with its quote, offsets, status and event time.</li>
          <li><strong>Timeline</strong>: latest signed versions, the observation window and copied-forward notes applied (clinical-methods §6).</li>
          <li><strong>Compare and categorise</strong> each field (7.1–7.8) with its evidence; flag what the rules cannot decide as “needs human review”.</li>
        </ol>
        <p>On the pipeline stage each case then reaches one of three destinations, decided only from the two field categories: <strong>Discrepancy</strong> (either field 7.1, 7.2, 7.3 or 7.8), <strong>Needs review</strong> (no alert, but 7.4, 7.5, a “review: …” result, or out of scope under §5) or <strong>No discrepancy detected</strong> (both fields 7.6 or 7.7). Review decisions never move a case.</p>
        <p>The pipeline is deterministic and frozen. {p ? <>Tag <span className="mono">{p.tag}</span>, commit <span className="mono">{p.tag_commit?.slice(0, 12) || 'unknown'}</span>; the {p.frozen_files.length} frozen files {p.frozen_files_match ? 'match' : <strong>do not match</strong>} the hashes in docs/freeze.md.</> : 'Loading its version…'}</p>

        <h2>What the pipeline view does not show</h2>
        <p>The animation is driven by real results only. Where the data does not say something, nothing is drawn for it:</p>
        <ul>
          <li><strong>Pace.</strong> The pipeline finishes a case in milliseconds. The stage replays the real stage results slowly enough to follow; a record never moves before its real result exists. The measured times are shown under Numbers.</li>
          <li><strong>Links between records.</strong> Each mark is one case. The data holds no relationships between cases, so none are drawn; the only links are case → stage → destination → finding type.</li>
          <li><strong>Folder preview.</strong> The server has no way to describe a folder before importing it, so the import reports what it found afterwards.</li>
          <li><strong>Dropping files.</strong> The server only accepts a folder path inside this project, so case folders cannot be dropped onto the page. A single note (.txt) can be dropped into the New case form.</li>
          <li><strong>Baseline A.</strong> When it is chosen, the simpler method runs beside the pipeline on the same case. It is a comparison, not a stage the record passes through, so the stage does not draw it; the inspector and the case page list its measured time, and it is left out of the pipeline time.</li>
          <li><strong>Baseline B.</strong> The AI-model comparison is never run by this app: it would send case text to an outside service, and the app makes no network calls. Its answers are collected separately, once (<span className="mono">python -m resauce.baseline_b</span>), stored, and appear only on the Results page.</li>
          <li><strong>Stages inside “verify all”.</strong> That endpoint reports whole cases only, so the page verifies cases one by one through the single-case endpoint, which reports each stage. Each call stores a run and an audit entry exactly as before.</li>
        </ul>

        <h2>Discrepancy categories</h2>
        <dl className="cat-list">
          {CATEGORIES.map(([c, name, text]) => <div key={c}><dt><span className="mono">{c}</span> {name}</dt><dd>{text}</dd></div>)}
        </dl>

        <h2>Known limitations</h2>
        {summary.data && <ul>{summary.data.limitations.map((l) => <li key={l}>{l} <span className="source">resauce/evaluate.py</span></li>)}</ul>}
        <ul>{MORE_LIMITATIONS.map(([text, source]) => <li key={text}>{text} <span className="source">{source}</span></li>)}</ul>
        <p className="note">Reference answers: {summary.data?.reference_label || '…'}.</p>
      </div>
    </div>
  )
}
