# I04 — Candidate fix shapes synthesis

Synthesis only. No code written, no data pulled, nothing executed for this task. Every claim below
traces to I01, I02, I03, or a plan §4 fact (F-0x). **Every option in this document is a candidate,
not an adoption decision** — the follow-up Stage-1 implementation plan owns the choice.

## Ranked table

| rank | option | effort | risk | scope (Stage 6 only / whole platform) | supporting evidence (I01/I02/I03) | verdict |
|---|---|---|---|---|---|---|
| 1 | **(b) Ingest external dataset — Microsoft Global ML Building Footprints** | Medium — one-off enrichment script per tract: download quadkey tile(s), spatial-join polygons onto existing OSM footprints, carry over `height_m` where present (I02) | Medium — CDLA Permissive 2.0 license is clean and access is unauthenticated bulk download (I02), but the height *sub*-layer's actual density at these 4 exact bounding boxes is unverified without downloading, which this plan could not do (I02 "what could not be assessed") | Whole platform — enriches `height_m` itself, upstream of Stage 6, IDF generation (F-03), and any other consumer | I02: only candidate that is boundary-independent by construction, which directly answers I02's load-bearing finding that `nyc_suburban`/`nyc_rural` sit outside NYC's five boroughs and `austin_rural` sits outside Austin city limits — municipal-portal candidates (NYC Open Data, City of Austin) are geographically inapplicable to 3 of the 4 tracts for this exact reason | **candidate — not adopted** |
| 2 | **(f) [added] Wire `impute_column`'s existing KDE path for partially-missing cells (austin_centre-class only)** | Low — I03 shows this already works today, zero new code, calling the existing `"auto"` dispatch is sufficient for any column that is *not* 100% missing | Low-medium — fills 349/349 rows in `austin_centre`, but I03 is explicit that this is "a purely non-spatial, single-column distributional fill" with "no spatial reasoning, no confidence tiering, no MNAR awareness at all" — quality is real but shallow | Stage 6 only in practice — nothing currently calls `impute_column` for `height_m` in production (F-04), so wiring it would be a narrow, targeted change scoped to unblock the microclimate domain module, not a platform-wide enrichment | I03: `impute_column(method="auto")` resolves to `kde` (not `pde`) at 84.5% missing because `nan_mask.all()` is `False`, and fills 100% of `austin_centre`'s gap today with no structural change needed; explicitly **does not** apply to the 3 fully-NaN cells, which hit the `pde` branch and raise `ValueError("...bounds must be provided...")` | **candidate — not adopted** |
| 3 | **(d) Widen `spatial_impute.py`'s donor pool across cell boundaries (structural, not "raise a constant")** | High — I03 is explicit this is *not* a radius-parameter tweak. `knn_fill` filled **exactly 0** rows in the 3 fully-NaN cells at 100/250/500/1000 m because "every neighbour is also 100% missing by construction" (I03 radius-sensitivity probe). A real fix requires the donor pool to cross the cell's own `GeoDataFrame` boundary (F-06/F-07: `spatial_impute.py` is invoked per-cell, one `GeoDataFrame` at a time) — i.e. a new cross-cell/cross-cluster donor-admission mechanism, plus a decision on how the MNAR guard interacts with a multi-cell pool | High — once cross-cell pooling exists, donor selection must still respect zone-type/fabric similarity or it silently imports the wrong building typology (see I01's per-cell `building_tag` profiles: `la_rural` is `yes:113/industrial:14/warehouse:11`-dominated vs. Hill-Country `austin_rural`'s `yes:185/retail:21/commercial:11/semidetached_house:9`-dominated mix — cross-city "rural" donors are not fabric-equivalent). Also inherits **E-UTCI-10** (silent no-donor rows, §8 of the plan) as an adjacent, still-open diagnostics gap in the same module | Whole platform, if ever wired into production — it is a change to `spatial_impute.py` itself, currently unwired anywhere (F-05), so the immediate scope is "make the module *capable of* fixing this," not an automatic platform-wide effect until a call site adopts it | I03 §"Verdict": "Widening the radius alone cannot fix this... crossing into a different cell's data... is a different, larger design change than 'wire up the existing imputer'" and states this is "necessary, not just one option among several, for these 3 cells" | **candidate — not adopted** |
| 4 | **(c) Regional/cell-level statistical fallback — borrow median height from nearest "good" cell of the same zone-type, low-confidence flagged** | Low — no new ingestion, no new external license, a lookup against I01's own already-computed per-cell statistics | High — same cross-fabric mismatch risk as (d) above, arguably worse because it is a single point-value borrow with no per-building spatial reasoning at all: e.g. the only "good" `rural` cell is `la_rural` (0.671% NaN, footprint mean 509 m²) — borrowing its median height for `nyc_rural` (Catskills) or `austin_rural` (Texas Hill Country) crosses three different regional building stocks. For `suburban`, the good donors are `la_suburban` (1.117%) and `austin_suburban` (26.087%) — again cross-city relative to `nyc_suburban` (Long Island) | Stage 6 only — this is a targeted unblock for the microclimate domain module's hard `.notna()` filter (F-06); it does not need to write back into the platform's canonical `height_m` column, since other stages already have their own independent fallback that does not require `height_m` to be filled (F-03: `_impute_levels`/`derive_num_floors` default to group-median or flat 1 storey directly, never reading a borrowed value) | I02 independently flags `GHS-BUILT-H` (100 m grid, neighbourhood-average height, global, boundary-independent) as mapping directly onto exactly this candidate shape ("maps directly onto I04 candidate (c), not candidate (b)") — a possible *external* donor for the median-borrow instead of a cross-cell platform-internal one | **candidate — not adopted** |
| 5 | **(a) Targeted OSM re-fetch (post-§5.3-unblock or scoped exception)** | Low code effort — F-07 confirms the acquisition code path is identical for all 12 cells (`ingest_buildings`, same function, different coordinates only); no new pipeline code needed, just re-running an existing call | High procedural/payoff risk — gated behind CLAUDE.md's live-network rule (F-09) until §5.3 unblocks or a scoped one-off exception is separately granted, which is itself outside this plan's or a Stage-1 plan's unilateral control. Payoff is also uncertain: F-07 states "the differential coverage is a function of live OSM community-tagging density... not a code defect" — a re-fetch today may return the same near-total gap if community tagging in these tracts has not changed since the original fetch | Whole platform, and highest-fidelity if it succeeds — a real re-observed OSM `height` tag flows through the exact same F-01/F-02/F-03 pipeline as every other building, with no new code path to maintain | F-01/F-07: acquisition is a direct, unconditional pass-through of the raw OSM tag with no DSM/LiDAR fallback; F-09: the gate is real and not this plan's to lift | **candidate — not adopted** |
| 6 | **(e) Accept and permanently document as a known Stage-6 limitation** | Near zero — documentation only, no code | Low technical risk, but a standing quality cost: the 3 fully-NaN cells keep reporting `svf_mean = 1.0000` (a flat open field) indefinitely for however long this option alone stands (plan Executive Summary) | Stage 6 only — by construction, this changes nothing upstream; it only formalizes what F-06 already does today (hard-exclude and report `n_excluded_no_height`) | F-06: Stage 6 is already the only hard-exclusion point in the pipeline and already reports the exclusion rather than silently masking it — this option is a documentation ratification of existing, correct behaviour, not a new mechanism | **candidate — not adopted** |

