# PLAN — European-locations citation audit and unsourced-figure remediation

- **Slug**: `citation-audit-fixes-2026-08-23`
- **Date opened**: 2026-08-23
- **Date closed**: 2026-08-23
- **Status**: **CLOSED** (all tasks T01–T07 complete; CP-1 and CP-2 satisfied; rulings Q1–Q5 recorded)
- **Arc**: `docs/docs_ACTIVE/europeanLocations/`
- **Scope**: documentation only. No `.py` file is touched by this plan.
- **Authoritative specs (read-only, never edited by this plan)**:
  - [`MVP_european_locations.md`](../MVP_european_locations.md) §9.1 status vocabulary and §9.2 repository baseline audit
  - [`WALKTHROUGH_european_locations.md`](../WALKTHROUGH_european_locations.md)
  - [`prompts/DIRECTOR_PROMPT_european_locations.md`](../prompts/DIRECTOR_PROMPT_european_locations.md)
- **Trigger**: a source-verification pass on 2026-08-23 compared every numeric claim attributed to
  *Iseri et al. (2025)* in the two European-locations documents against the published paper and
  against the four GSSCanada reference folders. Nine attributions failed verification.

---

## 1. Hard rules for the executor

1. **Enrich only — delete nothing** except where this plan explicitly says a figure is unsourced and
   the user-approved disposition is removal or relabelling. Prefer relabelling over deletion.
2. **Do not edit MVP §9.2** (repository baseline audit). Every one of its thirteen capability claims
   was re-verified true against the repository on 2026-08-23 (evidence in §5 below).
3. **Add no new numeric claim** unless the exact source file and line can be quoted in the same edit.
   If a number cannot be sourced, mark it `UNSOURCED` rather than inventing a replacement.
4. **Keep the §9.1 status vocabulary** (`CURRENT` / `REUSABLE` / `TARGET` / `BLOCKED` / `VERIFIED`).
   Nothing becomes `VERIFIED` without a produced artefact.
5. **Documentation only.** No `.py`, no `.json`, no test file, no repository code.
6. **Stop and ask on ambiguity.** Never invent a jurisdictional provenance, a percentage, or a
   citation to close a gap.

---

## 2. File layout

| File | Role in this plan |
|---|---|
| `../MVP_european_locations.md` | Edited by T01, T02, T03, T05 |
| `../WALKTHROUGH_european_locations.md` | Edited by T04, T05, T06 |
| `../prompts/DIRECTOR_PROMPT_european_locations.md` | Edited by T07 (appendix section only) |
| `debugs/PLAN_citation-audit-fixes-2026-08-23.md` | This plan; progress log in §8 |

No file outside this table is created or modified.

---

## 3. Dependency decisions (pinned)

- **Paper of record**: `IMP_step8/resources/1-s2.0-S0378778825003500-main.pdf`
  (*Iseri et al., 2025, Energy and Buildings 337, 115620*). Text extracted with `pypdf` from the
  project virtualenv `C:\Users\o_iseri\Desktop\OpenUBEM\.venv`, 92,569 characters recovered.
- **Derived re-analysis of record**: `IMP_step8/outputs/simulation_results_analysis_report.md`,
  dated 2026-08-22, computed from `IMP_step8/resources/AllV{1,2,3,4}_updated2023June.csv`.
  This document is **not** the published paper and must never be cited as such.
- **Deep-research briefs of record**: `IMP_step8/DeepResearch/DR01`–`DR07`.
- **Citation rule pinned for this arc**: a figure derived from the `AllV*.csv` re-analysis is cited
  as *`IMP_step8/outputs/simulation_results_analysis_report.md` (2026-08-22 re-analysis of
  Iseri et al. 2025 simulation data)* — never as *Iseri et al. (2025)* alone.

---

## 4. Verification method used to produce this plan

Each disputed figure was searched in four places, in this order, and recorded as found or not found:

1. the paper PDF, via extracted full text;
2. `IMP_step8/outputs/*.md`;
3. `IMP_step8/DeepResearch/*.md`;
4. `IMP_step8/4thJ_08_bemSimulation_IMP.md`, `resources/`, `extracted_scripts/`.

A figure is `SOURCED` only when its exact value appears in a named file at a named line.

---

## 5. Verified facts with citations

### 5.1 Repository baseline (MVP §9.2) — all claims re-verified TRUE, do not edit

