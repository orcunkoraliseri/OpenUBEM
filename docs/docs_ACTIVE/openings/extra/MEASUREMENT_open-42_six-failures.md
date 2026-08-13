# MEASUREMENT — OPEN-42 T07: why did the six simulations fail?

**Slug:** `rulings-and-five-items-2026-08-12`, T07. **No cluster used** (no `ssh`, `srun`, `sbatch`) —
every measurement below is local. **Foreground, sequential.**

---

## 1. The six, confirmed count = six, no more

From the adopted run's own
`docs/docs_VALIDATION/validations/overAll/results/phaseE_elevrb/<cell>/04_simulation_manifest.parquet`
(`la_rural`, `la_urban`; the twelve-cell manifest set has `success` for all other rows):

| osm_id | cell | manifest `status` | `05_results.csv` `simulation_status` | `n_severe` (manifest) | `n_warnings` |
|---|---|---|---|---|---|
| way/472960972 | la_rural | failed | not_simulated | 26 | 169 |
| way/472961034 | la_rural | failed | not_simulated | 7 | 240 |
| way/472961088 | la_rural | failed | not_simulated | 4 | 179 |
| way/472961091 | la_rural | failed | not_simulated | 12 | 169 |
| way/472961171 | la_rural | failed | not_simulated | 4 | 173 |
| way/402215469 | la_urban | failed | not_simulated | 24 | 1358 |

Five in `la_rural`, one in `la_urban`, exactly six — asserted in
`scripts/analysis/open42_six_failures.py` (`assert len(fail) == 6`), which raised nothing.

The `n_severe` column above **is** an adopted-run artifact even though the raw `.err` text is not: it
was computed by `v12_cell_pipeline.py::build_sim_manifest` (`:622-624`) from the `.err` file at run
time and persisted into the parquet manifest, which does survive.

---

## 2. Does the adopted run's own `eplusout.err` survive locally? No.

Searched, in order:

1. **The `phaseE_elevrb` tree itself** — `docs/docs_VALIDATION/.../phaseE_elevrb/<cell>/` has no
   per-building `sim_out/` subtree at all; only the aggregated `04_simulation_manifest.parquet` and
   `05_results.*`.
