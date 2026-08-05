# Executor prompt — R08 (documentation closure, final task before CP-E)

> Written by the director 2026-08-04, after R09 was accepted and R06c landed. Dispatch a **fresh Sonnet**.
> This is the **last executor task in the arc**. Nothing runs after it except the director's CP-E signature.

---

Working directory `C:\Users\o_iseri\Desktop\OpenUBEM`. Read, in this order:

1. §1 (hard rules) and §3 task **R08** of
   `docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\debug\storey-Matching\PLAN_storey-matching_REMAINder.md`
2. In §5 of that same doc, the **last six entries**, in order:
   `#### R06`, `## 🔶 AUDIT — R06`, `#### R09`, `## 🔶 AUDIT — R09`, `#### R06c`, `## 🔶 AUDIT — R06c`
   (the file is 1,968 lines; these run from ~line 1142 to the end).
   The two AUDIT entries **override** the executor entries wherever they disagree — the corrections in
   them are binding, and three of them exist precisely because an executor entry printed a number that
   does not reproduce.
3. `docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\figures\README.md` — R09 already wrote the
   T20 disclosure block there. **Reuse its wording rather than inventing a second, drifting version.**

Do **not** read `PLAN_storey-matching_implementation.md` (CLOSED, ~3,500 lines). Grep it by
`F-nn` / `E-LA-nn` ID and read only the surrounding lines.

## 🔴 Absolute rules

- **This is a documentation task. Do not touch `openubem/` production code, do not run the pipeline,
  do not use the cluster, do not re-submit the fleet, do not regenerate any figure.**
