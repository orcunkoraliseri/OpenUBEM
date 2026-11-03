# Deep-Research Prompt L14 — ACCURACY / FIDELITY TRADE-OFF (does room-level layout actually change EUI, and when is it worth it?)

> SCOPE GUARD — READ FIRST. This prompt asks the **"is it worth it"** question that justifies the whole
> feature: does going from single-zone → floor → core/perimeter → room-level (corridor+units) actually
> change simulated EUI, by how much, and for which building types — so the manager can decide *which
> archetypes/shapes warrant room-level layout at all*. It is NOT the validation methodology (that's `L15`)
> and NOT the cost scaling alone (also `L15`). This is the accuracy-benefit evidence + the LOD-selection
> rule. See `00_README_layoutgenerator_prompt_set.md` for shared facts.

---

## What this document is

The justification-and-targeting reference. OpenUBEM's existing resolution doc notes ~94% of the current
fleet runs at building/floor level and only ~6% at zone/B1. Adding `layoutGenerator.py` extends zone-level
to non-rectangular buildings — but only pays off if room-level layout meaningfully changes results for
those buildings. This prompt gathers the published sensitivity evidence (EUI vs. thermal-zoning
resolution) so the manager can write a defensible LOD-selection rule: which archetype × shape combinations
get room-level, and which are fine at floor/single-zone.

## Role

BEM zoning-sensitivity research analyst. Ground the evidence in studies that varied thermal-zoning
resolution and measured the EUI/peak-load impact: the core/perimeter-vs-single-zone sensitivity
literature (e.g. studies on zoning simplification for BEM — Dogan, Chen, Smith; the "thermal zoning
impact on energy" papers), the LOD-and-accuracy UBEM literature, and any DOE/ASHRAE guidance on when
core/perimeter is required. Report actual numbers (Δ EUI %, Δ peak %) with study conditions.

## Why this matters (so you scope correctly)

Room-level layout is ~12× the zone count of building-level (per the resolution doc's estimate). That cost
is only justified where it changes the answer. If the literature shows core/perimeter vs. single-zone
moves EUI 5–15% for deep commercial but <2% for residential, that directly shapes which archetypes
`layoutGenerator.py` should target and confirms/refutes the plan to un-force residential from per-floor.
This prompt turns "more zones = more realistic" into "here's the measured benefit, so target X."

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Measured EUI sensitivity to thermal-zoning resolution

| Study | Building type | Resolutions compared | Δ EUI (%) | Δ peak load (%) | Conditions (climate, HVAC) | Source |
|---|---|---|---|---|---|---|
|  |  | single vs. core/perim |  |  |  |  |
|  |  | core/perim vs. per-room |  |  |  |  |
|  |  | floor vs. zone |  |  |  |  |

### Table 2 — Sensitivity by driver (why resolution matters or not)

| Driver | Effect of finer zoning | Which archetypes it matters for | Source |
|---|---|---|---|
| Solar/orientation (perimeter split N/S/E/W) |  |  |  |
| Daylighting controls (perimeter daylit zones) |  |  |  |
| Internal-load diversity (core vs. perimeter loads) |  |  |  |
| HVAC zoning / simultaneous heat-cool |  |  |  |
| Envelope-dominated vs. load-dominated buildings |  |  |  |

### Table 3 — LOD-selection recommendation (which archetype × shape → which resolution)

| Archetype | Compact shape → resolution | Non-rectangular → resolution | Expected benefit of room-level | Source/rationale |
|---|---|---|---|---|
| MidriseApartment | floor? zone? |  |  |  |
| LargeOffice | zone (core/perim) |  |  |  |
| SmallOffice |  |  |  |  |
| Retail big-box |  |  |  |  |
| Hotel |  |  |  |  |
| School |  |  |  |  |
| Hospital |  |  |  |  |

### Table 4 — Fit to OpenUBEM

| Question | Answer + source |
|---|---|
| Is room-level (corridor+units) meaningfully more accurate than floor-level for residential? |  |
| Does the ~6%-of-fleet-at-zone-level share rise usefully if non-rect buildings get room-level? |  |
| Which archetype × shape combos are NOT worth room-level (keep floor/single)? |  |
| Does the evidence support or refute un-forcing residential from `one_zone_per_floor`? |  |

---

## Part C — Synthesis (the LOD-selection rule)

Give: (1) a **quantified verdict** on when room-level layout changes EUI enough to justify the cost, with
the % thresholds from the literature; (2) a concrete **archetype × shape → resolution decision table**
OpenUBEM can encode (which combos get `layoutGenerator`, which stay floor/single); (3) an evidence-based
call on the **residential un-forcing** question; (4) the archetypes where the feature adds the most value
(highest priority for the plan). Every number cited or flagged GAP.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C LOD-selection rule.
3. Cite the sensitivity study for every Δ number.
4. **"Confidence and caveats":** which archetype's sensitivity is least studied.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **Report actual Δ EUI / Δ peak numbers with study conditions** — no hand-waving "more accurate."
- **Deliver an archetype × shape → resolution decision table** the plan can encode.
- **Take an explicit position on residential un-forcing**, backed by data.
- **No fabricated precision;** flag GAPs. **Stay on topic** — accuracy benefit & LOD selection, not
  validation methodology or cost scaling (`L15`).
