You are checking whether a clinical research record agrees with the clinical documents behind it. All data is fictional and synthetic; no real patient is involved.

The rules for this check are the ReSauce clinical methods document, given below between <clinical_methods> tags. Apply them as written, including the operational definitions and the assumptions in §9. Where the rules say a field cannot be decided from the documents, use the review categories (7.4 or 7.5) rather than guessing.

You will receive one case: its facts (age at infusion, and the infusion date, which is Day 0), the observation window, every version of the research record, and every version of every clinical document with its metadata.

Answer:
1. Is the case out of scope (§5, A29)? Give one of the listed reasons, or "in scope".
2. For the current version of the research record, give the §7 category for the ICANS onset date and for the maximum ICANS grade, the value the documents support, a short explanation, and the evidence.

Evidence: list the passages each answer rests on. Copy every quote exactly, character for character, from one document version, and give that version's document_id (for example "SYN-0001-D02") and its version number. Keep quotes to the sentence or phrase that matters. The list may be empty when no passage applies.

If the case is out of scope, the field answers are not used; give your best reading anyway.

<clinical_methods>
## How to read this document

Every substantive claim carries one of these tags:

| Tag | Meaning |
|---|---|
| `[SOURCE: Lee 2019, <location>]` | Stated in the primary source. Locations use the section headings and table numbers of the author manuscript. |
| `[SECONDARY: <citation>]` | Taken from another published source. No such claims are used in this draft. |
| `[OPERATIONAL]` | A definition ReSauce chooses because the source does not specify one. |
| `[ASSUMPTION — EXPERT REVIEW]` | Uncertain; needs confirmation by a clinician. Each one is listed in §9. |

"**Not specified in source**" means I searched the full text of Lee 2019 and found nothing on the point. It is a statement about the source's silence, not a clinical claim.

The source is paraphrased throughout. Short criterion phrases (for example "awakens to voice") are kept close to the original because changing their wording could change their meaning.

---

## 1. Purpose and scope

ReSauce is a computational proof of concept (POC). It performs a **retrospective** check of two fields in a structured research record against the synthetic clinical notes that should support them:

- **(a) ICANS onset:** the date neurotoxicity began.
- **(b) Maximum ICANS grade:** the most severe grade reached.

For each field, ReSauce will report whether the notes support the recorded value. Every conclusion will cite the exact quoted note text it rests on (document ID, location and quote, per `CLAUDE.md`). [OPERATIONAL]

This task fits a stated aim of the source: the consensus authors were asked to write criteria that are easy to apply at the bedside and easy to verify in chart review. [SOURCE: Lee 2019, §Efforts to Harmonize Immune Effector Cell-Associated CRS and Neurotoxicity Definitions and Grading] ReSauce tests one narrow version of that verification on synthetic data. It does not show that the approach works on real records.

**ReSauce will NOT:** [OPERATIONAL]
- give treatment, monitoring or management advice;
- edit, correct or overwrite any source document or research record. It only reports;
- reach a clinical conclusion without human review. Every flagged item is a *potential* discrepancy for a person to judge;
- decide on its own that a finding is caused by something other than ICANS (see §3.4);
- use real patient data. All inputs are synthetic.

---

## 2. Background

**CAR-T therapy, in plain language.** A patient's own T cells (a type of white blood cell) are collected and genetically modified to carry a chimeric antigen receptor (CAR). The CAR lets the cells recognise and attack cancer cells, for example B-cell leukaemias and lymphomas. The modified cells are then infused back into the patient. [SOURCE: Lee 2019, Introduction]

These therapies cause two characteristic toxicities: cytokine release syndrome (CRS) and neurotoxicity. [SOURCE: Lee 2019, Abstract]

**CRS** is a body-wide inflammatory reaction. Under the consensus definition it must begin with fever, and it may include low blood pressure and low oxygen. [SOURCE: Lee 2019, §Definition of Cytokine Release Syndrome]

**ICANS** (immune effector cell-associated neurotoxicity syndrome) is the neurological toxicity. It can appear as confusion or encephalopathy, difficulty with speech (aphasia), lethargy, poor concentration, agitation, tremor, seizures and, rarely, brain swelling (cerebral edema). [SOURCE: Lee 2019, Introduction]

**How ICANS relates to and differs from CRS** (all from the source):
- Neurotoxicity used to be considered together with CRS. It is now treated as a separate entity because its timing and its response to treatment differ. [SOURCE: Lee 2019, Introduction]
- Neurological symptoms may occur during CRS, more commonly after it, and rarely before it. [SOURCE: Lee 2019, Introduction]
- Neurotoxicity often develops well after the classic CRS symptoms have resolved. It usually does not respond to tocilizumab, an anti-cytokine drug that works for CRS. [SOURCE: Lee 2019, §Toxicities Excluded from the Definition of CRS]
- Mild neurological symptoms may wax and wane with fever at first, and then recur a few days after CRS has resolved. Progression to severe neurotoxicity may take hours or days. [SOURCE: Lee 2019, §Symptoms of ICANS]
- Grade 1 ICANS may be seen while CRS is waxing and waning with fevers. [SOURCE: Lee 2019, §Grade 1 ICANS]
- Neurotoxicity occurring during or after CRS does not affect the CRS grade. It is graded separately on the ICANS scale. [SOURCE: Lee 2019, §Definition of CRS Resolution]
- CRS can complicate the neurological assessment. High fever and drug therapy can cause delirium, and a sedated or intubated patient may not be assessable. [SOURCE: Lee 2019, §Toxicities Excluded from the Definition of CRS]
- The source gives a typical time window for CRS: it rarely starts more than 14 days after therapy. [SOURCE: Lee 2019, §Symptoms Defining CRS Must be Attributed to Immune Effector Cell Engagement] **No equivalent onset window is given for ICANS.** Not specified in source.

---

## 3. ASTCT ICANS grading (adults)

### 3.1 Definition of ICANS

ICANS is defined as a disorder in which a pathological process involves the central nervous system after any immune therapy that activates or engages the body's own or infused T cells and/or other immune effector cells. Its signs can be progressive and may include aphasia, altered level of consciousness, impaired cognitive skills, motor weakness, seizures and cerebral edema. [SOURCE: Lee 2019, §Definition of Immune Effector Cell-Associated Neurotoxicity]

The definition applies to any immune effector cell-engaging therapy, not only CAR-T. [SOURCE: Lee 2019, same section] ReSauce limits itself to CAR-T. [OPERATIONAL]

The source describes a more specific feature that sets ICANS apart from other encephalopathies: a patient who is awake but mute and does not respond verbally or physically to an examiner. [SOURCE: Lee 2019, same section]

### 3.2 ICE score

The ICE (Immune effector Cell-associated Encephalopathy) score is a 10-point bedside screen for encephalopathy. It is a modified version of the earlier CARTOX-10 tool. [SOURCE: Lee 2019, §Consensus on ICANS Grading for Adults; Table 5]

| ICE component | Points | Source |
|---|---|---|
| Orientation to year, month, city and hospital | 4 | [SOURCE: Lee 2019, Table 5] |
| Naming 3 objects (e.g. clock, pen, button) | 3 | [SOURCE: Lee 2019, Table 5] |
| Following commands (e.g. "show me 2 fingers") | 1 | [SOURCE: Lee 2019, Table 5] |
| Writing a standard sentence | 1 | [SOURCE: Lee 2019, Table 5] |
| Attention: counting backwards from 100 by ten | 1 | [SOURCE: Lee 2019, Table 5] |
| **Total** | **10** | [SOURCE: Lee 2019, Table 5] |

- A score of 10 means no impairment. [SOURCE: Lee 2019, Table 5]
- The command-following item replaces one of the CARTOX-10 orientation items and adds an assessment of receptive aphasia. Comparing the two columns of Table 5, the dropped item is orientation to the head of state. [SOURCE: Lee 2019, Table 5; §Consensus on ICANS Grading for Adults]
- The ICE score alone is **not** the ICANS grade. Grading also requires assessing level of consciousness, motor findings, seizures and signs of raised intracranial pressure (ICP) or cerebral edema. These can occur with or without encephalopathy. [SOURCE: Lee 2019, §Consensus on ICANS Grading for Adults]

