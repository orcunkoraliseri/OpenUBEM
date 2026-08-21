# PROPOSED AMENDMENT — open-items register, 2026-08-05

> **Status: proposed, not applied.** Awaiting the user's approval before it is written into
> `docs/docs_ACTIVE/openings/DONE/INVESTIGATION_open-items-register.md`.
> Source: the five Phase-1 measurements M01–M05, each independently re-derived by the manager.
> Reports in `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-0*.md`.

---

## A. Evidence-mark changes

| Item | Was | Becomes | Basis |
|---|---|---|---|
| OPEN-01 | ✅ | ✅ **measured** | M01 — all 28 archetype tokens, 6,939 fleet rows |
| OPEN-02 | ✅ | ✅ **measured + decided** | M02 — 881 local `.eio`; retention approved in principle |
| OPEN-03 | 📄 | ✅ **measured** | M03 — verdict + 12-archetype magnitude bound |
| OPEN-04 | ⚠️ | ✅ **explained** | M04 — bisect reproduces the drift exactly |
| OPEN-28 | ✅ | ✅ **quantified** | M05 — full join, 8,160-row union |
| OPEN-08 | 📄 | 📄 **partially quantified** | M05 — the confound is 13.4% archetype disagreement |

---

## B. Per-item amendments

### OPEN-01 — amend

**Superseded.** The inferred factor table (register lines 124–130) covered `MidriseApartment` only
and assumed `4 / num_floors`. It is replaced by direct measurement of all 28 archetype tokens across
the 25 baseline IDFs.

**Measured.** Only **2 of 28** archetypes carry a `ZoneGroup` list multiplier:
`MidriseApartment` 3 bands → **4** storeys (×2), `HighriseApartment` 3 bands → **10** (×8). The other
26 have `n_storeys_represented == n_proto`.

**Fleet-wide, 6,939 non-`applied` rows:** only **877 (12.6%)** sit at error factor 1.0. Median
**2.0**, mean 1.83, range **0.118× – 10.0×**. Largest masses: ×2.0 (2,263), ×4.0 (1,316),
×0.667 (1,031).

**Correction to the record.** `openubem/outputs/comparisons/a1_prototype_storey_structure.csv` must
not be cited for this item. Its `num_modelled_storeys` is the **band count**, not the
multiplier-aware storey count, and its `has_multiplier_gt_1` flag reads `False` for both archetypes
that actually carry a multiplier — it tests `Zone.Multiplier` and is blind to `ZoneGroup`'s list
multiplier. It understates `MidriseApartment` by 1 and `HighriseApartment` by 7.

**"What is NOT known" — item 1 is now closed.** Items 2 (which remedy) and 3 (whether any *adopted*
result depends on this) remain open and unmeasured. **Item 3 is now load-bearing** — see §C, new
item OPEN-32.

### OPEN-02 — amend

**Measured.** `eplusout.eio` median **76,068 B** (n=881 local, min 6,736, max 1,092,989). Marginal
cost of retaining it, per run, against what the pipeline already keeps: **12.6%** (median of the
per-run ratio; 2.4% by aggregate bytes). One five-mode fleet pass: **1.3 GB** typical to **~43–45 GB**
worst case, against **8.1 TB** free on the shared filesystem — **0.5% at the absolute worst.**

**The register's own prediction is confirmed verbatim.** Line 169 said *"the fear may not survive
contact with the number."* It did not. The ">800 GB untrimmed per city" figure at
`submit_fleet_t08.sbatch:63` covers **eleven** file types deleted together; `.eio` alone was never
the cost.

**Stated limitation.** `fast_zone` has **zero** local `.eio` samples; its contribution is a bounded
estimate from zone-count ratios, not a measurement. Its worst-case bound is still negligible.

**Decision taken 2026-08-05 (CP-M1).** A five-mode re-run retaining `.eio` is **approved in
principle**. Execution moved off the Speed cluster at the user's instruction — its 32-CPU account cap
is fully occupied by an unrelated account (32 running / 675 pending, observed read-only). Local
feasibility is being costed; the pass is **not scoped, not submitted, and may yet be reduced in
scope**.

### OPEN-03 — amend, and correct the register's own claim

