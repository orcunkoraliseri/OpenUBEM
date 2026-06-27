# Prompt 1 — New York City measured EUI (Local Law 84 / 133 benchmarking disclosure)

**Run this in Google Antigravity (deep web research). Save the answer per the instruction at the bottom.**

**Why this prompt:** OpenUBEM models NYC commercial/multifamily buildings (ASHRAE climate zone 4A)
and reports annual SITE EUI in kWh/m²·yr. This prompt fetches the real MEASURED EUI distribution
from NYC's mandatory benchmarking disclosure so the model can be scored against ground truth.

---

```
You are an energy-data research assistant. I need real, MEASURED commercial-building energy-use
intensity (EUI) statistics for New York City, sourced from the city's mandatory benchmarking
disclosure program (Local Law 84 / Local Law 133, administered via the NYC Mayor's Office of
Climate & Environmental Justice and ENERGY STAR Portfolio Manager). This is to validate an urban
building energy model, so I need distributions, not anecdotes.

Do deep web research and return:

1. The most recent publicly available NYC LL84/LL133 benchmarking disclosure dataset: its year,
   official name, the exact download URL (NYC Open Data or city portal), the number of properties,
   and which columns report WEATHER-NORMALIZED SITE EUI and SOURCE EUI.

2. For NYC commercial/multifamily buildings, the measured SITE EUI distribution (median and p25/p75
   quartiles, plus mean if available) BROKEN OUT BY PRIMARY PROPERTY TYPE. I specifically need these
   types if present: Office, Retail Store, Restaurant, Multifamily Housing (mid- and high-rise),
   Hotel, Non-Refrigerated Warehouse, Hospital, Medical Office, K-12 School, Supermarket/Grocery.

3. Report every EUI value in BOTH the original unit (kBtu/ft²·yr) AND converted to kWh/m²·yr using
   1 kBtu/ft²·yr = 3.15459 kWh/m²·yr. Show both columns.

4. The overall NYC all-property-type median site EUI (one headline number) in both units.

5. Any published analyses or city reports that summarize these distributions by property type, with
   full citations (title, author/agency, year, URL, access date).

Output as clean markdown tables: one row per property type, columns = [Property type, N buildings,
Site EUI p25, p50, p75 (kBtu/ft²), Site EUI p25, p50, p75 (kWh/m²), Source/citation]. State sample
size for every row. If a property type is missing from the data, say so explicitly — do not invent.
Flag any value you are not confident about.
```

---

**After researching, save your full response as a markdown file named**
`RESULT_1_nyc_ll84_measured.md` **in this folder:**
`C:\Users\o_iseri\Desktop\OpenUBEM\docs\validations\external_literature`
