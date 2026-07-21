# Prompt 2 — Verbatim DOE prototype schedules: Residential & Lodging (Apartment, Hotel)

**Run this in Google Antigravity (deep web research). Save the answer per the instruction at the bottom.**

**Why this prompt:** This is the highest-priority cluster. OpenUBEM currently forces apartment lighting to ~0.37–0.91 of peak *all day* (because its synthetic schedule tracks occupancy, which never drops below 0.3 for homes), giving ~5,831 equivalent full-load hours/yr and an inflated 43.9 kWh/m² lighting EUI — the root cause of the multifamily over-prediction. We need the REAL DOE MidriseApartment dwelling-unit schedules and the Hotel schedules to replace it. Use the source pinned in `RESULT_1_canonical_source_location.md` (DOE Commercial Prototype IDFs / openstudio-standards, ANSI/ASHRAE/IES 90.1-2013).

---

```
You are a building-energy-modeling data extraction assistant. From the U.S. DOE Commercial Prototype
Building Models (PNNL, for the DOE Building Energy Codes Program; as implemented in NREL
openstudio-standards), ANSI/ASHRAE/IES Standard 90.1-2013 edition, extract the VERBATIM fractional
operating SCHEDULES for the following building prototypes:

  A) MidriseApartment — the DWELLING-UNIT / apartment-zone schedules (e.g. BLDG_LIGHT_APARTMENT_SCH,
     and the matching apartment occupancy and plug-equipment schedules). Do NOT use corridor,
     common-area, or whole-building average schedules — I need the apartment living-space profile.
     If HighriseApartment differs from MidriseApartment, give both.
  B) SmallHotel — guest-room schedules for occupancy, lighting, and plug equipment. If LargeHotel
     differs materially, give both and note which zones (guest room vs lobby/common) each applies to;
     prioritize the guest-room/dominant profile.

For EACH prototype and EACH of the three families — OCCUPANCY (fraction of peak people),
LIGHTING (fraction of peak lighting power), EQUIPMENT (fraction of peak plug/process power) —
return the full day-profiles for these three day-types:
  - Weekday
  - Saturday
  - Sunday (use this also for holidays / "AllOtherDays")

Report each profile as an ordered list of (Until HH:MM, fraction) breakpoints exactly as in the
EnergyPlus Schedule:Compact / Schedule:Day object — i.e. the hour at which each fractional value
ends, and the fraction (0.0–1.0). Preserve the exact values; do not round, smooth, or "clean up."

For EVERY profile you return, also give:
  - the exact SOURCE schedule OBJECT NAME it came from,
  - the exact source FILE (IDF filename or openstudio-standards path) and its URL,
  - an ANNUAL EQUIVALENT FULL-LOAD HOURS (EFLH) self-check computed as:
        daily_EFLH(day) = sum over segments of [fraction × segment_length_in_hours]
        annual_EFLH     = daily_EFLH(Weekday)×261 + daily_EFLH(Saturday)×52 + daily_EFLH(Sunday)×52
    Report annual_EFLH for the Lighting and Equipment profiles of each prototype. (Sanity anchor:
    real residential lighting is typically ~1,500–2,500 EFLH/yr; flag if yours falls outside that.)

Output as clean markdown: one subsection per prototype, with three labeled tables
(Occupancy / Lighting / Equipment), each table having columns
[Day-type, Until HH:MM, Fraction] and a footer line giving the source object name, source file+URL,
and the annual EFLH. End with a citation block (title, repo/agency, edition, URL, access date).

CRITICAL: if you cannot find the PRIMARY-SOURCE value for any profile, write "PRIMARY SOURCE NOT
FOUND" for that profile and explain what you searched — do NOT infer, interpolate, or substitute a
generic shape. Flag any value you are less than fully confident transcribing.
```

---

**After researching, save your full response as a markdown file named**
`RESULT_2_residential_lodging_schedules.md` **in this folder:**
`C:\Users\o_iseri\Desktop\OpenUBEM\docs\implementation\scheduleDigitization\deepResearch`
</content>
</invoke>
