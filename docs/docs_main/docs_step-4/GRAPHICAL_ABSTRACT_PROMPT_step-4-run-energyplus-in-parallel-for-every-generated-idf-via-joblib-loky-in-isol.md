# Graphical Abstract Prompt — Step 4: Per-Building IDF Fleet → Parallel EnergyPlus Execution in Isolated Work Directories

> **Slug:** `step-4-run-energyplus-in-parallel-for-every-generated-idf-via-joblib-loky-in-isol` &nbsp;•&nbsp; **Companion to:** `DESIGN_step-4-run-energyplus-in-parallel-for-every-generated-idf-via-joblib-loky-in-isol.md` &nbsp;•&nbsp; **Generated:** `2026-06-09`

---

## Concept

The figure must communicate the fan-out / fan-in orchestration that turns a fleet of per-building IDF files into a fleet of per-building simulation results, with strict worker isolation. The single most important takeaway in 5 seconds: **every building gets its own EnergyPlus process in its own isolated directory — dispatched in parallel by joblib/loky, classified into a closed status vocabulary, and fanned back into one simulation manifest.** The visual story is "many identical lanes, no lane touches another lane."

## Suggested Structure

3-panel left-to-right horizontal flowchart whose middle panel is a stack of 5–6 identical horizontal "worker lanes", plus one small inset above the middle panel (the version handshake) and one small inset below it (the resume check).

Reasoning: the architecture *is* the replication — the figure should show the same simple lane repeated, not one complex diagram. The two insets (handshake, resume) are the only non-obvious mechanisms and deserve small callouts; everything else is deliberately boring by design.

## Key Elements to Show

- **Panel 1 — Input fan-out**: a stack of file icons labelled `<osm_id>.idf` (4–5 visible, implied more by ellipsis) next to a small table icon labelled `03_idf_manifest.parquet` with a filter chip reading `generation_status == success`. A small joined chip reads `epw_path` (from the enriched GeoDataFrame). An arrow splits into the worker lanes, labelled `joblib / loky · n_jobs`.
- **Panel 2 — Worker lanes (the heart)**: 5–6 identical horizontal lanes, each containing, in order: an IDF file icon → a gear/process icon labelled `energyplus -w -d -x -r` → a folder icon labelled `results/<osm_id>/` containing tiny file chips (`eplusout.sql`, `.err`, `.end`). Each lane is enclosed in its own rounded rectangle with visible separation — **no shared elements between lanes**. One lane shows a red ✕ and a chip `failed_fatal`; one lane shows a clock icon and chip `failed_timeout`; the rest show green ✓ `success`. A padlock icon on each lane border with the caption `isolated work_dir (I2)`.
  - **Inset above**: a small handshake icon labelled `energyplus --version == 23.1 (I3)` with an arrow gating the entry to all lanes.
  - **Inset below**: a small loop-arrow icon labelled `resume: eplusout.end → success_cached (I6)` pointing at one lane that is greyed out (skipped, not re-run).
- **Panel 3 — Fan-in**: all lanes converge into a single table icon labelled `04_simulation_manifest.parquet` with 4–5 visible column chips (`osm_id`, `status`, `wall_clock_s`, `sql_path`, `n_severe`). A small legend of the six status tokens as coloured dots: `success`, `success_cached`, `failed_fatal`, `failed_timeout`, `failed_crash`, `not_attempted_invalid_idf`. An exit arrow labelled `→ Stage 5: results parsing`.
- **Bottom strip — invariants**: 3 small chips: `I2: one work_dir per building`, `I3: binary ↔ IDD handshake`, `I6: resumable manifest`.
- Key numbers: `n_jobs = -1 (SLURM_CPUS_PER_TASK on HPC)`, `timeout 900 s`, `6-token status vocabulary`, `~10–25 MB retained per building`.
- What to **NOT** show: any building physics (zones, surfaces, HVAC — Step 3 territory); EUI/GWP numbers or charts (Stage 5 territory); EnergyPlus solver internals; the purge file list (caption detail); SLURM cluster topology (Phase-2, OQ-3).

## Visual Metaphors

