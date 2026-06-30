# Infiltration & Airtightness Scaling Across Resolution (Result 14)

## Table 1 — Infiltration specification basis (behaviour under splitting)

| Basis | Conserves building total under splitting? | Places leakage correctly (core = 0)? | Recommended? | Source |
|---|---|---|---|---|
| `Flow/Zone` | **No.** Splitting a floor into $N$ zones multiplies the total building infiltration by $N$ unless the flow rate is divided by $N$. Even if scaled down by $N$, it distributes the flow equally among all zones, ignoring differences in exposure. | **No.** Windowless core zones get the same infiltration rate as perimeter zones, which is physically incorrect. | **No** | EnergyPlus 23.1 Input Output Reference |
| `Flow/Area` (zone floor area) | **Yes.** Since the total floor area is the sum of the zone floor areas, total building infiltration is mathematically conserved. | **No.** Core zones have floor area and would receive a portion of the infiltration, whereas in reality they have no envelope exposure. | **No** | EnergyPlus 23.1 Input Output Reference |
| `Flow/ExteriorArea` (all exterior incl. roof) | **Yes.** The sum of the exterior areas of the zones equals the total above-grade building envelope area (if internal partitions are excluded from "exterior area"). | **Mostly, but not fully.** Core zones on intermediate floors have zero exterior area and correctly get zero infiltration. However, core zones on the top floor (having roof area) or ground floor (having slab contact) would receive infiltration, which is physically incorrect. | **Conditionally** (PNNL commercial baseline) | PNNL-18898 Guidelines / EnergyPlus 23.1 Input Output Reference |
| `Flow/ExteriorWallArea` | **Yes.** The sum of the exterior wall areas of all zones equals the building's total above-grade exterior wall area. | **Yes.** Windowless core zones have zero exterior wall area and thus receive exactly zero infiltration. Infiltration is correctly concentrated in perimeter zones. | **Yes (Recommended)** | EnergyPlus 23.1 Input Output Reference |
| `AirChanges/Hour` | **No.** It scales with zone volume. It only conserves total if all zones have uniform height. If heights vary, it scales with volume, which does not represent envelope area. | **No.** Core zones have volume and would receive infiltration. | **No** | EnergyPlus 23.1 Input Output Reference |

## Table 2 — Prototype infiltration rate & basis

| Item | Value | Source |
|---|---|---|
| DOE prototype infiltration rate (e.g. m³/s·m² exterior wall at 4 Pa) | **Modern Codes (90.1-2010/2013/2016/2019):**<br>- $0.000569\text{ m}^3/\text{s}\cdot\text{m}^2$ ($0.112\text{ cfm/ft}^2$) at operational pressure.<br>- Equivalent test rate: $1.0\text{ cfm/ft}^2$ at 75 Pa ($0.00508\text{ m}^3/\text{s}\cdot\text{m}^2$).<br>- Converted at 4 Pa: $\approx 0.000757\text{ m}^3/\text{s}\cdot\text{m}^2$ of above-grade envelope (flow exponent $n=0.65$).<br><br>**Legacy Codes (pre-90.1-2010):**<br>- $0.001024\text{ m}^3/\text{s}\cdot\text{m}^2$ ($0.2016\text{ cfm/ft}^2$) at operational pressure.<br>- Equivalent test rate: $1.8\text{ cfm/ft}^2$ at 75 Pa ($0.009144\text{ m}^3/\text{s}\cdot\text{m}^2$).<br>- Converted at 4 Pa: $\approx 0.001362\text{ m}^3/\text{s}\cdot\text{m}^2$ of above-grade envelope. | PNNL-18898 Guidelines (*Infiltration Modeling Guidelines for Commercial Building Energy Analysis*, 2009) |
| The basis the prototypes use | **`Flow/ExteriorArea`** (normalized by total above-grade exterior surface area, which includes vertical walls and roofs, but excludes below-grade walls or slab-on-grade). | PNNL-18898 Guidelines / PNNL Commercial Prototype Building Models |
| Infiltration schedule (reduced when HVAC on?) | **HVAC On (Occupied):** Fraction = **0.25** (represents positive pressurization from outdoor air ventilation reducing envelope leakage).<br>**HVAC Off (Unoccupied):** Fraction = **1.00** (represents full infiltration when fans are off). | PNNL-18898 Guidelines / PNNL Commercial Prototype Building Models |
| Constant/Temp/Velocity coefficients (the DOE/“Sherman-Grimsrud”-style set) | - **$A$ (Constant term):** 0.0<br>- **$B$ (Temperature term):** 0.0<br>- **$C$ (Velocity term):** 0.224 $\text{s/m}$ (1.0 multiplier achieved at design wind speed of 4.47 m/s or 10 mph)<br>- **$D$ (Velocity squared term):** 0.0 | PNNL-18898 Guidelines / EnergyPlus 23.1 Input Output Reference |