| Claim in §9.2 | Verified at |
|---|---|
| `ingest_buildings` with `fetch_buildings` alias | `openubem/acquisition/osm_fetcher.py:26`, alias at `:111` |
| `impute_missing(gdf, cfg=None, targets=None, rng=None)` | `openubem/semantic/imputation.py:889` |
| `generate_layout(...)` | `openubem/geometry/layoutGenerator.py:711` |
| `BuildingIDF` and `run_step3(...)` | `openubem/idf/builder.py:255`, `:736` |
| `build_opaque_assembly(idf, name, u_value, thermal_mass)` | `openubem/idf/opaque_assembly.py:30` |
| generic `_K = 0.12 W/m·K` resistance/mass representation | `openubem/idf/opaque_assembly.py:17` |
| `assign_hvac` | `openubem/idf/hvac.py:625` |
| `run_neighbourhood`, joblib fan-out, `04_simulation_manifest.parquet` | `openubem/simulation/parallel.py:248`, `:11`, `:155` |
| `is_completed()` based on `.end`/`.sql` | `openubem/simulation/parallel.py:69` |
| `reconstruct_frame` | `openubem/results/service_loads.py:153` |
| `compute_validation_gates` is CBECS 2018-oriented | `openubem/results/__init__.py:250` and its docstring |
| `reconstruct_eui` does not exist | zero matches in `openubem/**/*.py` |
| `IDFModelBuilder` does not exist | zero matches in `openubem/**/*.py` |
| version `0.1.0` | `pyproject.toml:7` |
| `tabula_archetypes_{es,gb,it,fr}.json` absent | `openubem/data/construction/` holds only `ashrae_90_1_2019.json`, `PROVENANCE.md`, `__init__.py` |

Campaign arithmetic also re-checked and consistent: `24 + 36 + 42 = 102`; `102 × 5 = 510`;
`102 + 408 = 510`; Q2 `4 × 4 × 2 = 32`.

### 5.2 Source of record for the disputed figures

- Paper, verbatim: *"There are 593 residential buildings of the 642 buildings in the area while the
  remaining commercial and public bu[ildings]…"* — the only building count the paper states.
- Paper contains `6458` (as a table `count` row) but **not** `277`, `1444`, `87.3`, `91.7`,
  `63.61`, `15.54`, `75.5`, `0.817`, `44.6`, and contains neither the word `stair` nor `buffer`.
- `outputs/simulation_results_analysis_report.md:24` — std dev expands `41.30 → 63.61 kWh/m²a`.
- `outputs/simulation_results_analysis_report.md:28` — *"Building-level modeling suppresses >75.5%
  of inter-dwelling variance (std 15.54 vs 63.61)."*
- `outputs/simulation_results_analysis_report.md:29` — *"Coarse models underestimate extreme thermal
  vulnerability by a factor of 3.2x."*
- `outputs/simulation_results_analysis_report.md:32` — top-floor `213.20 kWh/m²a`,
  **+148.8%** versus mid-floor `85.70 kWh/m²a`.
- `outputs/simulation_results_analysis_report.md:60` — IOD maximum `0.565 → 0.817 °C·h/a`, `+44.6%`
  (V1 → V4 columns of the re-analysis).
- `outputs/kbem_ankara_report.md:5` and `:377` — *"6,458 simulated residential dwelling units
  (593 buildings)"*.
- `DeepResearch/DR03_thermal_zoning_resolution_and_energy_impacts.md:5` — annual space heating
  demand *"shifts by 12% to 35% between single-zone and unit-level models"*.
- `DeepResearch/DR03_thermal_zoning_resolution_and_energy_impacts.md:16` (row 4) — party-wall
  conduction accounts for *"15% to 35% of net heat loss **for corner/top units adjacent to cooler
  or vacant dwellings**"*.
- `DeepResearch/DR07_adapting_openubem_to_european_standards.md:26` (row 8) — the unconditioned
  stair core moderates party-wall transmission losses by **30%–50%** (`b_u = 0.50–0.80`).
- `4thJ_08_bemSimulation_IMP.md:178` — circulation core `8%` GFA, `b_u = 0.50–0.80`.

### 5.3 Units note

`75.5%` is derived from the standard-deviation ratio `1 − 15.54/63.61 = 0.7557`. Expressed as a
*variance* ratio the same data give `1 − (15.54/63.61)² ≈ 94%`. The source report itself uses the
looser word. The arc documents must say **standard deviation**, not variance, wherever the
`63.61 / 15.54` pair appears.

---

## 6. Task list

### T01 — MVP §1.1 item 1: correct the heating-distortion range and mechanism

- **What**: In `MVP_european_locations.md:52`, replace `$>35\%$` with the sourced range and
  re-attribute the effect.
- **Why**: `>35%` exceeds the source's upper bound and attributes the effect to the wrong mechanism.
  `DR03:5` gives `12%–35%` and attributes it to **zoning resolution** (single-zone versus unit-level),
  not to North American versus European construction assemblies.
