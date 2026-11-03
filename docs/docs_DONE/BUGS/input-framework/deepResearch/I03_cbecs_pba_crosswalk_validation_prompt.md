# Deep-Research Prompt I03 — ARCHETYPE ↔ CBECS PBA crosswalk (is the national-benchmark mapping defensible?)

> SCOPE GUARD — READ FIRST. This is a **crosswalk-validation** task. The deliverable is a sourced
> check of `cbecs_pba_map.json` — the table that maps each OpenUBEM archetype to a CBECS 2018
> Principal Building Activity (PBA) numeric code for national-benchmark validation gates (NMBE,
> CV(RMSE), R², KS_D against the CBECS 2018 survey). It is NOT about how a building gets its
> archetype in the first place (`I02`) and NOT about the three city-level ground-truth datasets
> (NYC LL84 / LA EBEWE / Austin CBECS-proxy — already documented in
> `docs/docs_VALIDATION/step1/external_literature/`). If you are writing about anything other than
> **whether the archetype→PBA-code mapping itself is correct and complete**, stop and return to the
> tables. See `00_README_input_classification_prompt_set.md` for the decision, shared facts, roster,
> conventions.

---

## What this document is

A fill-in-the-blanks validation request. `cbecs_pba_map.json` maps OpenUBEM's archetypes onto CBECS
2018 PBA codes as follows (current state, verbatim):

| OpenUBEM archetype(s) | CBECS 2018 PBA code (current) |
|---|---|
| SmallOffice, SmallOfficeDetailed, MediumOffice, MediumOfficeDetailed, LargeOffice, LargeOfficeDetailed, TallBuilding, SuperTallBuilding | 2 |
| RetailStandalone | 25 |
| RetailStripmall | 23 |
| SuperMarket | 6 |
| FullServiceRestaurant, QuickServiceRestaurant | 15 |
| SmallHotel, LargeHotel | 18 |
| Hospital | 16 |
| Outpatient | 8 |
| PrimarySchool, SecondarySchool, College | 14 |
| Courthouse | 7 |
| Laboratory | 4 |
| Warehouse | 5 |
| MidriseApartment, HighriseApartment | excluded (`null`) — "no clean CBECS 2018 PBA" |
| SmallDataCenterHighITE/LowITE, LargeDataCenterHighITE/LowITE | excluded (`null`) — "no clean CBECS 2018 PBA" |
| OpenUBEMUnknown | `"distribution_only"` (included in distribution gates, excluded from per-archetype scoring) |

This table was authored once, directly from the CBECS codebook, and has never been checked against
how other published UBEM validation studies that also use CBECS as a national benchmark constructed
their own archetype↔PBA crosswalk.

## Role

Building-energy benchmarking research analyst, specifically on **CBECS 2018** (EIA Commercial
Buildings Energy Consumption Survey) usage in UBEM validation literature. Trace every claim to the
**CBECS 2018 public-use microdata codebook** (the authoritative PBA code list and definitions), the
**DOE/PNNL Commercial Reference/Prototype Buildings** documentation (which itself was originally
built to span CBECS building-activity categories), and any **published UBEM validation study that
scores per-archetype results against CBECS** (e.g. studies validating URBANopt, AutoBEM, or similar
fleet-scale models against CBECS).

## Why this matters (so you scope correctly)

Five OpenUBEM archetypes collapse onto PBA 2 ("Office"); both restaurant archetypes collapse onto
PBA 15; both hotel archetypes onto PBA 18; all three education archetypes onto PBA 14. If CBECS
itself reports separate statistics for sub-categories OpenUBEM is currently lumping together (e.g.
CBECS distinguishing limited-service vs. full-service food establishments, or education levels), the
benchmark comparison is coarser than it needs to be and could mask a real per-sub-type bias. Equally
important: **residential and data-center archetypes are entirely excluded** from CBECS scoring today
— CBECS only covers commercial buildings (residential national benchmarking would need RECS, the
Residential Energy Consumption Survey, a separate EIA survey), so this gap may simply be correct and
unavoidable, or there may be a defensible residential crosswalk OpenUBEM hasn't built yet.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — CBECS 2018 PBA code definitions (ground truth)

| PBA code | CBECS 2018 official category name | Does CBECS report any finer sub-breakdown within this code (and if so, by what variable)? | Source |
|---|---|---|---|
| 2 |  |  |  |
| 4 |  |  |  |
| 5 |  |  |  |
| 6 |  |  |  |
| 7 |  |  |  |
| 8 |  |  |  |
| 14 |  |  |  |
| 15 |  |  |  |
| 16 |  |  |  |
| 18 |  |  |  |
| 23 |  |  |  |
| 25 |  |  |  |

### Table 2 — Many-to-one collapses: is finer CBECS resolution available?

| OpenUBEM archetypes collapsed together | Shared PBA code | Could CBECS support splitting these (sub-variable exists)? | Recommendation | Source |
|---|---|---|---|---|
| Small/Medium/Large/Detailed Office + TallBuilding + SuperTallBuilding | 2 |  |  |  |
| FullServiceRestaurant + QuickServiceRestaurant | 15 |  |  |  |
| SmallHotel + LargeHotel | 18 |  |  |  |
| PrimarySchool + SecondarySchool + College | 14 |  |  |  |

### Table 3 — Residential exclusion

| Question | Answer | Source |
|---|---|---|
| Does CBECS 2018 cover any residential building types at all? |  |  |
| What EIA survey is the correct national-benchmark source for residential (RECS)? |  |  |
| Does RECS have housing-type codes that map cleanly onto MidriseApartment/HighriseApartment? |  |  |
| Have any published UBEM studies built a residential archetype↔RECS crosswalk? |  |  |

### Table 4 — Data-center exclusion

| Question | Answer | Source |
|---|---|---|
| Does CBECS 2018 have any PBA code that plausibly covers data centers (even imperfectly)? |  |  |
| How have published studies that include data centers in a CBECS-benchmarked fleet handled this (excluded, folded into Office, used a different source)? |  |  |
| Is OpenUBEM's current full exclusion the most defensible option, or is there a better-fit code? |  |  |

---

## Part C — Synthesis (verdict on the current crosswalk)

Give: (1) whether each many-to-one collapse in Table 2 is appropriate given CBECS's actual
resolution, or should be split (name the CBECS sub-variable that would enable it); (2) whether the
residential exclusion is correct-and-unavoidable or whether a RECS-based crosswalk is worth building
as a parallel benchmark (with a concrete proposed mapping if precedent exists); (3) whether the
data-center exclusion should stay as-is or use a specific better-fit PBA code; (4) any PBA code in
the current table that may simply be **wrong** (i.e. CBECS defines it differently than OpenUBEM
assumed).

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C verdict.
3. Cite the CBECS 2018 codebook explicitly (document name, table/variable name, page).
4. **"Confidence and caveats":** which exclusion (residential/data-center) is least certain.
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **Use the actual CBECS 2018 codebook**, not a secondary summary, for every PBA code definition.
- **Give an explicit yes/no per many-to-one collapse** on whether CBECS supports a finer split.
- **State plainly whether the residential/data-center exclusions are correct as currently coded.**
- **No fabricated precision;** flag GAPs. **Stay on topic** — the archetype↔PBA crosswalk only, not
  the three city-level ground-truth datasets (those are out of scope here).