## Per-option notes

**(a) Targeted OSM re-fetch.** The code-side lift is genuinely trivial — F-07 shows every one of the
12 cells already goes through the identical `ingest_buildings` call, so "re-fetch" is operationally
just re-running that call for 4 coordinate pairs. The real cost is procedural (the §5.3 gate, F-09)
and probabilistic (F-07's point that today's gap reflects live community-tagging density, which a
re-fetch cannot force to be higher). It is the only option that fixes the gap at its true root — the
missing OSM `height` tag itself — with zero new pipeline surface area, which is why it ranks on
fidelity even though its gate makes it slow to act on. **Candidate — not adopted.**

**(b) Ingest an I02 external dataset.** Microsoft Global ML Building Footprints is the standout
candidate specifically because I02's load-bearing geographic finding — `nyc_suburban`/`nyc_rural` and
`austin_rural` sit outside their namesake municipal boundaries — rules out every boundary-scoped
candidate (NYC Open Data, City of Austin) for 3 of the 4 tracts regardless of those datasets' data
quality. Microsoft's coverage is nationwide by construction, so it does not care about the boundary
mismatch. The residual uncertainty (does the height *sub*-layer actually land inside these 4 specific
boxes?) is real and unresolved by desk research alone (I02), but it is a "download one tile and check"
question, not a structural blocker. USGS 3DEP / TNRIS StratMap are viable alternates but I02 rates them
a materially heavier lift (new point-cloud → DSM/DTM-difference → footprint-join ingestion module,
not a tabular join). **Candidate — not adopted.**

