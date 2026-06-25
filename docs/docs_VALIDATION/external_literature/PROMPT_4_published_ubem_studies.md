# Prompt 4 — Published UBEM validation studies: reported accuracy & reference datasets

**Run this in Google Antigravity (deep web research). Save the answer per the instruction at the bottom.**

**Why this prompt:** This is the interpretive frame. OpenUBEM's per-building round-trip deviation is
~45% while its aggregate numbers are tight. This prompt gathers what comparable published UBEMs
reported, so that result can be positioned against the field rather than read as a defect.

---

```
You are a building-energy research librarian. I am validating an open-source archetype-based Urban
Building Energy Model (UBEM) that simulates thousands of commercial/multifamily buildings with
EnergyPlus and reports annual site EUI. I need to know how comparable published UBEM studies
validated their results and what accuracy they reported, so I can position my own numbers.

Do deep web research and return a structured evidence table covering peer-reviewed UBEM studies and
established UBEM platforms — prioritize those that modeled US cities (New York, Los Angeles, Austin,
Boston, Chicago, San Francisco, Seattle, etc.) or are widely cited. Cover at least: City Energy
Analyst (CEA), CityBES (LBNL), UMI (MIT), TEASER/AixLib, URBANopt (NREL), and any NYC-, LA-, or
Texas-specific UBEM papers.

For each study/platform, report:
1. Study/platform name, authors, year, venue, DOI or URL.
2. City/region and number of buildings modeled.
3. What MEASURED reference data they validated against (utility bills, AMI smart-meter data,
   benchmarking disclosure, monthly bills, etc.).
4. The accuracy metric(s) reported and the value: e.g. aggregate annual % error, CV(RMSE), NMBE,
   MAPE, R² — at BOTH the individual-building level and the aggregate/district level if given.
5. Any explicit statement about the expected RANGE of per-building error for archetype UBEMs vs the
   aggregate error (this distinction is central to my validation argument).

Then give a 1-paragraph synthesis: what is the consensus expected accuracy for (a) individual
buildings and (b) aggregate stock in archetype UBEM, with citations. Output as a markdown table plus
the synthesis paragraph. Every row must have a citation with a URL/DOI. Distinguish clearly between
peer-reviewed measured-data validation and model-to-model or self-consistency checks.

State explicitly whether each accuracy figure was quoted directly from the named publication or
estimated/inferred from secondary sources or general knowledge; if estimated, label that row as
ESTIMATED rather than presenting it as a verbatim reported value.
```

---

**After researching, save your full response as a markdown file named**
`RESULT_4_published_ubem_studies.md` **in this folder:**
`C:\Users\o_iseri\Desktop\OpenUBEM\docs\validations\external_literature`
