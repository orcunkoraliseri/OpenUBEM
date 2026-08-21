# MEASUREMENT — OPEN-38: what actually killed the 44

> T04 of `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_ten-live-items-2026-08-20-evening.md`.
> This is the item's own named first measurement, quoted verbatim in book I §OPEN-38, run here
> for the first time. Measurement only — no remedy proposed.

## 1. Population and scope

Corpus: `C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest` — the E02 harvest, 40,800
`eplusout.err` files across five cities x four zones x five modes (`auto`, `building`,
`fast_zone`, `floor`, `layout_assign`). Fatal test is the two-space form `**  Fatal  **`
(the one-space form is the OPEN-45 defect and finds nothing, per F9/OPEN-45).

Script: `scripts/analysis/open38_fatal_cause_census_2026-08-20.py`.
Outputs: `openubem/outputs/comparisons/open38_fatal_causes_2026-08-20.csv` (44 rows, one per
fatal building) and `openubem/outputs/comparisons/open38_la_rural_intersection_2026-08-20.csv`
(11 rows, one per `la_rural` stem that fails in at least one of `fast_zone`/`auto`/`floor`).

## 2. C11 — file count

**44 of 44** `.err` files carry the two-space `**  Fatal  **` marker, matching F9's headline
count exactly.

F9 also states "44 fatal `.err` + 1 missing `.end` = 45 = `sacct` FAILED". Within this corpus,
875 directories are missing `eplusout.end` overall (matches F8's harvest-custody shortfall,
OPEN-53's population) — but **none of the 44 fatal directories are among them** (every fatal run
still wrote its `.end` file; checked directly). The specific "1 missing-`.end`" building that
F9 counts as the 45th `sacct`-FAILED member cannot be told apart, from local disk alone, from
the other 874 harvest-custody-missing directories that OPEN-53 already tracks — that requires
`sacct` status data, which is T05's scope, not T04's. This is reported as a scoping boundary,
not a failed control: the 44-fatal number the intersection depends on is exact, so the task
proceeds per C11's instruction (stop only if the fatal count itself does not match).

## 3. C12 — severe-message classes

Every one of the 44 fatals is assigned to exactly one severe class (captured from the last
`** Severe **` line in the 5 lines preceding the `**  Fatal  **` line, or the first `** Severe **`
line in the file if none falls in that window); **`no_preceding_severe` count is 0** — every
fatal has an identifiable preceding severe message, stated here as the headline number the plan
requires, not a footnote.

| Class | Count |
|---|---|
| `Temperature (high) out of bounds <BOUND> for zone=<ZONE> for surface=<SURFACE>` | 21 |
| `CalcHeatBalanceInsideSurf: The temperature of <NUM> C for zone=<ZONE> for surface=<SURFACE>` | 17 |
| `Temperature (low) out of bounds <BOUND> for zone=<ZONE> for surface=<SURFACE>` | 5 |
| `DetermineShadowingCombinations: There are <NUM> surfaces which are casting surfaces and are non-convex.` | 1 |

38 of 44 (86%) are a temperature-bounds/heat-balance divergence class (the first three rows
combined); 1 is a geometry-shadowing warning escalated to fatal. Per rule 1, this finding is
reported as-is — no cause is diagnosed further and no fix is proposed.

## 4. C13 — the `la_rural` cross-mode intersection (decisive)

11 distinct `la_rural` stems fail (carry a fatal) in at least one of `fast_zone` (10), `auto`
(7), `floor` (7). Of those 11, **6 of 11 buildings fail in all three modes**
(`way_472960972`, `way_472961034`, `way_472961047`, `way_472961088`, `way_472961091`,
`way_472961171` — see `open38_la_rural_intersection_2026-08-20.csv`).

**The evidence selects the "same buildings" branch, but only partially.** A majority (6 of 11,
55%) of `la_rural`'s failing stems fail identically across all three geometry modes, which is
consistent with a per-building input-data cause independent of geometry pipeline. The remaining
5 of 11 fail in only one or two modes (3 in `fast_zone` only, 1 in `auto` only, 1 in
`fast_zone`+`floor`), which is not explained by the same mechanism. Per rule 1 and C13's instruction, no remedy is written
either way; the item's next step is the user's to name, informed by this split rather than a
single verdict.

## 5. Denominator statement (D5)

Population: all 40,800 `.err` files in the E02 harvest corpus. Fatal population: 44/40,800.
`la_rural` cross-mode population: 11 stems observed failing in `{fast_zone, auto, floor}`
(denominator for the intersection is these 11, not all `la_rural` buildings).
