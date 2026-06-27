# Prompt 2 — Los Angeles / California measured EUI (EBEWE & AB 802 benchmarking)

**Run this in Google Antigravity (deep web research). Save the answer per the instruction at the bottom.**

**Why this prompt:** OpenUBEM models LA commercial/multifamily buildings (ASHRAE climate zone 3B,
hot-dry / Mediterranean) and reports annual SITE EUI in kWh/m²·yr. This prompt fetches the real
MEASURED EUI distribution from LA/California benchmarking disclosure so the model can be scored
against ground truth.

---

```
You are an energy-data research assistant. I need real, MEASURED commercial-building energy-use
intensity (EUI) statistics for Los Angeles and/or California, sourced from mandatory benchmarking
disclosure programs — specifically the Los Angeles Existing Buildings Energy & Water Efficiency
(EBEWE) ordinance and the California statewide AB 802 building energy benchmarking program (CEC).
This is to validate an urban building energy model, so I need distributions, not anecdotes.

Do deep web research and return:

1. The most recent publicly available LA EBEWE and/or California AB 802 benchmarking dataset: year,
   official name, exact download URL (LA Open Data / CEC portal), number of properties, and which
   columns report SITE EUI vs SOURCE EUI and whether they are weather-normalized.

2. The measured SITE EUI distribution (median and p25/p75 quartiles, mean if available) BROKEN OUT
   BY PRIMARY PROPERTY TYPE for: Office, Retail Store, Restaurant, Multifamily Housing, Hotel,
   Warehouse, Hospital, Medical Office, K-12 School, Supermarket/Grocery.

3. Every EUI value in BOTH kBtu/ft²·yr AND kWh/m²·yr (1 kBtu/ft²·yr = 3.15459 kWh/m²·yr). Show both.

4. Note that Los Angeles is ASHRAE climate zone 3B (hot-dry / Mediterranean) — if the source data
   lets you filter to LA County or the LA metro specifically rather than all of California, prefer
   that and say which geography each number represents.

5. Full citations for every source (title, agency, year, URL, access date) and sample size per row.

6. State explicitly whether you computed these statistics from the actual downloaded dataset or
   estimated them from secondary sources/knowledge; if estimated, label the table as ESTIMATED and
   give the real dataset row counts you could verify.

Output as clean markdown tables: one row per property type, columns = [Property type, Geography
(LA vs CA statewide), N buildings, Site EUI p25/p50/p75 (kBtu/ft²), Site EUI p25/p50/p75 (kWh/m²),
Source]. State sample size for every row. If a property type or geography is missing, say so — do
not invent. Flag low-confidence values.
```

---

**After researching, save your full response as a markdown file named**
`RESULT_2_la_california_measured.md` **in this folder:**
`C:\Users\o_iseri\Desktop\OpenUBEM\docs\validations\external_literature`
