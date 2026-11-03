# Prompt 1 — Pin the canonical source for DOE prototype building schedules

**Run this in Google Antigravity (deep web research). Save the answer per the instruction at the bottom.**

**Why this prompt:** OpenUBEM's schedule library (`doe_schedules.json`) currently ships *synthetic* lighting/equipment day-profiles derived from occupancy by a linear transform — a placeholder for the deferred "real DOE digitization" (DESIGN OQ-2). Before transcribing real values we must pin, unambiguously, **where the authoritative schedule fractions live**: which repository / dataset / file, which exact schedule objects, which standard edition, and the license. This prompt locates and verifies the source so the four follow-up prompts (and the engineer who transcribes) all draw from one pinned, citeable origin. This prompt returns **no fraction values** — only the source map and access method.

---

```
You are a building-energy-modeling data librarian. I need to locate the AUTHORITATIVE, primary
source for the operating SCHEDULES (fractional day-profiles) used in the U.S. DOE Commercial
Prototype Building Models — the ones developed by Pacific Northwest National Laboratory (PNNL) for
the DOE Building Energy Codes Program (energycodes.gov), as implemented in NREL's
openstudio-standards. I will use these to replace placeholder schedules in an urban building energy
model, so I need the EXACT canonical files, not summaries.

Pin the standard edition to ANSI/ASHRAE/IES Standard 90.1-2013 prototypes (state if a different
edition is the only one available for any building type, and note it).

Do deep web research and return:

1. SOURCE OPTIONS, ranked by authority, for the per-building-type operating schedules:
   (a) The DOE Commercial Prototype Building EnergyPlus IDF files (the ones containing
       Schedule:Compact / Schedule:Day:Interval objects such as BLDG_LIGHT_SCH, BLDG_EQUIP_SCH,
       BLDG_OCC_SCH, BLDG_LIGHT_APARTMENT_SCH). Give the exact download location (energycodes.gov
       prototype page and/or the NREL GitHub repo that mirrors them), the directory/file-naming
       convention, and how a given building type + climate zone maps to a specific .idf file.
   (b) The NREL/openstudio-standards repository: the exact path(s) under the repo where schedule
       fraction values are stored as data (JSON/CSV) versus generated in Ruby code. If schedules are
       generated programmatically rather than stored as data, say so explicitly and identify the
       Ruby file(s) and the rule.
   (c) The PNNL prototype "scorecard" spreadsheets or technical reports (e.g. PNNL-23269,
       PNNL-20405) that tabulate hourly schedule fractions, with the exact document + table numbers.

2. For EACH of these 9 building prototypes, give the EXACT source file (URL or repo path) and the
   exact schedule OBJECT NAMES for occupancy, lighting, and electric/plug equipment:
   - MediumOffice (or LargeOffice)
   - RetailStandalone
   - PrimarySchool (and SecondarySchool if it differs)
   - SmallHotel (and LargeHotel if it differs)
   - MidriseApartment (the dwelling-unit/apartment zone schedule, NOT corridor/common-area)
   - Warehouse
   - FullServiceRestaurant (and QuickServiceRestaurant if it differs)
   - Hospital
   - Outpatient (Outpatient HealthCare)
   Also include SuperMarket if a distinct DOE prototype exists for it.

3. LICENSE / TERMS: under what license are the DOE prototype IDFs and the openstudio-standards data
   released (e.g. public domain / BSD-3 / other)? Quote the license name and link. State whether
   re-distributing the digitized fraction values in an open-source project is permitted.

4. A short REFRESH PROCEDURE: the minimal steps to re-pull these exact source files in the future
   (URLs, repo + commit/tag, or dataset version) so the digitization is reproducible.

5. A note on CLIMATE INVARIANCE: confirm whether the occupancy/lighting/equipment FRACTIONAL
   schedules are identical across climate zones for a given prototype (so any one climate variant's
   IDF gives the same internal-load profiles), or whether they vary by climate. Cite where this is
   stated.

Output as clean markdown: (1) a ranked source-options section with URLs; (2) a table with columns
[Prototype, Source file/URL, Occupancy object name, Lighting object name, Equipment object name];
(3) a license section with quoted terms; (4) a refresh-procedure list; (5) the climate-invariance
note. Give a full citation (title, agency/repo, edition/version, URL, access date) for every source.
If you cannot locate a primary source for any prototype, SAY SO EXPLICITLY for that prototype — do
not guess a file name or object name. Flag anything you are not fully confident about.
```

---

**After researching, save your full response as a markdown file named**
`RESULT_1_canonical_source_location.md` **in this folder:**
`C:\Users\o_iseri\Desktop\OpenUBEM\docs\implementation\scheduleDigitization\deepResearch`
</content>
</invoke>
