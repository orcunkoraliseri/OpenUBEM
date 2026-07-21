# Prompt 2 — Why DOE prototype office models over-predict measured office EUI across cities

**Run this in Google Antigravity (deep web research). Save the answer per the instruction at the bottom.**

**Why this prompt:** OpenUBEM models commercial offices using the DOE / ASHRAE 90.1-2013 prototype office buildings (Small / Medium / Large Office) in EnergyPlus 23.1, with operating schedules parsed from the DOE prototype IDFs. After the V19 re-score (which corrected a multi-floor zoning bug), our modeled office site EUI now runs **+30% to +50% higher than measured benchmarking data across multiple cities** (NYC LL84, LA EBEWE). This over-prediction is consistent and cross-city, so it is a systematic office-archetype problem, not noise. Notably, the old NYC office "perfect match" (−0.3%) was an accident of the zoning bug under-counting loads; fixing the bug revealed the true over-prediction, exactly as V18 predicted. Before calibrating, we need a citeable review of which office inputs are typically too high and by how much.

---

```
You are an expert building-energy modeler. I model commercial offices using the DOE / ASHRAE 90.1-2013
prototype office buildings (Small, Medium, Large Office) in EnergyPlus 23.1, with schedules parsed from
the DOE prototype IDFs. After fixing a multi-floor zoning bug, my modeled office SITE EUI now runs
+30% to +50% HIGHER than measured benchmarking data across MULTIPLE cities (NYC Local Law 84, LA EBEWE).
This is consistent, cross-city over-prediction — a systematic archetype problem.

Do deep web research across peer-reviewed papers, DOE/NREL/LBNL reports, and benchmarking datasets.
Answer the following, with a citation for every claim:

1. DOCUMENTED COMPARISONS of DOE prototype office models vs MEASURED office EUI (CBECS, NYC LL84,
   city benchmarking, CEUS). Report the typical SIGN and MAGNITUDE of the discrepancy and what drives it.

2. WHICH PROTOTYPE OFFICE INPUTS are most often too high relative to real stock, with typical
   prototype-vs-measured numbers where available:
   - Plug / equipment power density (W/ft2 or W/m2)
   - Lighting power density (and whether prototypes lag real LED retrofits)
   - Occupant density
   - HVAC operating schedules / equipment runtime / after-hours operation
   - Ventilation rates (cfm/person, cfm/ft2)
   - HVAC efficiency and sizing
   Distinguish by office SIZE (Small/Medium/Large) where the prototype values differ.

3. The role of REAL-WORLD PART-TIME OCCUPANCY, vacancy, and "soft" / reduced operation versus the
   prototype's near-full-schedule assumption, in driving over-prediction. (Note post-2020 occupancy
   shifts if relevant to recent benchmarking data.)

4. RECOMMENDED CALIBRATION ADJUSTMENTS (typical value ranges) used in the literature to reconcile
   prototype offices with measured EUI.

Output as clean markdown:
- A RANKED TABLE: input parameter | DOE prototype value (2013; by office size if it varies) |
  typical real / measured value | EUI impact (direction + magnitude) | source citation.
- A "SINGLE BIGGEST CONTRIBUTOR" verdict (2-3 sentences) for the +30-50% over-prediction.
- A full citation list (title, author/org, year, URL, access date) for every claim.
If any value is undocumented or uncertain, SAY SO EXPLICITLY rather than guessing. Flag low-confidence items.

WHEN FINISHED: save your full response as a markdown file named
`RESULT_2_office_overprediction.md` in the SAME FOLDER as this prompt document
(`docs/docs_ACTIVE/v19_validation/deepResearch`).
```

---

**After researching, save your full response as a markdown file named**
`RESULT_2_office_overprediction.md` **in this folder:**
`C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\v19_validation\deepResearch`