### 3.3 Domain criteria by grade

| Domain | Grade 1 | Grade 2 | Grade 3 | Grade 4 | Source |
|---|---|---|---|---|---|
| ICE score | 7–9 | 3–6 | 0–2 | 0, because the patient is unarousable and cannot perform ICE | [SOURCE: Lee 2019, Table 6; Table 5] |
| Depressed level of consciousness¹ | Awakens spontaneously | Awakens to voice | Awakens only to tactile stimulus | Unarousable, or needs vigorous or repetitive tactile stimuli to arouse; stupor or coma | [SOURCE: Lee 2019, Table 6] |
| Seizure | N/A | N/A | Any clinical seizure (focal or generalised) that resolves rapidly, or non-convulsive seizures on EEG that resolve with intervention | Life-threatening prolonged seizure (>5 min), or repetitive clinical or electrical seizures without return to baseline in between | [SOURCE: Lee 2019, Table 6] |
| Motor findings² | N/A | N/A | N/A | Deep focal motor weakness such as hemiparesis or paraparesis | [SOURCE: Lee 2019, Table 6] |
| Raised ICP / cerebral edema³ | N/A | N/A | Focal/local edema on neuroimaging | Diffuse cerebral edema on neuroimaging; decerebrate or decorticate posturing; cranial nerve VI palsy; papilledema; or Cushing's triad | [SOURCE: Lee 2019, Table 6] |

