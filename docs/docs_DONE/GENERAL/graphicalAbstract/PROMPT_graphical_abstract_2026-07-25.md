# Graphical Abstract — Image Generation Prompt (for Gemini) — **v2, current**

> **v2 — 2026-07-25.** Adds **section 7: outdoor thermal comfort (Stage 6 / UTCI)**, on the closure
> and archiving of the UTCI arc. Sections 1–6 are byte-identical to v1; the subtitle and the overall
> composition paragraph changed to make room for the new panel.
>
> **Previous version:** [`PROMPT_graphical_abstract_2026-07-05.md`](PROMPT_graphical_abstract_2026-07-05.md) (v1, frozen) — rendered as
> `docs/docs_EXPLANATION/OpenUBEM_fundamentals_2026-07-05.png`. v1 stays valid for material about the
> energy pipeline alone.
>
> **Rendered output of this prompt:** *not generated yet.* When you generate it, save as
> `docs/docs_EXPLANATION/OpenUBEM_fundamentals_2026-07-25.png` — beside the v1 image, never over it.
>
> **Source of truth for the content:** `docs/docs_EXPLANATION/OpenUBEM_fundamentals.md` (§1–§8 for
> sections 1–6, **§11** for section 7). Room-level layout generation (§5.1.1 / zone-mode internals) is
> intentionally excluded — keep the visualization at the "what the platform does" level, not the
> geometry-engine level.

> ⚠️ **The one thing this image must not do: put UTCI on the same footing as EUI and carbon.**
> Stage 6 is a *separate analysis product* precisely because it is **not** validated against measured
> data, while EUI is (±9 % across three cities). Section 7 is therefore drawn as a distinct, visually
> secondary panel with an explicit "separate analysis product" caption — never as a sixth pipeline
> step, and never as a fourth per-building headline stat-card. This is a binding product decision
> (Q-04, user, 2026-07-23), not a layout preference. **If a generated image blurs that line,
> regenerate it rather than shipping it.**

> 🖉 **Known render defects in the v1 image — check these in any new render.** Gemini mis-set two
> strings in the SIMULATION RESOLUTION panel: *"zoning **departing** type/size"* (should be
> *depending on*) and *"building divided floor slice"* (should be *divided into floor slices*).
> Neither is a prompt error. Proofread the rendered text before use.

---

## Prompt to paste into Gemini