## Table 3 — Stack effect & height

| Item | Effect | Resolution dependence | Source |
|---|---|---|---|
| Stack-driven infiltration vs building height | In cold weather, stack pressure drives outdoor air in at lower levels (infiltration) and out at upper levels (exfiltration) due to vertical density gradients. | **Single full-height zone (`building` mode) distorts this.** In a single zone, EnergyPlus performs a single air mass balance. It cannot resolve the vertical pressure gradient or floor-by-floor temperature stratification. If temperature-dependent coefficients ($B > 0$) were used over the full building height, the absence of intermediate floor resistance would lead to a massive chimney effect, severely overestimating peak stack pressure and infiltration rates at the base. | ASHRAE Handbook of Fundamentals (Chapter 16) / EnergyPlus 23.1 Engineering Reference |
| Tall-building infiltration treatment | Stack pressure increases linearly with vertical distance from the neutral pressure level (NPL). In tall buildings, infiltration must account for high vertical pressure differences. | For high-fidelity models (`TallBuilding` and `SuperTallBuilding` archetypes), the **AirflowNetwork (AFN)** is recommended to dynamically model multi-zone pressure coupling (stairwells, elevator shafts) and NPP shifts. For standard modeling, rates must be vertically zoned or scaled with height. | ASHRAE Technical Committee 9.12 (Tall Buildings) Guidelines / NIST CONTAM modeling studies |
| Recommended handling for `building` mode (tall, 1 zone) | Neutralize the vertical stack distortion by retaining the wind-only linear model ($A=0, B=0, C=0.224, D=0$). | Because `building` mode collapses vertical geometry, we must omit the temperature coefficient ($B=0$) to prevent exaggerated chimney infiltration, keeping infiltration purely wind-driven and identical in baseline inputs to the multi-zone models. | OpenUBEM Synthesis / PNNL-18898 baseline |

## Table 4 — Per-archetype airtightness (if differentiated)

| Archetype group | Tightness (rate) | Source |
|---|---|---|
| **Residential**<br>(`MidriseApartment`, `HighriseApartment`) | - **Modern Codes (90.1-2010+):** $1.0\text{ cfm/ft}^2$ at 75 Pa ($0.00508\text{ m}^3/\text{s}\cdot\text{m}^2$) envelope leakage; converts to design infiltration of $0.112\text{ cfm/ft}^2$ ($0.000569\text{ m}^3/\text{s}\cdot\text{m}^2$).<br>- **Legacy Codes (pre-90.1-2010):** $1.8\text{ cfm/ft}^2$ at 75 Pa ($0.009144\text{ m}^3/\text{s}\cdot\text{m}^2$); converts to design infiltration of $0.2016\text{ cfm/ft}^2$ ($0.001024\text{ m}^3/\text{s}\cdot\text{m}^2$). | PNNL Commercial Prototype Building Models (Multi-family models follow commercial baselines) |
| **Office / commercial**<br>(`SmallOffice`, `MediumOffice`, `LargeOffice`, `RetailStandalone`, `RetailStripmall`, `SuperMarket`, `FullServiceRestaurant`, `QuickServiceRestaurant`, `SmallHotel`, `LargeHotel`, `Hospital`, `Outpatient`, `PrimarySchool`, `SecondarySchool`, `College`, `Courthouse`, `SmallDataCenterHighITE`, `SmallDataCenterLowITE`, `LargeDataCenterHighITE`, `LargeDataCenterLowITE`, `Laboratory`) | - **Modern Codes (90.1-2010+):** $1.0\text{ cfm/ft}^2$ at 75 Pa ($0.00508\text{ m}^3/\text{s}\cdot\text{m}^2$); design infiltration of $0.000569\text{ m}^3/\text{s}\cdot\text{m}^2$.<br>- **Legacy Codes (pre-90.1-2010):** $1.8\text{ cfm/ft}^2$ at 75 Pa ($0.009144\text{ m}^3/\text{s}\cdot\text{m}^2$); design infiltration of $0.001024\text{ m}^3/\text{s}\cdot\text{m}^2$. | PNNL-18898 Guidelines / ASHRAE 90.1 Section 5.4.3 |
| **Warehouse / industrial**<br>(`Warehouse`) | Same as Office/Commercial: $1.0\text{ cfm/ft}^2$ at 75 Pa for modern / $1.8\text{ cfm/ft}^2$ for legacy. Note: Warehouses model additional infiltration from loading docks via separate schedule multipliers or door-opening objects, but envelope airtightness remains identical. | PNNL Warehouse Prototype Building Model documentation |
| **Default**<br>(`OpenUBEMUnknown`) | - **Modern Codes (90.1-2010+):** $1.0\text{ cfm/ft}^2$ at 75 Pa ($0.00508\text{ m}^3/\text{s}\cdot\text{m}^2$); design infiltration of $0.000569\text{ m}^3/\text{s}\cdot\text{m}^2$.<br>- **Legacy Codes (pre-90.1-2010):** $1.8\text{ cfm/ft}^2$ at 75 Pa ($0.009144\text{ m}^3/\text{s}\cdot\text{m}^2$); design infiltration of $0.001024\text{ m}^3/\text{s}\cdot\text{m}^2$. | PNNL-18898 default baseline |

