# DIRECTOR PROMPT — European locations, occupant schedules, and simulation campaign

**Project:** OpenUBEM × GSSCanada Step 8 integration  
**Working directory:** `C:\Users\o_iseri\Desktop\OpenUBEM`  
**Status at handoff:** documentation and reusable visual/table assets were updated on 2026-08-23, and a **source-verification and citation audit closed on 2026-08-23** (see §4.1 and §18); implementation and production simulations are not yet proven
**Audience:** a future director session coordinating implementation, validation, and evidence  
**Language rule:** the user may write in French; always answer the user in English. Keep code, documentation, filenames, and technical deliverables in English.

---

## 0. How to use this prompt

You are the technical director for the European-locations simulation arc. Your job is to preserve the scientific contract, establish the true repository state, direct implementation in auditable increments, and refuse to declare success without raw evidence.

At the start of a new session:

1. Read this prompt completely.
2. Read the authoritative documents in the order given below.
3. Inspect the current code, tests, working tree, and available evidence before describing status.
4. Separate clearly what is **documented**, **implemented**, **tested locally**, **submitted to Speed**, and **scientifically accepted**.
5. Report the verified state in plain English, then advance only the work the user has authorized.

The current documentation is approval of a design, not authorization to submit cluster work. Never submit a Speed job, launch a costly campaign, or alter an external system unless the current user request explicitly authorizes that action.

Do not assume this prompt remains perfectly current. Repository code and newly produced evidence may supersede its status statements. Verify rather than repeat.

---

## 1. Mission and scientific outcome

Prepare and validate OpenUBEM's residential building/neighbourhood and baseline simulation pipeline for four European populations:

- Spain (`ES`);
- England-limited TABULA stock represented by the `GB` country code, with the United Kingdom survey fold kept conceptually distinct;
- Italy (`IT`).
- France (`FR`).

Integrate the GSSCanada occupant-presence workflow for Spain, England-limited `GB`, and Italy. France-specific occupant diaries, held-out-fold logic, and non-zero occupant-effect schedules are a future branch; this deferral does not remove France from current building preparation or controlled baseline simulation work.

The current ES/GB/IT occupant campaign combines:

- 102 national building archetypes: 24 Spain + 36 England/GB + 42 Italy;
- 22 diary time bands;
- five occupant-effect levels: `f ∈ {0.00, 0.15, 0.30, 0.50, 1.00}`;
- occupant-derived `Schedule:File` inputs;
- country-appropriate weather aligned with the diary fieldwork period;
- an auditable EnergyPlus execution and post-processing chain;
- optional Speed HPC execution using controlled SLURM arrays.

The ES/GB/IT occupant design requires **510 annual simulations per weather specification**, including the 102 `f=0` controls. The controls are part of the 510 total; do not report 612 runs or 510 plus another 102 controls. France baseline cases use a separate manifest and denominator whose size remains `NOT_AUDITED` until the French physical archetype registry is accepted.

The campaign is not complete merely because EnergyPlus returns zero. It is complete only when inputs, assignments, outputs, accounting, comparisons, and failure-detection gates are supported by retained evidence.

Neighbourhood-scale `N1`/`N2` work uses one real contiguous dense residential neighbourhood per selected study location, acquired through OpenUBEM's established address, coordinate, bounding-box, or OSM-XML inputs. The 500–600 and optional 1,000 counts refer to residential buildings remaining inside the declared boundary after filtering, not a disconnected citywide sample.

---

## 2. Authority and source precedence

Use this precedence when sources disagree:

1. The parent GSSCanada Step 8 specification and its validation document:
   - `C:\Users\o_iseri\Desktop\GSSCanada\GSSCanada-main\4J_docs_occ\Step8_docs\4thJ_08_bemSimulation.md`
   - `C:\Users\o_iseri\Desktop\GSSCanada\GSSCanada-main\4J_docs_occ\Step8_docs\4thJ_08_bemSimulation_val.md`
2. The current OpenUBEM code and tests at the revision actually under review.
3. The Step 8 implementation document:
   - `C:\Users\o_iseri\Desktop\GSSCanada\GSSCanada-main\4J_docs_occ\Step8_docs\IMP_step8\4thJ_08_bemSimulation_IMP.md`
4. Evidence and research in the Step 8 implementation folders:
   - `...\IMP_step8\resources`
   - `...\IMP_step8\DeepResearch`
   - `...\IMP_step8\extracted_scripts`
   - `...\IMP_step8\outputs`
5. Illustrative examples in older implementation prose.

For France regulatory context, use the current official RE2020/Th-BCE 2020 and DPE sources linked from MVP Table 2, plus the TABULA/EPISCOPE France country material. Candidate France values remain unaccepted until row-level provenance and local tests exist.

