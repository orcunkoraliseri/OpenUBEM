# RESEARCH — OPEN-47 T07: tracing the office 25,000 / 100,000 ft² thresholds to a primary source

**Task:** T07, `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_three-new-items-2026-08-12.md`.
**Executor:** C. **Date:** 2026-08-12.

**Verdict (one sentence):** A primary, retrievable, Crossref-verified source for the exact
25,000 ft² / 100,000 ft² office size tiering **was found** — Chen, Hong & Piette (2017),
*Automatic generation and simulation of urban building energy models based on city datasets for
city-scale building retrofit analysis*, Applied Energy 205, 323–335, DOI
`10.1016/j.apenergy.2017.07.128` — but it is **not** the paper `RESULT_I02` cited (Hong et al.
2015), and it presents the numbers as CityBES's own applied case-study classification, not as a
citation to an external standard, so it is a **definitional donor for CityBES's own rule**, not
proof the rule traces to DOE/PNNL/ASHRAE/CBECS.

🔴 Per hard rule 10, every claim below is backed by a file downloaded to the scratchpad
(`C:\Users\o_iseri\AppData\Local\Temp\claude\C--Users-o-iseri-Desktop-OpenUBEM\c7fdc068-fdd8-45d0-803c-b95ae2158842\scratchpad\open47\`,
not committed anywhere) and searched with
`scripts/analysis/open47_threshold_search.py`, which also runs the mandatory non-vacuity control
on every document. Full script output:
`...\scratchpad\open47\open47_threshold_search_output.txt`. I do not cite `RESULT_I02`, the plan,
the register, or any other OpenUBEM document as evidence anywhere below (only as the thing being
checked).

---

## Non-vacuity controls (run first, for every document)

For each document, the script also searches for a string the executor had already read in that
document by eye, before trusting the "not found" result on the real targets. All six pass.

| Document | Control string | Result |
|---|---|---|
| EIA CBECS 2018 flipbook | "Commercial Buildings Energy Consumption Survey" | PASS — page 1 |
| Deru et al. (2011) NREL/TP-5500-46861 | "NREL/TP-5500-46861" | PASS — page 1 (first attempt used the report's title, which line-wraps across three lines in the PDF and is invisible to a per-line search — the control itself caught this; string changed to a title-page code that appears on one line, then passed) |
| PNNL-23269 (2014) | "High-Rise Apartment" | PASS — page 5 |
| Hong et al. (2015), Applied Energy 159 | "Commercial Building Energy Saver" | PASS — page 1 |
| Chen, Hong & Piette (2017), Applied Energy 205 | "City Datasets for City-Scale Building" | PASS — page 1 |
| Chen, Hong & Piette (2017), IBPSA BS2017_071 | "CityBES" | PASS — page 1 |

ASHRAE 90.1 could not be retrieved at all (see Candidate 4) so no control could be run on it;
it is reported as "could not retrieve," not as "not found."

---

## Candidate-by-candidate table

Target strings searched in every document: `2,322`, `2322`, `9,290`, `9290`, `25,000`, `100,000`.

| # | Candidate | Document | Retrieved | Search strings | Result | Verbatim hit / page |
|---|---|---|---|---|---|---|
| 1 | CBECS published size-category bin edges (EIA) | EIA, *CBECS 2018 Building Characteristics Flipbook*, `eia.gov/consumption/commercial/data/2018/pdf/CBECS_2018_Building_Characteristics_Flipbook.pdf` | Yes | all six | **FOUND — 25,000 and 100,000, both as CBECS's general (all-building-type) size-bin edges** | p.9: *"10,001 to 25,000 ... 25,001 to 50,000 ... 50,001 to 100,000 ... 100,001 to 200,000"* — the bin boundaries EIA uses to bucket **all** commercial buildings by size for sampling. |
| 2a | CityBES/CBES — the paper `RESULT_I02` actually cited | Hong, Piette, Chen, Lee, Taylor-Lange, Zhang, Sun, Price (2015), *Commercial Building Energy Saver: An energy retrofit analysis toolkit*, Applied Energy 159, 298–309, DOI `10.1016/j.apenergy.2015.09.002` | Yes (`eta-publications.lbl.gov`) | all six | **not found** | 0 hits on any of the six target strings anywhere in the 12-page text extraction. |
| 2b | CityBES/CBES — the real primary source | Chen, Hong & Piette (2017), *Automatic generation and simulation of urban building energy models based on city datasets for city-scale building retrofit analysis*, Applied Energy 205, 323–335, DOI `10.1016/j.apenergy.2017.07.128` (LBNL author manuscript, `simulationresearch.lbl.gov`) | Yes | all six | **FOUND** | Manuscript p.18 (Table 1, "Summary of the selected 940 buildings in Northeast San Francisco"): *"Small office (<2322 m2 and <= 3 floors)"*, *"Medium office\* (2322 to 9290 m2, <= 5 floors)"*, *"Large office (>9290 m2 or >=6 Floors)"*, with footnote *"the medium office building definition also includes buildings that are <2300 m2 with four or five floors."* This is a **case-study classification table for 940 SF buildings**, not a stated general definitional rule — see caveat below. |
| 2c | CityBES/CBES — the BS2017 conference paper (plan says already searched, not to be re-reported as a hit) | Chen, Hong & Piette (2017), *City-Scale Building Retrofit Analysis: A Case Study using CityBES*, IBPSA BS2017 proceedings, `publications.ibpsa.org/proceedings/bs/2017/papers/BS2017_071.pdf` | Yes (independently re-downloaded and re-searched, not taken on the plan's word) | all six | **not found**, confirmed independently | 0 hits. Only incidental match is the word "offices" in an unrelated sentence about buildings CBES does not yet support. This is consistent with — but derived independently of — the plan's existing claim. |
| 3 | DOE Commercial Prototype / Reference Building documentation | Deru et al. (2011), NREL/TP-5500-46861, `docs.nrel.gov` mirror unreachable from this sandbox (DNS failure); retrieved via OSTI (`osti.gov/servlets/purl/1009264`, `doi:10.2172/1009264`) | Yes | all six | **not found** (one irrelevant coincidental hit) | Only hit on "25,000" is p.18: *"...with a mean of more than 25,000 ft2/person (2,323..."* — an **occupant-density** statistic, unrelated to floor-area tiering. No occurrence of 2322/9290/100,000 anywhere. The report gives each archetype's own fixed floor area (Small Office 5,500 ft², Medium Office 53,628 ft², Large Office 498,588 ft², Table 13 p.19) but draws **no boundary** between them. |
| 3 | PNNL prototype documentation | PNNL-23269 (2014), *Enhancements to ASHRAE Standard 90.1 Prototype Building Models*, `pnnl.gov/main/publications/external/technical_reports/PNNL-23269.pdf` (the URL `RESULT_I02` cites, `energycodes.gov/.../901_PrototypeBuildingModelEnhancements.pdf`, is dead — 404) | Yes | all six | **not found** | 0 hits. This report documents specific WWR/vestibule/lighting enhancements to existing prototypes; it does not tabulate office floor-area tiers at all. |
| 4 | ASHRAE 90.1 (and other standards that tier offices by area) | ANSI/ASHRAE/IES Standard 90.1 | **Could not retrieve.** ASHRAE 90.1 is a paywalled ANSI standard. No free full-text PDF mirror was found; `ashrae.org`'s "read-only" viewer requires an authenticated session my sandbox does not have (`ashrae.org/technical-resources/bookstore/standard-90-1-2019-i-p--edition` → 404 for a direct fetch; `ashrae.iccsafe.org` unreachable). Public excerpts found via search (Section 5 envelope-requirement training slides from state energy offices) do not contain an office size-tiering table. | — | **could not retrieve — per hard rule 10 this is reported as a retrieval failure, not as "not found."** | — |

---

## What this means for the thresholds

- The code's `_OFFICE_SMALL_MAX_M2 = 2322.0` / `_OFFICE_MEDIUM_MAX_M2 = 9290.0` **do** correspond
  exactly to a real, Crossref-verified, retrievable primary source: **Chen, Hong & Piette (2017),
  Applied Energy 205, 323–335**, Table 1, manuscript p.18. This is a genuine hit, independently
  found and independently verified (not asserted from `RESULT_I02` or the plan).
- It is **not** the paper `RESULT_I02` actually names (Hong et al. 2015). That paper does not
  contain these numbers anywhere in its full text.
- **Caveat, stated as the plan requires for a "numeric but not definitional" donor, extended to
  this hit too:** the Chen/Hong/Piette (2017) table is presented as the classification CityBES
  used **for one specific case study** (940 buildings in northeast San Francisco), with a footnote
  admitting an internal inconsistency (medium office also includes some <2,300 m² buildings with
  4–5 floors). It is not framed in that paper as a citation to an external standard, nor as a
  universally-asserted CityBES specification independent of that case study — it is CityBES's own
  applied rule, stated once, in a case-study table. Whether CityBES treats it as a fixed, versioned
  specification elsewhere (its live web app, `citybes.lbl.gov`) was not established — the site is a
  JS-rendered application behind Cloudflare and a static fetch returns only navigation chrome, not
  the classification logic; this was not pursued further given the time budget, and is flagged as
  **unresolved, not as a negative result**.
- CBECS's 25,000 / 100,000 ft² bin edges are real and independently confirmed, but per the plan's
  own caveat they bin **all** commercial buildings by size for sampling purposes and do not define
  office archetypes — a numeric coincidence, not a definitional source, and CBECS is not what
  either the code or `RESULT_I02` claims as the origin.
- No DOE/PNNL prototype document (Deru et al. 2011, PNNL-23269) draws a floor-area boundary between
  its office archetypes anywhere; they document each archetype's own fixed size, which is a
  different fact than a boundary rule.
- ASHRAE 90.1 remains unchecked because it could not be retrieved. This is an open gap, not a
  negative result, and should not be read as "ASHRAE 90.1 does not have this."

**Overall:** the code's numbers are traceable to a real, verifiable, non-`RESULT_I02` source, but
that source is a single applied case-study table, not a general definitional standard, and one
candidate (ASHRAE 90.1) was never actually checked because it could not be retrieved. Both facts
belong in the code comment (T06 Leg C) and in the erratum (T06 Leg A).

## Files

- Search script: `scripts/analysis/open47_threshold_search.py`
- Script output (all six documents, both control and target results):
  `...\scratchpad\open47\open47_threshold_search_output.txt`
- Downloaded documents (scratchpad only, never committed): `hong2015_apenergy159_cbes.pdf`,
  `chen2017_apenergy205_citybes_retrofit.pdf`, `chen2017_bs2017_071.pdf`, `eia_cbecs2018_flipbook.pdf`,
  `deru2011_osti3.pdf`, `pnnl23269.pdf`, plus their `pdftotext -layout` extractions and the Crossref
  JSON responses used to verify DOIs (see `FIX_open-47_citation-erratum.md` for the DOI verdicts).
