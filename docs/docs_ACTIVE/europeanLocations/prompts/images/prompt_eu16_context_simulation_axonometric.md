# Image prompt — `EU-16` context selection and the individual simulation (annotated axonometric)

**Shows:** how the peripheral buildings are picked and carried into each individual building's run, so that solar
shading and reflection are measured on real surroundings.
**Style:** §2.3 hybrid annotated axonometric (`docs/docs_EXPLANATION/OpenUBEM_graphic_summary_prompt_styles.md`), laid
out as the panelled axonometric flowchart of the reference figure.
**Source of the rules:** `rules/RULES_context_geometry_simulation_2026-08-30.md` R1–R9 ·
*Energy & Buildings* 337 (2025) 115620 §4.1.1 **Fig. 4 (a) (b) (c)** ·
`implementation/PLAN_eu15-eu16-zoning-context-2026-08-30.md` T06–T08.
**Attach alongside the prompt (strongly recommended):** the reference Fig. 4 screenshot — the panel structure of the
image must follow it.

**Revision 2026-08-30** — rewritten after the first render: the image now follows the reference figure's three panels
(a) simplification, (b) context, (c) zoning, plus a solar panel; labels shortened; duplication forbidden explicitly.

---

## Prompt to paste

Create one wide realistic 3D axonometric (isometric) architectural illustration in the style of an annotated engineering
figure — photorealistic materials, soft studio lighting, gentle cast shadows, neutral pale-gray background — organised
as **four labelled panels side by side, (a) (b) (c) (d), reading left to right**, each on its own flat floating ground
plane, all sharing one camera angle and one light direction. Thin precise leader-lines connect elements to small white
rectangular technical cards (thin dark border, small clean uppercase sans-serif text).

**Colour rule, fixed for the whole image and never broken:** the one simulated building is **solid, saturated green and
lit**; every context building is **plain translucent frosted grey glass, empty, unlit**; conditioned dwelling zones are
**light blue**, unconditioned zones **warm amber**; a single **teal** accent for rings and leader-lines; warm sunlight
used only for rays and shadows.

**Panel (a) — GEOMETRY SIMPLIFICATION.** A flat district plane seen from above-oblique carrying about ten real building
footprints, each drawn as a thin blue simplified outline overlaid on a slightly noisier orange original outline. Caption
under the panel: "(a) GEOMETRY SIMPLIFICATION". One card: "FOOTPRINT → SIMPLIFIED, 0.15 m". One card:
"SOURCE 01_buildings_clean.gpkg".

**Panel (b) — CONTEXT SELECTION.** The same block extruded into volumes: one building at the centre solid, green and
lit; the buildings around it plain frosted grey blocks; a flat translucent teal ring drawn on the ground around the
green building, with the grey blocks inside the ring standing at full height and the blocks outside it faded almost to
nothing. Caption under the panel: "(b) CONTEXT SELECTION". One engraved plaque on the ring: "RADIUS 20.0 m". One card:
"CONTEXT = SHADING GEOMETRY ONLY". One card: "NO ZONE, NO LOAD, NO RESULT". One card, with its leader-line pointing at
the face where a grey block touches the green building: "ATTACHED WALL → ADIABATIC".

**Panel (c) — RESIDENTIAL THERMAL ZONING.** The same green building, now cut open and enlarged, showing its storeys
stacked: on every storey light-blue dwelling cells around one warm-amber circulation zone, with the amber core running
as a continuous shaft from the ground to the roof. The frosted grey neighbours stay in place around it, drawn as faint
wireframe boxes. Caption under the panel: "(c) RESIDENTIAL THERMAL ZONING". One card pointing at a blue cell:
"CONDITIONED ZONE". One card pointing at the amber shaft: "UNCONDITIONED ZONE".

**Panel (d) — THE SOLAR RUN.** The same scene under a low warm sun coming from the upper left: visible sun rays strike
the frosted grey neighbours, their long shadows fall across the green building's facade, and a faint warm bounce of
reflected light is shown returning from a neighbouring facade onto the green building's windows. Caption under the
panel: "(d) SOLAR EXCHANGE". One card: "Solar Distribution = FullExterior". One card: "ONE ENERGYPLUS RUN PER
BUILDING". One card: "NEIGHBOURS SHADE, THEY DO NOT HEAT".

**Base plaque, bottom, full width, matte dark slate, visually different from the white cards.** Engraved in one line of
small clean text: "TODAY — 0 of 2,516 IDFs carry a shading or adiabatic surface · run_eu_s2_campaign.py:227 passes an
empty context list".

**Rendering hygiene, obey strictly.** Every card and caption listed above appears exactly ONCE in the whole image; never
repeat the same label above and below a panel. Do not add any card, title or word that is not written above. Spell every
string exactly as given — no invented words, no word repeated twice in a row, no truncation, no placeholder text. If a
string does not fit its card, reduce the font size; never abbreviate, wrap or garble it. Place all cards in a single
upper annotation band, one leader-line each, no crossing lines. No people, no logos, no watermarks, no sky, no
landscape.
