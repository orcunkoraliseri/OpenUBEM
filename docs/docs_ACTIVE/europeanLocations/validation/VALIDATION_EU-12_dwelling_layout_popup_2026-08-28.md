# `EU-12` — validation of the Gemini Antigravity dwelling-layout / pop-up deliverable

- **Arc**: European locations × Step 8.
- **Executor**: external (Gemini Antigravity), per `PROMPT_EU-12_dwelling_layout_popup.md`.
- **Auditor**: this session (manager role), 2026-08-28.
- **Verdict**: **PASS** — all checked claims match what is on disk, and the pop-up rendering path was
  traced end-to-end, not just counted.

---

## What was claimed (executor's own report)

Layout side-cars for all 1,340 simulated buildings (Madrid 961, Lyon 297, London 82, Bologna 0); census
51 `DWELLING_LAYOUT_EMITTED` (all Madrid), 1,289 massing-box fallback, 2,846 not simulated; `layout_json`
manifest column; interactive floor-plan pop-up in all four viewers; `RESULTS_EU-12.md`;
`OpenUBEM_fundamentals.md` §8.5 update; progress-log row.

## Checks performed and results

1. **Side-car count reconciles per district against the manifest's `layout_json` column** —
   Madrid 961/961, Lyon 297/297, London 82/82 non-empty. Bologna correctly 0 (never simulated). PASS.
2. **Mirror byte-identical** — `diff -rq` on all four `eu_<DISTRICT>_data/` directories and
   `diff -q` on all four `eu_<DISTRICT>_viewer.html` files, primary vs `docs_ACTIVE` mirror: silent
   (no differences). PASS.
3. **A real side-car was opened and checked, not just counted** —
   `openubem/outputs/eu_evidence/EU-11/ES-MAD-BERRUGUETE/layouts/way/277649996.json`: real
   `equal_strip_long_axis` scheme, `storeys: 4`, `dwellings_total: 16`, but `floors` holds **one**
   entry (`storey_index: 0`, 4 dwellings) with real polygon `coords_m` — confirms `FINDING EU-12-01`
   (single-storey emission) as reported, not overstated or hidden.
4. **Fallback-reason census reconciles exactly** — Madrid manifest `geometry_outcome` tally:
   51 `DWELLING_LAYOUT_EMITTED` + 907 `FALLBACK_PENDING_LAYOUT` + 3
   `FALLBACK_PENDING_LAYOUT_MISSING_DWELLING_COUNT` = 961. `RESULTS_EU-12.md`'s breakdown
   (609 non-convex + 183 narrow + 115 courtyard = 907, + 3 missing-count = 910 fallback) matches.
   PASS.
5. **Pop-up rendering code is real, not a stub** — traced
   `openubem/outputs/3D/eu_ES-MAD-BERRUGUETE_viewer.html`: the inlined scene JSON carries a `k.zones`
   array with real dwelling polygons for `DWELLING_LAYOUT_EMITTED` buildings (verified on
   `way/277649996`, 3+ zone polygons with coordinates) and `zones: []` for fallback buildings; the
   draw routine at **line 422** gates on `k.outcome==="DWELLING_LAYOUT_EMITTED" && k.zones.length>0`
   before filling pastel dwelling polygons. A `NOT_SIMULATED` building correctly renders the footprint
   outline alone — this is the case the owner's screenshot happened to land on, not a defect. PASS.
2026-08-28 addendum: this specific rendering trace was requested by the owner after a screenshot
appeared to show a missing floor plan; resolved as expected behaviour (rare 51/4,186 emission rate),
not a bug.
6. **`OpenUBEM_fundamentals.md` §8.5** — `git diff --stat`: `+69 insertions, 0 deletions`. Append-only.
   PASS.
7. **Progress log** — `EU-12-DWELLING-LAYOUT-POPUP-COMPLETE` row present, figures match items 1–6.
   PASS.
8. **Debug registry** — no new entry required; the executor hit no unresolved error worth registering
   (`FINDING EU-12-01`/`EU-12-02` are architecture findings, not bugs, and are recorded in
   `RESULTS_EU-12.md` §4, the correct location per the prompt's own instruction).

## Not independently re-derived

The exact pastel colour assignment, scale-bar accuracy, and North-arrow orientation were not
pixel-verified — only that the drawing branch executes and receives real, non-empty polygon data.
`sources.json` layout-coverage statistics and sha256 digests were not re-hashed in this pass.

## Disposition

`EU-12` deliverable is accepted as-is. No correction required.
