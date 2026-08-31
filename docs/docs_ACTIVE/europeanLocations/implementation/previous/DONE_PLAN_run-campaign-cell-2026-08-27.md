# PLAN — `run_campaign_cell`, the per-cell entry point for the 510 EU campaign cells

**Slug:** `run-campaign-cell` · **Date:** 2026-08-27 · **Arc:** European locations × Step 8
**DESIGN pointers:** `MVP_european_locations.md` §9.4 (campaign boundary), §9.5 (presence-series record), §9.6
**Correspondence that fixes the contract:** `messages_GSSCanada/2026-08-27_4J_to_OpenUBEM_presence_binding_ruled_and_delivered.md` · `…_v1-1_repin_issued_and_binding_verified.md` · `…_c19_prose_closed_and_binding_v2_verified.md`

---

## 1. What this is, in one paragraph

§9.4 makes GSSCanada 4J's `EU-08` **the loop** and OpenUBEM **the engine**. 4J will not reach inside
OpenUBEM to build IDFs; OpenUBEM will not decide which cells run. So OpenUBEM must export exactly one
callable that takes **one cell of the frozen spec** and returns **one proven result**. That callable is
`run_campaign_cell`. It is the last OpenUBEM-side item before the 408 `f > 0` cells can execute.

---

## 2. Hard rules for the executor

1. **Never amend a frozen spec.** `eu_campaign_cell_spec_v1.1.json` (sha256 `16d3fbd6…`) is
   `FROZEN_PINNED`. The function **reads** it and **verifies its digest**; it never writes to it.
2. **`schedule_status` is not the authority on the `f > 0` lift.** All 408 rows read
   `BLOCKED_CHAINING_RULE` in `v1.1` exactly as in `v1.0`, and always will. The lift is carried **by the
   identity of the 10.1 notice**, never by a boolean. A runner that refuses a cell on that frozen field
   is reading the wrong authority.
3. **Presence series come from the binding artefact**, `eu_cell_presence_binding_v2.json`, with its
   `presence_sha256`. **Never re-derive the sort order**, even though the rule is documented and
   reproducible — a re-derivation that silently drifts is undetectable downstream.
4. **The binding carries no occupant semantics.** It is arbitrary-but-fixed, never stratum-matched,
   never representative. No output of this function may be phrased as if it were.
5. **`diary_origin_hour = 4` and `rotated_to_midnight = true` are one composed sentence** (`FINDING 141`,
   `D-S9-3`). Never record or read either flag alone.
6. **No new physics.** Every construction, control, mass and geometry call already exists and is used by
   `run_eu_s2_campaign.py` / `run_eu_s3_campaign.py`. This task **extracts and parameterises**; it does
   not invent a model.
7. **No compute in this task.** `dry_run=True` paths and unit tests only. Running the 510 is a separate,
   separately authorised step.
8. Do not touch root `main.py`, OVERVIEW or DESIGN docs. No `.py` under `docs/`.

---

## 3. File layout

| file | action |
|---|---|
| `openubem/campaign/eu_cell_runner.py` | **new** — the entry point and its helpers |
| `openubem/campaign/__init__.py` | **new if absent** — package marker only |
| `tests/test_eu_cell_runner.py` | **new** — the tests named in §6 |
| `scripts/run_eu_s2_campaign.py`, `scripts/run_eu_s3_campaign.py` | **read-only** — sources of the extracted logic; do **not** refactor them in this task |
| `openubem/data/campaign/eu_campaign_cell_spec_v1.1.json` | read-only |
| `openubem/data/campaign/eu_campaign_cell_spec_v1.1_addendum_prose_corrections.json` | read-only |

⚪ The two campaign scripts stay as they are. Converging them onto the new entry point is a **later**,
separate task: they produced promoted artefacts whose `idf_sha256` must not move.

---

## 4. Dependency decisions (pinned)

| item | pinned value |
|---|---|
| spec | `openubem/data/campaign/eu_campaign_cell_spec_v1.1.json`, sha256 `16d3fbd62a9f79265c08c5746bbc70f5130cd30cb673c1a68c74755c79aa65f6` |
| spec addendum (prose only) | `…_v1.1_addendum_prose_corrections.json`, sha256 `882ccf62e6e62e844931b0a5e3f3a8a39e5c1386a5f44356417f586527b07692` |
| binding | `4J_docs_occ/Step10_docs/outputs_step10/eu_cell_presence_binding_v2.json`, sha256 `8f94165dab807c5a…` |
| `f > 0` lift notice | `4J_docs_occ/Step10_docs/docs/2026-08-26_10.1_chaining-closure-notice.md` |
| chaining rule string | taken **from the notice**, not hard-coded in the module |
| EnergyPlus | 23.1 via `openubem.config.ENERGYPLUS_PATH` / `ENERGYPLUS_IDD_PATH` |
| gain emitter | `openubem.semantic.european_schedules.emit_step8_gain_schedule` — unchanged |