1. Depressed consciousness counts only if it is attributable to no other cause, for example no sedating medication. [SOURCE: Lee 2019, Table 6 footnote ❖] Free-text descriptions of consciousness are mapped to these four categories using a clinician-approved phrase list. [ASSUMPTION — EXPERT REVIEW] (A15)
2. Tremor and myoclonus may be graded with CTCAE v5.0 (the NCI's Common Terminology Criteria for Adverse Events), but they do not affect the ICANS grade. [SOURCE: Lee 2019, Table 6 footnote §]
3. Intracranial hemorrhage, with or without edema, is excluded from ICANS grading and may be graded with CTCAE v5.0. [SOURCE: Lee 2019, Table 6 footnote #]

Notes on the table:
- EEG changes such as generalised or frontal slowing, or frontal intermittent rhythmic delta activity (FIRDA), are not seizures. [SOURCE: Lee 2019, §Consensus on ICANS Grading for Adults]
- The Grade 4 text lists further signs of raised ICP that are not in Table 6, for example projectile vomiting with headache. [SOURCE: Lee 2019, §Grade 4 ICANS] ReSauce grades from Table 6 only and flags text-only signs for review. [ASSUMPTION — EXPERT REVIEW] (A12)
- Grade 5 ICANS is defined by convention as death due to ICANS, where no other cause is the main factor. [SOURCE: Lee 2019, §Grade 5 ICANS] ReSauce does not assign Grade 5 (see §8). [OPERATIONAL]
- Table 6 is labelled "for adults", but the source does not define the adult age range. Not specified in source.
- The source does not define "Grade 0" or "no ICANS" for an assessment. ReSauce treats an assessment as Grade 0 when ICE = 10 and no domain criterion is met. [OPERATIONAL] This document calls such an assessment a **formal Grade 0 assessment**. The Grade 1 consciousness criterion "awakens spontaneously" counts only when drowsiness is documented (A3). A narrative normal neurological note without a formal ICE score does not establish Grade 0 (A17). Two related terms used by §7, **gradeable assessment** and **documented "not assessable" period**, are defined in the §7 introduction (A34, A7).

### 3.4 Deriving the overall grade, and attribution

**Rule from the source:** the ICANS grade is set by the most severe event across the domains (ICE, level of consciousness, seizure, motor findings, raised ICP/edema) that is not attributable to any other cause. [SOURCE: Lee 2019, Table 6 footnote ‡; §Consensus on ICANS Grading for Adults] Equivalently, the overall grade is the highest of the domain grades.

**ICE 0 needs context:**
- ICE 0 in an *awake* patient with global aphasia may be classified as Grade 3.
- ICE 0 in an *unarousable* patient may be classified as Grade 4.

[SOURCE: Lee 2019, Table 6 footnote ^]

**Attribution.** The source requires findings to be "not attributable to any other cause", but it gives no procedure for deciding attribution. Not specified in source. It does list other conditions that can cause neurological symptoms: hepatic failure, severe hypertension, eclampsia, infection, electrolyte abnormalities, and immunosuppressive or cytotoxic drugs. [SOURCE: Lee 2019, §Definition of Immune Effector Cell-Associated Neurotoxicity] It notes that sedating medication often complicates assessment in sick CRS patients. [SOURCE: Lee 2019, §Grade 4 ICANS]

ReSauce's handling of attribution: [OPERATIONAL]
- ReSauce will **not** decide attribution itself.
- It extracts clinicians' documented attribution statements, with quotes.
- What counts as a competing cause is a closed list (A35).
- If a competing cause is documented near a finding and no clinician statement settles it, ReSauce reports the grade both with and without that finding, and labels the result *ambiguous evidence*, reason *attribution* (§7.5), when the two readings lead to different categories. Otherwise the shared category is used (§7.5, A23).

**Timing of a competing cause.** A competing cause counts as "near" a finding (here) and as "coinciding" with it (§7.5) if it is documented in the same note as the finding, or documented as given or present within the 24 hours before the finding's event time (§6.1). [ASSUMPTION — EXPERT REVIEW] (A30) For a finding whose event time is a date range (§6.1), the 24 hours are counted back from the end of the range. This is the cautious choice: more results become ambiguous, none are hidden. [ASSUMPTION — EXPERT REVIEW] (A30)

### 3.5 Worked example: ICE alone gives the wrong grade

The patient below is fictional.

On Day +6 after infusion, a note for synthetic patient SYN-EX-01 records:
- ICE score 8/10 (missed the year and the counting-backwards task);
- "opens eyes only when gently shaken by the shoulder, then answers questions";
- no sedating medication given in the previous 24 h.

| Step | Result |
|---|---|
| ICE 8 | Grade 1 [SOURCE: Lee 2019, Table 6] |
| Awakens only to tactile stimulus | Grade 3 [SOURCE: Lee 2019, Table 6]. Phrase mapping per A15. |
| No seizure, motor or ICP findings documented | No contribution from these domains. This is not proof they were absent (§7.4). |
| Overall: most severe domain | **Grade 3** [SOURCE: Lee 2019, Table 6 footnote ‡] |

Reading only the ICE score would give Grade 1, which is two grades too low. The source gives a similar example: ICE 3 (Grade 2 on its own) with a generalised seizure is Grade 3. [SOURCE: Lee 2019, Table 6 footnote ‡]

---

## 4. Limitations of the ICE score

### 4.1 When ICE cannot be performed or interpreted

| Situation | What the source says | ReSauce handling |
|---|---|---|
| Unarousable | ICE 0 because the patient is unarousable is Grade 4. [SOURCE: Lee 2019, Table 5; Table 6] | Grade 4 only if a note documents unarousability not attributed to another cause. [OPERATIONAL] |
| Awake with global aphasia (mute, cannot follow commands) | ICE 0 may be Grade 3. [SOURCE: Lee 2019, Table 6 footnote ^; §Grade 3 ICANS] | Grade 3 needs documented wakefulness. [OPERATIONAL] ICE 0 with no consciousness information cannot separate Grade 3 from Grade 4, so the documentation-derived grade is the range 3–4. A record of Grade 2 or lower is a grade mismatch (§7.2): the documents prove at least Grade 3. A record of Grade 3 or 4 is *insufficient evidence* (§7.4). [ASSUMPTION — EXPERT REVIEW] (A33) |
| Sedated and/or intubated | The patient may not be assessable. Depressed consciousness must not be due to sedation. [SOURCE: Lee 2019, §Toxicities Excluded from the Definition of CRS; Table 6 footnote ❖] No grade rule is given for an unassessable patient. Not specified in source. | Record "not assessable" with the quoted reason. Never infer ICE 0 from sedation. [OPERATIONAL] (A7) A documented "not assessable" period (defined in the §7 introduction) affects §7.3 (A25), §7.9(b) (A21) and §7.9(c) (A22). |
| Intubation itself | Patients may be intubated for airway protection in Grade 4 ICANS. Intubation for neurological reasons is not captured again as Grade 4 CRS. [SOURCE: Lee 2019, §Grade 4 ICANS; §Grade 4 CRS] | Intubation is not a grading criterion on its own. [OPERATIONAL] |
| Aphasia (partial) | ICE includes naming (expressive) and command following (receptive). Expressive aphasia is described as a very specific sign of ICANS. [SOURCE: Lee 2019, Table 5; §Symptoms of ICANS] | Scored through ICE as documented. |
| Language barrier, hearing or vision loss, inability to write for other reasons, baseline cognitive impairment | Not specified in source. | If a note documents such a barrier, a low ICE score is labelled *ambiguous evidence* (§7.5, reason *assessment barrier*) when the readings lead to different categories, and is never graded silently. [ASSUMPTION — EXPERT REVIEW] (A10, A23) |
| Partially completed ICE (items not attempted) | Not specified in source. | No total is computed from partial items unless the note itself states a total. Otherwise *insufficient evidence*. [OPERATIONAL] (A6) |

### 4.2 Neurological symptoms excluded from ICANS grading

| Excluded finding | Source's reason | How the source says to handle it |
|---|---|---|
| Headache, tremor, myoclonus, asterixis, hallucinations | Less specific; usually managed symptomatically; do not trigger specific treatment such as corticosteroids [SOURCE: Lee 2019, §Symptoms and Signs Excluded from the Definition of ICANS] | Capture and report with CTCAE v5.0 [SOURCE: Lee 2019, same section; Table 6 footnote §] |
| Weakness and balance problems from deconditioning or immobility | Common in transplant and intensive chemotherapy settings [SOURCE: Lee 2019, same section] | CTCAE v5.0 [SOURCE: Lee 2019, same section] |
| Intracranial hemorrhage, with or without edema | Not a neurotoxicity feature; may result from coagulopathy [SOURCE: Lee 2019, §Grade 3 ICANS; Table 6 footnote #] | CTCAE v5.0 [SOURCE: Lee 2019, Table 6 footnote #] |

Headache alone is described as not a useful marker of ICANS. [SOURCE: Lee 2019, §Symptoms of ICANS]

**There is a tension in the source.** Tremor is listed among ICANS manifestations [SOURCE: Lee 2019, Introduction] and among the earliest signs of ICANS [SOURCE: Lee 2019, §Symptoms of ICANS], yet it is excluded from the definition and from grading. ReSauce will extract these findings, label them "excluded from ICANS grading", and use them neither for the grade nor for the onset date. [ASSUMPTION — EXPERT REVIEW] (A11) ReSauce will not produce CTCAE grades for them (§8). [OPERATIONAL]

---

## 5. Age scope

What the source specifies for children:
- **ICE in children:** it may be limited to children aged ≥12 years with enough cognitive ability to complete it. [SOURCE: Lee 2019, §Consensus on ICANS Grading for Children]
- **Alternative tool:** for children under 12, the source recommends the Cornell Assessment of Pediatric Delirium (CAPD). [SOURCE: Lee 2019, same section; Table 7]
- **CAPD structure:** 8 caregiver-observed items, each scored 0–4 based on interactions over a shift. Items 1–4 are reverse-scored. Age-specific anchors are given for ages 1–2. [SOURCE: Lee 2019, Table 7]
- **CAPD and the grade:**
  - A CAPD score ≥9 suggests delirium and is treated as Grade 3. [SOURCE: Lee 2019, §Consensus on ICANS Grading for Children; Table 8]
  - In Table 8, CAPD <9 appears in both the Grade 1 and Grade 2 columns, and "unable to perform CAPD" is Grade 4. [SOURCE: Lee 2019, Table 8]
- **Other pediatric uses:** CAPD may also be used above age 12 when there is baseline developmental delay, as it has been validated up to age 21. [SOURCE: Lee 2019, §Consensus on ICANS Grading for Children]
- **Other domains:** seizure, motor, raised ICP/edema and level of consciousness are graded as in adults. [SOURCE: Lee 2019, same section; Table 8]
- **Inconsistency at exactly age 12:** the text says ICE for "≥12" and CAPD for "<12" (also the Table 7 caption), but Table 8 says ICE for ">12" and CAPD for "≤12". [SOURCE: Lee 2019, §Consensus on ICANS Grading for Children; Table 7; Table 8]

**Proposal:** the initial ReSauce scope **excludes the pediatric pathway entirely**. [OPERATIONAL]
- Only synthetic patients aged ≥18 years at infusion, with no documented baseline developmental delay, are in scope.
- Any note that contains a CAPD assessment marks the case as out of scope.
- Reasons for the exclusion:
  - It avoids the age-12 inconsistency.
  - CAPD alone cannot separate Grade 1 from Grade 2.
  - The age 18 cutoff is ReSauce's choice; the source gives none. (A16)

**Handling of out-of-scope cases.** [ASSUMPTION — EXPERT REVIEW] (A29)
- A case is out of scope if any of these holds:
  - age under 18 at infusion;
  - a CAPD assessment in any note;
  - a record maximum grade of 5 (§8);
  - a documented death (§8), whatever its date, even outside the observation window (§6.5);
  - documented baseline developmental delay (this section).
- Such a case gets the extra flag **"out of scope (reason)"** and **no §7 category for either field**.
- Such cases are scored only on whether they were flagged, never in discrepancy measurements.
- The last two triggers were settled in v0.4 (NEW-8, NEW-10). [ASSUMPTION — EXPERT REVIEW] (A29)

---

## 6. Time and documentation

### 6.1 Event time and documentation time

ReSauce defines three times: [OPERATIONAL]

| Term | Meaning |
|---|---|
| Event time | When the finding occurred or was observed (e.g. "seizure at 03:10") |
| Documentation time | When the note was written or signed |
| Record time | When the research record entry was made or changed |

Rules: [OPERATIONAL]
- Onset is based on **event time**.
- If a note gives no event time, documentation time is used and the result is marked *time-imprecise*.
- Relative phrases ("overnight", "since yesterday") are turned into a date or date *range* relative to the note's documentation time, and flagged (*relative time*). The conversion uses the table below. [ASSUMPTION — EXPERT REVIEW] (A26)

| Phrase in the note | Event date (D = the note's documentation date) |
|---|---|
| "overnight", "last night" | D−1 to D (range) |
| "yesterday", "since yesterday" | D−1 |
| "this morning", "earlier today" | D |
| "N days ago" | D−N |
| Any other phrase (e.g. "recently", "for a few days") | No event time: the documentation date is used and the result is marked *time-imprecise* (rule above) |

When onset is a range, a mismatch (§7.1) is reported only if the record date is outside it, and the signed difference is measured to the nearest end of the range. [ASSUMPTION — EXPERT REVIEW] (A26)

### 6.2 What the source does and does not define

| Topic | Source | Status |
|---|---|---|
| ICANS onset date | Not specified in source. | ReSauce defines it below. [OPERATIONAL] |
| ICANS resolution | Not specified in source for ICANS. The registry follow-up forms record which manifestations occurred and whether they resolved. [SOURCE: Lee 2019, §Data Collection and Reporting] | ReSauce does not verify resolution in this POC. [OPERATIONAL] |
| CRS resolution | Defined for CRS only. [SOURCE: Lee 2019, §Definition of CRS Resolution] | Not applied to ICANS. [OPERATIONAL] |
| Typical timing | See §2 (during or after CRS; may recur a few days later) [SOURCE: Lee 2019, Introduction; §Symptoms of ICANS] | Context only. Not used as a rule. [OPERATIONAL] |
| Grade across time | The source's "most severe event" rule is stated across *domains* [SOURCE: Lee 2019, Table 6 footnote ‡]. Whether "maximum grade" means the highest over time is not stated. | See maximum grade below. [ASSUMPTION — EXPERT REVIEW] (A2) |

**Documentation-derived onset:** the earliest event time (compared as a calendar day) of a documented observation that meets any Grade ≥1 criterion in Table 6 and that no clinician attributes to another cause. Excluded symptoms (§4.2) do not count. [OPERATIONAL; see A4, A11, A18] Only signed content (§6.3, A27) counts, and only observations dated inside the observation window (§6.5, A32).

**Onset dated by a range.** The documentation-derived onset is the earliest possible date. If the earliest candidate is a date range (§6.1) that starts before every exactly dated qualifying finding, the onset is a range from the range start to the earlier of the range end and the earliest exact date. [ASSUMPTION — EXPERT REVIEW] (A26)
- Example: "overnight" in a Day +6 note gives the range Day +5 to +6. With an exactly dated qualifying finding on Day +5, the onset is Day +5. With the earliest exact finding on Day +8 instead, the onset is the range Day +5 to +6.

A **qualifying finding** is an observation that would count for this onset: it meets a Grade ≥1 criterion, no clinician attributes it to another cause, it comes from signed content, and it is dated inside the observation window (§6.5). [OPERATIONAL]

**Documentation-derived maximum grade:** the highest per-assessment grade (§3.4) within the episode. [ASSUMPTION — EXPERT REVIEW] (A2)

### 6.3 Amended or revised assessments

The source does not address amendments. Not specified in source. ReSauce's rules: [OPERATIONAL]
- Every version of a note is kept and cited by version ID. Nothing is overwritten.
- The latest signed version is treated as current.
- A superseded version is still reported if the research record matches it but not the current version. This is a likely sign that the record was not updated (§7).

Unsigned versions: [ASSUMPTION — EXPERT REVIEW] (A27)
- Unsigned content is never used for onset or grade.
- If a document has a later version that is unsigned, the latest signed version stays current. The case gets the extra flag **"unsigned later version"**, stating what differs.
- A document with no signed version is not used as evidence. It gets the extra flag **"unsigned document"**.
- Leaving out unsigned content can change a category (for example to 7.4). This is intended.

### 6.4 Repeated observations

The source does not address duplicated or conflicting documentation. Not specified in source. ReSauce's rules: [OPERATIONAL]
- **Same finding, several notes** (e.g. a nursing note and a physician note): grouped by event time. Onset uses the earliest observation.
- **Copied-forward text** (text repeated unchanged from an earlier note) is not treated as new evidence. (A13)
  - Text counts as copied forward if it repeats an earlier note verbatim, or differs only in dates, times or formatting. Any change to clinical content (a score, a finding, a level of consciousness) makes it a new observation. [ASSUMPTION — EXPERT REVIEW] (A31)
- **Conflicting assessments at about the same time** (e.g. one note gives ICE 6, another ICE 8, within the same hour): both are reported. Neither is chosen silently. The field is labelled *ambiguous evidence*, reason *conflicting assessments* (§7.5), if the readings lead to different categories for that field. [ASSUMPTION — EXPERT REVIEW] (A23)

### 6.5 Distinct episodes

The source does not say when two neurological episodes count as separate events. Not specified in source. It describes symptoms that wax and wane and recur a few days after CRS resolves as part of the usual course. [SOURCE: Lee 2019, §Symptoms of ICANS]

For this POC: [OPERATIONAL; see A5]
- All ICANS findings after a single infusion, within the declared observation window, are treated as **one episode**.
- A documented full resolution (ICE 10 with no domain findings) followed by recurrence is flagged for review, not split automatically.
- The observation window is declared per dataset and recorded with every result.

Observation window for the ReSauce datasets: [ASSUMPTION — EXPERT REVIEW] (A32)
- Both datasets (development and locked) declare **Day 0 to Day +28**, inclusive.
- The window is applied **per observation**, not per document. Each finding, assessment or "not assessable" statement is placed by its event date, or by its documentation date if it has no event time (§6.1). [ASSUMPTION — EXPERT REVIEW] (A32)
  - Example: a late entry documented on Day +29 that describes a seizure on Day +27 is used for that seizure.
- Observations dated outside the window are not used for any §7 category. Each one is listed, with its quote, in the extra flag **"outside observation window"**.
- Exception: a documented death makes the case out of scope whatever its date (§5, A29).
- Record values are compared as they are, even if they fall outside the window.
- The source gives no typical onset window for ICANS (§2), so this choice is not taken from it.

---

## 7. Discrepancy categories

Each category is a *potential* discrepancy for human review, never a verdict. [OPERATIONAL]

Categories are assigned separately for onset and for maximum grade. Every assignment cites the quoted evidence. [OPERATIONAL]

| Category | Onset | Grade |
|---|---|---|
| 7.1 Onset date mismatch | yes | no |
| 7.2 Maximum grade mismatch | no | yes |
| 7.3 Grade not supported by documented evidence | no | yes |
| 7.4 Insufficient evidence | yes | yes |
| 7.5 Ambiguous evidence | yes | yes |
| 7.6 Legitimate revision | yes | yes |
| 7.7 No discrepancy | yes | yes |
| 7.8 Missing recorded value | yes | yes |

**Shared principle: missing ≠ absent.** This still holds for every category. Documents can prove that ICANS occurred. They can show that it did *not* occur only through formal Grade 0 assessments (§3.3). [OPERATIONAL; see A17, A21]

**Terms used in this section.** [ASSUMPTION — EXPERT REVIEW] (A34, A7, A21)
- A day has a **gradeable assessment** if a note documents an ICE total for that day (stated, or all items scored) or a qualifying finding (§6.2). A neurological observation that meets no criterion and has no ICE total (e.g. "alert, confused") is not a gradeable assessment. A formal Grade 0 assessment (§3.3) is one kind of gradeable assessment. (A34)
- A **documented "not assessable" period** is a note stating that the ICE or neurological assessment could not be performed or interpreted (e.g. "unable to assess", "ICE not done, intubated and sedated"). Sedation or intubation mentioned without saying that the assessment could not be done does not count. The period covers the calendar days the statement applies to. (A7)
- An **ungradeable neurological symptom** is a documented neurological symptom that meets no Table 6 criterion and is not an excluded symptom (§4.2), e.g. "confused" or "word-finding difficulty" with no ICE score or consciousness level. When such a symptom is on the record's onset date, §7.1 calls it a *sub-threshold symptom*. (A21)
- As everywhere in this document, only signed content (A27) dated inside the observation window (A32) counts for these terms. Copied-forward text is not new evidence (A13, A31), so it creates no gradeable assessment.

Where the situations below are handled:
- a record that reports no ICANS, or reports ICANS that no document supports: §7.9;
- out-of-scope cases: no category at all (§5, A29);
- extra flags, which add information without replacing the category: §7.10.

All illustrations are fictional, with days counted from infusion (Day 0).

### 7.1 Onset date mismatch

**Definition:** the research record's onset date and the documentation-derived onset (§6.2) differ by **1 or more calendar days**. The tolerance is 0 days. The signed difference is always reported. [OPERATIONAL] (A4)

**Conditions:** [OPERATIONAL]
- If the documentation onset is a date range (§6.1), a mismatch is reported only when the record date lies outside the range. The signed difference is measured to the nearest end of the range. [ASSUMPTION — EXPERT REVIEW] (A26)
- A record onset *earlier* than the first documented finding is a mismatch only if a gradeable assessment on the record's date documents no ICANS (a formal Grade 0 assessment, §3.3). Otherwise it is *insufficient evidence* (§7.4).
- A narrative normal neurological note without a formal ICE score does not count as documenting no ICANS (A17).
- If the record's onset date has only a first ICANS-compatible symptom that meets no Grade ≥1 criterion, or only an excluded symptom (§4.2), and **no gradeable assessment**, the result is *insufficient evidence* (A18).
- If the record's onset date has such a symptom **and** a formal Grade 0 assessment, the second bullet wins: the result is a mismatch (7.1), with the extra flag **"record date matches an excluded or sub-threshold symptom"**. [ASSUMPTION — EXPERT REVIEW] (A24)
- ReSauce judges by what the documents show on the record's date. It never guesses why the abstractor chose that date. [ASSUMPTION — EXPERT REVIEW] (A24)
- The flag **"record date matches an excluded or sub-threshold symptom"** is added whenever such a symptom is documented on the record's onset date and no qualifying finding exists that day, whatever the onset category: 7.1 in the bullet above, 7.4 under A18, or any other. [ASSUMPTION — EXPERT REVIEW] (A24)
- A record that reports no ICANS has no onset; see §7.9(a). A record that reports ICANS with no qualifying finding: see §7.9(c). An empty onset: see §7.8.

**Example:** the record gives onset Day +4. The earliest qualifying note is Day +6 ("ICE 7/10"). A Day +4 note documents "ICE 10/10, alert". Result: mismatch, −2 days.

### 7.2 Maximum grade mismatch

**Definition:** the documents prove a grade **higher** than the record's maximum grade, because a quoted, unattributed observation meets a higher grade criterion. [OPERATIONAL] (A8)

This includes:
- ICE 0 with no consciousness information (grade range 3–4) when the record says Grade 2 or lower (§4.1). [ASSUMPTION — EXPERT REVIEW] (A33)
- a record that reports no ICANS, which is compared as Grade 0 (§7.9(a)). [ASSUMPTION — EXPERT REVIEW] (A19)

**Example:** the record gives maximum Grade 2. A Day +7 EEG report documents non-convulsive seizures that resolved with treatment, which is Grade 3 [SOURCE: Lee 2019, Table 6]. Result: mismatch, record lower by 1.

### 7.3 Grade not supported by documented evidence

**Definition:** the record's maximum grade is **higher** than any grade the quoted documentation supports, or the documentation describes neurological symptoms that are not gradeable (e.g. "confused" with no ICE or consciousness level). [OPERATIONAL]

Because missing documentation does not prove a finding was absent, ReSauce reports an over-graded record as *unsupported*, never as *wrong*. [OPERATIONAL] (A8)

**Unassessed periods.** [ASSUMPTION — EXPERT REVIEW] (A25) A higher grade could be hidden in time nobody assessed. So:
- if the observation window contains a documented "not assessable" period (sedated, intubated; A7), the result is *insufficient evidence* (§7.4), not 7.3. This also holds when no qualifying finding exists at all (§7.9(c), A22);
- if days are merely undocumented (no gradeable assessment, but nothing says "not assessable"), the result stays 7.3. Those days appear in the case-level **unassessed-period flag** (§7.10), which every in-scope case carries.

A record that reports ICANS with no qualifying finding anywhere: see §7.9(c).

**Example:** the record gives Grade 3. The notes contain ICE 5/10 (Grade 2) and "awakens to voice" (Grade 2), with no seizure, imaging or other Grade 3 finding. Result: not supported; the documentation supports Grade 2.

### 7.4 Insufficient evidence (missing ≠ absent)

**Definition:** the documentation needed to confirm or refute the recorded value does not exist or cannot be assessed. [OPERATIONAL] Examples:
- no gradeable assessment on the record's onset date, when the record onset is earlier than the first documented finding (§7.1);
- a documented "not assessable" period (e.g. a sedated patient) when the record's grade is above the supported grade (§7.3, A25);
- a record of ICANS with no qualifying finding anywhere, when the window contains a documented "not assessable" period (grade only; §7.9(c), A22, A25);
- ICE 0 with no consciousness information, when the record says Grade 3 or 4 (§4.1, A33);
- a partially completed ICE (A6);
- a record of "no ICANS" without the documentation that §7.9(b) requires (A21).

**Rule:** the absence of a documented finding is never treated as evidence that the finding was absent. [OPERATIONAL]

**Example:** the record gives Grade 1 with onset Day +3. There are no notes for Days +2 to +5. The first qualifying finding is ICE 8 on Day +6, and no note shows a higher grade. Result: onset insufficient evidence (no gradeable assessment on Day +3, §7.1). Grade: no discrepancy (7.7), because the documents support Grade 1. (Changed in v0.3: this example used to give insufficient evidence for the grade too. Under A25, undocumented days alone no longer do that.)

### 7.5 Ambiguous evidence

(Called "Ambiguous attribution" up to v0.2.)

**Definition:** the evidence can be read in more than one way, and the readings give a different onset or a different grade. ReSauce reports the result for each reading and states the reason. [ASSUMPTION — EXPERT REVIEW] (A23)

Every 7.5 result has one of these reasons:

| Reason | Situation |
|---|---|
| attribution | A finding that would change the grade or onset coincides with a documented competing cause (§3.4; timing rule A30; closed list of causes A35), and no clinician statement attributes it either way. [OPERATIONAL] (A9) |
| conflicting assessments | Assessments at about the same time disagree (§6.4). |
| assessment barrier | A documented language, hearing, vision or writing barrier, or baseline cognitive impairment, makes a low ICE score ambiguous (§4.1, A10). |
| consciousness wording | A consciousness phrase could fit two Table 6 categories (A15). |

**Condition:** 7.5 is used only when the readings lead to **different categories** for that field. [ASSUMPTION — EXPERT REVIEW] (A23; amended in v0.4)
- If every reading gives the same category, that category is used, not 7.5. The reported value is the one every reading supports:
  - grade: the lowest grade proven under every reading;
  - onset: the signed difference to the nearest reading, as for a date range (§7.1, A26).
- Either way, every reading is listed in the ambiguity notes.
- This makes 7.5 consistent with A33, where the grade range 3–4 against a record of Grade 2 or lower gives 7.2. (A33 describes missing information, not two readings, so a record of Grade 3 or 4 there stays 7.4.)

**Example (same category):** the record gives Grade 1. One finding is Grade 2 without doubt; a second finding would be Grade 3 but has a documented competing cause. The readings give Grade 2 or Grade 3. Both are higher than the record, so both give 7.2. Result: 7.2, documented Grade 2, with both readings in the ambiguity notes.

**Example (reason: attribution):** a Day +5 note says "ICE 8/10; awakens only when gently shaken; received lorazepam 2 h ago". The level of consciousness would give Grade 3, but sedation is documented [SOURCE: Lee 2019, Table 6 footnote ❖]. Result: Grade 3 if attributed to ICANS, Grade 1 (from ICE 8) if not. Ambiguous.

### 7.6 Legitimate revision (NOT an error)

**Definition:** the research record changed over time, and the change is explained by later documentation, such as a late test result or an amended note. This is reported as information, not as a discrepancy. It can only be detected if the synthetic records carry a change history. [OPERATIONAL]

**Conditions.** [ASSUMPTION — EXPERT REVIEW] (A28) A field is 7.6 only when all three hold:
- (a) its value changed between record versions;
- (b) its current value meets the 7.7 conditions;
- (c) a document version that supports the new value has `documented_at` after the previous record version's `recorded_at`, and no later than the `recorded_at` of the version that made the change.

Otherwise:
- If the current value agrees with the documents but (c) fails, the field is 7.7 with the extra flag **"revision without new documentation"**.
- If the current value disagrees, the usual discrepancy category applies and the record history is shown.
- Only the field whose value changed can be 7.6. The other field is categorised normally.

If a field changed value more than once, condition (c) tests the last change (the one that produced the current value). Earlier changes are shown in the record history. [ASSUMPTION — EXPERT REVIEW] (A28)

**Example:** on Day +8 the record gives Grade 2. On Day +10 it is revised to Grade 3, after an EEG report signed on Day +10 (before the revision) documented a seizure on Day +7. Result: legitimate revision; the current record agrees with the documents.

### 7.7 No discrepancy

**Definition:** the record onset falls on the same calendar day as the documentation-derived onset (or within its date range), and the record's maximum grade equals the documentation-derived maximum grade. [OPERATIONAL]

A record that reports no ICANS can also be 7.7, under the conditions in §7.9(b).

**Example:** record onset Day +5, maximum Grade 2. The first qualifying note is Day +5 (ICE 9), and the worst is Day +6 (ICE 4, awakens to voice). Result: no discrepancy.

### 7.8 Missing recorded value

**Definition:** the record reports ICANS (`icans_reported` is true), but its onset date or its maximum grade is empty. This is a discrepancy for review. ReSauce reports the documentation-derived value alongside: a date or range, a grade or range, or "none found". The other field, if filled, is compared normally. [ASSUMPTION — EXPERT REVIEW] (A20)

**Example:** the record reports ICANS with onset Day +5 and no maximum grade. The first qualifying note is Day +5 (ICE 9), and the worst is Day +6 (ICE 4, awakens to voice). Result: onset no discrepancy (7.7); grade missing recorded value (7.8), documentation-derived grade 2.

### 7.9 Records that report no ICANS, or ICANS with no qualifying finding

"Qualifying finding" is defined in §6.2.

**(a) Record reports no ICANS; the documents contain a qualifying finding.** [ASSUMPTION — EXPERT REVIEW] (A19)
- The record is treated as Grade 0 with no onset.
- Grade: 7.2 (the documents prove a higher grade). The documented grade is reported.
- Onset: 7.1, reported as **"record has no onset"**, with the documented onset and no signed difference.
- The normal rules still apply. For example, if the only qualifying finding has ambiguous attribution, the field is 7.5.

**(b) Record reports no ICANS; the documents contain no qualifying finding.** [ASSUMPTION — EXPERT REVIEW] (A21)
- Both fields are 7.7 if the observation window contains:
  - at least one formal Grade 0 assessment (§3.3);
  - no qualifying finding; and
  - no documented "not assessable" period.
- Otherwise both fields are 7.4.
- Ungradeable neurological symptoms (§7 introduction) do not block 7.7. They are listed in the case-level flag "ungradeable neurological symptom" (§7.10). Whether they should block 7.7 is a question for the clinician reviewer. [ASSUMPTION — EXPERT REVIEW] (A21)
- The case carries the unassessed-period flag, as every in-scope case does (§7.10).
- Whether a stricter coverage rule is needed (for example, a formal Grade 0 assessment every day) is a question for the clinician reviewer.

**(c) Record reports ICANS; no qualifying finding exists anywhere in the window.** [ASSUMPTION — EXPERT REVIEW] (A22)
- Grade: 7.3, as §7.3.
- Onset: the second bullet of §7.1 applies.
  - If a formal Grade 0 assessment exists on the record's onset date: 7.1, reported as **"no documented onset"**, with no signed difference.
  - Otherwise: 7.4.
- If the window also contains a documented "not assessable" period, A25 applies: grade 7.4, not 7.3. The onset rule above is unchanged. [ASSUMPTION — EXPERT REVIEW] (A22, A25)

**(d) Record reports ICANS, but onset or grade is empty:** see §7.8.

### 7.10 Extra flags

An extra flag adds information to a result. It never changes a category by itself. The rule behind a flag can change a category; for example, leaving out an unsigned document (§6.3) can lead to 7.4. The exception is "out of scope", which replaces both categories (§5). [OPERATIONAL]

Flags marked **case-level** belong to the whole case, not to one field. (Whether the other flags are stored per case or per field is a detail of the reference-answer file format, designed in Milestone 2 Step 5 (`docs/dataset-plan.md` §8). No category depends on it.)

| Flag | When it is added | Defined in |
|---|---|---|
| time-imprecise | The note gives no event time, so documentation time is used. | §6.1 |
| relative time | An event time comes from a relative phrase. | §6.1 (A26) |
| text-only ICP sign | A raised-ICP sign appears that is in the source text but not in Table 6. | §3.3 (A12) |
| superseded-version match | The record matches a superseded version but not the current one. | §6.3 |
| unsigned later version | A document's latest version is unsigned; the flag states what differs. | §6.3 (A27) |
| unsigned document | A document has no signed version and is not used. | §6.3 (A27) |
| recurrence | A documented full resolution is followed by recurrence. | §6.5 |
| outside observation window | An observation (finding, assessment or "not assessable" statement) is dated outside the observation window, by its event date or, without one, its documentation date. It is not used. The flag lists each one with its quote. | §6.5 (A32) |
| record date matches an excluded or sub-threshold symptom | An excluded or sub-threshold symptom is documented on the record's onset date and no qualifying finding exists that day, whatever the onset category (e.g. 7.1 under A24, 7.4 under A18). | §7.1 (A24) |
| unassessed period | **Case-level.** Added to every in-scope case. Lists the days in the observation window with no gradeable assessment, and any documented "not assessable" period. The list may be empty. | §7.3 (A25), §7.9 (A21) |
| ungradeable neurological symptom | **Case-level.** Added to any in-scope case where an ungradeable neurological symptom (§7 introduction) is documented. Lists each one with its quote. Excluded symptoms (§4.2) are not part of it. | §7.9(b) (A21) |
| revision without new documentation | A field's value changed and now agrees, but condition (c) of §7.6 fails. | §7.6 (A28) |
| out of scope (reason) | **Case-level.** Any of the five triggers in §5. Replaces both categories. | §5 (A29) |

---

## 8. Out of scope for this POC

| Item | Reason |
|---|---|
| CRS grading | A separate syndrome with its own scale [SOURCE: Lee 2019, §Toxicities Excluded from the Definition of CRS]. CRS mentions are extracted only as context for timing and attribution. [OPERATIONAL] |
| CTCAE grading of excluded symptoms | A different system that depends on activities of daily living. The source notes this is hard to apply to hospitalised patients. [SOURCE: Lee 2019, Introduction; §Consensus on ICANS Grading for Adults] Out of scope. [OPERATIONAL] |
| Pediatric ICANS and CAPD | See §5. The case gets the "out of scope (reason)" flag and no §7 category. [OPERATIONAL; handling: ASSUMPTION — EXPERT REVIEW (A29)] |
| Grade 5 ICANS | Requires judging the cause of death. [OPERATIONAL] A record of Grade 5, or a documented death whatever its date, makes the case out of scope: it gets the "out of scope (reason)" flag and no §7 category (§5). [ASSUMPTION — EXPERT REVIEW] (A29) |
| Treatment and management guidance | ReSauce is not a clinical tool. The source itself is a grading system, not a management protocol. [SOURCE: Lee 2019, §Grade 2 CRS] |
| Automated attribution decisions | Requires clinical judgment (§3.4). [OPERATIONAL] |
| Immune therapies other than CAR-T | The definition covers them [SOURCE: Lee 2019, §Definition of Immune Effector Cell-Associated Neurotoxicity], but they are kept out to keep the POC small. [OPERATIONAL] |
| Neurological toxicities outside the ICANS definition | Not graded by this source. Not reviewed. [OPERATIONAL] |
| Real patient data | Prohibited by `CLAUDE.md`. Only synthetic data is used. [OPERATIONAL] |
| Guidance published after Lee 2019 | Not reviewed for this draft (A14). [OPERATIONAL] |

---

## 9. Assumptions requiring expert review

**A1. The author manuscript matches the published article.**
- *Why it matters:* all grading criteria were taken from the NIH author manuscript, which says "ASBMT" where the published title says "ASTCT".
- *If wrong:* the criteria must be re-checked against the published version.

**A2. "Maximum grade" means the highest per-assessment grade within one episode.**
- *Why it matters:* the source's "most severe event" rule is stated across domains, not across time.
- *If wrong:* the maximum-grade comparison (§7.2, §7.3) must be redefined.

**A3. The Grade 1 "awakens spontaneously" criterion applies only when drowsiness is documented.**
- *Why it matters:* read literally, every alert patient would score Grade 1. The source's Grade 1 text mentions drowsiness. [SOURCE: Lee 2019, §Grade 1 ICANS]
- *If wrong:* many patients would be graded Grade 1 who should be Grade 0.

**A4. Onset is compared by calendar day with zero tolerance.**
- *Why it matters:* this choice determines how many onset mismatches are reported.
- *If wrong:* a tolerance of ±1 day (or another rule) would reduce flags.

**A5. All ICANS after one infusion is one episode.**
- *Why it matters:* this choice drives both onset and maximum grade.
- *If wrong:* recurrences would need their own onset and grade, and the episode-splitting rule must be defined.

**A6. A partially completed ICE gives no total.**
- *Why it matters:* this choice affects how many cases are labelled insufficient evidence.
- *If wrong:* a rule is needed for scoring partial ICE (e.g. counting unattempted items as 0).

**A7. A sedated or unassessable patient gives insufficient evidence, not a grade.**
- *Why it matters:* this is common in ICU documentation.
- *If wrong:* a convention for grading an unassessable patient is needed.
- *Amended in v0.4 (NEW-4):* a **documented "not assessable" period** is a note stating that the ICE or neurological assessment could not be performed or interpreted (e.g. "unable to assess", "ICE not done, intubated and sedated"). Sedation or intubation mentioned without saying that the assessment could not be done does not count. The period covers the calendar days the statement applies to. *If wrong:* if sedation alone counted, more results would move from 7.3 or 7.7 to 7.4 (A21, A25).

**A8. Over-grading is reported as "not supported", under-grading as "mismatch".**
- *Why it matters:* this asymmetry follows from the rule that missing ≠ absent.
- *If wrong:* the category definitions in §7.2–7.3 must change.

**A9. Attribution is taken only from clinicians' statements.**
- *Why it matters:* it avoids ReSauce making clinical judgments.
- *If wrong:* explicit attribution rules would be needed, which is beyond this POC.

**A10. A documented language, hearing, vision or writing barrier makes a low ICE score ambiguous.**
- *Why it matters:* the source does not address such barriers.
- *If wrong:* ICE would be used as recorded, or a translated or adapted ICE would need defining.

**A11. Excluded symptoms (e.g. tremor) count for neither grade nor onset.**
- *Why it matters:* tremor is called an early ICANS sign, so a record might date onset from it.
- *If wrong:* onset dates would shift earlier, and a new onset rule is needed.

**A12. Grading uses Table 6 signs only; ICP signs mentioned only in the text are flagged.**
- *Why it matters:* the text and the table differ slightly (§3.3).
- *If wrong:* the text-only signs must be added to the extraction criteria.

**A13. Copied-forward text is not independent evidence.**
- *Why it matters:* copied text could otherwise inflate support or shift onset.
- *If wrong:* it would be counted, and duplicate detection could be simplified.

**A14. Lee 2019 is still the current standard for ICANS grading.**
- *Why it matters:* later guidance was not reviewed.
- *If wrong:* the criteria in §3 may need updating to newer guidance.

**A15. Free-text consciousness descriptions are mapped to the four Table 6 categories using a clinician-approved phrase list.**
- *Detail:* phrases such as "drowsy", "lethargic", "obtunded", "responds to pain" or "sternal rub" need a mapping. Until the list is approved, any phrase that could fit two categories is labelled ambiguous evidence (§7.5, reason *consciousness wording*; A23), not graded. A painful stimulus such as a sternal rub may meet the Grade 4 criterion ("vigorous or repetitive tactile stimuli") rather than Grade 3.
- *Why it matters:* notes rarely use the Table 6 wording, and this domain alone can set Grade 3 or 4 (§3.5).
- *If wrong:* consciousness-based grades would be assigned inconsistently, shifting the maximum grade by one or more levels.
- *Amended in v0.4 (NEW-3):* a phrase that could fit two categories gives 7.5 only when the two readings lead to different categories for the field (§7.5, A23).

**A16. The initial scope is limited to patients aged ≥18 at infusion.**
- *Why it matters:* this cutoff is ReSauce's choice; the source gives none (§5).
- *If wrong:* a different cutoff would change which synthetic cases are in scope, and might bring in the pediatric pathway.

**A17. A narrative normal neurological note without a formal ICE score does not establish Grade 0.**
- *Detail:* a note such as "alert and oriented x4, neuro exam non-focal" is treated as insufficient evidence for ruling out ICANS on that date.
- *Why it matters:* such notes are common, and they decide whether an earlier record onset can be refuted (§7.1).
- *If wrong:* expert review may decide they count as negative evidence, turning some "insufficient evidence" results into mismatches.

**A18. Abstractors may date onset from the first ICANS-compatible symptom.**
- *Detail:* abstractors may use, for example, new confusion or word-finding difficulty, even without a formal grade. ReSauce's documentation-derived onset requires a Grade ≥1 criterion (§6.2), so the two may differ systematically. Under §7.1 such cases are insufficient evidence.
- *Why it matters:* this could produce many onset flags that reflect a definitional difference, not an error.
- *If wrong:* expert review should confirm this handling. If symptom-based onset is accepted, the onset rule in §6.2 must change.

### Added in v0.3: provisional decisions on GAP-1 to GAP-15

A19–A33 are provisional decisions made by the user so that synthetic test cases can be given definite answers. Each one is a ReSauce choice, not taken from the source, and needs clinician review. The gap numbers refer to `docs/dataset-plan.md` v0.1 §10.

**A19. A record of "no ICANS" is compared as Grade 0 with no onset.** (GAP-1; §7.9(a))
- *Detail:* if the documents contain a qualifying finding, grade is 7.2 (the documented grade is reported) and onset is 7.1, reported as "record has no onset" with no signed difference. Normal rules still apply (e.g. 7.5 for ambiguous attribution).
- *Why it matters:* §7.1 and §7.2 assume a recorded value to compare. Without this rule, a record that misses ICANS entirely would have no category.
- *If wrong:* a separate category (e.g. "ICANS not recorded") may be needed, and these cases would be counted differently.

**A20. An empty onset or grade in a record that reports ICANS is its own category, 7.8 Missing recorded value.** (GAP-2; §7.8)
- *Detail:* the documentation-derived value is reported alongside. The other field is compared normally.
- *Why it matters:* an empty value cannot be compared, but it is a gap in the record that a reviewer should see.
- *If wrong:* empty values might instead be treated as insufficient evidence (7.4) or not reported; the number of discrepancies would change.

**A21. A record of "no ICANS" is confirmed (7.7) only if the observation window has at least one formal Grade 0 assessment, no qualifying finding and no documented "not assessable" period. Otherwise both fields are 7.4.** (GAP-3; §7.9(b))
- *Detail:* the unassessed-period flag is always added. Whether a stricter coverage rule is needed (e.g. a formal Grade 0 assessment every day) is a question for the reviewer.
- *Why it matters:* "no ICANS" records are judged only by this rule. One assessment is a weak standard, because ICANS could occur on days nobody assessed.
- *If wrong:* a stricter rule would move many "no ICANS" records from 7.7 to 7.4. A looser rule (e.g. accepting narrative normal notes, cf. A17) would move some from 7.4 to 7.7.
- *Amended in v0.4 (NEW-2, NEW-5):* ungradeable neurological symptoms (§7 introduction) do not block 7.7. They get the case-level flag "ungradeable neurological symptom", which lists each one with its quote and is added in any in-scope case where one is documented. Excluded symptoms (§4.2) are not part of this flag. The unassessed-period flag is now case-level and is added to every in-scope case. **Question for the clinician:** should ungradeable neurological symptoms block 7.7? *If they should:* such "no ICANS" records would become 7.4.

**A22. A record that reports ICANS with no qualifying finding anywhere gets grade 7.3, and onset 7.1 ("no documented onset") only if a formal Grade 0 assessment exists on the record's onset date; otherwise onset 7.4.** (GAP-4; §7.9(c))
- *Why it matters:* §7.1 assumed a documented onset to compare with.
- *If wrong:* onset might always be 7.4 in this situation, or a separate category may be needed.
- *Amended in v0.4 (NEW-1):* if the window also contains a documented "not assessable" period, A25 wins: grade 7.4, not 7.3. The onset rule is unchanged.

**A23. Ambiguity that is not about attribution also uses category 7.5 (renamed "Ambiguous evidence"), with a required reason.** (GAP-5; §7.5)
- *Detail:* the reasons are attribution, conflicting assessments (§6.4), assessment barrier (A10) and consciousness wording (A15). 7.5 is used only when the ambiguity would change the onset or the grade. The result is reported for each reading.
- *Why it matters:* §4.1, §6.4 and A15 called these situations "ambiguous" but no category existed for them.
- *If wrong:* some reasons may belong under 7.4, or need their own categories; counts of review items would shift between categories.
- *Amended in v0.4 (NEW-3):* 7.5 applies only when the readings lead to different categories for the field. If every reading gives the same category, that category is used. The reported value is the one every reading supports: for a grade, the lowest grade proven under every reading; for onset, the signed difference to the nearest reading, as for a date range. The readings are listed in the ambiguity notes. This makes 7.5 consistent with A33. *If wrong:* these fields would be 7.5 (review flag) instead of a discrepancy category, and A33 would need the same change.

**A24. On the record's onset date, a formal Grade 0 assessment outweighs an excluded or sub-threshold symptom.** (GAP-6; §7.1)
- *Detail:* the result is 7.1 with the flag "record date matches an excluded or sub-threshold symptom". The A18 rule (7.4) applies only when there is no gradeable assessment on that date. ReSauce judges by what the documents show on that date, not by guessing the abstractor's reasoning.
- *Why it matters:* in v0.2 the second and fourth bullets of §7.1 gave different answers for this situation.
- *If wrong:* if symptom-based onset is accepted (A18), these cases would be 7.4 or 7.7 instead of mismatches.
- *Amended in v0.4 (NEW-6):* the flag is added whenever an excluded or sub-threshold symptom is documented on the record's onset date and no qualifying finding exists that day, whatever the onset category (so also with 7.4 under A18).

**A25. A documented "not assessable" period anywhere in the observation window turns an unsupported grade (7.3) into insufficient evidence (7.4). Merely undocumented days do not; they give 7.3 plus the unassessed-period flag.** (GAP-7; §7.3)
- *Why it matters:* under missing ≠ absent, a higher grade could be hidden in any unassessed time. This rule draws the line at documented inability to assess.
- *If wrong:* undocumented days might also give 7.4 (fewer 7.3 results), or only periods close to the record's grade might count.
- *Amended in v0.4 (NEW-1, NEW-5):* the rule also applies when the record reports ICANS and no qualifying finding exists at all (§7.9(c)). The unassessed-period flag is case-level and is added to every in-scope case; its list may be empty.

**A26. Relative time phrases are converted with a fixed table (§6.1). Any other phrase gives no event time. For a range, the signed difference is measured to the nearest end.** (GAP-8; §6.1, §7.1)
- *Why it matters:* §6.1 required a date range but gave no conversion, so the same phrase could be dated differently.
- *If wrong:* onset dates taken from relative phrases would move by about a day, changing some 7.1 and 7.7 results.
- *Amended in v0.4 (NEW-9a):* the documentation-derived onset is the earliest possible date. If the earliest candidate is a date range that starts before every exactly dated qualifying finding, the onset is a range from the range start to the earlier of the range end and the earliest exact date (§6.2).

**A27. Unsigned content is never used for onset or grade.** (GAP-9; §6.3)
- *Detail:* a later unsigned version gets the flag "unsigned later version"; a document with no signed version gets the flag "unsigned document". This can change a category.
- *Why it matters:* unsigned text may be an unfinished draft. §6.3 already treated only signed versions as current, but did not say what to do with unsigned ones.
- *If wrong:* unsigned content might be usable, at least when it is the only documentation, and some 7.4 results would change.

**A28. A record revision counts as a legitimate revision (7.6) only if the value changed, the current value agrees with the documents, and a supporting document version appeared between the previous record version and the change.** (GAP-10; §7.6)
- *Detail:* if the current value agrees but no new documentation appeared in that interval, the field is 7.7 with the flag "revision without new documentation". Only the changed field can be 7.6.
- *Why it matters:* without a timing test, any revision that ends up correct would look "explained".
- *If wrong:* more or fewer revisions would count as 7.6, and a revision without new documentation might deserve a discrepancy category rather than a flag.
- *Amended in v0.4 (NEW-7):* if a field changed value more than once, condition (c) tests the last change, the one that produced the current value. Earlier changes are shown in the record history. *If wrong:* a different change (e.g. the first) would be tested, and some such fields would move between 7.6 and 7.7.

**A29. Out-of-scope cases (age under 18, a CAPD assessment, a record of Grade 5, or a documented death) get the flag "out of scope (reason)" and no §7 category for either field.** (GAP-11; §5, §8)
- *Detail:* they are scored only on whether they were flagged.
- *Why it matters:* §5 and §8 excluded these cases, but did not say whether categories were still computed.
- *If wrong:* categories might still be computed for some (e.g. the onset of a Grade 5 record), and these cases would enter the discrepancy measurements.
- *Amended in v0.4 (NEW-8, NEW-10):* documented baseline developmental delay in an adult is a fifth trigger, as §5 already excluded it. A documented death makes the case out of scope whatever its date, even outside the observation window.

**A30. A competing cause counts if it is documented in the same note as the finding, or documented as given or present within the 24 hours before the finding's event time.** (GAP-12; §3.4, §7.5)
- *Why it matters:* §3.4 said "near" and §7.5 said "coincides", without a time window.
- *If wrong:* a longer window (e.g. for long-acting drugs) would produce more 7.5 results; a shorter one fewer.
- *Amended in v0.4 (NEW-9b):* for a finding whose event time is a date range, a competing cause counts if it falls within the 24 hours before the end of the range. This is the cautious choice: more results become ambiguous, none are hidden.

**A31. Text counts as copied forward if it repeats an earlier note verbatim or differs only in dates, times or formatting. Any change to clinical content makes it a new observation.** (GAP-13; §6.4)
- *Why it matters:* v0.2 covered only unchanged copies, but templated notes often update the date.
- *If wrong:* lightly edited copies might count as new evidence, or copies with small clinical edits might still count as copies. Both affect onset and the recurrence flag.

**A32. Both ReSauce datasets use the observation window Day 0 to Day +28.** (GAP-14; §6.5)
- *Detail:* documents outside the window are not used for categories and get the flag "outside observation window". Record values are compared as they are.
- *Why it matters:* the onset, the maximum grade, the "no ICANS" rule (A21) and the unassessed-period flag all depend on the window. The source gives no ICANS onset window (§2).
- *If wrong:* a longer window would bring later findings into the comparison; a shorter one would leave findings out.
- *Amended in v0.4 (NEW-8):* the window is applied per observation, by its event date (or its documentation date if there is no event time), not per document. Observations dated outside it are not used and are listed in the flag "outside observation window". The decision speaks of findings; v0.4 applies the same rule to assessments and "not assessable" statements (to be confirmed: `docs/dataset-plan.md` §10.2, NEW-11). *If wrong:* judging by documentation date would leave out late entries about in-window events.

**A33. ICE 0 with no consciousness information gives the grade range 3–4.** (GAP-15; §4.1)
- *Detail:* a record of Grade 2 or lower is 7.2 (the documents prove at least Grade 3). A record of Grade 3 or 4 is 7.4.
- *Why it matters:* ICE 0–2 meets the Grade 3 ICE criterion (Table 6) whatever the consciousness level, but Grade 4 cannot be ruled out.
- *If wrong:* if ICE 0 without consciousness information should not count at all, these cases would all be 7.4.

### Added in v0.4: provisional decision on NEW-4

**A34. A day has a gradeable assessment if a note documents an ICE total for that day (stated, or all items scored) or a qualifying finding (§6.2).** (NEW-4; §7 introduction)
- *Detail:* a neurological observation that meets no criterion and has no ICE total (e.g. "alert, confused") is not a gradeable assessment. A formal Grade 0 assessment is one kind of gradeable assessment. A partial ICE without a stated total is not one (A6), unless the same day has a qualifying finding.
- *Why it matters:* this term decides §7.1 (whether a record's onset date can be refuted, or is insufficient evidence), the A24 flag and the day list of the unassessed-period flag.
- *If wrong:* a broader definition (e.g. any neurological observation) would list fewer unassessed days and move some onset results away from 7.4; a narrower one (e.g. ICE totals only) would do the opposite.

### Added in v0.4.1: competing causes

**A35 [ASSUMPTION — EXPERT REVIEW] Competing causes (§3.4, §7.5) are a closed list, each documented as given or present, not merely suspected: sedating medication (benzodiazepines, opioids, propofol, dexmedetomidine, sedating antihistamines), hepatic failure, severe hypertension, eclampsia, a documented infection, an electrolyte abnormality, hypoglycaemia. These are never competing causes: CRS itself (including fever), and treatment for CRS or ICANS (tocilizumab, acetaminophen, corticosteroids such as dexamethasone, levetiracetam given as seizure prophylaxis).** Reason: the source lists immunosuppressive drugs among other causes, but these drugs are the standard treatment of the syndromes being graded; counting them would make almost every case ambiguous.
</clinical_methods>
