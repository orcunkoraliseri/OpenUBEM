# MEASUREMENT — OPEN-58: blast radius (independent re-derivation)

> T03 of `implemenation/PLAN_twenty-items-2026-08-19.md`. Script:
> `scripts/analysis/open58_run_ep_enumeration_2026-08-19.py`. Output:
> `openubem/outputs/comparisons/open58_run_ep_consumers.csv`.

## Premise check — the plan's premise is FALSE at HEAD, quoted per hard rule 1

T03's **What** states: *"OPEN-58's size is recorded as 'unknown — every local batch result that
imported `run_ep()`'. Enumerate them."* **That is stale.** The register's own `### OPEN-58`
§-section (`INVESTIGATION_open-items-register.md:7713-7760`) already carries:

> *"✅ BLAST RADIUS MEASURED — 2026-08-19, T06–T08 of
> `implemenation/previous/PLAN_open-57-and-58_2026-08-19.md`. Record:
> `extra/MEASUREMENT_open-58_blast-radius.md`; artifact table
> `openubem/outputs/comparisons/open58_blast_radius_artifacts.csv` (6 rows)."*

Both cited files exist on disk and were verified present before this task started:
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-58_blast-radius.md` and
`openubem/outputs/comparisons/open58_blast_radius_artifacts.csv`. The "unknown" quoted in T03's
**What** is the state OPEN-58 was opened with, not its state at HEAD. Per rule 11 ("re-derive
rather than quote"), the right response is not to trust either the stale premise or the existing
measurement's own numbers — it is to **independently re-derive the enumeration from source** and
check whether it agrees. That is what follows.

## Independent re-derivation

Method (deliberately different from whatever method produced the existing artifact, so the two are
not the same measurement twice): walk every `.py` file under `scripts/` on disk (**not** `git grep`
— the existing record notes the origin file and its importers are **untracked**, so a
tracked-files-only search would silently undercount; confirmed by testing `git grep -l run_ep`
first, which found only the 5 files that happen to be tracked and missed the 3 untracked real
importers). For each of the 8 files that mention `run_ep` anywhere, classify as **real importer**
(imports a name from `open56_zone_volume_experiment.py`), **name-collision** (defines its own
`run_ep`/`_run_ep` and imports nothing from the origin file), or the **origin** file itself.

| file | classification | names imported from `open56_zone_volume_experiment` |
|---|---|---|
| `scripts/analysis/open56_zone_volume_experiment.py` | origin (defines `run_ep`, `read_run`) | — |
| `scripts/analysis/open56_fleet_cost_stratified.py` | **real importer** | `BASE, RESULTS, assert_one_field_diff, epw_for, read_run, run_ep, write_treated` |
| `scripts/analysis/open56_fleet_cost_repair.py` | **real importer** | `epw_for, read_run, run_ep` |
| `scripts/analysis/open35_storey_intervention_2026-08-19.py` | **real importer** | `_split_objects, _fields, _verts, read_run` (imports `read_run`, not `run_ep`; the file defines its own `run_ep_isolated` and aliases `run_ep = run_ep_isolated` at line 113, confirmed by direct read) |
| `scripts/analysis/a3_measure_band_deletion.py` | name-collision (own `def run_ep` at `:93`) | — |
| `scripts/diagnostics/t01_reproduce_degenerate.py` | name-collision (own `def run_ep` at `:73`) | — |
| `scripts/diagnostics/t04_validate_way428643335.py` | name-collision (own `def _run_ep` at `:82`) | — |
| `scripts/diagnostics/t06_validate_relation6374725.py` | name-collision (own `def _run_ep` at `:83`) | — |

**Result: 3 real importers, 4 name-collisions, 1 origin — 8 files touched in total.** This
independently reproduces the existing artifact's headline count ("Three real importers, not four
or seven") using a different search method (disk walk vs. whatever the prior pass used) and a
different classification script written from scratch for this task.

### Why `open35_storey_intervention_2026-08-19.py` counts as exposed despite not importing `run_ep`

It imports `read_run` (`open56_zone_volume_experiment.py:160-188`), which is where **defect (b)**
lives: `rec["eui_kwh_m2"] = rec["site_energy_gj"] * 277.7778 / rec["floor_area_m2"]` (`:187`) — Total
Site Energy ÷ Total Building Area, not production's per-end-use sum over the multiplier-aware
`.eio` area (`openubem/results/parser.py`). Importing `read_run` alone is enough exposure to defect
(b) even though the same file's local `run_ep = run_ep_isolated` alias (`:113`, overriding the
risky shared-cwd `run_ep` at `open56_zone_volume_experiment.py:150`) makes it immune to defect (a).
Confirmed directly by reading both files; not inferred.

## How-to-test: the required control (T04's `_results_v2.csv` must independently verify as clean)

The plan requires reaching, independently, the same verdict the existing record reached for
`open35_storey_intervention_results_v2.csv` — that it is **not** affected by either defect. Rather
than reproduce the prior pass's method (hashing `.sql` files and cross-checking zone-key `osm_id`),
a different, independent check was used: **a byte-identical-row test**, the same logic that first
surfaced OPEN-58's contamination defect (two different buildings cannot legitimately produce
identical numeric output).

```
n rows: 21, n unique osm_id_key: 21
duplicated numeric *_base columns across different osm_id_key: 0
duplicated numeric *_treat columns across different osm_id_key: 0
```

**Zero duplicated rows across 21 distinct buildings, both arms.** No contamination signature.
**Verdict reached independently: `_results_v2.csv` is unaffected — the same verdict the existing
record reports**, reached by a different check. The control passes.

## What this task adds beyond the stale premise

Nothing about the blast radius's *size* is new — 3 real importers / 4 collisions / 1 origin
reproduces exactly. What this task adds: (1) an independent confirmation, by a second method, that
the count is not an artifact of the first pass's search technique (git-tracked-only search would
have undercounted to 5 files and misclassified `open56_fleet_cost_stratified.py`'s multi-line
import — a fragile-regex trap that this script's second version had to fix, worth naming as a
reminder that "import list" parsing over real Python source is easy to get subtly wrong); (2) an
independent verdict on `open35_storey_intervention_results_v2.csv` by a different check than the
one already on record.

**No recommendation beyond what the register already carries** (four director-recommended
corrections, listed at `INVESTIGATION_open-items-register.md:7757-7760`, none of which this task
is positioned to add to or subtract from). This task does not open, close, strike, or retire
OPEN-58.

## Output

This document; `openubem/outputs/comparisons/open58_run_ep_consumers.csv` (8 rows).
