# Prompt 4 — Verbatim DOE prototype schedules: Commercial day-operation (Office, Retail, Warehouse, Supermarket)

**Run this in Google Antigravity (deep web research). Save the answer per the instruction at the bottom.**

**Why this prompt:** These are the day-operation commercial types. Their synthetic schedules in OpenUBEM are closer to reality than the residential ones (because their occupancy zeroes out overnight), but for a faithful, citeable digitization we still replace them with the real DOE prototype values. SuperMarket is included because OpenUBEM currently lumps it into the "Retail" schedule group, yet supermarkets run longer hours with refrigeration — this lets us check whether it deserves its own profile. Use the source pinned in `RESULT_1_canonical_source_location.md` (DOE Commercial Prototype IDFs / openstudio-standards, ANSI/ASHRAE/IES 90.1-2013).

---

```
You are a building-energy-modeling data extraction assistant. From the U.S. DOE Commercial Prototype
Building Models (PNNL, DOE Building Energy Codes Program; as implemented in NREL openstudio-standards),
ANSI/ASHRAE/IES Standard 90.1-2013 edition, extract the VERBATIM fractional operating SCHEDULES for:

  A) MediumOffice  (note if LargeOffice / SmallOffice use the SAME schedule shapes; if identical, say so)
  B) RetailStandalone  (and RetailStripmall if it differs)
  C) Warehouse  (the conditioned/office portion's lighting+occupancy and the bulk-storage equipment;
     label which zone each profile is for)
  D) SuperMarket  (if a distinct DOE prototype exists; include its refrigeration-relevant operating
     hours if the lighting/equipment schedules reflect extended hours)

For EACH prototype and EACH of the three families — OCCUPANCY (fraction of peak people),
LIGHTING (fraction of peak lighting power), EQUIPMENT (fraction of peak plug/process power) —
return the full day-profiles for these three day-types:
  - Weekday
  - Saturday
  - Sunday (use this also for holidays / "AllOtherDays")

Report each profile as an ordered list of (Until HH:MM, fraction) breakpoints exactly as in the
EnergyPlus Schedule:Compact / Schedule:Day object — the hour each fractional value ends and the
fraction (0.0–1.0). Preserve exact values; do not round or smooth.

For EVERY profile, also give:
  - the exact SOURCE schedule OBJECT NAME,
  - the exact source FILE (IDF filename or openstudio-standards path) and its URL,
  - the ANNUAL EQUIVALENT FULL-LOAD HOURS (EFLH) self-check:
        daily_EFLH(day) = sum over segments of [fraction × segment_length_in_hours]
        annual_EFLH     = daily_EFLH(Weekday)×261 + daily_EFLH(Saturday)×52 + daily_EFLH(Sunday)×52
    Report annual_EFLH for the Lighting and Equipment profiles of each prototype.
    (Sanity anchors: DOE office lighting ≈ 2,800–3,200 EFLH; standalone retail ≈ 3,500–4,500 EFLH;
    supermarkets run noticeably higher. Flag profiles that fall far outside their expected band.)

Also answer explicitly: does SuperMarket use materially LONGER operating hours / higher EFLH than
RetailStandalone in the DOE prototypes? Quote the values that show it.

Output as clean markdown: one subsection per prototype, three labeled tables
(Occupancy / Lighting / Equipment), columns [Day-type, Until HH:MM, Fraction], a footer per table
with source object name + file URL + annual EFLH, then a citation block (title, repo/agency, edition,
URL, access date), then the SuperMarket-vs-Retail answer.

CRITICAL: if a PRIMARY-SOURCE value cannot be found for any profile, write "PRIMARY SOURCE NOT FOUND"
and explain your search — do NOT infer or substitute a generic shape. Flag low-confidence values.
```

---

**After researching, save your full response as a markdown file named**
`RESULT_4_commercial_schedules.md` **in this folder:**
`C:\Users\o_iseri\Desktop\OpenUBEM\docs\implementation\scheduleDigitization\deepResearch`
</content>
</invoke>
