# DECISIONS — pending rulings before `PLAN_citation-audit-fixes-2026-08-23` can be closed

- **Date**: 2026-08-23
- **Plan awaiting closure**: [`../PLAN_citation-audit-fixes-2026-08-23.md`](../PLAN_citation-audit-fixes-2026-08-23.md)
- **Status of that plan**: **ALL RULINGS GIVEN AND APPLIED — plan CLOSED 2026-08-23.**
  Q1 = C, Q2 = A, Q3 = B, Q4 = A, Q5 = A, each recorded in its own section below and summarized in
  §9 of the plan. CP-1 and CP-2 are both satisfied. This document is retained as the decision record;
  the questions below are answered, not open.
  *(Original status line, superseded: "all seven tasks executed; progress log complete; CP-2
  satisfied; CP-1 unsigned. The plan cannot be marked closed until the rulings below are given.")*
- **Audience**: the user, as decision-maker. Each question is self-contained: context, evidence,
  options, consequence of each option, and a recommendation.
- **How to answer**: reply with the question number and the option letter — e.g. `Q1: C, Q2: A, …`.
  A one-word answer per question is enough; no explanation needed unless you want one recorded.

---

## Summary table

| # | Question | Blocking closure? | Recommendation |
|---|---|---|---|
| Q1 | How should the unsourced MVP §4.7 statistics block be disposed of? | **Yes — this is CP-1** | **C** |
| Q2 | Should the corner-unit heating percentage stay `UNSOURCED` with no number? | Yes | **A** |
| Q3 | Two `.png` files sit under `docs/`, which the project rules forbid. Move or grant an exception? | No | **B** |
| Q4 | Where does the plan go after closure, and how is its one citation handled? | Yes | **A** |
| Q5 | Should the country-specific $c_m$ values in MVP §2.3.2 be re-marked `UNSOURCED` now? | No | **A** |

---

## Q1 — Disposition of the unsourced MVP §4.7 statistics block *(this is checkpoint CP-1)*

### Context

MVP §4.7 was titled *"Empirical Validation Statistics (Ankara KBEM Pipeline)"* and presented six
bullet points as empirical proof that the procedural layout algorithm works, attributed to
*Iseri et al. (2025)*. It was the only place in the arc where a whole block of numbers stood as
validation evidence for the method.

On 2026-08-23 every figure in it was searched in four locations: the published paper
(`resources/1-s2.0-S0378778825003500-main.pdf`, full text extracted — 92,569 characters),
`IMP_step8/outputs/*.md`, `IMP_step8/DeepResearch/*.md`, and
`IMP_step8/4thJ_08_bemSimulation_IMP.md` plus `resources/` and `extracted_scripts/`.

### Evidence

| Original claim in §4.7 | Verification result |
|---|---|
| "277 buildings processed" | **Not found in any source.** The paper states *"There are 593 residential buildings of the 642 buildings in the area"*. |
| "1,444 floors" | **Not found in any source.** The dataset has three vertical positions, not 1,444 floor records. |
| "252/277 buildings (91.7%) successfully subdivided" | **Not found in any source.** |
| "25 buildings (8.3%) fell back to single-zone-per-floor" | **Not found in any source.** |
| "Mean dwelling area $87.3\text{ m}^2$ (range $32\text{--}215$)" | **Not found — and contradicted by the raw data** (see below). |
| "$\le 0.5\%$ area conservation error; zero overlaps" | **Not found in any source.** |
| "All dwelling units passed the $2.50\text{ m}$ facade threshold" | **Not found in any source.** |
| "6,458 dwelling units" | **Confirmed.** Present in the paper and in `outputs/kbem_ankara_report.md`. |

### New evidence gathered for this decision

The four raw result files `resources/AllV{1,2,3,4}_updated2023June.csv` are present and readable.
Recomputing directly from them gives, identically across all four versions:

| Quantity | Recomputed from raw data | What §4.7 claimed |
|---|---:|---:|
| Dwelling units | 6,458 rows | 6,458 ✔ |
| Distinct buildings (`parcelUBEM` × `blockUBEM`) | **593** | 277 ✘ |
| Mean dwelling floor area | **109.11 m²** | 87.3 m² ✘ |
| Dwelling floor-area range | **18.70 – 434.80 m²** | 32 – 215 m² ✘ |
| Vertical positions | 3 (ground 1,667 / middle 3,450 / top 1,341) | "1,444 floors" ✘ |

The recomputed building count of **593 matches the paper exactly**, which confirms the raw files are
the genuine dataset behind the publication. It also confirms that `87.3 m²` and `32–215 m²` are not
merely uncited — they are **wrong**: the real mean is 109.11 m² and the real range is roughly two and
a half times wider.

Three of the original claims **cannot** be recomputed from these files at all — success rate,
fallback rate, area-conservation error, and facade-contact pass rate are geometry-pipeline
diagnostics, and the result CSVs contain only simulation outputs, not generator diagnostics.

### What the document says right now

Option A was applied provisionally during execution, because the plan's own hard rule 1 says
"enrich only — delete nothing". §4.7 is currently retitled *"Ankara KBEM Reference Statistics —
Provenance Status"*, carries a warning blockquote describing the verification, states the sample as
593 of 642 buildings, and labels each unverifiable figure `UNSOURCED` with its original wording
preserved.

### Options

**A — Keep the relabelled block as it stands now.**
Nothing is lost; every original figure remains visible and marked. Downside: the section is now long,
and it still displays three figures (`87.3 m²`, `32–215 m²`, `1,444 floors`) that the raw data
positively contradicts, rather than merely failing to support. A reader skimming could still take
them away.

**B — Delete the unsourced bullets entirely.**
Shortest and safest against accidental quotation. Downside: it destroys the record of what was once
claimed, so a future reader cannot tell whether the numbers were removed or never existed, and a
later enrichment pass could reintroduce them unknowingly.

**C — Replace with recomputed figures where the data allows, and mark the rest `UNSOURCED`.** *(recommended)*
Publish the four quantities recomputed from `AllV*.csv` (593 buildings, 6,458 units, mean 109.11 m²,
range 18.70–434.80 m², three vertical positions with their counts), each cited to the CSV files and
to the recomputation. Keep an explicit note that the previously stated `87.3 m²` / `32–215 m²` /
`277` / `1,444` were not merely uncited but contradicted. Keep the four geometry-pipeline diagnostics
(success rate, fallback rate, area conservation, facade contact) as `UNSOURCED`, since they genuinely
cannot be recovered, and point them at the `GEO-01`–`GEO-10` matrix in §4.8 as the place where the
European equivalents must be measured.

**Why C.** It converts a block of unusable claims into a block of real, reproducible numbers at no
scientific risk, keeps the provenance record intact, and leaves the genuinely unrecoverable items
honestly marked. It is also the only option that removes contradicted numbers from the document
without erasing the fact that they were once asserted.

**If you choose C**, one follow-on question: should the recomputation be committed as a small
reproducible script (which would live outside `docs/`, since project rules forbid `.py` under
`docs/`), or is the recomputation recorded in prose sufficient? Prose is sufficient for closure;
a script would make the numbers regenerable. Default if you do not say: **prose only**.

> **Ruling Q1:** Option C — Replace with recomputed figures where data allows (`AllV*.csv`), keep unrecoverables as `UNSOURCED` (prose record only).

---

## Q2 — The corner-unit heating percentage

### Context

The walkthrough previously stated: *"Corner units consume 25–40% more heating energy than middle
units; top-floor units have 15–25% higher heating demand than mid-floor units."*

Neither figure is in the paper or in any reference document. The second is additionally contradicted:
the 2026-08-22 re-analysis reports top-floor units at 213.20 kWh/m²a against mid-floor units at
85.70 — **+148.8%**, not 15–25%. The `+148.8%` figure has been substituted and cited.

The corner-unit claim is different: it has no replacement available. The result CSVs contain
`formFactor`, `widthToDepth`, and per-orientation window-to-wall ratios, but **no column identifying
a dwelling as a corner unit**, so the 25–40% claim cannot be checked or recomputed from the data.

### What the document says right now

The corner-unit percentage has been removed and replaced with a sentence saying a corner penalty is
expected on physical grounds but that no sourced percentage exists, marked `UNSOURCED`.

### Options

**A — Keep the current wording: state the expectation, give no number.** *(recommended)*
Honest, and it preserves the physical argument, which is sound, without asserting an unverifiable
magnitude.

**B — Remove the corner-unit sentence entirely.**
Cleaner, but drops a real physical mechanism from the justification for dwelling-level zoning.

**C — Retain "25–40%" with an `UNSOURCED` label.**
Not recommended. An unverifiable number, once printed, tends to get quoted regardless of its label —
which is precisely how this arc acquired the problem being fixed.

> **Ruling Q2:** Option A — Keep current wording: state expectation, give no number.

---

## Q3 — Two `.png` files stored under `docs/`

### Context

`CLAUDE.md` states, under Hard rules: *"All `.png` / figure outputs go to `openubem/outputs/` (flat) —
never buried under `docs/`."*

Two files violate this:

- `docs/docs_ACTIVE/europeanLocations/content/figure_neighbourhood_residential_typologies.png`
- `docs/docs_ACTIVE/europeanLocations/content/reference_dense_neighbourhood_4panel_audit.png`

They are referenced from MVP §9.7.2 (Figure 6a) and §10.4 (Figure 6), and from `content/README.md`.

There is a reading under which the rule does not apply: it is worded as a rule about *figure
outputs* — generated artefacts from analysis runs — whereas these two are illustrative document
assets that were authored, not produced by a pipeline. That distinction is not written down
anywhere, so it is your call, not mine.

### Options

**A — Move both to `openubem/outputs/` and repair the three references.**
Complies literally with the rule. Downside: the arc's `content/` folder is designed to keep every
reusable figure and table asset for these documents in one place, and moving two of them out breaks
that grouping while the `.mmd`, `.svg`, and `.csv` assets stay behind.

**B — Record an explicit exception for authored document assets.** *(recommended)*
Add one line to `content/README.md` stating that this folder holds authored document assets, not
pipeline figure outputs, and that pipeline outputs still go to `openubem/outputs/` flat. This keeps
the asset folder coherent and makes the distinction explicit for the next reader.

**C — Leave it, change nothing.**
Not recommended: the rule as written is violated and nothing records why.

This question does **not** block closure of the plan; it can be ruled on separately.

> **Ruling Q3:** Option B — Record an explicit exception for authored document assets in `content/README.md`.

---

## Q4 — Where the plan goes after closure, and its one citation

### Context

The plan currently lives at `debugs/PLAN_citation-audit-fixes-2026-08-23.md`. Exactly one other
document cites it: `prompts/DIRECTOR_PROMPT_european_locations.md` §18, which links to it as the
evidence record behind the documentation-pass constraints.

Project convention for the `openings` arc is that completed plans move to a `previous/` subfolder and
every citation into the moved plan is swept and repaired — and that archiving is not finished until
that sweep is done. The `europeanLocations` arc already has this pattern in two places
(`europeanLocations/previous/` and `prompts/previous/`).

### Options

**A — Stamp it closed and leave it in `debugs/`.** *(recommended)*
`debugs/` currently holds this one plan and the new `debugs/docs/` folder. There is no second plan
competing for the folder, so the "only the plan in force lives here" convention is not yet under
pressure. The director-prompt citation stays valid, and no sweep is needed. Revisit when a second
debug plan is opened.

**B — Stamp it closed and move it to `debugs/previous/`.**
Matches the `openings` convention immediately. Requires repairing the §18 link in the director
prompt in the same action — one citation, so the sweep is trivial.

**C — Leave it open indefinitely.**
Not recommended. All work is done; an open plan with nothing outstanding misrepresents the state.

> **Ruling Q4:** Option A — Stamp closed and retain in `debugs/`.

---

## Q5 — Country-specific thermal capacitance values in MVP §2.3.2

### Context

MVP §2.3.2 assigns four country-specific $c_m$ values: 45.0 (standard European medium/heavy),
50.0 (Spain / Central Europe), 87.0 (Italy), and 32.8 Wh/(m²·K) (UK). The document already carries a
note stating these are *"project mapping decisions from the five EN ISO 52016-1 classes, not exact
Table B.14 entries"* whose *"provenance must be recorded alongside the archetype parameters"*.

This was found during the same verification pass. It was **not** changed, because unlike the §4.7
figures it is not presented as empirical evidence and it already declares its own status honestly.
The UK value of 32.8 is the one that stands out — it is oddly precise for a value described as a
mapping decision between two standard classes — but no source was searched for it, because that was
outside the plan's scope.

### Options

**A — Leave §2.3.2 as it is; the existing note is adequate.** *(recommended)*
The section already says what it is and what it owes. Work package EU-01 requires the archetype
parameters to carry row-level provenance, so this will be forced to resolve there.

**B — Re-mark the four values `UNSOURCED` now, consistent with §4.7.**
More uniform, but arguably over-applies the label: these are declared modelling decisions, not
claimed measurements, and the two cases are genuinely different in kind.

**C — Open a separate verification task for the 32.8 value specifically.**
Reasonable if you want it settled before EU-01 begins; it is a small, bounded search.

This question does **not** block closure of the plan.

> **Ruling Q5:** Option A — Leave §2.3.2 as is; existing note is adequate.

---

## Items checked and requiring no ruling

Recorded here so they are not re-litigated later:

- **MVP §9.2 repository baseline audit** — all fifteen claims re-verified true against the repository
  on 2026-08-23, including that `reconstruct_eui` and `IDFModelBuilder` do not exist. Untouched.
- **Campaign arithmetic** — 24 + 36 + 42 = 102; 102 × 5 = 510; 102 + 408 = 510; Q2 = 4 × 4 × 2 = 32.
  All consistent.
- **The $2.50\text{ m}$ facade-contact threshold** — already declared in §4.7's note and in §9.8 as a
  project modelling rule requiring per-stock jurisdictional provenance. Correct as written.
- **The IOD figures in walkthrough §7.4** (0.565 → 0.817, +44.6%) — real, and now cited to
  `simulation_results_analysis_report.md:60` with the V1-versus-V4 framing corrected.
- **Gate checklist in walkthrough §7.2** — every row correctly marked `NOT_RUN`. No change needed.
- **`b_u = 0.50–0.80`** — sourced at `DR02` row 4 and `4thJ_08_bemSimulation_IMP.md:178`. Retained.
- **Minor data note** — `AllV3_updated2023June.csv` has 6,466 rows against 6,458 in V1, V2, and V4.
  Eight extra rows, cause unknown. Not load-bearing for anything in these documents; recorded only
  so the discrepancy is not rediscovered as a surprise.

---

## What happens after you rule

1. Q1, Q2 and Q4 are applied to the documents and to the plan.
2. A closure stamp and the rulings are appended to §8 of the plan.
3. If Q4 = B, the plan moves and the single director-prompt citation is repaired in the same action.
4. Q3 and Q5, if ruled, are applied; if deferred, they are recorded as open items rather than lost.
