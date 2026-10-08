# MEASUREMENT — the adopted run's own `.err` census, at 100% coverage

Corpus: `evidence/open48_refleet4/*/sim_out/*/eplusout.err`, 8,160 files. Script:
`scripts/analysis/open38-09-45_err-census-fleetwide_2026-08-21b.py`. Output:
`openubem/outputs/comparisons/open38-09-45_err-census-buildings_2026-08-21b.csv` (8,160 rows).

## C12 — file count

**8,160 / 8,160 `.err` files read. No shortfall.**

## Fatal / Severe / Warning census

- Two-space `**  Fatal  **` marker: **7 / 8,160** files.
- `** Severe  **` (two-space) occurrences, fleet-wide total: **110**.
- `** Warning **` (one-space) occurrences, fleet-wide total: **339,168**.
- All 7 fatal files have an identifiable preceding severe (0/7 `no_preceding_severe`), using the
  predecessor's rule: last `** Severe  **` in the 5 lines before `**  Fatal  **`, else the first
  severe in the file.

## C13 — OPEN-09 signature

Exact string `Inside surface heat balance did not converge`: **16 / 8,160** files. Reproduces the
register's 16 exactly.

## Severe-message classes (26 files carry >=1 severe; class assigned per file, normalized)

| Class | Count / 26 |
|---|---|
| `DetermineShadowingCombinations: There are <NUM> surfaces which are casting surfaces and are non-convex.` | 19 |
| `Temperature (low) out of bounds <BOUND> for zone=<ZONE>, for surface=<SURFACE>` | 6 |
| `CalcHeatBalanceInsideSurf: The temperature of <NUM> C for zone=<ZONE>, for surface=<SURFACE>` | 1 |

This is the adopted run's own error profile, at 100% coverage — not the harvest's 5-geometry-mode
corpus. Per F2, prior claims quoting harvest-only percentages (OPEN-38's 86%, etc.) are not
generalisable to this run and are not restated here.