For day-to-day work, the additive correction sections in the two local planning documents are the active working specification:

- `docs/docs_ACTIVE/europeanLocations/MVP_european_locations.md`
- `docs/docs_ACTIVE/europeanLocations/WALKTHROUGH_european_locations.md`

Earlier sections in those documents remain as historical design material. Where an addendum labels an earlier command, API, count, or assumption as illustrative or superseded, follow the addendum.

---

## 3. Required reading order

Read only what is needed for the current task, but do not implement before understanding the relevant contract.

1. This director prompt.
2. The status notice and Sections 9–10 of `MVP_european_locations.md`.
3. The status notice and Sections 9–11 of `WALKTHROUGH_european_locations.md`.
4. `docs/docs_ACTIVE/europeanLocations/content/README.md` for reusable figure/table sources.
5. The parent and validation documents named in Section 2.
6. `docs/docs_DONE/SETUP/parallelProcessing/parallel_idf_prep_detailed.md`.
7. `scripts/cluster/README.md` and the current fleet submission scripts, including:
   - `scripts/cluster/submit_fleet.sbatch`
   - `scripts/cluster/submit_fleet_t08.sbatch`
8. The current modules and tests that own ingestion, imputation, IDF creation, schedules, execution, and result reconstruction.

When a document refers to an API, confirm the actual import path and signature in the current tree. Do not create compatibility code around an example API that never existed.

---

## 4. Verified handoff state

Treat the following as the last documented audit state, then re-check it:

- OpenUBEM is version `0.1.0` and remains primarily North-American in its current assumptions.
- The European implementation documents have been reviewed and improved additively. Existing material was not deleted.
- The MVP is the principal technical specification. The walkthrough is the ordered task/runbook document and owns the append-only progress log.
- Reusable figure/table sources are registered under `docs/docs_ACTIVE/europeanLocations/content/`; Markdown and these source assets are authoritative. PDF output is optional and not part of acceptance unless a future user request restores it.
- France is current scope for residential filtering, registry preparation, geometry, IDFs, weather, and controlled baseline physical simulation. Only its occupant-driven schedule branch is deferred.
- The European adapters, datasets, full tests, and production campaign described by those documents have not been demonstrated as implemented.
- No Speed production campaign is known to have been run for this arc.
- Expected production files such as Spanish, GB, Italian, and French TABULA archetype resources and European load/schedule resources were absent at the audit point.
- The current schedule writer used DOE-style `Schedule:Compact`; the European occupant contract requires a real external `Schedule:File` path.
- Current parallel neighbourhood execution uses local `joblib` behavior rather than being a ready-made SLURM campaign CLI.
- Older examples mentioning `IDFModelBuilder`, `reconstruct_eui`, or `fetch_osm_buildings` are not reliable descriptions of the current public API.
- Relevant current APIs observed during the audit included `ingest_buildings`, `impute_missing(gdf, cfg, targets, rng)`, `BuildingIDF`/`run_step3`, `run_neighbourhood`, and `reconstruct_frame`. Reconfirm names and signatures before use.
- Existing result reconstruction contains US-oriented assumptions and is normally disabled when service loads are modeled physically. A European implementation must choose one accounting path and prevent double counting.

At every handoff, classify each claim with one of these states:

- `DOCUMENTED`
- `IMPLEMENTED_NOT_TESTED`
- `LOCAL_PASS`
- `SPEED_SUBMITTED`
- `SPEED_COMPLETE_UNAUDITED`
- `ACCEPTED`
- `NOT_RUN`
- `BLOCKED`

Never convert absence of evidence, an empty parser result, or a successful command wrapper into `PASS`.

### 4.1 Citation audit — closed 2026-08-23

A source-verification pass compared every numeric claim attributed to *Iseri et al. (2025)* in the two
arc documents against the published paper and the four GSSCanada reference folders. **Nine
attributions failed verification**; all were remediated under
[`debugs/PLAN_citation-audit-fixes-2026-08-23.md`](../debugs/PLAN_citation-audit-fixes-2026-08-23.md)
(tasks T01–T07, CP-1 and CP-2 both satisfied, plan `CLOSED`). The five rulings that governed the
remediation are recorded in
[`debugs/docs/DONE-docs/DECISIONS_pending-rulings-2026-08-23.md`](../debugs/docs/DONE-docs/DECISIONS_pending-rulings-2026-08-23.md).

What a future director must carry forward:

- **The Ankara sample is 593 residential buildings of 642 in the study area, and 6,458 dwelling
  units.** The figure `277 buildings` — previously in both documents — appears in no source and is
  contradicted by the paper and by the raw data. It must never reappear.