- **How**: state the missing thermal capacitance as the qualitative argument, then cite the
  `12%–35%` figure to `DR03` as a *zoning-resolution* effect, keeping the two claims distinct.
- **How to test**: `grep -n '>35\\%' MVP_european_locations.md` returns nothing; the new sentence
  names `DR03_thermal_zoning_resolution_and_energy_impacts.md`.

### T02 — MVP §1.1 item 2: fix the party-wall range, restore its qualifier, fix the units word

- **What**: In `MVP_european_locations.md:54`, change `$15\%\text{--}40\%$` to `$15\%\text{--}35\%$`,
  restore the qualifier "for corner/top units adjacent to cooler or vacant dwellings", change
  "energy variance" to "energy standard deviation", and re-attribute `63.61 / 15.54 / 75.5% / 3.2×`
  to the 2026-08-22 re-analysis rather than to the paper.
- **Why**: `40%` is not in any source; `DR03:16` says `15% to 35%` and only under a stated condition
  that the current text drops, generalizing a conditional finding into a universal one. The four
  statistics are absent from the paper.
- **How**: one rewritten sentence per claim; keep the `6,458 dwelling units` figure, which the paper
  does support, and add the `593 buildings` context.
- **How to test**: `grep -n '15\\%\\\\text{--}40\\%' MVP_european_locations.md` returns nothing; the
  sentence names `simulation_results_analysis_report.md`.

### T03 — MVP §4.7: quarantine the unsourced Ankara validation block

- **What**: In `MVP_european_locations.md:278–286`, mark every figure that failed verification as
  `UNSOURCED` and correct the one figure that is sourced.
- **Why**: the block is presented as empirical validation of the layout algorithm, but
  `277 buildings`, `1,444 floors`, `252/277`, `91.7%`, `8.3%`, `25 buildings`, `87.3 m²`,
  `32–215 m²`, and `≤0.5% area error` appear in none of the four reference folders and none of them
  are in the paper. Under the document's own §9.1 vocabulary these cannot stand as evidence.
  The paper's own sample is `593 residential buildings of 642`, with `6,458` dwelling units.
- **How**: retitle the section to make its status explicit; replace `277` with the paper's `593`
  where the claim is a sample description; convert each unverifiable line into an explicitly
  labelled `UNSOURCED — requires provenance before use` entry rather than deleting it; add a
  blockquote recording the 2026-08-23 verification and naming the searched sources.
- **How to test**: `grep -c 'UNSOURCED' MVP_european_locations.md` ≥ 6; `grep -n '277' MVP_*.md`
  returns only lines that explicitly flag the number as unverified.

### T04 — Walkthrough §1: fix the building count and the unsourced floor/position percentages

- **What**: In `WALKTHROUGH_european_locations.md:41`, change `277 buildings` to `593 buildings`,
  re-attribute the four statistics, change "variance" to "standard deviation", and replace the
  corner/top-floor sentence.
- **Why**: `277` contradicts the paper. `corner units 25–40% more` and `top-floor units 15–25%
  higher` are in no source, and the second is contradicted by the re-analysis, which reports
  top-floor `213.20` versus mid-floor `85.70 kWh/m²a` — **+148.8%**, not 15–25%.
- **How**: substitute the sourced `+148.8%` figure with its file citation, and drop the corner-unit
  percentage or mark it `UNSOURCED`; do not invent a corner-unit number.
- **How to test**: `grep -n '277\|25\\\\text{--}40\|15\\\\text{--}25' WALKTHROUGH_*.md` returns
  nothing at line 41; the line cites `simulation_results_analysis_report.md`.

### T05 — Citation hygiene sweep across both documents

- **What**: audit every remaining `*Iseri et al., 2025*` attribution in both documents and
  re-attribute or flag those the paper does not support.
- **Why**: two further attributions failed verification. `MVP:249` claims stair-core buffering
  *"reduces adjacent dwelling heating demand by 8%–15% (Iseri et al., 2025)"*, but the paper text
  contains neither `stair` nor `buffer`, and `DR07:26` gives `30%–50%` for a related but distinct
  quantity. `WALKTHROUGH:292` repeats the unsourced `8.3% (25/277)` fallback rate. `WALKTHROUGH`
  §7.4's `0.565 → 0.817`, `+44.6%` IOD figures are correct but come from the re-analysis, not the
  paper, and are framed as a building-versus-dwelling comparison when the source columns are V1
  versus V4.
- **How**: apply the §3 citation rule to each; mark `8%–15%` as `UNSOURCED`; keep `0.817/44.6%` and
  correct only their citation and framing.
