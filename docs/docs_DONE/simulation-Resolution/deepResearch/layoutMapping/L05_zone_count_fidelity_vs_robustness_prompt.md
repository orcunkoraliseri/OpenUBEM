# Deep-Research Prompt L05 — DOES EXACT ZONE COUNT MATTER? (layout fidelity vs robustness, the Option-1 cost)

> SCOPE GUARD — READ FIRST. This is an **accuracy-evidence** task. The deliverable is the published
> evidence on whether reproducing a prototype's **exact zone count/layout** (e.g. 8 apartments + corridor)
> versus a **simplified** core/perimeter (e.g. 4 perimeter + 1 core) materially changes the **energy
> result** — annual EUI, end-use split, peak — and at what cost in runtime/robustness. This is the
> evidence that tells the manager whether **Option 1 is worth its complexity** over **Option 2**. It is
> NOT about how to build the layout (Prompts L01–L04). If you are writing about anything other than **the
> measured energy/cost difference between detailed and simplified zone layouts and the source**, stop and
> return to the tables. See `00_README_layout_mapping_prompt_set.md` for the decision, shared facts,
> conventions.

---

## What this document is

A fill-in-the-blanks request on the value-of-fidelity. Before OpenUBEM invests in Option 1 (match the DOE
zone count on arbitrary shapes), we need the literature's answer to: *does it change the answer?* If
8-apartment vs 4-perimeter zoning moves whole-building EUI by < a few %, Option 2 (robust, simpler) is the
rational choice; if it moves peak/comfort or specific end-uses materially, Option 1 is justified for those
cases. Treat each cell as a question; fill with sourced quantitative findings.

## Role

UBEM/BEM zoning-sensitivity research analyst. Trace to peer-reviewed **thermal-zoning sensitivity**
studies (Chen & Hong 2018; Cerezo Davila et al. 2017; Korolija et al. 2013; Johari et al. 2022; Dogan &
Reinhart 2017 Shoeboxer) and any DOE/PNNL or IBPSA work comparing zone-count levels for the same building.
Report magnitudes in SI/%. Distinguish building-scale from district-scale.

## Why this matters (so you scope correctly)

OpenUBEM is zero-fitted and validated at city scale within ±9 %. If zone-count fidelity changes city EUI
by far less than that, spending complexity/robustness budget on Option 1 is hard to justify except where
it demonstrably matters (e.g. residential corridor loads, perimeter daylighting, peak sizing). We need the
quantitative break-points to scope v1 honestly.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Energy impact of zone-count/layout fidelity

| Comparison | Annual EUI delta | Heating/Cooling delta | Peak delta | Building type | Source |
|---|---|---|---|---|---|
| Detailed prototype zoning vs core/perimeter |  |  |  |  |  |
| Core/perimeter vs one-zone-per-floor |  |  |  |  |  |
| Exact unit count (8) vs lumped perimeter (4) |  |  |  |  |  |
| Residential corridor-core vs uniform loads |  |  |  | residential |  |

### Table 2 — Where fidelity matters most vs least

| Factor | Sensitive to zone count? | Why | Source |
|---|---|---|---|
| Annual whole-building EUI |  |  |  |
| Peak demand / equipment sizing |  |  |  |
| Perimeter daylighting savings |  |  |  |
| Residential corridor mis-loading |  |  |  |
| District-scale aggregate |  |  |  |

### Table 3 — Cost of fidelity

| Aspect | Detailed (Option 1) | Simplified (Option 2) | Source |
|---|---|---|---|
| Zones per building (typical) |  |  |  |
| Runtime per building |  |  |  |
| City-scale tractability |  |  |  |
| Geometry failure rate on real footprints |  |  |  |

### Table 4 — Recommendation by archetype group

| Archetype group | Worth Option 1? | Recommended layout fidelity | Source |
|---|---|---|---|
| Office / retail (uniform loads) |  |  |  |
| Residential / hotel (corridor matters) |  |  |  |
| School / hospital (functional cores) |  |  |  |
| Warehouse / strip-mall (single volume) |  |  |  |

---

## Part C — Synthesis (is Option 1 worth it?)

Give a clear verdict: (1) the **magnitude** of the energy difference detailed-vs-simplified zoning makes,
at building and district scale; (2) the archetype groups/metrics where Option 1 is **justified** vs where
Option 2 is **sufficient**; (3) a recommended **per-archetype fidelity level** for OpenUBEM v1 that
balances faithfulness against the ±9 % validation tolerance and city-scale robustness. Be quantitative.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C verdict.
3. Cite ≥4 zoning-sensitivity studies with numbers.
4. **"Confidence and caveats":** where the evidence is thin (e.g. exact-unit-count studies are rare).
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **Quantify** the EUI/peak difference with sourced numbers, not adjectives.
- **Give a per-archetype-group Option-1-vs-2 recommendation.**
- **Relate magnitudes to the ±9 % city-scale tolerance.**
- **No fabricated precision;** flag GAPs. **Stay on topic** — fidelity-vs-cost evidence only.
