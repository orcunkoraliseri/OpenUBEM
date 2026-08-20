# MEASUREMENT — open-28-harvest-generation-join

> **Slug:** `open-28-harvest-generation-join` · **Date:** 2026-08-05 · **Register item:** OPEN-28
> **Plan:** `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_published-numbers.md`, task M05.
> **This is a measurement-only report.** No remediation was performed or proposed, and no corrected
> cross-mode delta was computed (plan §6 M05, explicit prohibition). The only writes this task made
> are this file and `openubem/outputs/comparisons/open28_t08_t20_join.csv`.

---

## 0. Provenance — the exact files joined, named first

| Side | File | Rows | Unique `osm_id` | Cells covered |
|---|---|---:|---:|---|
| **T08** | `openubem/outputs/comparisons/t08_all_modes_eui.csv` | 18,120 (4 modes × 4,530 buildings) | 4,530 | `la_centre`, `nyc_centre`, `nyc_rural`, `nyc_suburban`, `nyc_urban` |
| **T20** | `openubem/outputs/comparisons/t20_layout_assign_eui.csv` | 8,160 (1 mode: `layout_assign`) | 8,160 | all 12 cells |

**Two candidate T08 files existed and how the choice was made.** `openubem/outputs/comparisons/`
also holds `t08_local_remainder_eui.csv` and `t08_mode_cell_summary.csv`. The latter is a per-cell
aggregate (not building-level, cannot be joined on `osm_id`). The former is a small supplementary
patch set, not the harvest's own building-level table. `t08_all_modes_eui.csv` is the file
`scripts/cluster/t08_harvest_results.py` itself writes as `OUTPUT_ALL_CSV` (script docstring, line 16)
and the file `docs_EXPLANATION/Results/OpenUBEM_results_Resolution.md` §4 cites as its own source — it
is the T08 harvest's canonical building-level output. No T20-side ambiguity existed:
`t20_layout_assign_eui.csv` is `t20_harvest_layout_assign.py`'s sole `OUTPUT_ALL_CSV` (script line 88),
and is the file `OpenUBEM_results_Resolution.md` §10.3/§10.7 names as the T20 fleet result.

**What generated each file, verified before use (plan §2 rule 12 / §5.6 lesson).**
`scripts/cluster/t08_harvest_results.py` and `scripts/cluster/t20_harvest_layout_assign.py` both parse
raw per-building EnergyPlus meter output harvested from the cluster (`REMOTE_HOST` fetch + SQL/err
parsing) and both source `osm_id` / `archetype_id` / `floor_area_m2` from the **same** local fixture
path, `PHASED_RESULTS = docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/05_results.gpkg`
(`t08_harvest_results.py:55-56,277-278`; `t20_harvest_layout_assign.py:84-85,295-296`). Neither is a
derived summary of another CSV — both are the harvest scripts' own first-generation output.

---

## 1. Join method

Both tables carry `osm_id` in `way/<id>` form (OSM way IDs, globally unique — verified no duplicate
`osm_id` within either table: 0 duplicates in T20 by construction; T08 collapsed from 4 mode-rows to 1
row per `osm_id` after confirming `archetype_id`, `floor_area_m2` and `cell` are **invariant across
all 4 T08 modes for every building** — 0 of 4,530 `osm_id` show >1 distinct value on any of those three
columns across modes). An outer join was performed on `osm_id` alone (T08 osm_ids are OSM way IDs,
globally unique across cells, so no cell-qualification was needed for correctness).

Reproduction command (from repo root, `./.venv/Scripts/python.exe`):
```python
import pandas as pd
t08 = pd.read_csv('openubem/outputs/comparisons/t08_all_modes_eui.csv').drop_duplicates('osm_id')
t20 = pd.read_csv('openubem/outputs/comparisons/t20_layout_assign_eui.csv')
merged = t08.merge(t20, on='osm_id', how='outer', indicator=True)
```

---

## 2. Test 1 — row-count reconciliation