- **Never `git commit`.** Never edit root `main.py`, any OVERVIEW or DESIGN doc, or `MEMORY.md`.
- **🔒 Frozen:** everything under `layoutAssigner\figures\` (R09's five regenerated
  `layout_assign_vs_modes_*` deliverables are now final — you may cite and describe them, not rebuild
  them); all `t17_*`/`t18_*`/`t19_*`/`t20_*` harvests; `openubem/idf/opaque_assembly.py`.
- Frozen constants: `T_ENGAGE = 0.868`, `T_MASS_MAX = 0.35`.
- Progress-log entries are **append-only**; never rewrite a frozen entry, including the AUDIT entries.
- **Every number you print must be traceable to a named file or a named §5 entry.** Three separate
  entries in this arc have shipped numbers that did not reproduce from the file they cited. Do not add
  a fourth. If a number you want to print exists only in an executor entry that an AUDIT corrected,
  **print the AUDIT's number.**

## Files to update — exactly three

1. **`OpenUBEM_results_LayoutAssigner.md` §3 / §3a** — the results write-up.
2. **`docs/PROJECT_CHECKLIST.md` §L** — the user's monitoring surface.
3. **Q3's own entry in `DONE/DONE-implementation_plan.md` §7** — Q3 is closed by this arc or it is not
   closed at all. Say which, in that entry.

No other file. If you believe a fourth file needs updating, **STOP and report** rather than editing it.

## The disclosure list — headline text, not a footnote

Every item below is disclosed plainly, in the results doc's own prose, not buried in a caveats
appendix. Items 1–8 carry over from the original R08 brief; items 9–15 are new, added by the R06,
R09 and R06c audits. **All 15 ship.**

1. `match_storeys()` expresses only `n_proto ∈ {1, 3}` and only the taller case. `n_proto == 2`
   (`SmallOffice`, 2,848 fleet buildings) and `n_proto >= 4` fall back permanently, as does every
   `n_real < n_proto`.
2. **R10's exactness rule further shrinks the expressible set on the two ZoneGroup archetypes:**
   `HighriseApartment` matches only at `n_real ∈ {10, 18, 26, …}`, `MidriseApartment` only at even
   `n_real ≥ 4`. **Use the AUDIT — R06 measured count: the `applied` population is 503, down from 593,
   a change of 90 buildings (66 `MidriseApartment` + 24 `HighriseApartment`), all
   `applied → fallback_not_expressible`, from `openubem/outputs/comparisons/t20_r10_reach_change.csv`.
   The old 81.6% / 98.4% inert shares are STALE and must not be reprinted anywhere.**
3. Storey matching is invisible in geometry by construction (D3(a)). Height does **not** track
   `num_floors` (E-LA-33) — state it, so no reader infers that 12.19 m towers over 1-storey houses
   were intended.
4. 718 buildings (8.8%) have no `ARCHETYPE_IDF_MAP` entry.
5. The shape-mismatch overlap residual is a **design property** of the mode, not a bug.
6. **R03's PV/generator invariance is synthetic-fixture only** — neither apartment archetype carries
   PV or generator objects, so it has no real-run evidence. Disclose it as such; do not imply it was
   validated on a real run.
7. **E-LA-36** (the `Zone.Multiplier` × `ZoneList` compounding, a silent 50% storey over-count on the
   dominant archetype) was found and fixed **inside this arc**. Say what it was and what it would have
   cost — a defect caught by audit is part of the result, not an embarrassment to bury.
8. **Forwarded out, not fixed here:** E-LA-21/22/23/24 and **E-LA-37** (editing the `ZoneGroup`'s own
   Zone List Multiplier would restore exact expressibility at every `n_real`; it is a different
   mechanism from D3(a) and R04 is closed at option (a)).
9. 🆕 **The EUI denominator is nominal, not simulated.** Every EUI in this arc — every mode, every
   harvest T08 through T20 — divides by `footprint_area_m2 × levels` from Stage-2 enrichment, **not**
   by the multiplier-aware total floor area EnergyPlus actually simulated. The verifying file
   (`eplusout.eio`) is deleted unconditionally by the shared cluster template
   (`scripts/cluster/submit_fleet_t08.sbatch:63`, `rm -f "$OUTDIR"/*.eio`), byte-identical across
   T08→T20, so **no fleet-scale EUI in this arc has an `eio`-verified denominator and none can be
   reconstructed without re-running the fleet.** R09 already prints this on Figures 2 and 5 — reuse
   that wording. R06c's local measurement is the only `eio`-true evidence that exists; report its
   scope honestly as single-digit-N and local.
10. 🆕 **E-LA-38 — the harvest's archetype labels are wrong for 41 of 8,160 buildings** (33
    `LargeHotel` + 8 `SmallHotel` mislabelled by `05_results.gpkg`). This is not cosmetic: **all 7 of
    T20's fleet failures are true `SmallHotel`** — 7 of the fleet's 8 (87.5%), against 0.00% failure
    everywhere else. State that the fleet's only failure population *is* the mislabel population.
    Correct the record if any earlier text calls the 7 failures a generic envelope defect.
11. 🆕 **E-LA-39 — `has_fatal` is a dead column.** It is `False` on all 8,160 harvest rows including
    the 7 that carry a literal `** Fatal **` in raw `eplusout.err`. Never cite it; anything that used
    it is unreliable.
12. 🆕 **E-LA-40 — three buildings regressed from success (T19) to failure (T20)**:
    `la_urban/way/401910463`, `nyc_rural/way/965718402`, `nyc_rural/way/965718403`, all inside the
    E-LA-38 mislabelled-`SmallHotel` population. 3/8,160 = 0.037%. **The arc closes with this open and
    forwarded, not fixed.** R09's hypothesis (multiplier scaling newly tipping the same
    `LAUNDRYROOMFLR1` warmup divergence) is explicitly a hypothesis — do not print it as a cause.
13. 🆕 **Print the full success-gain decomposition, all four terms**, not the two largest:
    `+150 (E-LA-20, fixed 2026-07-25, pre-dates this arc) + 2 (other nyc_rural, cause not investigated)
    + 14 (other cells, cause not investigated) − 3 (E-LA-40 regressions) = +163`, taking 7,990/8,160
    (97.92%) to 8,153/8,160 (99.914%). **The headline success-rate improvement is overwhelmingly not
    this arc's work.** Say so in the sentence that reports it, not in a following one.
14. 🆕 **E-LA-41 — the EUI denominator is wrong by `n_storeys_represented / num_floors` for every
    non-`applied` building.** Registered by AUDIT — R06c; read §3 of that entry and reproduce its
    separation of measured from inferred **exactly**:
    - **Measured** (real fleet buildings, real `eplusout.eio`, `openubem/outputs/comparisons/r06c_local_results.csv`):
      `applied` buildings hold `eio floor area == footprint × num_floors` to ~0.002% (N=4);
      `MidriseApartment` `identity` buildings fail at **exactly 4/3** (N=2), because the untouched
      prototype is a 4-storey-equivalent (3 Z-bands × a `ZoneGroup` list multiplier of 2 on the middle
      band) simulated for a 3-storey building.
    - **Inferred from the code contract, not measured** — `match_storeys()` mutates the IDF *only* when
      status is `applied`, so `identity`, `fallback_shorter` and `fallback_not_expressible` are one case.
      `MidriseApartment` non-`applied` exposure: **1,225 buildings at 4.000×, 1,048 at 2.000×, 343 at
      1.333×**, 66 below 1.0, **2,682 total**. Fleet-wide **6,939 of 7,442** evaluated buildings are
      non-`applied`; the factor for other archetypes is unmeasured.
    - State the reading the audit gives it: for a 1-storey building the mode simulates a 4-storey
      apartment prototype and divides that energy by one storey's area — **a correct number for the
      wrong building.** It is the numeric expression of E-LA-33 and of the fallback design, not a new
      mechanism. **Forwarded open, not fixed here.**
15. 🆕 **CP-D's two carried conditions are now answered — report both outcomes, including the negative
    one.** Condition (c): holds for `applied`, fails at 4/3 for non-`applied` (item 14). Condition (a),
    F-08's heating ratio on an `eio`-true denominator: **0.3244× and 0.0660×** on two matched real
    pairs — it moves *away* from 1.0, and in the opposite direction from F-08's original concern.
    **Its scope limit goes in the same sentence as the number, never in a following one:** one cell
    (`la_urban`), one archetype (`MidriseApartment`), one mild climate where heating is only
    **0.03–0.65% of total EUI**. Make no claim about `nyc_suburban` (F-08's original cell) or the fleet.

## Corrections that must land, in the words of the audits

- **F-11 / transformer cliff.** The conclusion is signed and stands: 0% transformer overload at every
  residual multiplier ≤ 7, 100% at every multiplier ≥ 8, a perfectly deterministic cliff; D9's
  conservative bound holds through 7 and fails at 8. **The counts printed in R06's item 4 were
  returned as non-reproducing** (its `0/125` and `107/107` do not close: 125+107=232≠231). Print
  **`0/114 (0.0%)` and `117/117 (100%)`** and no others — from
  `scratchpad/f11_transformer_check_v3.csv` filtered to `archetype_id=="MediumOffice" &
  new_status=="applied"` (231 rows), split at `new_multiplier<=7` vs `>=8`; 114+117=231 closes exactly.
  Both R06c and the director recomputed this independently and agree.
- **F-11's population is 439**, not 698 and not 805: the 698-row file filtered to
  `new_status ∈ {"applied", "fallback_not_expressible"}`, i.e. the taller-than-prototype half of F-11's
  original definition. 698 is the transformer-bearing staging population regardless of height; 805 is
  the stale pre-fix estimate. Name the filter so a reader can reproduce it.
- **503 vs 435 are both correct and are not in conflict** — the `applied` population is 503, of which
  435 carry a residual multiplier ≥ 2 and 68 carry multiplier exactly 1. Use whichever matches the
  sentence you are writing, and say which one you mean.
- **E-LA-36:** 0 / 522 violations, verified by the director.
- Fleet headline: **8,153 / 8,160 = 99.914% success, median `total_eui` 122.23 kWh/m²/yr** (T19
  103.75; adopted fleet baseline 158.0). **E-LA-22 still stands** — this delta is reported as a fact,
  not credited to or blamed on R01/R02/R03/R10.

## R07 — reduced, absorbed into R08

**R07 is REDUCED to a written statement inside R08** — no new figure panel. Write up its three
already-measured quantities (placement: hull centroid vs `footprint_centroid_utm`; plate area and
aspect ratio vs the real footprint; the overlap residual labelled as the design property it is), from
B08a/B08b's measurements, plus the explicit out-of-scope statement about height. Nothing is dropped
from the record — only the redundant rendering pass. R06 did not change geometry, so R07 is **not**
reinstated in full.

## Outdoor-analysis registry

This arc produced no new outdoor/site metric, so
`docs_EXPLANATION/OpenUBEM_outdoor_analysis_reference.md` needs **no** entry. Do not add one. State in
your progress-log entry that you checked and it does not apply.

## Deliverable

Append **one** `R08` progress-log entry to §5 (Artifacts / Deviations / Test status / Notes), then
write a short **completion report** for the director covering: what changed in each of the three
files, the final disclosure list as shipped (15 items), and anything you could not close.

**Do not sign CP-E — it is the director's.** Do not open any new task.