---

## 5. DESIGN and code facts, with citations

- `build_step8_gain_series` implements `phi_int(t) = 3.0 · ((1 − f) + f · g(t)/mean(g))`, asserts annual
  conservation, and rejects any presence array not of shape `(8760,)` —
  `openubem/semantic/european_schedules.py:22-62`.
- The `f > 0` gate is a **string** gate: `if not chaining_rule or not chaining_rule.strip(): raise` —
  `openubem/semantic/european_schedules.py:51-52`.
- `emit_step8_gain_schedule(idf, *, sensitivity_f, dwelling_zone, dwelling_id, emitted_csv_path,
  presence=None, chaining_rule=None)` — `openubem/semantic/european_schedules.py:88-97`. It **never**
  creates a `People` object; the series is an internal-gain signal, not an occupancy fraction (`:100-102`).
- Callers **must remove the legacy `OtherEquipment` gain** that `add_european_heating_controls` installs,
  before adding the external-file replacement, or TABULA's `phi_int` is double-counted —
  `scripts/run_eu_s2_campaign.py:255-259`.
- `emit_step8_gain_schedule` re-creates a fixed-name `ScheduleTypeLimits` on **every** call, so across
  multiple dwelling zones in one IDF the prior copy must be dropped immediately before each call or
  EnergyPlus fails input processing — `scripts/run_eu_s2_campaign.py:260-266`.
- Zone volumes must be written explicitly after extrusion (`write_zone_volumes`), and footprints oriented
  counter-clockwise, or the two defects `C-20` (57.74× ventilation understatement) and `C-21` (11.8 % on
  vertex order alone) reappear — `scripts/run_eu_s2_campaign.py:227-228`, `:154-160`.
- Heating is read from the **hourly `Zone Ideal Loads Zone Total Heating Energy` variable**, never from a
  meter — `scripts/run_eu_s2_campaign.py:285-302`. **No saved EU IDF carries any `Output:Meter`**; that is
  known, systemic and deliberately deferred. Do not add one here: it would move every promoted `idf_sha256`.

---

## 6. Tasks

### T01 — the module skeleton and the frozen signature

**What.** Create `openubem/campaign/eu_cell_runner.py` exporting exactly:

```python
def run_campaign_cell(
    cell: Mapping[str, object],
    *,
    spec_path: Path,
    spec_sha256: str,
    binding_path: Path,
    chaining_notice_path: Path,
    run_root: Path,
    dry_run: bool = False,
    energyplus_timeout: int = 600,
) -> dict[str, object]:
```

**Why.** 4J calls this once per cell in whatever order and concurrency `EU-08` chooses. Every input that
determines the result is an explicit argument, so a run is reproducible from its own manifest alone; no
module-level default may silently supply a spec, a binding or a notice.

**How.** Signature and docstring only in T01; body raises `NotImplementedError`. State in the docstring
that `cell` is one element of the spec's `cells` array, passed **verbatim**, and that the caller is
responsible for iteration, ordering and concurrency.

**How to test.** `inspect.signature` matches the above exactly, all keyword-only after `cell`.

### T02 — provenance verification, before any work

**What.** Verify, and refuse loudly on any mismatch: `sha256(spec_path) == spec_sha256`; `cell` is present
in that spec, matched on `cell_id`, and **field-for-field identical** to the spec's copy; the binding
artefact's `spec.sha256` equals `spec_sha256` **or** the binding declares `binding_invariance` (in which
case a weather-only revision is accepted and the acceptance is recorded in the manifest); the EPW at
`cell['epw_path']` exists and hashes to `cell['weather_sha256']`.

**Why.** Every one of these has already failed once in this arc or its neighbours. The digest check is
what makes a completed run provable rather than merely finished.

**How to test.** One test per refusal: wrong spec digest, cell not in spec, cell mutated in one field,
EPW digest mismatch. Each raises with the offending value in the message.

### T03 — the `f > 0` lift, by notice identity

**What.** Read the chaining rule string and the notice's identity (path + sha256 + the rule text it names)
from `chaining_notice_path`. Pass the rule to `emit_step8_gain_schedule`. **Ignore `cell['schedule_status']`
entirely** for the gating decision, and record in the manifest that it was ignored and what it said.

**Why.** Hard rule 2. The frozen field is permanently stale by construction; a boolean read of it would
refuse all 408 cells forever.

**How to test.** A cell with `schedule_status == 'BLOCKED_CHAINING_RULE'` and `sensitivity_f == 0.15`
proceeds; the manifest records `schedule_status_frozen_value` and `lift_authority`. A missing or empty
notice raises before any IDF is built.

### T04 — presence lookup from the binding artefact