| Quantity | Value |
|---|---:|
| `rows_in_both` | **4,530** |
| `t08_only` | **0** |
| `t20_only` | **3,630** |
| **Sum** (`both + t08_only + t20_only`) | **8,160** |
| **Union** (`t08_ids ∪ t20_ids`) | **8,160** |
| Sum == union? | **PASS** |

**T08 is a strict subset of T20 by building identity.** Every one of T08's 4,530 buildings also
appears in T20 — `t08_only = 0` is not a bug, it is the direct consequence of T08 having been scoped
to 5 cells (§0 table) that are all also present in T20's full 12-cell fleet. The 3,630 `t20_only`
buildings are simply the 7 cells (`austin_centre`, `austin_rural`, `austin_suburban`, `austin_urban`,
`la_rural`, `la_suburban`, `la_urban`) T08 never covered.

---

## 3. Archetype agreement for the 4,530 shared buildings

| Quantity | Value |
|---|---:|
| n shared | 4,530 |
| Archetype **agrees** (T08 `archetype_id` == T20 `archetype_id`) | **3,923 (86.60%)** |
| Archetype **disagrees** | **607 (13.40%)** |

**Top disagreeing pairs** (`t08_archetype_id → t20_archetype_id`, n = count):

| T08 archetype | T20 archetype | n | % of that archetype's T08 population |
|---|---|---:|---:|
| MediumOffice | SmallOffice | 396 | 396/559 = **70.8%** |
| LargeOffice | MediumOffice | 153 | 153/282 = **54.3%** |
| MediumOffice | LargeOffice | 50 | 50/559 = **8.9%** |
| PrimarySchool | SecondarySchool | 5 | 5/6 = 83.3% |
| SmallOffice | MediumOffice | 3 | 3/1,833 = 0.2% |

**Floor area agreement, for contrast:** all 4,530 shared buildings agree on `floor_area_m2` to within
1% between T08 and T20 (4,530/4,530 = 100%). The building's nominal geometry is stable across
harvests; **only the archetype classification drifted.**

### 3.1 Root cause of the drift, established (not merely observed)

Both harvest scripts read `archetype_id` from the same live path,
`docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/05_results.gpkg`
(§0), which is **git-tracked**. `git log` on that path (all 5 T08 cells) shows exactly one commit
touching it in the relevant window: `0df422e` — *"feat: implement machine learning imputer,
classification thresholds updates, and 3D viz enhancements"*, **2026-07-03 10:53:14 -0400**. The
parent state is `e063865` — *"feat: implement simulation resolution mode switch and finalize phaseE
documentation and plots"*, **2026-06-30 19:07:12 -0400**.

- `t08_all_modes_eui.csv` mtime: **2026-07-01 11:12:56** — between `e063865` and `0df422e`.
- `t20_layout_assign_eui.csv` mtime: **2026-08-04 18:14:15** — after `0df422e`, and no further commits
  touch this path since, so the file `t20_harvest_layout_assign.py` read is byte-identical (for this
  column set) to `0df422e`'s content.

Extracting both historical blobs read-only via `git show <rev>:<path>` (working tree left untouched —
verified with `git status` before and after, no diff) and comparing `archetype_id` per `osm_id`:

- The 5-cell gpkg content at `e063865` (pre-commit) vs `0df422e` (post-commit) shows **exactly 607
  archetype changes out of 4,530 matched rows** — the identical count, and the identical
  `(from → to)` pairs and counts, as the T08-vs-T20 harvest-CSV disagreement above.
- **Direct validation of the inference:** T08 harvest CSV's `archetype_id` matches the `e063865` blob
  for all 4,530 buildings (0 mismatches). T20 harvest CSV's `archetype_id` matches the `0df422e` blob
  for all 4,530 buildings restricted to the 5 T08 cells (0 mismatches).

**Conclusion: the 13.40% archetype disagreement is not resimulation noise or a join artifact. It is
commit `0df422e`'s classification-threshold change, landing 2 days after T08 ran and before T20 ran.**
This is the E-LA-22 / OPEN-08 confound, quantified for the first time and traced to its exact cause.

