# Deep-Research Prompt V11 — SIMULATION-OUTPUT VISUALIZATION (mapping EnergyPlus results onto the scene — the heat-map)

> SCOPE GUARD — READ FIRST. This prompt owns **which OpenUBEM outputs get painted onto the scene and at
> what geometric granularity** — the direct Torino-heat-map analogue. It is NOT the colormap/classification/
> legend logic (that is `V09` — reference its coloring recipes, don't re-derive them), and NOT the
> time-slider UI control that lets a user scrub through the data (that is `V10` — reference it, don't design
> it). This prompt answers "what data, on what geometry, from what file" only. See
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

The output-mapping specification grounded in exactly what OpenUBEM emits today: `eui_summary.json` (annual
EUI, kWh/m²/yr, per building), per-building energy **end-uses**, **carbon**, and results at **both annual
and 8760-hourly** granularity. OpenUBEM's static renderer never paints any of this — its only colour logic
is the fixed per-category material palette (wall/roof/floor/window). This prompt is the direct equivalent of
the `fereshtehsabeghi/Torino-3d-heat-mapping` per-building web heat-map the user named as an exemplar: it
must decide, output by output, whether the honest visual encoding is an extruded/coloured building mass, a
per-surface colour (e.g. solar irradiance on individual wall/roof polygons, if OpenUBEM ever emits that),
or a temporal animation — always bounded by what granularity the source file actually supports.

## Role

Building-performance-simulation visualization analyst. Ground every mapping claim in the actual EnergyPlus/
OpenUBEM output structure (`eui_summary.json` schema, end-use categories as EnergyPlus reports them,
per-surface output variables EnergyPlus *can* report if requested — e.g. `Surface Outside Face Incident
Solar Radiation Rate per Area` — vs. what OpenUBEM's pipeline actually requests today), and in peer
practice: the **Torino-3d-heat-mapping** repo (read its actual per-building metric and encoding), **ubem.io**'s
gallery visual encodings, **CEA**'s per-building and per-surface (radiation) output maps, and general UBEM
visualization literature on extrusion-height-vs-colour-vs-both encodings for energy metrics.

## Why this matters (so you scope correctly)

This is the feature the user is most directly asking for — "colour the scene by a simulation output" — and
it is where the **faithful-to-model** constraint is sharpest: painting a per-surface heat-map on a building
that was only simulated at `building`-mode resolution (one lumped zone, no per-surface solar output
computed) would fabricate spatial detail the simulation never produced. This prompt must draw that line
explicitly, output by output, and hand `V09` a clean list of "attribute → honest granularity" so the
coloring system never overstates what the data supports.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Output inventory

| OpenUBEM output | Source file/field | Granularity available (building / surface / zone) | Best visual encoding (extrude-height+colour / surface-colour / animation / other) | Source |
|---|---|---|---|---|
| Annual EUI (kWh/m²/yr) |  |  |  |  |
| Per-building end-use breakdown (heating/cooling/lighting/plug/DHW/…) |  |  |  |  |
| Carbon (annual) |  |  |  |  |
| Hourly demand (8760, whole-building) |  |  |  |  |
| Per-surface solar irradiance (if/where OpenUBEM's EnergyPlus runs request it) |  |  |  |  |
| Comfort metrics (if OpenUBEM computes any) |  |  |  |  |

### Table 2 — Per-surface vs. per-building mapping honesty

| Output | Can it honestly be painted per-surface today (does the simulation compute it at that granularity)? | If not, what is the honest fallback (per-building average, "not available at this resolution")? | Resolution-mode dependency (does `zone` mode unlock a finer mapping `building` mode cannot)? | Source |
|---|---|---|---|---|
| EUI |  |  |  |  |
| End-use breakdown |  |  |  |  |
| Carbon |  |  |  |  |
| Solar/irradiance |  |  |  |  |
| Hourly demand |  |  |  |  |

### Table 3 — Temporal output handling

| Temporal view | What it shows | Feasibility given 8760-hourly data volume at neighbourhood scale | Animation vs. static-snapshot vs. slider-driven (cross-ref `V10`) | Source |
|---|---|---|---|---|
| Annual single value (default view) |  |  |  |  |
| Monthly aggregation |  |  |  |  |
| Hourly animation (e.g. a summer week) |  |  |  |  |
| Peak/extreme-hour snapshot (e.g. design day) |  |  |  |  |

### Table 4 — Peer precedent and the MVP output view

| Question | Answer + source |
|---|---|
| What exact metric and encoding does the Torino-3d-heat-mapping repo use (read its actual code/README — per-building? per-surface? what colour scale, cite `V09`'s classification table by reference)? |  |
| What does CEA's radiation/demand map do differently (per-surface solar vs. per-building demand)? |  |
| What does ubem.io's gallery show as its primary output encoding? |  |
| Given OpenUBEM's actual output granularity (Table 1/2), what is the single **MVP output view** to build first — the one that is both high-value and 100% honestly representable today? |  |

---

## Part C — Synthesis (the output-mapping spec + MVP)

Give: (1) the **output-to-geometry mapping table** OpenUBEM should encode — for each output in Table 1, the
exact granularity it may be painted at and the visual encoding, cross-referencing `V09` for the colormap and
`V04`/resolution-mode for the granularity gate; (2) the **MVP output view** — the one output + encoding to
ship first, with the concrete justification (data already exists, granularity is honest, closest match to
the Torino/ubem.io precedent); (3) an explicit **"do not paint this way" list** — any mapping that would
overstate the simulation's actual spatial or temporal resolution; (4) the **downstream note for `V10`** on
which outputs need the time-slider (hourly) vs. are static (annual).

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C spec.
3. Cite the actual `eui_summary.json` schema / OpenUBEM output code, the EnergyPlus output-variable
   documentation for any per-surface claim, and the Torino repo's real code/README (do not guess its
   metric).
4. **"Confidence and caveats":** which per-surface-granularity claim is unverified against OpenUBEM's
   actual EnergyPlus output-variable requests.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **Every output in Table 1 must resolve to a real OpenUBEM source file/field** — no hypothetical outputs.
- **Explicitly enforce the resolution-mode granularity gate** (Table 2) — this is where faithful-to-model is
  operationalized for the heat-map specifically; a `building`-mode building must never get a per-surface
  paint job.
- **Read and cite the actual Torino-3d-heat-mapping repo**, not an assumption about what it probably does.
- **No fabricated precision;** flag GAPs. **Stay on topic** — the *output-to-geometry mapping* only, not the
  colormap/legend system (`V09`) or the time-slider UI mechanics (`V10`).
