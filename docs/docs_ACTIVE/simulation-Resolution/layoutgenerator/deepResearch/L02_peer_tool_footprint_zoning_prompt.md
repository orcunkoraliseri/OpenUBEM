# Deep-Research Prompt L02 — PEER-TOOL FOOTPRINT ZONING (how shipped UBEM/BEM tools subdivide real footprints)

> SCOPE GUARD — READ FIRST. This is the **"what do peer tools actually do"** anchor for the set. The
> deliverable is a sourced, tool-by-tool account of how established UBEM/GIS-to-BEM tools turn a real
> building footprint into interior thermal zones — and **specifically what they do when the footprint is
> not a clean rectangle** (L / U / T / O-courtyard / irregular). It is NOT the abstract method taxonomy
> (that's `L01`), NOT the standards definition (`L03`), and NOT the geometry algorithms (`L05`); it is
> *what shipped code does and whether it degrades gracefully or gives up*. See
> `00_README_layoutgenerator_prompt_set.md` for shared facts, roster, conventions.

---

## What this document is

A fill-in-the-blanks comparison across the tools OpenUBEM benchmarks itself against. OpenUBEM's own
handling is known and pre-filled: geomeppy native core/perimeter (4.57 m buffer) for compact commercial
≥500 m², else floor-level; **no core/perimeter at all for courtyard or narrow footprints** — it silently
degrades to `one_zone_per_floor`. The question the manager must answer from this table: *when a real OSM
footprint is L/U/O-shaped, do UMI / CEA / AutoBEM / URBANopt / ComStock / TEASER also degrade to a coarse
zoning, or do they decompose / template / generate a finer interior — and if so, how?*

## Role

UBEM / GIS-to-BEM tooling research analyst. Trace every behaviour to the tool's own documentation, source
code, or a peer-reviewed description: **UMI** (Dogan & Reinhart), **City Energy Analyst / CEA** (Fonseca
et al.), **AutoBEM / AutoBEM-Geo** (New et al., ORNL — footprint-driven), **URBANopt / OpenStudio** and
its geometry measures (`create_bar_from_building_type`, geometry-from-footprint, "space-type-and-
construction-set" workflows), **ComStock / ResStock** (NREL — how they assign a prototype geometry to a
stock building), **geomeppy** (`add_block` core/perim — OpenUBEM's own engine), **TEASER** (RWTH — its
1-to-4-element reduced-order zoning), and **Ladybug/Honeybee + Dragonfly** (LBT — how Dragonfly
auto-subdivides a footprint into core/perimeter). Include the İşeri et al. in-repo paper's zone-level
handling as a first-class peer method.

## Why this matters (so you scope correctly)

OpenUBEM's degrade-to-floor-level behaviour on non-rectangular footprints may be the field norm, or it
may be well behind tools that decompose the footprint first. If ≥3 peer tools rectangular-decompose an
L-shape into wings and core/perimeter each wing, that is a concrete, citable design for
`layoutGenerator.py`. If most tools also single-zone or extrude complex footprints, that ratifies a
simpler fallback and lowers the bar. This prompt converts "we drop to floor-level" into "here is what the
field does with the same footprint, and whether we match it."

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Default interior zoning on a *compact rectangular* footprint

| Tool | Zones it builds per floor by default | Core/perimeter? perimeter depth used | Perimeter zones = 4, or shape-following? | Source |
|---|---|---|---|---|
| UMI |  |  |  |  |
| CEA |  |  |  |  |
| AutoBEM |  |  |  |  |
| URBANopt / OpenStudio |  |  |  |  |
| ComStock / ResStock |  |  |  |  |
| Dragonfly (Honeybee) |  |  |  |  |
| TEASER |  |  |  |  |
| İşeri et al. (in-repo) |  |  |  |  |
| **OpenUBEM (current)** | core + 4 perimeter per floor (commercial ≥500 m²), else 1/floor | Yes — geomeppy native, **4.57 m** | 4 perimeter + 1 core | `geometry/zoning.py:44,77-99` |

### Table 2 — Behaviour on a *non-rectangular* footprint (L / U / T)

| Tool | What it does with an L/U/T footprint | Decompose into wings? / template-swap? / extrude as-is? / single-zone? | Preserves true shape or replaces with a prototype rectangle? | Source |
|---|---|---|---|---|
| UMI |  |  |  |  |
| CEA |  |  |  |  |
| AutoBEM |  |  |  |  |
| URBANopt / OpenStudio |  |  |  |  |
| ComStock / ResStock |  |  |  |  |
| Dragonfly (Honeybee) |  |  |  |  |
| TEASER |  |  |  |  |
| **OpenUBEM (current)** | core/perim buffer still attempted; if core forms, uses it | geomeppy buffers the true polygon (no decomposition) | Preserves true shape | `geometry/zoning.py:78-85` |

### Table 3 — Behaviour on a *courtyard / O-shape* footprint (interior ring) and *narrow* footprint

| Tool | Courtyard (O-shape) handling | Narrow / thin footprint handling | Provenance recorded that zoning degraded? | Source |
|---|---|---|---|---|
| UMI |  |  |  |  |
| CEA |  |  |  |  |
| AutoBEM |  |  |  |  |
| URBANopt / OpenStudio |  |  |  |  |
| Dragonfly (Honeybee) |  |  |  |  |
| **OpenUBEM (current)** | **degrades to `one_zone_per_floor`** (donut core → E+ Fatal) | **degrades to `one_zone_per_floor`** (core < 10 m²) | Logged, not yet a provenance flag | `geometry/zoning.py:78-89` |

### Table 4 — Interior program assignment (does the tool fill zones with room *types*?)

| Tool | After zoning, does it assign per-zone space types / loads from a prototype? | Uses DOE prototype programs? | Conserves whole-building loads across zones? | Source |
|---|---|---|---|---|
| UMI |  |  |  |  |
| CEA |  |  |  |  |
| AutoBEM |  |  |  |  |
| URBANopt / OpenStudio |  |  |  |  |
| ComStock / ResStock |  |  |  |  |
| **OpenUBEM (current)** | Yes — DOE prototype per-space intensities, verbatim (Phase-E) | Yes | Yes (floor-area-based) | Phase-E realism baseline |

---

## Part C — Synthesis (per-behaviour verdict)

For **each behaviour** (compact zoning, non-rectangular handling, courtyard/narrow handling, program
assignment), give an explicit verdict: (a) does OpenUBEM match the majority of peer tools, is it more
rigorous, or cruder; (b) the single most-cited technique the field uses for non-rectangular footprints
(e.g. "N tools decompose into rectangular wings — see `L05`"); (c) whether any tool preserves the *true*
footprint while still going room-level (OpenUBEM's requirement) or whether they all swap in a prototype
rectangle. End with the highest-value, best-documented technique OpenUBEM should adopt for
`layoutGenerator.py`.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C per-behaviour verdict.
3. Cite each tool's documentation / paper / source explicitly; flag undocumented behaviour as GAP.
4. **"Confidence and caveats":** which tool's non-rectangular handling is least documented.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **Cover ≥6 peer tools** plus the İşeri in-repo paper.
- **For every tool, state explicitly what it does with a non-rectangular footprint** — this is the point
  of the prompt; a tool that "just extrudes" or "just single-zones" is a valid, citable finding.
- **Note whether each tool preserves the true footprint vs. substitutes a prototype rectangle**, and
  whether it records provenance of any degradation.
- **No fabricated precision;** flag GAPs. **Stay on topic** — shipped-tool *zoning behaviour* only, not
  the standards theory (`L03`) or geometry algorithms (`L05`).
