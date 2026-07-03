# Deep-Research Prompt L03 — ASHRAE 90.1 APP-G CORE/PERIMETER ZONING & ITS GENERALIZATION TO NON-RECTANGULAR FOOTPRINTS

> SCOPE GUARD — READ FIRST. This prompt pins down the **rule OpenUBEM already uses** and asks how the
> standard + the field extend it beyond rectangles. Deliver: (1) the exact definition of ASHRAE 90.1-2019
> Appendix G / LEED automatic core-and-perimeter thermal zoning — the perimeter depth, the "4 perimeter +
> 1 core" convention, and its stated assumptions — and (2) how standards, tools, and papers **generalize
> that rule to L / U / T / concave / courtyard footprints** where a single inward offset does not yield a
> clean core. Do NOT survey tools broadly (that's `L02`) and do NOT specify the offset/skeleton algorithms
> at implementation level (that's `L05`). See `00_README_layoutgenerator_prompt_set.md` for shared facts.

---

## What this document is

The authoritative-rule reference for the whole set. OpenUBEM's `perimeter_core` is a direct implementation
of the App-G convention: `core = footprint.buffer(-4.57 m)`, 4 perimeter zones + 1 core, 4.57 m (15 ft)
perimeter depth. That convention is *defined for rectangular floor plates*. The manager needs to know,
with citations: is 4.57 m the correct, current, published depth? Is "4 perimeter zones" mandated or just
conventional? And crucially — **what does the standard/field say to do when the plate is L/U/O-shaped**,
where "4 perimeter + 1 core" is ill-defined? This is the rulebook `layoutGenerator.py` must follow to
stay zero-fitted-parameters.

## Role

Building-energy-standards analyst. Ground every claim in the primary source: **ASHRAE Standard 90.1-2019
Appendix G** (esp. the baseline-building thermal-block / zoning rules — G3.1, the perimeter/core
definition), the **ASHRAE 90.1 User's Manual**, **LEED / PNNL modeling guidance**, the **DOE prototype
building documentation** (how the reference models are zoned), and any peer-reviewed treatment of
automated App-G zoning (e.g. OpenStudio/PNNL zoning-tool papers). Quote clause numbers and exact
dimensions. Where the standard is silent on non-rectangular plates, say so explicitly and cite the
tool/paper conventions that fill the gap.

## Why this matters (so you scope correctly)

`layoutGenerator.py` must derive its geometry from a citable rule, not a tuned knob — that is the
zero-fitted-parameters constraint. If the perimeter depth is 4.57 m per App-G, OpenUBEM is correct; if the
standard actually specifies a different depth or a range, OpenUBEM must change. And when the footprint is
non-rectangular, the generator needs a *defensible* rule for placing perimeter and core — this prompt
establishes whether that rule exists in the standard, in tool conventions, or must be flagged as a
manager decision.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — The core/perimeter rule as written

| Rule element | What App-G 90.1-2019 (or cited authority) specifies | Clause / page | OpenUBEM current value | Match? |
|---|---|---|---|---|
| Perimeter depth from exterior wall |  |  | 4.57 m (15 ft) |  |
| Number of perimeter zones per floor |  |  | 4 (geomeppy native) |  |
| Core zone definition |  |  | `footprint.buffer(-4.57)` |  |
| Orientation split (per façade / cardinal) |  |  | geomeppy 4-way |  |
| Minimum floor area / height to warrant zoning |  |  | commercial ≥500 m² (OpenUBEM rule) |  |
| Treatment of floors (ground / mid / top separate?) |  |  | per-floor stack |  |

### Table 2 — What the standard/field says for NON-rectangular plates

| Footprint condition | Does App-G / the field give an explicit rule? | The rule or convention (perimeter follows all exterior edges? decompose first?) | Source |
|---|---|---|---|
| Concave / L / U / T plate |  |  |  |
| Courtyard / O-shape (interior ring — perimeter on *both* outer and inner walls?) |  |  |  |
| Very deep plate (core dominates) |  |  |  |
| Narrow plate (< 2× perimeter depth wide → no core) |  |  |  |
| Multiple disconnected wings |  |  |  |

### Table 3 — "Perimeter follows the wall" vs. "4 cardinal zones"

The key generalization question: on an L-shape, is the perimeter one continuous shape-following band
(inner-offset ring) or still forced into 4 orientation zones?

| Approach | Who uses it (standard / tool / paper) | How perimeter zones are counted on an L-shape | Handles courtyard inner wall? | Source |
|---|---|---|---|---|
| Shape-following perimeter band (offset ring) |  |  |  |  |
| 4 cardinal/orientation perimeter zones |  |  |  |  |
| Per-façade perimeter (one zone per exterior edge) |  |  |  |  |
| Decompose-to-rectangles, then rectangular core/perimeter each |  |  |  |  |

### Table 4 — Fit to OpenUBEM

| Question | Answer + source |
|---|---|
| Is OpenUBEM's 4.57 m perimeter depth the correct current App-G value? |  |
| Is the "core < 10 m² → no core" degrade defensible per the standard's intent? |  |
| For a courtyard, should perimeter zones hug the *inner* ring too — and is that in any standard? |  |
| Does any authority bless "decompose L into rectangular wings, core/perimeter each"? |  |

---

## Part C — Synthesis (the rulebook for layoutGenerator)

Give: (1) the **exact, cited core/perimeter rule** OpenUBEM should encode (confirming or correcting the
4.57 m / 4-zone values); (2) the **defensible generalization to non-rectangular plates** — state whether
the field's convention is shape-following-band, per-façade, or decompose-first, and which OpenUBEM should
adopt; (3) an explicit **"GAP — needs manager decision"** for any non-rectangular case the standard does
not cover, with the closest defensible convention and its source; (4) whether residential (currently
forced per-floor) should get core/perimeter under the standard at all, or whether corridor+units (`L06`)
is the residential-appropriate analogue.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C rulebook synthesis.
3. Quote clause numbers / exact dimensions for every standards claim; separate standard-text from
   tool-convention.
4. **"Confidence and caveats":** which non-rectangular rule is least grounded in a primary source.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **Quote the primary standard** (clause + dimension) for the core/perimeter rule — no paraphrase-only.
- **Explicitly address courtyard (inner-ring perimeter) and narrow-plate cases** — these are OpenUBEM's
  two current failure modes.
- **Every recommended dimension must be a published convention** (zero-fitted-parameters) — flag any that
  is not.
- **No fabricated precision;** flag GAPs. **Stay on topic** — the standards rule + its generalization
  only, not tool surveys (`L02`) or algorithm implementation (`L05`).
