# MEASUREMENT — OPEN-07 + OPEN-38 subsurface sub-question — 2026-08-18

**Script:** `scripts/analysis/open07_smallhotel_idf_diff.py`
**Output:** `openubem/outputs/comparisons/open07_smallhotel_idf_diff.csv`
**Task:** T02 of `docs/docs_ACTIVE/openings/implemenation/PLAN_open-52-and-four-items-2026-08-18.md`

## Scope

Two of the three E-LA-40 regressed buildings have a surviving paired A/B IDF in
`scratchpad/e-la-20-investigation/i03/work_part1/`:

- `nyc_rural/way/965718402`
- `nyc_rural/way/965718403`

`la_urban/way/401910463` has **no** surviving IDF in that cache (confirmed by directory search — the
scratchpad only holds `way_965718402` and `way_965718403` under both `step3_A_.../idfs/` and
`step3_B_.../idfs/`). **Everything below covers 2 of the 3 buildings. It is not generalised to the
third.**

## Step 1 — artifact verification (gate)

```
way_965718402 [A] exists=True size=1909240 mtime=1785020292.9 path=...step3_A_as_classified_today/idfs/way_965718402.idf
way_965718402 [B] exists=True size=358867  mtime=1785020716.7 path=...step3_B_as_recorded_in_t19_SmallOffice/idfs/way_965718402.idf
way_965718403 [A] exists=True size=1909240 mtime=1785020294.3 path=...step3_A_as_classified_today/idfs/way_965718403.idf
way_965718403 [B] exists=True size=358867  mtime=1785020717.2 path=...step3_B_as_recorded_in_t19_SmallOffice/idfs/way_965718403.idf
CONTROL SmallHotel_90.1-2013.idf exists=True size=1561172 path=docs/docs_DONE/LOADS & SCHEDULES/scheduleDigitization/sources/SmallHotel_90.1-2013.idf
```

All four A/B files and the control prototype exist and are non-empty. `way/401910463` is confirmed
absent from both `idfs/` directories.

## Step 4 — control (gate, run before the finding)

Subsurface-fit test (see Method below) run on the repo's own healthy `SmallHotel_90.1-2013.idf`
prototype, which is not part of the regressed population:

```
Control summary: {'n_subsurfaces': 106, 'n_fitted': 106, 'n_unfitted': 0, 'n_no_base_surface': 0}
```

**The control is clean: 0 of 106 subsurfaces flagged.** The test does not spuriously flag a healthy
IDF, so the same test on the A/B sides below is not void.

## Method — subsurface-fit test

For every `FenestrationSurface:Detailed` object (both `Window`- and `Door`-typed; no separate `Door:`
objects exist in these IDFs), the base surface is looked up by name, its plane is fit with Newell's
method, both the base polygon and the subsurface vertices are projected into that plane's local 2D
coordinates, and the subsurface is scored `fitted` only if every projected vertex is within the base
polygon (ray-casting point-in-polygon, 0.02 m boundary tolerance) **and** every subsurface vertex sits
within 0.02 m of the base surface's own plane. This is an independent re-implementation of what
EnergyPlus's `CHKSBS` check does, not the EnergyPlus source itself — the control run above is what
establishes it behaves sanely, not an assumption.

## A vs B diff, per building

| | A (`SmallHotel`, as classified today) | B (`SmallOffice`, as recorded in T19) |
|---|---|---|
| Zones | 67 | 6 |
| Surfaces | 485 | 43 |
| Subsurfaces | 106 | 23 |
| Has a zone named `*LaundryRoom*` | Yes (both buildings) | No (either building) |
| Distinct subsurface multipliers | {1.0} | {1.0} |
| Subsurface-fit result | 106/106 fitted, 0 unfitted, 0 missing-base | 23/23 fitted, 0 unfitted, 0 missing-base |

Identical for both `way_965718402` and `way_965718403` — the A-side and B-side counts do not vary by
building.

**A-side is not a re-extruded building — it is the raw prototype, unmodified.** A's zone/surface/
subsurface counts (67 / 485 / 106) are **exactly** the control prototype's own counts (67 / 485 / 106),
for both regressed buildings. This corroborates OPEN-38's existing finding (the substituted DOE
`SmallHotel` prototype) with an independent count-level check: the "classified today" geometry is not
an OSM-extruded building reclassified as `SmallHotel` — it is the literal, un-resized DOE prototype
IDF, dropped in wholesale, for two different OSM buildings, byte-for-byte identical to each other
(1,909,240 bytes, same mtime family) and shape-identical to the repo's own prototype source.