---

## 4. Vintage agreement — could not be measured; here is why, in full

**Neither T08 nor T20's provenance chain carries a vintage column.** `05_results.gpkg` at both
`e063865` and `0df422e` (and the current working-tree copy, identical to `0df422e` for this path) was
read directly — column list at all three states:

```
osm_id, footprint_area_m2, levels, height_m, archetype_id, zoning_strategy, data_quality_flag,
heating_eui_kwh_m2, cooling_eui_kwh_m2, lighting_eui_kwh_m2, equipment_eui_kwh_m2, fans_eui_kwh_m2,
pumps_eui_kwh_m2, dhw_gas_eui_kwh_m2, dhw_elec_eui_kwh_m2, dhw_eui_kwh_m2, cooking_eui_kwh_m2,
refrigeration_eui_kwh_m2, total_eui_kwh_m2, gwp_*_kgco2_m2 (x9), iod, simulation_status,
error_summary, geometry
```

No `vintage_standard` column, at any of the three states checked. `openubem/semantic/
construction_sets.py:126`'s `resolve_vintage()` produces a `vintage_standard` token
(`construction_sets.py:352`), but it is consumed **internally**, inside the same module, to select
`_ENVELOPE_VALUE_COLS` for `envelope_patcher` — it is never persisted as a standalone column in any
file either T08's or T20's harvest scripts read. **This is a genuine absence, not a search failure**;
confirmed by reading the actual columns of the actual files at the actual git states each harvest ran
against.

**Two other `05_results.gpkg` files in the tree do carry `vintage_standard`, and were deliberately
excluded** (plan §2 rule 12 — checking what generated a file before using it):

- `docs/docs_VALIDATION/step1/overAll/results/cases/<cell>/05_results.gpkg` — mtime 2026-06-12,
  predates T08 by 19 days.
- `docs/docs_VALIDATION/validations/overAll/results/cases/<cell>/05_results.gpkg` — mtime
  2026-06-26, predates T08 by 5 days; last touched by commit `e063865` (T08's own pre-state commit,
  coincidentally), but at a **different path** (`.../results/cases/`, not `.../results/phaseE/`).

Both belong to the `v11_*`/`v12_*`/`r6_rescore_cells.py` validation-pipeline lineage (confirmed by
`grep` — neither `t08_harvest_results.py` nor `t20_harvest_layout_assign.py` references the `cases/`
path at all, only `phaseE/`). Using either as a stand-in for T08's or T20's vintage would be exactly
the failure mode plan §5.6 warns about — a file from a different provenance chain that looks like an
answer. **Vintage agreement between T08 and T20 is therefore reported as UNMEASURABLE from the named
harvest artifacts, not as a silent pass or a fabricated number** (plan §2 rule 8).

---

## 5. Which harvest each side of the −29.1% figure came from

**Established, with a direct citation.** The −29.1% figure lives in
`docs/docs_DONE/SETUP/layoutAssigner/figures/OpenUBEM_results_LayoutAssigner.md`, §7.2 "Where the
fleet-wide −29% comes from (4,365 matched buildings)" (lines 449–458), inside §7 "Why `layout_assign`
differs from the other resolution modes — measured, 2026-07-26". The section's own opening line
(`:422-423`) states its provenance verbatim:

> *"Every number below was derived from `t19_layout_assign_eui.csv` and `t08_all_modes_eui.csv` at the
> time of writing."*

So:

- **`auto` side of the −29.1%: T08** (`t08_all_modes_eui.csv`, `mode == "auto"`).
- **`layout_assign` side of the −29.1%: T19** (`t19_layout_assign_eui.csv`) — **not T20.**