**Verdict: `undocumented but deliberate`** — traceable to a decision that was never written into any
spec. Zero matches for `layout_assign` / `resolution_mode` anywhere under `docs/docs_main`. The
decision is real and traceable to
`docs/docs_DONE/SETUP/layoutAssigner/DONE/DONE-implementation_plan.md:155` and `:494`, the latter
flagging the mechanism "for a future arc".

**Correction to line 179 of this register.** It currently reads *"documented in results §7."* That is
misleading: results §7 (`OpenUBEM_results_LayoutAssigner.md:463`) is a **post-hoc write-up produced by
the same session that discovered the effect**, not a prior specification. Its wording — *"a direct
consequence of prototype substitution, not a defect"* — is recorded here as a **contradictory
statement, not adjudicated**.

**Magnitude, static, no simulation (n=12 archetypes matched, 0 unmatched).** 2013-code vs 2022-code:
lighting power ratio median **1.722** (range 1.256–2.502); equipment **1.064**; occupancy **1.000**.
The two equipment ratios of exactly 1.000 were checked against raw IDF text and are genuine source
agreement, not a parsing artefact.

**The proxy understates the real error.** No canonical fleet-wide `vintage_standard` column exists
(see OPEN-30). The only fleet-wide sample available — a prior investigation's byproduct, cited with a
provenance caveat — puts **92.9%** of buildings at `DOERefPre1980`, far older than the 2013 code used
as the comparison floor.

### OPEN-04 — amend, downgrade urgency, keep the item open for a different reason

**The 92.0/88.0 pair is `test_fine_top1` only** — cited at
`docs/docs_main/docs_step2/PLAN_step-2-classifier-coverage-R3.md:131,148` and
`docs/docs_DONE/BUGS/input-framework/PLAN_input-framework-classification-fixes.md:84,140`.
`test_coarse_top1` was **100% at every commit tested** and never at risk. The apparent contradiction
(88% vs a 90% gate) dissolves: the fine gate is **0.70**. Verified live at HEAD — 3/3 pass.

**Bisect, read-only via disposable worktrees, main tree clean before and after:**

| commit | date | fine top-1 | role |
|---|---|---|---|
| `7635ce2` | 2026-06-12 | 92.0% | R3-era reference (CP-α) |
| `67ede73` | 2026-07-01 | **84.0%** | **first change** — E-R3-3 tier bins; 14 fixture rows relabelled + rules rewritten |
| `0df422e` | 2026-07-03 | **88.0%** | second change — partial recovery |
| `ef19141` | 2026-07-21 | 88.0% | contains Phase-D fusion/crosswalk — **no change** |
| `bca92d0` | 2026-08-05 | 88.0% | HEAD |

**Phase-D fusion/crosswalk hypothesis: FALSIFIED.** The drift completed 18 days before that work
landed, and `git diff` on every classifier/fixture/test file between `0df422e` and `ef19141` is empty.

**Reframe the item.** It is no longer *"an unexplained drift."* It is a **ratified change (E-R3-3)
whose effect on the labelled fixture was never compared against the prior baseline.** The register's
line 192–194 framing — *"an accuracy gate that drifts without anyone noticing is a broken
instrument"* — is upheld in substance but the instrument is not broken; the **review process** is the
defect. Carried to §C as new item OPEN-31.

### OPEN-28 — amend, and correct its central claim

**Join, `t08_all_modes_eui.csv` × `t20_layout_assign_eui.csv`:** shared **4,530**, T08-only **0**,
T20-only **3,630**, union **8,160**. T08 is a strict subset of T20.

**Archetype agreement 86.60%** (3,923/4,530) — **13.40% disagree.** Top pair
`MediumOffice → SmallOffice`, n=396. Root cause traced and reproduced from the historical blob:
commit **`0df422e`** (2026-07-03, "classification thresholds updates") changed the shared
`05_results.gpkg` fixture between the two harvests.

**Floor-area agreement 100%** (4,530/4,530 within 1%). Only the archetype drifted.

