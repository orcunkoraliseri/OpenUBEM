# Prompt 5 — Verbatim DOE prototype schedules: Institutional & Health (School, Hospital, Outpatient)

**Run this in Google Antigravity (deep web research). Save the answer per the instruction at the bottom.**

**Why this prompt:** Completes the digitization. Schools are strongly seasonal/day-typed (closed evenings/weekends/summer-ish), hospitals run ~24/7 with a high overnight base, and outpatient clinics are daytime. Each has a distinct real DOE profile that the synthetic occupancy-linear transform approximates poorly. Use the source pinned in `RESULT_1_canonical_source_location.md` (DOE Commercial Prototype IDFs / openstudio-standards, ANSI/ASHRAE/IES 90.1-2013).

---

```
You are a building-energy-modeling data extraction assistant. From the U.S. DOE Commercial Prototype
Building Models (PNNL, DOE Building Energy Codes Program; as implemented in NREL openstudio-standards),
ANSI/ASHRAE/IES Standard 90.1-2013 edition, extract the VERBATIM fractional operating SCHEDULES for:

  A) PrimarySchool  (and SecondarySchool if its schedule shapes differ; state if identical)
  B) Hospital
  C) Outpatient (Outpatient HealthCare)

For EACH prototype and EACH of the three families — OCCUPANCY (fraction of peak people),
LIGHTING (fraction of peak lighting power), EQUIPMENT (fraction of peak plug/process power) —
return the full day-profiles for these three day-types:
  - Weekday
  - Saturday
  - Sunday (use this also for holidays / "AllOtherDays")

If a prototype uses different schedules per major zone (e.g. school classroom vs gym/kitchen;
hospital patient-room vs OR/lab), report the DOMINANT whole-building-representative profile for each
family and label which zone it represents. For schools, if the prototype encodes a reduced-occupancy
summer period, describe it but still return the standard Weekday/Saturday/Sunday day-profiles used
for the bulk of the year.

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
    (Sanity anchors: school lighting is LOW per year due to evenings/weekends/summer closure; hospital
    lighting+equipment are HIGH due to ~24/7 operation. Flag profiles outside the expected direction.)

Output as clean markdown: one subsection per prototype, three labeled tables
(Occupancy / Lighting / Equipment), columns [Day-type, Until HH:MM, Fraction], a footer per table
with source object name + file URL + annual EFLH, then a citation block (title, repo/agency, edition,
URL, access date).

CRITICAL: if a PRIMARY-SOURCE value cannot be found for any profile, write "PRIMARY SOURCE NOT FOUND"
and explain your search — do NOT infer or substitute a generic shape. Flag low-confidence values.
```

---

**After researching, save your full response as a markdown file named**
`RESULT_5_institutional_health_schedules.md` **in this folder:**
`C:\Users\o_iseri\Desktop\OpenUBEM\docs\implementation\scheduleDigitization\deepResearch`
</content>
</invoke>
