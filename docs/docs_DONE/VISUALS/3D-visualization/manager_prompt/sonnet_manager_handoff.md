# Sonnet Manager Handoff — 3D Viewer Phase G (urban context layers)

**Written:** 2026-07-03 by the outgoing Opus manager, at the user's request, to hand the tail end of Phase G to a **Sonnet manager** session. The remaining work is low-reasoning (wait for a running job, audit a summary file, write doc-log entries) — appropriate for Sonnet per the project's model-cost discipline.
**Your role:** You are the **manager** for the rest of Phase G. Read `C:\Users\o_iseri\Desktop\OpenUBEM\CLAUDE.md` first. You **plan and audit; you never write feature code** under `openubem/` or `tests/`. The one remaining execution artifact (the regen driver) already exists in a scratchpad and is already running — you do not write it.

Stay in the working directory `C:\Users\o_iseri\Desktop\OpenUBEM`.

---

## 1. What Phase G is

Adds an **urban context layer** to the self-contained single-HTML 3D neighbourhood viewer: OpenStreetMap **roads**, **green space**, and **derived block boundaries**, rendered as flat ground layers *below* the EUI/archetype-coloured buildings, each independently **toggleable like Google Maps** (green ON, roads ON, blocks OFF by default). Context is never simulation output — desaturated palette, not pickable, labelled "Urban context (OSM — not simulated)" with OSM attribution.

## 2. Status: feature code DONE + CP-5 pilot-audited PASS — DO NOT re-touch

The Phase G feature code (T23–T26) is complete and was CP-5-audited PASS by the prior Opus manager (pilot `nyc_centre` with live toggle screenshots). **Do not re-audit or edit any of it:**
- `openubem/viz/context_features.py` (T23) — OSM fetch/cache of roads/green/derived-blocks; osmnx pinned `[1.9, 2.0)`; non-fatal per-layer; sidecar `06_context.json` always written on completion. Block boundaries derived via `shapely.ops.polygonize` **after a `unary_union` noding step** (documented in `_blocks_to_features`).
- `openubem/viz/viewer_export.py` (T24) — loads context into `scene["urban_context"]`; graceful omit when caches absent; adds a `has_urban_context` export stat.
- `openubem/viz/shell/viewer_app.mjs` (T25) — three THREE.Group z-stacked layers, excluded from the raycaster (not pickable).
- `openubem/viz/shell/colormaps.mjs` (T26) — context hues byte-distinct from every EUI ramp/sector hue; `URBAN_CONTEXT_DEFAULT_VISIBLE = {green:true, roads:true, blocks:false}`.

**Tests:** 64 Python + 46 Node green (do not re-run unless auditing a change — there are no code changes left).

## 3. The ONE remaining execution task (regen) is ALREADY RUNNING

The only feature-facing work left is **regenerating all 12 cell viewers with the context layer** into BOTH `openubem/outputs/3D/` and `docs/docs_ACTIVE/3D/outputs/`. This is **already in progress** — you do not launch anything unless it has died.

- **Driver script:** `<prior Opus scratchpad>\phaseG_regen_capped_v2.py`
  (full path: `C:\Users\o_iseri\AppData\Local\Temp\claude\C--Users-o-iseri-Desktop-OpenUBEM\b1abb870-9290-4b85-b52a-5541cad3f35a\scratchpad\phaseG_regen_capped_v2.py`).
- **Live run:** harness background command **`bmuxnk45z`**, log at
  `...\b1abb870-...\scratchpad\phaseG_regen_v4.log`, summary written on completion to
  `...\b1abb870-...\scratchpad\phaseG_summary.json`.
- As of this handoff: **11 of 12 cells exported**, only `nyc_suburban` and `nyc_urban` left. It should be done within minutes.

### What the driver does (for your understanding — do not rewrite)
Per cell: reads the step3 IDF manifest; if the sidecar `06_context.json` already exists it **skips the OSM fetch** (cached), else fetches roads/green/blocks live from Overpass; regenerates the basemap if absent; exports the self-contained viewer to `openubem/outputs/3D/` and **mirrors it to `docs/docs_ACTIVE/3D/outputs/`** via `shutil.copy2`. Writes one summary row per cell.

### Known-good history / why earlier attempts stalled (do NOT repeat)
1. **First attempt:** the driver was launched **twice** → both hammered Overpass → rate-limiting. Fixed: exactly one instance.
2. **Second attempt (v3):** a single stuck Overpass retry-loop **hung the whole run for 3 hours** — the wall-clock cap was defeated because `with ThreadPoolExecutor() as ex:` blocks on exit (`shutdown(wait=True)`) waiting for the leaked network thread. Fixed in **v2/v4** by running the fetch on a **daemon thread** with `join(timeout)`; on timeout the wedged thread is abandoned (dies with the process) and the run moves on. **This is the version now running — it cannot hang.**

### Expected graceful-degradation in this run (already observed — report, don't "fix")
Overpass is up but **sluggish** today. Some large cells time a layer out and export with **partial context** — this is correct behaviour, the viewer omits the missing layer honestly. From the v4 log so far:
- `la_centre` — roads only (green/blocks timed out).
- `la_suburban` — roads only (green/blocks timed out).
- `nyc_rural` — came back empty first, the built-in 30 s retry recovered full context.
- All others full context (roads+green+blocks) or fully cached (both Austin except urban, nyc_centre).

## 4. What YOU do — in order

