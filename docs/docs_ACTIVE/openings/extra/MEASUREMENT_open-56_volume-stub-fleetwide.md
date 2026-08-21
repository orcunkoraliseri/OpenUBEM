# MEASUREMENT — OPEN-56: the volume stub, counted exactly, fleet-wide

Corpus: `evidence/open48_refleet4/*/sim_out/*/eplusout.eio`, 8,160 files, 100% coverage. Script:
`scripts/analysis/open56_volume-stub-fleetwide_2026-08-21b.py`. Outputs:
`openubem/outputs/comparisons/open56_volume-stub-zones_2026-08-21b.csv` (46,127 zone rows),
`openubem/outputs/comparisons/open56_volume-stub-buildings_2026-08-21b.csv` (8,159 building rows).

## C3 — reproduction

`nyc_urban/relation_17949119`, zone `RELATION/17949119_F0_WHOLE`: Ceiling Height 3.50, Floor Area
2343.46, Volume 10.00 — reproduced exactly.

## Zone-level result

46,127 zones parsed from 8,160/8,160 `.eio` (all carry the `Zone Information` header). **42,269 of
46,127 zones (91.64%) have `volume == 10.0` exactly.** Per-zone `volume_ratio` (built/expected)
distribution: min 0.0000, p10 0.0027, p25 0.0108, median 0.0245, p75 0.0633, p90 0.6918, max 5.4945.

## C4 — building-level count, against the register's 8,160/8,160 claim

Buildings are grouped from sim directories, merging `_part0`/`_part1` pairs to one `osm_id`
(1 building, `nyc_urban/relation/17953040`, is such a pair) — **8,159 distinct buildings**, not
8,160, from 8,160 sim directories.

- **Buildings with ANY stubbed zone: 8,159 / 8,159 (100%)** — every building has at least one
  volume==10.0 zone.
- **Buildings with ALL zones stubbed: 7,769 / 8,159 (95.22%)**, not the register's claimed
  8,160/8,160. The register's figure appears to describe "any stub" (which is universal), not "all
  zones stubbed" (which is not). Report as-is; no correction proposed.
- Buildings with some-but-not-all zones stubbed: 390 / 8,159. Buildings with no stub at all: 0.

## C5 — fleet volume ratio

Σ as-built volume = 11,477,577.85 m³; Σ expected volume (floor_area × ceiling_height) =
85,704,214.36 m³. **Fleet volume ratio (built/expected) = 0.133921.**

## Root cause visible in `.err`

`Indicated Zone Volume <= 0.0 for Zone=<Z> ... The calculated Zone Volume was=<negative> ... set to
10.0 m3` — the stub is EnergyPlus's own fallback for a negative computed geometric volume, not an
estimate.
