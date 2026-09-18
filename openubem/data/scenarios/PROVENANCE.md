# PROVENANCE — openubem/data/scenarios/measures.json

Both measures shipped in J02. Every number below was re-derived from the cited public source, not
copied from any host-project number.

**Status update (J02b, 2026-09-17).** `envelope_u_upgrade` is withdrawn (see its own section
below). `lighting_power_density` stays active but is now scoped to `in_scope_archetypes`, since
its cited figure is an Office-occupancy number (see that section for the derivation of the list).

**Status update (J03b, 2026-09-17).** `thermostat_setback` is withdrawn (see its own section
below): the occupancy heuristic it shipped with drove the real-prototype occupied heating setpoint
from 21.0 C to 10.0444 C and the occupied cooling setpoint from 24.0 C to 29.4778 C for every hour
of every day, switching the HVAC off rather than applying a setback. The occupancy heuristic was
rewritten to derive occupied/setback values from each schedule's own workday entries instead of an
assumed business-hours window; the citation and targets below are unchanged.

## lighting_power_density

**What it changes.** `Watts_per_Zone_Floor_Area` on `LIGHTS` objects whose
`Design_Level_Calculation_Method == "Watts/Area"`, lowered to a single flat target. Never raised.

**Target:** 6.0 W/m2 (0.56 W/ft2).

**Public source.** ASHRAE 90.1-2022 Section 9.3.2, "Simplified Building Method" — the code's own
single-number, whole-building interior lighting power allowance for the Office occupancy
(distinct from, and lower-controls-burden than, the per-space-type Space-by-Space Method of
Section 9.5.2, and distinct from the per-building-type Building Area Method of Section 9.5.1).
The number is reproduced verbatim, with a visible slide citation, in the DOE Building Energy
Codes Program's official ASHRAE-committee-presented webinar "What You Need to Know About the New
Energy Standard for Commercial Buildings: ASHRAE Standard 90.1-2022" (Building Technologies
Office, Nov 16, 2023), slide 34: "Interior office LPD: 0.56 W/ft2 (6.0 W/m2)." That slide is
presented by Michael Myer (PNNL), the consultant to the ASHRAE SSPC 90.1 Lighting Subcommittee,
under the agenda item "Power, Lighting, & Renewables (Sections 8, 9, & 10)." PDF:
`https://www.energycodes.gov/sites/default/files/2023-11/ASHRAE90-1_2022_20231116_webinar.pdf`.

**Why this is not literally Section 9.5.1 (Building Area Method), as the block-5 ruling text
names.** The Building Area Method table (Table 9.5.1-1 in the 90.1-2022 base publication) was
searched extensively: ASHRAE's own PDF bookstore documents (base standard, Addendum b, Addendum s
to 90.1-2022) are copyright-locked and could not be read in full; DOE/PNNL secondary sources
(energycodes.gov webinar slides, the PNNL "90.1-2019: Power and Lighting" training deck) either
reproduce the *Simplified Method* or the *Space-by-Space Method* tables, never the Building Area
Method table for 90.1-2022 specifically. Two web-search snippets claimed an Office Building Area
Method value of "1.0 W/ft2" for 90.1-2022, but this could not be traced to any primary or
reproduced-table source, and it contradicts the verified trend (90.1-2016 Office BAM = 0.79 W/ft2,
90.1-2019 Office BAM = 0.64 W/ft2, both confirmed via the PNNL "90.1-2019: Power and Lighting"
training deck, slide 8, Addendum CG) — a rise to 1.0 would reverse the documented
tightening trend with no addendum cited to explain it. Rather than invent or trust an unverified
number, the Section 9.3.2 Simplified Method value is used instead: it is (a) drawn from the same
90.1-2022 edition, (b) a single flat number for Office (matching the measure's flat-target
design, mirroring the Building Area Method's own single-number-per-building-type shape), and
(c) confirmed from a primary-adjacent, ASHRAE-committee-authored source with a page/slide
citation. This substitution is flagged in the block-5 plan progress log as a deviation for the
manager to confirm or correct.

**Re-derivation.** The number is used exactly as published (0.56 W/ft2); the SI figure 6.0 W/m2 is
DOE's own published conversion on the same slide, not independently re-derived (0.56 x 10.7639 =
6.028, DOE rounds to 6.0).

