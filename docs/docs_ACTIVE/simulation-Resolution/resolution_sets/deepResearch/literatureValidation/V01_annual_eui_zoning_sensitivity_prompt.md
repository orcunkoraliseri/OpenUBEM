# Deep-Research Prompt V01 — ANNUAL-EUI zoning-resolution sensitivity (the building-scale envelope)

> SCOPE GUARD — READ FIRST. This is a **published-range** task. The deliverable is a sourced, quantitative
> account of **how much a building's annual whole-building EUI changes when thermal-zoning resolution is
> coarsened** — single-zone vs per-floor vs core/perimeter vs detailed multi-zone — at the **individual
> building scale**, holding all non-geometry inputs identical. It is NOT about *how* to build the zones
> (covered in `../layoutMapping/RESULT_L01..L06`), and NOT about district aggregation (that is V05); it is
> purely the **magnitude and direction of the annual-EUI error from zoning resolution**, with sources.
> If you are writing about anything other than **a numeric annual-EUI range tied to zoning resolution and
> its source**, stop and return to the tables. See `00_README_literature_validation_prompt_set.md` for the
> decision, shared facts, mode map, seed references, conventions.

---

## What this document is

A fill-in-the-blanks evidence table. OpenUBEM lets a user force `building` (single zone), `floor`
(per-storey), or `fast_zone` (core/perimeter) instead of the adaptive `auto` default, and its T08 sweep
found `building`-mode annual **site EUI runs 0–14 % below `floor` mode per cell** (median ratio 0.86–1.00,
largest gap in tall/dense cells). We need the **published envelope** for that effect: across the UBEM and
building-simulation literature, by how much does annual EUI move as zoning is coarsened, and in which
direction? Treat each cell as a question; fill with a sourced numeric range or a GAP.

## Role

UBEM validation / building-energy-simulation research analyst. Trace every range to a peer-reviewed study
or tool-accuracy report that **compares the same building at different zoning resolutions with identical
loads/schedules/envelope/weather** (an input-invariant comparison — the only kind that isolates the
zoning effect). Prioritise: **Dogan & Reinhart 2017 (Shoeboxer)**, **Chen & Hong (CityBES)**, **Cerezo
Davila 2017 (Boston)**, **Johari 2022 (review)**, **Faure 2022** and other single-vs-multi-zone
sensitivity studies, and DOE/PNNL prototype-vs-simplified comparisons. SI throughout.

## Why this matters (so you scope correctly)

Zero-fitted-parameters means OpenUBEM cannot calibrate a zoning delta away — it must *survive* comparison
to the literature. The manager will mark OpenUBEM's `building/floor` ratio **in-envelope** only if the
published annual-EUI zoning sensitivity brackets it. A single anecdotal number is not enough: we need the
central tendency **and** the spread (it depends on building depth, aspect ratio, glazing, and climate), so
that a large delta on a deep/tall building can be recognised as expected rather than a bug.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Annual whole-building EUI error vs zoning resolution (input-invariant studies)

| Study (author, venue, year) | Building type(s) | Coarse model | Reference (fine) model | Annual EUI Δ (signed %, coarse−fine) | Climate | Source detail (page/fig) |
|---|---|---|---|---|---|---|
|  |  | single-zone |  |  |  |  |
|  |  | per-floor |  |  |  |  |
|  |  | core/perimeter |  |  |  |  |

*(Add rows per study; sign convention: negative = coarse under-predicts annual EUI. State it per row.)*

### Table 2 — What drives the size of the delta

| Driver | Direction of influence on the zoning-EUI error | Published magnitude / rule | Source |
|---|---|---|---|
| Building depth / floor-plate size (perimeter-to-core ratio) |  |  |  |
| Number of storeys / height |  |  |  |
| Window-to-wall ratio / glazing |  |  |  |
| Climate (heating- vs cooling-dominated) |  |  |  |
| Aspect ratio / footprint irregularity |  |  |  |

### Table 3 — The single→multi→detailed ladder (outer bounds)

| Resolution step | Typical annual-EUI change reported | Is it monotonic? | Source |
|---|---|---|---|
| single-zone → per-floor |  |  |  |
| per-floor → core/perimeter |  |  |  |
| core/perimeter → full detailed (DOE multi-zone) |  |  |  |

### Table 4 — OpenUBEM cross-check

| OpenUBEM observation | Published envelope (from Tables 1–3) | In-envelope? (Y/N/partial) | Note |
|---|---|---|---|
| `building/floor` annual site-EUI median 0.86–1.00 (0–14 % below), largest in tall/dense cells |  |  |  |

---

## Part C — Synthesis (the envelope for OpenUBEM)

Give: (1) the **best single numeric range** for building-scale annual-EUI zoning sensitivity that the
literature supports (central value + spread), stated as signed % of the finer model; (2) whether
OpenUBEM's `building/floor` = 0.86–1.00 (i.e. −14 %…0 %) sits **inside** that range, and specifically
whether the **tall/dense-cell** end (largest gap) is still expected; (3) the conditions under which a
zoning-EUI delta should be flagged **out-of-envelope / investigate**. Name the published source for each
bound. Flag any regime with no published range as a GAP.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C envelope + the explicit in/out-of-envelope verdict for OpenUBEM's 0.86–1.00 ratio.
3. Cite each study explicitly (author, venue, year, and the figure/table the number comes from).
4. **"Confidence and caveats":** where the literature is thin or conflicting, and which building regime is
   least covered.
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **Only input-invariant comparisons** (same loads/schedules/envelope/weather, zoning varied) count for
  Table 1 — reject calibrated-vs-measured deltas that confound other error sources; note them separately.
- **Return numeric ranges in signed %**, with the sign convention stated per row — not just "higher/lower".
- **Cover at least single-zone, per-floor, and core/perimeter** coarse models against a finer reference.
- **Give the explicit in-envelope / out-of-envelope call** for OpenUBEM's 0.86–1.00 `building/floor` ratio.
- **No fabricated precision;** flag GAPs. **Stay on topic** — annual whole-building EUI vs zoning
  resolution, building scale only (heating/cooling split → V02; district aggregation → V05).