- **Identical parallel lanes with hard borders** — encodes both the embarrassing parallelism and invariant I2 (isolation) in one visual: the lanes never touch.
- **Funnel-out then funnel-in** — the manifest as the single point of truth that absorbs every outcome, including failures (flag-don't-drop).
- **Traffic-light status dots** on otherwise-identical lanes — failures are first-class recorded outcomes, not exceptions that break the picture.

## Style Guidance

- **Palette:** muted slate-blue for arrows and file icons; neutral grey lane borders; status colours used *only* on the small dots/chips (green `success`, teal `success_cached`, red `failed_fatal`, amber `failed_timeout`, dark-red `failed_crash`, light-grey `not_attempted`); one warm-orange accent on the manifest table in Panel 3.
- **Typography:** clean technical sans-serif (Inter / IBM Plex / Helvetica). Labels are short tokens (`-x`, `loky`, `eplusout.end`) — never sentences.
- **Background:** clean white. Optional very faint horizontal guides aligning the worker lanes.
- **Target width:** journal double-column (≤ 180 mm). 3 panels + 2 small insets; readable at quarter-page without zoom.
- **Density:** ≤ 7 visible top-level labels (one per panel, two insets, invariants strip). All other detail lives in the figure caption.

## Generation Prompt

> Paste directly into Midjourney, DALL-E, or Ideogram.

```
Clean technical scientific diagram, three-panel horizontal flowchart on a white background, illustrating parallel EnergyPlus simulation orchestration for urban building energy modeling. Panel 1 (left): a vertical stack of five document icons labelled "<osm_id>.idf" beside a small table icon labelled "03_idf_manifest.parquet" with a filter chip "generation_status == success" and a chip "epw_path"; one arrow fans out to the right labelled "joblib / loky · n_jobs". Panel 2 (center, dominant): six identical horizontal worker lanes, each a rounded rectangle with a hard grey border that never touches its neighbours, each containing left-to-right: a small IDF file icon, a gear icon labelled "energyplus -w -d -x -r", and a folder icon labelled "results/<osm_id>/" holding tiny file chips "eplusout.sql, .err, .end"; four lanes end with a green check dot labelled "success", one lane with a red cross dot labelled "failed_fatal", one lane with an amber clock dot labelled "failed_timeout"; a small padlock on each lane border captioned "isolated work_dir (I2)". Above the lanes, a small inset with a handshake icon labelled "energyplus --version == 23.1 (I3)" gating the lane entries; below the lanes, a small inset with a circular-arrow icon labelled "resume: eplusout.end → success_cached (I6)" pointing at one greyed-out lane. Panel 3 (right): all lanes converge into one warm-orange table icon labelled "04_simulation_manifest.parquet" with column chips "osm_id, status, wall_clock_s, sql_path, n_severe", a six-dot colour legend of status tokens, and an exit arrow labelled "→ Stage 5: results parsing". Bottom strip of three small grey chips: "I2 one work_dir per building", "I3 binary–IDD handshake", "I6 resumable manifest". Palette: muted slate-blue, neutral grey, small traffic-light status dots, single warm-orange accent on the manifest, white background. Typography: clean technical sans-serif (Inter or IBM Plex), short token labels, no sentences. Style: precise CAD-inspired technical illustration, vector-clean lines, no photorealism, no clutter, journal double-column width (180 mm). Publication quality.
```

## Alternative Prompt — schematic / technical variant

```
Schematic boxes-and-arrows diagram for a technical report figure, white background, three sequential stages left-to-right: [Stage A: task construction — 03_idf_manifest.parquet filtered to generation_status==success, joined with epw_path, emitting plain-primitive task tuples (osm_id, idf_path, epw_path, work_dir), explicitly annotated "no GeoDataFrame crosses the process boundary"] arrow to [Stage B: a 2×3 grid of six identical isolated boxes, each labelled "EnergyPlus 23.1 subprocess: -w epw -d work_dir -x -r idf" above a folder "results/<osm_id>/ {eplusout.sql, .csv, .mtr, .err, .end, tbl.htm}", with a gate icon before the grid labelled "binary --version handshake == locked IDD 23.1" and a side loop labelled "resume check: eplusout.end success marker → success_cached, stale dirs recreated"; one box marked failed_fatal, one marked failed_timeout (killed at SIM_TIMEOUT_S = 900 s)] arrow to [Stage C: fan-in — closed 6-token status classification (success / success_cached / failed_fatal / failed_timeout / failed_crash / not_attempted_invalid_idf), retention purge keeping {sql, csv, mtr, err, end, tbl.htm, run log} and always deleting .eso, then 04_simulation_manifest.parquet with 11 columns including wall_clock_s and ep_version]. Bottom annotation strip lists invariants I1, I2, I3, I6. Monochrome blue-grey line art with one orange accent on the output manifest box; clean technical sans-serif labels (Inter / IBM Plex); no shadows, no gradients, vector-precise; suitable for inclusion in a methods-section figure of an energy-modeling journal article.
```
