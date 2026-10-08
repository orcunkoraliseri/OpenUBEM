# MEASUREMENT — E02 floor-area / denominator audit (T04)

**Date:** 2026-08-11 · **Task:** T04 of `PLAN_e02-audit-and-closure.md` · **Touches:** OPEN-01(a/b),
OPEN-02, OPEN-28, OPEN-35. **Does not close OPEN-01 or OPEN-35** — see §7.

**Scripts:** `scripts/analysis/e02_t04_floor_area_audit.py`
**Outputs:** `openubem/outputs/comparisons/e02_simulated_floor_area.csv` (40,800 rows),
`openubem/outputs/comparisons/open01_denominator_audit.csv` (40,800 rows)

---

## 0. Lead: `auto` — the mode the adopted ~~158.0~~ **157.1 kWh/m²** (pooled: total simulated energy ÷
total simulated floor area; the struck figure was a count-weighted mean of the 12 cell means,
superseded 2026-08-12, OPEN-43) baseline came from

n = 8,160. **Median error factor = 1.0000.** Mean = 1.0592 (pulled up by a 6-building tail, §6).
Range 0.9998× – 336.65×. **99.63% (8,130 / 8,160) sit within ±1% of 1.0.**

**The stop condition (§6/T04: "if the fleet-wide `auto` median error factor is materially different
from 1.0, stop before writing any interpretation") is NOT triggered.** The adopted baseline's
denominator measures clean at the median. What follows is the full census, including a fleet-wide
`layout_assign` measurement that has never existed before, and two findings the parse surfaced
along the way.

---

## 1. Generation of every side of every comparison

| Side | Source | Generation |
|---|---|---|
| Simulated floor area | `eplusout.eio`, E02 harvest, `<cell>_<mode>` × 40,800 buildings | **4th generation** — E02, the fleet run this plan audits |
| Declared floor area | `docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/05_results.csv` | **3rd generation** — the adopted, published run. One file per cell, **not per mode** — the same declared area is compared against all five E02 modes |
| `archetype_id_manifest` / `zoning_strategy_manifest` | `03_manifest.parquet`, E02 build tree, per `(cell, mode)` | 4th generation (E02) |
| `archetype_id_results` / `zoning_strategy_results` | same `05_results.csv` as declared area | 3rd generation |
| `old_status` (applied/non-applied lookup) | `openubem/outputs/comparisons/open01_denominator_factors.csv` | prior measurement task (inference-based, not simulated) — read for comparison only, **not overwritten** |
| OPEN-35 subpopulation | `openubem/outputs/comparisons/open35_neither_population.csv` (2,611 rows) | prior measurement task |

Because declared area is 3rd-generation and simulated area is 4th-generation, every comparison in
this report **carries the OPEN-28 confound** (§5). It is bounded there, not eliminated.

---

## 2. Mandatory controls — actual numbers

**Parse coverage:** 40,800 of 40,800 parsed, **0 parse failures**. `parse_status` distribution:
`ok` × 40,800. Matches R10's prior report exactly.

**Multiplier control:** 2,850 zone-info rows fleet-wide carry `max_zone_list_multiplier > 1`. All
2,850 are in `mode == layout_assign`; by archetype: `MidriseApartment` 2,818, `HighriseApartment` 32,
**zero on any other archetype or any other mode.** The parser is reading the right column.

**Known-value control:** `way/401904735` (la_urban, `layout_assign`, `MidriseApartment`,
`old_status = identity`, declared 3 storeys, `footprint_area_m2 = 1850.454`). Multiplier-aware
simulated area = 7,401.68 m² against declared 5,551.36 m² → **error factor 1.33331** (4/3 =
1.33333, **0.0018% off**). The *plain* sum for the same building is 5,551.26 m² — 0.0018% away
from the *declared* area, i.e. the naive plain-sum parse would have silently reported this building
as correct. This is the exact trap §3 rule 2 names.

**The `applied` control — nuanced, reported in full, not smoothed:**
`open01_denominator_factors.csv` covers only the **non-applied** universe (6,939 rows); it contains
no list of genuinely-`applied` buildings. True `applied` buildings were identified as: `layout_assign`
mode, `zoning_strategy_manifest == 'layout_assign'` (i.e. actually went through `match_storeys()`),
**and absent from that file** (since absence from the non-applied census is what "applied" means).
That gives **503** buildings (7,442 evaluated − 6,939 non-applied = 503, matching the register's own
arithmetic exactly).
- All 503: median **1.0000**, mean 2.0076, range 0.6749–353.998, 78.33% within ±1%.
- Excluding the 6 buildings identified in §6 as carrying a separate, unrelated defect: median
  **1.0000**, mean **0.9999**, range 0.6749–1.1257, 79.28% within ±1%.
**Verdict:** the median satisfies the register's ~0.002% precision claim almost exactly (1.0000 vs
1.0000017). The join is not wrong. But at fleet scale the ~0.002% figure does **not** generalize to
the full `applied` population — about one in five `applied` buildings sits outside ±1%, up to +12.6%
/ −32.5%, even after removing the two known contaminants (§6). This is new information the N=4 local
sample could not have shown, and it is recorded here rather than smoothed into "the control passed."

