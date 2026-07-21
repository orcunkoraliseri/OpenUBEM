# Deep-Research Prompt V15 — OPENUBEM ASSET REUSE & MIGRATION MAP (what to lift from idf_reader)

> SCOPE GUARD — READ FIRST. This is an **OpenUBEM-internal codebase audit**, not a field survey — the
> "research" here is reading OUR OWN repository. Its job is the concrete reuse inventory: exactly what to
> lift from `idf_reader`'s existing static/CAD visualization assets, what is a dead-end for a web viewer, and
> the remaining build gap. It is NOT a general solution-space survey (that is `V01`/`V02` — those cover the
> field; this prompt covers only OpenUBEM's own code). See `00_README_3dviz_prompt_set.md` for shared facts,
> roster, conventions.

> RESEARCH BUDGET — KEEP IT BOUNDED (INTERNAL AUDIT, NO WEB). This is a repository read, not a web survey:
> **do NOT use web search** — at most ≤2 fetches to confirm a glTF/3D-Tiles spec clause cited as secondary
> support. Read only the files this prompt names, ONE pass, then fill the tables + Part C and STOP.
> Deliverable is the tables + Part C only; any cell you cannot verify from the code = mark it `GAP`. **Do
> NOT spawn sub-agents or invoke skills** — read the files yourself directly; delegating multiplies token
> spend. If run by a Sonnet employee: model Sonnet, effort medium.

---

## What this document is

The migration map that turns every other prompt's decision into a concrete "reuse this file / adapt this
function / build this new" instruction. `idf_reader` (the sibling codebase, geometry/plotting ancestor of
OpenUBEM) already contains: `visualizer_adapter.py` (direct-from-IDF geometry parsing, honouring
`GlobalGeometryRules`, feeding the static matplotlib axonometrics driven by `idf_reader/main.py`'s 4-view
NE/SE/SW/NW renderer), `idf_to_collada.py` / `idf_to_obj.py` / `idf_to_sketchup.py` (three CAD exporters
sharing one `collect_geometry` function that groups site → building → zone → per-category surfaces),
`neighbourhood_morphology.py` (whole-neighbourhood and full-floor axonometrics), and the per-category colour
convention (wall `#d4a574`, roof/ceiling `#8b5e3c`, floor `#c0c0c0`, window `#5dade2`/edge `#1a6fa8`/α 0.70,
shading translucent green). This prompt is the manager's own audit of exactly how much of that is usable for
a web viewer versus how much must be built from scratch.

## Role

