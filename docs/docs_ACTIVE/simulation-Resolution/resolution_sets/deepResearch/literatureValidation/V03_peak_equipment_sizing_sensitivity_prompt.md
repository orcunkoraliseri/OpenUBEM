# Deep-Research Prompt V03 — PEAK demand & EQUIPMENT-SIZING sensitivity to zoning resolution

> SCOPE GUARD — READ FIRST. This is a **published-range** task. The deliverable is a sourced, quantitative
> account of **how coarsening thermal-zoning resolution changes PEAK heating/cooling demand and AUTOSIZED
> equipment/HVAC capacity** — single-zone vs per-floor vs core/perimeter vs detailed multi-zone — at the
> **individual building scale**, holding all non-geometry inputs identical. This is the effect the
> literature reports as the **largest**: coarse modes can mis-size peak and autosized capacity by well over
> 100 % because lumping zones destroys the coincidence/diversity of individual-zone peaks. It is NOT annual
> energy (that is V01/V02); it is purely the **magnitude and direction of the peak-demand and
> equipment-sizing error from zoning resolution**, with sources.
> If you are writing about anything other than **a numeric peak-or-capacity range tied to zoning resolution
> and its source**, stop and return to the tables. See `00_README_literature_validation_prompt_set.md` for
> the decision, shared facts, mode map, seed references, conventions.

---

## What this document is

A fill-in-the-blanks evidence table. OpenUBEM lets a user force `building` (single zone), `floor`
(per-storey), or `fast_zone` (core/perimeter) instead of the adaptive `auto` default. Coarse modes are
expected to mis-size peak demand substantially because a single air node cannot resolve when each zone
actually peaks. **Important scoping fact: OpenUBEM v1 does NOT autosize equipment on the coarse modes and
does not report peak as a validated output — peak-demand validation is a GAP until AMI/interval-meter data
exists.** This prompt is therefore **report-only**: it commissions the published peak/sizing envelope so
the manager can state, with citations, how large the peak error *would* be, and justify why coarse modes
must not be used for sizing/peak studies. Treat each cell as a question; fill with a sourced numeric range
or a GAP.

## Role

UBEM validation / building-energy-simulation research analyst. Trace every range to a peer-reviewed study
or tool-accuracy report that **compares the same building at different zoning resolutions with identical
loads/schedules/envelope/weather** (an input-invariant comparison — the only kind that isolates the
zoning effect) **and reports peak demand or autosized capacity**, not just annual energy. Prioritise:
**Dogan & Reinhart 2017 (Shoeboxer)**, **Chen & Hong (CityBES)**, **Cerezo Davila 2017 (Boston)**,
**Johari 2022 (review)**, **Faure 2022** and other single-vs-multi-zone sensitivity studies, ASHRAE
load-calculation / sizing literature, and DOE/PNNL prototype-vs-simplified comparisons that report design
loads. SI throughout (kW, W/m² for demand; kW or tons→kW for capacity, note conversion).

## Why this matters (so you scope correctly)

Zero-fitted-parameters means OpenUBEM cannot calibrate a zoning delta away — it must *survive* comparison
to the literature. Peak and sizing are where zoning resolution bites hardest: annual energy partially
self-averages, but coincident peak does not, so a lumped zone can under- or over-size design capacity by a
factor. The manager needs the published magnitude to (a) document, with sources, why OpenUBEM v1 correctly
refrains from sizing on coarse modes, and (b) set the envelope for a future peak-validation step once
interval data is available. Because v1 does not use coarse modes for sizing, the OpenUBEM cross-check here
is explicitly **report-only** — there is no observed OpenUBEM peak delta to bracket yet, only the
literature envelope that justifies the design decision.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — PEAK demand error vs zoning resolution (input-invariant studies)

| Study (author, venue, year) | Building type(s) | Coarse model | Reference (fine) model | Peak-demand Δ (signed %, coarse−fine) | Heating or cooling peak | Source detail (page/fig) |
|---|---|---|---|---|---|---|
|  |  | single-zone |  |  |  |  |
|  |  | per-floor |  |  |  |  |
|  |  | core/perimeter |  |  |  |  |

*(Add rows per study; sign convention: negative = coarse under-predicts peak. State it per row.)*

### Table 2 — Autosized capacity / equipment-sizing error vs zoning resolution

| Study (author, venue, year) | Building type(s) | Coarse model | Reference (fine) model | Autosized-capacity Δ (signed %, coarse−fine) | Equipment/system type | Source detail (page/fig) |
|---|---|---|---|---|---|---|
|  |  | single-zone |  |  |  |  |
|  |  | per-floor |  |  |  |  |
|  |  | core/perimeter |  |  |  |  |

### Table 3 — Load-diversity / coincidence effect (why lumping zones distorts coincident peak)

| Mechanism aspect | How lumping zones distorts the coincident peak | Published magnitude / diversity factor | Direction (coarse over- or under-sizes) | Source |
|---|---|---|---|---|
| Loss of zone-level load diversity (non-coincident peaks summed as coincident) |  |  |  |  |
| Core/perimeter peak-timing offset collapsed to one node |  |  |  |  |
| Block/whole-building autosize vs sum-of-zone autosize |  |  |  |  |
| Sensitivity to number of zones lumped / building depth |  |  |  |  |

### Table 4 — OpenUBEM cross-check (report-only)

| OpenUBEM observation | Published envelope (from Tables 1–3) | In-envelope? (Y/N/partial/N-A report-only) | Note |
|---|---|---|---|
| Coarse modes expected to mis-size peak substantially; OpenUBEM v1 does NOT size on coarse modes — peak-demand validation is a GAP until AMI data exists (report-only) |  |  |  |

---

## Part C — Synthesis (the peak/sizing envelope for OpenUBEM)

Give: (1) the **best single numeric range** for building-scale **peak-demand** zoning sensitivity and,
separately, **autosized-capacity** zoning sensitivity that the literature supports (central value +
spread), each stated as signed % of the finer model; (2) an explicit statement of how much **larger** the
peak/sizing error is than the annual-energy error (V01/V02), with sources — the core justification for
not sizing on coarse modes; (3) the load-diversity mechanism and any published diversity/coincidence
factors; (4) since OpenUBEM v1 does not size on coarse modes, frame the verdict as **report-only** and
state the envelope a future AMI-based peak validation would test against. Name the published source for
each bound. Flag any regime with no published range as a GAP.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C envelope + the explicit report-only framing for OpenUBEM (no observed peak delta yet).
3. Cite each study explicitly (author, venue, year, and the figure/table the number comes from).
4. **"Confidence and caveats":** where the literature is thin or conflicting, and which system type /
   climate is least covered.
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **Only input-invariant comparisons** (same loads/schedules/envelope/weather, zoning varied) count for
  Tables 1–2 — reject calibrated-vs-measured deltas that confound other error sources; note them separately.
- **Report PEAK demand and AUTOSIZED capacity — not annual energy** (annual → V01/V02).
- **Return numeric ranges in signed %**, with the sign convention stated per row — not just "higher/lower".
- **Cover at least single-zone, per-floor, and core/perimeter** coarse models against a finer reference.
- **Frame the OpenUBEM cross-check as report-only** — v1 does not size on coarse modes; there is no
  observed OpenUBEM peak delta to bracket, only the literature envelope.
- **No fabricated precision;** flag GAPs. **Stay on topic** — peak demand and equipment sizing vs zoning
  resolution, building scale only (annual energy → V01/V02).

---

*OpenUBEM resolution-mode — literature-validation sub-set. Markdown only; binding specs remain
`docs/docs_main/`. 2026-07-01.*