## Subsurface-fit finding (OPEN-38's unfitted-subsurface sub-question)

**On the surviving scratchpad IDFs, 0 of 106 A-side and 0 of 23 B-side subsurfaces are unfitted, for
both buildings.** The subsurface-fit test does not separate A from B, and does not separate either
side from the healthy control. **This is a null result on the artifact that exists** — it does not
confirm unfitted subsurfaces below `.err`'s reporting threshold, and per the rule against rescuing a
hypothesis, that null result is reported as-is rather than explained away.

## `.err` cross-check — a disagreement, noted, not resolved

Both buildings' `layout_assign`-mode harvest carries the fatal and the CHKSBS warnings the register
records:

```
way_965718402 eplusout.err: n_fatal=1, n_severe=1, n_laundryroom_severe=1
  Severe: CalcHeatBalanceInsideSurf: The temperature of -11949.70 C for zone="LAUNDRYROOMFLR1",
          for surface="P_LAUNDRYROOMFLR1_10010_0_10008"
  CHKSBS "Base surface does not surround subsurface" warnings (3, plus 1 summary header line):
    Surface "W_REARSTAIRSFLR1_3_0_0" misses SubSurface "W_REARSTAIRSFLR1_3_0_0_DOOR"
    Surface "W_CORRIDORFLR1_10_0_0" misses SubSurface "W_CORRIDORFLR1_10_0_0_DOOR"
    Surface "W_FRONTSTAIRSFLR1_3_0_0" misses SubSurface "W_FRONTSTAIRSFLR1_3_0_0_DOOR"

way_965718403 eplusout.err: n_fatal=1, n_severe=1, n_laundryroom_severe=1
  Severe: CalcHeatBalanceInsideSurf: The temperature of -15490.64 C for zone="LAUNDRYROOMFLR1",
          for surface="W_LAUNDRYROOMFLR1_3_0_0"
  Same 3 CHKSBS-named pairs (plus 1 summary header line), by name.
```