**This is the sub-question the plan and register flag as easy to skip, and the answer is not what the
task title implies.** M05's own title is "T08 vs T20 harvest-generation join," and the join above is
built exactly that way — but the actual published −29.1% figure predates T20 entirely. It is a T08
(2026-07-01, `auto`) vs T19 (2026-07-24, `layout_assign`) comparison, computed and written on
2026-07-26, ten days before the T20 harvest (2026-08-04) that this report's join uses for the
`layout_assign` side. **The −29.1% figure has never been checked against T08-vs-T20 archetype
agreement at all** — its own `layout_assign` side is one harvest generation earlier than T20, so even
this report's 86.60%/13.40% archetype-agreement finding (§3) does not directly characterize the
population the −29.1% was computed over. A T08-vs-T19 archetype join was **not performed** — it is
outside M05's stated scope (T08 vs T20) and is not fabricated here.

---

## 6. Test 2 — 5 shared buildings sampled at random, verified by hand

`random.seed(42)`, `random.sample(sorted(shared_osm_ids), 5)` over the 4,530-building shared
population. Verified against the **raw CSV rows** (`awk`/grep on the files directly, not through the
pandas join) — all 5 reproduce exactly. Vintage cells are marked `N/A` per §4 (no vintage column
exists in either raw table to verify against).

| osm_id | T08 cell | T08 archetype | T08 floor_area_m2 | T20 cell | T20 archetype | T20 floor_area_m2 | Archetype match | Vintage |
|---|---|---|---:|---|---|---:|---|---|
| `way/241836680` | nyc_urban | MediumOffice | 662.5811129422391 | nyc_urban | SmallOffice | 662.5811129422391 | **NO** | N/A |
| `way/1014146286` | nyc_suburban | MidriseApartment | 157.32752782984775 | nyc_suburban | MidriseApartment | 157.32752782984775 | YES | N/A |
| `way/266170672` | nyc_centre | MediumOffice | 4248.131565674675 | nyc_centre | MediumOffice | 4248.131565674675 | YES | N/A |
| `way/265424430` | nyc_centre | LargeOffice | 9924.158034971624 | nyc_centre | LargeOffice | 9924.158034971624 | YES | N/A |
| `way/265301903` | nyc_centre | MediumOffice | 1752.934383512175 | nyc_centre | SmallOffice | 1752.934383512175 | **NO** | N/A |

Raw verbatim T08 rows (`t08_all_modes_eui.csv`, `mode=="auto"` line only, header included once):
```
cell,city,mode,osm_id,archetype_id,floor_area_m2,status,has_fatal,zoning_strategy,num_zones,heating_eui,cooling_eui,lighting_eui,equipment_eui,fans_eui,pumps_eui,dhw_eui,cooking_eui,refrig_eui,total_eui,phaseE_total_eui
nyc_urban,NYC,auto,way/241836680,MediumOffice,662.5811129422391,success,False,one_zone_per_floor,5,69.88822413847714,14.3885037982823,26.465100649367304,44.06327617747435,47.16542921538356,0.0,8.308042114687145,0.0,0.0,210.2785760936718,210.27857609366575
nyc_suburban,NYC,auto,way/1014146286,MidriseApartment,157.32752782984775,success,False,single_zone,1,89.66658537572391,4.155337808924041,3.9654911445009904,43.39802550000099,5.8357389853400505,0.0,41.33664469337628,0.0,0.0,188.35782350786627,188.35782350786428
nyc_centre,NYC,auto,way/266170672,MediumOffice,4248.131565674675,success,False,perimeter_core,35,72.58958911562299,13.731288720380917,26.465100598254853,44.06327609234067,43.18814772109282,0.0,4.199690547471158,0.0,0.0,204.2370927951634,204.2370927951534
nyc_centre,NYC,auto,way/265424430,LargeOffice,9924.158034971624,success,False,one_zone_per_floor,20,28.465066708600293,16.124080191481937,26.465100597963524,44.06327609188421,29.92254680538856,6.68102627200755,2.84902664036569,0.0,0.0,154.57012330769177,154.57012330770922
nyc_centre,NYC,auto,way/265301903,MediumOffice,1752.934383512175,success,False,one_zone_per_floor,6,42.73854974112959,10.780416226971653,26.465100598161417,44.06327609223696,30.181941853902508,0.0,5.276379284581757,0.0,0.0,159.50566379698387,159.50566379698216
```

