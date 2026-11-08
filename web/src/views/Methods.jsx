import { Loading } from '../components/Bits.jsx'

// One plain line per category, written from docs/clinical-methods.md §7.1–7.9.
const CATEGORIES = [
  ['7.1', 'Onset date mismatch', 'The record’s onset date and the onset derived from the documents differ by one calendar day or more (tolerance 0 days); the signed difference is reported.'],
  ['7.2', 'Maximum grade mismatch', 'A quoted observation, not attributed to another cause, proves a grade higher than the record’s maximum grade.'],
  ['7.3', 'Grade not supported by documented evidence', 'The record’s grade is higher than anything the quoted documents support. Reported as unsupported, never as wrong, because missing notes do not prove absence.'],
  ['7.4', 'Insufficient evidence', 'The documents needed to confirm or refute the recorded value do not exist or could not be assessed. Absence of a finding is never treated as evidence that it was absent.'],
  ['7.5', 'Ambiguous evidence', 'The evidence can be read in more than one way and the readings lead to different categories; each reading is reported with its reason (attribution, conflicting assessments, assessment barrier, consciousness wording).'],
  ['7.6', 'Legitimate revision', 'The record changed between versions and a later document, written before the change, supports the new value. Information, not an error.'],
  ['7.7', 'No discrepancy', 'The record’s onset falls on the documented onset day (or inside its date range) and its maximum grade equals the documented maximum grade.'],
  ['7.8', 'Missing recorded value', 'The record reports ICANS but its onset date or maximum grade is empty; the documented value is shown alongside.'],
  ['7.9', 'Records with no ICANS, or no qualifying finding', 'Rules for a record that reports no ICANS (compared as Grade 0) and for a record of ICANS with no qualifying finding in the window; they resolve to the categories above.'],
]

// Limitations recorded outside resauce/evaluate.py, each with where it is written down.
const MORE_LIMITATIONS = [
  ['The held-out split is in-repo and not sealed (same writer, same repository), and it is “seen”: the pipeline changed after the first held-out run.', 'evaluation-spec §6; handoff §0'],
  ['The dev split was used to build and debug the pipeline, so its numbers are expected to be optimistic.', 'evaluation-spec §1; handoff, Step 4 entry'],
  ['Agreement between the intended answers and the blind re-derivation (144 of 144 categories) is between two answer sets written by Claude models from the same rules text. It shows the rules are applied consistently, not that either is clinically right.', 'handoff, Step 5a entry'],
  ['A clinician has not yet reviewed the assumptions A1–A35 or the rule gaps 14 to 30 listed in reference/dev-v1/comparison.md §8.', 'handoff, Step 5a close-out and Step 6 entries'],
  ['Each case is a selection of 3 to 12 documents, so most days in the 29-day window have no documented assessment. The unassessed-period list is long by design; it reflects the selection of documents, not real monitoring practice.', 'handoff, Milestone 2 Step 4 part 2'],
  ['Partial copy-forward (a note repeating part of an earlier note) is not detected; only whole-note copies are.', 'handoff, session 4b'],
  ['Misspelt variants of competing-cause, attribution, barrier, hemorrhage and out-of-scope words are listed but never used, so a misspelt sedative can hide a competing cause.', 'handoff, session 4b'],
  ['CTCAE grading and Grade 5 are not built (out of scope for this proof of concept).', 'clinical-methods §8; handoff, session 4b'],
  ['Adults only: patients under 18, CAPD assessments, developmental delay, a record of Grade 5 and a documented death are out of scope and get no category.', 'clinical-methods §5; reference/dev-v1/README.md'],
  ['The locked set (written after the pipeline freeze, in a separate repository) has not been evaluated; no locked-set result exists yet.', 'handoff, Step 6 part 1'],
]