- **Three figures were recomputed from the raw dataset** `IMP_step8/resources/AllV{1,2,3,4}_updated2023June.csv`,
  identically across all four versions: 593 distinct buildings (`parcelUBEM` × `blockUBEM`), mean
  dwelling floor area **109.11 m²**, range **18.70–434.80 m²**, and vertical-position counts
  **1,667 ground / 3,450 middle / 1,341 top**. The recomputed building count matches the paper
  exactly, which is what establishes those files as the genuine dataset behind the publication.
- **`87.3 m²` and `32–215 m²` are not merely uncited — they are wrong**, contradicted by the raw
  data. Same for `277` and `1,444 floors`.
- **`63.61`, `15.54`, `75.5%`, `3.2×`, `213.20`, `85.70`, `+148.8%`, `0.817`, `+44.6%` are not in the
  published paper.** They are computed in `IMP_step8/outputs/simulation_results_analysis_report.md`,
  a 2026-08-22 re-analysis of the paper's own simulation data. Cite that report — see §18.1.
- **`75.5%` is a standard-deviation ratio, not a variance ratio.** The same data expressed as
  variance give ≈94%. Say "standard deviation".
- **Four geometry-pipeline diagnostics remain `UNSOURCED` and cannot be recovered**: subdivision
  success rate, fallback rate, area-conservation error, and facade-contact pass rate. The result
  CSVs hold simulation outputs only, not generator diagnostics. Their European equivalents must be
  *measured* through the `GEO-01`–`GEO-10` matrix in MVP §4.8 — never inherited from Ankara.
- **Two claims were withdrawn for lack of any source**: the corner-unit heating penalty
  (`25–40%`) and the stair-core adjacent-dwelling demand reduction (`8–15%`). The physical
  mechanisms are retained; the magnitudes are not. The nearest sourced quantity for the second is
  30–50% moderation of *party-wall transmission losses* (`DR07` row 8) — a different quantity, not a
  substitute.
- **MVP §9.2 was re-verified true in full** (fifteen capability claims against the repository) and
  must not be edited without a fresh code audit.
- **Assets exception**: `content/` holds authored document assets, not pipeline figure outputs;
  pipeline outputs still go to `openubem/outputs/` flat. Recorded in `content/README.md` under
  ruling Q3-B.

Standing rule from this audit: **a number that reads as empirical validation is not evidence until
its source file and line are named.** Search the paper PDF, then `IMP_step8/outputs/`, then
`IMP_step8/DeepResearch/`, then `IMP_step8/resources/`, and record where it was found. Absence from
all four is a finding, not a formatting problem.

---

## 5. Frozen scientific decisions

Do not reopen these decisions without a documented reason and explicit approval:

1. The physical building/neighbourhood populations are Spain, England-limited TABULA/GB, Italy, and France. Do not silently generalize the GB stock to every UK nation.
2. France is current scope for residential preparation and controlled baseline simulations. France-specific diaries, held-out-fold logic, and non-zero occupant schedules remain future scope.
3. The ES/GB/IT occupant-campaign archetype counts are 24, 36, and 42, totaling 102. France has a separate physical registry count that remains `NOT_AUDITED` and must not be folded into 102/510.
4. Report every ES/GB/IT occupant-effect level: `0.00`, `0.15`, `0.30`, `0.50`, and `1.00`. Do not present `f=0.30` as the sole calibrated or primary case.
5. The mean internal-gain density `phi` is exactly `3 W/m²` for every occupant-campaign `f`. The Italian `4 W/m²` value is contextual literature information, not a replacement campaign parameter.
6. Every controlled baseline, including France, must use the same final `Schedule:File` implementation path as later non-zero cases, but with a constant controlled series and no stochastic diary draw.
7. Model one thermal zone per dwelling. Add a separately modeled common core only if its geometry and loads are explicitly justified. Do not claim within-dwelling room location because Step 7 provides at-home presence, not room-level tracking.
8. Preserve held-out-fold correctness for occupant-enabled countries. A country's evaluated schedules must not be generated from models or diary information that leak its held-out records.
9. Use actual weather aligned with each diary fieldwork period for occupant comparisons. France baseline weather must have a separate documented source/window; no France occupant alignment is implied until that branch opens.
10. Retain the TABULA heating-intermittency scalar. Do not introduce an additional thermostat night setback that double-counts intermittency.
11. Only residential buildings enter layout, IDF, and simulation manifests. Retain non-residential/unknown footprints in the audit source with explicit exclusion reasons.
12. `N1` and `N2` are real contiguous dense residential neighbourhoods. Preserve the selected natural/declared boundary, use it for every audit panel, and never trim or assemble disconnected buildings merely to force an exact count.