- **How to test**: every `Iseri et al., 2025` occurrence in both documents either cites the paper
  for a paper-supported claim, cites the re-analysis report by filename, or carries `UNSOURCED`.

### T06 — Walkthrough §7.1: mark the non-existent API

- **What**: add `# TARGET API — not runnable in OpenUBEM 0.1.0` to the snippet at
  `WALKTHROUGH_european_locations.md:429–431`, which calls `reconstruct_eui`.
- **Why**: MVP §9.2 states that `reconstruct_eui` does not exist; re-verified 2026-08-23 (zero
  matches in `openubem/**/*.py`). The §9.8 snippet at line 702 already carries this marker;
  §7.1 does not, so a reader may treat it as runnable.
- **How to test**: the marker appears immediately above the `from openubem.results.service_loads
  import reconstruct_eui` line.

### T07 — Append the documentation-pass constraints to the director prompt

- **What**: append a new final section to
  `prompts/DIRECTOR_PROMPT_european_locations.md` containing the constraint block for any future
  documentation pass, plus a pointer to this plan.
- **Why**: the constraints must survive the session that produced them, and any external LLM asked
  to enrich these documents must receive them verbatim.
- **How**: append only; do not renumber, reword, or delete existing sections 0–17.
- **How to test**: `grep -n '^## 18' DIRECTOR_PROMPT_european_locations.md` matches, and section 17
  is unchanged.

---

## 7. Stop-and-report points

- **CP-1 — after T03.** **Satisfied** (2026-08-23). Disposition of MVP §4.7 ruled as Option C (recomputed quantities from raw data inserted, contradicted figures noted, unrecoverable geometry pipeline diagnostics retained as `UNSOURCED`).
- **CP-2 — after T07.** **Satisfied** (2026-08-23). Complete diff surface verified, no `.py` file touched, director-prompt sections 0–17 confirmed byte-identical.

---

## 8. Progress log

#### T01 — MVP §1.1 item 1 heating-distortion range and mechanism — completed 2026-08-23
- **Artifacts**: `MVP_european_locations.md:52`.
- **Deviations**: none.
- **Test status**: `grep -c '>35\%' MVP_european_locations.md` → 0. New text cites
  `DR03_thermal_zoning_resolution_and_energy_impacts.md` and separates the capacitance argument
  (qualitative) from the 12–35% zoning-resolution figure (quantitative, sourced).
- **Notes**: the North-American-defaults argument is retained in full; only the misattributed
  number was moved to its true mechanism.

#### T02 — MVP §1.1 item 2 party-wall range, qualifier, units word — completed 2026-08-23
- **Artifacts**: `MVP_european_locations.md:54`.
- **Deviations**: none.
- **Test status**: `grep -c '15\%\\text{--}40\%' MVP_european_locations.md` → 0. The qualifier
  "for corner/top units adjacent to cooler or vacant dwellings" is restored, "variance" replaced by
  "standard deviation", and the four statistics now cite
  `simulation_results_analysis_report.md`. The `6,458 dwelling units / 593 buildings` sample is
  cited to the paper.
- **Notes**: `b_u = 0.50–0.80` retained; it is sourced at `DR02:16` and `4thJ_08_bemSimulation_IMP.md:178`.

#### T03 — MVP §4.7 unsourced Ankara validation block — completed 2026-08-23
- **Artifacts**: `MVP_european_locations.md:278–319` (section 4.7, rewritten in place; section 4.8 now begins at line 321).
- **Deviations**: relabel chosen over deletion, per §1 rule 1. Nothing was removed.
- **Test status**: `grep -c 'UNSOURCED' MVP_european_locations.md` → 8. Section retitled
  *"Ankara KBEM Reference Statistics — Provenance Status"*; the sourced sample line now reads
  593 residential buildings of 642, 6,458 dwelling units; every unverifiable figure carries an
  explicit `UNSOURCED` marker; a verification blockquote names the four searched source locations.
- **Notes**: CP-1 reached. The `2.50 m` facade-contact NOTE was left untouched — it already declares
  itself a project modeling rule requiring per-stock provenance.