2. **The elevator-rebaseline temp work tree** the manifest's own `work_dir` column points at —
   `C:\Users\o_iseri\AppData\Local\Temp\ubem_elev_rebaseline\<cell>\sim_out\way_<id>\` for all six.
   **Every one of the six directories exists but is empty** (0 files) — confirmed by direct listing.
3. **The T17/T18/T19/T20 harvest caches** (`C:\Users\o_iseri\AppData\Local\Temp\ubem_t{17,18,19,20}_harvest\{la_rural,la_urban}_layout_assign\way_<id>\`) —
   all twenty directories (5 buildings × 4 harvests, plus la_urban's own four) exist but are **empty**.
4. **`cache/` at the repo root** — contains only OSM query JSON blobs (keyed by hash), nothing
   EnergyPlus-related.

**Conclusion for this leg: the adopted `phaseE_elevrb` run's own `.err`/`.end`/`.audit` files do not
survive locally for any of the six buildings.** Per the plan's rule, that is itself a correct and
complete result for *this specific run's own trace* — no hypothesis substitutes for it, and
`fatal_count`, `phase`, `zone`, `surface` are reported as **not recoverable from the adopted run** in
the CSV, not filled in with a guess.

---

## 3. Corroborating local evidence — clearly a different run, not the adopted one

Two *other* local sources hold real (not hypothesised) EnergyPlus `.err` output for the same six
`osm_id`s, produced under `resolution_mode="auto"` (the production pipeline's default — confirmed by
grep, `v12_cell_pipeline.py` never passes `resolution_mode="layout_assign"` for these buildings' path).
Neither is the adopted `phaseE_elevrb` run; both are reported here **only** as context for the cause
narrative, per the plan's "say what you did not do" rule, not as a stand-in measurement:

- An earlier Claude session's scratchpad (`...\3f48ae9f-.../scratchpad\r09_new\la_rural_auto\`) holds a
  full local re-simulation of all 149 `la_rural` buildings, dated 2026-08-09. It includes the five
  `la_rural` osm_ids.
- The E02 40,800-run harvest's own `la_urban_auto` cache
  (`C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest\la_urban_auto\way_402215469\`) holds the sixth
  (`la_urban`). **This is the E02 campaign** — per the plan's leg-5 warning, its *numbers* (areas,
  blast radius) must never be paired with the adopted run's own; here it is cited only for the
  building's `.err` text, the same caution the register itself applied when it retracted the
  area-pairing claim in OPEN-42.

Fatal marker checked with the required **two-space** form (`**  Fatal  **`), never `has_fatal`. All
six show it exactly once, all in `RUNPERIOD1` (not Warmup, not Sizing — read, not assumed, per the
plan's OPEN-07 caution):

| osm_id | source | severe count (this trace) | last severe error | zone | phase |
|---|---|---|---|---|---|
| way/472960972 | r09 scratchpad, auto | 24 | Temperature (low) out of bounds [-444.53], surface `…F2_PERIM3 ROOF` | `WAY/472960972_F2_CORE` | RUNPERIOD1 |
| way/472961034 | r09 scratchpad, auto | 8 | Temperature (low) out of bounds [-364.80] | `WAY/472961034_F2_CORE` | RUNPERIOD1 |
| way/472961088 | r09 scratchpad, auto | 10 | Temperature (low) out of bounds [-250.61] | `WAY/472961088_F2_CORE` | RUNPERIOD1 |
| way/472961091 | r09 scratchpad, auto | 10 | Temperature (low) out of bounds [-256.09] | `WAY/472961091_F2_CORE` | RUNPERIOD1 |
| way/472961171 | r09 scratchpad, auto | 10 | Temperature (low) out of bounds [-262.52] | `WAY/472961171_F2_CORE` | RUNPERIOD1 |
| way/402215469 | E02 harvest, `la_urban_auto` | 12 | Temperature (low) out of bounds [-256.14], surface `…WHOLE STOREY 3 FLOOR` | `WAY/402215469_F3_WHOLE` | RUNPERIOD1 |

None of these severe counts equal the adopted run's own `n_severe` (26/7/4/12/4/24) — expected, since
these are different runs (different date, different code snapshot at time of run). They are cited only
to establish the **failure mechanism**, not the adopted run's own numbers.

---

## 4. The mechanism, cross-checked against the project's own prior investigation

The register (`INVESTIGATION_open-items-register.md:2800-2803`, OPEN-11, confirmed 2026-08-06 N04,
director-verified) already identifies this **exact** six-`osm_id` set as *"the REPORT §7 limitation-#6
inverted-geometry buildings whose `10_fails_solution.md` remediation was not re-applied in the
automated run."*

`docs/docs_DONE/LOADS & SCHEDULES/hvac-ServiceLoads/debugs/DONE_10_fails_solution.md` §7A documents a
**two-stage** root cause for these same six buildings, found when they first failed in the original
(pre-elevator) Phase-E run:

1. **Stage 1 — inverted (CW) footprint winding → negative zone volume → EnergyPlus's `10 m³` clamp.**
   Fixed **permanently and fleet-wide**: `openubem/idf/builder.py` inserts
   `poly_local = orient(poly_local, sign=1.0)` before `build_zones` (committed T01, `10_fails_solution.md:479-483`).
   This explains why the corroborating traces above show **zero** `Zone Volume <= 0.0` / `upside down`
   warnings — that half is fixed.
2. **Stage 2 — the largest Warehouses' all-`MATERIAL:NOMASS` envelope has no thermal mass to damp
   solar gain on the top-floor zone → runaway surface temperature → `Temperature (...) out of bounds`
   Severe errors → Fatal.** Fixed **only** by an opt-in `thermal_mass=True` construction mode
   (`10_fails_solution.md` §7A.4, task T13) applied by a **standalone recovery script**,
   `scripts/validation/phaseE_recover_10.py`, for exactly these six buildings in the original Phase-E
   run (T06-R, `10_fails_solution.md:517-521`: *"all 6 Group-A buildings recovered to success"*).

**That standalone fix was never merged into the standard production pipeline.** Verified two ways:

- `grep -n "thermal_mass" scripts/validation/v12_cell_pipeline.py` → **zero matches**.
- `openubem/idf/builder.py:191-198` — `BuildingIDF.__init__` defaults
  `thermal_mass = (resolution_mode in ("layout_assign", "layout_assigner"))` when the caller does not
  pass it explicitly. `v12_cell_pipeline.py` never sets `resolution_mode="layout_assign"` for the
  `auto`/production path that built these six for `phaseE_elevrb`, so `thermal_mass` defaults `False`.

So when `phaseE_elevrb` (the elevator-loads rebaseline) regenerated these six buildings from scratch
through the standard pipeline, stage 1 stayed fixed (orient is a permanent code change) but **stage 2
recurred**, because the fix for it lived only in a one-off script that this run never called. This is
consistent with — not a re-derivation of — every corroborating trace above: 0 volume clamps, but a
Fatal from repeated top-zone temperature-out-of-bounds Severe errors during `RUNPERIOD1`.

**This is reported as corroborated context, not as the adopted run's own measured cause** — the
adopted run's own `.err` does not survive, per §2. What is measured directly from the adopted run is:
it failed (`status=failed`/`not_simulated`), its own persisted `n_severe` is 26/7/4/12/4/24, and no
`.err` file naming a specific line survives to confirm the *same* mechanism fired *in that exact run*.

---

## 5. Leg 4 — why is `error_summary` empty for all six (and, it turns out, fleet-wide)?

`scripts/validation/v12_cell_pipeline.py:625-626`, inside `build_sim_manifest`:

```python
severes = [l.strip() for l in etxt.splitlines() if "** Severe **" in l]
error_summary = severes[0] if severes else ""
```

The literal search string is `"** Severe **"` — **one space** before `Severe` and **one space**
after it. The real EnergyPlus `.err` format is **one space before, two spaces after**:
`"** Severe  ** Temperature (low) out of bounds..."` (confirmed byte-for-byte on a real `.err` line
with `cat -A`, and cross-checked in Python: `"** Severe **" in line` → `False`,
`"** Severe  **" in line` → `True`, on the same line).

**This is the same shape as the `has_fatal`/`**  Fatal  **` spacing bug the plan warns about (OPEN-29),
but on the `Severe` marker instead of `Fatal`, at a different line.** Because the substring never
matches, `severes` is always empty and `error_summary` is always `""` — **not just for these six, for
every failing building the pipeline has ever manifested**, since this is the only writer of that
column (`grep -rn "error_summary" scripts/validation/v12_cell_pipeline.py` shows one assignment site,
`:626`, one manifest write, `:639`, and one read site in a debug print, `:1035`). The `n_severe` count
(computed by a **separate**, correctly-matching regex at `:622`, `r"(\d+)\s+Warning;\s*(\d+)\s+Severe"`,
against the `.end`-style summary line) is unaffected and correct.

This is a defect in its own right, independent of what caused the six failures, exactly as the plan
anticipated.

---

## 6. What the CSV says

`openubem/outputs/comparisons/open42_six_failures.csv` — six rows, columns `stem, cell,
simulation_status, error_summary, err_file_found, severe_count, fatal_count, phase, zone, surface,
cause`. For all six: `err_file_found=False` (adopted run's own trace), `severe_count` is the adopted
run's persisted `n_severe`, `fatal_count`/`phase`/`zone`/`surface` are left blank (not recoverable from
the adopted run), and `cause` carries the full corroborated-context narrative from §4 plus the leg-4
citation. Produced by `scripts/analysis/open42_six_failures.py`, which asserts exactly six rows twice
(manifest read, output write) and exits 0.

---

## 7. Plain statement of what is and is not established

- **All six:** the adopted run's own `.err`/`.end` does **not** survive locally. That is a complete,
  correct result for this leg on its own terms — no hypothesis substitutes for it.
- **All six:** a plausible, well-evidenced, register-corroborated mechanism exists — stage-1 fixed
  fleet-wide (orient), stage-2 fix never wired into the production path that built `phaseE_elevrb` —
  but it is corroborated from *other* local runs of the same buildings, not measured from this run's
  own artifacts. The director should treat this as strong context, not as a closed cause-per-building.
- **All six:** `error_summary`'s emptiness is fully explained and cited — a one-space/two-space
  substring mismatch at `v12_cell_pipeline.py:625-626`, fleet-wide, independent of the six failures'
  own cause.
- **Not done:** no code was changed (the plan does not ask T07 to fix the spacing bug or wire the
  thermal-mass fallback into production — that is a separate decision).