**(c) Regional/cell-level statistical median borrow.** Cheapest option on paper, but I01's own
per-cell `building_tag` and footprint-area tables (cited above) show that "same zone-type" is not the
same as "same building stock" once the borrow crosses cities — `la_rural` is the only good `rural`
donor and its fabric (industrial/warehouse-heavy, footprint mean 509 m²) has little in common with
`nyc_rural` (Catskills) or `austin_rural` (Hill Country, footprint mean 631 m²). This option is
strongest when explicitly low-confidence-flagged, exactly as the plan's option text requires, and is
structurally closer to option (d) than its surface simplicity suggests (see Prerequisites below) —
one could view (c) as "(d) done manually, at the cell/scalar level, instead of at the per-building/
spatial-index level." I02 separately surfaces `GHS-BUILT-H` as an *external* variant of this same
shape (a global 100 m-grid neighbourhood-average height, boundary-independent) rather than an
internal platform-only borrow. **Candidate — not adopted.**

**(d) Widen the spatial-impute donor pool across cell boundaries.** I03's radius-sensitivity probe is
the single most important piece of evidence against treating this as a quick fix: `n_filled` stayed
at exactly 0 for `nyc_suburban`, `nyc_rural`, and `austin_rural` at 100 m, 250 m, 500 m, and 1000 m —
every neighbour found at any tested radius was itself 100% missing on `height_m`, "by construction"
(I03). The radius parameter alone converts silent-no-donor rows into MNAR-blocked rows; it does not
manufacture donor signal that does not exist within the cell. A real version of this option requires
`spatial_impute.py` (or its caller) to admit donors from *other* cells/clusters of a compatible
zone-type — a genuinely larger, structural change to a module that today operates strictly per-cell
(F-06/F-07). I03 calls this change "necessary, not just one option among several" for the 3 fully-NaN
cells specifically — meaning if the eventual fix path runs through "wire up the existing imputer" at
all, this structural change is not optional, it is the precondition. This option also inherits
E-UTCI-10 (the silent no-donor blind spot, plan §8) as an adjacent defect in the same module that a
future implementer would likely want to close alongside it, though the two are logically separable.
**Candidate — not adopted.**

**(e) Accept and document.** The cheapest option and, notably, not really a "fix" — it is a ratification
of what F-06 already does today (Stage 6 already hard-excludes and reports the exclusion rather than
silently masking it). Its cost is a standing, indefinite quality gap in `svf_mean`/UTCI outputs for
these 4 tracts specifically, which is acceptable only if those tracts are known to be low-priority for
downstream users of Stage 6's outputs — a product/scoping judgement outside this investigation's remit.
It is the natural fallback position if none of (a)-(d) clear their respective bars (procedural gate,
unverified external coverage, cross-fabric risk, or engineering cost). **Candidate — not adopted.**

