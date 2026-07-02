# RESULT_16_output_aggregation_reporting_provenance — Results Pipeline, Denominator, and Provenance

This report establishes the methodology for aggregating multi-zone EnergyPlus simulation outputs to building-level totals, defines the EUI denominator contract, and specifies the provenance metadata requirements across simulation resolution modes in OpenUBEM. The rules are designed to ensure that results are mathematically comparable regardless of the selected `resolution_mode` (`building`, `floor`, `zone`, or `auto`).

---

## 1. REQUIRED OUTPUT TABLES

### Table 1 — Aggregating per-zone output to building totals

| Quantity | Source (building `Output:Meter` vs sum of zone vars) | Zone-Multiplier-safe? | Recommended | Source |
|---|---|---|---|---|
| **Total site/source energy** | Building `Output:Meter` (`Electricity:Facility`, `NaturalGas:Facility`) | Yes (meters automatically scale by the multiplier) | Read building-level facility meters directly from the SQL output. | EnergyPlus Input Output Reference (v23.1), "Meters" & "Output:Meter" |
| **End-use splits (heating/cooling/lights/equip/fans/pumps/DHW/refrig)** | Building `Output:Meter` (e.g. `Cooling:Electricity`, `InteriorLights:Electricity`, `InteriorEquipment:Electricity`) | Yes (meters automatically scale by the multiplier) | Read building-level end-use meters directly from SQL. Avoid summing zone variables, which are not multiplier-safe. | EnergyPlus Input Output Reference (v23.1), "Meters" & "Output:Meter" |
| **Per-zone temperatures (for IOD)** | Sum/average of zone variables (`Zone Operative Temperature`, `Zone People Occupant Count`) | No (zone variables represent a single zone; must be scaled manually) | Occupant-weighted mean of per-zone exceedances. Scale the occupant count by the zone multiplier from the `Zones` SQL table. | EnergyPlus Input Output Reference (v23.1), "Zone Multiplier" & "Report Variables" |
| **Peak demand** | Building `Output:Meter` peak demand (from `Electricity:Facility` or ABUPS table) | Yes (meters automatically scale by the multiplier) | Read from the `TabularDataWithStrings` table in SQL (`AnnualBuildingUtilityPerformanceSummary` -> "Utility Use Summary" -> "Electricity" -> "Peak Demand"). | EnergyPlus Input Output Reference (v23.1), "Tabular Reports" |

---

### Table 2 — EUI denominator consistency

| Item | Rule | Source |
|---|---|---|
| **Floor area = `footprint_area_m2 × num_floors` in ALL modes** | The EUI denominator must be locked to the metadata contract area: $A_{\text{floor}} = A_{\text{footprint}} \times N_{\text{floors}}$ from the database. This value must remain identical across all resolution modes. | OpenUBEM results schema design convention |
| **Does splitting/multiplier change the conditioned floor area E+ reports?** | Yes. In `building` mode (1 zone), EnergyPlus reports only the footprint area ($A_{\text{footprint}}$), completely omitting intermediate floor areas. In `floor` or `zone` mode, buffers and simplifications cause minor geometric deviations, and multipliers limit the modeled area. | EnergyPlus Engineering Reference (v23.1), "Zone Multiplier" & OpenUBEM zoning schema |
| **Reconcile E+ reported area vs OpenUBEM's contract area** | Always use the OpenUBEM metadata contract area ($A_{\text{floor}}$) as the denominator for EUI. Do NOT use the floor area reported in EnergyPlus SQL or tabular output, as resolution-dependent geometric variations will introduce artificial noise into EUI comparisons. | OpenUBEM results schema design convention |

---

### Table 3 — IOD / comfort metric across zones