**What.** For `f > 0`, look up `(cell['survey_fold'], cell['archetype_id'])` in the binding's
`folds[fold]['binding']`, take `presence_csv` and `presence_sha256`, verify the file against that digest,
read it with `read_presence_csv`, and assert `shape == (8760,)`. For `f == 0`, pass `presence=None` and
record `presence_source = 'not_required_f0'`.

**Why.** Hard rule 3. The mapping is ruled (`D-S10-8`) and must be **read**, never recomputed.

**How to test.** A known `(fold, archetype_id)` returns the expected `hid` and digest; an unknown pair
raises; a digest mismatch raises; an 8,759-row CSV raises before emission.

### T05 — build, run, and the per-cell manifest

**What.** Assemble the IDF exactly as `run_eu_s2_campaign.build_idf_for_building` does — extrusion,
counter-clockwise footprints, `write_zone_volumes`, TABULA constructions, internal mass, sizing, heating
controls, legacy gain removed, `ScheduleTypeLimits` de-duplicated per zone, the hourly ideal-loads output
variable, `Output:SQLite`. Run EnergyPlus unless `dry_run`. Write the manifest to `cell['manifest_path']`
and return it.

**Manifest fields — required, and this list is the contract 4J will read:**

```
cell_id, archetype_id, survey_fold, sensitivity_f, control_cell_id, country_stock_code
spec_path, spec_sha256, spec_schema_version
binding_path, binding_sha256, binding_ruling            # "D-S10-8, ruled 2026-08-27"
presence_csv, presence_sha256, presence_hid, presence_source, presence_n_hours
diary_origin_hour, rotated_to_midnight                  # written and read together, never apart
chaining_rule, lift_authority                           # notice path + sha256 + its rule text
schedule_status_frozen_value, schedule_status_ignored   # true, with the reason
epw_path, weather_sha256, weather_id, weather_status
idf_path, idf_sha256, gain_csv_path, gain_csv_sha256
energyplus_version, return_code, severe_count, fatal_count, runtime_s
heating_kwh, heating_source                             # "Zone Ideal Loads Zone Total Heating Energy, hourly variable"
occupant_semantics_warning                              # verbatim from the binding artefact
openubem_git_commit, created_utc
```

**Why.** 4J's stated requirement is that *a completed run can prove what it actually read*. Every digest
above exists so that proof does not depend on trusting the runner.

**How to test.** `dry_run=True` on one `f=0` and one `f>0` cell produces a manifest with **every** field
above non-null except the EnergyPlus result fields; `heating_source` is the variable string, never a meter;
`occupant_semantics_warning` is non-empty.

### T06 — the two refusals that must not become warnings

**What.** `run_campaign_cell` **raises** rather than degrades when: the presence series is missing or
mis-hashed, and when `sensitivity_f > 0` with no chaining rule available. Neither may be downgraded to a
logged warning or a null result row.

**Why.** Both defects are invisible in every aggregate — 8,760 rows are produced either way. The same class
as the calendar defect (`D-S10-7`) and the four-hour rotation (`D-S9-3`).

**How to test.** Both raise; neither writes a manifest.

---

## 7. Stop-and-report points

- **CP-1 — after T04.** Report the signature, the four refusals, and one real `(fold, archetype_id)`
  lookup. **The signature goes to 4J before T05 is written**, per the standing agreement.
- **CP-2 — after T06.** Report the two `dry_run` manifests in full and the suite result. **Do not run any
  cell for real; that authorisation is separate.**

---

## 8. Progress log

*(one entry per task: `#### TXX — <title> — completed YYYY-MM-DD`, then Artifacts / Deviations / Test status / Notes)*

#### T07 — first real execution: three defects repaired, one raised — completed 2026-08-28

**Artifacts.** `openubem/campaign/eu_cell_runner.py` (`_energyplus_exe`, `add_european_internal_mass`
call, `completed` / `completion_status`); `tests/test_eu_cell_runner.py` **30 passed**;
`docs/docs_ACTIVE/europeanLocations/debugs/docs/DONE-docs/DECISION_REQUEST_D-EU-26_s0_wall1_host_2026-08-28.md`;
two entries appended to `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`.

**Deviations.** CP-2 said *do not run any cell for real*. GSSCanada 4J ran the 510-cell campaign under
its own authorisation and reported four findings; this session ran **one cell, three times**, purely to
confirm the repair. No campaign was run here and no result was scored.

**Test status.** Targeted 54 passed; full suite re-run after the change.