**(f) [added, not one of the plan's named five] Wire `impute_column`'s existing KDE path for the
`austin_centre`-class case.** I03 found this already works today with literally zero new code: at
84.5% missing (not 100%), `impute_column("auto")` resolves to the `kde` branch instead of the `pde`
branch and successfully fills all 349/413 rows from the 64 real observed `height_m` values in that
same cell — no exception, no bounds argument needed (unlike the `pde` branch, which raises
`ValueError` for the 3 fully-NaN cells). This is genuinely the cheapest lever available for any
future *partially*-missing cell of `austin_centre`'s shape, but I03 is explicit about its shallowness:
"no spatial reasoning, no confidence tiering, no MNAR awareness at all" — a distributional resample,
not a spatial inference. It is added here because I01-I03's own evidence shows it is qualitatively
different in cost/risk from every other option and specific to the one cell (`austin_centre`) that is
not 100% missing — folding it into (c) or (d) would obscure that it needs no structural change at all,
unlike either of those. **Candidate — not adopted.**

## Prerequisites and combinations

- **(d) is a precondition of "wire up the existing imputer" ever working for the 3 fully-NaN cells** —
  not an independent alternative to that broader idea. I03's radius probe forecloses "radius alone"
  as a fix; the structural cross-cell-boundary change *is* what "wire up the existing imputer" would
  have to mean for these 3 cells. There is no lighter-weight version of "make `spatial_impute.py` work
  here" that skips (d).
- **(c) does not strictly depend on (b)**, but the quality of (c)'s donor pool improves if (b) lands
  first: today's "good" cells are all sourced from the same OSM fetch (F-07) and carry the same kind
  of community-tagging variance across cities that created the gap in the first place (I01's
  cross-city fabric mismatch, discussed under (c) above). If (b) enriches even the "good" cells'
  `height_m` coverage or corroborates it against an independent source, a subsequent median-borrow in
  (c) would be resting on more trustworthy donor values. This is a sequencing preference, not a hard
  gate — (c) is executable today with zero dependency on (b).
- **(b) and (a) are the only two options that touch `height_m` at (or near) its source**, and are
  mutually reinforcing rather than competing: a successful (a) re-fetch for a tract makes (b)'s
  enrichment for that same tract unnecessary, and vice versa. Running both is not wasteful risk-hedging
  so much as attacking the same fields from two independent sources and keeping whichever resolves
  more tracts; I02 already flags exactly which tracts (b) can plausibly reach (all 4, pending
  per-point height-density verification) versus which (a) can reach (all 4, pending the §5.3 gate and
  a re-tagging-density gamble).
- **(f) has no dependency on any other option** — it is self-contained, cheap, and only applicable to
  `austin_centre`'s partially-missing shape. It could be adopted in isolation regardless of what (if
  anything) is later decided for the 3 fully-NaN cells.
- **(e) is not mutually exclusive with anything** — it is the natural "in the meantime" position for
  whichever tracts remain unresolved after any subset of (a)-(d)/(f) is pursued, and could reasonably
  be adopted immediately (zero cost, zero risk) while a heavier option is scoped and built.
- **Strongest plausible combination given the evidence:** (b) attempted first for all 4 tracts
  (boundary-independent, moderate effort, whole-platform scope) + (f) applied immediately to
  `austin_centre` (already works today, zero engineering) + (e) documenting whatever residual gap
  survives both, for whichever of the 3 fully-NaN tracts (b) does not resolve. (d) and (c) remain
  live options if (b) turns out not to cover the height sub-layer for the 3 fully-NaN tracts once
  actually checked — but that check itself falls outside this investigation.

## One-fix-for-all vs. split strategy

The evidence does not support a single fix shape for all 4 tracts. I03 is explicit that
`austin_centre` "behaves differently from the other three" — it is 84.5% missing, not 100%, has 64
real observed `height_m` values to draw on, and is *already* partially or fully fillable today with
zero structural change via `knn_fill` (15/349) or `impute_column`'s KDE path (349/349) respectively.
None of that machinery does anything for the 3 fully-NaN cells (I03: 0 filled at every tested radius;
`impute_column` raises outright). A **split strategy** — a lightweight, near-term fix for
`austin_centre` (option (f), or (d)/(c) if a spatial/statistical approach is preferred there instead)
paired with a heavier-weight or externally-sourced fix for the 3 fully-NaN cells (option (b), (a), or
the structural version of (d)) — is what I01-I03's evidence actually points toward. A one-fix-for-all
approach would either overengineer `austin_centre`'s case (building the cross-cell donor-pool
machinery of (d) for a cell where the existing non-spatial KDE path already reaches 100% fill) or
underserve the 3 fully-NaN cells (applying only `austin_centre`-class tooling, i.e. (f), to cells where
that tooling structurally cannot produce a fill at all, per the `ValueError` in I03).