Raw verbatim T20 rows (`t20_layout_assign_eui.csv`, header included once):
```
cell,city,mode,osm_id,archetype_id,floor_area_m2,status,has_fatal,n_severe,n_warmup_convergence,heating_eui,cooling_eui,lighting_eui,equipment_eui,fans_eui,pumps_eui,dhw_eui,cooking_eui,refrig_eui,total_eui,phaseE_total_eui
nyc_urban,NYC,layout_assign,way/241836680,SmallOffice,662.5811129422391,success,False,0,0,4.1210322951263505,1.5228261641611525,1.931603330603074,4.972954053099257,2.3917304838849986,2.423954196489111e-11,2.582873281187544,0.0,0.0,17.523019608086614,124.62135629433833
nyc_suburban,NYC,layout_assign,way/1014146286,MidriseApartment,157.32752782984775,success,False,0,0,282.8767319896889,26.542664549071244,20.288413096966835,149.62502575456676,39.93353316960294,0.0,157.29483017427185,0.0,0.0,676.5611987341686,188.35782322689812
nyc_centre,NYC,layout_assign,way/266170672,MediumOffice,4248.131565674675,success,False,0,0,14.859019770325128,17.496579987353147,9.274355098839576,79.58012215917799,8.981426788496732,0.019066366623864295,12.393515874480379,0.0,0.0,142.60408604529678,204.2370927951534
nyc_centre,NYC,layout_assign,way/265424430,LargeOffice,9924.158034971624,success,False,10,2,14.67155399438704,2.6408465663281957,2.0532340759206855,17.603305926068714,6.418607900208297,0.950694668540501,0.9577163528492629,0.0,0.0,45.2959594843027,154.57012330770922
nyc_centre,NYC,layout_assign,way/265301903,SmallOffice,1752.934383512175,success,False,0,0,2.3273154955952466,1.0148489686334032,1.619401447557106,4.143902881037564,1.5147207374292075,2.0198519005945674e-11,2.151965140702248,0.0,0.0,12.772154670974976,101.67700687873315
```

All 5 archetype/floor_area values reproduce exactly against the raw CSV rows (byte-for-byte match on
`awk`-extracted lines vs. the pandas-computed table above). No STOP condition triggered.

---

## 7. Comparability verdict (measurement only — no correction computed)

- **Building overlap:** every T08 building is present in T20 (4,530/4,530 = 100%); T20 additionally
  covers 3,630 buildings T08 never touched (7 extra cells).
- **Archetype comparability: degraded.** 13.40% of shared buildings carry a different `archetype_id`
  in T08 vs T20, traced to one specific classification-threshold commit (`0df422e`) landing between
  the two harvests. This is not noise — it is fully deterministic and 100% explained.
- **Floor-area (denominator) comparability: intact.** 100% agreement to within 1% on the shared
  population.
- **Vintage comparability: cannot be assessed.** No vintage column exists in either harvest's actual
  provenance chain.
- **The −29.1% figure specifically is T08-`auto` vs T19-`layout_assign`, not T08-vs-T20** (§5) — this
  report's T08-vs-T20 archetype-agreement number does not characterize the population that figure was
  computed over; a T08-vs-T19 join would be required for that and was not performed (out of M05's
  stated scope).

**No corrected cross-mode delta was computed.** Per plan §6 M05, that is remediation and out of scope.

---

## 8. Artifacts

- `openubem/outputs/comparisons/open28_t08_t20_join.csv` — 8,160 rows, one per union `osm_id`, columns
  `osm_id, join_status, t08_*, t20_*, archetype_agree, floor_area_agree_1pct, vintage_t08, vintage_t20,
  vintage_agree` (the last three explicit `NOT_AVAILABLE`/`UNMEASURABLE` markers, never a silent
  blank).
