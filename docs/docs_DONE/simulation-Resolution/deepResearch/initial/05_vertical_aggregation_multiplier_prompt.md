# Deep-Research Prompt 05 — VERTICAL AGGREGATION: zone multiplier vs every-floor modelling

> SCOPE GUARD — READ FIRST. This is a **modelling-method + cost** task. The deliverable is the
> sourced basis for deciding whether OpenUBEM's `zone` mode (and tall buildings in any multi-floor
> mode) should model **every floor explicitly** or use a **representative-floor + `Zone Multiplier`**
> scheme — and the **accuracy and runtime** consequences. It is NOT about intra-floor zoning (Prompt
> 03) or boundary conditions (Prompt 06). If you are writing about anything other than **vertical
> aggregation method, its accuracy, its cost, and the source**, stop and return to the tables. See
> `00_README_resolution_prompt_set.md` for modes, roster, conventions.

---

## What this document is

A fill-in-the-blanks request on vertical aggregation. Today OpenUBEM stacks **every** floor
explicitly (a 45-storey tower in `zone` mode → ~225 zones). DOE prototypes instead model a
**bottom / middle×N / top** representative-floor scheme using `Zone Multiplier`. This prompt sources
whether OpenUBEM should adopt multipliers, the accuracy delta, and the runtime saving. Treat each cell
as a question; fill with a sourced value or a GAP.

## Role

Building-energy-modelling research analyst. Trace every value to: the **DOE/PNNL prototype**
documentation (which prototypes use `Zone Multiplier` and how — e.g. LargeOffice, ApartmentHighRise),
the **EnergyPlus Input-Output / Engineering Reference** (`Zone` Multiplier field; what it does and
does not replicate — surfaces, solar, daylight), and **peer-reviewed UBEM / prototype-modelling
literature** on representative-floor accuracy. SI; state IP + convert.

## Why this matters (so you scope correctly)

`Zone Multiplier` tells EnergyPlus to count a modelled zone N times in load/energy sums **without**
building N geometries — cutting runtime and memory ~linearly in floors. But the multiplied middle
floor is a single thermal solution applied to all middle floors: it averages out floor-to-floor
differences in solar, shading from neighbours at different heights, and stack effect. We need the
sourced trade: how DOE applies it, what error it introduces, and whether it is acceptable for an
8,000-building city run where `zone`-mode every-floor would be ~12× the zone count.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — How DOE prototypes apply Zone Multiplier vertically

| Prototype | Floors modelled explicitly | Multiplier scheme (bottom / mid×N / top) | Source |
|---|---|---|---|
| LargeOffice | | | |
| MediumOffice | | | |
| HighriseApartment | | | |
| MidriseApartment | | | |
| LargeHotel | | | |
| Hospital | | | |
| (others that use multipliers) | | | |

### Table 2 — What Zone Multiplier does and does NOT replicate

| Aspect | Replicated correctly by multiplier? | Note | Source (E+ Eng. Ref.) |
|---|---|---|---|
| Internal loads & HVAC energy sums | | (scaled ×N) | |
| Conduction through exterior walls | | | |
| Solar gains on the multiplied floor | | (same incidence assumed all floors?) | |
| Neighbour shading varying with height | | (single height used) | |
| Stack-effect infiltration vs height | | | |
| Inter-floor surfaces (adiabatic top/bottom of mid floor) | | | |

### Table 3 — Accuracy of representative-floor vs every-floor

| Comparison | Annual energy error / bias | Conditions (building height, density) | Source |
|---|---|---|---|
| Multiplier mid-floor vs all-floors-explicit (heating) | | | |
| Multiplier vs explicit (cooling) | | | |
| Error growth with building height | | | |
| Error in dense urban context (height-varying shading) | | | |

### Table 4 — Cost / scaling (the reason to consider multipliers)

| Metric | Every-floor | Representative + multiplier | Source / estimate |
|---|---|---|---|
| Zones for a 45-storey tower (`zone` mode) | ~225 | ~15 (3 floors × 5) | |
| Relative EnergyPlus runtime per building | | | |
| Relative memory / IDF size | | | |
| Fleet zone count at city scale (8,000+ buildings) | | | |

---

## Part C — Recommendation (one paragraph)

Give a clear **adopt-or-defer verdict** for OpenUBEM v1: keep every-floor (matches the validated
`auto`/`perimeter_core` path, simplest, but ~12× cost at `zone` level), or adopt a representative-floor
multiplier scheme (cheaper, with a stated accuracy penalty). If adopt, specify the **exact scheme**
(which floors explicit, multiplier on which) and the **floor-count threshold** above which to switch.
Account for OpenUBEM's neighbour-shading (height-varying) when judging multiplier validity in dense
cells.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C adopt-or-defer verdict + exact scheme + threshold.
3. Cite the prototype multiplier usage, the E+ Engineering Reference on what Multiplier replicates,
   and ≥1 accuracy study.
4. **"Confidence and caveats":** the conditions where multipliers break (dense urban, tall, height-
   varying shading) — directly relevant to OpenUBEM's real-neighbour shading.
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **State exactly what Zone Multiplier does NOT replicate** (the bias source).
- **Give a quantified accuracy penalty** vs every-floor, with a source.
- **Give the runtime/zone-count saving** at city scale.
- **Make a v1 recommendation** with a floor-count threshold if adopting.
- **Address height-varying neighbour shading** explicitly (OpenUBEM models it).
- **No fabricated precision;** flag GAPs with a defensible default.
- **Stay on topic.** If it is not about vertical aggregation, cut it.