**Correction to this item's central claim.** The register frames OPEN-28 as *"`layout_assign` is T20."*
For the **published −29.1% figure that specifically is wrong.** Per
`OpenUBEM_results_LayoutAssigner.md:422-423,449-458`, that figure's `layout_assign` side is **T19**,
not T20; the `auto` side is T08. The join above therefore **does not describe the population the
published −29.1% was computed over.** The register recorded this as *"not established"*; it is now
established, and it is a third generation, not a second.

**Convergence worth recording.** M04 and M05 were executed by separate agents with no shared context
and both independently identified commit `0df422e` — one as the point the accuracy metric settled,
the other as the cause of the fleet-scale reclassification. Neither knew of the other's finding.

### OPEN-08 — amend

The confound is no longer unquantified. Cross-generation archetype disagreement between T08 and T20
is **13.40%** on 4,530 shared buildings (M05). Vintage disagreement remains unquantifiable — see
OPEN-30.

---

## C. New items

### OPEN-30 — Assigned vintage is never persisted by any harvest ✅
*Added 2026-08-05, from M05.*

Neither `t08_all_modes_eui.csv` nor `t20_layout_assign_eui.csv` — nor their shared provenance file
`05_results.gpkg` at either git state — carries a `vintage_standard` column. `resolve_vintage()`
(`openubem/semantic/construction_sets.py:126`) produces the token, `envelope_patcher` consumes it,
and it is then discarded.

**Consequence.** Vintage agreement between harvest generations cannot be checked now, and could not
have been checked at any past point either. This is not a gap in the comparison — it is a gap in what
was ever recorded. It also blocks OPEN-03 from being bounded against the fleet's real vintage
distribution rather than a proxy.

**First measurement:** none needed; the absence is verified. **Decision owed:** whether to persist the
token on future runs — one column, and the re-run already approved in principle is the natural place.

### OPEN-31 — Ratified changes are adopted without a before/after on the labelled fixture ✅
*Added 2026-08-05, from M04 + M05.*

E-R3-3 was ratified and adopted. It cost **4 points** of fine top-1 accuracy and reclassified
**13.4%** of the fleet's shared buildings, and neither effect was measured against its predecessor at
adoption time. Both surfaced weeks later, separately, in unrelated investigations.

**This is a process defect, not a code defect.** No line of code is wrong.

**Decision owed (CP-M3):** whether a ratified classification change must carry a before/after on the
50-row labelled fixture before adoption.

### OPEN-32 — Two large `layout_assign` errors point in opposite directions; the net is unmeasured ✅
*Added 2026-08-05, from M01 + M03.*

OPEN-01 inflates the numerator relative to the denominator for 87.4% of buildings (median ×2.0).
OPEN-03 deflates the numerator by modelling loads at a code year newer than 92.9% of the fleet
(lighting ratio ≥1.72×). **They oppose each other, and their net effect has never been computed.**

A `layout_assign` EUI could be approximately correct while both of its inputs are substantially
wrong — which is a weaker footing than a number that is right component-wise, because the
cancellation is coincidental and will not hold under any change to either mechanism.

**Explicitly not claimed:** that the adopted fleet baseline (~~158.0~~ **157.1 kWh/m²** (pooled: total
simulated energy ÷ total simulated floor area; the struck figure was a count-weighted mean of the 12
cell means, superseded 2026-08-12, OPEN-43)) is affected. OPEN-01 item 3
— *whether any adopted result depends on `layout_assign`* — is **still unmeasured**, and register
line 148 requires it be confirmed rather than assumed. **That confirmation is this item's first
measurement**, and it is cheap.

---

## D. §9 pattern 1 — amend

Currently: *"Four items (OPEN-01, 02, 03, 04) can make already-published numbers wrong."*

All four are now measured. Proposed replacement:

> **All four items that could make already-published numbers wrong have been measured (2026-08-05).**
> Two are confirmed large and unremediated (OPEN-01, OPEN-03). One is confirmed cheap to fix and
> approved in principle (OPEN-02). One turned out not to be a metric defect at all (OPEN-04) and has
> been re-cast as a process defect (OPEN-31). Three new items were opened by the measurements
> themselves (OPEN-30, OPEN-31, OPEN-32) — the expected outcome of measuring rather than planning.
> **Next free ID: OPEN-33.**
