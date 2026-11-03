# Deep-Research Prompt V04 — DAYLIGHTING / lighting over-prediction from coarse zoning

> SCOPE GUARD — READ FIRST. This is a **published-range** task. The deliverable is a sourced, quantitative
> account of **how much LIGHTING ENERGY is over-predicted when coarse thermal-zoning cannot host perimeter
> daylighting controls** — because a lumped or core/perimeter-only zone lacks a properly daylit perimeter
> band — single-zone vs per-floor vs core/perimeter vs detailed multi-zone, at the **individual building
> scale**, holding all non-geometry inputs identical. It is NOT about heating/cooling (V02) or peak (V03);
> it is purely the **magnitude and direction of the lighting-energy error from zoning resolution and
> daylighting-control hosting**, with sources.
> CRITICAL NUANCE: OpenUBEM v1 has **daylighting OFF (D7) in ALL modes**, so you must report BOTH
> (a) the **absolute** lighting over-prediction vs a metered/daylit reference AND (b) what **survives in a
> RELATIVE mode comparison** when daylighting is disabled everywhere (i.e. does the error cancel across
> modes, or does residual geometry-driven lighting difference remain?).
> If you are writing about anything other than **a numeric lighting-energy range tied to zoning resolution
> / daylighting hosting and its source**, stop and return to the tables. See
> `00_README_literature_validation_prompt_set.md` for the decision, shared facts, mode map, seed
> references, conventions.

---

## What this document is

A fill-in-the-blanks evidence table. Daylighting controls dim electric lighting in a daylit perimeter
band; a model that cannot host that band (because coarse zoning has no distinct daylit perimeter)
over-predicts lighting energy — the literature reports this on the order of **~10–20 %**. OpenUBEM lets a
user force `building` (single zone), `floor` (per-storey), or `fast_zone` (core/perimeter), and in v1 it
runs with **daylighting disabled (D7) in every mode**. We therefore need TWO published envelopes: the
**absolute** over-prediction a daylighting-off model carries versus a daylit reference, and the
**relative** residual that survives when *all* OpenUBEM modes have daylighting off, so the manager knows
whether the lighting error cancels in a cross-mode comparison or leaves a geometry-driven residue. Treat
each cell as a question; fill with a sourced numeric range or a GAP.

## Role

UBEM validation / building-energy-simulation research analyst. Trace every range to a peer-reviewed study
or tool-accuracy report that quantifies **lighting-energy savings from perimeter daylighting controls**
and/or **the lighting over-prediction of models that omit daylighting or lack a daylit perimeter zone**,
ideally in an **input-invariant** comparison (same loads/schedules/envelope/weather, zoning/daylighting
varied). Prioritise: **Dogan & Reinhart 2017 (Shoeboxer)**, **Chen & Hong (CityBES)**, **Cerezo Davila
2017 (Boston)**, **Johari 2022 (review)**, IEA/ASHRAE and DOE/PNNL daylighting-control savings literature,
and studies on daylit-perimeter zoning. SI throughout (kWh/m²·yr, W/m²).

## Why this matters (so you scope correctly)

Zero-fitted-parameters means OpenUBEM cannot calibrate a lighting delta away — it must *survive*
comparison to the literature. But OpenUBEM's design choice (D7: daylighting off in all modes) changes the
question: an *absolute* over-prediction vs metered data is carried equally by every mode and therefore
**cancels** in a relative cross-mode comparison — unless coarse zoning changes something else about the
lighting calculation (e.g. hosting geometry, floor-area partition) that leaves a residual. The manager
needs both numbers: the absolute figure documents a known bias of v1 (to report as a caveat), while the
relative figure decides whether V04 contributes anything to the cross-mode zoning error at all. If the
literature shows the effect is purely a daylighting-hosting phenomenon, then with daylighting off it should
cancel — and the prompt must confirm that with sources rather than assume it.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Lighting-energy over-prediction vs perimeter daylighting controls & zoning

