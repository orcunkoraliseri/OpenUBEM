# DECISIONS — parent open items ruled under delegation, 2026-08-23

- **Date**: 2026-08-23 (evening)
- **Authority**: user instruction *"pourquoi, vas-y résoudre maintenant"* in reply to the list of open parent decisions; rulings below are taken **under that delegation** and are reversible by a one-line user reply (`D-EU-nn: overruled → <new rule>`).
- **Scope**: every item in MVP Table 19 (parent `archetype_parameter_provenance.md` §6 items 1, 3, 4; §7 licence; §11.4 weather acquisition; Step 7 decision 14) plus the items the director prompt §6 lists as "decisions that still require evidence" that can be settled from artefacts already on disk.
- **Evidence base**: `tabula-calculator.xlsx` (`Calc.Set.Building`, 333 columns, cached values) read on 2026-08-23 with `openpyxl` for exactly the 102 archetype rows of `outputs_step8/archetype_parameters_{es,uk,it}.csv`. The extracted columns are filed next to this record as [`tabula_102_extra_columns_2026-08-23.csv`](tabula_102_extra_columns_2026-08-23.csv) (102 rows, 24 columns). Every number below comes from that extraction or from a tier-1 parent document; none is a simulation result.
- **Deciding principle used throughout**: *when TABULA does not specify something, choose the EnergyPlus representation that reproduces TABULA's own monthly balance most literally, declare it, and make it a one-line sensitivity later.* This keeps the `f=0` control comparable to the TABULA band (G8.7) and keeps every non-geometric assumption identical across folds.
- **Format** (director prompt §5): old rule → ruled rule → evidence → expected effect → approval status.

---

## Summary

| ID | Item | Status | Closing work package |
|---|---|---|---|
| D-EU-01 | Geometry box: floor plate, storeys, facade areas, orientation, window-to-face mapping, dwellings per archetype | **RULED** (from TABULA areas + `n_Apartment`) | EU-04 |
| D-EU-02 | Layer build-up and thermal mass (`c_m = 45`), thermal-bridging surcharge, `b`-factors / ground coupling | **RULED** | EU-03 |
| D-EU-03 | Air change: use rate + per-archetype infiltration; window opening | **RULED** (corrects the v1.3 text "0.4 for every cell") | EU-05 |
| D-EU-04 | Which archetype represents a cell (GB parallel rows, IT composite codes, empty cells); non-integer `n_Apartment` | **RULED** | EU-01 / EU-02 |
| D-EU-05 | Weather: twelve-month rule, source, station | **CLOSED 2026-08-23 (DR08)** — ERA5/C3S source, Madrid/London/Bologna stations confirmed; file acquisition = slice X-07 | EU-07 |
| D-EU-06 | EUI accounting mode (MVP §9.10) | **RULED**: four-end-use mode with TABULA `q_w_nd` | EU-10 |
| D-EU-07 | Gain object, radiant/latent fractions, cooling, `F_red_temp` realisation | **RULED** | EU-05 / EU-06 |
| D-EU-08 | TABULA licence / redistribution | **CLOSED 2026-08-23 (DR09 A, clause re-verified live)** — publication permitted with mandatory attribution; X-02 files the verbatim text | EU-01 |
| D-EU-09 | Chaining rule (Step 7 decision 14) | **NOT RULABLE HERE** — upstream experiment; the arc's only remaining block, `f>0` cells only | blocks EU-06 `f>0` only |
| D-EU-10 | Neighbourhood density rule and EPC/cadastre sources for N1/N2 | **CLOSED 2026-08-23 (DR10)** — datasets + crosswalks + candidate lists pinned; FR city = Lyon; final unit by own counts under NS-05 | EU-02 / EU-08 |
| D-EU-11 | France physical registry source and count | **CLOSED 2026-08-23 (DR09 B)** — 40 `FR.N` rows adopted, 10 `FR.OPHM` excluded; executor re-derives from the pinned workbook in X-08 | EU-01 (FR) |

Deep-research briefs for the OWED items are in [`../../DeepResearch/`](../../DeepResearch/README.md) (DR08–DR11), written in the format of the parent's `IMP_step8/DeepResearch/` dossier.

---

## D-EU-01 — Geometry box

