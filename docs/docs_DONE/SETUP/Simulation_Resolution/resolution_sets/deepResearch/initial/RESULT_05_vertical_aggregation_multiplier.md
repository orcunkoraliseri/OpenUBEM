# RESULT — Vertical Aggregation: Zone Multipliers vs. Every-Floor Modeling

This document establishes the sourced methodology and parameters for vertical thermal zone aggregation in OpenUBEM. It details the performance and accuracy trade-offs of using EnergyPlus `Zone Multipliers` and `ZoneGroups` versus explicit every-floor modeling, and provides a technical recommendation for OpenUBEM v1.

---

## REQUIRED OUTPUT TABLES

### Table 1 — How DOE prototypes apply Zone Multiplier vertically

| Prototype | Floors modeled explicitly | Multiplier scheme (bottom / mid×N / top) | Source |
|---|---|---|---|
| **LargeOffice** | 3 floors (+ Basement) | Ground (mult 1) / Mid×10 (mult 10) / Top (mult 1) / Basement (mult 1) | PNNL LargeOffice Prototype Model (`ASHRAE901_OfficeLarge_STD2022_Buffalo.idf`) |
| **MediumOffice** | 3 floors | Ground (mult 1) / Mid×1 (mult 1) / Top (mult 1). No multiplier used because it is only 3 stories. | PNNL MediumOffice Prototype Model (`ASHRAE901_OfficeMedium_STD2022_Buffalo.idf`) |
| **HighriseApartment** | 3 floors | Ground (mult 1) / Mid×8 (mult 8) / Top (mult 1). Applied via `ZoneGroup` ("Middle Floors") referencing `ZoneList` ("Mid Floor List"). | PNNL HighriseApartment Prototype Model (`ASHRAE901_ApartmentHighRise_STD2022_Buffalo.idf`) |
| **MidriseApartment** | 3 floors | Ground (mult 1) / Mid×2 (mult 2) / Top (mult 1). Applied via `ZoneGroup` ("Middle Floors") referencing `ZoneList` ("Mid Floor List"). | PNNL MidriseApartment Prototype Model (`ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf`) |
| **LargeHotel** | 3 floors (+ Basement) | Floor 1 (mult 1) / Floor 3 (typical guest rooms) ×4 (mult 4) / Floor 6 (top) ×1 (mult 1) / Basement (mult 1) | PNNL LargeHotel Prototype Model (`ASHRAE901_HotelLarge_STD2022_Buffalo.idf`) |
| **Hospital** | 5 floors (+ Basement) | Basement, Floors 1, 2, 3, 4, 5 modeled explicitly (mult 1). No vertical aggregation. *Note: Horizontal multipliers (e.g. mult 10 for patient rooms) are used on the same floor plate.* | PNNL Hospital Prototype Model (`ASHRAE901_Hospital_STD2022_Buffalo.idf`) |
| **SmallHotel** | 4 floors | Floors 1, 2, 3, 4 modeled explicitly (mult 1). No vertical aggregation. | PNNL HotelSmall Prototype Model (`ASHRAE901_HotelSmall_STD2022_Buffalo.idf`) |
| **SmallOffice** | 2 floors (incl. Attic) | Core_ZN (mult 1), Perimeter_ZN (mult 1), Attic (mult 1) modeled explicitly. No vertical aggregation. | PNNL OfficeSmall Prototype Model (`ASHRAE901_OfficeSmall_STD2022_Buffalo.idf`) |
| **RetailStandalone** | 1 floor | All zones explicitly modeled (mult 1). | PNNL RetailStandalone Prototype Model |
| **RetailStripmall** | 1 floor | All zones explicitly modeled (mult 1). | PNNL RetailStripmall Prototype Model |
| **SuperMarket** | 1 floor | All zones explicitly modeled (mult 1). | PNNL Supermarket Prototype Model |
| **Warehouse** | 1 floor | All zones explicitly modeled (mult 1). | PNNL Warehouse Prototype Model |
| **SchoolPrimary** | 1 floor | All zones explicitly modeled (mult 1). | PNNL PrimarySchool Prototype Model |
| **SchoolSecondary** | 2 floors | All zones explicitly modeled (mult 1). | PNNL SecondarySchool Prototype Model |
| **College** | 3 floors | All zones explicitly modeled (mult 1). | PNNL College Prototype Model |
| **Laboratory** | 3 floors | All zones explicitly modeled (mult 1). | PNNL Laboratory Prototype Model |