| Study (author, venue, year) | Building type(s) | Condition (no daylighting / no daylit perimeter zone) | Reference (daylit multi-zone) | Lighting Δ (signed %, over-prediction) | Climate | Source detail (page/fig) |
|---|---|---|---|---|---|---|
|  |  | single-zone (no daylit perimeter) |  |  |  |  |
|  |  | core/perimeter (perimeter present, controls on/off) |  |  |  |  |
|  |  | daylighting disabled entirely |  |  |  |  |

*(Add rows per study; sign convention: positive = model over-predicts lighting energy. State it per row.)*

### Table 2 — Absolute vs relative-mode effect when daylighting is disabled

| Comparison framing | What the number represents | Published magnitude (signed %) | Does it CANCEL across modes when daylighting is off everywhere? | Source |
|---|---|---|---|---|
| Absolute: daylighting-off model vs metered/daylit reference |  |  |  |  |
| Relative: coarse mode vs fine mode, daylighting OFF in both |  |  |  |  |
| Residual geometry-driven lighting difference (partition/hosting), daylighting off |  |  |  |  |

### Table 3 — Climate / orientation / WWR dependence of the lighting effect

| Driver | Direction of influence on lighting over-prediction | Published magnitude / rule | Source |
|---|---|---|---|
| Climate / latitude (available daylight) |  |  |  |
| Orientation (N/S/E/W perimeter) |  |  |  |
| Window-to-wall ratio / glazing |  |  |  |
| Perimeter depth / daylit-band fraction of floor plate |  |  |  |

### Table 4 — OpenUBEM cross-check

| OpenUBEM observation | Published envelope (from Tables 1–3) | In-envelope? (Y/N/partial) | Note |
|---|---|---|---|
| Coarse modes cannot host perimeter daylighting; D7 (daylighting OFF) in all v1 modes — absolute over-prediction carried equally, relative cross-mode residual expected small |  |  |  |

---

## Part C — Synthesis (the lighting envelope for OpenUBEM)

Give: (1) the **best single numeric range** for the **absolute** lighting over-prediction of a
daylighting-off / no-daylit-perimeter model vs a daylit reference (central value + spread, signed %);
(2) the **relative** cross-mode residual expected when daylighting is off in *every* mode — i.e. how much
of the effect **cancels** and how much survives as a geometry-driven residue, with sources; (3) the
climate/orientation/WWR conditions that widen the effect; (4) an explicit statement of whether V04 should
contribute to OpenUBEM's cross-mode zoning error at all (given D7), or be reported purely as an absolute
v1 caveat. Name the published source for each bound. Flag any regime with no published range as a GAP.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C envelope + the explicit absolute-vs-relative verdict for OpenUBEM's daylighting-off design.
3. Cite each study explicitly (author, venue, year, and the figure/table the number comes from).
4. **"Confidence and caveats":** where the literature is thin or conflicting, and which climate/orientation
   is least covered.
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **Report BOTH the absolute over-prediction AND the relative cross-mode residual** with daylighting off —
  a single number that conflates them is a failure.
- **Prefer input-invariant comparisons** (same loads/schedules/envelope/weather, zoning/daylighting varied)
  — reject calibrated-vs-measured deltas that confound other error sources; note them separately.
- **Return numeric ranges in signed %**, with the sign convention stated per row — not just "higher/lower".
- **Cover single-zone, core/perimeter, and daylighting-disabled** conditions against a daylit reference.
- **Give the explicit call** on whether V04 contributes to OpenUBEM's cross-mode zoning error given D7
  (daylighting off in all modes).
- **No fabricated precision;** flag GAPs. **Stay on topic** — lighting/daylighting energy vs zoning
  resolution, building scale only (heating/cooling → V02; peak → V03).

---

*OpenUBEM resolution-mode — literature-validation sub-set. Markdown only; binding specs remain
`docs/docs_main/`. 2026-07-01.*