**Old rule.** Parent §6.1: *"Calc.Set.Building gives envelope AREAS and a conditioned volume — enough for a box model, not a 3D geometry. Footprint aspect ratio, orientation of the box, and how A_Window_East/South/West/North map onto its faces are ours to assume and to declare."* MVP §9.3 adds that dwelling allocation per archetype is undecided.

**Ruled rule.**

1. **Conserve TABULA's envelope areas exactly.** The box is built *from* the areas, not the areas from the box: `A_Roof_1+2`, `A_Wall_1+2+3`, `A_Floor_1+2`, `A_Window_{Horizontal,East,South,West,North}`, `A_Door_1` are reproduced to within 0.5 % in the saved IDF. TABULA's transmission balance is defined by those areas; any box that does not reproduce them stops computing TABULA's quantity.
2. **Floor plate and storey height from the table.** `A_plate = A_C_Ref / n_Storey`; `h_storey = V_C / A_C_Ref` (cross-check against `h_room`; `h_Ceiling` is 0 on all 102 rows and is ignored).
3. **Exposed perimeter from the wall areas.** `P_exp = (A_Wall_1 + A_Wall_2 + A_Wall_3) / (n_Storey_effective_envelope × h_storey)` — using the envelope storey count column where it differs from `n_Storey`. If `P_exp ≥ 4·√A_plate`, the plate is the rectangle with area `A_plate` and perimeter `P_exp` (two real roots → length and width). If `P_exp < 4·√A_plate` (attached TH/MFH rows whose party walls are not in `A_Wall`), the plate is the square of side `√A_plate`, the exposed length `P_exp` is distributed over the four faces in proportion to the window areas of that orientation (faces with zero window area and zero remaining perimeter become **adiabatic party walls**), and the reason token `ATTACHED_PARTY_WALL` is recorded.
4. **Orientation is taken from TABULA, not assumed.** The box faces are literally N/E/S/W; `A_Window_<dir>` goes on the face of that orientation; `A_Window_Horizontal` goes on the roof. No rotation parameter exists. (Rationale: the parent's open item was "how the oriented window areas map onto faces" — mapping them to their own orientation is the only choice that does not add information.)
5. **One window per face per storey**, area `A_Window_<dir> / n_Storey`, centred, sill at 0.9 m, height capped at `h_storey − 1.1 m` (width absorbs the rest). The window-to-wall ratio is therefore **derived**, never an input.
6. **Dwellings per archetype = `n_Apartment`** (column present in `Calc.Set.Building`; values read 2026-08-23: `SFH` = 1 on all 30 rows, `TH` = 1 on all 25, `MFH` 5–20, `AB` 6.6–78). The §4 slicing engine receives `n_Apartment` and `n_Storey` and applies the §4.5 remainder rule; `units_per_floor = ceil(n_Apartment / n_Storey)`. Non-integer counts → D-EU-04 item 3.
7. **Circulation core** only where `n_Apartment / n_Storey ≥ 2` (MFH/AB): §4.3 rules apply, area taken from the §4.3 band at its **lower** bound (6 % of the plate) because TABULA's `A_C_Ref` is a *conditioned* reference area and the core is not in it — the core is added **outside** `A_C_Ref`, so conditioned area and all per-m² quantities stay TABULA's. SFH/TH: no core.

**Evidence.** `tabula_102_extra_columns_2026-08-23.csv` columns `n_Apartment`, `A_C_Ref`, `V_C`, `n_Storey`, `h_room`; parent §6.1; MVP §4 and §9.8.

**Expected effect.** Transmission and ventilation coefficients (`h_Transmission` 0.57–9.77 W/(m²·K), `h_Ventilation` 0.38–0.68 — both in the CSV) are reproducible per archetype and become **GEO/EU-03 read-back assertions**: the saved IDF's Σ U·A / A_C_Ref must equal `h_Transmission` within 2 % after the D-EU-02 surcharge and `b`-factors. This is a much stronger acceptance test than area conservation alone.

**Approval.** Ruled under delegation 2026-08-23. Sensitivity owed later: aspect-ratio ±30 % on one archetype per type (diagnostic only).

---

## D-EU-02 — Layer build-up, thermal mass, thermal bridging, ground coupling

**Old rule.** Parent §6.3: *"TABULA gives U-values, not layers. Thermal mass enters as c_m (45 Wh/m²K on the EU set); reproducing that with real layers is an inverse problem with many answers."* MVP §2.3.1 proposes brick–EPS–plaster sizing; §2.3.2 proposes `InternalMass` with country-specific `c_m`.

**Ruled rule.**

1. **Envelope U-values are realised exactly with the existing CTF-safe path** — `build_opaque_assembly(idf, name, u_value, thermal_mass=False)` (MVP §9.2 row 5): a `Material:NoMass` layer sized to the target U. The brick–EPS–plaster build-up of §2.3.1 is **not adopted** for the campaign; it is retained as a documented future sensitivity because it adds undeclared capacitance and its EPS thickness is the inverse problem the parent warns about.
2. **All thermal mass is explicit and equals TABULA's `c_m`.** One `InternalMass` object per dwelling zone with surface area `A_mass = A_zone` and a single material whose `ρ · c_p · d = 45 Wh/(m²·K) = 162 000 J/(m²·K)` (e.g. `d = 0.10 m`, `ρ = 1800 kg/m³`, `c_p = 900 J/(kg·K)`; `λ = 1.0 W/(m·K)`). Because the envelope is mass-less, the **zone's total capacity is exactly `c_m × A_zone`** and is verifiable from the saved IDF by arithmetic. This is the TABULA single-capacity conception realised literally. `c_m = 45` for all 102 rows (read from `Calc.Set.Building`, column `c_m`; identical to `Tab.BoundaryCond` EU rows). The country-specific values of MVP §2.3.2 are not used (ruling Q5-A left the text standing; this ruling fixes the campaign value).
3. **Thermal-bridging surcharge.** `delta_U_ThermalBridging` (column definition: *"additional losses of the thermal envelope caused by thermal bridging (supplement to all U-values)"*; values 0 / 0.05 / 0.10 / 0.15 W/(m²·K) across the 102 rows) is **added to every envelope U-value, opaque and window alike**, before the NoMass sizing. Recorded per archetype in the provenance file.
4. **`b`-factors are realised as boundary conditions, not as U-value edits.** `b_Transmission_*` per element (values read: roof 1 on all rows; wall 0.5 on 8 rows; floor 0.5 on 51 rows, 1 on 51 rows). `b = 1` → `Outdoors` (floors with `b = 1` use `SurfaceProperty:OtherSideCoefficients` with external dry-bulb coefficient 1.0 and no sun/wind, so no solar lands on a floor). `b = 0.5` → `SurfaceProperty:OtherSideCoefficients` with `Zone Air Temperature Coefficient = 0.5` and `External Dry-Bulb Temperature Coefficient = 0.5`, which gives `U·A·(T_i − T_other) = 0.5·U·A·(T_i − T_e)` exactly. No `GroundDomain`, no `Ground:FCfactorMethod` (the Ankara pipeline's abandonment of `GroundDomain:Slab` for stability — walkthrough §4.3 — is noted; the coefficient approach avoids the question). Read-back assertion: every surface's boundary condition and coefficients match the archetype's `b`.
5. **Windows.** `WindowMaterial:SimpleGlazingSystem` with `U = U_Window_1 + delta_U_ThermalBridging`, `SHGC = g_gl_n_Window_1` (values 0.67 / 0.72 / 0.75 / 0.76 / 0.85 across the 102 rows; `g_gl_n_Window_2 = 0` everywhere, so only one window type exists per archetype). The MVP Table 14 row that said `g_gl` was absent is corrected: it is in `Calc.Set.Building`, not in the 44 carried columns.

**Evidence.** CSV columns `c_m` (not carried in the CSV but read = 45 on all rows during extraction), `delta_U_ThermalBridging`, `b_Transmission_*`, `g_gl_n_Window_1/2`; MVP §9.2 row 5 (CTF cap); EnergyPlus `SurfaceProperty:OtherSideCoefficients` field semantics (to be asserted by a one-surface fixture in EU-03 before use — **the fixture, not this record, verifies the coefficient arithmetic**).

**Expected effect.** `Σ(U_i + ΔU)·A_i·b_i / A_C_Ref` from the saved IDF reproduces TABULA's `h_Transmission` (median 2.62 W/(m²·K)) → EU-03 acceptance assertion within 2 %. Dynamics come from a single declared capacity; every fold shares it.

**Approval.** Ruled under delegation 2026-08-23. Sensitivity owed later: envelope-embedded mass vs internal mass on one MFH archetype (diagnostic).

---

## D-EU-03 — Air change and window opening (corrects the v1.3 wording)

**Old rule.** MVP §11.2 (v1.3, this morning): *"`n_air_use = 0.4 h⁻¹` for every cell."* Walkthrough §5.4 (v1.0): per-country 0.40 / 0.59 / 0.30.

**Ruled rule.** Total air change per archetype is **`n_air_use + n_air_infiltration`**: `n_air_use = 0.4` on all 102 rows (EU boundary condition) **plus** the per-row `n_air_infiltration` ∈ {0.05 (2 rows), 0.1 (37), 0.2 (29), 0.4 (34)}. Check: TABULA's `h_Ventilation = 0.34 · (n_air_use + n_air_infiltration) · V_C / A_C_Ref`; with `h_room = 2.5` the CSV's minimum 0.3825 = 0.34·0.45·2.5 and maximum 0.68 = 0.34·0.8·2.5 reproduce exactly. Realised as one constant `ZoneInfiltration:DesignFlowRate` (AirChanges/Hour = `n_air_use + n_air_infiltration`) per dwelling zone, constant schedule, no wind/temperature coefficients (TABULA has none). No window opening (TABULA carries none — provenance §3). The circulation core (D-EU-01 item 7) keeps MVP §4.3's separate infiltration rule. The national rates remain a declared sensitivity only.

**Evidence.** CSV columns `n_air_use`, `n_air_infiltration`, `h_Ventilation`, `h_room`.

**Expected effect.** Ventilation losses match TABULA per archetype; the v1.3 inline notes in MVP §2.2.2/§5.3 and walkthrough §5.4 are completed by an additive correction pointing here.

**Approval.** Ruled under delegation 2026-08-23.

---

## D-EU-04 — Archetype selection, composite codes, empty cells, non-integer dwelling counts

**Old rule.** Parent §6.4: *"Which archetype represents a uk/it cell where two parameterisations exist … and what to do with the 3 empty GB cells and 6 empty IT cells."* Not taken.

**Ruled rule.**

1. **The archetype campaign runs all 102 rows.** No selection is needed for the 510-cell matrix; a row is a cell. GB parallel rows (`.Gen` and `.Detached`) and IT composite rows are all simulated; the dossier reports them by row code, never collapsed into a type × period grid that would hide the duplication.
2. **Observed-building mapping (S1–S3, N1/N2)** is deterministic: key = (`country_stock_code`, `building_type`, `tabula_period(year_built)`). Candidate rows are those whose `Code_BuildingSizeClass` equals the type (or whose composite type contains it — `MFH-AB` matches `MFH` and `AB`; `SFH-TH` matches `SFH` and `TH`) **and** whose period code equals the band (or whose composite/merged period contains it — `.01-03` contains `.02`; `SFH.04-08` contains `GB.06`). If exactly one candidate → match. If several → prefer the row with **no** composite in either axis; among GB `.Gen`/`.Detached` pairs prefer `.Gen` unless an observed attachment attribute is present (OSM `building=detached` → `.Detached`; `terrace`/`semidetached_house` → `.Gen`). If still several → `ARCHETYPE_AMBIGUOUS` error, building excluded with reason; never a silent first match. If none (the 3 GB / 6 IT empty cells) → nearest band of the same type, older band preferred on a tie, provenance token `ARCHETYPE_NEAREST_PERIOD`, and the count of such buildings is reported in every audit panel.
3. **Non-integer `n_Apartment`** (three GB `AB` rows: 6.57, 13.64, 17.21 — synthetic-average rows, suffix `SyAv`) → `round()` to nearest integer (7, 14, 17); the unrounded value is kept in the provenance file; per-dwelling areas use the rounded count.

**Evidence.** Parent §5 and §6.4; CSV column `n_Apartment`; MVP §11.5.

**Expected effect.** The 510 count is unchanged; the observed-building pipeline cannot silently pick a row; the empty-cell fallback is visible.

**Approval.** Ruled under delegation 2026-08-23.

---

## D-EU-05 — Weather: rules ruled, files owed

**Old rule.** Parent §11.4: three items owed (calendars → 12 months; licensed AMY source; station). Windows ruled: `es` 2009–2010, `uk` 2014–2015, `it` 2013–2014.

**Ruled rule.**

1. **Twelve-month rule adopted as proposed by the parent**: the twelve consecutive calendar months containing the most diaries in that fold, measured from the Step 7 corpus's own diary dates; ties broken toward the earlier start. The rule is applied by a script over the corpus and its output (start month, end month, diary count in window, diary count outside) is the first row of `weather_registry.json`. Until the corpus dates are read, the window is recorded as the two calendar years above with `status: "RULED_NOT_PINNED"`.
2. **Source**: an ERA5-derived actual-meteorological-year EPW is the **primary candidate** (Copernicus C3S licence terms to be copied verbatim into the registry — DR08 item A); a measured-station AMY (national met service) is the secondary candidate where its licence permits publication. TMYx/TMY files are excluded by the ruling except as `SMOKE_TMY`.
3. **Station/location**: one per fold, chosen as the most populous city inside the TABULA climate region that the fold's diaries cover — working defaults **Madrid (`ES.ME`), London (`GB.ENG`), Bologna (`IT.MidClim`)** from the tier-3 document, each to be confirmed or replaced by DR08 item B using the corpus's regional distribution; the decision token is written into the registry.

**Evidence.** Parent §11; MVP §11.6; DR08 brief.

**Expected effect.** EU-07 can write the registry schema and the window script now; no weather-driven number is quoted until DR08 returns and the files are on disk with checksums.

**Approval.** Rules ruled under delegation 2026-08-23; acquisition OWED.

---

## D-EU-06 — EUI accounting mode

**Old rule.** MVP §9.10: the campaign owner must choose physical mode or four-end-use mode before EU-10.

**Ruled rule.** **Four-end-use mode.** The simulation emits space heating (IdealLoads, D-EU-07), lighting and equipment only as the combined `phi_int` gain path (no separate DOE lighting/equipment objects), and **no physical DHW, cooking, refrigeration or elevator objects** (Phase E service loads are switched off by configuration for every European cell; MVP §9.2 row 9). The reported whole-dwelling figure adds **TABULA's own `q_w_nd`** (net DHW energy need, kWh/(m²·a), per archetype row — values 10–15 in the ES rows read) as a post-processed, separately labelled column, divided by the same `A_C_Ref` denominator. No US coefficient table is used. Reason: Phase E's service loads are US-calibrated and unvalidated for Europe; TABULA supplies the DHW need directly; the occupant effect under test lives entirely in the simulated gains. The manifest records `eui_accounting_mode = "four_end_use_tabula_dhw"`, modeled end uses, the `q_w_nd` value and its row code.

**Evidence.** MVP §9.2 rows 9–10, §9.10; CSV column `q_w_nd` (carried in the parent tables).

**Expected effect.** No double counting is possible by construction; G8.10's tripwire reconciles heating + gains against the facility meters only.

**Approval.** Ruled under delegation 2026-08-23.

---

## D-EU-07 — Gain object, fractions, cooling, heating intermittency realisation

**Old rule.** Director prompt §6: gain-object radiant/latent/lost fractions undecided; cooling set-point 26 °C appears in old text; `F_red_htr` "preserved as a scalar" without an EnergyPlus realisation.

**Ruled rule.**

1. **Gain object**: one `OtherEquipment` per dwelling zone (fuel-neutral → no meter contamination), `Design Level = 3.0 W/m² × A_zone`, schedule = dimensionless `phi_int(t)/3.0` via `Schedule:File` with a non-fractional `ScheduleTypeLimits` (walkthrough §9.8). **Fractions: latent 0, radiant 0, lost 0** — i.e. EnergyPlus's defaults, all-convective. Rationale: TABULA's `phi_int` is a direct gain to the single zone node with no split; any split is information TABULA does not carry. Declared assumption; a 0.5-radiant sensitivity is owed later on one archetype.
2. **No cooling.** TABULA has no cooling term and the EU boundary conditions carry only `theta_i = 20`. Cells run heating-only IdealLoads with no cooling set-point; summer is free-floating, and overheating is reported as an *indicator* (IOD; TM59 criteria informational for GB) from zone operative temperatures. The 26 °C set-point in MVP §2.1/§5.2 text is not used.
3. **Heating set-point** 20 °C constant (EU `theta_i`), no schedule.
4. **`F_red_temp` realisation.** TABULA applies a per-archetype temperature-reduction factor `F_red_temp` (interpolated between `F_red_htr1` at `h_tr = 1` and `F_red_htr4` at `h_tr = 4`; values read 0.80–0.993, median 0.870) to the whole heat-transfer term. Realised in EnergyPlus as a **multiplier on every envelope U-value (after the ΔU surcharge) and on the air-change rate** of the archetype — the only realisation that is a scalar on the transfer coefficients and adds no schedule. The per-archetype factor is recorded in the provenance file and a `F_red_temp = 1` sensitivity is owed on one archetype per type.

**Evidence.** CSV columns `F_red_temp`, `h_Transmission`; parent `FINDING 57` and provenance §9.5; MVP §9.9.

**Expected effect.** Control cells compute TABULA's quantity as literally as a dynamic engine can; the only campaign-varying object is the gain schedule.

**Approval.** Ruled under delegation 2026-08-23.

---

## D-EU-08 — TABULA licence (process)

**Ruled rule.** Internal use proceeds now (parent §7 allows it). **Publication of any derived table is blocked** until the licence text is copied verbatim, with URL and retrieval date, into `openubem/data/construction/TABULA_PROVENANCE.md` — DR09 item A. A licence is never inferred from the absence of a paywall. Slice X-02 writes the placeholder with `status: "UNVERIFIED"`.

## D-EU-09 — Chaining rule (Step 7 decision 14)

**Not rulable in this arc.** It is a Step 7 experiment (chaining-rule sensitivity on peak demand, 25 % threshold). Status stays **BLOCKED for every `f>0` cell**; Q1–Q3 and FR-B proceed. No deep-research brief is written for it because it is an experiment on the project's own corpus, not a literature question.

## D-EU-10 — Neighbourhood density rule and data sources

**Ruled rule (shape).** For each study city the density metric is **residential buildings per km² of the candidate boundary after the residential filter**, with a dwelling proxy (`building:levels × footprint area`) as tie-breaker; candidates are administrative sub-units available as open boundaries (Madrid *barrios*, London *wards*/LSOAs, Bologna *quartieri/zone*, FR *IRIS*), ranked before any energy result exists; the selected unit must pass `NS-05` (500–600 residential buildings). Which open EPC/cadastre datasets feed panels (a)–(d) is **owed → DR10**.

## D-EU-11 — France physical registry

**Owed → DR09 Part B.** No count is asserted; the TABULA France subset, construction-period crosswalk and RE2020/DPE field sources must be pinned before `tabula_archetypes_fr.json` exists.

---

## What this record changes in the arc documents

- MVP §11 gains §11.12 (rulings table + additive correction of §11.2 on air change and of Table 14 on `g_gl`).
- Walkthrough §12.4 slice X-02 gains the extra-column extraction from `Calc.Set.Building` (`n_Apartment`, `n_air_infiltration`, `g_gl_n_Window_1`, `b_Transmission_*`, `delta_U_ThermalBridging`, `F_red_temp`, `h_Transmission`, `h_Ventilation`, `n_Storey_effective_envelope`, `q_w_nd`).
- Director prompt §6 items are re-labelled RULED / OWED with pointers here; head box updated.
- `DeepResearch/README.md` + DR08–DR11 briefs created.

---

# CLOSURE ADDENDUM — DR08–DR11 returned and accepted, 2026-08-23

- **Authority**: user instruction *"oui ils sont prets … fermer toutes des blockage ou decisions ouverts"* (2026-08-23). Reports saved unchanged next to their briefs; acceptance verdicts and caveats in [`../../DeepResearch/README.md`](../../DeepResearch/README.md) §Acceptance Record.
- **Director verification performed**: `episcope.eu/communication/download/` fetched live — the DR09 licence clause matches verbatim; the DR08 Copernicus licence PDF URL is stale (404) but the current CDS ERA5 page states plain **CC-BY**, so the verdict stands with the executor instructed to file the licence text served at download time.

## D-EU-05 — CLOSED (weather source, station, validation gates)

1. **Source (item 2)**: **ERA5 (Copernicus C3S)**, converted to EPW via the `cdsapi` → `pvlib` route with Perez/DISC solar decomposition (DR08 §4.1). Licence publication-compatible **and redistributable** with attribution *"Contains modified Copernicus Climate Change Service information [Year]"* (currently CC-BY). National station data (AEMET / MIDAS Open OGL v3 / ARPAE IODL-CC-BY) serve as GATE-5 monthly benchmarks only. Commercial AMY (Meteonorm, White Box) rejected: derived results publishable but converted-EPW redistribution forbidden.
2. **Stations (item 3), confirmed from the working defaults**: **Madrid** (Barajas/Retiro, WMO 08221), **London** (Heathrow, WMO 03772), **Bologna** (Borgo Panigale/Marconi, WMO 16140). Rome explicitly rejected for `it` — climatic Zone D (1,415 GG) belongs to `IT.MedClim`, not `IT.MidClim` Zone E; Bologna is the TABULA-Italy brochure's own reference station (DR08 §5.2).
3. **Six-gate EPW validation checklist** (DR08 §6: header, 8,760 rows, zero missing, physical/thermodynamic bounds incl. solar closure ≤5 W/m², monthly benchmark |ΔT|≤1.5 K / |ΔGHI|≤10 %, one-zone E+ smoke test rc 0) is **adopted into EU-07** as the acceptance gate before any file enters `weather_registry.json`.
4. **Still execution, not decision**: download + convert + validate (slice X-07); 12-month window pinning by the ruled diary-count script (window stays `RULED_NOT_PINNED` until the corpus dates are read). Timezone rule: LST no DST, UTC+0 uk / UTC+1 es,it; all five window years are non-leap.

## D-EU-08 — CLOSED (licence text obtained and re-verified)

**Publication of derived parameter tables, JSON registries and generated IDFs is PERMITTED** under the EPISCOPE third-party terms, condition: *"'IEE Projects TABULA + EPISCOPE (www.episcope.eu)' is visibly mentioned as the source"* — clause re-verified live by the director 2026-08-23. Consequences: (i) X-02 writes `openubem/data/construction/TABULA_PROVENANCE.md` with the verbatim clause, URL, retrieval date and the DR09 §4 citation forms, and the registry licence field becomes `status: "VERIFIED"` instead of `"UNVERIFIED"`; (ii) every generated IDF and exported table carries the two-line attribution header (DR09 §9); (iii) original-workbook redistribution is avoided in favour of a pinned-fetch script with MD5 checks (conservative option, DR09 §3 row iii). The publication block of the earlier process ruling is **lifted** once (i) exists on disk.

## D-EU-10 — CLOSED (datasets, crosswalks, candidates; fourth city = Lyon)

1. **Fourth study city: Lyon** (over Paris/Nantes/Grenoble) — open-data completeness (Data Grand Lyon LOD2 + PCI, 100 % BDNB indexation) and clean dense contiguous fabrics (DR10 §1.2).
2. **Primary datasets per attribute per city** (DR10 §1.1 / §2, all with derived-publication-permitted licence verdicts): Madrid — DGC Catastro INSPIRE `BU` (+ Comunidad de Madrid CEE registry, join on `referencia_catastral`); London — MHCLG EPC open data + OS Open UPRN (OGL v3; PAF address strings never republished); Bologna — Comune DBT Edifici (+ SACE/APE, ISTAT tract material shares); Lyon — CSTB BDNB Open (+ ADEME DPE v2, IGN BD TOPO `cleabs`).
3. **Period crosswalks adopted**: ES exact-year → `ES.01–06` clean 1:1; FR exact-year → `FR.01–10` clean 1:1; IT clean with exact year (ISTAT `E1`/`E5` straddles handled at tract level); **GB is the hard case** — 6 of 12 EPC `CONSTRUCTION_AGE_BAND` bands straddle TABULA thresholds; the DR10 §4.2B deterministic majority-duration assignment is adopted **with a `PERIOD_STRADDLE_*` provenance token on every straddled building**, counted in the audit panels.
4. **Typology crosswalk adopted** (DR10 §4.1) incl. the two one-to-many rules (Madrid missing dwelling count; London single-flat-certificate footprints).
5. **Candidate lists recorded, selection NOT taken**: Madrid Trafalgar/Gaztambide/Arapiles (Chamberí); London Earl's Court + Camden 2-LSOA cluster; Bologna Bolognina-Casaralta / Marconi-Lame / Galvani 2; Lyon Croix-Rousse Centre / Guillotière Sud. All counts are published-statistics estimates; the final unit is chosen by the project's own computed counts under the pre-registered metric (`NS-03`) and `NS-05` — unchanged from the shape ruling.
6. **Open boundary sources** (DR10 §6) pinned with CRS + licence per city; store under `openubem/data/boundaries/` with SHA-256.

## D-EU-11 — CLOSED (France registry)

**`tabula_archetypes_fr.json` = exactly the 40 national rows `FR.N.<AB|MFH|SFH|TH>.<01..10>.Gen.ReEx.001.001`** (4 sizes × 10 period bands, pre-1915 → post-2013), boundary conditions `EU.SUH` (SFH/TH) / `EU.MUH` (MFH/AB) — same EU set as the 102, so every ruling D-EU-01…07 applies unchanged. **The 10 `FR.OPHM` Montreuil pilot rows are excluded** (unset size/period metadata, non-standard `LC_*` classes, hardcoded `FR.MUH-DPE1` boundary pointer). Anomaly parsed literally per D-EU-01, no override: `FR.N.MFH.08` has `n_Apartment = 1`, `n_Storey = 1` at 497.2 m². `FR.07` end-year 1999 carries an IWU admin patch note; the `FR.48/74/99/00` macro rows belong to the excluded OPHM study. Executor re-derives all counts from the pinned workbook in slice X-08 (DR09 is the map, the workbook the authority); DPE/RT crosswalk of DR09 §7 informs the FR audit panel bands.

## D-EU-01 / 02 / 03 / 07 — VALIDATED by DR11 (no ruling overturned)

Verdicts: **Standard** — R1 geometry box, R2 zoning+core, R5 `b`-factors, R6 constant air change, R9 no cooling, R10 simple glazing. **Acceptable with caveat** — R3 mass-less envelope (+8–18 % diurnal peak, <3 % annual; no phase lag), R4 ΔU on windows (<3 % of transmission shifted to glazing), R7 `F_red` multiplier (damps morning warm-up 10–25 %; the only realisation that does not confound the occupancy signal — clause-level answer under EN ISO 13790 §13.2 delivered), R8 all-convective gain (air swings +0.5–1.5 °C). The four caveats are **declared limitations for the dossier text**, not changes to the rulings.

**Adopted into the slices**: (i) the three DR11 §4 numeric fixtures join X-04 — R3 time-constant box (τ = C_m/H = 14.0625 h; free-fall to 20/e = 7.3576 °C ± 0.05), R5 one-surface flux (q = 20.000 W ± 0.001; T_other = 10.000 °C ± 0.001), R7 two-zone scaling (Φ_B/Φ_A = 0.8500 ± 0.0001); (ii) the whole-building read-backs (areas 0.5 %, `h_Transmission` 2 %, `h_Ventilation` 1 %) were already MVP §11.12 assertions — DR11 §4.1 confirms them. **Sensitivities owed later (diagnostic, one archetype each)**: layered-CTF vs NoMass; 50 % radiant split; `F_red_temp = 1`.

## Remaining block

**D-EU-09 only** (Step 7 chaining rule, upstream experiment) — blocks `f>0` cells and Q4. Everything the arc itself can decide is decided; X-01…X-08 are pure execution.

**Direction issued 2026-08-23 (user instruction):** a protocol proposal for the chaining experiment (candidate rules C1–C3, 20–50-dwelling sample per fold at `f = 1.00`, pre-registered 25 %-peak / 10 %-annual decision criterion, inherited G8/FINDING-57 constraints) was appended to the parent implementation spec as **§10** of `C:\Users\o_iseri\Desktop\GSSCanada\GSSCanada-main\4J_docs_occ\Step8_docs\IMP_step8\4thJ_08_bemSimulation_IMP.md`. The block lifts when the Step 7 side files the frozen rule, seed policy, script and spread table back to this arc.
