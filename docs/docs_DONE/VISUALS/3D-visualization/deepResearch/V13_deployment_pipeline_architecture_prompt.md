# Deep-Research Prompt V13 — DEPLOYMENT & PIPELINE ARCHITECTURE (Python → viewer build & serving)

> SCOPE GUARD — READ FIRST. This prompt owns **how the viewer is produced and served**: the Python →
> interchange-format → viewer build chain, static-site vs. server delivery, self-contained single-file HTML
> (matching OpenUBEM's outputs discipline) vs. streamed-tile delivery, and hosting/offline options. It is
> NOT the geometry format choice itself (that is `V03` — assume its output as this prompt's input), and NOT
> the rendering-stack pick (that is `V06` — assume it and design the build/serve chain around it). See
> `00_README_3dviz_prompt_set.md` for shared facts, roster, conventions.

> RESEARCH BUDGET — KEEP IT BOUNDED. Run this cheaply, in a SINGLE pass. Hard caps: **≤6 web searches and
> ≤10 page fetches, total.** After that pass, fill the required tables + Part C and STOP — do not iterate
> toward "comprehensive." Deliverable is the tables + Part C only: no preamble, no literature review beyond
> what the cells and synthesis need. Any cell you cannot fill within budget = mark it `GAP`; do not spend
> extra searches chasing one cell. **Do NOT spawn sub-agents or invoke skills to do this research** — run
> the searches yourself with plain web-search/fetch only; delegating to agents or skills multiplies token
> spend. If run by a Sonnet employee: model Sonnet, effort medium.

---

## What this document is

The packaging decision for the whole viewer. OpenUBEM's every existing output is a **Python-generated static
artifact**: PNGs from `visualizer_adapter.py`/`neighbourhood_morphology.py`, CAD files from `idf_to_*`, JSON
result summaries (`eui_summary.json`) — all written to one findable place and openable without a running
service. This prompt decides how that exact discipline extends to a browser 3D viewer: does the pipeline
emit a **single self-contained HTML file** (geometry + attributes + viewer code inlined or data-URI'd) a
user double-clicks open, a **static-site bundle** (HTML/JS/CSS + separate data files, served via any static
file host or opened via `file://`), a **tile server** (necessary only if `V12` mandates streaming at scale),
or a full **hosted app**? Each has different implications for the reproducibility constraint and for where
the artifact lives relative to `openubem/outputs/`.

## Role

Web-deployment / static-site-architecture analyst. Ground delivery-model claims in established
static-site-generator and single-file-bundling practice (e.g. Vite/esbuild single-file build modes, `glTF`
data-URI embedding conventions, how CesiumJS/MapLibre/three.js apps are typically bundled and whether they
tolerate `file://` origin restrictions such as CORS/module-loading quirks), and in how peer tools from `V02`
actually ship (does ubem.io/CEA/the Torino repo ship a static bundle, a hosted app, or something else — read
their actual repos/deployment docs, don't assume).

## Why this matters (so you scope correctly)

This is where the **reproducible/self-contained/open-source** constraint becomes a literal packaging
requirement: OpenUBEM's whole outputs discipline is "one place the user can actually find," openable without
a server or paid host. A viewer architecture that requires `npm run dev`, a live backend, or a paid static
host to ever be seen breaks that pattern and would be inconsistent with every other OpenUBEM output. This
prompt must give the manager a concrete, buildable answer — not "it depends on the deployment target."

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Delivery models

| Model | How it works | Offline-openable (`file://`, no server)? | Size ceiling before it becomes impractical | Hosting cost if hosted | Fit for OpenUBEM's outputs discipline | Source |
|---|---|---|---|---|---|---|
| Self-contained single HTML file (geometry+data inlined/data-URI) |  |  |  |  |  |  |
| Static-site bundle (HTML/JS/CSS + separate data files) |  |  |  |  |  |  |
| Tile server (only if `V12` scale mandates streaming) |  |  |  |  |  |  |
| Hosted interactive app (server-rendered or SPA behind a live backend) |  |  |  |  |  |  |

### Table 2 — Python build pipeline per candidate delivery model

| Delivery model | Pipeline stage that produces it (new module vs. extends an existing exporter) | Build tool needed (pure Python / needs a JS bundler step) | Reproducibility (deterministic byte-for-byte rebuild from the same pipeline run?) | Source |
|---|---|---|---|---|
| Self-contained single HTML |  |  |  |  |
| Static-site bundle |  |  |  |  |
| Tile server |  |  |  |  |

### Table 3 — Where artifacts live

| Question | Answer + source |
|---|---|
| Does the recommended delivery model fit as a flat artifact under `openubem/outputs/` per the project's existing figure/artifact-output convention, or does it need its own subtree (e.g. a data directory alongside one HTML entry point)? |  |
| If data files are separate from the HTML (static-site bundle), how many files / what total size for a realistic OpenUBEM neighbourhood, and is that still "one place the user can actually find"? |  |
| Does any candidate model risk fragmenting outputs across multiple non-obvious locations? |  |

### Table 4 — Fit to reproducible/self-contained/open-source constraint

| Question | Answer + source |
|---|---|
| Which delivery model requires zero paid host/service to view (works from a laptop with no internet)? |  |
| Which requires a JS build toolchain (npm/webpack/vite) at pipeline-run time, and does that conflict with OpenUBEM's Python-only pipeline discipline (or is a one-time pre-built JS bundle + Python data-injection acceptable)? |  |
| Flag explicitly: does any candidate need a paid host (Mapbox tiles, Cesium Ion, a commercial tile server) baked into the delivered artifact itself, not just during development? |  |

---

## Part C — Synthesis (the deployment decision)

Give: (1) the **recommended delivery model** for OpenUBEM's MVP viewer, with the 2–3 decisive reasons
(constraint fit + outputs-discipline fit first); (2) the **concrete Python build-pipeline design** — where
in the pipeline the export step sits, what it emits, and whether any one-time (non-per-run) JS build step is
acceptable and how it's isolated from the reproducible-per-run Python pipeline; (3) the **exact output
location** under (or alongside) `openubem/outputs/`, stated as a rule the manager can put directly in a PLAN
doc; (4) an explicit fallback if `V12` later mandates tile-streaming (does the self-contained model degrade
gracefully, or is it a hard fork into a different delivery model at scale).

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C decision.
3. Cite official bundler/library docs and the peer tools' actual deployment method (read their repos/docs,
   don't assume) for every claim.
4. **"Confidence and caveats":** which size-ceiling or reproducibility claim is an estimate vs. verified.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **Force a ranked decision** — a single recommended delivery model + explicit fallback, not a menu.
- **State plainly whether a JS build toolchain is required and when it runs** (once, at development time, vs.
  per pipeline run) — this bears directly on reproducibility.
- **Give the exact artifact location convention** consistent with `openubem/outputs/` — "one place the user
  can actually find."
- **No fabricated precision;** flag GAPs. **Stay on topic** — the *build/deployment/serving architecture*
  only, not the geometry format (`V03`) or the rendering-stack pick (`V06`).
