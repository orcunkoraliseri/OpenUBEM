# RESULT_V13: Deployment & Pipeline Architecture

This document decides how OpenUBEM should package and serve the interactive 3D viewer output, with the same "one place the user can actually find" discipline used for the rest of the pipeline.

---

## Table 1 - Delivery models

| Model | How it works | Offline-openable (`file://`, no server)? | Size ceiling before it becomes impractical | Hosting cost if hosted | Fit for OpenUBEM's outputs discipline | Source |
|---|---|---|---|---|---|---|
| Self-contained single HTML file (geometry + data inlined / data-URI) | Python writes one HTML entry point that embeds the viewer shell, scene payload, and styling; assets are inlined or encoded into the document, so the artifact is a single double-clickable file. | Yes, if all JS/CSS/scene payloads are embedded and no runtime fetches remain. This is the best match to the offline requirement. | Estimate: comfortable for neighborhood-scale scenes up to the low tens of MB; beyond roughly 25-50 MB the load time and browser memory cost start to dominate, and >100 MB is a warning sign. | None. | Best fit. It preserves the project's flat-output convention and keeps the viewer in one artifact. | [esbuild API](https://esbuild.github.io/api/) (`--outfile`, data URL loader); [glTF spec](https://github.com/KhronosGroup/glTF/blob/main/specification/2.0/Specification.adoc) (GLB packs JSON + buffer in one file); [Vite build options](https://vite.dev/config/build-options) (`assetsInlineLimit`, `cssCodeSplit`) |
| Static-site bundle (HTML/JS/CSS + separate data files) | Python writes a small site directory: one HTML entry point, a JS bundle, optional CSS, and one or more scene/data files. | Usually yes for local files, but `file://` module/CORS behavior is browser-sensitive; the safer assumption is "works best with a local static server." | Estimate: better than the single file once scenes grow, because data can be split; practical neighborhood bundles are usually a handful of files and tens of MB total. | None if self-hosted. | Good, but weaker than the single-file model because the deliverable becomes a directory tree rather than one artifact. | [Vite build options](https://vite.dev/config/build-options) (`outDir`, `assetsInlineLimit`, `cssCodeSplit`); [esbuild API](https://esbuild.github.io/api/) (`bundle`, `outfile`, `outdir`) |
| Tile server (only if `V12` scale mandates streaming) | Python emits streamed tiles or a tileset, and a local or remote HTTP service serves tiles on demand to the browser client. | No, not as a pure file artifact; it needs a live server. | Best for very large city-scale datasets because the "ceiling" is operational rather than file-size limited. | Low if fully self-hosted, but ongoing compute/storage cost is real; higher if you rely on managed infrastructure. | Poor fit for the current outputs discipline because the viewer is no longer a single local artifact. | [OGC 3D Tiles standard](https://www.ogc.org/standards/3dtiles/) (streaming massive 3D geospatial content); [3DCityDB web map client](https://github.com/3dcitydb/3dcitydb-web-map) (Docker-packaged, server-backed Cesium viewer) |
| Hosted interactive app (server-rendered or SPA behind a live backend) | Python feeds a backend or uploads artifacts to a live web app; the browser retrieves state from the service at runtime. | No. It requires network access and a running service. | In theory unbounded on the server, but the client still inherits browser and device limits. | Medium to high, depending on compute, storage, and any commercial basemap/terrain usage. | Worst fit. It breaks the "open locally without a service" discipline unless treated as a separate non-MVP deployment mode. | [City Energy Analyst](https://cityenergyanalyst.com/) (desktop + console + cloud variants); [Speckle server repo](https://github.com/specklesystems/speckle-server) (server + frontend + viewer); [3DCityDB web map client](https://github.com/3dcitydb/3dcitydb-web-map) (official hosted web link) |

## Table 2 - Python build pipeline per candidate delivery model

| Delivery model | Pipeline stage that produces it (new module vs. extends an existing exporter) | Build tool needed (pure Python / needs a JS bundler step) | Reproducibility (deterministic byte-for-byte rebuild from the same pipeline run?) | Source |
|---|---|---|---|---|
| Self-contained single HTML | New post-processing exporter after Step 5, ideally adjacent to `openubem/results/visualization.py` and `plotting_suite.py`; it consumes `05_results.gpkg` / `05_summary.json` and emits one viewer HTML. | Pure Python at run time is enough if the JS viewer shell is frozen once and vendored; a JS bundler is a one-time developer step, not a per-run dependency. | Mostly yes, if the bundle version is pinned and the exporter serializes scene data in stable order. Byte-for-byte stability is achievable but must be enforced, not assumed. | [esbuild API](https://esbuild.github.io/api/) (`bundle`, `outfile`); [glTF spec](https://github.com/KhronosGroup/glTF/blob/main/specification/2.0/Specification.adoc) (self-contained GLB); [Vite build options](https://vite.dev/config/build-options) (`assetsInlineLimit`, `cssCodeSplit`) |
| Static-site bundle | New exporter/staging module after Step 5 that writes a site directory rather than one file. | Needs a JS bundler step if the viewer shell is built from source each run; can be reduced to pure Python only if the JS bundle is prebuilt and frozen. | Yes in principle, but harder to keep byte-stable because chunk names, hashes, and asset splitting can change unless the toolchain is tightly pinned. | [Vite build options](https://vite.dev/config/build-options) (`outDir`, `assetsInlineLimit`, `cssCodeSplit`); [esbuild API](https://esbuild.github.io/api/) (`outdir`) |
| Tile server | New branch after Step 5: one module exports tilesets / tile assets, another module or container serves them. This is not just an exporter; it is an export + serve architecture. | Usually needs both a tile-generation toolchain and a JS client bundle or prebuilt viewer shell. The runtime service is required. | Deterministic tile content is possible, but the deployment is not a single immutable artifact because serving and indexing state are part of the system. | [OGC 3D Tiles standard](https://www.ogc.org/standards/3dtiles/); [3DCityDB web map client](https://github.com/3dcitydb/3dcitydb-web-map) |

## Table 3 - Where artifacts live

| Question | Answer + source |
|---|---|
| Does the recommended delivery model fit as a flat artifact under `openubem/outputs/` per the project's existing figure/artifact-output convention, or does it need its own subtree (e.g. a data directory alongside one HTML entry point)? | Yes, the recommended model fits as a flat artifact under `openubem/outputs/`: `openubem/outputs/<run_id>_viewer.html`. That is the cleanest match to the repo convention that all figure outputs stay visible in one place. [CLAUDE.md](../../../../CLAUDE.md#L96) [README.md](../../../../README.md#L339) |
| If data files are separate from the HTML (static-site bundle), how many files / what total size for a realistic OpenUBEM neighbourhood, and is that still "one place the user can actually find"? | For the primary model: zero separate files. If the fallback static-site bundle is used, expect roughly 3-6 files total (HTML + JS bundle + optional CSS + scene/data files), usually tens of MB for a neighborhood-scale run. It is still one directory, but it is no longer the project-preferred flat artifact. Estimate only. | 
| Does any candidate model risk fragmenting outputs across multiple non-obvious locations? | Yes: the tile-server and hosted-app options inherently split artifacts between a browser entry point, generated data, and runtime service state. The single-file model does not fragment outputs. | 

## Table 4 - Fit to reproducible/self-contained/open-source constraint

| Question | Answer + source |
|---|---|
| Which delivery model requires zero paid host/service to view (works from a laptop with no internet)? | The self-contained single HTML file. It is the only option that directly satisfies "double-click it offline" without a service dependency. [esbuild API](https://esbuild.github.io/api/); [glTF spec](https://github.com/KhronosGroup/glTF/blob/main/specification/2.0/Specification.adoc) |
| Which requires a JS build toolchain (`npm` / webpack / Vite) at pipeline-run time, and does that conflict with OpenUBEM's Python-only pipeline discipline (or is a one-time pre-built JS bundle + Python data-injection acceptable)? | The static-site bundle and tile-server paths require a JS toolchain at run time if the viewer shell is built per run. That conflicts with the Python-only discipline. A one-time prebuilt shell is acceptable only if the per-run pipeline itself stays pure Python and only injects data into a frozen artifact. [Vite build options](https://vite.dev/config/build-options); [esbuild API](https://esbuild.github.io/api/) |
| Flag explicitly: does any candidate need a paid host (Mapbox tiles, Cesium Ion, a commercial tile server) baked into the delivered artifact itself, not just during development? | Not in the recommended model. Paid host dependence is a risk in hosted-app and some tile-server variants, but it is not required by the architecture. If a future design hard-codes a commercial basemap/terrain or managed tile service into the delivered artifact, that would violate the OpenUBEM constraint. This is a design warning, not a spec requirement. | 

---

## Part C - Synthesis

### Recommended delivery model
The recommended MVP delivery model is **self-contained single HTML**.

Decisive reasons:
1. It is the only model that directly matches OpenUBEM's existing artifact discipline: one visible output that the user can open offline without starting a service.
2. It preserves the Python-first pipeline: Step 5 can end by writing one HTML artifact, while the JS viewer shell is frozen once and not rebuilt on every pipeline run.
3. It is the least operationally fragile option. No backend, no tile server, no token-dependent basemap, no extra deployment target.

### Concrete build-pipeline design
1. Add a new Step 5 post-processing exporter, e.g. `openubem/results/viewer_export.py`, called after `05_results.gpkg` and `05_summary.json` exist.
2. The exporter serializes the neighborhood scene and attributes into a stable payload, then writes one HTML file with the viewer shell and scene data embedded directly.
3. Use a one-time JS build only for the frozen shell, not per pipeline run. That shell should be version-pinned and treated as a vendored asset, so the per-run pipeline remains pure Python.
4. If the viewer shell uses three.js, the browser-side code can rely on standard capabilities such as raycasting, controls, and file loading without needing a live backend. [three.js docs](https://threejs.org/docs/)
5. Keep the output deterministic by sorting features, pinning library versions, and normalizing serialization order.

### Exact output location rule
Write the primary viewer artifact to:

`openubem/outputs/<run_id>_viewer.html`

If a future fallback requires a directory form, use:

`openubem/outputs/<run_id>_viewer/`

with `index.html` at the root of that subtree. The primary rule should stay flat unless scale forces a hard fork.

### Fallback if `V12` later mandates streaming
This does **not** degrade gracefully forever. The single-file model is the correct MVP default, but at larger scale it becomes a hard fork:

1. First fallback: static-site bundle in one subdirectory.
2. Second fallback, only if streaming is mandatory: tile-server / 3D Tiles architecture.

So the answer is: **single-file first, then a hard fork at scale**.

---

## Confidence and caveats

- The "size ceiling" in Table 1 is an estimate, not a spec limit. The practical break point depends on geometry complexity, texture use, browser memory, and whether the target machine is a laptop or mobile device.
- The byte-for-byte reproducibility claim is strongest for the artifact layout, not for all possible bundler outputs. It becomes exact only if you pin the toolchain and normalize any ordering / timestamps.
- The `file://` claim for the single-file path is a synthesis from the artifact model plus the browser's normal origin rules. It is the right architecture, but the final implementation still needs to avoid stray runtime fetches.
- I did not independently verify a live `ubem.io` deployment page in this pass, so I did not rely on it for the decision.

---

## Reference list

1. OpenUBEM `CLAUDE.md`. Project convention for outputs: all figure outputs go to `openubem/outputs/` (flat, visible). Local file, accessed 2026-07-02. [Path](../../../../CLAUDE.md#L96)
2. OpenUBEM `README.md`. Pipeline overview and statement that automated figure generation saves outputs to `openubem/outputs/`. Local file, accessed 2026-07-02. [Path](../../../../README.md#L339)
3. Evan Wallace. `esbuild` API documentation. Accessed 2026-07-02. https://esbuild.github.io/api/
4. Vite. Build options documentation. Accessed 2026-07-02. https://vite.dev/config/build-options
5. Khronos Group. glTF repository and specification. Accessed 2026-07-02. https://github.com/KhronosGroup/glTF and https://github.com/KhronosGroup/glTF/blob/main/specification/2.0/Specification.adoc
6. Open Geospatial Consortium. 3D Tiles standard. Accessed 2026-07-02. https://www.ogc.org/standards/3dtiles/
7. 3DCityDB. `3dcitydb-web-map` repository / Web Map Client README. Accessed 2026-07-02. https://github.com/3dcitydb/3dcitydb-web-map
8. City Energy Analyst. Official site and product pages for Desktop, Console, and Pro Cloud. Accessed 2026-07-02. https://cityenergyanalyst.com/
9. Speckle Systems. `speckle-server` repository and product site. Accessed 2026-07-02. https://github.com/specklesystems/speckle-server and https://speckle.systems/
10. Three.js. Documentation. Accessed 2026-07-02. https://threejs.org/docs/

