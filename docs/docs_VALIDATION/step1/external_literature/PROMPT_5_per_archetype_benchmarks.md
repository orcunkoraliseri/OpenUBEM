# Prompt 5 — Per-archetype benchmark EUI (ENERGY STAR / CBECS / DOE national reference values)

**Run this in Google Antigravity (deep web research). Save the answer per the instruction at the bottom.**

**Why this prompt:** OpenUBEM reports EUI per archetype. This prompt fetches authoritative national
reference site EUI by building type so each modeled archetype has its own sanity band, in addition
to the city-level disclosure comparisons (Prompts 1–3).

---

```
You are an energy-benchmarking research assistant. I need authoritative NATIONAL reference values
for annual SITE energy-use intensity (EUI) by US commercial/multifamily building type, to use as a
per-archetype sanity benchmark for an urban building energy model.

Do deep web research and return, for each of these building types, the reference median/typical SITE
EUI: Small Office, Medium Office, Large Office, Stand-alone Retail, Strip-mall Retail, Full-Service
Restaurant, Quick-Service/Fast-Food Restaurant, Mid-Rise Apartment, High-Rise Apartment, Small
Hotel, Large Hotel, Non-Refrigerated Warehouse, Hospital, Outpatient/Medical Office, Primary School,
Secondary School, Supermarket/Grocery.

Pull from the most authoritative sources, and label which source each number comes from:
- US EPA ENERGY STAR Portfolio Manager "US national median site EUI by property type" technical
  reference table.
- EIA CBECS 2018 (or latest) site EUI by Principal Building Activity (PBA).
- DOE / PNNL Commercial Prototype Building Models reported EUIs (by climate zone if available).

For each building type give: source name, the reported SITE EUI, the original unit, the value
converted to kWh/m²·yr (1 kBtu/ft²·yr = 3.15459 kWh/m²·yr), and the year/edition of the source.
Where a source gives climate-zone-specific values, include the rows for ASHRAE zones 2A (hot-humid),
3B (hot-dry), and 4A (mixed-humid) since those are the climates I care about.

State explicitly whether each value was read directly from the actual published source table or
estimated from secondary sources/knowledge; if estimated, label that row as ESTIMATED and give the
real source table/edition you could verify.

Output as a markdown table: columns = [Building type, Source, Climate zone (if any), Site EUI
(original unit), Site EUI (kWh/m²·yr), Source year, Citation URL]. If multiple sources disagree for
a type, show all of them as separate rows rather than averaging. Do not invent values; mark gaps
explicitly.
```

---

**After researching, save your full response as a markdown file named**
`RESULT_5_per_archetype_benchmarks.md` **in this folder:**
`C:\Users\o_iseri\Desktop\OpenUBEM\docs\validations\external_literature`