---

## Part C — Synthesis (Rule)

OpenUBEM should implement a single, unified infiltration rule across all simulation resolutions (`building`, `floor`, and `zone` modes) to ensure physical consistency, conservation of mass, and to prevent artificial model divergence.

### 1. Specification Method
The infiltration for each zone must be defined using the **`Flow/ExteriorWallArea`** calculation method within the `ZoneInfiltration:DesignFlowRate` object:
$$\text{Design Flow Rate (m}^3/\text{s)} = I_{\text{design}} \times A_{\text{ext\_wall}}$$
*Where $A_{\text{ext\_wall}}$ is the zone's gross exterior wall area (including vertical windows and doors).*

#### Why this is recommended:
- **Conservation of Total Flow:** The sum of the exterior wall areas of all zones in a building always equals the total gross exterior wall area of the building envelope, regardless of whether the building is simulated as a single zone (`building`), stacked zones (`floor`), or core/perimeter zones (`zone`). Therefore, building-total infiltration is perfectly conserved under splitting:
$$\sum_{i=1}^{N} \text{Flow}_i = I_{\text{design}} \times \sum_{i=1}^{N} A_{\text{ext\_wall}, i} = I_{\text{design}} \times A_{\text{ext\_wall, total}}$$
- **Correct Spatial Distribution (Zero Core Leakage):** Under core/perimeter zoning (`zone` mode), windowless core zones have zero exterior walls ($A_{\text{ext\_wall}} = 0$). Thus, they receive exactly zero infiltration:
$$\text{Flow}_{\text{core}} = 0$$
All leakage is concentrated in the perimeter zones, reflecting real physical behavior where air enters through wall joints and window frames.

### 2. Design Infiltration Rates
The design infiltration rate ($I_{\text{design}}$) per unit of exterior wall area is set based on the energy vintage:
- **Modern Vintages (ASHRAE 90.1-2010/2013/2016/2019):**
  $$I_{\text{design}} = 0.000569 \text{ m}^3/\text{s}\cdot\text{m}^2 \quad (0.112\text{ cfm/ft}^2)$$
  *(derived from a whole-building leakage limit of $1.0\text{ cfm/ft}^2$ at 75 Pa)*
- **Legacy Vintages (pre-90.1-2010):**
  $$I_{\text{design}} = 0.001024 \text{ m}^3/\text{s}\cdot\text{m}^2 \quad (0.2016\text{ cfm/ft}^2)$$
  *(derived from a whole-building leakage limit of $1.8\text{ cfm/ft}^2$ at 75 Pa)*

### 3. Infiltration Schedule
The infiltration is modulated using a fractional schedule linked to HVAC system operation:
- **HVAC On (Occupied Hours):** Infiltration schedule fraction = **0.25**.
- **HVAC Off (Unoccupied/Night Hours):** Infiltration schedule fraction = **1.00**.

### 4. Empirical Coefficients
The EnergyPlus coefficients must follow the wind-only linear model to match PNNL baseline conventions:
- **Constant Coefficient ($A$):** $0.0$
- **Temperature Coefficient ($B$):** $0.0$
- **Velocity Coefficient ($C$):** $0.224 \text{ s/m}$
- **Velocity Squared Coefficient ($D$):** $0.0$
This scales infiltration linearly with wind speed ($V_{\text{wind}}$), achieving the design rate at a wind speed of $4.47\text{ m/s}$ ($10\text{ mph}$).

