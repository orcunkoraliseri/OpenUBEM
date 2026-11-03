# Prompt 1 — Why an ASHRAE 90.1 prototype model over-predicts energy in Los Angeles' mild climate

**Run this in Google Antigravity (deep web research). Save the answer per the instruction at the bottom.**

**Why this prompt:** OpenUBEM simulates city building stock using DOE / ASHRAE 90.1-2013 prototype buildings in EnergyPlus 23.1. After the V19 re-score, our modeled site EUI for Los Angeles runs **+38.8% higher than measured benchmarking data (LA EBEWE ordinance)**, while the same approach matches New York City within ~10%. Critically, this LA over-prediction did **not** move when we fixed a multi-floor internal-load / zoning bug — so it is **not** a geometry artifact. It is a genuine climate / HVAC-response problem: our model does not run "cool enough" in a mild climate that should be the lowest-energy of our three cities. Before we calibrate, we need a citeable review of *where* ASHRAE 90.1-2013 prototype assumptions diverge from California reality (Title 24) and which parameters drive the over-prediction.

---

```
You are an expert building-energy modeler specializing in EnergyPlus and California climate/code.
I run an Urban Building Energy Model (UBEM) using DOE / ASHRAE 90.1-2013 prototype buildings
simulated in EnergyPlus 23.1 with climate-zone-appropriate weather. My modeled SITE EUI for the
Los Angeles building stock runs +38.8% HIGHER than measured data (LA EBEWE benchmarking ordinance).
The same modeling pipeline matches New York City within ~10%. This over-prediction in a MILD climate
did NOT change when I corrected a multi-floor zoning bug, so it is a climate / HVAC-response problem,
not a geometry problem.

Do deep web research across documentation, peer-reviewed papers, code/standards, and government reports.
Answer the following, with a citation for every claim:

1. SYSTEMATIC DIFFERENCES between ASHRAE 90.1-2013 prototype assumptions and California Title 24
   (2013 / 2016 / 2019 vintages) that would cause an ASHRAE-based model to OVER-predict energy in a
   mild California climate. Focus on, and quantify where possible:
   - Cooling equipment efficiency minimums (SEER/EER/IEER) — ASHRAE 90.1-2013 vs Title 24.
   - Economizer requirements and thresholds (airside economizers are highly effective in mild coastal CA).
   - Fan power limits / fan energy.
   - Envelope (wall/roof/window U, SHGC) for mild CA climate zones.
   - Lighting power density and mandatory daylighting/controls under Title 24.
   - Any climate-zone-specific provisions for CA coastal / mild zones (CEC CZ 6-9, IECC/ASHRAE 3B/3C/4C).

2. Whether ASHRAE 90.1 prototype HVAC SIZING and PART-LOAD behavior tends to over-predict cooling
   and fan energy in mild climates (few cooling-design hours, high economizer/free-cooling potential,
   oversized equipment cycling at low part-load).

3. Published LITERATURE on UBEM or prototype-model OVER-prediction in California vs measured benchmarking
   data (LA EBEWE, CEUS, California stock studies) — report the SIGN, MAGNITUDE, and stated ROOT CAUSES.

4. The 3-5 HIGHEST-LEVERAGE parameter changes (with typical numeric values) that practitioners use to
   bring an ASHRAE-90.1 prototype model into agreement with California measured EUI.

Output as clean markdown:
- A RANKED TABLE: parameter | ASHRAE 90.1-2013 value | likely-better CA / Title 24 value |
  expected EUI impact (direction + rough magnitude) | source citation.
- A short "MOST LIKELY ROOT CAUSE" verdict (2-3 sentences) for the +38.8% LA over-prediction.
- A full citation list (title, author/org, year, URL, access date) for every claim.
If any behavior is undocumented or uncertain, SAY SO EXPLICITLY rather than guessing. Flag low-confidence items.

WHEN FINISHED: save your full response as a markdown file named
`RESULT_1_LA_climate_overprediction.md` in the SAME FOLDER as this prompt document
(`docs/docs_ACTIVE/v19_validation/deepResearch`).
```

---

**After researching, save your full response as a markdown file named**
`RESULT_1_LA_climate_overprediction.md` **in this folder:**
`C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\v19_validation\deepResearch`
