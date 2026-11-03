# `EU-11B` — Executor prompt: bind the `EU-11` results into the four district 3D viewers

- **Arc**: European locations × Step 8. Runs **after** [`PROMPT_EU-11_full_district_campaign_speed.md`](PROMPT_EU-11_full_district_campaign_speed.md) has produced its manifests.
- **Executor**: external (Gemini Antigravity). **Paste everything below the rule into the tool.**
- **Date of prompt**: 2026-08-28.

---

## Task (paste from here)

You are binding the `EU-11` simulation results into the four European district viewers of the OpenUBEM
repository `C:\Users\o_iseri\Desktop\OpenUBEM`. Python is **`.venv/Scripts/python.exe`**. Git is handled
externally: **never commit and never stage.**

### 1. What exists today

Four self-contained offline viewers, canonical copies in `openubem/outputs/3D/` and byte-identical mirrors
in `docs/docs_ACTIVE/europeanLocations/outputs_3D/`:

```
eu_ES-MAD-BERRUGUETE_viewer.html      + eu_ES-MAD-BERRUGUETE_data/
eu_FR-LYO-HAUTCOEURPENTES_viewer.html + eu_FR-LYO-HAUTCOEURPENTES_data/
eu_GB-LDN-STDUNSTANS_viewer.html      + eu_GB-LDN-STDUNSTANS_data/
eu_IT-BOL-GALVANI2_viewer.html        + eu_IT-BOL-GALVANI2_data/
```

Each page embeds its scene as JSON in `<script type="application/json" id="scene">` and already carries a
**complete EUI channel**: a `colour: EUI` mode, a two-handle range filter, a legend, a per-building tooltip
and a `Data folder` link. The channel is driven by three payload fields — `eui_bound` (bool), `eui_note`
(HTML shown in the filter panel) and `warn_html` (the HUD banner) — plus, per building, `e` (EUI) and `g`
(geometry outcome). Today `FR-LYO-HAUTCOEURPENTES` is bound on **31 of its 530** buildings from
`s2_campaign_v3_manifest.csv`; the other three are unbound and say so.

The documented contract for all of this is
`docs/docs_EXPLANATION/OpenUBEM_fundamentals.md` **§8.5** — read it before changing anything.

### 2. What you must do

1. Extend the generator so that each district's EUI comes from its `EU-11` manifest
   (`openubem/outputs/eu_evidence/EU-11/<DISTRICT>/…_manifest.csv`), joined on `building_id` against
   `osm_id` in `02_residential_manifest.gpkg` — **the ids match verbatim, including any `_part0` suffix; do
   not strip it.**
2. Regenerate all four viewers **and** their `eu_<DISTRICT>_data/` folders, then copy both to the
   `docs/docs_ACTIVE/europeanLocations/outputs_3D/` mirror.
3. In each data folder keep the existing contract exactly: `buildings.csv` (one row per building with
   `height_source`, `eui_kwh_m2` and `eui_status`), `results.csv` **and** the untouched `results_source.csv`
   where a run exists, `sources.json` (repo-relative path **and sha256** of every input read, plus the
   coverage fraction), and `index.html`.
4. Update `sources.json` to name the **Speed** run: `platform`, `energyplus_version`, the EPW and its
   sha256, and the campaign directory.

### 3. 🔴 Rules the page must keep obeying

- **Coverage is stated, never implied.** If a district is bound on *k* of *n* residential buildings, the HUD
  says so, the filter counter says so, and the unbound buildings render **grey with a `not simulated`
  tooltip**. A partially bound channel never renders as a full one.
- **Nothing is interpolated, defaulted or borrowed** — not from another district, not from an archetype
  campaign, not from a neighbour. A building with no run has no value.
- **An absent `results.csv` stays absent**, never an empty file, and `index.html` says why.
- The page stays **self-contained and offline**: no CDN, no external stylesheet, no fetch. Everything is
  inlined; assets, if any, are `data:` URIs.
- Keep the height-provenance channel intact (`measured` / `storeys × 3.0 m` / `assumed 9.0 m`, counted in
  the panel). It is independent of the result channel.
- Carry the campaign's own caveats onto the page: heating-only; the `geometry_outcome` split
  (`FINDING EU-S2-01` massing-box fallback) in each tooltip; and the fact that this is the **`S2`
  real-footprint perimeter**, not the S0 archetype campaign, so no comparison with
  `it = 108.25 kWh/m² ± 0.16 %` may appear on the page.

### 4. Deliverable

The four regenerated viewers and data folders in both locations; one appended row in
`docs/docs_ACTIVE/europeanLocations/content/walkthrough_progress_log.csv`; and, if the channel model
changes in any way, an update to `OpenUBEM_fundamentals.md` §8.5 so the document keeps describing what the
code actually does. All `.png` and figure outputs go to `openubem/outputs/` flat — never under `docs/`.