| Item | Method | Source |
|---|---|---|
| **IOD from a single zone (building mode)** | Compute directly from the single zone's hourly operative temperature ($T_{\text{ot}}$) and occupancy ($N_{\text{occ}}$) using the ASHRAE Standard 55 adaptive comfort model. | OpenUBEM Design Doc (§3D) & ASHRAE Standard 55-2020 |
| **IOD aggregation across N zones (area-weighted? worst zone?)** | Use occupant-count-weighted mean of per-zone IOD (exceedance). The weighting occupant count for each zone must be scaled by its `Zone Multiplier` (queried from the `Zones` SQL table) to represent the actual population. | OpenUBEM results parser (`_compute_iod`) & EnergyPlus Engineering Reference (v23.1) |
| **Consistency of IOD definition across modes** | Mathematically identical adaptive comfort exceedance formula applied across all modes, collapsing to a single building-wide value. Exclusion of unconditioned zones (zero design occupancy) is required. | OpenUBEM Design Doc (§3D) & ASHRAE Standard 55-2020 |

---

### Table 4 — Provenance & reproducibility

| Field | Record where | Source |
|---|---|---|
| **`resolution_mode` per building** | Stored in `manifest.parquet` and Step-5 final output tables (e.g. `results.csv` or `results.geojson`) as a string column: `'building'`, `'floor'`, `'zone'`, or `'auto'`. | OpenUBEM reproducibility guidelines |
| **`zoning_strategy` actually used (incl. fallbacks)** | Already recorded in `manifest.parquet` (values: `'single_zone'`, `'one_zone_per_floor'`, `'perimeter_core'`). Enables verification of target vs. executed geometry. | `openubem/geometry/zoning.py` & existing parser |
| **`num_zones` per building** | Already recorded in `manifest.parquet` and Step-5 results. | `openubem/results/parser.py` |
| **Seed / version stamping unchanged** | Logged in the project run metadata (Git commit hash, OpenUBEM library version, EPW weather file name, and random seed). | Standard software reproducibility practice |

---

## 2. PART C — SYNTHESIS (AGGREGATION + PROVENANCE RULE)

To ensure consistency and comparability across different simulation resolutions, the results pipeline must adhere to three core rules:

### 1. Aggregation Rule
* **Preferred Source:** All energy end-use EUIs (heating, cooling, lighting, equipment, fans, pumps, water systems, refrigeration, and cooking) must be extracted from building-level `Output:Meter` objects (e.g. `Cooling:Electricity`, `InteriorLights:Electricity`) in the SQLite output. Meters automatically sum energy across all zones and scale them by their respective `Zone Multiplier` (if applicable), eliminating the risk of under-counting.
* **Zone-Level Exception (Comfort Metrics):** For non-meterable, zone-specific variables like `Zone Operative Temperature` used in the Index of Thermal Discomfort (IOD), aggregation must be performed as an occupant-count-weighted average of exceedances across all occupied zones:
  $$\text{IOD}_{\text{building}} = \frac{\sum_{z \in \text{zones}} (\text{IOD}_z \times N_{\text{occ}, z} \times M_z)}{\sum_{z \in \text{zones}} (N_{\text{occ}, z} \times M_z)}$$
  where $\text{IOD}_z$ is the exceedance calculated for zone $z$, $N_{\text{occ}, z}$ is the zone's design occupancy, and $M_z$ is the zone multiplier queried from the SQL `Zones` table. Unconditioned zones (e.g. plenums, crawlspaces) where design occupancy is zero must be excluded.

### 2. Denominator Rule
* **Lock the EUI Denominator:** The total conditioned floor area used as the denominator for all EUI calculations must be fixed to the "metadata contract area" ($A_{\text{floor}} = A_{\text{footprint}} \times N_{\text{floors}}$) defined in the building database/manifest. 
* **Bypass EnergyPlus Area Reports:** Do NOT use the building floor area reported by EnergyPlus. In `building` mode (single zone spanning the building height), EnergyPlus only sees the floor area of a single zone ($A_{\text{footprint}}$), which is off by a factor of $N_{\text{floors}}$. In `floor` and `zone` modes, polygon buffering and simplification introduce minor geometric deviations (typically $\pm 1\text{--}3\%$) that would inject artificial variance into EUI comparisons.

### 3. Provenance Fields
* **Self-Describing Results:** The final output schemas (`results.csv`, `results.geojson`) must append a `resolution_mode` column alongside the existing `zoning_strategy` and `num_zones` fields. This ensures that any downstream analysis can filter results by fidelity and audit whether geometry fallbacks occurred (e.g. a building targeted for `zone` mode falling back to `floor` mode because of a narrow footprint).

