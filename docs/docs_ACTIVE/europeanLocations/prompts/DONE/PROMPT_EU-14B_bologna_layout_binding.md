# `EU-14B` — Executor prompt: give Bologna the dwelling layouts it has never had, without corrupting its manifest

- **Arc**: European locations × Step 8.
- **Order**: **after `EU-13B`.** This task consumes `EU-13B`'s partitioner and its conservation fix; running
  it first would emit the same defective strip layouts for a fourth district.
- **Predecessor**: `prompts/previous/PROMPT_EU-14_bologna_construction_year_reopening.md` (closed — Bologna
  is simulated and bound, `openubem/outputs/eu_evidence/EU-14/RESULTS_EU-14.md`). This task closes the one
  gap that closure disclosed.
- **Spec**: same two documents as `EU-13B` — `MVP` §4.2–§4.4 and
  `C:\Users\o_iseri\Desktop\GSSCanada\GSSCanada-main\4J_docs_occ\Step8_docs\IMP_step8\outputs\floor_layout_generation_report.md`.
- **Executor**: external LLM. **Paste everything below the rule into the tool.**
- **Date of prompt**: 2026-08-28. **Blocked task**: none — see §5.
- 🔴 **`D-EU-38` — ruled 2026-08-30 by the owner:** resimulation is unblocked (`EU-13B` `T09`). `T05` below
  may now submit Bologna's resimulation to Speed after `T02`, same cluster hard rules as `EU-13B` `T09`
  (`sbatch --array` only, never the login node, never `srun`, `_ssh()` tcsh wrapper). Regenerate
  `docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_IT-BOL-GALVANI2_viewer.html` from the harvest.

---

## Task (paste from here)

You are working in the OpenUBEM repository `C:\Users\o_iseri\Desktop\OpenUBEM`. Python is
**`.venv/Scripts/python.exe`** — never bare `python`. Git is handled externally: **never commit and never
stage.** Do not edit root `main.py`, any OVERVIEW or DESIGN doc, `previous/MVP_european_locations.md` or
`previous/WALKTHROUGH_european_locations.md`, and never annotate MVP Table 9.7. No `.py` files under
`docs/`.

### 0. Where Bologna actually stands, measured

`IT-BOL-GALVANI2` is simulated and bound: **1,202 of 1,220** residential buildings, pooled heating EUI
**55.5346 kWh/m²** over 2,520,390.9432 m², Speed job `1295646`. 🔴 **Every row's construction period is
imputed** — `construction_period_provenance = IMPUTED_CENSUS_SECTION_CONSTRUCTION_PERIOD` on 1,204 of 1,204
manifest rows — and that tag must appear in the same sentence as any figure you quote, in every document.

Three things are open:

| # | Open item | Measurement |
|---|---|---|
| **1** | **Bologna has zero floor-plan pop-ups.** `scripts/emit_eu11_layout_sidecars.py` calls `allocate_european_dwellings` on a codepath incompatible with the ISTAT-imputed provenance; a test run **wiped `geometry_outcome` to NaN across the manifest** and was recovered only by a clean re-harvest from Speed. | 0 side-cars, vs Madrid 961 / Lyon 297 / London 82 |
| **2** | **The dwelling-count imputation is the weakest of the four districts.** Bologna publishes no per-building dwelling count at all, so 100 % of layouts rest on the four-tier cascade, and **408 of 1,204** could not even reach that. | 796 `DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT`, 408 `FALLBACK_PENDING_LAYOUT_MISSING_DWELLING_COUNT` |
| **3** | **`FINDING 199` is open and unexplained.** 55.5346 sits inside `DR16`'s own pre-registered **INCOMPATIBLE (Too Low)** band (< 95.0; `CONSISTENT` is 115.0–165.0). | `results/RESULTS_EU-11.md` § External validation |

🔴 **Item 1 is a data-destroying bug. Until `T01` is green, never run
`scripts/emit_eu11_layout_sidecars.py` against `IT-BOL-GALVANI2`.**

### 1. `T01` — Make the side-car emitter safe on the ISTAT-imputed path

**What.** Find and fix the incompatibility that let a side-car run write NaN into
`openubem/outputs/eu_evidence/EU-11/IT-BOL-GALVANI2/it_bol_galvani2_manifest.csv`.

**Why.** A tool that can silently destroy a harvested manifest must not be pointed at a fourth district. The
manifest is the only local record of a Speed run.

**How.** Two independent changes, both required:
1. **Root cause.** Trace why the Bologna rows lose `geometry_outcome`. The Bologna preparation path is
   `scripts/run_eu_s2_district_campaign.py::_it_rows` (~line 178), which produces rows with
   `census_section`, `census_section_dominant_period`, `construction_period_provenance` and
   `observed_dwellings = None` — a shape the other three districts never produce. Report the actual
   mechanism with a `file:line`, do not guess.
2. **Make the write non-destructive regardless.** The emitter must never widen or blank a column it did not
   compute. Read the manifest, compute, and write back **only** the columns it owns, asserting row count and
   `building_id` set are unchanged and that no previously-non-null cell became null. If that assertion
   fails, abort and leave the file untouched.

**How to test.** `tests/geometry/test_eu14b_sidecar_manifest_safety.py`: take a copy of the Bologna
manifest, run the emitter against it, and assert byte-identity on every column the emitter does not own, and
zero new nulls anywhere. Add a deliberately-malformed row fixture and assert the emitter aborts without
writing. **Then, and only then**, run it for real against Bologna.

### 2. `T02` — Emit Bologna's layouts with `EU-13B`'s partitioner

