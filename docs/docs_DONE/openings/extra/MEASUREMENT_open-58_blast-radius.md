# MEASUREMENT — OPEN-58 blast-radius audit

**Date:** 2026-08-19. **Plan:** `implemenation/previous/PLAN_open-57-and-58_2026-08-19.md`, T06-T08.
**Scope:** who imports `run_ep`/`read_run` from `scripts/analysis/open56_zone_volume_experiment.py`,
which of the two OPEN-58 defects each is exposed to, which published artifacts descend from them,
and whether the exposure actually corrupted anything that is cited. Audit only — no fix applied,
per §4.8.

## Headline

**3 scripts import the helper for real** (2 exposed to both defects, 1 to defect (b) only).
**6 artifacts descend from them.** **1 row, in 1 artifact, is confirmed corrupted by defect (a)** —
and it was already excluded from every pooled figure that cites that artifact, though the register's
stated reason for excluding it was wrong. **Every pooled/relative figure this audit could check
against production's own EUI formula reproduces within noise of the cited number.** No published
figure needs restating. One register correction is recommended (below), and one code-comment
correction to the OPEN-58 defect (a) mechanism itself.

## T06 — the import census

Grep at HEAD for `open56_zone_volume_experiment` outside its own file, cross-checked against `def
run_ep`/`def read_run` for name collisions:

| script | imports | real import? |
|---|---|---|
| `scripts/analysis/open56_fleet_cost_stratified.py:37-38` | `read_run, run_ep, epw_for, BASE, RESULTS, assert_one_field_diff, write_treated` | yes — calls `run_ep` at `:111-112`, `read_run` at `:113` |
| `scripts/analysis/open56_fleet_cost_repair.py:24` | `epw_for, read_run, run_ep` | yes — calls `run_ep` at `:38`, `read_run` at `:39` |
| `scripts/analysis/open35_storey_intervention_2026-08-19.py:89` | `_split_objects, _fields, _verts, read_run` | yes, `read_run` only — `run_ep` is deliberately **not** imported; the script defines its own `run_ep_isolated` (`:82-95`) and rebinds `run_ep = run_ep_isolated` (`:98`) |
| `scripts/analysis/open35_storey_intervention_reparse.py` | — | no import at all; imports `openubem.results.parser.parse_building` instead (`:26`) |
| `scripts/analysis/a3_measure_band_deletion.py:93` | — | no, own local `def run_ep(idf_obj, run_dir, epw_path)` |
| `scripts/diagnostics/t01_reproduce_degenerate.py:73` | — | no, own local `def run_ep(idf_path)` |
| `scripts/diagnostics/t04_validate_way428643335.py:82` | — | no, own local `def _run_ep(idf_path)` (leading underscore — not even a name collision) |
| `scripts/diagnostics/t06_validate_relation6374725.py:83` | — | no, own local `def _run_ep(idf_path)` |
| `scripts/analysis/open56_denominator_census_2026-08-19.py` | — | no import of either symbol at all; unrelated script, excluded |

**§5.8's table (the plan's own starting inventory) is confirmed correct on which scripts import
what**, with one correction below.

**git history gives no window.** `git log --diff-filter=A --follow` on
`open56_zone_volume_experiment.py` returns nothing, and `git status --porcelain` shows the file (and
every one of its importers: `open56_fleet_cost_repair.py`, `open56_fleet_cost_stratified.py`,
`open35_storey_intervention_2026-08-19.py`, `open35_storey_intervention_reparse.py`) as untracked
(`??`). **None of these files has ever been committed** — there is no "window in which the defect
could have been inherited" to bound by history, because there is no history. Everything relevant is
working-tree-only, all dated 2026-08-18/19.

### Correction to §5.7/§5.8's framing of defect (a)