**Notes.**
- 🔴 **The campaign was not reproducible, and the cause was in this file.** `_build_idf` never added
  the `InternalMass` object, so the `Material:NoMass` S0 envelope gave the zone **zero heat capacity**;
  EnergyPlus said so as a **Warning**, not a Severe, and the `dry_run` path never reaches it, so no
  test on either side could have caught it. Measured before: 130 of 510 cells changed status across
  three runs and 132 of the 264 always-completing cells returned a different value, worst case 27.1 %.
  After: `uk__GB.ENG.MFH.02.Gen.ReEx.001.001__f050` returns **76524.889 kWh three times identically**,
  0 severe, 0 fatal. **Every `idf_sha256` from the first campaign is superseded; no published figure
  moves, because nothing from it was scored.**
- 🔴 **Standing lesson:** `run_eu_s2_campaign.py:244` had carried the capacity all along. A new entry
  point that reuses a builder must also reuse everything the *existing* driver adds around it — the
  builder's own tests pass without it.
- `ENERGYPLUS_PATH` is the **install directory** everywhere else in the repo; this file was the sole
  outlier and was moved to the convention, not the other way round.
- ⚪ Three geometry warnings persist by design (`european_box.py:48-58`) and no longer cause drift.
- ⚠ **115 of 510 cells refuse deterministically**, 22 of the 23 archetypes on the `b=1` `Wall_1` host
  check — `uk` loses 17 of 36. Raised as `D-EU-26`, **RULED 2026-08-28 Option B — check retained, perimeter 395 of 510, `uk` never quoted at fold level**; `EU-09`/`EU-10` stay unscored on `FINDING 181`, not on this.

#### T08 — the second marker: `completed` is necessary and not sufficient — recorded 2026-08-28

**Artifacts.** `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` (`[OPEN]` entry); three-run
reproductions under the session scratchpad; no repository change beyond the T07 fixes.

**Deviations.** One geometry change was made and **reverted**: flipping the S0 floor normals to the
correct downward tilt. It cleared `GetVertices: Floor is upside down!` and **made the cell worse** —
`es__ES.ME.AB.01.Gen.ReEx.001.001__f000` went from three identical runs to 1 fatal in 3. Reverted with
`git checkout`, and the three identical runs were re-confirmed after the revert.

**Test status.** Suite unchanged at 2,341 passed / 55 skipped; nothing in this entry changes code.

**Notes.**
- 🔴 **After the `InternalMass` repair the campaign is still not reproducible.** 4J, three full runs:
  **333 / 346 / 348 completed**, of which **97 / 102 / 94 carry an instability marker**; 185 cells are
  clean in all three, **49 of those still differ (max 45.5 %)**, leaving **136 of 510 clean and
  bit-reproducible** and only **5 archetypes complete across all five `f` levels**.
- 🔴 **The `es` fold contributes zero** — every completed `es` cell in every run carries
  `Temperature out of range [-100. to 200.] (PsyPsatFnTemp)`. Madrid is unusable, not merely reduced.
- 🔴 **`completed: true` is necessary and NOT sufficient.** Screen `eplusout.err` for
  `PsyPsatFnTemp`, `did not converge`, and `CalcHeatBalanceInsideSurf`. **Count per archetype across
  all five `f` levels, never raw cells** — the sensitivity design compares `f` within an archetype.
- ⚠ **What is left is a property of the S0 equivalent-envelope method, not a defect in this file.**
  The zone is deliberately unenclosed, so `FixViewFactors: View factors not complete` is raised and the
  interior radiant exchange is ill-posed; the windows sit in hosts whose outside boundary is
  `OtherSideCoefficients`. **That is a DESIGN question and this session will not rule it.**

#### T09 — the signal is below the noise floor — recorded 2026-08-28

**Artifacts.** Debug-references `[OPEN]` entry extended; director prompt item 9. No code change.

**Test status.** Unchanged; nothing here touches code.

**Notes.**
- 🔴 **The `f` sweep moves heating by 0.11–0.39 %, against a 45.5 % run-to-run spread.** Measured by
  4J on the only five archetypes whose whole sweep is clean and bit-reproducible in all three runs
  (`it` 3, `uk` 2, `es` 0; all five `Gen.ReEx.001.001`). The effect is **not monotone** — two turn back
  up at `f100` — which at 0.1–0.4 % is what one expects of numerical residue rather than a signal.
- 🔴 **Consequence for `D-EU-26`: a ruling that only recovers refused cells cannot make `EU-09`
  scoreable while `FINDING 181` is open.** The two are not substitutes; the stability question is the
  binding one. This does not change what `D-EU-26` asks, but it changes what ruling it buys.
- ⚪ **Completeness histogram, useful as an ex-ante check on whichever option is taken:** of the 42
  archetypes with any reproducible cell, 5 have all five `f` levels, **16 have four**, 7 three, 12 two,
  2 one. Sixteen archetypes are one cell short — the cheapest place a partial fix would show up.
- ⚪ **Five archetypes is not a population and the pathway is heating-only**; nothing here is a finding
  about `f` itself, and no `f` result may be quoted from it.