export default function Methods({ summary }) {
  if (!summary) return <Loading label="Loading" />
  return (
    <div className="page methods">
      <div className="page-head">
        <h1>Methods &amp; limitations</h1>
        <p className="page-sub">How each field is categorised and scored, what the comparison method does, and every known limitation. Results on synthetic data are not clinical validation.</p>
      </div>

      <section className="methods-section" aria-labelledby="pipeline-title">
        <h2 id="pipeline-title">The pipeline</h2>
        <ol className="steps">
          <li><strong>Load</strong> the case: its documents (every version), its research record (every version) and the observation window.</li>
          <li><strong>Extract</strong> observations from the text with fixed phrase rules: ICE scores, level of consciousness, seizures, motor and raised-pressure signs, symptoms, competing causes and statements that an assessment could not be done. Each keeps its quote, offsets, status (present, absent, uncertain) and event time.</li>
          <li><strong>Reconstruct the timeline</strong>: event time kept apart from documentation time; signed and unsigned versions, superseded versions and the observation window applied.</li>
          <li><strong>Compare</strong> the record’s onset date and maximum grade with what the documents support, under the ASTCT grading rules written out in clinical-methods §3.</li>
          <li><strong>Categorise</strong> each field (7.1–7.8) with its evidence, add flags, and list anything the rules cannot decide as “needs human review”.</li>
        </ol>
        <p className="section-note">The pipeline is deterministic and frozen (tag <span className="mono">pipeline-freeze-v1</span>; docs/freeze.md). Every category is a potential discrepancy for human review, never a verdict (clinical-methods §7).</p>
      </section>

      <section className="methods-section" aria-labelledby="cat-title">
        <h2 id="cat-title">Discrepancy categories</h2>
        <dl className="cat-list">
          {CATEGORIES.map(([c, name, text]) => (
            <div key={c} className="cat-item">
              <dt><span className="mono cat-code">§{c}</span> {name}</dt>
              <dd>{text}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section className="methods-section" aria-labelledby="score-title">
        <h2 id="score-title">Scoring</h2>
        <p className="section-note">From docs/evaluation-spec.md §3. Each in-scope case has two fields, onset and maximum grade.</p>
        <table className="score-table">
          <tbody>
            <tr><th scope="row">Positive field</th><td>The reference category is {summary.scoring.positive.join(', ')}.</td></tr>
            <tr><th scope="row">Negative field</th><td>The reference category is {summary.scoring.negative.join(' or ')}.</td></tr>
            <tr><th scope="row">Review field</th><td>The reference category is {summary.scoring.review.join(' or ')}.</td></tr>
            <tr><th scope="row">Detection</th><td>An alert (7.1, 7.2, 7.3 or 7.8) on a positive field. Any alert category counts.</td></tr>
            <tr><th scope="row">Miss</th><td>A positive field with no alert.</td></tr>
            <tr><th scope="row">False alert</th><td>An alert on a negative field.</td></tr>
            <tr><th scope="row">Review flag</th><td>7.4 or 7.5 from the method. Never counted as a detection or a false alert.</td></tr>
            <tr><th scope="row">“review: …” result</th><td>A field the method could not decide. Neither an alert nor a review flag; shown in this app as “needs human review”.</td></tr>
            <tr><th scope="row">Precision · Recall · F1</th><td>detections ÷ (detections + false alerts) · detections ÷ positive fields · 2PR ÷ (P + R).</td></tr>
            <tr><th scope="row">Exact agreement</th><td>The share of in-scope fields where the category equals the reference category.</td></tr>
            <tr><th scope="row">Out of scope</th><td>Scored only on whether the case is flagged out of scope with the same reason; never part of the discrepancy measures.</td></tr>
            <tr><th scope="row">Evidence-quote validity</th><td>The share of evidence references whose quote equals the document text at their offsets.</td></tr>
          </tbody>
        </table>
        <p className="section-note">No significance tests or confidence intervals: the splits are too small for them to mean much (evaluation-spec §3).</p>
      </section>

      <section className="methods-section" aria-labelledby="base-title">
        <h2 id="base-title">Baseline A: conventional validation</h2>
        <p>
          What a careful data manager would check without reconstructing event time, built to be as strong as such checks can be
          (evaluation-spec §4). It uses the same extracted observations as ReSauce, the latest version of each document, and dates
          every finding by when its note was written. It has no attribution or competing causes, no observation window and no record
          history. It can give 7.1, 7.2, 7.3, 7.7 or 7.8 only. Baseline B (a language model) has not been run.
        </p>
      </section>

      <section className="methods-section" aria-labelledby="lim-title">
        <h2 id="lim-title">Limitations</h2>
        <h3>Reported with every result (resauce/evaluate.py)</h3>
        <ul className="lim-list">
          {summary.limitations.map((l) => <li key={l}>{l}</li>)}
        </ul>
        <h3>Recorded in the project documents</h3>
        <ul className="lim-list">
          {MORE_LIMITATIONS.map(([text, source]) => (
            <li key={text}>{text} <span className="lim-source">{source}</span></li>
          ))}
        </ul>
      </section>
    </div>
  )
}
