# Deep-Research Prompt M01 — MISSING-DATA LANDSCAPE & MECHANISMS in UBEM (what goes missing, why, and the remedy taxonomy)

> SCOPE GUARD — READ FIRST. This is the **framing / taxonomy** task for the whole imputation set. Its
> job is to map the solution space so the four downstream tiers (`M03` stats, `M04` ML, `M05` deep,
> `M06` spatial) scope cleanly. Answer two things only: (1) **which UBEM inputs go missing, how often,
> and under which missing-data mechanism** (MCAR/MAR/MNAR), and (2) **the full taxonomy of remedies**
> (list-wise drop / single default / statistical impute / ML impute / external-data fusion / hard-fail)
> and when each is appropriate. Do NOT benchmark specific method accuracy (that is `M03`–`M06`) and do
> NOT redesign OpenUBEM's classifier (that is the `input-framework/` set). See
> `00_README_imputation_prompt_set.md` for shared facts, roster, conventions.

---

## What this document is

A structured landscape survey. OpenUBEM currently handles missingness per-stage with no unifying model
of *why* each input is missing or *which* remedy class is warranted. Before building an imputation
subsystem we need the field's own map: for the inputs a bottom-up, OSM-fed UBEM actually consumes,
which go missing, under what mechanism, and what the literature considers the appropriate response. The
in-repo İşeri et al. paper (`../resources/…docx.md`) already argues that "each pattern of missing data
may require a different imputation technique" and that mechanism analysis must precede method choice —
this prompt tests and sources that claim against the broader literature.

## Role

UBEM / missing-data-methods research analyst. Ground the mechanism taxonomy in the canonical
missing-data literature (Rubin 1976; Little & Rubin, *Statistical Analysis with Missing Data*; van
Buuren, *Flexible Imputation of Missing Data*) and the *application* of it to building-stock / UBEM
data in peer-reviewed UBEM work (İşeri et al.; Wang et al.; Nägeli et al.; Mastrucci et al.; the
building-stock-characterization literature the in-repo paper cites). Distinguish clearly between
missing-data *theory* and its *documented use on building attributes*.

## Why this matters (so you scope correctly)

The remedy must match the mechanism. Imputing an MCAR gap with a group-wise mean is defensible;
imputing an MNAR gap (e.g. `year_built` missing *because* the building is informal/unpermitted, i.e.
missingness correlates with the very value) the same way injects systematic bias into the entire
building-stock EUI. If OpenUBEM picks one imputer and applies it blindly to every missing input, it
will be right for some and biased for others. This prompt tells the manager which inputs fall in which
mechanism class, so the implementation plan can route each input to an appropriate tier instead of a
one-size-fits-all fill.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Per-input missingness profile

One row per OpenUBEM missing-prone input. "Typical missing rate" = what the UBEM/OSM literature reports
for that field at city scale (cite); "Likely mechanism" = MCAR / MAR / MNAR with a one-line reason.

| OpenUBEM input | Typical missing rate at city scale (cite) | Likely mechanism (MCAR/MAR/MNAR) + why | OpenUBEM's current handling (for comparison) | Source |
|---|---|---|---|---|
| `building:levels` (floor count) |  |  | Heuristic `height//3.5`, else `1`; flag `HEURISTIC_HEIGHT`/`HEURISTIC_DEFAULT` |  |
| `height` (m) |  |  | Derived `levels × 3.5` when absent |  |
| `year_built` / `start_date` (vintage) |  |  | NaN → `DOERefPre1980` (oldest, U×1.6); flag `VINTAGE_NAN_PERMISSIVE_DEFAULT` |  |
| `building`/`amenity`/`shop`/`office` use tags |  |  | Unresolved → `OpenUBEMUnknown` (LOW) or size-bucketed office |  |
| `footprint_area_m2` (DHW/cooking) |  |  | `.get(...) or 400.0` — silent (Tier-B) |  |
| Envelope U-value / construction params |  |  | KDE-fill from sibling climate zones; flag `KDE_IMPUTED` |  |
| HVAC `cop` / fan / efficiency |  |  | `.get(key) or default` — silent (Tier-B) |  |

### Table 2 — Remedy taxonomy (the classes the implementation plan will choose among)

| Remedy class | What it is | When it is the *right* choice (mechanism / data conditions) | Known failure mode | Representative source |
|---|---|---|---|---|
| List-wise deletion (drop the building) |  |  |  |  |
| Single deterministic default (constant / archetype value) |  |  |  |  |
| Group-wise / stratified statistic (mean/median/mode by strata) |  |  |  |  |
| Distribution sampling (KDE / parametric draw) |  |  |  |  |
| Regression / model-based single imputation |  |  |  |  |
| Multiple imputation (MICE-family) |  |  |  |  |
| ML / deep imputation |  |  |  |  |
| External-data fusion (fetch the real value) |  |  |  |  |
| Hard-fail (refuse to guess) |  |  |  |  |

### Table 3 — Mechanism → recommended remedy tier (the routing rule)

| Mechanism | Recommended remedy class(es) | Why | Source |
|---|---|---|---|
| MCAR |  |  |  |
| MAR |  |  |  |
| MNAR |  |  |  |

### Table 4 — Does the field agree with OpenUBEM's "consequence-tiered" split?

OpenUBEM chose Tier-A/B/C partly by *how consequential a wrong guess is* (drop→default→impute→fail).

| Question | Literature answer | Source |
|---|---|---|
| Is "route the remedy by downstream consequence, not just mechanism" a recognized practice? |  |  |
| Do UBEM studies distinguish geometry-input missingness from semantic-input missingness in method choice? |  |  |
| Is there precedent for *hard-failing* rather than imputing a critical input (e.g. weather/climate zone)? |  |  |

---

## Part C — Synthesis (the routing recommendation)

Give: (1) a one-paragraph verdict on **which OpenUBEM inputs are safe to impute vs. which are MNAR-risky
and should be flagged/fetched rather than guessed**; (2) whether the literature supports a **single
default imputer for all inputs** or a **per-input routing** by mechanism/consequence (the İşeri paper's
implicit position); (3) an explicit statement of **which remedy classes the downstream prompts should
cover** (confirming the M03–M07 split is the right decomposition, or proposing a change); (4) any input
in Table 1 where OpenUBEM's *current* handling is mechanism-inappropriate (e.g. `year_built → oldest
vintage` when the mechanism is MNAR toward *newer* informal buildings) — this is directly actionable.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C synthesis.
3. Cite the missing-data-theory source for every mechanism claim and a UBEM-application source for every
   building-attribute claim — keep the two kinds of citation distinct.
4. **"Confidence and caveats":** which input's mechanism classification is least certain.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **Classify every input in Table 1 into MCAR/MAR/MNAR** with a reason — no "unknown" without stating
  what evidence would resolve it.
- **Distinguish theory citations from building-application citations.**
- **Respect the two hard constraints** (zero-fitted-parameters, mandatory provenance) when saying which
  remedies are admissible.
- **No fabricated precision;** flag GAPs. **Stay on topic** — mechanisms and remedy *taxonomy* only, not
  per-method accuracy benchmarks (`M03`–`M06`).