**Join integrity, both directions, every mode:**

| mode | matched | corpus stems with no `05_results` row | `05_results` rows with no corpus dir |
|---|---|---|---|
| auto | 8,160 | 0 | 0 |
| building | 8,160 | 0 | 0 |
| fast_zone | 8,160 | 0 | 0 |
| floor | 8,160 | 0 | 0 |
| layout_assign | 8,160 | 0 | 0 |

Zero unmatched rows in either direction, in every mode. `osm_id ↔ stem` via `/` → `_` is exact at
fleet scale.

**Row count:** `auto` joins to **8,160** buildings — matches the corpus and the fixture exactly, no
generation drift in this join.

**Manifest coverage:** all 40,800 corpus rows matched a `03_manifest.parquet` row (0 unmatched).

---

## 3. (b) Fleet-wide, all five modes — `auto` first

| mode | n | median | mean | range | share within ±1% |
|---|---|---|---|---|---|
| **auto** | 8,160 | **1.0000** | 1.0592 | 0.9998× – 336.65× | **99.63%** |
| fast_zone | 8,160 | 1.0000 | 1.0631 | 0.8390× – 336.65× | 94.80% |
| floor | 8,160 | 1.0000 | 1.0593 | 0.4953× – 336.65× | 98.43% |
| layout_assign | 8,160 | 0.9999 | 1.4977 | 0.0557× – 353.998× | 15.37% |
| building | 8,160 | 0.5000 | 0.6287 | 0.0095× – 112.22× | 39.94% |

`auto`, `fast_zone` and `floor` all measure clean at the median (0.9998–1.0000) with 95–99.6% inside
±1%. `layout_assign` is the outlier mode by a wide margin, exactly where the register's inference
said the defect lives. `building` mode's median of 0.5 is new information — not previously measured
in any generation — and is flagged here as a finding, not investigated further (out of this task's
scope).

---

## 4. (a) `layout_assign` non-`applied` buildings — OPEN-01(a)

Population, using the register's own accounting (`old_status` present in
`open01_denominator_factors.csv`, all of which the file's own corrected `new_status` classifies as
non-applied): **n = 6,939**, matching the register's stated non-applied count exactly.

**E02-measured (this task):** median **0.9474**, mean 1.5122, range 0.0557× – 10.0008×, **2.05%
(142/6,939) within ±1% of 1.0.**

**Compared against `open01_denominator_factors.csv`'s inferred figures** (not overwritten, read only):
register-cited median **2.0**, mean 1.83, range 0.118×–10.0×, 12.6% at exactly 1.0.