**in_scope_archetypes (added J02b).** The cited target is the Simplified Building Method's Office
figure, not a fleet-wide number. The J01 census found it applied unscoped to every archetype,
including an operating room at 23.62 W/m2 (`ASHRAE901_Hospital_STD2022_Buffalo.idf`) — an office
number would book a fake saving there. The measure is scoped to the archetype ids in
`openubem/data/construction/ashrae_90_1_2019.json` (read as that file's top-level keys, 29 total)
that are genuinely offices: `SmallOffice`, `MediumOffice`, `LargeOffice`, `SmallOfficeDetailed`,
`MediumOfficeDetailed`, `LargeOfficeDetailed`. Every other archetype id in that file (Hospital,
Outpatient, retail, school, hotel, apartment, warehouse, restaurant, data-center, etc.), and any
archetype that is `None` or not present in the file, is out of scope and is skipped via
`gate_archetype_out_of_scope`, never applied.

## envelope_u_upgrade

**WITHDRAWN (J02b, 2026-09-17).** The targets below are byte-identical to the MediumOffice/6A row
of `openubem/data/construction/ashrae_90_1_2019.json`, which is the code baseline OpenUBEM already
applies via `openubem/semantic/construction_sets.py:172-194`. The measure was therefore a
guaranteed no-op on its own archetype (MediumOffice/6A: current already equals target) and, on the
few archetypes whose baseline wall U-value happens to be worse than the office wall, a leak of
one archetype's code baseline onto another rather than a retrofit. `apply_measure` now refuses to
run it: it reports `status: "withdrawn"` with this reason and changes nothing. The applier code,
its gate, and its delegation to `patch_envelope()` remain in the module for reuse, unused by the
public entry point, should a verified better-than-baseline target become available (see the
block-5 plan's "What would un-withdraw it" note). The record below is left as-is for provenance of
the withdrawn parameters; it does not describe active behaviour.

**What it changes.** Delegates to `openubem.geometry.envelope_patcher.patch_envelope()` with an
upgraded parameter row: wall/roof/floor U-value, window U-value, window SHGC. Direction rule
(never raise) is enforced by this module before delegating (see `measures.py` docstring), not by
inventing a new gate.

**Targets (W/m2K unless noted):** wall 0.278, roof 0.182, floor 0.29, window 1.931, SHGC 0.38.

**Public source.** ASHRAE 90.1-2019, climate zone 6A, archetype `MediumOffice` — the envelope
assembly U-factors already ingested, vetted, and cited at
`openubem/data/construction/ashrae_90_1_2019.json` (row `["MediumOffice"]["6A"]`), whose own
`PROVENANCE.md` traces every value to NREL/openstudio-standards commit `83b1e64c6f130f02b48c8b3ad4eeb3eb4da41663`
(`ashrae_90_1_2019.construction_properties.json` / `ashrae_90_1_2019.construction_sets.json`,
retrieved 2026-06-10, Apache 2.0). Values are stored in that file already converted to W/m2K
(confirmed: the CZ1 window row equals 2.839 W/m2K, exactly `0.5 Btu/h.ft2.F x 5.678263`, per that
file's own `PROVENANCE.md` worked example) — no further unit conversion was applied here.

Raw values read from `openubem/data/construction/ashrae_90_1_2019.json["MediumOffice"]["6A"]`:
`{"roof": {"u_value": 0.182, "assembly": "IEAD"}, "wall": {"u_value": 0.278, "assembly":
"SteelFramed"}, "window": {"u_value": 1.931, "shgc": 0.38}, "floor": {"u_value": 0.29}}`.

**Why 90.1-2019 stands in for the ruling's named ASHRAE 90.1-2022 Appendix A.** The exact
90.1-2022 Appendix A CZ6 opaque/window U-factor digits could not be verified from any accessible
primary source in the time available (the base standard and its lighting addenda were the only
90.1-2022 documents whose full text could be read; envelope Appendix A was not reproduced in any
accessible secondary source found). The DOE/ASHRAE-committee "What You Need to Know About ...
90.1-2022" webinar (Nov 16, 2023), slide 20, "Section 5 - Building Envelope, Updated
Requirements," lists only: Air Leakage, Roof replacements, Envelope commissioning, Insulated
metal panels, Compliance calculations to steel-framed walls; "New Concepts": Wall solar
reflectance, Thermal bridging, Envelope backstop. Opaque/window prescriptive U-factor table
revisions are not listed among either category, which is evidence (not proof) that Table
5.5-x / Appendix A U-factor values were not changed between 90.1-2019 and 90.1-2022. Given that,
the already-vetted, in-repo 90.1-2019 CZ6A MediumOffice row is used as the best-verified proxy.
This substitution is flagged in the block-5 plan progress log as a deviation for the manager to
confirm or correct, or to supply a directly-read 90.1-2022 Appendix A table if one becomes
available.

**Re-derivation.** No unit conversion needed (values already SI in the source file). No
archetype/CZ selection ambiguity: `MediumOffice` was chosen because it is the existing house
convention's default test-fixture archetype (`tests/test_envelope_patcher.py::_make_row`,
`tests/test_envelope_patcher_windows.py::_make_row`); CZ6A because `layout_assign` baseline
prototypes are natively built for a Buffalo (CZ6A) climate (`envelope_patcher.py` module
docstring).

## thermostat_setback (J03, 2026-09-17; occupancy heuristic rewritten J03b, 2026-09-17)

**WITHDRAWN (J03b, 2026-09-17).** Run against the real prototype
`ASHRAE901_OfficeMedium_STD2022_Buffalo.idf`, the J03 occupancy heuristic tested the END time of a
`Schedule:Compact` `Until:` entry against a hard-coded 07:00-18:00 business-hours window. The DOE
occupied block `Until: 22:00, 21.0` covers 07:00-22:00 but was tested at 22:00 and labelled
unoccupied; no workday entry fell inside the window at all. With no candidate found, the code fell
back to the earliest entry (the 05:00 night-setback value, 15.6) and treated it as the occupied
setpoint, driving the occupied heating setpoint from 21.0 C to 10.0444 C and the occupied cooling
setpoint from 24.0 C to 29.4778 C for every hour of every day — switching the HVAC off, not
applying a setback. `apply_measure` now refuses to run it: it reports `status: "withdrawn"` with
this reason and changes nothing. The occupancy heuristic was rewritten (J03b) to derive the
occupied setpoint and setback level from each schedule's own workday values (`max`/`min` for
heating, `min`/`max` for cooling) instead of an assumed clock window, to skip `WinterDesignDay` /
`SummerDesignDay` blocks entirely, and to report `gate_no_setback_block` rather than invent
occupied hours for a schedule with no setback structure at all. The citation and targets below are
unchanged and still describe the measure's intended behaviour once it is verified against the real
prototype and returned to `"active"`.

**What it changes.** For each `ThermostatSetpoint:DualSetpoint` object, its heating and cooling
`Schedule:Compact` setpoint schedules. A schedule whose values are constant (no setback at all) has
no setback block to deepen and is reported `gate_no_setback_block`, left untouched; one with an
existing setback shallower than required is deepened; one already at or past the required
magnitude is left untouched (`already_compliant`). Never narrows an existing deadband.

**Targets:** `heating_setback_delta_c = 5.5556`, `cooling_setup_delta_c = 2.7778` (delta-T, degrees
Celsius / Kelvin — the two are the same size for a temperature difference).

**Public source.** ASHRAE 90.1-2022 Section 6.4.3.3.2, "Setback Controls" (a numbered subsection of
Section 6.4.3.3, "Off-Hour Controls"). Read directly, primary text, from a full, freely reachable
(no login, no paywall) copy of ANSI/ASHRAE/IES Standard 90.1-2022 (I-P) at
`https://nclose.us.com/wp-content/uploads/2024/02/ASHRAE-90.1-2022-.pdf`, retrieved 2026-09-17,
converted with `pdftotext -layout`. Exact text (page carries the notice "Copyrighted material
licensed to Sean Scott ... All rights reserved. No further reproduction or distribution is
permitted" — quoted here only to identify and verify the section, not redistributed):

> 6.4.3.3.2 Setback Controls. Heating systems shall be equipped with controls capable of and
> configured to automatically restart and temporarily operate the system as required to maintain
> zone temperatures above an adjustable heating set point at least 10F below the occupied heating
> set point. Cooling systems shall be equipped with controls capable of and configured to
> automatically restart and temporarily operate the mechanical cooling system at the lowest
> practical fan speed as required to maintain zone temperatures below an adjustable cooling set
> point at least 5F above the occupied cooling set point or to prevent maximum space humidity
> levels as required by Standard 62.1.

This is a required capability delta-T (a control must be able to reach a setpoint at least this
far from the occupied setpoint), not a paywalled absolute-value table digit, matching the task's
citation rule.

**Re-derivation.** 10 F is a temperature *difference*, not a reading, so the F-to-C conversion uses
the 5/9 scale factor only, no 32-degree offset: 10 x 5/9 = 5.55555... C, stored as 5.5556. Cooling:
5 x 5/9 = 2.77777... C, stored as 2.7778.

**Implementation convention not covered by the cited text (documented here, not a citation
matter).** ASHRAE 90.1-2022 6.4.3.3.2 states a magnitude, not a schedule shape. To decide which
`Schedule:Compact` value fields are "outside the occupied block" when introducing or deepening a
setback, `_select_reference_and_outside()` in `measures.py` picks a single reference (occupied)
value field per schedule — the first value field whose `Until:` time falls in (07:00, 18:00] under
a `For:` line that is not a recognized non-workday keyword (weekend/Saturday/Sunday/
holiday/AllOtherDays/custom), or, failing that, the field with the earliest `Until:` time — and
treats every other value field in the schedule as adjustable. This 07:00-18:00 business-hours
window is an implementation default, not a cited number; flagged here for the manager to confirm
or replace with a project-standard occupied-hours convention if one exists elsewhere in OpenUBEM
(none was found — see the block-5 plan / progress log).

**Repointing scope.** Only the one `ThermostatSetpoint:DualSetpoint` object being processed has its
`Heating_Setpoint_Temperature_Schedule_Name` / `Cooling_Setpoint_Temperature_Schedule_Name` field
rewritten to the clone's name. No other object of any type that names the original schedule is
touched, per the measured `ASHRAE901_OutPatientHealthCare_STD2022_Buffalo.idf` (`ALWAYS_ON`, 245
references) and `ASHRAE901_OfficeMedium_STD2022_Buffalo.idf` (15 `ThermostatSetpoint:DualSetpoint`
objects sharing `HTGSETP_SCH_YES_OPTIMUM` / `CLGSETP_SCH_YES_OPTIMUM`) cases named in the block-5
plan.

## clone_schedule (J03, 2026-09-17)

**What it does.** Creates a new `Schedule:Compact` object under a caller-supplied name that copies
every populated field of the named source object, and does not modify the source or repoint
anything itself.

**Implementation note — `obj.fieldnames` is not the real field count.** For an extensible object
type like `Schedule:Compact`, eppy's `fieldnames` property always returns the IDD's extensible
maximum (10001 entries for this object type, verified empirically), regardless of how many fields
are actually populated on that specific object; the real, populated field count is
`len(obj.fieldvalues)` (or equivalently `len(obj.obj)`). `clone_schedule` reads `fieldnames` as
directed but caps the copy at `len(original.fieldvalues)`, so the clone ends up with exactly the
same real field count as the source — copying the full, uncapped `fieldnames` list field-by-field
would instead pad the clone out to 10001 fields (mostly blank), which is not "a full copy," it is
corruption. Verified independence and exact field-for-field equality empirically before writing
the shipped implementation.

## thermostat_setback — restored to active (J03c, 2026-09-17)

**Status update (J03c, 2026-09-17).** `thermostat_setback` was withdrawn at J03b (see that section
above) and is now restored to `"active"`. The J03b-rewritten occupancy heuristic was re-measured
against the real prototype `ASHRAE901_OfficeMedium_STD2022_Buffalo.idf` and the acceptance
condition was met: the occupied heating peak (21.0 C) and the occupied cooling peak (24.0 C) are
untouched; only the night-setback entries move, heating 15.6 -> 15.4444 and cooling 26.7 ->
26.7778, both at `Until: 05:00` and `Until: 24:00` only; `WinterDesignDay` and `SummerDesignDay`
blocks are untouched; 30 clones created, zero originals mutated. The citation, targets, and
`PROVENANCE.md` text under the J03/J03b section above are unchanged and now describe active
behaviour.

## infiltration_tightening (J04, 2026-09-17; revised J04b, 2026-09-17)

**Status.** Shipped `"status": "withdrawn"`, `withdrawn_reason: "pending manager verification against
a real prototype (J04c)"`. `apply_measure` refuses to run it and changes nothing; the applier code
(`_apply_infiltration_tightening`) and its six gates are implemented and unit-tested against
synthetic fixtures only. The manager runs J04c against a real DOE prototype before flipping the
measure to `"active"`.

**J04b ruling (DEFECT J04-D1).** The J04 per-zone proportional split, measured against
`ASHRAE901_OfficeMedium_STD2022_Buffalo.idf`, wrote `0.00022584 m3/s-m2` where Section 11.5.3's own
formula requires `0.00041548 m3/s-m2` -- a ratio of `0.544`, over-tightening by 45%. The invented
split is removed rather than tuned: Section 11.5.3 already states the intensity directly for the two
calculation methods it covers, so there is nothing to invent for those, and the two methods it does
not cover are now gated (`gate_unsupported_calculation_method`) rather than reached through a
convention. Standing rule: where a cited standard states a quantity directly, no OpenUBEM convention
may restate it; a convention is only admissible for a case the standard does not cover at all.

**What it changes.** Lowers `ZoneInfiltration:DesignFlowRate` objects toward the standard's own
uniform intensity, applied building-wide, never raising a value. Never touches
`ZoneInfiltration:EffectiveLeakageArea`, `ZoneInfiltration:FlowCoefficient`, any
`ZoneInfiltration:DesignFlowRate` whose `Design_Flow_Rate_Calculation_Method` is outside `Flow/Zone`,
`Flow/Area`, `Flow/ExteriorArea`, `Flow/ExteriorWallArea` (for example `AirChanges/Hour`), any
`Flow/Zone` or `Flow/ExteriorArea` object (Section 11.5.3 states no formula for either), or any object
whose four infiltration coefficients are not the DOE-2 wind-driven set within `1e-6`.

**Source 1 (the conversion, primary).** ANSI/ASHRAE/IES Addendum t to ANSI/ASHRAE/IES Standard
90.1-2019, Section 11.5.3 "Modeling Building Envelope Air Leakage", published 2022-08-12,
`ashrae.org/file library/technical resources/standards and guidelines/standards addenda/90_1_2019_t_20220812.pdf`.
Verbatim formulas: `IFLR = 0.112 x I75Pa x S / AFLR`; `IAGW = 0.112 x I75Pa x S / AAGW`;
`I75Pa = Q / S`, where `S` is the total building envelope area (lowest floor, below-grade and
above-grade walls, roof, including vertical fenestration and skylights). `IFLR`/`IAGW` are the
adjusted air leakage rate at a reference wind speed of 10 mph (4.47 m/s), exactly the DOE-2
wind-velocity-coefficient reference.

**Source 2 (independent confirmation of the 0.112 factor and the coefficient set).** Gowri K.,
D.W. Winiarski, R.E. Jarnagin, *Infiltration Modeling Guidelines for Commercial Building Energy
Analysis*, PNNL-18898, Pacific Northwest National Laboratory, 2009, Section 4: derives
`Idesign = 0.2016 cfm/ft2 (0.001024 m3/s-m2)` from `I75Pa = 1.8 cfm/ft2 (0.00915 m3/s-m2)`;
`0.2016 / 1.8 = 0.112` exactly. Stated assumptions: wind exponent `n = 0.65`, `UH = 4.47 m/s`,
`rho = 1.18 kg/m3`, `Cs = 0.1617`, urban terrain `alpha_bldg = 0.22`. Table 1 gives the DOE-2
coefficient set as constant `0`, temperature `0`, velocity `0.224`, velocity-squared `0` at the
10 mph reference wind speed -- the coefficient set `IFLR`/`IAGW` assume, and the one this measure
requires (within `1e-6`) before it will touch an object (`gate_unsupported_coefficients` otherwise).

**Source 3 (the tightening target).** Same Addendum t, Section 5.4.3.1.1 Whole-Building Air Leakage:
the measured air leakage rate of the building envelope "shall not exceed 0.35 cfm/ft2 (1.7 L/s.m2)
under a pressure differential of 75 Pa (0.30 in. of water), with this air leakage rate normalized by
the sum of the above-grade and below-grade building envelope areas." Addendum t lowers the
90.1-2019 published value of 0.40 cfm/ft2 to 0.35; the budget-building clause in the same addendum
independently fixes `I75Pa = 0.35 cfm/ft2 (1.7 L/s.m2)` of building envelope area. Used as
`I75Pa_target = 0.0017 m3/s-m2`, citing Addendum t and not the 2019 base document, because the base
document states the superseded 0.40 value.

**Re-derivation.** `IFLR = conversion_factor x i75pa_target_m3_s_m2 x S / AFLR` and
`IAGW = conversion_factor x i75pa_target_m3_s_m2 x S / AAGW` are computed by the code from the two
stored parameters (`conversion_factor = 0.112`, `i75pa_target_m3_s_m2 = 0.0017`) and the three
building-level areas (`S`, `AFLR`, `AAGW`) at run time, not copied in as a pre-multiplied digit;
`measures.json` stores only the two source factors, matching the plan's instruction to recompute
rather than copy the derived target. `AFLR` is the summed gross floor area of every zone that owns a
`ZoneInfiltration:DesignFlowRate` object (from that zone's `Floor`-type `BuildingSurface:Detailed`
objects); `AAGW` is the summed above-grade exterior wall area (`Outside_Boundary_Condition ==
Outdoors`, `Wall`-type only) of those same zones. Both intensities are applied uniformly to every
object of the matching method -- Section 11.5.3 states a single building-level intensity per method,
not a per-zone one, so no object of a given method is scaled differently from any other.

**Unit handling (implementation, not a citation matter).** `Flow/Area` objects declare
`Flow_Rate_per_Floor_Area` and `Flow/ExteriorWallArea` objects declare
`Flow_Rate_per_Exterior_Surface_Area`, both already in the field's native units, m3/s-m2 -- the same
units `IFLR`/`IAGW` are expressed in. Each covered object's existing declared value is therefore
compared directly against the uniform intensity for its method, with no per-zone conversion or
back-conversion; the lower of the two is kept and written back through that same field, so the
object's own declared units and calculation method are never altered. `Flow/Zone` (which declares an
absolute `Design_Flow_Rate`, no area) and `Flow/ExteriorArea` have no formula in Section 11.5.3 and
are gated (`gate_unsupported_calculation_method`) rather than approximated through a substitute area.
A building whose qualifying zones sum to `AFLR == 0.0` or `AAGW == 0.0` for the method an object
needs cannot be safely divided and that object is reported `gate_zero_normalizing_area`, left
byte-identical, rather than divided by zero.

**Field names (verified against the EnergyPlus 23.1 IDD, `C:\EnergyPlusV23-1-0\Energy+.idd`).**
`Zone_or_ZoneList_or_Space_or_SpaceList_Name`, `Design_Flow_Rate_Calculation_Method`,
`Design_Flow_Rate` (m3/s), `Flow_Rate_per_Floor_Area` (m3/s-m2), `Flow_Rate_per_Exterior_Surface_Area`
(m3/s-m2, shared by both `Flow/ExteriorArea` and `Flow/ExteriorWallArea`), `Constant_Term_Coefficient`,
`Temperature_Term_Coefficient`, `Velocity_Term_Coefficient`, `Velocity_Squared_Term_Coefficient` --
matching the field-name trap already registered in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`
from the J01 census (`Flow_Rate_per_Floor_Area` / `Flow_Rate_per_Exterior_Surface_Area`, not the
guessed `Flow_per_Zone_Floor_Area` / `Flow_per_Exterior_Surface_Area`).

## infiltration_tightening — restored to active (J04c, 2026-09-17)

**Status update (J04c, 2026-09-17).** `infiltration_tightening` was withdrawn at J04b (see that
section above) and is now restored to `"active"`. The J04b-corrected applier was measured against
the real prototype `ASHRAE901_OfficeMedium_STD2022_Buffalo.idf` and the pinned acceptance condition
was met: every `Flow/ExteriorWallArea` object receives the single uniform value
`0.00041548 m3/s-m2`, the standard's own `0.112 x I75Pa x S / AAGW` with `S = 4315.5894 m2` and
`AAGW = 1977.6687 m2`; the `Flow/Zone` door object `Perimeter_bot_ZN_1_Door_Infiltration` is gated
`gate_unsupported_calculation_method` and left byte-identical at `0.678659786 m3/s`; 15 objects were
tightened; zero objects gained leakage. `Flow/ExteriorArea` and `Flow/Zone` objects are declined by
design, not by omission: the cited clause (Section 11.5.3) states a formula only for floor-area
normalization (`Flow/Area`) and above-grade-wall-area normalization (`Flow/ExteriorWallArea`), and
has no formula for either the whole-zone absolute flow (`Flow/Zone`) or the general exterior-surface
normalization (`Flow/ExteriorArea`), so both remain gated rather than approximated through a
substitute area. The citation, targets, and `PROVENANCE.md` text under the J04/J04b section above are
unchanged and now describe active behaviour.