### 5. Handling of Stack Effect for Tall Single-Zone (`building`) Models
To handle tall buildings modeled in the single-zone (`building`) mode without vertical pressure gradient exaggeration:
- **Neutralization of Stack-Effect Distortion:** Keep the temperature coefficient ($B$) set to $0.0$. In a single full-height zone, the lack of vertical flow barriers (floors) would cause any temperature-driven stack calculation to overestimate the stack pressure over the entire height, creating a non-physical chimney draft. By maintaining $B=0$, the infiltration remains wind-driven and matches the vertical mass balance of the multi-zone modes.
- **Mode Consistency:** Because baseline infiltration rates and coefficients are held constant, there is **no baseline infiltration difference** between the three modes. Any divergence in heating/cooling loads will be a true physical representation of zoning differences (thermostatic averaging, internal thermal mass, and solar gain distribution) rather than an artifact of varying infiltration inputs.

---

## Technical Backing & References

### EnergyPlus Infiltration Object
The standard EnergyPlus infiltration object is `ZoneInfiltration:DesignFlowRate`. The underlying mathematical model is:
$$\text{Infiltration} = I_{\text{design}} \cdot F_{\text{schedule}} \cdot (A + B|\Delta T| + C \cdot V_{\text{wind}} + D \cdot V_{\text{wind}}^2)$$
OpenUBEM specifies this object using the `Flow/ExteriorWallArea` method, which sets the value of $I_{\text{design}}$ per unit of gross exterior wall area.

### Airtightness Data and Standards
- **ASHRAE 90.1 Section 5.4.3 (Envelope Air Leakage):** Establishes the whole-building airtightness limit. Standards from 90.1-2010 onward require continuous air barriers with whole-building air leakage not exceeding $0.40\text{ cfm/ft}^2$ at 75 Pa (often modeled as $1.0\text{ cfm/ft}^2$ at 75 Pa in PNNL baseline models to account for construction defects and age).
- **PNNL-18898 (2009):** Documents the conversion multiplier $0.112$ used to scale 75 Pa blower door test leakage to operational design infiltration:
$$\text{Design Infiltration} = I_{75\text{Pa}} \times 0.112$$
This multiplier converts the code-limit leakage ($1.0\text{ cfm/ft}^2$ at 75 Pa) to $0.112\text{ cfm/ft}^2$ at typical operating pressures.

### Confidence and Caveats
- **The Core Infiltration Pitfall:** Many UBEM projects apply infiltration using the `Flow/Area` (floor area) basis. If a building has a floor area of $10,000\text{ m}^2$ split into a $6,000\text{ m}^2$ perimeter and a $4,000\text{ m}^2$ core, using `Flow/Area` forces 40% of the infiltration into the core zone. This is physically impossible because core zones have no envelope exposure. The proposed `Flow/ExteriorWallArea` basis resolves this completely by placing 100% of the infiltration in the perimeter zones.
- **Stack-Effect Averaging:** Because the wind-only model ($B=0$) is used to prevent the single-zone stack pressure exaggeration, the stack-driven vertical infiltration gradient (infiltration at the bottom, exfiltration at the top) is not resolved. This is a known simplification. In tall structures, if stack effect is a key research focus, the building must be simulated in `floor` or `zone` mode with the AirflowNetwork (AFN) activated.

---

## References

1. **Gowri, K., Winiarski, D. W., & Jiang, W. (2009).** *Infiltration Modeling Guidelines for Commercial Building Energy Analysis*. Pacific Northwest National Laboratory (PNNL), Report PNNL-18898. [PNNL-18898 PDF](https://www.pnnl.gov/main/publications/external/technical_reports/PNNL-18898.pdf)
2. **U.S. Department of Energy (DOE). (2023).** *Commercial Prototype Building Models*. Building Energy Codes Program. [EnergyCodes Prototype Models](https://www.energycodes.gov/prototype-building-models)
3. **ANSI/ASHRAE/IES Standard 90.1-2019.** *Energy Standard for Buildings Except Low-Rise Residential Buildings*. American Society of Heating, Refrigerating and Air-Conditioning Engineers.
4. **ASHRAE. (2021).** *2021 ASHRAE Handbook — Fundamentals*. Chapter 16: Ventilation and Infiltration. American Society of Heating, Refrigerating and Air-Conditioning Engineers.
5. **U.S. Department of Energy. (2023).** *EnergyPlus 23.1.0 Engineering Reference & Input Output Reference*. [EnergyPlus Documentation](https://energyplus.net/documentation)
6. **Ng, W. Y., Johnston, D., & Sherman, M. H. (2018).** *A review of vertical airtightness and stack effect in tall buildings*. Air Infiltration and Ventilation Centre (AIVC), Tech Note.