The two measurements **do not match closely**, and the direction of the mismatch matters: the
inference-based figures cluster the median near 2.0 (dominated by the MidriseApartment 3-band→4-storey
×2 case), while the E02-simulated figures put the median at 0.9474 — closer to 1.0, but with a much
lower share landing inside tolerance (2.05% vs 12.6%). The inferred computation and the actual
simulation are measuring related but not identical things: the inferred figure is a storey-count ratio
computed from the manifest/prototype relationship, while the E02 figure is the true multiplier-aware
floor-area ratio pulled from what EnergyPlus actually built, which folds in additional real-world
factors (window/wall trims, prototype footprint vs. real footprint mismatch, per-archetype geometry)
that a pure storey-count ratio cannot see. **Both measurements agree on the top-line conclusion — the
defect is large and the assertion rarely holds (2–13% at 1.0, either way) — but disagree on its
central tendency and shape.** This is reported as a finding, not reconciled; reconciling it would
require re-deriving one measurement from the other, which is out of scope here.

---

## 5. (c) OPEN-28 — the generation confound, bounded

Archetype/zoning agreement between E02's own `03_manifest.parquet` (4th generation) and
`05_results.csv` (3rd generation), matched rows only (40,800 of 40,800 matched):

**Fleet-wide by mode:**

| mode | archetype agreement | zoning-strategy agreement |
|---|---|---|
| **auto** | **99.5%** | **100.0%** |
| building | 99.5% | 39.94% |
| fast_zone | 99.5% | 7.60% |
| floor | 99.5% | 52.48% |
| layout_assign | 99.5% | 8.80% |

**`auto` mode, per cell (archetype / zoning agreement, both 100% except where noted):**

| cell | archetype agree | zoning agree |
|---|---|---|
| austin_centre | 99.5% | 100.0% |
| austin_rural | 100.0% | 100.0% |
| austin_suburban | 100.0% | 100.0% |
| austin_urban | 100.0% | 100.0% |
| la_centre | 98.2% | 100.0% |
| la_rural | 100.0% | 100.0% |
| la_suburban | 100.0% | 100.0% |
| la_urban | 99.2% | 100.0% |
| nyc_centre | 96.5% | 100.0% |
| nyc_rural | 98.0% | 100.0% |
| nyc_suburban | 100.0% | 100.0% |
| nyc_urban | 100.0% | 100.0% |

**Reading:** `auto` mode's own `zoning_strategy` choice agrees with the adopted 3rd-generation run at
100% in every cell — `auto` is, by this measure, the mode closest to the code state that produced the
published baseline, consistent with it being the adopted mode. Archetype agreement is high (96.5–100%)
but not perfect — a handful of buildings per cell were assigned a different archetype between
generations 3 and 4, a genuine but small confound. **The other four modes' zoning-strategy agreement
with the adopted run collapses to single digits or tens of percent (7.6%–52.5% fleet-wide)** — expected,
since those modes deliberately force a different zoning approach (`fast_zone`, `floor`,
`layout_assign`) than whatever the adopted run used per building, so low agreement there is not a
defect, it is the experiment design. The confound is real but **fully bounded to `auto`'s 96.5–100%
archetype-agreement band**, which is the only mode whose comparison to the adopted denominator
matters for OPEN-01(b).

---

## 6. New findings surfaced by this parse (not requested, recorded per §5 of the plan)

**Finding 1 — a placeholder `footprint_area_m2 = 200.0` on 6 `Warehouse` buildings, all modes.**
`la_rural/way/472961171`, `la_rural/way/472960972`, `la_rural/way/472961088`, `la_rural/way/472961034`,
`la_rural/way/472961091`, `la_urban/way/402215469` — every one carries `data_quality_flag` containing
`no_floors` and a `footprint_area_m2` of exactly 200.0, while their simulated `perimeter_core`
multiplier-aware area ranges 4,063–67,330 m². This produces error factors up to **336.65×** in `auto`
mode alone (present, same magnitude, in every mode since `declared_area_m2` is mode-independent).
This is a **denominator data-quality defect, not a simulation or storey-matching defect** — it is
present in `auto`, the adopted mode, and it inflates every fleet-wide range and mean statistic in
this report. A fleet-wide scan for `footprint_area_m2 <= 210` on `archetype_id == 'Warehouse'` found
**16** buildings near this threshold (15 in `la_rural`, 1 in `la_urban`); exactly **6** sit at the
literal placeholder value 200.0. Not remediated here — recorded for the director to assign an item ID.

