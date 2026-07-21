# Deep-Research Prompt V05 — ATTRIBUTE BINDING & DATA SCHEMA (attaching function/population/output data to geometry for the browser)

> SCOPE GUARD — READ FIRST. This prompt owns **how per-building and per-surface attributes reach the
> browser attached to geometry** — feature IDs, glTF `EXT_mesh_features`/`EXT_structural_metadata`, 3D-Tiles
> batch/property tables, GeoJSON properties — and **where population data would come from**, since OpenUBEM
> does not store it today. It is NOT how those attributes are *coloured* (that is `V09` — reference it,
> don't answer it), and NOT the geometry format decision itself (that is `V03` — assume its output and bind
> to it). See `00_README_3dviz_prompt_set.md` for shared facts, roster, conventions.

> RESEARCH BUDGET — KEEP IT BOUNDED. Run this cheaply, in a SINGLE pass. Hard caps: **≤6 web searches and
> ≤10 page fetches, total.** After that pass, fill the required tables + Part C and STOP — do not iterate
> toward "comprehensive." Deliverable is the tables + Part C only: no preamble, no literature review beyond
> what the cells and synthesis need. Any cell you cannot fill within budget = mark it `GAP`; do not spend
> extra searches chasing one cell. **Do NOT spawn sub-agents or invoke skills to do this research** — run
> the searches yourself with plain web-search/fetch only; delegating to agents or skills multiplies token
> spend. If run by a Sonnet employee: model Sonnet, effort medium.

---

## What this document is

The data-schema decision that makes the scene queryable and colourable. OpenUBEM already computes, per
building, an archetype/function classification (DOE prototype name), a vintage/`year_built`, floor count,
footprint area, and simulation outputs in `eui_summary.json` (annual EUI kWh/m²/yr), per-building end-uses,
and carbon — all annual **and** 8760-hourly. None of this is attached to any geometry file today; the
static PNG renderer only ever uses a fixed per-category *material* colour, not a data attribute. This
prompt decides the concrete mechanism — at what granularity (per-building vs. per-surface vs. per-zone), in
what container, keyed by what ID — these attributes travel with the geometry chosen in `V03` so a browser
can look them up, filter on them, and (via `V09`) colour by them. It must also resolve the **population**
gap the user explicitly flagged: OpenUBEM has no per-building population field today.

## Role

Geospatial-data-schema / 3D-Tiles-metadata analyst. Ground every mechanism claim in the actual
specifications: **glTF 2.0** `EXT_mesh_features` and `EXT_structural_metadata` (Khronos ratified
extensions, property tables/textures), **OGC 3D Tiles 1.1** metadata (batch tables in 1.0, structural
metadata in 1.1), **GeoJSON** (RFC 7946) `properties` objects, and **CityJSON** attribute dictionaries. For
the population-sourcing question, ground claims in recognized sources for building-level population
estimation: census block/tract disaggregation methods, **OSM `building:levels`** + footprint-area occupancy
heuristics (cite a published dasymetric-mapping or building-level population-estimation paper), and
residential-archetype dwelling-unit-count conventions (DOE prototype occupancy assumptions).

## Why this matters (so you scope correctly)

If attributes cannot bind at the right granularity, `V09`'s per-surface solar heat-map and `V11`'s
output-visualization are impossible regardless of how good the geometry or colormap is. This is also a
**provenance** flashpoint (ties to `V14`): an imputed or low-confidence value (e.g. an input filled by the
`input/imputation/` tiers) must travel with a flag, not silently look identical to a directly-observed
value, or the viewer misrepresents the model's confidence. Getting the schema wrong here means every
downstream prompt either re-litigates it or ships something dishonest.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Attribute inventory

