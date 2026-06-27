# Prompt 3 — Austin / Texas measured EUI (ECAD benchmarking)

**Run this in Google Antigravity (deep web research). Save the answer per the instruction at the bottom.**

**Why this prompt:** OpenUBEM models Austin commercial/multifamily buildings (ASHRAE climate zone 2A,
hot-humid) and reports annual SITE EUI in kWh/m²·yr. This prompt fetches the real MEASURED EUI
distribution from Austin/Texas benchmarking disclosure so the model can be scored against ground
truth. Austin disclosure data is thinner than NYC/LA — the prompt allows clearly-labeled Texas /
ERCOT substitutes.

---

```
You are an energy-data research assistant. I need real, MEASURED commercial-building energy-use
intensity (EUI) statistics for Austin, Texas, sourced from the Austin Energy Conservation Audit &
Disclosure (ECAD) ordinance and any associated City of Austin / Austin Energy benchmarking
disclosure datasets. If Austin-specific commercial EUI distributions are thin, supplement with the
best available Texas or ERCOT-region commercial benchmarking data and clearly label the geography.
This is to validate an urban building energy model.

Do deep web research and return:

1. The most recent publicly available Austin ECAD (and/or Texas) commercial benchmarking dataset:
   year, official name, exact download URL, number of properties, and which columns report SITE vs
   SOURCE EUI and whether weather-normalized.

2. The measured SITE EUI distribution (median, p25/p75, mean if available) BROKEN OUT BY PRIMARY
   PROPERTY TYPE for: Office, Retail Store, Restaurant, Multifamily Housing, Hotel, Warehouse,
   Hospital, Medical Office, K-12 School, Supermarket/Grocery.

3. Every EUI value in BOTH kBtu/ft²·yr AND kWh/m²·yr (1 kBtu/ft²·yr = 3.15459 kWh/m²·yr).

4. Note Austin is ASHRAE climate zone 2A (hot-humid). Label whether each number is Austin-specific,
   Texas statewide, or ERCOT-region.

5. Full citations (title, agency, year, URL, access date) and sample size per row.

6. State explicitly whether you computed these statistics from the actual downloaded dataset or
   estimated them from secondary sources/knowledge; if estimated, label the table as ESTIMATED and
   give the real dataset row counts you could verify.

Output as clean markdown tables: one row per property type, columns = [Property type, Geography,
N buildings, Site EUI p25/p50/p75 (kBtu/ft²), Site EUI p25/p50/p75 (kWh/m²), Source]. State sample
size per row. If Austin-specific data does not exist for a type, say so and clearly mark any
Texas/ERCOT substitute. Do not invent values. Flag low-confidence numbers.
```

---

**After researching, save your full response as a markdown file named**
`RESULT_3_austin_texas_measured.md` **in this folder:**
`C:\Users\o_iseri\Desktop\OpenUBEM\docs\validations\external_literature`