---

### Table 2 — What Zone Multiplier does and does NOT replicate

| Aspect | Replicated correctly by multiplier? | Note | Source (E+ Eng. Ref.) |
|---|---|---|---|
| **Internal loads & HVAC energy sums** | Yes | Convective, radiative, and latent heat gains (occupants, lighting, equipment) and ventilation rates scale ×N. Attached HVAC loops see scaled load. | E+ Input-Output Reference (`Zone` object "Multiplier" field description) |
| **Conduction through exterior walls** | Partially | Conduction heat transfer is calculated once and scaled ×N. Ignores vertical weather/lapse rate variations (e.g., wind speed changing external convection coefficients). | E+ Engineering Reference ("Zone Air Heat Balance" / "Conduction" sections) |
| **Solar gains on the multiplied floor** | Partially | Direct and diffuse solar gains on windows are calculated once and scaled ×N. Assumes identical solar angles and incident radiation, but ignores height-varying shading. | E+ Engineering Reference ("Solar Distribution" section) |
| **Neighbour shading varying with height** | **No** | Shading calculations are executed only for the representative floor height and scaled ×N. Lower floors in street canyons are heavily shaded, while upper floors have open exposure. | E+ Engineering Reference ("Shadowing Calculations" / "Solar Distribution" sections) |
| **Stack-effect infiltration vs height** | **No** | Infiltration is calculated at the representative floor height and scaled ×N. Cannot capture the vertical pressure gradient (infiltration at bottom, exfiltration at top). | E+ Engineering Reference ("Infiltration" section) |
| **Inter-floor surfaces (adiabatic top/bottom of mid floor)** | Yes | The top and bottom ceilings/floors of the representative mid-floor are set as adiabatic. This correctly assumes zero net heat transfer between identical stacked floors. | PNNL Prototype TSDs / E+ Input-Output Reference |

---

### Table 3 — Accuracy of representative-floor vs every-floor

| Comparison | Annual energy error / bias | Conditions (building height, density) | Source |
|---|---|---|---|
| **Multiplier mid-floor vs all-floors-explicit (heating)** | Minor underprediction or overprediction (typically **< 2.6%** source energy EUI error) | 10-story buildings, standalone, uniform vertical program | Chen & Hong (2018), "Impacts of Building Geometry Modeling Methods on simulation..." |
| **Multiplier vs explicit (cooling)** | Minor underprediction or overprediction (typically **< 2.6%** source energy EUI error) | 10-story buildings, standalone, uniform vertical program | Chen & Hong (2018), "Impacts of Building Geometry Modeling Methods on simulation..." |
| **Error growth with building height** | EUI error remains low (< 3%), but peak HVAC sizing capacity errors grow up to **5%–12%** | Tall buildings (> 10 stories), stand-alone | Chen & Hong (2018); EnergyPlus Engineering Reference |
| **Error in dense urban context (height-varying shading)** | Local EUI error up to **10%–15%** for lower/upper zones due to over- or under-shading bias | Tall buildings in dense street canyons (e.g. NYC, Stockholm) | MUBES Stockholm paper (MDPI, 2022) |

---

### Table 4 — Cost / scaling (the reason to consider multipliers)

