# Deep-Research Prompt V02 — HEATING / COOLING resolution effect (end-use split of the zoning error)

> SCOPE GUARD — READ FIRST. This is a **published-range** task. The deliverable is a sourced, quantitative
> account of **how coarsening thermal-zoning resolution changes ANNUAL HEATING and ANNUAL COOLING EUI
> separately** — single-zone vs per-floor vs core/perimeter vs detailed multi-zone — at the **individual
> building scale**, holding all non-geometry inputs identical. The driving mechanism is
> **core-heating / perimeter-cooling cancellation inside one lumped zone**: when opposing loads net out in
> a single air node, heating and cooling both change, usually in opposite ways. It is NOT the
> whole-building EUI envelope (that is V01) and NOT peak/sizing (that is V03); it is purely the
> **end-use-split magnitude and direction of the zoning error for heating and for cooling**, with sources.
> If you are writing about anything other than **a numeric annual heating-or-cooling range tied to zoning
> resolution and its source**, stop and return to the tables. See
> `00_README_literature_validation_prompt_set.md` for the decision, shared facts, mode map, seed
> references, conventions.

---

## What this document is

A fill-in-the-blanks evidence table. OpenUBEM lets a user force `building` (single zone), `floor`
(per-storey), or `fast_zone` (core/perimeter) instead of the adaptive `auto` default. Its own expectation
is `zone ≥ floor ≥ building` for annual heating, because a single lumped zone lets a warm core cancel a
cold perimeter (and vice versa for cooling), suppressing the separately-metered heating and cooling that a
multi-zone model would resolve. We need the **published envelope** for that split: across the UBEM and
building-simulation literature, by how much do annual **heating** and annual **cooling** each move as
zoning is coarsened, and in which direction? Treat each cell as a question; fill with a sourced numeric
range or a GAP.

## Role

UBEM validation / building-energy-simulation research analyst. Trace every range to a peer-reviewed study
or tool-accuracy report that **compares the same building at different zoning resolutions with identical
loads/schedules/envelope/weather** (an input-invariant comparison — the only kind that isolates the
zoning effect) **and reports heating and cooling as separate end uses**. Prioritise: **Dogan & Reinhart
2017 (Shoeboxer)**, **Chen & Hong (CityBES)**, **Cerezo Davila 2017 (Boston)**, **Johari 2022 (review)**,
**Faure 2022** and other single-vs-multi-zone sensitivity studies, and DOE/PNNL prototype-vs-simplified
comparisons that break out heating vs cooling. SI throughout.

## Why this matters (so you scope correctly)

Zero-fitted-parameters means OpenUBEM cannot calibrate a zoning delta away — it must *survive* comparison
to the literature. A whole-building EUI that looks in-envelope (V01) can hide two large, opposite end-use
errors that partially cancel: coarse zoning can under-predict heating while over-predicting cooling (or the
reverse), so the net EUI moves little while each end use is badly wrong. The manager therefore needs the
**separate** heating and cooling envelopes, with their climate dependence, to know whether OpenUBEM's
end-use split is physically expected. OpenUBEM's internal expectation is a heating effect on the order of
**~10–26 %** with peak-sizing implications — but that is an *internal* number and must NOT be cited as
external evidence; it only tells you the regime the published ranges must bracket.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Annual HEATING EUI error vs zoning resolution (input-invariant studies)

| Study (author, venue, year) | Building type(s) | Coarse model | Reference (fine) model | Annual HEATING Δ (signed %, coarse−fine) | Climate | Source detail (page/fig) |
|---|---|---|---|---|---|---|
|  |  | single-zone |  |  |  |  |
|  |  | per-floor |  |  |  |  |
|  |  | core/perimeter |  |  |  |  |

*(Add rows per study; sign convention: negative = coarse under-predicts annual heating. State it per row.)*

### Table 2 — Annual COOLING EUI error vs zoning resolution (input-invariant studies)

| Study (author, venue, year) | Building type(s) | Coarse model | Reference (fine) model | Annual COOLING Δ (signed %, coarse−fine) | Climate | Source detail (page/fig) |
|---|---|---|---|---|---|---|
|  |  | single-zone |  |  |  |  |
|  |  | per-floor |  |  |  |  |
|  |  | core/perimeter |  |  |  |  |

*(Add rows per study; sign convention: negative = coarse under-predicts annual cooling. State it per row.)*

### Table 3 — The load-cancellation mechanism (single zone nets opposing core/perimeter loads)

| Mechanism aspect | How a single lumped zone nets opposing loads | Published magnitude / rule | Climate dependence (heating- vs cooling-dominated) | Source |
|---|---|---|---|---|
| Core heating vs perimeter cooling cancellation |  |  |  |  |
| Simultaneous heating+cooling suppressed to net demand |  |  |  |  |
| Direction: does coarse under-predict heating, cooling, or both? |  |  |  |  |
| Sensitivity to floor-plate depth / perimeter-to-core ratio |  |  |  |  |

### Table 4 — OpenUBEM cross-check

| OpenUBEM observation | Published envelope (from Tables 1–3) | In-envelope? (Y/N/partial) | Note |
|---|---|---|---|
| Expected `zone ≥ floor ≥ building` for annual heating; single-zone core/perimeter cancellation splits the EUI error by end use |  |  |  |

---

## Part C — Synthesis (the end-use envelope for OpenUBEM)

Give: (1) the **best single numeric range** for building-scale annual **heating** zoning sensitivity and,
separately, annual **cooling** zoning sensitivity that the literature supports (central value + spread),
each stated as signed % of the finer model; (2) whether the published evidence confirms the
`zone ≥ floor ≥ building` heating ordering and states the corresponding cooling ordering; (3) how the two
end-use errors trade off against each other by climate (heating-leaning NYC/CZ 4A, mixed Austin/CZ 2A,
cooling-leaning LA/CZ 3B); (4) the conditions under which a heating or cooling zoning delta should be
flagged **out-of-envelope / investigate**. Name the published source for each bound. Flag any regime with
no published range as a GAP.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C envelope + the explicit in/out-of-envelope verdict for OpenUBEM's `zone ≥ floor ≥ building`
   heating expectation and the corresponding cooling direction.
3. Cite each study explicitly (author, venue, year, and the figure/table the number comes from).
4. **"Confidence and caveats":** where the literature is thin or conflicting, and which end use / climate
   is least covered.
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **Only input-invariant comparisons** (same loads/schedules/envelope/weather, zoning varied) count for
  Tables 1–2 — reject calibrated-vs-measured deltas that confound other error sources; note them separately.
- **Report heating and cooling as SEPARATE end uses** — a combined-EUI number belongs in V01, not here.
- **Return numeric ranges in signed %**, with the sign convention stated per row — not just "higher/lower".
- **Cover at least single-zone, per-floor, and core/perimeter** coarse models against a finer reference,
  for both heating and cooling.
- **Give the explicit in-envelope / out-of-envelope call** for OpenUBEM's `zone ≥ floor ≥ building` heating
  ordering.
- **No fabricated precision;** flag GAPs. **Stay on topic** — annual heating and cooling end-use split vs
  zoning resolution, building scale only (whole-building EUI → V01; peak/sizing → V03).

---

*OpenUBEM resolution-mode — literature-validation sub-set. Markdown only; binding specs remain
`docs/docs_main/`. 2026-07-01.*