**What.** Run the corrected `emit_eu11_layout_sidecars.py` for `IT-BOL-GALVANI2` and regenerate the four
viewers, using the `EU-13B` grid partitioner, conservation fix and >8/floor cap — not the old strip cutter.

**Why.** Bologna is the only district that has never had a pop-up; it must arrive already conforming to the
ruled scheme rather than inheriting the defects `EU-13B` just removed.

**How.** After `T01` is green: emit side-cars, run `scripts/generate_eu_3d_viewers.py`, verify the
`docs/docs_ACTIVE/europeanLocations/outputs_3D/` mirror is byte-identical, and verify `sources.json` carries
the **current** sha256 of the manifest it read.

**How to test.** Assert one side-car per simulated building (expected 1,204); assert every side-car conserves
its declared dwelling total (`EU-13B` `T01`); assert no storey exceeds 8 dwellings; assert the pop-up header
and `has_unconditioned_core` agree.

### 3. `T03` — Carry the imputation tag into the layout, and report the cascade honestly

**What.** Every Bologna side-car must carry both provenance tags: `construction_period_provenance =
IMPUTED_CENSUS_SECTION_CONSTRUCTION_PERIOD` **and** its `dwelling_count_provenance` tier token.

**Why.** Bologna is the only district where *both* the construction period and the dwelling count are
imputed. A reader of a Bologna pop-up must be able to see that without opening a document.

**How.** Add the field to the side-car and surface both tags as badges in the pop-up, in the same visual
style already used for `DWELLING_LAYOUT_EMITTED (IMPUTED COUNT)`.

**How to test.** Assert 1,204 of 1,204 side-cars carry both fields non-empty; assert the badge text appears
in the generated viewer HTML for a sampled building.

### 4. `T04` — The 408, and the 16: measure, name, do not close

**What.** Produce a census, per reason token, of (a) the 408 buildings that reach no dwelling count even
after the four-tier cascade, and (b) the 16 excluded pre-run
(`CENSUS_SECTION_NO_RESIDENTIAL_BUILDINGS` 4, `CENSUS_SECTION_PERIOD_TIE_E8_E9` 10,
`CENSUS_SECTION_PERIOD_TIE_E9_E10` 2).

**Why.** These are the honest limits of the district and belong in the record, not in a footnote.

**How.** State for each group what datum is missing and what source, if any, could supply it. 🔴 **Do not
invent a dwelling count to move a building out of the 408.** A tie between two ISTAT bands is a real
ambiguity, not a rounding problem; propose no tie-break, and if you believe one is defensible, write it as a
recommendation for the owner and leave it unexecuted.

**How to test.** The counts in your census must reconcile exactly with `summary_prerun.json` and the
manifest's `geometry_outcome` histogram. Any discrepancy is a finding, not a rounding difference.

### 5. `T05` — `FINDING 199` diagnosis, plus resimulation (`D-EU-38`, unblocked `2026-08-30`)

`DR16`'s own recommended action for the INCOMPATIBLE (Too Low) range is to audit HVAC setpoint schedules,
internal gains and boundary surface types. That is a campaign-wide question — **all four districts sit at
55–79 kWh/m², below their own dossiers' bands** — and it is not Bologna's to answer alone. 🔴 **Do not tune
any input to move a figure into a band.**

**What.** After `T02`: rebuild Bologna's IDFs from the corrected layouts, submit the full resimulation to
Speed (`sbatch --array`, never the login node, never `srun`, `_ssh()` tcsh wrapper — same rules as `EU-13B`
`T09`), harvest, and recompute Bologna's pooled EUI under the new zoning. Report it beside 55.5346, stating
plainly whether the `FINDING 199` verdict moved. Regenerate
`docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_IT-BOL-GALVANI2_viewer.html` from the harvest and update
`RESULTS_EU-11.md`'s Bologna figure, disclosing `IMPUTED_CENSUS_SECTION_CONSTRUCTION_PERIOD` in the same
sentence. Report, and stop.

### 6. Deliverables

1. `openubem/outputs/eu_evidence/EU-14B/RESULTS_EU-14B.md` — the root cause from `T01` with its `file:line`;
   the coverage census from `T04`; the before/after pooled EUI from `T05`; and, wherever a Bologna figure
   appears, `IMPUTED_CENSUS_SECTION_CONSTRUCTION_PERIOD` in the same sentence.
2. Bologna side-cars, regenerated viewers, byte-identical `outputs_3D/` mirror.
3. One appended `walkthrough_progress_log.csv` row per task.
4. One `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` entry per solved error, house format, before
   closing — the manifest-corruption root cause from `T01` is mandatory there.

### 7. What must never happen

- Never run the side-car emitter against Bologna before `T01`'s safety test is green.
- Never drop the `IMPUTED_CENSUS_SECTION_CONSTRUCTION_PERIOD` tag from any Bologna figure, anywhere.
- Never merge Bologna into a pooled figure with Madrid / Lyon / London without stating the tag.
- Never set any Bologna figure beside the S0 archetype `it` = 108.25 kWh/m² ± 0.16 % — different perimeter,
  geometry, weather years and now an imputed period (`D-EU-31`, `FINDING 192`).
- Never `srun`, never compute on the login node — `T05`'s resimulation is `sbatch --array` only.

### 8. Stop-and-report points

1. After `T01` — report the root cause and the safety test result **before** touching the real manifest.
2. After `T04` — report, then continue to `T05` (resimulation unblocked `2026-08-30`, `D-EU-38`).
3. After `T05` harvests — report the resimulated pooled EUI beside 55.5346 and the `FINDING 199` verdict,
   then **stop**.