This **confirms** the register's fatal zone (`LAUNDRYROOMFLR1`) and the Sizing/Warmup-phase framing
already on record (the severe fires "during Warmup & Sizing" per the `.err` text, consistent with the
register's Sizing-phase attribution).

**It does not confirm the CHKSBS pairing geometrically.** All three named surface/subsurface pairs
exist by name in the scratchpad A-side IDF, and were hand-checked directly (not just through the
script): e.g. `W_RearStairsFlr1_3_0_0` spans x∈[12.002, 12.560] m, z∈[0, 3.353] m, and its door
`W_RearStairsFlr1_3_0_0_Door` spans x∈[12.247, 12.456] m, z∈[0, 2.134] m — fully inside, by margins of
0.1–1.2 m, not a borderline case. The same pattern holds for `W_CorridorFlr1_10_0_0` /
`..._Door`. **The scratchpad IDF's geometry, for the exact surfaces the `.err` names, does not
reproduce the defect the `.err` reports.**

The most likely explanation, stated as a hypothesis and not resolved here: the scratchpad IDFs were
built 2026-07-25 (mtime) for the `i03` investigation, while the harvested `.err` is dated 2026-08-10 —
**eleven days later**. Same classification, same surface-naming convention, but not established to be
the same generated geometry. **This is recorded as an open disagreement, per the plan's instruction not
to resolve it**, not as a refutation of the `.err`'s own report.

## Limit

Findings above cover **2 of the 3** `E-LA-40` buildings. `la_urban/way/401910463` has no surviving IDF
anywhere under `scratchpad/e-la-20-investigation/`; nothing here is extended to it.

## Recommended dispositions (director decides)

- **OPEN-07**: the "no T20 IDF survives locally" blocker is **false for 2 of 3 buildings** and stays
  true for the third. Recommend: **keep OPEN-07 open**, narrowed — its own multiplier-scaling hypothesis
  is not what the surviving geometry shows (no multiplier disagreement, both sides multiplier=1.0); the
  operative mechanism is OPEN-38's wholesale-prototype-substitution finding, already recorded there.
  Do not close OPEN-07 as "answered by OPEN-38" without a director ruling, since 1 of 3 buildings is
  still unmeasured.
- **OPEN-38's subsurface sub-question**: answerable-but-null on 2 of 3 buildings — the surviving IDFs
  show 0 unfitted subsurfaces on both sides, control included, but the `.err` cross-check surfaced an
  unresolved disagreement about which geometry actually ran. Recommend recording it as **measured, null
  result, with an open provenance question** — not as "answered."


---

## Director's audit, 2026-08-18 — re-derivation, one correction, and a sharper reading

Everything below was re-derived independently from the same files; nothing is carried from the report
above.

**1. The counts reproduce exactly.** A = 67 zones / 485 surfaces / 106 subsurfaces, B = 6 / 43 / 23,
for *both* `way_965718402` and `way_965718403`; the read-only prototype
`docs/docs_DONE/LOADS & SCHEDULES/scheduleDigitization/sources/SmallHotel_90.1-2013.idf` is also
67 / 485 / 106. The A-side-is-the-raw-prototype reading stands. The two A-side files are byte-different
(`md5` `03f3ce77…` vs `5e5ec57c…`) at identical size — consistent with per-building renaming over one
geometry, not with two geometries.

**2. Correction — the provenance doubt is weaker than the report states, and the director's own first
check was wrong.** A case-sensitive grep for the `.err`'s uppercased fatal surface name returned 0 and
briefly looked like proof that the scratchpad IDF was a different generation. It is not: EnergyPlus
uppercases names in `.err`. Matched case-insensitively, **the scratchpad IDF contains the exact fatal
surface `P_LaundryRoomFlr1_10010_0_10008` and all three CHKSBS base/door pairs, name for name**. The
11-day mtime gap therefore dates the scratchpad *copy*, not a different geometry. The report was right
to flag the gap and right not to resolve it; on the evidence it resolves in favour of same-geometry.

**3. The `.err`-vs-geometry disagreement is real and is stronger than "the door fits."** Re-derived for
all three flagged pairs on the A-side IDF:

| pair | sub coplanar with base | sub inside base in-plane | duplicate names |
|---|---|---|---|
| `W_RearStairsFlr1_3_0_0` / `_Door` | **0.0000 m** on all 4 vertices | x[12.247,12.456] ⊂ [12.002,12.560], z[0,2.134] ⊂ [0,3.353] | none |
| `W_CorridorFlr1_10_0_0` / `_Door` | **0.0000 m** | x[5.741,5.950] ⊂ [5.449,6.146], z ⊂ [0,3.353] | none |
| `W_FrontStairsFlr1_3_0_0` / `_Door` | **0.0000 m** | x[0.224,0.433] ⊂ [0.011,0.569], z ⊂ [0,3.353] | none |

The IDF carries **591 surface+subsurface objects and zero duplicate names**, so EnergyPlus is not
resolving `BaseSurfaceName` to some other instance. Each door is exactly in its wall's plane and
strictly inside it, and EnergyPlus still reports `Overlap Status=No-Overlap`. The one non-generic
feature is that each door's bottom edge lies exactly on its wall's bottom edge (z=0 on both) — recorded
as an observation, **not** as an explanation; no test here establishes it as the trigger.

🔴 **4. What this does to the report's null result.** The subsurface test's only control was a
known-*negative* (the healthy prototype, 0 unfitted). It was never shown to return a positive on a case
the authority flags — and on the three cases EnergyPlus does flag here, **it disagrees with
EnergyPlus**. A detector with no demonstrated true positive cannot support "no unfitted subsurfaces
found": the 106/106 and 23/23 results are a **null result of unvalidated power**, not evidence of
absence. This does not impeach the A/B diff, which rests on counts, not on the detector.

🔴 **5. The finding that actually settles the sub-question, and it is a refutation.** The three CHKSBS
warnings are on **`RearStairs`, `Corridor` and `FrontStairs`** — **none of them is
`LaundryRoomFlr1`**, the zone that carries the Severe and kills the run
(`** Severe ** CalcHeatBalanceInsideSurf: The temperature of -11949.70 C for zone="LAUNDRYROOMFLR1",
for surface="P_LAUNDRYROOMFLR1_10010_0_10008"`). So even taking every CHKSBS warning at face value,
**the unfitted-subsurface signature does not touch the dying zone.** Unfitted subsurfaces are not
OPEN-38's mechanism.

This is the same shape as the refutation that killed the orientation lead for OPEN-42 on 2026-08-18:
a signature that fires on healthy zones and is absent from the fatal one. **The director accepts the
report's recommendation — OPEN-07 and OPEN-38 stay open and stay separate — and strengthens its
OPEN-38 half from "measured null" to "refuted on the dying zone."**
