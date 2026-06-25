# Prompt 3 — Apples-to-apples: how to fairly compare simulated EUI against NYC / LA / Austin benchmarking data

**Run this in Google Antigravity (deep web research). Save the answer per the instruction at the bottom.**

**Why this prompt:** OpenUBEM validates by comparing its **simulated site EUI** against three cities' measured benchmarking datasets — **NYC Local Law 84, Los Angeles EBEWE, and Austin ECAD**. The V19 cross-city findings (LA +38.8%, offices +30-50%) only hold if the *measured* baselines are truly comparable to what we simulate. Before we calibrate the model to chase these targets, we must confirm we are not comparing site-EUI to source-EUI, weather-normalized to raw, or conditioned-area to gross-area. This prompt establishes exactly what corrections each city's data needs.

---

```
You are an expert in building energy benchmarking and disclosure ordinances. I compare a SIMULATED
SITE EUI (from EnergyPlus models) against measured benchmarking EUI from three city ordinances:
- New York City Local Law 84 (LL84)
- Los Angeles Existing Buildings Energy & Water Efficiency (EBEWE)
- Austin Energy Conservation Audit & Disclosure (ECAD)

Do deep web research across the ordinances' official documentation, ENERGY STAR Portfolio Manager
methodology, and peer-reviewed analyses. For EACH of the three datasets, determine and cite:

1. Whether the reported EUI is SITE EUI or SOURCE EUI (and the source-energy conversion factors used).
2. Whether the reported EUI is WEATHER-NORMALIZED or raw/actual, and the normalization method.
3. The FLOOR-AREA basis: gross floor area vs conditioned/heated floor area, and any exclusions
   (parking, etc.).
4. Property-type COVERAGE and any gaps or filing thresholds (e.g. minimum building size) that bias
   the dataset.
5. Reporting YEAR / vintage and any known data-quality caveats (self-reported errors, outliers).

Then give a SYNTHESIS:
- A COMPARISON TABLE: dataset | site vs source EUI | weather-normalized? | floor-area basis |
  coverage/threshold | year | source.
- A concrete CHECKLIST of corrections I must apply to my SIMULATED SITE EUI (or to the measured data)
  before benchmarking against each city, so the comparison is apples-to-apples.

Output as clean markdown with a full citation (title, author/org, year, URL, access date) for every claim.
If anything is ambiguous or undocumented, SAY SO EXPLICITLY rather than guessing. Flag low-confidence items.

WHEN FINISHED: save your full response as a markdown file named
`RESULT_3_benchmarking_normalization.md` in the SAME FOLDER as this prompt document
(`docs/docs_ACTIVE/v19_validation/deepResearch`).
```

---

**After researching, save your full response as a markdown file named**
`RESULT_3_benchmarking_normalization.md` **in this folder:**
`C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\v19_validation\deepResearch`
