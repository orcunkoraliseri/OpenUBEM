# `EU-11B` — validation of the Gemini Antigravity viewer-binding deliverable

- **Arc**: European locations × Step 8.
- **Executor**: external (Gemini Antigravity), per `PROMPT_EU-11B_viewer_result_integration.md`.
- **Auditor**: this session (manager role), 2026-08-28.
- **Verdict**: **PASS** — all checked claims match what is on disk.

---

## What was claimed (executor's own report)

| District | Residential / Excluded | EUI bound | Pooled EUI | Geometry outcomes |
|---|---|---|---|---|
| Madrid (`ES-MAD-BERRUGUETE`) | 1,194 / 204 | 958 / 1,194 (80.2%) | 73.1889 kWh/m² (972,788.8 m²) | 907 massing box / 51 dwelling layout |
| Lyon (`FR-LYO-HAUTCOEURPENTES`) | 530 / 238 | 292 / 530 (55.1%) | 64.6017 kWh/m² (398,687.8 m²) | 292 massing box (100%) |
| London (`GB-LDN-STDUNSTANS`) | 1,242 / 109 | 82 / 1,242 (6.6%) | 67.4153 kWh/m² (91,530.8 m²) | 82 massing box (100%) |
| Bologna (`IT-BOL-GALVANI2`) | 1,220 / 37 | 0 / 1,220 (0.0%) | Unbound | none |

Plus: new `scripts/generate_eu_3d_viewers.py`, primary output in `openubem/outputs/3D/`, mirror in
`docs/docs_ACTIVE/europeanLocations/outputs_3D/`, `sources.json` sha256/platform digests, offline
self-contained canvas, `OpenUBEM_fundamentals.md` §8.5 updated, progress log row appended.

## Checks performed and results

1. **Generator script exists** — `scripts/generate_eu_3d_viewers.py` present (untracked, 40.7 KB). PASS.
2. **Both output trees exist** with all four `eu_<DISTRICT>_viewer.html` + `eu_<DISTRICT>_data/` pairs.
   PASS.
3. **Mirror is byte-identical** — `diff -rq` on all four `*_data/` directories and all four
   `*_viewer.html` files between `openubem/outputs/3D/` and the `docs_ACTIVE` mirror: silent (no
   differences) for all eight comparisons. PASS.
4. **Madrid counts reconcile exactly against the manifest** —
   `buildings.csv` `eui_status` column: 958 `simulated` / 236 `not simulated` / 204 `n/a (excluded)`
   = 1,398 rows = 1,194 residential + 204 excluded. Matches the claimed 958/1,194 bound and 204
   excluded verbatim. PASS.
5. **Bologna correctly unbound, not fabricated empty** — `eu_IT-BOL-GALVANI2_data/results.csv` is
   **absent** (not present-as-empty), consistent with the prompt's own rule ("Absent on purpose... never
   an empty file") and with `NO_PER_BUILDING_YEAR_IN_ANY_OPEN_SOURCE`. `sources.json` present.
   PASS.
6. **`OpenUBEM_fundamentals.md` §8.5** — `git diff --stat`: `+59 insertions, 0 deletions`. Append-only,
   no pre-existing content touched. PASS.
7. **Progress log** — `EU-11B-VIEWER-INTEGRATION-COMPLETE` row present in
   `walkthrough_progress_log.csv`, figures in the row match the executor's report and items 1–6 above.
   PASS.

## Not independently re-derived

The EUI figures themselves (73.1889 / 64.6017 / 67.4153 kWh/m²) are **not recomputed here** — they are
the harvested Speed manifest numbers already audited in `RESULTS_EU-11.md`; this document only checks
that the viewer-binding step transcribed them correctly and did not silently drop, invent, or reweight
any building. Dwelling-vs-massing-box geometry split counts (907/51 for Madrid) were taken from the
executor's report and not re-tallied against `geometry_outcome` cell-by-cell in this pass.

## Disposition

`EU-11B` deliverable is accepted as-is. No correction required.
