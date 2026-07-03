# Deep-Research Prompt V05 — DISTRICT-SCALE wash-out of the zoning error

> SCOPE GUARD — READ FIRST. This is a **published-range** task. The deliverable is a sourced, quantitative
> account of **how much the building-scale zoning-EUI error SHRINKS when results are aggregated to
> district / city scale** — portfolio error cancellation across a heterogeneous building stock — and
> **where zoning resolution RANKS among EUI drivers** (versus HVAC, occupancy, envelope). It is NOT the
> building-scale magnitude of the zoning error (that is V01); it is purely the **aggregation / wash-out
> behaviour and the driver ranking**, with sources.
> If you are writing about anything other than **a numeric building→district error-shrinkage range, or the
> rank/share of zoning among EUI drivers, and its source**, stop and return to the tables. This is a
> **LOAD-BEARING prompt — pair with V01**: together V01 (building-scale magnitude) and V05 (district-scale
> wash-out) decide whether OpenUBEM's zoning error matters at the scale it reports. See
> `00_README_literature_validation_prompt_set.md` for the decision, shared facts, mode map, seed
> references, conventions.

---

## What this document is

A fill-in-the-blanks evidence table. OpenUBEM reports at city scale, so a zoning error that is meaningful
per building may wash out when thousands of heterogeneous buildings are summed — if the error is random
across the stock it cancels; if it is systematic it biases and does not. OpenUBEM's internal expectation is
a **residual city-scale error below ~2.3 %**, with resolution a **secondary** EUI driver (roughly
**5–15 %** at building scale) sitting **behind HVAC / occupancy / envelope (roughly 30–50 %)**. Those are
*internal* expectations and must NOT be cited as external evidence — they only tell you the regime the
published ranges must bracket. We need the **published envelope** for the wash-out and for the driver
ranking. Treat each cell as a question; fill with a sourced numeric range or a GAP.

## Role

UBEM validation / building-energy-simulation research analyst. Trace every range to a peer-reviewed study
or tool-accuracy report that **quantifies how a building-scale modelling error changes when aggregated to
district/city scale** and/or **ranks EUI drivers by their share of total variance/error**. Prioritise:
**Chen & Hong (CityBES)** city-scale LOD studies, **Cerezo Davila 2017 (Boston)** stock validation,
**Johari 2022 (review)**, **Dogan & Reinhart 2017**, sensitivity-analysis / Sobol-index UBEM studies that
rank drivers, and stock-aggregation validation papers. SI throughout (kWh/m²·yr; % of aggregate).

## Why this matters (so you scope correctly)

Zero-fitted-parameters means OpenUBEM cannot calibrate the aggregate away — the city-scale number must
*survive* comparison to the literature. The whole defensibility of coarse modes rests on this prompt: if
the published evidence shows building-scale zoning error largely **cancels** across a heterogeneous stock
(random, not systematic), then a per-building `building/floor` delta that looks alarming in V01 is
acceptable at the reporting scale — and if instead the error is **systematic** (all buildings biased the
same direction), it does NOT wash out and coarse modes threaten the city result. The manager also needs
the **driver ranking** to state, with sources, that zoning resolution is a second-order EUI driver behind
HVAC/occupancy/envelope, so that reporting effort is proportionate. This is why V05 is load-bearing and
paired with V01.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Building → district error shrinkage (aggregation studies)

| Study (author, venue, year) | Stock / scale (n buildings, city) | Building-scale error (signed %) | District/city-scale error (signed %) | Shrinkage factor | Source detail (page/fig) |
|---|---|---|---|---|---|
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |

*(Add rows per study; state the error metric — EUI %, CV(RMSE) — and sign convention per row.)*

### Table 2 — Rank / share of EUI drivers

| EUI driver | Rank / share of total EUI variance or error | Published magnitude (signed % or share) | Method (Sobol / OAT / scenario) | Source |
|---|---|---|---|---|
| Zoning resolution / geometry LOD |  |  |  |  |
| HVAC system / efficiency |  |  |  |  |
| Occupancy / internal loads / schedules |  |  |  |  |
| Envelope / construction / infiltration |  |  |  |  |

### Table 3 — The cancellation mechanism (random vs systematic zoning error across a stock)

| Mechanism aspect | Does the zoning error cancel or bias at aggregate scale? | Published magnitude / evidence | Source |
|---|---|---|---|
| Random per-building zoning error (cancels on summation) |  |  |  |
| Systematic directional bias (e.g. coarse always under-predicts → does NOT cancel) |  |  |  |
| Stock heterogeneity (mix of types/depths) effect on cancellation |  |  |  |
| Residual city-scale error after aggregation |  |  |  |

### Table 4 — OpenUBEM cross-check

| OpenUBEM observation | Published envelope (from Tables 1–3) | In-envelope? (Y/N/partial) | Note |
|---|---|---|---|
| Zoning effect expected to shrink sharply when aggregated to city scale; resolution a secondary driver behind HVAC/occupancy/envelope |  |  |  |

---

## Part C — Synthesis (the wash-out envelope for OpenUBEM)

Give: (1) the **best single numeric range** for the building→district **shrinkage** of a zoning-EUI error
that the literature supports (e.g. "X % building-scale → Y % city-scale"), with the conditions for it;
(2) an explicit statement of whether the published zoning error is **random (cancels)** or **systematic
(biases)** across a heterogeneous stock, with sources — the deciding factor for coarse-mode
defensibility; (3) the **rank/share** of zoning resolution among EUI drivers relative to
HVAC/occupancy/envelope; (4) the conditions under which the city-scale residual should be flagged
**out-of-envelope / investigate**. Name the published source for each bound. Flag any regime with no
published range as a GAP.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C envelope + the explicit random-vs-systematic verdict and driver ranking for OpenUBEM.
3. Cite each study explicitly (author, venue, year, and the figure/table the number comes from).
4. **"Confidence and caveats":** where the literature is thin or conflicting, and which stock type / scale
   is least covered.
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **Report BOTH the aggregation shrinkage AND the random-vs-systematic character** of the zoning error —
  the wash-out claim is only valid if the error is random across the stock; say so with sources.
- **Rank zoning resolution against HVAC, occupancy, and envelope** as EUI drivers, with published shares.
- **Return numeric ranges in signed %** (or share of variance), with the metric and sign convention stated
  per row — not just "higher/lower".
- **Distinguish building-scale from district/city-scale** explicitly — building-scale magnitude belongs in
  V01, not here.
- **No fabricated precision;** flag GAPs. **Stay on topic** — aggregation / wash-out and driver ranking
  only (building-scale magnitude → V01).

---

*OpenUBEM resolution-mode — literature-validation sub-set. Markdown only; binding specs remain
`docs/docs_main/`. 2026-07-01.*
