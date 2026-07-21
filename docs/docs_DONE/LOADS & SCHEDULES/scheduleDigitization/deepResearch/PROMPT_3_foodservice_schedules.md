# Prompt 3 — Verbatim DOE prototype schedules: Food Service (Full-Service & Quick-Service Restaurant)

**Run this in Google Antigravity (deep web research). Save the answer per the instruction at the bottom.**

**Why this prompt:** External validation (V17) found OpenUBEM over-predicts restaurant energy by ~110–160%. Part of that is the reconstruction layer, but the simulated base also rides on the synthetic occupancy-derived lighting/equipment schedules. We need the REAL DOE FullServiceRestaurant and QuickServiceRestaurant schedules to replace the placeholder. Use the source pinned in `RESULT_1_canonical_source_location.md` (DOE Commercial Prototype IDFs / openstudio-standards, ANSI/ASHRAE/IES 90.1-2013). Note: in OpenUBEM, QuickServiceRestaurant currently borrows FullServiceRestaurant fractions — confirm whether the DOE prototypes actually differ so we can decide whether to split them.

---

```
You are a building-energy-modeling data extraction assistant. From the U.S. DOE Commercial Prototype
Building Models (PNNL, DOE Building Energy Codes Program; as implemented in NREL openstudio-standards),
ANSI/ASHRAE/IES Standard 90.1-2013 edition, extract the VERBATIM fractional operating SCHEDULES for:

  A) FullServiceRestaurant
  B) QuickServiceRestaurant

For EACH prototype and EACH of the three families — OCCUPANCY (fraction of peak people),
LIGHTING (fraction of peak lighting power), EQUIPMENT (fraction of peak electric plug/kitchen
equipment power) — return the full day-profiles for these three day-types:
  - Weekday
  - Saturday
  - Sunday (use this also for holidays / "AllOtherDays")

If the dining and kitchen zones use different schedules, report the DINING-area occupancy/lighting
and the dominant EQUIPMENT (kitchen) schedule, and clearly label which zone each came from. If gas
cooking is on a separate schedule from electric equipment, return the ELECTRIC equipment schedule
(OpenUBEM models electric plug/process loads) and note the gas one separately if available.

Report each profile as an ordered list of (Until HH:MM, fraction) breakpoints exactly as in the
EnergyPlus Schedule:Compact / Schedule:Day object — the hour each fractional value ends and the
fraction (0.0–1.0). Preserve exact values; do not round or smooth.

For EVERY profile you return, also give:
  - the exact SOURCE schedule OBJECT NAME,
  - the exact source FILE (IDF filename or openstudio-standards path) and its URL,
  - the ANNUAL EQUIVALENT FULL-LOAD HOURS (EFLH) self-check:
        daily_EFLH(day) = sum over segments of [fraction × segment_length_in_hours]
        annual_EFLH     = daily_EFLH(Weekday)×261 + daily_EFLH(Saturday)×52 + daily_EFLH(Sunday)×52
    Report annual_EFLH for the Lighting and Equipment profiles of each prototype.

Also answer explicitly: do FullServiceRestaurant and QuickServiceRestaurant use DIFFERENT schedule
shapes in the DOE prototypes, or the same? Quote the object names that show this.

Output as clean markdown: one subsection per prototype, three labeled tables
(Occupancy / Lighting / Equipment), columns [Day-type, Until HH:MM, Fraction], a footer per table
with source object name + file URL + annual EFLH, then a citation block (title, repo/agency, edition,
URL, access date), then the FSR-vs-QSR difference answer.

CRITICAL: if a PRIMARY-SOURCE value cannot be found for any profile, write "PRIMARY SOURCE NOT FOUND"
and explain your search — do NOT infer or substitute a generic shape. Flag low-confidence values.
```

---

**After researching, save your full response as a markdown file named**
`RESULT_3_foodservice_schedules.md` **in this folder:**
`C:\Users\o_iseri\Desktop\OpenUBEM\docs\implementation\scheduleDigitization\deepResearch`
</content>
</invoke>