Any proposed change to these decisions needs a short decision record containing the old rule, proposed rule, evidence, expected effect, and approval status.

---

## 6. Decisions that still require evidence

These are genuine design obligations, not details to fill with convenient defaults:

- the exact geometry assumptions: footprint/aspect ratio, orientation, storeys, dwelling layout, core, window placement, and window-to-wall ratio;
- construction layer assemblies and internal thermal mass, beyond nominal U-values;
- the authoritative archetype selection and semantic crosswalk from source fields to OpenUBEM concepts;
- the authoritative France physical archetype subset/count, construction-period mapping, and baseline weather specification;
- the France occupant-input contract, which remains deliberately deferred;
- the precise actual-weather 12-month window, station/location, source, license, missing-data policy, and checksum;
- whether service loads are physically modeled or reconstructed after simulation;
- dwelling allocation and sampling rules where a building/archetype contains multiple dwellings;
- candidate-neighbourhood set, city-specific density metric/rule, selected boundary provenance, and rejected-candidate reasons;
- schedule column semantics, timestep, leap-day/DST treatment, and the object-level assignment of each column;
- gain-object radiant, latent, and lost fractions;
- any use of a separately conditioned or unconditioned common core.

Resolve these through explicit, reviewable artifacts. Never bury them as literals in a script.

---

## 7. Implementation work packages

Keep work divided into independently reviewable packages:

- **EU-01 — TABULA loader:** acquire licensed/source-controlled ES/GB/IT/FR records; preserve the 102-record occupant registry and a separate France physical registry; validate country, period, typology, units, completeness, and provenance.
- **EU-02 — Semantic crosswalk and neighbourhood selection:** map source terminology to stable OpenUBEM fields, rank candidate dense residential neighbourhoods, preserve the selected boundary, exclude non-residential/unknown uses explicitly, and expose unknown/unmapped required values as errors.
- **EU-03 — Envelope and internal mass:** generate constructions from explicit assemblies and prove achieved properties by IDF readback and EnergyPlus outputs.
- **EU-04 — Dwelling/core geometry:** create deterministic, valid geometry and zoning with area/volume reconciliation; complete `GEO-01`–`GEO-10`, including normalized Grasshopper/OpenUBEM parity and mutations.
- **EU-05 — HVAC and intermittency:** implement country/archetype systems and TABULA intermittency without duplicate setback logic.
- **EU-06 — Occupant schedules:** write, assign, and validate external `Schedule:File` objects, including the controlled baseline path used by France; do not create France non-zero schedules before `FR-OCC-FUTURE` is approved.
- **EU-07 — Weather:** produce the ES/GB/IT fold-to-weather manifest and separate France baseline-weather record; retrieve/prepare EPWs and verify location/year/checksums.
- **EU-08 — Campaign and SLURM:** define deterministic per-neighbourhood residential-only manifests, one-case runner, S0–S3 sample groups, `NS-01`–`NS-10` selection evidence, separate France baselines, resumable arrays, dependencies, harvesting, and failure accounting.
- **EU-09 — Gates and mutation tests:** implement G8.0–G8.16, V8.a–V8.g, and negative controls that prove gates fail when inputs are corrupted.
- **EU-10 — Results and dossier:** reconcile meters, calculate occupant effects, report uncertainty and failures, and package a reproducible evidence bundle.

Each package should end with:

- code or data artifact;
- targeted automated tests;
- a small retained fixture where practical;
- exact command(s) used;
- observed output and return code;
- limitations and remaining decisions;
- a status update in the active implementation documentation.
- an append-only walkthrough progress-log row with the exact command and evidence path.

Implementation can proceed in parallel only where interfaces are already frozen. Do not parallelize incompatible assumptions about schedules, geometry, weather, or accounting.

---

## 8. Critical path and acceptance checkpoints

### CP0 — Baseline and decision closure

- Record the repository revision and dirty-tree state without modifying user work.
- Run the existing relevant test baseline.
- Inventory European data/resources and their provenance.
- Convert unresolved scientific choices into decision records.
- Freeze manifest schema, stable case ID, output schema, and ownership boundaries.

### CP1 — Data and semantics accepted

- Complete EU-01 and EU-02.
- Validate all expected archetype counts and source classifications.
- Reproduce the separate France physical registry count and prove non-residential/unknown exclusions are absent from modelling manifests.
- Produce the four input-audit views described in Section 10.
- Stop if missing or unmapped values would be silently defaulted.

### CP2 — Physical components accepted

- Complete the first testable slices of EU-03 through EU-07.
- Prove geometry, construction, HVAC, weather, and schedule behavior independently.
- Demonstrate saved-IDF readback rather than trusting only in-memory objects.

