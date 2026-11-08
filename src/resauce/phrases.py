"""Closed phrase lists used by the extraction stage (resauce.extract).

Every list cites the rule in docs/clinical-methods.md (v0.4.1) it serves.
The lists are deliberately closed: a phrase that is not listed here is not
recognised, and extract.py reports leftover neurological wording as an
"unrecognised" observation instead of guessing.

How the lists were built: from clinical-methods.md and the 20 development
cases only (docs/evaluation-spec.md §1). They are provisional. The
consciousness list in particular is [ASSUMPTION — EXPERT REVIEW] (A15): it
must be approved by a clinician. Misspelt words are not matched.

Patterns are regular expressions, matched case-insensitively. Parts that
must match capitals only (ICE, HA) are wrapped in (?-i:...).
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Sentence structure: negation, hedging, plan lines (no clinical meaning)
# ---------------------------------------------------------------------------

# Words that negate a finding that follows them in the same clause.
NEGATION_BEFORE = (
    r"\bno\b|\b(?:did |does )?not\b|\bwithout\b|\bw/o\b|\bdenies\b|\bdenied\b|"
    r"\bnegative for\b|\bnone of\b|\bnor\b|\bnever\b"
)
# Phrases that contain a negation word but do not negate a finding.
PSEUDO_NEGATION = r"\bno (?:longer|change|new orders)\b|\bnot (?:only|excluded|done|performed)\b"
# Verbal negations that stop at a comma ("Not following commands, confused"
# leaves "confused" positive). List negations such as "no X, Y, Z" cross commas.
NEGATION_STOPS_AT_COMMA = r"^(?:not|did not|does not)$"
# A negation reaches at most this many words forward.
NEGATION_MAX_WORDS = 6
# Words that end the reach of a negation or hedge (NegEx-style terminators).
# A colon also ends it: "ICE not done: intubated and sedated" does not negate
# "sedated".
SCOPE_TERMINATORS = (
    r"\bbut\b|\bbecause\b|\balthough\b|\bthough\b|\bhowever\b|\bexcept\b|"
    r"\bwhich\b|\bwhereas\b|:"
)
# "Seizure activity ....... none", "Sedating meds past 24 h: none".
NEGATION_AFTER_VALUE = r"^[^:]*?(?::|\.{2,})\s*(?:none|no|nil|negative|absent)\b"

# Words that make a finding uncertain (planned, suspected, to be ruled out).
HEDGE_BEFORE = (
    r"\br/o\b|\brule out\b|\blook for\b|\bevaluate for\b|\beval for\b|"
    r"\bconcern for\b|\bconcerning for\b|\bsuspect(?:ed)?\b|\bpossible\b|"
    r"\bpossibly\b|\bprobable\b|\bquery\b|\bif\b|\bunless\b|\brisk of\b"
)
HEDGE_AFTER = r"^\W*\w*\W*(?:not excluded|cannot be excluded|not ruled out)\b"
# Lines whose content is a plan or recommendation, not an observation.
PLAN_LINE = r"^\s*(?:plan|p|rec|recs|recommendations?)\s*:"
# Lines that hold a clinician's assessment.
ASSESSMENT_LINE = r"^\s*(?:assessment|a|imp|impression)\s*:"
# A finding word followed by one of these is not a finding ("seizure
# prophylaxis", "seizure precautions").
NOT_A_FINDING_AFTER = r"^\s*(?:prophylaxis|ppx|precautions)\b"

# ---------------------------------------------------------------------------
# Time (§6.1, A26)
# ---------------------------------------------------------------------------

# Study-day notation, converted with the infusion date (format §8).
STUDY_DAY = (
    r"\b(?:D|Day|day|DAY)\s?(?:post infusion:\s*|:\s*)?([+\-−])\s?(\d{1,3})\b"
    r"|\b(?:D|Day|day)\s?(0)\b"
    r"|\bpost-infusion day:\s*(\d{1,3})\b"
)
# A26 conversion table. D = the note's documentation date.
# Each entry: (pattern, days before D for the range start, days before D for the end).
RELATIVE_TABLE = (
    (r"\bovernight\b|\blast night\b", 1, 0),
    (r"\b(?:since )?yesterday(?:'s)?\b", 1, 1),
    (r"\bthis morning\b|\bearlier today\b", 0, 0),
)
# "N days ago" (A26): handled separately because N varies.
DAYS_AGO = r"\b(\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten) days? ago\b"
# Relative phrases outside the A26 table: no event time (A26 "any other
# phrase"), so the documentation date is used and the time is imprecise.
RELATIVE_OTHER = (
    r"\b(?:the )?next (?:morning|day|evening|night)\b|\bthe following (?:day|morning)\b|"
    r"\brecently\b|\ba few days\b|\bfor (?:a )?few days\b|\btoday\b|\btonight\b|"
    r"\bthis (?:evening|afternoon|shift)\b|\bearlier\b|\bsince waking\b"
)
# Lines near the top of a note that give the note's own date.
HEADER_LABEL = (
    r"^\s*(?:date(?: of service| of exam)?|service date|date/time|time|visit date|"
    r"exam(?: date/time)?|performed|recording|study|assessment date/time)\b"
)
HEADER_MAX_LINES = 4

NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}

# ---------------------------------------------------------------------------
# ICE score (§3.2, Table 5; A6, A34)
# ---------------------------------------------------------------------------

ICE_WORD = r"(?-i:\bICE\b)"
# Words that, before an "N/10", show it is an ICE total.
ICE_ANCHOR = r"(?-i:\bICE\b)|\btotal\b|="
# Words that, before an "N/10", show it is a pain score instead.
PAIN_WORD = r"\bhead\w*|\bpain\b|\bache\b|(?-i:\bHA\b)"
# "N/10" just before these words is an ICE total ("scored 10/10 on the ICE").
ICE_AFTER = r"^\s*on the ICE\b"
# Dotted form: "ICE SCORE ............ 8".
ICE_DOTTED = r"(?-i:\bICE)(?:\s+(?:score|total))?\s*\.{2,}\s*(\d{1,2})\b"
# Bare form: "ICE 8" or "ICE score 0" with no "/10".
ICE_BARE = r"(?-i:\bICE)(?:\s+(?:score|total))?\s+(\d{1,2})\b(?!\s*(?:/|:|-|\d|times\b|x\b|h\b|hours\b|mg\b))"
# Words just before a total that make it a condition, not a result.
ICE_CONDITION = r"\b(?:if|when|once|until|unless|below|above|goal|target)\s+(?:the\s+)?(?:ICE\s+)?(?:score\s+)?(?:is\s+)?$"
# ICE mentions that are not scores (orders, headers, references).
ICE_NOT_A_SCORE = (
    r"(?-i:\bICE)\s*(?:q\s?\d+\s?h?|every|twice|screening|monitoring|checks?|"
    r"screen|assess\w*|flowsheet|record|form)\b"
    r"|\b(?:repeat|recheck|completed|RN|nursing|perform(?:ed)?)\s+(?:the\s+)?ICE\b"
    r"|(?-i:\bICE\b)[^.;|]{0,25}\breviewed\b|(?-i:\bICE)(?: score)? alone\b"
    r"|(?-i:\bICE)\s+(?:[A-Za-z]+\s+){0,2}\d{4}-\d{2}-\d{2}"
)
# ICE items: (name, label pattern, maximum points), Table 5.
ICE_ITEMS = (
    ("orientation", r"\b(?:orientation|orient)\b", 4),
    ("naming", r"\b(?:naming|name objects|objects)\b", 3),
    ("commands", r"\b(?:commands?|cmds?|follow command)\b", 1),
    ("writing", r"\b(?:writing|write sentence|sentence)\b", 1),
    ("attention", r"\b(?:attention|attn|count[- ]back|counting)\b", 1),
)
# Single-letter labels ("O 2/4 - N 3/3 - C 1/1 - W 0/1 - A 1/1"), case-sensitive.
ICE_ITEM_LETTERS = {"O": "orientation", "N": "naming", "C": "commands", "W": "writing", "A": "attention"}

# ---------------------------------------------------------------------------
# Level of consciousness (Table 6; A3, A15) [ASSUMPTION — EXPERT REVIEW]
# ---------------------------------------------------------------------------

# The four Table 6 categories, in the source's wording.
SPONTANEOUS = "awakens spontaneously"
VOICE = "awakens to voice"
TACTILE = "awakens only to tactile stimulus"
UNAROUSABLE = "unarousable"
AWAKE = "awake (no depressed consciousness)"

_AROUSAL_VERB = (
    r"\b(?:awakens?|wakes?|wakens?|rouses?|arouses?|arousal|arousable|rousable|"
    r"opens? (?:his |her |their )?eyes|opened (?:his |her |their )?eyes|eye opening|"
    r"respon(?:ds?|ded|se))\b"
)
# (pattern, category). Checked in this order; a later pattern is skipped
# where an earlier one already matched the same words.
CONSCIOUSNESS = (
    (r"\bun(?:a)?rousable\b|\bnot (?:a)?rousable\b|\bstupor(?:ous)?\b|\bcoma(?:tose)?\b(?! scale)"
     r"|\bvigorous\b[^.;|]{0,30}stimul\w*|\brepetitive tactile\b", UNAROUSABLE),
    (_AROUSAL_VERB + r"[^.;|]{0,40}?\b(?:touch\w*|tactile|tap\w*|shak\w*|physical stimul\w*)", TACTILE),
    (_AROUSAL_VERB + r"[^.;|]{0,30}?\b(?:voice|verbal\w*|spoken to|name (?:is |was )?called|name called|by name)\b", VOICE),
    (r"\b(?:awakens?|wakes?|rouses?|arouses?)\s+spontaneously\b", SPONTANEOUS),
)
# Phrases that could fit two categories (A15): reported with candidates, never graded.
CONSCIOUSNESS_AMBIGUOUS = (
    (r"\bsternal rub\b|\bresponds? (?:only )?to pain\w*|\bpainful stimul\w*", (TACTILE, UNAROUSABLE)),
)
# Phrases with no approved mapping at all (A15 names them as needing one).
CONSCIOUSNESS_UNMAPPED = r"\bdrowsy\b|\bsleepy\b|\blethargic\b|\bsomnolent\b|\bobtunded\b"
# Wakefulness: no depressed consciousness. Not a Table 6 category; kept for
# A3 (drowsiness context) and §3.4 / A33 (ICE 0 in an awake patient).
CONSCIOUSNESS_AWAKE = (
    r"(?<!once )(?<!stays )(?<!remained )\bawake\b|\balert\b|\bA&O\s?x\s?[1-4]\b|\bA&Ox[1-4]\b|"
    r"\bconversant\b|\bconversing\b|\bchatting\b|\btalking\b|\battentive\b|\beyes open\b"
)

# ---------------------------------------------------------------------------
# Seizures (Table 6; §3.3 note on EEG changes)
# ---------------------------------------------------------------------------

SEIZURE = (
    r"\b(?:(?:non-?convulsive|convulsive|electrographic|clinical|generalized|focal|"
    r"tonic-clonic)\s+)*(?:seizures?|sz|convulsions?)\b|\bstatus epilepticus\b"
)
SEIZURE_EEG_CONTEXT = r"\belectrographic\b|\bnon-?convulsive\b|\bon EEG\b|\bEEG\b"
SEIZURE_DURATION = (
    r"(about|approximately|approx\.?|~|under|less than|<|over|more than|>)?\s*"
    r"(\d+|one|two|three|four|five|six|seven|eight|nine|ten)"
    r"(?:\s*(?:-|to)\s*(\d+))?\s*(seconds?|secs?|s|minutes?|mins?|min)\b"
)
SEIZURE_SELF_TERMINATED = (
    r"\bstopped on its own\b|\bstopp(?:ed|ing) by itself\b|\bself-limit\w*|"
    r"\bself-terminat\w*|\b(?:resolved|ended|stopped) spontaneously\b"
)
SEIZURE_WITH_INTERVENTION = (
    r"\b(?:resolved|stopped|ended|terminated|aborted|controlled)\s+(?:after|with|following)\s+"
    r"[^.;]{0,30}?\b(?:levetiracetam|LEV|lorazepam|midazolam|diazepam|benzodiazepines?|"
    r"treatment|intervention|anti-?seizure\w*|phenytoin|fosphenytoin|valproate|lacosamide)\b"
)
SEIZURE_BASELINE_NO = r"\b(?:without|w/o|no) return to (?:its |their |the )?baseline\b"
SEIZURE_BASELINE_YES = r"\breturn(?:ed|s)? to (?:its |their |the )?baseline\b|\bback to baseline\b"
SEIZURE_REPETITIVE = (
    r"\b(?:repetitive|recurrent|repeated|multiple|\d+|two|three|four|five)\s+"
    r"(?:(?:separate|discrete|electrographic|clinical|non-?convulsive|generalized|focal)\s+){0,3}"
    r"(?:seizures|sz)\b"
)

# EEG changes that are not seizures (§3.3 notes).
EEG_FINDINGS = (
    (r"\bslowing\b", "slowing"),
    (r"\bFIRDA\b|\bfrontal intermittent rhythmic delta activity\b", "FIRDA"),
    (r"\bepileptiform discharges?\b", "epileptiform discharges"),
)

# ---------------------------------------------------------------------------
# Motor findings (Table 6) and raised ICP / edema (Table 6; A12)
# ---------------------------------------------------------------------------

MOTOR = (
    r"\bhemiparesis\b|\bhemiplegia\b|\bparaparesis\b|\bparaplegia\b|\bmonoparesis\b|"
    r"\bquadriparesis\b|\btetraparesis\b|\bfocal (?:motor )?(?:weakness|deficits?|wkns)\b|"
    r"\bweakness\b|\bwkns\b|\bdrift\b|\bfacial droop\b"
)
# Edema counts only with a brain qualifier, or inside an imaging report.
EDEMA = (
    r"\b(?:(diffuse|focal|local|localized|localised|global|generalized|vasogenic|"
    r"cytotoxic|surrounding|perilesional)\s+)?(?:(cerebral|brain|parenchymal)\s+)?"
    r"(edema|oedema|swelling)\b"
)
EDEMA_DIFFUSE = ("diffuse", "global", "generalized")
EDEMA_FOCAL = ("focal", "local", "localized", "localised")
ICP_SIGNS = (
    (r"\bpapill?o?edema\b|\bpapilloedema\b", "papilledema"),
    (r"\b(?:cranial nerve VI|CN ?VI|sixth (?:cranial )?nerve|abducens)\s+(?:nerve\s+)?pals(?:y|ies)\b",
     "cranial nerve VI palsy"),
    (r"\b(?:decerebrate |decorticate |extensor |flexor )?posturing\b", "posturing"),
    (r"\bcushing'?s? triad\b", "Cushing's triad"),
)
# A12: raised-ICP signs in the source text but not in Table 6. Only the
# example named in clinical-methods §3.3 is listed.
TEXT_ONLY_ICP = ((r"\bprojectile vomit\w*", "projectile vomiting"),)

# ---------------------------------------------------------------------------
# Symptoms excluded from grading (§4.2, A11) and ungradeable symptoms (A21)
# ---------------------------------------------------------------------------

EXCLUDED = (
    (r"\bheadaches?\b|\bhead ache\b", "headache"),
    (r"(?-i:\bHA\b)", "headache"),
    (r"\btremors?\b|\btremulous\b", "tremor"),
    (r"\bmyoclon(?:us|ic)\b", "myoclonus"),
    (r"\basterixis\b", "asterixis"),
    (r"\bhallucinat\w*", "hallucinations"),
)
# Intracranial hemorrhage counts only with a qualifier or in an imaging report.
HEMORRHAGE = (
    r"\b(?:(intracranial|subdural|epidural|subarachnoid|intraparenchymal|cerebral)\s+)?"
    r"(hemorrhage|haemorrhage|hematoma|haematoma|bleed)\b"
)
DECONDITIONING = r"\bdeconditioning\b|\bimmobility\b"
DECONDITIONING_SIGN = r"\bweakness\b|\bunsteadiness\b|\bunsteady\b|\bbalance\b"

UNGRADEABLE = (
    (r"\bconfus(?:ed|ion)\b", "confusion"),
    (r"\bword[- ]finding (?:difficulty|difficulties|problems?)\b", "word-finding difficulty"),
    (r"\bdisorient(?:ed|ation)\b", "disorientation"),
    (r"\baphasi(?:a|c)\b", "aphasia"),
    (r"\bdysarthri(?:a|c)\b|\bslurred speech\b", "dysarthria"),
    (r"\bagitat(?:ed|ion)\b", "agitation"),
    (r"\binattent(?:ive|ion)\b", "inattention"),
    (r"\bencephalopath(?:y|ic)\b", "encephalopathy"),
    (r"\bunsteady\b|\bunsteadiness\b", "unsteadiness"),
)

# ---------------------------------------------------------------------------
# "Not assessable" statements (§4.1, A7)
# ---------------------------------------------------------------------------

NOT_ASSESSABLE = (
    r"\bunable to (?:be )?assess(?:ed)?\b|\bnot assessable\b|\bunassessable\b|"
    r"\bnot able to assess\b|\bcould not be assessed\b|\bcannot be assessed\b|"
    r"\b(?:ICE|neuro(?:logical)? (?:exam|assessment|check))\s+(?:was\s+)?(?:not done|deferred|not performed|not possible)\b|"
    r"\bunable to perform (?:the )?(?:ICE|assessment|neuro\w*)"
)

# ---------------------------------------------------------------------------
# Competing causes (§3.4, A35): closed list. CRS, fever, tocilizumab,
# acetaminophen, corticosteroids and levetiracetam are never competing causes,
# so they are not listed.
# ---------------------------------------------------------------------------

COMPETING_CAUSES = (
    (r"\b(?:lorazepam|midazolam|diazepam|clonazepam|alprazolam|temazepam|benzodiazepines?|"
     r"morphine|hydromorphone|oxycodone|fentanyl|opioids?|opiates?|propofol|dexmedetomidine|"
     r"diphenhydramine|hydroxyzine|promethazine|antihistamines?|sedatives?|"
     r"sedating (?:medications?|medicines?|meds|drugs?|agents?)|sedation|sedated)\b",
     "sedating medication"),
    (r"\b(?:hepatic|liver) failure\b", "hepatic failure"),
    (r"\bsevere hypertension\b|\bhypertensive (?:emergency|crisis)\b", "severe hypertension"),
    (r"(?<!pre-)\beclampsia\b", "eclampsia"),
    (r"\binfections?\b|\bsepsis\b|\bseptic\b|\bbacter[a]?emia\b|\bpneumonia\b|\bmeningitis\b|"
     r"\bencephalitis\b|\bUTI\b|\bcellulitis\b|\bpositive blood cultures?\b", "documented infection"),
    (r"\bhypo(?:natr|kal|calc|magnes|phosphat)[a]?emia\b|\bhyper(?:natr|kal|calc|magnes)[a]?emia\b|"
     r"\belectrolyte (?:abnormalit(?:y|ies)|derangements?|disturbances?|imbalance)\b",
     "electrolyte abnormality"),
    (r"\bhypoglyc[a]?emi(?:a|c)\b|\blow blood (?:sugar|glucose)\b", "hypoglycaemia"),
)

# ---------------------------------------------------------------------------
# Clinician attribution statements (§3.4, A9)
# ---------------------------------------------------------------------------

ATTRIBUTION_CUE = (
    r"\bdue to\b|\bsecondary to\b|\battributed to\b|\battributable to\b|\bconsistent with\b|"
    r"\bc/w\b|\bcaused by\b|\brelated to\b|\bunrelated\b|\bnot related\b|\blikely from\b|"
    r"\bin the setting of\b"
)
ICANS_NAME = r"\bICANS\b|\bneurotoxicity\b"

# ---------------------------------------------------------------------------
# Assessment barriers (§4.1, A10) and out-of-scope triggers (§5, A29)
# ---------------------------------------------------------------------------

ASSESSMENT_BARRIERS = (
    (r"\blanguage barrier\b|\binterpreter\w*|\bnon-?English[- ]speaking\b|\blimited English\b|"
     r"\bdoes not speak English\b", "language barrier"),
    (r"\bhearing (?:loss|impairment|impaired)\b|\bhard of hearing\b|\bdeaf(?:ness)?\b|\bhearing aids?\b",
     "hearing loss"),
    (r"\bvision (?:loss|impairment)\b|\bvisual(?:ly)? impair\w*|\bblind(?:ness)?\b", "vision loss"),
    (r"\b(?:unable to|cannot) write (?:due to|because)\b", "writing barrier"),
    (r"\bbaseline cognitive impairment\b|\bdementia\b|\bintellectual disability\b",
     "baseline cognitive impairment"),
)
OUT_OF_SCOPE_MENTIONS = (
    (r"\bCAPD\b|\bCornell Assessment of Pediatric Delirium\b", "CAPD assessment"),
    (r"\bdied\b|\bdeath\b|\bdeceased\b|\bpassed away\b|\bpronounced dead\b", "documented death"),
    (r"\bdevelopmental(?:ly)? delay(?:ed)?\b", "developmental delay"),
)

# ---------------------------------------------------------------------------
# Words that should have produced an observation. A clause that still
# contains one after every rule has run is reported as "unrecognised".
# ---------------------------------------------------------------------------

# Form labels that name a field but are not findings ("Level of arousal: alert").
FIELD_LABELS = r"\b(?:level of )?arousal\s*(?::|\.{2,})"

NEURO_TRIGGER = (
    r"(?-i:\bICE\b)|seiz|\bsz\b|convuls|epilept|slowing|FIRDA|edema|oedema|papill|posturing|"
    r"arous|awaken|unresponsive|paresis|plegia|weakness|\bwkns\b|unable to assess|"
    r"aphasi|letharg|drows|somnol|obtund|stupor"
)
