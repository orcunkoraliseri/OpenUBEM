# Opus Manager Handoff — 3D Viewer Phase G (urban context layers)

**Written:** 2026-07-03 by the outgoing Opus manager session, at the user's request, to hand the arc to a fresh Opus manager session for token efficiency.
**Your role:** You are the **Opus MANAGER** for OpenUBEM. Read `C:\Users\o_iseri\Desktop\OpenUBEM\CLAUDE.md` first — you plan and audit, you never write feature code, and Sonnet employees execute. This handoff gives you everything to finish the Phase G regen and close it.

---

## 1. What Phase G is

Adds an **urban context layer** to the self-contained 3D neighbourhood viewer: OpenStreetMap **roads**, **green space**, and **derived block boundaries**, rendered as flat ground layers *below* the EUI/archetype-coloured buildings, each independently **toggleable like Google Maps** (green ON, roads ON, blocks OFF by default). Context is never simulation output — desaturated palette, not pickable, labelled "Urban context (OSM — not simulated)" with OSM attribution.

## 2. Status: feature code DONE + CP-5 AUDITED PASS

The Phase G **feature code is complete and I (prior manager) already ran the CP-5 audit — it PASSES.** Do **not** re-audit or re-touch this code. Files (all audited):
- `openubem/viz/context_features.py` (T23) — OSM fetch/cache of roads/green/derived-blocks; osmnx pinned `[1.9, 2.0)`; non-fatal per-layer; deterministic. Block boundaries derived via `shapely.ops.polygonize` **with a `unary_union` noding step first** (the one code deviation — documented in the file's `_blocks_to_features` docstring; roads crossing mid-span would otherwise not enclose cells).
- `openubem/viz/viewer_export.py` (T24) — loads context into `scene["urban_context"]` (separate from `scene["context"]` = failed-building placeholders); graceful omit when caches absent; `export_viewer_from_run(..., context_features_dir=None)` **defaults context_features_dir to results_dir**; adds a `has_urban_context` export stat.
- `openubem/viz/shell/viewer_app.mjs` (T25) — three THREE.Group layers, z-stack basemap −0.1 / green −0.06 / roads −0.05 / blocks −0.04 / buildings 0; blocks outline-only; groups excluded from raycaster (not pickable).
- `openubem/viz/shell/colormaps.mjs` (T26) — `CONTEXT_GREEN`/`CONTEXT_ROAD`/`CONTEXT_BLOCK` (byte-distinct from every ramp/sector hue) + `URBAN_CONTEXT_DEFAULT_VISIBLE = {green:true, roads:true, blocks:false}`.

**Tests:** 64 Python + 46 Node green. **Pilot `nyc_centre` validated** with live screenshots in `docs/docs_ACTIVE/3D/debug/Image-outputs/` (toggles genuinely hide layers; building colours unchanged; attribution + "not simulated" legend present). Pilot HTML 41.4 MB (`/1e6`) / 39.5 MiB — under the 45 MB ceiling (known max cell).

## 3. What remains = ONE mechanical task (regen) + doc debt

The user's standing request: **regenerate all 12 cell viewers with the context layer into BOTH `openubem/outputs/3D/` and `docs/docs_ACTIVE/3D/outputs/`.** That is the only feature-facing work left.

### Why the first attempt stalled (root cause — do not repeat)
The prior regen driver hit **two orchestration bugs** (bugs in the *driver script*, not the Phase G code):
1. **It got launched twice** — two `python phaseG_regen.py` processes ran concurrently, both hammering the OSM Overpass API → server-side rate-limiting/throttling. A background monitor was even watching a stale third PID.
2. **No per-fetch timeout** — rural/suburban cells cover huge geographic extents; the live green-space Overpass query over that area is slow and hung indefinitely (stalled ~8+ min on `austin_rural` with flat RSS = network-blocked). Dense urban cells were fine (`austin_centre` full context in 75 s).

I stopped both duplicate processes and both background tasks. **Nothing is running now.**

### Current cache state (verified after cleanup)
```
austin_centre    RGBS   (full — keep)
austin_rural     R---   (roads-only partial — will be re-fetched under the cap)
austin_suburban  ----
austin_urban     ----
la_centre        ----
la_rural         ----
la_suburban      ----
la_urban         ----
nyc_centre       RGBS   (full — pilot, keep)
nyc_rural        ----
nyc_suburban     ----
nyc_urban        ----
(R=06_context_roads.geojson G=06_context_green.geojson B=06_context_blocks.geojson S=06_context.json sidecar)
```
Caches live in each cell's results dir: `docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/`.
All 12 `<cell>_viewer.html` currently exist in both output dirs but **10 are stale / context-less** — only `nyc_centre` + `austin_centre` reflect Phase G context.

### Regen feasibility (verified)
- IDFs are present in `%LOCALAPPDATA%\Temp\ubem_validation\phaseE\<cell>\step3\` (sampled OK).
- 12 archive zips `<cell>_step3_idfs_archive.zip` exist as restore fallback if any IDFs are missing.

## 4. Recommended path (user-approved this session)

Dispatch **ONE** Sonnet employee to run the **capped** driver below (single instance, in background), then report. The cap makes slow cells degrade gracefully instead of hanging, bounding the whole run to ~15–20 min. Some large rural/suburban cells may end up with partial (roads-only) or no context if OSM is slow — that is acceptable graceful degradation; the viewer omits the missing layer honestly.

### The corrected capped driver (have Sonnet write this to ITS OWN scratchpad and run ONCE)

Changes vs. the failed driver: (a) `ox.settings.requests_timeout` bounds each HTTP call; (b) a per-cell wall-clock backstop via a worker thread; (c) the "fully cached" guard now keys on the **sidecar** (`06_context.json`, written only on full completion) so `austin_rural`'s roads-only partial is re-fetched, while fully-cached `austin_centre`/`nyc_centre` are skipped.

```python
"""Phase G 12-cell viewer regen — CAPPED (single-instance). Adds a per-layer OSM
HTTP timeout + a per-cell wall-clock backstop so large rural/suburban extents
degrade gracefully instead of hanging. Local Windows gen-time OSM fetch is fine
(NOT the cluster — the login-node compute rule does not apply here)."""
import os, json, shutil, traceback
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
import geopandas as gpd
import pandas as pd
import osmnx as ox
from openubem.viz.viewer_export import export_viewer_from_run
from openubem.viz.basemap_raster import generate_basemap
from openubem.viz.context_features import (
    generate_context_features, ROADS_NAME, GREEN_NAME, BLOCKS_NAME, SIDECAR_NAME,
)

# --- caps: primary bound is the per-request HTTP timeout; wall-clock is a backstop ---
ox.settings.requests_timeout = 60          # each Overpass HTTP call aborts after 60s -> non-fatal per-layer catch
CELL_CTX_CAP_S = 240                        # wall-clock backstop per cell's whole context fetch

LOCAL = os.environ["LOCALAPPDATA"]
CELLS = ["austin_centre", "austin_rural", "austin_suburban", "austin_urban",
         "la_centre", "la_rural", "la_suburban", "la_urban",
         "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban"]
RESULTS = Path("docs/docs_VALIDATION/validations/overAll/results/phaseE")
OUT_REPO = Path("openubem/outputs/3D")
OUT_DOCS = Path("docs/docs_ACTIVE/3D/outputs")
OUT_REPO.mkdir(parents=True, exist_ok=True)
OUT_DOCS.mkdir(parents=True, exist_ok=True)
SIZE_CEILING_MB = 45.0
SUMMARY = Path(__file__).with_name("phaseG_summary.json")


def log(m): print(m, flush=True)


def _count(path):
    if path is None or not Path(path).exists():
        return 0
    return len(json.loads(Path(path).read_text(encoding="utf-8")).get("features", []))


def _fetch_with_cap(g, rdir):
    """Run generate_context_features under a wall-clock backstop; on timeout,
    proceed (leaked worker is network-bound, not corrupting output)."""
    with ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(generate_context_features, g, rdir)
        try:
            return fut.result(timeout=CELL_CTX_CAP_S), "fetched"
        except FuturesTimeout:
            return None, "timeout"


rows = []
for c in CELLS:
    try:
        step3 = Path(LOCAL) / "Temp" / "ubem_validation" / "phaseE" / c / "step3"
        manifest = step3 / "03_idf_manifest.parquet"
        rdir = RESULTS / c

        md = pd.read_parquet(manifest)
        n_success = int((md["generation_status"] == "success").sum()) \
            if "generation_status" in md.columns else None
        missing = [str(p) for p in md["idf_path"] if not Path(str(p)).exists()]
        if missing:
            log(f"STOP {c}: {len(missing)} missing IDFs (first {missing[0]}) — "
                f"restore from {c}_step3_idfs_archive.zip before regen")
            rows.append({"cell": c, "status": "MISSING_IDFS", "n_missing": len(missing)})
            continue

        # 1. urban context — skip ONLY if fully cached (sidecar present = completed run)
        roads_p, green_p, blocks_p = rdir / ROADS_NAME, rdir / GREEN_NAME, rdir / BLOCKS_NAME
        sidecar_p = rdir / SIDECAR_NAME
        if sidecar_p.exists():
            log(f"{c}: full context cache present -> skip fetch")
            ctx_status = "cached"
        else:
            g = gpd.read_file(rdir / "01_buildings.gpkg")
            res_ctx, ctx_status = _fetch_with_cap(g, rdir)
            log(f"{c}: context {ctx_status} "
                f"roads={roads_p.exists()} green={green_p.exists()} blocks={blocks_p.exists()}")

        # 2. basemap (cache if absent)
        if not (rdir / "06_basemap_utm.png").exists():
            g = gpd.read_file(rdir / "01_buildings.gpkg")
            sc = generate_basemap(g, out_dir=rdir)
            log(f"{c}: basemap {'OK' if sc else 'NONE (graceful degrade)'}")

        # 3. export self-contained viewer (context auto-loaded from rdir)
        res = export_viewer_from_run(
            run_id=c, results_dir=str(rdir), manifest_path=str(manifest),
            basemap_path=str(rdir), out_dir=str(OUT_REPO),
        )
        html = OUT_REPO / f"{c}_viewer.html"
        shutil.copy2(html, OUT_DOCS / html.name)  # mirror to docs outputs folder

        size_mb = res["size_bytes"] / 1e6
        over = size_mb > SIZE_CEILING_MB
        rows.append({
            "cell": c, "status": "OK",
            "n_buildings": res["n_buildings"], "gen_success": n_success,
            "count_match": res["n_buildings"] == n_success,
            "has_urban_context": res.get("has_urban_context"),
            "n_roads": _count(roads_p), "n_green": _count(green_p), "n_blocks": _count(blocks_p),
            "context_status": ctx_status, "has_basemap": res["has_basemap"],
            "size_mb": round(size_mb, 2), "over_45mb": over,
        })
        flag = "  !! OVER 45MB" if over else ""
        log(f"{c}: EXPORTED n={res['n_buildings']} match={res['n_buildings']==n_success} "
            f"ctx={res.get('has_urban_context')} ctxstat={ctx_status} size={size_mb:.2f}MB{flag}")
    except Exception as e:
        log(f"ERROR {c}: {e}")
        traceback.print_exc()
        rows.append({"cell": c, "status": "ERROR", "error": str(e)})

SUMMARY.write_text(json.dumps(rows, indent=2))
log("=== PHASE G REGEN DONE ===")
log(json.dumps(rows, indent=2))
```

### Sonnet dispatch prompt (send verbatim, adapt the scratchpad path)
```
Write the capped Phase G regen driver (I will paste it) to YOUR scratchpad as phaseG_regen_capped.py,
then run it ONCE in the background from the repo root C:\Users\o_iseri\Desktop\OpenUBEM.
BEFORE launching, confirm there is NO other python process already running any phaseG_regen*.py
(Get-CimInstance Win32_Process -Filter "Name='python.exe'" | ? CommandLine -like '*phaseG*') — if there is, STOP and report.
Launch exactly ONE instance. Do not launch twice. Do not read your own agent output JSONL.
When it finishes it writes phaseG_summary.json next to the script. Report back with:
1. The full phaseG_summary.json contents (12 rows).
2. Confirmation: 12/12 status OK, count_match all true, has_urban_context per cell (flag any false + its context_status),
   any over_45mb cells with sizes.
3. Confirmation both openubem/outputs/3D and docs/docs_ACTIVE/3D/outputs have all 12 <cell>_viewer.html.
Do NOT edit any code under openubem/ or tests/. Do NOT rebuild viewer.js. Do NOT git commit.
```

## 5. Guardrails (CLAUDE.md + memory — apply to you and the executor)
- **Manager plans/audits, never writes feature code.** The driver above is orchestration (scratchpad, not `openubem/`) — fine for you to hand over; do not let Sonnet touch `openubem/` or `tests/`.
- **Never git commit or offer to** — the user's own tool auto-commits.
- **Never edit** `main.py`, any OVERVIEW/DESIGN doc; **no `.py` under `docs/`**.
- **Local Windows OSM fetch at gen-time is FINE.** The absolute "no compute on the Speed login node / always sbatch" rule is about the cluster — it does **not** apply to this local regen.
- **Exactly one driver instance.** Verify no duplicate `phaseG` python process before and after (the prior failure was a double-launch).
- **Monitoring:** prefer event-driven completion; if you must poll, ≥30 min between checks. **Do not Read/tail the agent's output JSONL** (context overflow) — check ground truth via the filesystem (`phaseG_summary.json`, cache files, HTML sizes) and `Get-CimInstance` for the process.
- Figure/output rule: viewers go to `openubem/outputs/3D/` and are mirrored to `docs/docs_ACTIVE/3D/outputs/` (the folder the user named).

## 6. Audit checklist when the regen reports back
1. `phaseG_summary.json`: 12 rows, all `status: OK`; `count_match` all `true`; `has_urban_context` — expect `true` for cells where OSM returned data; any `false`/`timeout` cells are acceptable graceful degradation but **note them to the user** (don't silently ship them as "full").
2. `over_45mb`: flag any; `nyc_centre` is the known max (~41.4 MB by `/1e6`). If any cell exceeds 45 MB, report the cell + size rather than shipping silently.
3. Both `openubem/outputs/3D/` and `docs/docs_ACTIVE/3D/outputs/` contain all 12 `<cell>_viewer.html`, byte-identical between the two dirs.
4. If any cell is `MISSING_IDFS`: have Sonnet restore from `<cell>_step3_idfs_archive.zip` and re-run just that cell.

## 7. Doc debt — still owed (the killed executor never wrote these)
Append **§8 progress-log entries for T23–T27** to `docs/docs_ACTIVE/3D/PLAN_3dviz_implementation.md` (standard format: Artifacts / Deviations / Test status / Notes). Facts to use (verify against the files, do not invent):
- **Deviation to record (T23):** `_blocks_to_features` does `unary_union(lines)` noding before `polygonize` — documented in `context_features.py`. Rationale: `polygonize` only splits linework at shared endpoints, so un-noded roads crossing mid-span would not enclose cells.
- **Test status:** 64 Python + 46 Node green.
- **T27 (regen ride-along):** record the driver double-launch + no-fetch-cap failure and the capped-driver fix, and the final 12-cell `phaseG_summary.json` outcome.

## 8. Open gates / next
- **CP-5 (Phase G):** pilot audit PASSED (prior manager). Closes once the full-12 regen is audited clean → then report CP-5 sign-off to the user.
- **Parent 3D arc CP-3/CP-4:** combined sign-off is de-facto accepted but **not formally closed** — surface it to the user after CP-5.
- Update `docs/PROJECT_CHECKLIST.md` with the Phase G status line.
- Memory: `project_3dviz_arc.md` (index `MEMORY.md`) — update when Phase G closes.

## 9. Screenshots / evidence pointers
- Live-smoke screenshots: `docs/docs_ACTIVE/3D/debug/Image-outputs/` (`nyc_centre_context_after.png`, `..._all_three_topdown.png`, `..._all_off.png`, + before/blocks-only/roads-only/toggle variants).
- Pilot outputs already correct: `docs/docs_ACTIVE/3D/outputs/nyc_centre_viewer.html` and `openubem/outputs/3D/nyc_centre_viewer.html` (41,434,047 bytes).
