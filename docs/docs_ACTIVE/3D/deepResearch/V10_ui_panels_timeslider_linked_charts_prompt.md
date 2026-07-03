# Deep-Research Prompt V10 — UI PANELS, TIME-SLIDER & LINKED CHARTS

> SCOPE GUARD — READ FIRST. This prompt owns the **data-driven UI around the 3D scene**: the attribute
> selector, filtering controls, an hourly/annual **time-slider** over OpenUBEM's 8760-hourly results,
> tooltips/pop-ups, and dashboards that link 2D charts to the 3D scene (brushing & linking). It is NOT the
> coloring/colormap/legend system itself (that is `V09` — this prompt only decides the *controls* that
> trigger a recolour, not the colour logic), and NOT the camera/selection interaction grammar (that is
> `V08`). See `00_README_3dviz_prompt_set.md` for shared facts, roster, conventions.

---

## What this document is

The dashboard layer OpenUBEM's static PNGs have no equivalent of at all — a fixed axonometric image has no
controls, no tooltip, no way to scrub through time. OpenUBEM's results are **annual + 8760-hourly**
(`eui_summary.json`, per-building end-uses, carbon), which makes a genuine time-slider both possible and
valuable (a user could watch a neighbourhood's demand heat-map animate through a summer day). This prompt
designs the UI chrome that surrounds the 3D scene: what controls exist, what a time-slider over 8760 hours
should look/behave like (playback, aggregation, performance), what a tooltip shows on hover/click, and how a
2D chart panel (e.g. a load-duration curve) can be linked bidirectionally with the 3D selection.

## Role

Data-visualization / dashboard-UX analyst, working from recognized geospatial-dashboard practice: **kepler.gl**
and **deck.gl**'s panel/filter/time-animation conventions (Uber/vis.gl docs), **CesiumJS**'s
`Clock`/`Timeline` widget for temporal playback, **Observable Plot / D3** brushing-and-linking patterns,
and any time-slider or dashboard behaviour documented for the peer tools in `V02` (ubem.io, CEA dashboard,
the Torino heat-map repo). Reconcile chart-panel design with the repo's own `dataviz` skill so any 2D chart
in the linked view matches OpenUBEM's established chart language.

## Why this matters (so you scope correctly)

Without this layer, the 3D scene is a pretty but mute object — the user cannot ask "what was demand at 6pm
in July" or "show me only school buildings above median EUI." This is also where the
**reproducible/self-contained** constraint bites hardest: the UI must ship *inside* the static artifact
(`V13`), so any control that assumes a live backend (server-side filtering, a database query) is
disqualified unless it degrades gracefully to client-side computation over the pre-baked data.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — UI-panel inventory

| Control | Function | Data it drives | Peer-tool precedent (cite `V02` or a named tool) | Source |
|---|---|---|---|---|
| Attribute selector (switch coloring mode: function/population/EUI/carbon/…) |  |  |  |  |
| Filter panel (e.g. by function, vintage range, resolution mode) |  |  |  |  |
| Time-slider (hourly/monthly/annual) |  |  |  |  |
| Tooltip / hover pop-up (per-building or per-surface value) |  |  |  |  |
| Legend (cross-reference `V09`) |  |  |  |  |
| Linked 2D chart panel (e.g. load-duration curve, end-use breakdown) |  |  |  |  |
| Search/locate a building by ID/address |  |  |  |  |

### Table 2 — Time-slider design for 8760-hourly / monthly / annual results

| Design question | Answer + source |
|---|---|
| Playback model (scrub bar vs. auto-play animation vs. both)? |  |
| Aggregation levels offered (hourly / daily / monthly / annual) and how the user switches between them? |  |
| Client-side performance at neighbourhood scale — can hundreds of buildings' 8760-hour series be held in-browser without a server, and at what data-size cost? |  |
| Precedent: how does CesiumJS `Clock`/`Timeline`, kepler.gl's time filter, or any peer UBEM tool implement this? (cite `V02`) |  |

### Table 3 — Linked-view / brushing-and-linking patterns

| Pattern | How it works | Applicability to OpenUBEM (3D scene ↔ 2D chart) | Source |
|---|---|---|---|
| Select-in-3D → filter/highlight-in-chart |  |  |  |
| Brush-in-chart (e.g. drag a time range) → recolour/filter-in-3D |  |  |  |
| Hover-linked tooltip (synchronized cursor across views) |  |  |  |

### Table 4 — Fit to constraints, incl. reproducible/self-contained

| Question | Answer + source |
|---|---|
| Can every control in Table 1 operate purely client-side against pre-baked JSON/binary data, with no server? |  |
| What is the realistic data payload size for an 8760-hourly time-slider over a few-hundred-building neighbourhood, and does it threaten the self-contained single-file delivery goal (`V13`)? |  |
| Does any UI pattern here require a proprietary charting/dashboard library, or can it be built on the repo's existing `dataviz` conventions? |  |
| Which UI element is the single highest-value MVP addition given OpenUBEM has real hourly data no current OpenUBEM output exposes interactively? |  |

---

## Part C — Synthesis (the UI/time-slider spec)

Give: (1) the **MVP UI-panel set** — which controls from Table 1 ship first and why; (2) the **concrete
time-slider design** — playback model, aggregation levels, and the performance mitigation if raw 8760-hourly
payload is too large (e.g. pre-aggregate to daily/monthly by default, hourly only for a selected building);
(3) the **linked-view design** for at least one 3D↔2D pairing (state which chart, which interaction); (4)
an explicit statement of what must be pre-computed at pipeline time (Python) vs. computed client-side, tying
back to the self-contained delivery constraint.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C spec.
3. Cite kepler.gl/deck.gl/CesiumJS official docs and the `V02` peer-tool findings for every precedent claim.
4. **"Confidence and caveats":** which performance claim (payload size, client-side responsiveness) is an
   estimate vs. benchmarked.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **Every UI-panel row must state what data it drives**, tied to a real OpenUBEM output field, not a
  hypothetical one.
- **The time-slider design must explicitly address the 8760-hourly payload/performance problem** — do not
  hand-wave "it just works."
- **Respect the reproducible/self-contained constraint** — flag any control assuming a live server.
- **No fabricated precision;** flag GAPs. **Stay on topic** — the *UI panels, time-slider, and linked-chart*
  layer only, not the coloring/colormap logic (`V09`) or the camera/selection grammar (`V08`).