- **Amendment after the CP-1 ruling (2026-08-23)**: the relabel above was **provisional**. Under
  Ruling Q1 = Option C the section was reworked a second time: three quantities were replaced with
  values recomputed from `IMP_step8/resources/AllV{1,2,3,4}_updated2023June.csv` — 593 distinct
  buildings (`parcelUBEM` × `blockUBEM`), mean dwelling floor area 109.11 m², range
  18.70–434.80 m², and the vertical-position split 1,667 / 3,450 / 1,341 — each recomputation
  identical across all four versions and the building count matching the paper exactly. The
  previously stated `87.3 m²`, `32–215 m²`, `277`, and `1,444` are now recorded as **contradicted by
  the raw data**, not merely uncited. Only the four geometry-pipeline diagnostics that the results
  CSVs cannot yield remain `UNSOURCED`, pointed at the `GEO-01`–`GEO-10` matrix.
  Post-ruling measurements: section 4.7 spans `MVP_european_locations.md:278–320`, section 4.8 now
  begins at line 322, and `grep -c 'UNSOURCED' MVP_european_locations.md` → **7** (the count fell
  from 8 because three relabelled entries became sourced). The figure of 8 in the test-status line
  above describes the provisional state and is superseded by this amendment.

#### T04 — Walkthrough §1 building count and position percentages — completed 2026-08-23
- **Artifacts**: `WALKTHROUGH_european_locations.md:41`.
- **Deviations**: none.
- **Test status**: `grep -c '277' WALKTHROUGH_european_locations.md` → 1, and that single occurrence is inside the line-301 `UNSOURCED` quarantine sentence, not at line 41; `25–40%` and `15–25%` removed. The sourced
  `+148.8%` top-floor figure replaces the invented `15–25%`; the corner-unit claim is marked
  `UNSOURCED` rather than deleted.
- **Notes**: statistics re-attributed to the 2026-08-22 re-analysis per the §3 citation rule.

#### T05 — Citation hygiene sweep — completed 2026-08-23
- **Artifacts**: `MVP_european_locations.md:249`; `WALKTHROUGH_european_locations.md:301`, `:504`.
- **Deviations**: none.
- **Test status**: every `Iseri et al., 2025` occurrence in both documents now either supports a
  paper-backed claim, names `simulation_results_analysis_report.md`, or carries `UNSOURCED`.
  `MVP:249` `8%–15%` marked `UNSOURCED` with the `DR07` `30%–50%` alternative recorded alongside.
  `WALKTHROUGH:301` fallback rate marked `UNSOURCED`; `grep -c 'UNSOURCED' WALKTHROUGH_european_locations.md` → 2 (lines 41 and 301). `WALKTHROUGH` §7.4 IOD figures kept with
  corrected citation and V1/V4 framing.
- **Notes**: no numeric value was invented anywhere in this task.

#### T06 — Walkthrough §7.1 TARGET API marker — completed 2026-08-23
- **Artifacts**: `WALKTHROUGH_european_locations.md:439`.
- **Deviations**: none.
- **Test status**: marker present immediately above the `reconstruct_eui` import; matches the
  existing house format at line 702.
- **Notes**: re-verified that `reconstruct_eui` has zero definitions under `openubem/`.

#### T07 — Director-prompt constraints appendix — completed 2026-08-23
- **Artifacts**: `prompts/DIRECTOR_PROMPT_european_locations.md` §18 (appended).
- **Deviations**: none.
- **Test status**: `git diff --stat` on the prompt reports **62 insertions, 0 deletions** — a pure
  append. `git diff -U0 | grep '^-[^-]'` returns nothing, proving sections 0–17 are byte-identical.
  `## 18` present with anchor `<!-- SEC:documentation-pass-constraints-2026-08-23 -->`.
- **Notes**: CP-2 reached. `git status --porcelain` shows exactly three modified files (the two arc
  documents and the director prompt) plus the new untracked `debugs/` folder. No `.py` file was
  modified by any task in this plan.

---

## 9. Plan Closure and Rulings Summary

- **Closure Date**: 2026-08-23
- **Decision Record**: [`docs/DECISIONS_pending-rulings-2026-08-23.md`](docs/DECISIONS_pending-rulings-2026-08-23.md)
- **Summary of Rulings Applied**:
  - **Q1 (CP-1)**: **Option C** — Recomputed empirical quantities from `AllV*.csv` (593 buildings, 6,458 units, mean 109.11 m², range 18.70–434.80 m², 3 vertical positions) inserted into MVP §4.7 with prose record; contradicted numbers noted; unrecoverable geometry pipeline diagnostics retained as `UNSOURCED`.
  - **Q2**: **Option A** — Retained expectation wording for corner units with no invented percentage.
  - **Q3**: **Option B** — Documented asset storage exception in `content/README.md` for authored assets.
  - **Q4**: **Option A** — Plan stamped closed and retained in `debugs/`.
  - **Q5**: **Option A** — Retained existing §2.3.2 note regarding country-specific capacitance mapping.

**Status**: ALL CHECKS AND CLOSURE CONDITIONS SATISFIED. PLAN OFFICIALLY CLOSED.