| Attribute | OpenUBEM source (file/field) or "NOT AVAILABLE — needs source" | Data type | Granularity (per-building / per-surface / per-zone) | Temporal (static / annual / 8760-hourly) | Source |
|---|---|---|---|---|---|
| Function / archetype (DOE prototype name) |  |  |  |  |  |
| Vintage / `year_built` |  |  |  |  |  |
| Number of floors / footprint area |  |  |  |  |  |
| Population (per building) | NOT AVAILABLE — needs source (see Table 3) |  |  |  |  |
| Annual EUI (kWh/m²/yr) |  |  |  |  |  |
| Per-building end-uses |  |  |  |  |  |
| Carbon |  |  |  |  |  |
| Hourly demand (8760) |  |  |  |  |  |
| Per-surface solar irradiance / other per-surface EnergyPlus output |  |  |  |  |  |
| Resolution mode (`building`/`floor`/`zone`/`auto`) |  |  |  |  |  |
| Imputed/low-confidence flag on any input | NOT AVAILABLE — needs source (input-framework/imputation arc) |  |  |  |  |

### Table 2 — Binding mechanism per format

| Format (from `V03`) | How it carries per-feature metadata | Supports per-surface (sub-mesh) granularity, not just per-object? | Query/lookup pattern in the browser | Source |
|---|---|---|---|---|
| glTF 2.0 (+ `EXT_mesh_features`/`EXT_structural_metadata`) |  |  |  |  |
| 3D Tiles (batch table / structural metadata) |  |  |  |  |
| CityJSON (attribute dictionaries) |  |  |  |  |
| Extruded GeoJSON (`properties`) |  |  |  |  |

### Table 3 — Population sourcing options

| Option | Method | Granularity achievable (per-building?) | Accuracy/caveats | Licence/cost | Verdict |
|---|---|---|---|---|---|
| Census block/tract disaggregation |  |  |  |  |  |
| OSM `building:levels` + footprint-area occupancy heuristic |  |  |  |  |  |
| Dwelling-unit count from residential DOE archetype occupancy assumptions |  |  |  |  |  |
| Other (national statistics agency building-level datasets, if any exist for OpenUBEM's cities) |  |  |  |  |  |

### Table 4 — Fit to constraints, including provenance

| Question | Answer + source |
|---|---|
| Which binding mechanism keeps attributes exactly traceable to their source file/field (faithful-to-model, no derived/interpolated values presented as real)? |  |
| How does an imputed or low-confidence input travel with its attribute through the chosen binding mechanism (a sibling `*_confidence` property, a separate flag layer, a categorical bucket)? |  |
| Is the chosen mechanism producible deterministically from Python with no proprietary tooling? |  |
| What is the concrete schema-versioning story if the pipeline adds a new output field later (does the binding mechanism require a full re-export, or can it extend)? |  |

---

## Part C — Synthesis (the attribute schema decision)

Give: (1) the **concrete binding mechanism** OpenUBEM should adopt for the format chosen in `V03`, with the
exact property/table names and granularity per attribute; (2) the **population verdict** — which sourcing
option (or explicit "none — omit population until a source exists") OpenUBEM should adopt, with the
accuracy caveat stated plainly; (3) the **provenance-flag design** — how an imputed/low-confidence value is
represented in the schema so `V14`/`V09` can surface it; (4) a **GAP list** of any attribute in Table 1
marked NOT AVAILABLE that has no defensible source yet.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C decision.
3. Cite the glTF/3D-Tiles/CityJSON spec clauses for every binding-mechanism claim, and a named
   population-estimation paper or dataset for every Table 3 option; separate spec guarantees from your own
   synthesis.
4. **"Confidence and caveats":** which population-sourcing option is least evidenced for OpenUBEM's actual
   cities (NYC/LA/Boston/Torino-style cells).
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **Every Table 1 row must resolve to a real OpenUBEM source or an explicit "NOT AVAILABLE — needs source"**
  — no attribute left ambiguous.
- **Treat population as a new data dependency, not an assumed field** — state plainly that OpenUBEM does
  not have it today.
- **Design the provenance-flag mechanism explicitly** — this feeds `V14` directly and must not be hand-waved.
- **No fabricated precision;** flag GAPs. **Stay on topic** — the *binding mechanism and schema* only, not
  how attributes are coloured (`V09`) or the geometry format's own internals (`V03`).
