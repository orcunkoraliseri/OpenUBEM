# Prompt 6 — Measured end-use breakdowns (to externally check the service-load reconstruction)

**Run this in Google Antigravity (deep web research). Save the answer per the instruction at the bottom.**

**Why this prompt:** OpenUBEM simulates only 4 end-uses (heating, cooling, lighting, equipment) and
reconstructs the missing 5 (fans, pumps, DHW, refrigeration, cooking) using published per-archetype
fraction splits (Table 4). This prompt fetches independent measured end-use breakdowns to check
those fractions — especially the large refrigeration/cooking shares for supermarkets and restaurants.

---

```
You are a building-energy research assistant. I have a model that simulates only four end-uses
(space heating, space cooling, lighting, and plug/equipment) and then reconstructs the missing
end-uses (ventilation fans, pumps, service hot water/DHW, refrigeration, and cooking) by applying
published per-building-type end-use FRACTION splits. I need independent, authoritative measured
end-use breakdowns to check those fractions.

Do deep web research and return, for US commercial/multifamily building types, the share (% of
total SITE energy) attributable to each end-use: heating, cooling, ventilation/fans, pumps, water
heating (DHW), interior lighting, plug/equipment ("other"), refrigeration, and cooking. Prioritize
these types: Large Office, Stand-alone Retail, Supermarket/Grocery, Full-Service Restaurant,
Quick-Service Restaurant, Mid-Rise Apartment, Hospital, Hotel, Warehouse.

Authoritative sources to mine, labeled per number:
- EIA CBECS 2018 end-use consumption tables (by Principal Building Activity).
- DOE / PNNL Commercial Prototype Building Model end-use breakdowns.
- Any peer-reviewed measured end-use disaggregation studies.

Pay special attention to refrigeration share for supermarkets and cooking + refrigeration + DHW
share for restaurants — I expect these to be very large (40–67% of total) and I need to confirm that
against measured data.

State explicitly whether each end-use split was read directly from the actual published source table
or estimated from secondary sources/knowledge; if estimated, label that row as ESTIMATED and give the
real source table/edition you could verify.

Output as a markdown table: one row per building type, columns = [Building type, Heat %, Cool %,
Fans %, Pumps %, DHW %, Lighting %, Equipment %, Refrigeration %, Cooking %, Source, Year]. Each row
should sum to ~100% — note if it doesn't. Give a citation URL per source. Do not invent values; mark
any end-use the source does not report.
```

---

**After researching, save your full response as a markdown file named**
`RESULT_6_measured_enduse_splits.md` **in this folder:**
`C:\Users\o_iseri\Desktop\OpenUBEM\docs\validations\external_literature`