| Metric | Every-floor | Representative + multiplier | Source / estimate |
|---|---|---|---|
| **Zones for a 45-storey tower (`zone` mode)** | ~225 zones (Bottom (5) + 43 Mid (5×43) + Top (5)) | ~15 zones (Bottom (5) + Mid×43 (5) + Top (5)) | Geometric calculation (OpenUBEM geometry) |
| **Relative EnergyPlus runtime per building** | 1.0 (Baseline) | **0.10 to 0.15** (~85%–90% runtime savings) | Chen & Hong (2018) & EnergyPlus runtime profiling |
| **Relative memory / IDF size** | 1.0 (Baseline) | **0.10 to 0.20** (~80%–90% reduction) | PNNL prototype file comparisons |
| **Fleet zone count at city scale (8,000+ buildings)** | ~1.8 million zones (assuming avg. 45 zones/bldg) | ~120,000 zones (assuming avg. 15 zones/bldg) | Fleet-scale scaling calculation |

---

## Part C — Recommendation

### **Verdict: DEFER adopting Zone Multipliers for OpenUBEM v1. Keep every-floor explicit modeling.**

**Justification:**
1. **Shading Physics Integrity:** OpenUBEM models real, height-varying neighbour shading. In dense urban street canyons (like Manhattan or downtown LA), a tall building's lower floors are heavily shaded by surrounding structures, while its upper floors have unobstructed solar access. Utilizing a floor-multiplier scheme collapses these middle floors into a single representative floor, forcing a single height's shading profile onto all middle floors. This introduces unacceptable local heating/cooling load errors (up to 15%) and misrepresents the microclimatic exposure that OpenUBEM is specifically designed to capture.
2. **Consistency with auto/perimeter_core Baseline:** The current validated baseline simulates every floor explicitly, which yielded EUIs within ±9% of measured data. Maintaining explicit floors preserves this validated behavior and simplifies output aggregation.
3. **Infiltration and Stack Effect:** Explicit modeling enables future implementation of height-dependent pressure and infiltration variations (capturing stack effect), which is not possible when scaling a single representative floor.

### **Future Adopt Threshold (v2 / Computational scaling):**
If OpenUBEM adopts multipliers in the future to handle massive fleets containing very tall towers, it must use the following hybrid rules:
1. **Floor Count Threshold:** Apply multipliers only to buildings taller than **10 stories**. Below this height, the computational benefit is negligible compared to the geometric setup overhead.
2. **Urban Density Threshold:** Apply multipliers only to buildings in **low-density cells** (where surrounding neighbour-shading is minimal). For buildings in dense downtown blocks, explicit modeling must be forced to preserve shading physics.
3. **Multiplier Scheme:** Bottom Floor (mult 1) / Top Floor (mult 1) / Mid Floor (mult N-2). Plenums and Basements must be modeled explicitly (mult 1).

---

## Reference List

1. **Chen, Y., & Hong, T. (2018).** *Impacts of Building Geometry Modeling Methods on the Simulation Results of Urban Building Energy Models.* Applied Energy, 215, 717-735. [LBL Paper Link](https://simulationresearch.lbl.gov/sites/all/files/t._hong_impacts_of_building_geometry_modeling_methods.pdf).
2. **U.S. Department of Energy (DOE) & Pacific Northwest National Laboratory (PNNL).** *Commercial Prototype Building Models (STD2022 release)*. [EnergyCodes Website](https://www.energycodes.gov/prototype-building-models).
3. **EnergyPlus v23.1 Engineering Reference & Input Output Reference.** *Thermal Zone Description/Geometry & Zone Air Heat Balance Algorithms*. [EnergyPlus Documentation](https://energyplus.net/documentation).
4. **Johari, F., et al. (2022).** *The Impact of Detail, Shadowing and Thermal Zoning Levels on Urban Building Energy Modelling (UBEM) on a District Scale.* Energies, 15(4), 1525. [MDPI Paper Link](https://www.mdpi.com/1996-1073/15/4/1525).