```
Create a clean, modern, professional graphical abstract (infographic) for a software
platform called "OpenUBEM" — an Open-Source Urban Building Energy Modeling platform.
Style: flat design, technical/scientific infographic, similar to a journal graphical
abstract or a product one-pager. Use a cohesive color palette (deep blue, teal, amber/orange
accent for energy, white/light-grey background). Clean sans-serif typography. No photographic
textures — vector/flat illustration style. Landscape orientation, single image, well-balanced
layout with clear section groupings and thin connecting arrows showing flow from left to right
and top to bottom.

Title at the top: "OpenUBEM — Urban Building Energy Modeling Platform"
Subtitle: "From a neighbourhood footprint to per-building energy and carbon — and to the outdoor
heat between the buildings — at district scale."

Include the following sections, each visually distinct (cards, panels, or zones):

1. THE FIVE-STAGE PIPELINE (main horizontal spine of the image, left to right, 5 connected
   steps with small icons):
   - Step 1 — Data Acquisition: icon of a map/OpenStreetMap pin, downloading building
     footprints. Label: "Building footprints from OpenStreetMap"
   - Step 2 — Semantic Enrichment: icon of a building being tagged/classified. Label:
     "Classify into 1 of 30 archetypes, assign climate zone + weather"
   - Step 3 — IDF Generation: icon of a 3D building wireframe/blueprint. Label: "Build a
     physics-based EnergyPlus model per building (geometry, zoning, HVAC)"
   - Step 4 — EnergyPlus Simulation: icon of a gear/CPU with a sun and thermometer. Label:
     "Simulate a full year, hourly (8,760 timesteps), for every building"
   - Step 5 — Results, Carbon & Validation: icon of a bar chart + leaf (carbon) + checkmark
     (validation). Label: "Energy use, carbon emissions, and validation against measured data"
   Show a thin arrow flowing left-to-right connecting all five steps, each producing a small
   labeled data artifact icon (document/database icon) beneath it.

2. THE END-USES (a small panel or set of icons, below or beside the pipeline, grouped under a
   heading "What gets simulated"):
   - Space heating (flame icon)
   - Space cooling (snowflake/AC icon)
   - Lighting (lightbulb icon)
   - Plug loads / equipment (plug icon)
   - Fans (fan icon, metered separately)
   Show these as simulated (checkmark or "physics-based" badge), and note in small text that
   pumps/hot water/refrigeration/cooking are added back afterward in reporting, not simulated
   directly.

3. OUTPUTS PER BUILDING (a panel with 3 small stat-card icons):
   - EUI — Energy Use Intensity (kWh/m²/yr) — bar chart icon
   - Carbon (kg CO2e/m²) — leaf / cloud icon
   - IOD — Indoor Overheating Degree (summer comfort metric) — thermometer/sun icon

4. SIMULATION RESOLUTION (a panel showing a single building silhouette split into zone
   configurations at increasing fidelity, left to right, as a short spectrum/slider graphic):
   - "Building" — whole building as one block/zone
   - "Floor" — building divided into horizontal floor slices
   - "Auto" (default) — adaptive, mixed zoning depending on building type/size
   - "Fast zone" — building floors divided into core + perimeter rings
   Label the spectrum "Selectable simulation fidelity — coarse to fine" with a small note
   "one building = one EnergyPlus model, every time." Do NOT depict detailed room-by-room
   interior layouts or corridors — keep this panel at the level of simple block/zone diagrams
   only.

5. LOCATIONS (a panel with a simple world/US map silhouette showing 3 pins on U.S. cities: New
   York City, Los Angeles, Austin, each with a small "validated" badge/checkmark). Small caption:
   "Validated across 3 U.S. cities, 12 density cells, 8,160 buildings — within ±9% of measured
   energy use." Include a small note "works anywhere OpenStreetMap has building footprints."

6. VISUALIZING RESULTS — THE INTERACTIVE 3D VIEWER (a panel showing a stylized 3D isometric
   city block of extruded, color-coded buildings — a color gradient from cool blue/teal (low
   energy use) to warm amber/red (high energy use), on a simple map/street grid base). Include
   a small cursor/click icon on one building to suggest interactivity, and a small browser
   window frame around the whole 3D scene to convey "runs in a single self-contained HTML file,
   no install, no server." Caption: "Orbit, click, and drill into any building's energy and
   provenance — one self-contained offline file."

7. OUTDOOR THERMAL COMFORT — STAGE 6 (a panel set slightly apart from the others, separated by a
   thin divider line or a subtle tinted background, to read visually as an optional add-on rather
   than a pipeline step). Heading: "Stage 6 — Outdoor Microclimate & Thermal Comfort". Directly
   under the heading, a small pill-shaped badge reading "separate analysis product — runs only on
   request".
   Inside the panel, show a small street-level scene between two extruded buildings, seen from
   ground level rather than from above: a single small human figure standing on the pavement, with
   a building shadow falling across part of the street. Overlay the scene with a heat-map gradient
   on the ground going from cool blue-green in the shaded strip to warm orange-red in the sunlit
   strip. Around the figure, place four small labelled input icons feeding into it with thin
   arrows:
   - a thermometer — "Air temperature"
   - a droplet — "Humidity"
   - a small wind/streamline arrow — "Wind"
   - a sun-plus-radiating-surfaces icon — "Mean radiant temp"
   These four arrows converge on a single output chip beside the figure reading "UTCI — Universal
   Thermal Climate Index (°C)", drawn against a short horizontal 10-class colour scale running
   from deep blue (extreme cold stress) through neutral grey-green to deep red (extreme heat
   stress).
   Add two small captions at the bottom of the panel:
   - "Sky view factor, shadows, surface temperatures → per-hour GeoTIFF maps at 1.1 m"
   - "Which buildings sit in the worst outdoor heat?"
   Include one small warning-style note in muted text: "Not validated against measured data — kept
   separate from EUI and carbon."
   Do NOT draw this panel as a sixth step in the pipeline spine, do NOT connect it into the
   left-to-right pipeline arrow, and do NOT add UTCI as a fourth stat-card in the outputs panel
   (item 3). It connects to the rest of the diagram by a single thin dashed arrow drawn FROM
   Step 5 TO this panel, labelled "reads results, one-way".

Overall composition: pipeline spine (item 1) as the dominant horizontal band across the middle
of the image; end-uses and outputs-per-building (items 2–3) as smaller supporting panels
directly under/near Step 3–4 of the pipeline; simulation resolution (item 4) as a panel below
the pipeline; locations (item 5) and the 3D viewer (item 6) as two panels anchoring the bottom
of the image side by side. Outdoor thermal comfort (item 7) sits to the RIGHT of the pipeline
spine's end, or as a clearly separated band along the right edge or lower-right corner —
visually adjacent to the energy pipeline but plainly outside it, linked only by the single
dashed "reads results, one-way" arrow. Keep all text short (label-length, not sentences). Make
sure the image reads clearly at a glance as "input footprint → simulated per building →
validated results → interactive 3D output, plus an optional outdoor-comfort analysis on the
side."
```
