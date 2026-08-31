# `s3_campaign_manifest.csv` — energy basis and denominators

**Written 2026-08-27.** Additive. `s3_campaign_manifest.csv` is a **promoted** artefact under
`D-EU-24` and is **not edited** — no column was renamed, no row changed, no value restated. This
file is the label the column itself cannot carry.

## 1. `eui_kwh_m2` is HEATING-ONLY

| column | what it actually is |
|---|---|
| `heating_kwh` | annual sum of the hourly `Zone Ideal Loads Zone Total Heating Energy` `Output:Variable`, extracted at `scripts/run_eu_s2_campaign.py:285` |
| `floor_area_m2` | conditioned floor area of the emitted zones |
| `eui_kwh_m2` | `heating_kwh / floor_area_m2` — **a heating-only intensity, NOT a whole-building EUI** |

It contains **no lighting, no appliance electricity, no DHW, no cooling**. No `Output:Meter` object
exists in any saved IDF, so no fuel or end-use total was available to this manifest — the whole-
building total below was recovered by an **off-path sidecar**, never by the promoted campaign.

🔴 **Every figure below must be quoted with the words "heating-only".**

| figure | value |
|---|---|
| pooled over the 95 accepted | **66.86769 kWh/m²** over 113,768.5830 m² |
| min / median / max | 29.566258 · 80.323298 · 222.294548 |
| `FR` / `ES` | 55.4141 · 87.2000 |

Read as a whole-building EUI — against TABULA, against a measured national figure, or into an `N1`
projection — a heating-only number is wrong by a large factor **in the direction that looks
plausible**. That is why this is a factor-level error and not a wording one.

🔴 **MEASURED 2026-08-27 by the `EU-05` meter sidecar** (95 off-path re-runs, promoted hashes
unchanged, hourly heating series identical at `max_abs_diff = 0`):

| quantity | pooled over the same 113,768.5830 m² |
|---|---|
| heating-only (the promoted `eui_kwh_m2`) | **66.868 kWh/m²** |
| **two-end-use model total** (NOT a whole-building EUI) | **93.768 kWh/m²** |
| ratio total / heating | **1.4023** |

🔴 **`93.768` is a TWO-END-USE MODEL TOTAL and may never be printed without that qualifier.**
Object census of a promoted IDF (re-derived independently on the 4J side 2026-08-27): `People` **0**,
`Lights` **0**, `ElectricEquipment` **0**, `WaterUse*` **0**, cooling coils **0**; present are
`OtherEquipment`, `Schedule:File` and `HVACTemplate:Zone:IdealLoadsAirSystem` only. **No TABULA
comparison, no measured-national-EUI comparison and no `N1` projection is reachable at this rung,
sidecar or not** — `93.768` is not the fixed version of `66.868`, it is the same factor-level trap
one rung along.

The gap is **entirely** `InteriorEquipment:Electricity` — heating + equipment reproduces the site
total to 0.02 kWh over 10.67 GWh, with **no** lighting, DHW or cooling term in the model at all.

⚪ The models are not energy-empty. Every zone carries an `OtherEquipment` gain declared
**`Fuel Type = Electricity`**, `Watts/Area` with a multiplier of `1`, driven by a `Schedule:File`
whose type limits are `AnyNumber_Wm2` — so the CSV **is** the gain in W/m². At `f = 0` all **381**
gain CSVs are **flat at 3.0 W/m²**: the electricity term is a constant 3 W/m² baseline
(≈ 26.3 kWh/m²·yr) and carries **zero occupancy signal**. `NominalPeople`, `NominalLighting` and
`NominalElectricEquipment` are all **0** in every run's `eplusout.sql`.

🔴 Do not read the `1` in the `OtherEquipment` object as "1 W/m²" — it is a multiplier on the
schedule, and the delivered level is 3 W/m².

⚪ `TabularData` is **empty** in every promoted run: `Output:SQLite` was written as
`SimpleAndTabular`, but no `Output:Table:SummaryReports` was requested, so no
`AnnualBuildingUtilityPerformanceSummary` exists to read a whole-building total from.

## 2. Denominators — 95, 374 and 12 are three different populations

| population | N | what it is |
|---|---|---|
| accepted buildings | **95** | `eplus_return_code == 0`; 96th is the classified `EPLUS_FATAL` |
| zones | **374** | sum of `zone_count` over the 95 — **and exactly the 374 distinct schedule CSVs, one per zone** |
| buildings with dwelling geometry | **12** | `layout_mode == DWELLING_LAYOUT_EMITTED` (83 `FALLBACK_PENDING_LAYOUT`) |
| **dwelling** zones | **26** | zones inside those 12 buildings |
| massing zones | **348** | floors of one-zone-per-floor models, in the other 83 buildings |

🔴 **"374 dwellings" is false.** 374 is a zone count; only 26 of those zones are dwellings.

⚪ All five `EU-05` checks and all five `EU-06` checks are per-building or per-zone, so **95 is their
correct denominator** and none is restated. Any *per-dwelling* quantity downstream —
`G11.15`'s DHW-per-dwelling arm above all — has a population of **12 buildings / 26 dwellings**,
never 95 and never 374.

## 2b. Two clerical precisions (raised as note 3 by 4J, 2026-08-27, both verified here)

⚪ **The sidecar equivalence was compared PER-ZONE-HOUR, not per hour.** `rows_compared` in
`EU-05/meter_sidecar/meter_sidecar_manifest.csv` takes **eight distinct values, 8,760 … 70,080**
(= 8,760 h × `zone_count`), summing to the **374** zones. Any statement of “8,760 rows each”
understates the proof; the correct reading is stronger, not weaker.

🔴 **`381` is the all-96 zone total, not the accepted-95 one.** The accepted population is
**374** zones; the extra **7** belong to the fatal `BATIMENT0000000240879534_part0`. The `f = 0`
gain-CSV statement above is correctly over **381**, because those CSVs are *inputs* and exist for
all 96 — but `381` must never be quoted as an *accepted-campaign* population.

## 3. Provenance

Raised as challenges 2 and 3 of
`GSSCanada/GSSCanada-main/4J_docs_occ/messages_OpenUBEM/2026-08-27_4J_to_OpenUBEM_S3_EU-05-06_challenges.md`,
accepted on owner authorisation 2026-08-27. The two-end-use label and §2b were added
2026-08-27 on notes 2–3 of `…/messages_OpenUBEM/2026-08-27_4J_to_OpenUBEM_reply_S3_basis_population_closeout.md`,
re-derived here (`rows_compared` 8 distinct values, zone sum 374). Every number above was re-derived from
`s3_campaign_manifest.csv` and from the runs under `s3_campaign/` by the manager session; nothing
here is quoted from the challenge document.