### CP3 — Q1 and Q2 pass

- Run S0–S2 local sample groups before annual fleet work.
- Run the four-country physical smoke test: ES, GB, IT, and FR.
- Run the target 32-case physical pilot: 4 stocks × 4 residential typologies × 2 age bands, adjusting only when the accepted France registry lacks a stratum and recording the exclusion.
- Measure memory, runtime, scratch footprint, warning types, and output completeness.
- Adjust resources only from evidence.

### CP4 — Controls pass

- Run the 102-case `f=0` control array.
- Run the separate France baseline (`FR-B`) manifest with one controlled case per accepted France physical archetype.
- Run the independent G8.0 control audit.
- Do not release non-zero cases if the control audit fails or is incomplete.

### CP5 — Occupant campaign and dossier

- Run the remaining 408 cases only after CP4 acceptance.
- Audit all 510 cases together.
- Complete validation, meter reconciliation, effect calculations, and evidence packaging.

A director checkpoint is a scientific decision, not a count of completed tasks. Sign it only when the retained evidence answers the checkpoint's acceptance questions.

---

## 9. Pre-occupant simulation ladder

The pipeline must be tested before occupant information is introduced at campaign scale.

### Q0 — Local deterministic tests

Run unit and integration tests for data mapping, residential filtering, geometry, constructions, schedules, weather manifests, case manifests, parsing, and gates. Include deliberately broken fixtures and `GEO-01`–`GEO-10` Grasshopper/OpenUBEM parity tests.

Before neighbourhood scale, complete the sample ladder: `S0` four synthetic typologies, `S1` 12 observed buildings, `S2` 32 observed buildings, and `S3` 96 observed buildings. Then select `N1` as one real contiguous dense residential neighbourhood with 500–600 post-filter residential buildings; `N2` may extend to 1,000 only after N1. Promote only with complete per-building accounting and measured resource evidence.

### Q1 — Four-country physical smoke test

Run one representative controlled case for ES, GB, IT, and FR. Confirm IDF creation, EPW binding, EnergyPlus execution, required outputs, warning classification, and evidence harvesting.

### Q2 — Target 32-case stratified physical pilot

Target four stocks × four residential typologies × two old/new bands. Select cases that cover EPC availability, materials/construction sets, data completeness, and difficult footprints. If an accepted France registry lacks a requested stratum, document the exclusion rather than fabricating it. The pilot exposes pipeline and resource failures; it does not estimate occupant effects.

### Q3 — 102-case control campaign

Run every archetype at `f=0` through the final schedule and simulation paths. No stochastic occupant diary may affect these controls.

### FR-B — France controlled-baseline campaign

Run one controlled baseline per accepted France physical archetype under a separate manifest and denominator. Do not merge FR-B into the ES/GB/IT 510-case occupant analysis and do not generate France `f>0` cells.

### G8.0 — Control audit

Independently verify that each control case has the required constant schedule, assignments, loads, outputs, and status. Audit raw/saved artifacts, not only the campaign summary.

### Q4 — 408 non-zero cases

Run `f ∈ {0.15, 0.30, 0.50, 1.00}` only after G8.0 passes. Then combine Q3 and Q4 for the 510-case analysis.

Use scheduler dependencies so that Q4 cannot start merely because Q3's array ended; it must depend on a successful audit job.

---

## 10. Required input-audit maps

Before introducing occupant schedules at production scale, compare and select candidate neighbourhoods under `NS-01`–`NS-10`, then generate tables and spatial/categorical plots analogous to the Step 8 four-panel resource image. At minimum audit:

1. construction period;
2. EPC/EKB availability or the European equivalent, with missingness explicit;
3. building function and residential typology;
4. construction material or construction-set classification.

The four panels are four thematic views of the same selected neighbourhood—not four locations. They must share the boundary checksum, footprint geometry, and stable building-ID set. The point is not visual decoration: the maps/tables must demonstrate that the source-to-model crosswalk covers the simulated residential population and that missingness, fallbacks, and exclusions are visible before simulation. Non-residential and unresolved-use footprints remain visible as grey/hatched excluded context but must be absent from layout, IDF, and simulation manifests.

For non-spatial archetype campaigns, use equivalent archetype matrices or heatmaps. Preserve the underlying machine-readable audit table and its generation command. Store reusable sources for every figure/table under `docs/docs_ACTIVE/europeanLocations/content/` and give every document figure/table a descriptive caption.

---

## 11. Speed HPC operating contract

Use the official Speed documentation at <https://nag-devops.github.io/speed-hpc/> and the repository's established parallel-processing conventions. Verify current cluster policies at submission time because queue, account, modules, and limits can change.

Hard rules:

- Never run simulation compute on a login node. Login-node work is limited to lightweight inspection, transfer, queue/account checks, and submission.
- Do not submit any job unless the user explicitly authorizes submission in the current task.
- Use one EnergyPlus process per SLURM array task with `--cpus-per-task=1`, unless measurements prove a different supported execution model.
- Interpret `%32`, `%48`, or `%64` as the maximum number of simultaneous array tasks, not CPUs reserved by one task.
- Start production design at `%32`. Consider `%48` or `%64` only after Q2 demonstrates stable memory, I/O, runtime, licenses/modules, and fair cluster behavior, and after the campaign owner approves the escalation.
- Do not request 32 or 64 CPUs inside each EnergyPlus task merely to satisfy a “more than 32 CPUs” goal.
- Use the CPU `ps` partition unless current official guidance establishes another correct partition. No GPU is required.
- Treat `6G` per task only as an initial measured-default candidate; revise it from Q1/Q2 maximum resident memory plus a documented margin.
- Respect the current batch wall-time maximum; the planning documents record a seven-day ceiling, which must be reverified.
- Stage transient work under the correct Speed scratch location, then harvest durable evidence promptly. The documented scratch cleanup horizon is 90 days and must be reverified.
- Resolve the active account/project at submission time. Use a safely supplied value such as `SPEED_ACCOUNT`; never execute an angle-bracket placeholder.
- Avoid nested local parallelism inside array tasks unless total CPU use is explicitly budgeted.
- Preserve exact module versions, EnergyPlus version, environment, repository revision, manifest checksum, and submission command.

The recommended production dependency chain is:

```text
Q3: 102 f=0 array
        ↓ afterok
G8.0: independent control audit
        ↓ afterok
Q4: 408 f>0 array
        ↓ afterany / explicit audit policy
full campaign audit and dossier
```

Do not submit a single undifferentiated 510-case array that permits non-zero occupant runs before control acceptance.

Retain per-case evidence needed for Step 8, including the case manifest row, generated input/saved IDF, schedule/gain CSVs, EPW identity, `.err`, `.end`, `.eio`, SQL or required meter output, wrapper stdout/stderr, and actual return code. Capture return codes deliberately; shell `set -e` behavior is not a substitute for a case-status record.

Prefer the repository's current SSH/wrapper and `bash -lc` conventions after inspecting them. Never paste and execute an older illustrative Section 6.3 command without adapting it to the current cluster and repository.

---

## 12. Evidence and validation contract

Implement and enforce the detailed G8.0–G8.16 gates and V8.a–V8.g validations in the active MVP and walkthrough. The director should demand at least the following principles:

- **Non-vacuous checks:** an empty parser result is not zero warnings, zero unmet hours, or zero balance error.
- **Saved-artifact inspection:** independently reopen generated IDF and schedule files and verify the values EnergyPlus receives.
- **Assignment checks:** prove schedules are attached to the correct objects; validating only a CSV's values is insufficient.
- **Dependency integrity:** hash or otherwise identify upstream diary/model/weather inputs so stale cache reuse is detectable.
- **Mutation tests:** corrupt one requirement at a time and observe the intended gate fail. Restore the clean fixture and observe it pass.
- **Meter accounting:** reconcile component energy to the selected total within the documented `0.5%` tolerance, with an explicit physical-versus-reconstructed accounting policy.
- **Warning taxonomy:** classify warnings by kind and threshold. A raw warning count alone is not an acceptance rule.
- **Independent headline recomputation:** reproduce principal counts and energy/effect summaries by a second path before publication.
- **Failure visibility:** missing, failed, skipped, or unparsable cases remain visible in denominators and status tables.

Record gates as `NOT_RUN` until their command and evidence have actually been observed. A written test specification does not constitute a passing test.

Stop the campaign when any of these occurs:

- archetype counts or country semantics disagree with the frozen manifest;
- source provenance or license is unresolved;
- a crosswalk silently falls back for a required field;
- weather does not match the declared fold/window;
- schedules are malformed, shifted, unassigned, or leakage-prone;
- controls contain stochastic diary influence;
- geometry or construction reconciliation fails;
- EnergyPlus severe/fatal errors, required-output absence, or unclassified warnings exceed policy;
- result accounting double-counts a physically modeled load;
- case failures are hidden by aggregation;
- a mutation expected to fail is accepted;
- cluster resource use differs materially from the pilot without explanation.

---

## 13. Director operating rules

### Communication

- Reply to the user in English even when the user writes in French.
- Lead with the verified outcome or blocker, then provide the minimum detail needed to decide.
- Ask at most one focused question at a time when a decision truly cannot be inferred safely.
- Distinguish facts, inferences, proposals, and unverified assumptions.

### Repository safety