### Step A — confirm the regen finished (event-driven; do NOT poll tightly)
You will be notified when background command `bmuxnk45z` exits. Ground-truth check (do **not** tail the driver's agent JSONL):
- `phaseG_summary.json` exists next to the driver script, and
- the v4 log ends with `=== PHASE G REGEN DONE ===`.
If neither is true and no python process is running the driver, it died — see Step D.

### Step B — audit the summary (this is the core manager task)
Read `phaseG_summary.json` (12 rows) and verify:
1. **All 12 rows `status: "OK"`** (not `MISSING_IDFS` / `ERROR`).
2. **`count_match` true for all 12** — exported building count equals the manifest's `generation_status == "success"` count.
3. **`has_urban_context`** — expect `true` for every cell that returned any OSM layer. Any cell with `context_status: "timeout"` and only partial layers is **acceptable graceful degradation** — list those cells explicitly to the user (`la_centre`, `la_suburban` at minimum), do not present them as "full context".
4. **`over_45mb`** — flag any `true`. `nyc_centre` is the known max at ~41.5 MB (by `size_bytes/1e6`), under the 45 MB ceiling. If any cell exceeds 45 MB, report cell + size; do not silently ship.
5. **Both output dirs** `openubem/outputs/3D/` and `docs/docs_ACTIVE/3D/outputs/` contain all 12 `<cell>_viewer.html`, and each pair is byte-identical (the driver copies, so they should be — spot-check sizes).
6. **Every viewer actually embeds context:** `grep -c urban_context` > 0 in each of the 12 HTML files (confirms the export wired the layer in, not just that caches exist).

### Step C — write the doc debt (owed; the killed executor never wrote it)
Append **§8 progress-log entries for T23–T27** and a **CP-5 audit entry** to
`docs/docs_ACTIVE/3D/PLAN_3dviz_implementation.md` (standard format: Artifacts / Deviations / Test status / Notes). Verify facts against the files — do not invent. Key facts:
- **T23 deviation:** `_blocks_to_features` does `unary_union(lines)` noding before `polygonize` (rationale: `polygonize` only splits at shared endpoints, so un-noded roads crossing mid-span would not enclose cells).
- **Tests:** 64 Python + 46 Node green.
- **T27 (regen ride-along):** record the two prior failures (double-launch rate-limiting; v3 3-hour hang from the `ThreadPoolExecutor` shutdown-wait defeating the cap) and the **daemon-thread fix**, plus the final 12-cell `phaseG_summary.json` outcome including which cells degraded to partial context.
- **CP-5 entry:** pilot audit PASSED (prior manager) + full-12 regen audited clean = CP-5 closed.

Then:
- Update the **§1 checklist** line for T27 in the same PLAN doc.
- Update `docs/PROJECT_CHECKLIST.md` with the Phase G status line.
- Update memory `project_3dviz_arc.md` (and the one-line pointer in `MEMORY.md`) to reflect Phase G closed.

### Step D — only if the regen died (unlikely)
Restart **exactly one** instance from the repo root `C:\Users\o_iseri\Desktop\OpenUBEM`:
```
./.venv/Scripts/python.exe -u "C:\Users\o_iseri\AppData\Local\Temp\claude\C--Users-o-iseri-Desktop-OpenUBEM\b1abb870-9290-4b85-b52a-5541cad3f35a\scratchpad\phaseG_regen_capped_v2.py"
```
The sidecar-skip makes it resume cheaply (finished cells are not re-fetched). First confirm no other `phaseG` python process is already running:
`Get-CimInstance Win32_Process -Filter "Name='python.exe'" | ? CommandLine -like '*phaseG*'`.
If any cell reports `MISSING_IDFS`, restore from `<cell>_step3_idfs_archive.zip` (12 archive zips exist as fallback) and re-run just that cell.

### Step E — present sign-off to the user
- **CP-5 (Phase G):** report sign-off once the audit is clean, naming any partial-context cells.
- **Parent 3D arc CP-3/CP-4:** de-facto accepted but not formally closed — surface it to the user for the combined sign-off after CP-5.

## 5. Guardrails (CLAUDE.md + memory — non-negotiable)
- **Manager plans/audits, never writes feature code.** The driver is orchestration living in a scratchpad — fine to run/restart, but **never touch `openubem/` or `tests/`**, and do not rebuild `viewer.js`.
- **Never git commit or offer to** — the user's own tool auto-commits.
- **Never edit** `main.py`, any OVERVIEW/DESIGN doc; **no `.py` under `docs/`** (this handoff is Markdown — fine).
- **Local Windows OSM fetch at gen-time is FINE.** The absolute "no compute on the Speed login node / always `sbatch`" rule is **cluster-only** — it does not apply to this local regen.
- **Exactly one driver instance.** Verify no duplicate `phaseG` python process before any (re)launch.
- **Monitoring:** prefer event-driven completion; if you must poll, **≥30 min** between checks. **Do not Read/tail an agent's output JSONL** (context overflow) — check ground truth via the filesystem (`phaseG_summary.json`, HTML sizes/counts) and `Get-CimInstance` for the process.
- Viewers go to `openubem/outputs/3D/` and are mirrored to `docs/docs_ACTIVE/3D/outputs/`.

## 6. Evidence / pointers
- Live-smoke screenshots: `docs/docs_ACTIVE/3D/debug/Image-outputs/` (`nyc_centre_context_after.png`, `..._all_three_topdown.png`, `..._all_off.png`, `..._blocks_only_topdown.png`, `..._roads_only_topdown.png`, `..._toggle_blocksOn_greenOff.png`, before/after).
- Prior full Opus handoff (deeper background): `docs/docs_ACTIVE/3D/manager_prompt/opus_manager_handoff.md`.
- Driver + logs + summary: prior Opus scratchpad `...\b1abb870-9290-4b85-b52a-5541cad3f35a\scratchpad\` (`phaseG_regen_capped_v2.py`, `phaseG_regen_v4.log`, `phaseG_summary.json`).
