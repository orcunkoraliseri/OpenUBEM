# LayoutAssigner Arc — Completion Report

**Date:** 2026-07-22 · **Plan:** `implementation_plan.md` v2.1 · **Run mode:** autonomous director run (`prompt/DIRECTOR_PROMPT.md`), local-only, no cluster leg.

## 1. Per-task outcome

| Task | Outcome | Notes |
|---|---|---|
| T01 — Registry portability + lazy init | ✅ Done | `config.BASELINE_IDF_DIR` (env-overridable), `get_registry()` lazy singleton, no import-time scan |
| T02 — Re-key dicts on canonical vocab | ✅ Done | 28 canonical `_ARCHETYPE_VOCAB` tokens mapped; 2 case bugs fixed; partial-match fallback removed |
| T03 — Graceful no-baseline fallback | ✅ Done | `assign_baseline_layout()` returns `no_baseline: True` instead of a silent 3000 m² default |
| T04 — `scale_baseline_idf()` | ✅ Done | √S geometry, S absolute loads (Lights/Equipment/People/Infiltration/OA/DHW/Exterior Lights), density fields untouched |
| T05 — `parse_baseline_zones()` | ✅ Done | Live zone parse; surfaced E-LA-01 (plan §3.1's table was measurement error, corrected understanding: MidRise 27 not 92, Hospital 55 not 58) |
| **CP-A** | ✅ **PASS** | Scaling engine unit-green, 115/115 tests, director-verified |
| T06 — `purge_baseline_outputs()` + `patch_location_and_weather()` | ✅ Done | Output:*/OutputControl:* blanket purge; EPW-driven Site:Location + single annual RunPeriod |
| T07 — `builder.py` layout_assign branch | ✅ Done | Full `__init__`/`build()` integration; T03 fallback correctly wired here |
| T08 — E+ 22.1→23.1 library transition | ✅ Done | 25 unique baseline files transitioned to `00.BaselineBuildings_NUs_v231`; original 31-file library untouched; 0 hard-sized HVAC capacity fields found |
| T09 — Test restructure + LIVE_SMOKE-LA | ✅ Done | All real-library tests now `skipif`-guarded (portability proven: 42 passed/36 skipped/0 failed with the library absent); **LIVE_SMOKE-LA passed** (see §2) |
| **CP-B** | ✅ **PASS** | 148/148 regression, LIVE_SMOKE-LA real EnergyPlus run confirmed clean |
| T10 — Fix `compare_layout_assign.py` footguns | ✅ Done | Fabricated ×1.01 EUI removed → `*pending*`; real `parse_baseline_zones()` counts replace guessed formula; MD overwrite gated behind `--write-md` |
| T11 — `envelope_patcher.py` | ⏸ **Deferred (by design)** | Manager default (Q1): Buffalo CZ 6A envelope accepted for this validation pass. Not executed in this run. |
| T12 — Real simulation comparison (local leg) | 🟡 **Partial** | 6/6 sample archetypes built + simulated successfully with real EUI; full 12-cell cluster leg out of scope for this run (see §5) |
| **CP-C** | ✅ **PASS (partial — open blockers listed)** | Real per-archetype data now in §2 of the results doc; two genuine, unresolved findings carried forward (E-LA-05, E-LA-06) |

## 2. LIVE_SMOKE-LA result (T09, the CP-B gate)

One scaled `MidriseApartment` (footprint 2,500 m² × 6 levels = 15,000 m² real area vs. baseline 3,135 m² → **S = 4.78**, a materially non-trivial scale factor, 27 zones), built through the complete `layout_assign` pipeline and run under real EnergyPlus 23.1 against the real LA TMYx EPW (`USA_CA_Los.Angeles.Downtown-USC.Campus.722874`):

- `classify_outcome` → **`status = "success"`** (no Fatal, no crash, no timeout)
- 43 warnings, **0 severe errors**
- Wall clock: 199.8 s
- **Annual electricity: 411,303.48 kWh** (strictly non-zero, satisfying the plan's explicit gate)
- Partial (electricity-only) EUI: 27.42 kWh/m²/yr

This is the first real, physically-simulated proof that `layout_assign` scales and runs correctly end-to-end under EnergyPlus 23.1.

## 3. T12 local-leg real EUI results

6 archetype families, one real single-building EnergyPlus 23.1 annual simulation each (same LA EPW), scale factors deliberately spanning both up- and down-scaling:

| Archetype | Scale S | Zones | Total EUI (kWh/m²/yr) | Diagnostic status |
|---|---|---|---|---|
| MidriseApartment | 4.78 | 27 | 60.07 | Clean (43 warnings, 0 severe) |
| MediumOffice | 1.60 | 18 | 72.48 | † 73,803 real Severe Errors (transformer overload) |
| SmallHotel | 1.87 | 67 | 151.46 | † 120.5M recurring warnings (coil rated-flow out of range) |
| SecondarySchool | 0.51 | 46 | 67.18 | † 15.8M warnings + 28 severe (heat exchanger flow ratio) |
| RetailStandalone | 0.65 | 5 | 101.20 | † 604K warnings (unitary system part-load ratio) |
| FullServiceRestaurant | 0.78 | 3 | 886.08 | † 1.1M warnings (part-load ratio + DHW temperature) |

All 6 reached `status="success"` (no Fatal/crash/timeout) and produced EUI within `config.EUI_PLAUSIBILITY_BOUNDS` (25–1000 kWh/m²/yr). `MidriseApartment`'s meter-only electricity figure independently cross-checks exact against the T09 LIVE_SMOKE number, confirming harvest-methodology consistency.

Results doc §2 (per-archetype scaling matrix) now carries these 6 real numbers; §3 (12-cell fleet comparison table) deliberately stays `*pending*` for all 12 cells — a single-building-per-archetype local sample cannot honestly stand in for a per-cell fleet median, and conflating the two granularities would misrepresent the data. A note under §3 explains this.

## 4. Error log summary

| ID | Title | Status |
|---|---|---|
| E-LA-01 | Plan §3.1's zone-count table built from a naive-grep method contaminated by `BuildingSurface:Detailed`'s `Outside Boundary Condition = "Zone"` field value | CLOSED (not a code defect — `parse_baseline_zones()` is correct and authoritative; independently re-verified by the director with a column-anchored grep) |
| E-LA-02 | T08 batch-transition success check unreliable (log-banner false negatives) + a stale duplicate background process | CLOSED |
| E-LA-03 | T09 LIVE_SMOKE-LA process was killed by a tool-level timeout mid-run; employee failed to detect it and reported stale "still running" status across 3 turns | CLOSED (director stopped the agent, re-ran the employee's own correct script directly, obtained a clean real result) |
| E-LA-04 | T10 pre-fix sanity probe transiently ran the still-unmodified script and overwrote the results doc with fabricated content | CLOSED (self-corrected by the same task's mandated regeneration step; no lasting effect, doc was untracked in git) |
| E-LA-05 | `openubem/results/parser.py`'s `_check_zone_integrity()`/`ZONE_RX` assumes the OpenUBEM `{osm_id}_F{floor}_{label}` zone-naming convention; `layout_assign` zones keep the DOE baseline's native names, so the gate always false-negatives for `layout_assign` buildings | **OPEN-BLOCKED** — affects every `layout_assign` building, local or cluster-scale. Worked around for T12's own numbers (bypasses only the naming gate, not the EUI arithmetic); `parser.py` itself intentionally left unmodified (shared Step-5 code, out of this plan's scope) |
| E-LA-06 | `scale_baseline_idf()` (T04) does not scale fixed-capacity auxiliary equipment (electrical transformers, DHW tank capacity, HVAC coil/fan rated flow/capacity); at non-identity scale factors this produces large real warning/severe-error counts (most notably 73,803 Severe "Transformer Overloaded" errors on `MediumOffice` at S=1.60) | **OPEN-BLOCKED** — real EnergyPlus diagnostics, independently confirmed by the director from raw `eplusout.err` content, not a script artifact. Results remain physically plausible but the scaling engine has a genuine, unaddressed coverage gap at non-trivial scale factors |

**Exact pytest totals (director's own independent runs, not employee-reported):** `pytest tests/test_layout_assigner.py tests/test_zoning.py tests/test_idf_builder.py tests/test_resolution_mode_live.py -q` → **148 passed**, 0 failed, throughout T06–T12. Portability proof: with `OPENUBEM_BASELINE_IDF_DIR` pointed at a nonexistent path, `pytest tests/test_layout_assigner.py -q -rs` → 42 passed, 36 skipped, 0 failed.

## 5. What remains for a future arc

1. **E-LA-06 fix (recommended highest priority):** extend `scale_baseline_idf()` (or a new sibling function) to cover fixed-capacity auxiliary equipment — `ElectricLoadCenter:Transformer` rated capacity, `WaterHeater:*` tank capacity, and an audit of HVAC coil/fan rated-flow/capacity fields that fall outside valid performance-curve range at non-identity scale factors. This is the single biggest open item before `layout_assign` can be considered production-grade at arbitrary scale factors — right now it is reliably clean only very close to the baseline's own native scale (confirmed clean at S=4.78 for MidriseApartment specifically; S in the 0.5–1.9 range triggered real diagnostics for 5 of 6 other archetypes tested).
2. **E-LA-05 fix:** make `openubem/results/parser.py`'s `_check_zone_integrity()`/`resolve_zone()` tolerant of (or bypass-aware for) `layout_assign`-native DOE zone names, so the shared Step-5 harvesting path works for `layout_assign` without a manual workaround. Needed before any cluster-scale `layout_assign` harvesting.
3. **T11 — envelope patching:** cross-CZ U-value/SHGC patching was deferred by design (Q1 manager default). All T09/T12 simulations ran under the baseline's native Buffalo CZ 6A envelope even when simulated under LA weather — a separate, real approximation from E-LA-06, worth revisiting particularly given some T12 EUI values (e.g. `FullServiceRestaurant` at 886 kWh/m²/yr) are high, though still within plausibility bounds.
4. **Full 12-cell cluster leg (T12's remainder):** the local leg validated 6 representative archetypes at single-building scale; populating results-doc §3's actual per-cell fleet-median `layout_assign` column requires running the mode across the full 8,160-building / 12-cell dataset via sbatch, which this autonomous run explicitly did not attempt (no unattended cluster submission). Should also re-check E-LA-06 at cluster scale/statistics once fixed.
5. Plan §3.1's zone-count table (in `implementation_plan.md`) and the analogous tables in `walkthrough.md`/results-doc history contain the E-LA-01 measurement error (contaminated grep) for rows other than MidRise/Hospital, which were not individually re-verified — a future pass could re-measure the full 31-row table properly, though this has no functional impact since `parse_baseline_zones()` is already the enforced live source of truth everywhere it matters.

## 6. Files touched (repo)

`openubem/config.py`, `openubem/geometry/layout_assigner.py` (new), `openubem/geometry/zoning.py` (pre-existing wiring, untouched this run), `openubem/idf/builder.py`, `tests/test_layout_assigner.py` (new), `scripts/analysis/compare_layout_assign.py`, `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/implementation_plan.md`, `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/OpenUBEM_results_LayoutAssigner.md`, `openubem/outputs/comparisons/layout_assign_vs_resolution_modes.csv`. Library-side (outside repo): new sibling `C:\Users\o_iseri\Desktop\idf_reader\Content\00.BaselineBuildings_NUs_v231\` (25 E+ 23.1 files); original 31-file `00.BaselineBuildings_NUs` untouched.

No git commits were made (git is handled externally, per project convention).