---

## 3. ENERGYPLUS METER-VS-ZONE-VARIABLE SEMANTICS AND MULTIPLIER HANDLING

In EnergyPlus, a zone multiplier ($M_i$) is a metadata attribute specified in the `Zone` object to replicate thermal zones without duplicating geometric calculations (e.g. in high-rise buildings where middle floors are identical).
* **Meters (`Output:Meter`):** These are cumulative building-level variables. EnergyPlus automatically scales all zone-level loads by their respective zone multiplier before summing them:
  $$E_{\text{meter}} = \sum_{i \in \text{zones}} (E_{\text{zone}, i} \times M_i)$$
  Therefore, reading building-level meters is intrinsically zone-multiplier-safe and robust.
* **Zone Variables:** Report variables requested at the zone level (such as `Zone Lights Electricity Energy` or `Zone Electric Equipment Electricity Energy`) only report the energy consumption of a **single instance** of that zone ($E_{\text{zone}, i}$). If a parser sums these variables directly across all output keys without multiplying by each zone's multiplier $M_i$, the total energy consumption will be severely under-counted (e.g., underestimating lighting by 80% in a building with a multiplier of 5 on middle floors). 
* **Current Parser Limitation:** The existing OpenUBEM parser (`openubem/results/parser.py` §3C) sums zone variables directly for lighting and equipment:
  `kwh = float(df[df["variable_name"] == var_name]["value"].sum())`
  While this is functional when all floors are physically modeled (no multipliers), it is **not** zone-multiplier-safe. Rewiring lighting and equipment to use `InteriorLights:Electricity` and `InteriorEquipment:Electricity` meters is required to ensure compatibility with multiplier-based scaling models.

---

## 4. CONFIDENCE AND CAVEATS

> [!WARNING]
> **The Area-Resolution Mismatch Pitfall**
> The most critical pitfall that can corrupt a resolution comparison is dividing the energy consumption of a low-resolution simulation by a low-resolution floor area. In `building` mode, if a 10-story building is simulated as a single zone, EnergyPlus reports its floor area as $100\text{ m}^2$ (the footprint area), but it simulates the building loads of all 10 stories because internal loads and envelope areas are scaled. If the results parser divides the total energy by the EnergyPlus-reported area ($100\text{ m}^2$) instead of the contract area ($1000\text{ m}^2$), the EUI will be **over-predicted by exactly 1,000% (10x)**. This issue is fully resolved by enforcing a static contract area for EUI.

> [!IMPORTANT]
> **Sub-hourly and Diagnostic Summing Caveat**
> While building-level meters are excellent for annual or hourly total building energy, they do not provide spatial resolution. If a study requires evaluating the energy performance of perimeter vs. core zones (mode 3), building-level meters cannot be used. In such cases, the parser must query zone-level variables and manually multiply them by the zone's multiplier ($M_i$) and divide by the zone's metadata floor area.

---

## 5. REFERENCES

1. EnergyPlus™ Version 23.1.0. *Input Output Reference*. U.S. Department of Energy. Section "Output:Meter" and "Zone Multiplier". URL: [https://energyplus.net/documentation](https://energyplus.net/documentation)
2. EnergyPlus™ Version 23.1.0. *Engineering Reference*. U.S. Department of Energy. Section "Meters and Fuel Types" and "Zone Multiplier". URL: [https://energyplus.net/documentation](https://energyplus.net/documentation)
3. ASHRAE. (2020). *ANSI/ASHRAE Standard 55-2020 — Thermal Environmental Conditions for Human Occupancy*. American Society of Heating, Refrigerating and Air-Conditioning Engineers. Atlanta, GA.
4. ASHRAE. (2019). *ANSI/ASHRAE/IES Standard 90.1-2019 — Energy Standard for Buildings Except Low-Rise Residential Buildings*. American Society of Heating, Refrigerating and Air-Conditioning Engineers. Atlanta, GA.
5. OpenUBEM. (2026). *Step-5 Module 13: SQL extraction, zone resolution, EUI, and IOD (DESIGN §3A-§3D)*. Code reference: `openubem/results/parser.py`.