Codebase-migration analyst. Unlike every other prompt in this set, the primary "sources" here are **the
actual repository files**, not external literature — cite file paths and line-level behaviour, not papers.
Where a claim needs external grounding (e.g. "is `collect_geometry`'s hierarchy compatible with glTF node
hierarchies"), cite the relevant spec from the roster (glTF 2.0, `EXT_mesh_features`, etc.) as a secondary
source. **Because this is our own code, VERIFY every claim against the actual files rather than assuming
behaviour from the file names or the shared-facts summary** — read `visualizer_adapter.py`, `idf_to_collada.py`,
`idf_to_obj.py`, `idf_to_sketchup.py`, and `neighbourhood_morphology.py` directly.

## Why this matters (so you scope correctly)

Every prompt V03–V13 makes a decision assuming *something* is reusable from `idf_reader` (V03 assumes
`collect_geometry` might feed a new emitter; V09 assumes the colour dict might seed the categorical palette).
This prompt is where those assumptions get checked against the real code, converting "might reuse" into a
definitive verbatim/adapt/dead-end verdict per asset — the concrete input the manager needs to scope the
implementation PLAN doc's task list and avoid Sonnet re-deriving geometry-parsing logic that already exists
and works.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Asset inventory

| Module/function | What it does (verified against the actual file) | Reusable for the web viewer? (verbatim / adapt / dead-end) | Why | File path |
|---|---|---|---|---|
| `visualizer_adapter.py::render_idf_to_base64` (and its IDF-geometry parsing) |  |  |  |  |
| `idf_reader/main.py` (4-view NE/SE/SW/NW driver) |  |  |  |  |
| `idf_to_collada.py` |  |  |  |  |
| `idf_to_obj.py` |  |  |  |  |
| `idf_to_sketchup.py` |  |  |  |  |
| `collect_geometry` (shared by the three CAD exporters) |  |  |  |  |
| `neighbourhood_morphology.py` (neighbourhood + full-floor axonometrics) |  |  |  |  |
| The per-category colour dict (wall/roof/floor/window/shading) |  |  |  |  |

### Table 2 — Geometry-extraction reuse

| Question | Answer (verified against the code) | File path / line reference |
|---|---|---|
| Does `visualizer_adapter`'s IDF parsing (or `collect_geometry`) produce a data structure that could feed a `V03`-chosen web emitter (glTF/CityJSON/GeoJSON) with light adaptation, or does it need a full rewrite? |  |  |
| Does it already honour `GlobalGeometryRules` relative/absolute coordinates and per-zone origin offsets — a correctness detail a new emitter must not silently drop? |  |  |
| Does it distinguish surfaces from sub-surfaces (windows/doors) cleanly enough to support the `V04` two-LOD split? |  |  |
| Does it carry (or could it easily carry) a stable per-surface/per-building ID usable as the feature-ID key for `V05`'s attribute binding? |  |  |

### Table 3 — Colour/material convention reuse

| Question | Answer (verified against the code) | File path / line reference |
|---|---|---|
| Where exactly is the per-category colour dict defined, and is it a single source of truth or duplicated across the exporters? |  |  |
| Can it seed `V09`'s categorical basemap (the default wall/roof/floor/window material look) directly, or does it need remapping to a colour-blind-safe set? |  |  |
| Does the current translucent-shading treatment (green, α-blended) transfer to a glTF/3D-Tiles material model, or is it a matplotlib-only trick? |  |  |

### Table 4 — The gap list

| Capability the web viewer needs | Existing asset that covers it? | If none, what must be built new | Which downstream prompt owns the design of the new piece |
|---|---|---|---|
| Web-format geometry emission (glTF/CityJSON/GeoJSON) |  |  | `V03` |
| Per-feature attribute binding |  |  | `V05` |
| Interactive rendering/navigation |  |  | `V06`/`V08` |
| Data-driven (not fixed) coloring |  |  | `V09` |
| Geo-referencing recovery |  |  | `V07` |
| Population data |  |  | `V05` |

---

## Part C — Synthesis (the migration map)

Give: (1) a **verdict table restated as prose** — of the eight `idf_reader` assets in Table 1, which are
reused verbatim, which need adaptation, and which are dead-ends for the web viewer, with the one-line reason
each; (2) the **single most valuable reuse** (the asset that saves the most new-build effort) and exactly
what adaptation it needs; (3) the **confirmed gap list** (Table 4) restated as the concrete new-build task
list the eventual PLAN doc must include; (4) an explicit flag for any place this audit found the shared-facts
summary in `00_README_3dviz_prompt_set.md` to be inaccurate against the actual code (file behaviour differs
from what was assumed), since the manager pre-filled OpenUBEM-current rows across all 15 prompts from that
summary.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C migration map.
3. Cite **file paths (and line numbers where feasible)** for every behavioural claim about OpenUBEM's own
   code — this is a codebase audit, not a literature review. Cite external specs only as secondary support.
4. **"Confidence and caveats":** any asset whose behaviour could not be fully verified by reading the file
   (e.g. because it depends on runtime IDF content not inspectable statically).
5. **Reference list** — file paths for every internal source; external spec citations (dates/URLs) only
   where used as secondary support.

## Hard requirements

- **VERIFY against the actual files — do not assume behaviour from file names or the README summary.** Open
  and read `visualizer_adapter.py`, `idf_to_collada.py`, `idf_to_obj.py`, `idf_to_sketchup.py`, and
  `neighbourhood_morphology.py` before filling any table.
- **Give a definitive verbatim/adapt/dead-end verdict for every asset in Table 1** — no "could go either
  way."
- **Flag any discrepancy found between the actual code and the `00_README` shared-facts summary** — this
  audit is the check on that summary's accuracy.
- **No fabricated precision;** flag GAPs where code could not be verified. **Stay on topic** — the
  *OpenUBEM-internal reuse/migration audit* only, not a general survey of external tools (`V01`/`V02`).