The plan's own citation (§5.7) frames defect (a) as buildings that **share a `-d` output directory**.
Checked directly: every one of `open56_zone_volume_experiment.py`'s own `main()`, `open56_fleet_cost_
stratified.py`'s `_one()`, and `open56_fleet_cost_repair.py`'s loop passes a **per-building-unique**
`-d outdir` (`WORK / f"{cell}__{stem}" / f"{arm}_out"`). No two buildings ever share an `outdir`
literally. Taken at face value, none of the three would be "exposed."

That is not what actually happens, and `open35_storey_intervention_2026-08-19.py`'s own code comment
(`:82-91`) already says why, discovered live while building OPEN-35's isolated remedy: EnergyPlus's
`-x`/ExpandObjects preprocessing step consults an intermediate file **relative to the process's
current working directory**, not to `-d`'s outdir — and that cwd is the **same for every invocation
in a script's lifetime** unless `cwd=` is passed to `subprocess.run` (none of the three do). The
comment records two invocations, **run minutes apart, not a race**, producing byte-identical
`eplusout.sql` for two different buildings. "Minutes apart, not a race" means **serial execution
does not protect against this** — only per-call `cwd=outdir` does (`run_ep_isolated`, which is what
`open35_storey_intervention_2026-08-19.py` uses instead of the shared `run_ep`).

Practical effect: **all three real importers of the shared `run_ep` are exposed to defect (a)** —
including `open56_fleet_cost_repair.py`, which re-runs its subset **serially**, and including
`open56_zone_volume_experiment.py`'s own 16-building `main()`, also serial. Concurrency
(`open56_fleet_cost_stratified.py`'s 6-worker `ThreadPoolExecutor`) is not required for exposure and
is not the distinguishing factor — sharing an un-isolated process cwd across more than one
EnergyPlus invocation is. Recommend the register's OPEN-58 section be updated to say "sharing a
process working directory across more than one invocation," not "sharing a working directory" read
as the `-d` outdir, to prevent a future reader concluding a per-building `-d outdir` is sufficient
protection — it is not, `cwd=` is.

## T07 — which artifacts descend from them, and are any actually corrupted

Full table: `openubem/outputs/comparisons/open58_blast_radius_artifacts.csv` (6 rows). Method for
each: hash every surviving `eplusout.sql` under the two OPEN-56 work directories
(`%TEMP%/open56_zone_volume`, `%TEMP%/open56_fleet_cost` — both fully survive on disk, 32 and 141
`.sql` files respectively; the fleet-cost directory's 141st file is a `retry_base/` hand-check for
`nyc_centre/relation_11171793`, matching `open56_fleet_cost_repair.py`'s own docstring account of a
manual pre-check — not a third `base_out`/`treat_out` pair, and not counted among the 140 arm-cells) and look for byte-identical files across different building roots (the
literal contamination signature); then, wherever a `.sql` survives, recompute EUI with production's
`parse_building()` (§4.9) and diff it against the artifact's own ad hoc reading. Recompute detail:
`scratchpad/open58_eui_recompute.csv`, `scratchpad/open58_sql_hash_census.csv` (throwaway working
files, not part of the plan's file layout, kept only as this audit's evidence trail).

**Defect (a), direct test.** MD5 hashing found no byte-identical `.sql` pair (EnergyPlus stamps
run metadata into the file even when the physics is a copy, so identical simulated content does not
guarantee an identical hash). The stronger test is production's own `parse_building()`, which raises
a hard `RuntimeError` ("I2 breach: foreign osm_id") when a `.sql`'s zone names do not match the
osm_id it is being read for. **Exactly one of 165 recomputed arm-rows raised it**:
`open56_fleet_cost_stratified.csv`'s `nyc_centre/relation_3566904` **base** arm — its zone keys read
`RELATION/11171793_F0_WHOLE`. Cross-checked directly against the CSV itself: `relation_3566904`'s
`base_floor_area_m2` (157,115.48), `base_site_energy_gj` (150,207.12) and `base_eui_kwh_m2`
(265.563924) are **exact, to-the-last-decimal matches** of `relation_11171793`'s own base-arm row in
the same file. **This is defect (a) manifesting for real** — the base arm's output for one building
is another building's completed run, not "exposure" in the abstract.

This is not a new discovery of the underlying fact: the register (`extra/MEASUREMENT_ten-items-
2026-08-18-overnight.md`, X01 side-finding) already flagged this exact row and excluded it from the
pooled cost statistic. **What is new is the mechanism.** The register's stated reason was "the same
broken geometry that stubs the volume also mis-reports the area" (`157,115 m² → 37,551 m²`, treated
against baseline) — an OPEN-56 geometry hypothesis. The real reason is defect (a): the row's *base*
arm is not this building's own baseline at all. **Recommend:** correct the register's stated
explanation for this row from "geometry mis-reports area" to "defect (a) cross-contamination";
the exclusion action itself was already correct and needs no change.

No other row, in either artifact, raised the I2 check: **166 arm-rows were attempted in total**
(26 from `open56_zone_volume_experiment.csv`, 140 from `open56_fleet_cost_stratified.csv`); **165
parsed clean against their own claimed osm_id, exactly 1 raised the breach.**

**Defect (b), direct test.** Absolute EUI from `parse_building()` differs from the ad hoc
`Total Site Energy ÷ Total Building Area` read by **-0.4% to -24.0% per arm** across the 165 clean
rows (median **-1.4%**, mean **-4.5%**, driven by a long tail — 28/165 rows differ by more than 5%).
Floor area between the two reads is identical to the reported decimal in every one of those
outliers (checked explicitly — not a multiplier/area artifact), so the gap is entirely on the energy
side: production sums per-end-use meters and **deliberately excludes `fans_eui_kwh_m2`**
(§5.6/manager decision, CP-4) from `total_eui_kwh_m2`, while the ad hoc read's `Total Site Energy`
includes everything. Buildings with a larger fan-energy share show the largest gap.

**But every cited figure is a *relative* (base-vs-treat) comparison on the *same* building**, and
the per-building formula bias mostly cancels in that ratio:

- `open56_zone_volume_experiment.csv` (10 successful buildings, the source of the checklist's
  "+0.75% average, +0.67% typical, +1.67% worst case"): ad hoc mean/median = **0.7520% / 0.6667%**
  (matches the cited figures exactly); recomputed with production's formula = **0.7739% / 0.6847%**,
  same sign on 10/10, worst case 1.6920% (production) vs 1.6683% (ad hoc, cited as "+1.67%").
- `open56_fleet_cost_stratified.csv` (70 buildings, less the one confirmed-contaminated row): ad hoc
  pooled mean/median **including** the contaminated row = 0.2852% / 0.8422% (dragged down by its
  -47.8% artifact); **excluding** it = 0.9826% / 0.8433% — this matches the register's own
  post-exclusion figure ("+0.98% / +0.84%") to two decimals, confirming the exclusion is already in
  the numbers the register cites. Recomputed with production's formula (the contaminated row cannot
  be parsed at all, so it is necessarily excluded) = **1.0165% / 0.8584%**. Same-sign fraction is
  identical either way, **65/69**.

**No cited figure moves outside its own already-stated uncertainty.** The direction, the rough
magnitude, and the same-sign fraction are unchanged by using production's own formula in place of
the ad hoc one.

`open35_storey_intervention_results.csv` was already found, corrected, and superseded **by the task
itself**, not by this audit — a systematic +15% to +37% gap (a different population, different
archetype mix, so a different magnitude than the OPEN-56 samples above is expected and is not a
contradiction), fixed by `open35_storey_intervention_reparse.py` re-parsing the same completed `.sql`
files with `parse_building()` directly, emitting `open35_storey_intervention_results_v2.csv`. This
audit did not re-derive that finding; it is restated in the artifact table with its existing
citation for completeness, since T07 asked for every descended artifact, not only the unresolved
ones.

`open35_storey_intervention_results_v2.csv`, `_census.csv` and `_prep.csv` are not exposed to
either defect — the first calls `parse_building()` directly with no re-simulation, the second never
invokes EnergyPlus, and the third is IDF-build metadata with no EUI or energy column at all.

## Verdicts (per §T07's "How to test")

| verdict | count | which |
|---|---|---|
| sound | 5 | `open56_zone_volume_experiment.csv` (defect exposure confirmed, no contamination found, cited pct-change figures reproduce); `open35_storey_intervention_results_v2.csv`; `_census.csv`; `_prep.csv` |
| unsound (one row) | 1 | `open56_fleet_cost_stratified.csv` — `nyc_centre/relation_3566904` base arm is confirmed cross-contaminated; the pooled/cited figures built from this file are unaffected because that row was already excluded, but the file **as a whole** carries one bad row un-annotated as such |
| superseded | 1 | `open35_storey_intervention_results.csv` — already resolved in-arc by `_results_v2.csv` |
| unverifiable | 0 | none — every candidate artifact had either a surviving `.sql` or no EnergyPlus output to begin with |

**Zero artifacts are "none unsound"** — stated plainly per T08's instruction, because it would be
the wrong claim: one row, in one file, is confirmed unsound. But zero **cited, published figures**
are unsound; all of them were already computed with that row excluded, for a reason that (it turns
out) was right in effect and wrong in its stated cause.

## Recommendations to the director (record only — not acted on, per §4.8)

1. **Correct the register's OPEN-58 section and its X01 side-finding note**: `nyc_centre/
   relation_3566904`'s base-arm anomaly is defect (a) cross-contamination (confirmed: its base-arm
   floor area, site energy, and EUI are exact matches to `relation_11171793`'s own base-arm row),
   not a geometry/area-reporting artifact. No number changes; only the stated cause.
2. **Correct §5.7-style language ("shared working directory")** wherever it appears, including in
   the register's OPEN-58 section, to specify **shared process `cwd` across more than one EnergyPlus
   invocation** — a per-building `-d outdir` (which all three scripts already use) does **not**
   protect against this; only per-call `cwd=` does, as `open35_storey_intervention_2026-08-19.py`'s
   `run_ep_isolated` already does.
3. **`open56_fleet_cost_stratified.csv` itself is not annotated** with which row is contaminated.
   Recommend either a follow-up pass that drops/flags the `nyc_centre/relation_3566904` base-arm row
   in the file itself, or a durable note pointing future readers of the raw CSV (not just the
   register's narrative) at the exclusion. This plan does not do that (§4.8: no published CSV may be
   edited by this pass).
4. No remedy is recommended for defect (a) or (b) in `open56_zone_volume_experiment.py` itself —
   out of scope for this audit and already covered by OPEN-58's own registration.

## Evidence

- `openubem/outputs/comparisons/open58_blast_radius_artifacts.csv` — the T07 table (6 rows).
- `scratchpad/open58_blast_radius_audit.py` — the read-only script that hashed every `.sql` and
  drove the `parse_building()` recompute (not part of the plan's file layout; throwaway, kept for
  provenance).
- `scratchpad/open58_sql_hash_census.csv` — 173 rows, one per surviving `eplusout.sql`, path/size/md5.
- `scratchpad/open58_eui_recompute.csv` — 166 rows, one per recomputed arm-cell, ad hoc EUI vs
  production EUI vs parse status.