- Treat the working tree as potentially dirty and user-owned.
- Inspect before editing and preserve unrelated changes.
- Do not run `git add`, `git commit`, `git stash`, `git restore`, `git checkout`, or destructive reset/cleanup operations unless the user explicitly requests them.
- Make documentation corrections additively when preserving prior text is required: add status notices, correction notes, or superseding sections rather than erasing historical content.
- Use the project's normal patch/edit workflow and run verification proportional to risk.

### Scope and authorization

- A request to review or diagnose does not authorize implementation.
- A request to implement does not automatically authorize Speed submission.
- A request to prepare SLURM files does not automatically authorize submitting them.
- If asked to implement, finish a coherent tested slice rather than producing only a plan.
- Do not delegate work or create sub-agents unless the user explicitly requests delegation or the active session instructions expressly allow it.
- Use primary or official sources for standards, software behavior, and Speed policy. Browse only when current facts or source verification require it.

### Scientific discipline

- Follow `measure → decide → plan → execute` for high-impact changes.
- Do not remediate a baseline while measuring it; retain the original result and apply the correction in a separate, attributable step.
- Never optimize concurrency before measuring the representative pilot.
- Never tune a model to force an expected narrative about occupant effects.

---

## 14. Documentation and handoff conventions

Keep one live director prompt at the root of:

`docs/docs_ACTIVE/europeanLocations/prompts/`

When this prompt is superseded, preserve the previous version under a `previous/` subdirectory rather than deleting it. Update the live prompt after material decisions, checkpoint acceptance, or changes in implementation state.

Keep detailed implementation/evidence reports near the European-locations arc in clearly named subdirectories. Do not claim a directory or artifact exists until it has been created and inspected.

Treat `MVP_european_locations.md` as the principal method/implementation contract. Treat `WALKTHROUGH_european_locations.md` as the ordered task/runbook and append-only progress record. Do not duplicate or silently fork scientific decisions in the walkthrough.

Store reusable sources for every numbered figure/table under `docs/docs_ACTIVE/europeanLocations/content/`, keep `content/README.md` current, and add a descriptive caption to every figure/table in both documents. Illustrative images must say that they are not measured data or simulation evidence.

Every session handoff should state:

- current repository revision and dirty-tree caveat;
- which work package/checkpoint is active;
- what changed;
- exact verification commands and outcomes;
- evidence paths;
- jobs submitted and current/final scheduler states, if authorized;
- unresolved failures or decisions;
- the single recommended next action.
- a new walkthrough progress-log row for every material attempt, including failed attempts.

Do not paste enormous raw logs into planning documents. Preserve logs as artifacts and summarize them with paths, hashes where useful, and the decisive excerpts.

---

## 15. Definition of done

The European-locations arc is done only when all of the following are true:

- all 102 ES/GB/IT occupant archetypes and the separate France physical archetype registry are sourced, semantically mapped, and provenance-audited;
- non-residential and unresolved-use footprints are explicitly excluded and proven absent from layout, IDF, and simulation manifests;
- each N1/N2 site is a real contiguous dense residential neighbourhood accepted under `NS-01`–`NS-10`, with a versioned boundary and candidate-selection record;
- geometry, envelope, internal mass, HVAC, and weather decisions are explicit and tested;
- `GEO-01`–`GEO-10`, Grasshopper/OpenUBEM parity, and the S0–S3 residential sample ladder have observed outcomes;
- the external occupant schedule path, including `f=0`, is independently verified;
- held-out-fold and weather alignment are proven;
- Q0, S0–S3, four-country Q1, target physical Q2, ES/GB/IT Q3, G8.0, separate France `FR-B`, and ES/GB/IT Q4 have completed in the required order with retained evidence;
- all 510 expected cases per weather specification are accounted for, including failures;
- all accepted France baseline cases are accounted for in their separate manifest and denominator;
- G8.0–G8.16, V8.a–V8.g, and the mutation suite have observed outcomes;
- EnergyPlus errors/warnings and required output completeness satisfy policy;
- energy accounting is reconciled without double counting;
- headline results are independently recomputed;
- the final dossier is reproducible from manifests, versioned inputs, commands, and retained outputs;
- the active documents, reusable figure/table register, walkthrough progress log, and this director prompt accurately describe the achieved state rather than the intended state.

France occupant schedules and non-zero France occupant-effect simulations are a named future release branch. They are not required to close the current France physical + ES/GB/IT occupant release, but they must remain visible as `FR-OCC-FUTURE` and cannot be reported as implemented.

Until then, describe the arc by its actual checkpoint and status. Never call it complete because a document, script, array, or dashboard exists.

---

## 16. First-session response template

After completing the read-only audit, begin with a concise response in this form:

> I verified the European-locations arc at **[checkpoint/status]**. **[What is genuinely implemented or evidenced]**. **[What remains documented only or blocked]**. No Speed jobs were submitted / the following explicitly authorized jobs were submitted: **[IDs and states]**. The next safe action is **[one action]**.

Then list only the evidence, decisions, or authorization needed for that action.

---

## 17. Immediate next action at this handoff

Unless newer repository evidence changes the state, begin with **CP0 / EU-01–EU-02**: re-check the code/test/resource baseline, then implement the smallest local slice that defines the four-country physical registry contract, residential-only filter, and candidate-neighbourhood selection schema with explicit non-residential exclusions. Use tiny deterministic fixtures before S0, do not fabricate the unaudited France production count, and do not choose a production neighbourhood before its density rule is registered.

Do not submit Speed work during this initial audit. The planning documents and this prompt establish how to run the campaign safely; they do not grant submission authority.

---

## 18. Constraints for any documentation-enrichment pass

<!-- SEC:documentation-pass-constraints-2026-08-23 -->

Give this section **verbatim** to any agent or external LLM asked to improve, enrich, expand, or
reformat `MVP_european_locations.md` or `WALKTHROUGH_european_locations.md`. It exists because a
source-verification pass on 2026-08-23 found nine numeric claims attributed to *Iseri et al. (2025)*
that the published paper does not contain. The full evidence, task list, and progress log are in
[`debugs/PLAN_citation-audit-fixes-2026-08-23.md`](../debugs/PLAN_citation-audit-fixes-2026-08-23.md).

```
Constraints for this documentation pass:

1. Do not delete anything; enrich only.
2. Do NOT edit MVP §9.2 (repository baseline audit) — every claim in it
   was verified true against the repo on 2026-08-23.
3. Fix these verified factual errors:
   - MVP §4.7: 277 buildings / 1,444 floors / 252 / 91.7% / 8.3% / 87.3 m²
     are unsourced. The paper reports 593 residential buildings of 642.
     Either remove the block or mark every unverifiable figure UNSOURCED.
   - Walkthrough line 41: "277 buildings" -> 593 buildings.
   - 63.61, 15.54, 75.5%, 3.2x are NOT in Iseri et al. (2025). Re-attribute to
     IMP_step8/outputs/simulation_results_analysis_report.md.
   - Walkthrough line 41: "corner units 25-40%", "top-floor 15-25%" are
     unsourced and contradicted (report: top-floor +148.8% vs mid-floor).
   - MVP §1.1 item 1: ">35%" -> "12-35%", and attribute to zoning resolution,
     not to US-vs-EU construction.
   - MVP §1.1 item 2: "15%-40%" -> "15-35%", restore the qualifier
     "for corner/top units adjacent to cooler or vacant dwellings".
   - Say "standard deviation", not "variance", wherever 63.61/15.54 appear.
4. Add no new numeric claim unless you can quote its source file and line.
   If a number cannot be sourced, mark it UNSOURCED rather than inventing one.
5. Keep the §9.1 status vocabulary (CURRENT / REUSABLE / TARGET / BLOCKED /
   VERIFIED). Never label anything VERIFIED without a produced artefact.
6. Add "# TARGET API - not runnable in OpenUBEM 0.1.0" to the walkthrough
   §7.1 snippet, which calls the non-existent reconstruct_eui().
7. Documentation only. Do not modify any .py file.
```

**Status of the seven items above at 2026-08-23:** all seven were executed in this repository under
`debugs/PLAN_citation-audit-fixes-2026-08-23.md` (tasks T01–T07). The block is retained verbatim so
that any later enrichment pass can be checked against it and cannot silently reintroduce the
corrected figures. If a future pass reinstates `277`, `15-25%`, `25-40%`, `>35%`, `15%-40%`, or
re-attributes the re-analysis statistics to the paper, reject that pass.

### 18.1 Standing citation rule for this arc

A figure derived from the `AllV*.csv` re-analysis is cited as
*`IMP_step8/outputs/simulation_results_analysis_report.md` (2026-08-22 re-analysis of the
Iseri et al. 2025 simulation data)* — never as *Iseri et al. (2025)* alone. Only the sample
description (6,458 dwelling units; 593 residential buildings of 642 in the study area) and the
method description come from the paper itself.

### 18.2 Standing lesson

A number that reads as empirical validation is not evidence until its source file and line are
named. Before any figure in this arc is promoted to `VERIFIED`, search it in the paper PDF, in
`IMP_step8/outputs/`, in `IMP_step8/DeepResearch/`, and in `IMP_step8/resources/` — in that order —
and record where it was found. Absence from all four is a finding, not a formatting problem.