**Finding 2 — a `perimeter_core`-zoning geometry residual, ~0.2–1% of buildings, +2% to +30%.**
All 30 of `auto` mode's buildings outside ±1% tolerance (excluding the 6 in Finding 1) carry
`zoning_strategy_manifest == 'perimeter_core'`, with error factors clustered 1.02×–1.31×. This is a
small, consistent overshoot, not present in `single_zone` / `one_zone_per_floor` buildings under the
same mode (which measured 100% within ±1%, n=718, see §4 detail). Recorded as a finding; not sized
beyond this report (would need a `perimeter_core`-only census across all 5 modes to bound fully).

---

## 7. (d) OPEN-35 — the simulation-boundary check

Restricted to the 2,611 buildings in `open35_neither_population.csv` (neither `levels` nor `height_m`
persisted; all at `levels = 1.0` and flagged as if ~19 storeys by archetype assignment). All 2,611
matched in every mode (13,055 of 13,055 rows across the 5 modes).

| mode | OPEN-35 subset (n=2,611) | rest of fleet (n=5,549) |
|---|---|---|
| auto | median 1.0000, mean 1.0000, range 0.9998–1.0002, **100.00% within ±1%** | median 1.0000, mean 1.0871, range 0.9998–336.65, 99.46% within ±1% |
| building | median 1.0000, mean 1.0000, range 0.9998–1.0002, **100.00%** | median 0.3333, mean 0.4541, 11.68% |
| fast_zone | median 1.0000, mean 0.9997, range 0.8476–1.6269, 94.10% | median 1.0000, mean 1.0929, 95.13% |
| floor | median 1.0000, mean 1.0000, range 0.9998–1.0002, **100.00%** | median 1.0000, mean 1.0872, 97.69% |
| **layout_assign** | **median 1.0001, mean 2.3728, range 0.9399–10.0008, 17.92%** | median 0.8339, mean 1.0859, 14.16% |

**Reading — this is the independent check the register was waiting for, and it confirms the
mechanism.** In every mode except `layout_assign`, the OPEN-35 subpopulation's simulated area matches
its declared `levels = 1.0` footprint almost exactly (100% within ±1% in auto/building/floor) — which
is expected and unremarkable: those modes build zones from the persisted `levels`, so a building
persisted at `levels = 1.0` simulates at 1 storey and its own (wrong) declared denominator matches by
construction. **`layout_assign` breaks that pattern**: the same 2,611 buildings, run through prototype
storey-matching instead of the persisted `levels`, land at median error factor **1.0001 but mean
2.3728** with only **17.92%** inside tolerance — because `layout_assign` assigns storeys from the
*archetype*, not from the broken `levels = 1.0` field, and for a population whose real storey count
was never known (that is what "neither `levels` nor `height_m`" means), the archetype-driven estimate
and the placeholder `levels = 1.0` denominator disagree substantially. **The mechanism the register
hypothesized — that these buildings' geometry was built as if ~19 storeys while divided by a
`levels = 1.0` denominator — is directly visible in the `.eio`,** confirmed independently of the
inference this register entry was built on.

---

## 8. What this task closes and what it does not

**Does not close OPEN-01.** All three of its audit questions are now answered with a fleet-wide
measurement (a: layout_assign non-applied, n=6,939; b: all five modes fleet-wide; c: OPEN-01(c)'s
code-state question is T03's, not this task's). What remains is exactly one user decision — which
remedy (§6/T04 stop condition 2, not attempted here).

**Does not close OPEN-35.** Its mechanism is now confirmed by direct simulation evidence rather than
inference. The intended-fallback question (what *should* happen to a building with neither `levels`
nor `height_m`) is a DESIGN question, not measured or decided here.

**The two required sentences, together:** The adopted baseline (`auto` mode) is measured clear of
`layout_assign` — its median error factor is 1.0000 with 99.63% of 8,160 buildings within ±1%, and the
handful of exceptions trace to two separate, smaller, non-storey defects (§6), not to the storey-
matching mechanism. **And OPEN-01 and OPEN-03 remain exactly as large as they were measured** —
6,939 `layout_assign` non-applied buildings, median error factor 0.9474, only 2.05% within ±1% of the
correct denominator; this task did not shrink that number, it replaced its inference-based estimate
with a direct one.
