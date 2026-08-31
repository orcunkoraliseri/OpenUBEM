# DECISION REQUEST D-EU-34 — Bologna at zero simulations is not acceptable; retry the one open lead, then relax the observed-year rule

- **Date:** 2026-08-28
- **Arc:** European locations x Step 8
- **Record:** `docs/docs_ACTIVE/europeanLocations/debugs/EU11_Bologna_construction_year_investigation.md`
  (authoritative investigation doc, closed **Fail** 2026-08-28)
- **Blocks:** `IT-BOL-GALVANI2` — 1,220 residential buildings selected, prepared, and simulated at **0**
- **Follows:** the investigation's own "Fail" disposition, which is not overturned here — its terms are
  extended, per owner instruction
- **Ruled:** 2026-08-28, by owner instruction — a selected, prepared neighbourhood that simulates zero
  buildings is not an acceptable end state; either find a new source or relax the rule

---

## 1. The one-sentence version

The investigation swept every reachable open Bologna/Emilia-Romagna/national source by field name (not
title) and found no per-building construction year anywhere, correctly closing **Fail** under the
project's observed-data-only purity rule — but the owner has now ruled that "selected to simulate, ends at
zero" is worse than using a disclosed, tagged, non-observed source.

## 2. What the investigation already proved (not re-litigated)

- **702/702** Comune di Bologna datasets swept by field name; 137 have a date-like field, all
  administrative/fiscal, none a construction year.
- **10** permit datasets: procedure dates only, no completion date bound to a building.
- Emilia-Romagna CKAN (2,904 packages), Geoportale ER: no per-building year.
- **One lead not closed by measurement**: the Italian INSPIRE Buildings WFS — all four `GetCapabilities`
  attempts failed on transport grounds (DNS failure ×2, HTTP 404 SPA, HTTP 500 SOAP fault), not on a
  confirmed absence of the field. This is the only candidate left under the investigation's own five
  acceptance criteria.
- ISTAT 2011 census-section construction-period bands **exist**, but are section-scale, not a building
  attribute — this is exactly what the acceptance criteria (criterion 1: identifies one physical building)
  were written to exclude, and the investigation correctly refused to use them as an *observed* value.

## 3. Ruling

1. **Retry the INSPIRE Buildings WFS lead once, live, before anything else.** If a working endpoint is
   found and it satisfies all five acceptance criteria in the investigation doc, use it — this is a genuine
   "find another location" outcome and no rule needs relaxing.
2. **If INSPIRE remains unreachable or fails the acceptance test, relax the observed-year rule for Bologna
   only**, using the ISTAT 2011 census-section construction-period band as a **stated, tagged imputation**,
   not a claimed observation:
   - Every Bologna building's TABULA period comes from the ISTAT band of the census section its footprint
     centroid falls in — a documented, reproducible spatial join, not a random draw or neighbourhood
     average.
   - Tag every such building `IMPUTED_CENSUS_SECTION_CONSTRUCTION_PERIOD` in the manifest and the side-car —
     **never** `OBSERVED_YEAR`, and never comparable cell-for-cell against Madrid/Lyon/London's observed-year
     runs without that distinction stated in the same sentence.
   - Report coverage and exclusion counts (buildings whose centroid falls in an unmapped or ambiguous
     section) before any IDF is generated, per the investigation's own acceptance criterion 5.
   - The height question is unaffected and already solved (`c_a944ctc_edifici_pl.altezza_gr`, CC BY 4.0) —
     do not conflate the two.
3. **The investigation doc's "Fail" disposition is not deleted or rewritten** — it stands as the record of
   what pure observed-data sourcing found. This ruling is recorded as a **new, separate decision** layered on
   top of it, not a correction of it.

## 4. What must never happen

- No per-building year invented from height, storeys, typology, or a neighbouring building.
- No EPC/permit/renovation date reused as a construction year (criterion 2 of the investigation, unchanged).
- No silent merge of Bologna's imputed-period EUI figures into the same pooled/compared number as the three
  observed-year districts without the imputation flagged at the point of citation.

## 5. Next free identifier

`D-EU-33` and `D-EU-34` both consumed today. Next free identifier `D-EU-35`.
