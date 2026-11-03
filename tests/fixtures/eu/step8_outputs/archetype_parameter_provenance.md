# `archetype_parameter_provenance.md` — Step 8, work item 8.1

### 4J HETUS LLM pipeline. Created 2026-08-21.
#### Implementation: `../4thJ_08_bemSimulation.md`. Builder: `../../tools/4thJ_step8_tabula.py`.

---

## STATUS

🟢 **The TABULA parameter tables are BUILT for all three folds** —
`archetype_parameters_es.csv` (24 archetypes), `archetype_parameters_uk.csv` (36),
`archetype_parameters_it.csv` (42).

🔴 **No IDF has been written.** Item 8.1 says *"Build the archetype IDFs … via OpenStudio or TEASER"*;
what exists is the parameter table those IDFs must be built from, with a source reference on every
value and — the part that actually protects the paper — **a measured account of what TABULA does not
give us**. The geometry, zoning and layer build-up decisions are named in §6 and are **not taken here**.

---

## 1. The two workbooks, and the split between them is the first finding

| file | bytes | md5 | sheets |
|---|---|---|---|
| `raw/tabula-values.xlsx` | 4,028,656 | `7347b2cae3c4d9f5ce78221e9d5fb832` | 65 |
| `raw/tabula-calculator.xlsx` | 34,383,251 | `c99ddc9ffcb6dc0ae7391273d9619e37` | 15 |

Retrieved 2026-08-21 from `https://episcope.eu/fileadmin/tabula/public/calc/<file>`. The values
workbook's digest **matches the one `RL24` verified on 2026-08-20 exactly**; the calculator's digest is
pinned here for the first time.

🔴 **`tabula-values.xlsx` CONTAINS NO BUILDING ARCHETYPES.** Every sheet was searched for a first column
matching a TABULA building-type code (`<CC>.<region>.<SFH|TH|MFH|AB>.…`) — **zero sheets carry one**.
The route recorded on 2026-08-20 (*"download `tabula-values.xlsx` … read `Tab.Building.Constr`"*)
reaches the CONSTRUCTIONS but not the BUILDINGS: `Tab.Building.Constr` holds wall/roof/ceiling
assemblies (`ES.Wall.ReEx.01.01`), not archetypes.

**Item 8.1 needs the 34 MB calculator, which the 2026-08-20 entry explicitly recorded as NOT opened.**
It is opened here. `RL24`'s claim B16 — that `Calc.Set.Building` is where the archetypes live — is
therefore **VERIFIED**: 3,287 data rows × 333 columns, one row per building variant.

---

## 2. 🟢 The 22 construction-year bands, re-derived and matching

Read from `Tab.ConstrYearClass`, columns `ConstructionYearClass_FirstYear` / `_LastYear`. **All 22
boundaries match the table recorded on 2026-08-20 exactly**, independently re-derived:

| Spain | Great Britain | Italy |
|---|---|---|
| `ES.01` 0-1900 | `GB.01` 0-1918 | `IT.01` 0-1900 |
| `ES.02` 1901-1936 | `GB.02` 1919-1944 | `IT.02` 1901-1920 |
| `ES.03` 1937-1959 | `GB.03` 1945-1964 | `IT.03` 1921-1945 |
| `ES.04` 1960-1979 | `GB.04` 1965-1980 | `IT.04` 1946-1960 |
| `ES.05` 1980-2006 | `GB.05` 1981-1990 | `IT.05` 1961-1975 |
| `ES.06` 2007-9999 | `GB.06` 1991-2003 | `IT.06` 1976-1990 |
| | `GB.07` 2004-2009 | `IT.07` 1991-2005 |
| | `GB.08` 2010-9999 | `IT.08` 2006-9999 |

⚪ **The descriptive labels exist for SPAIN ONLY**, and they live in `Remark_ConstructionYearClass`
(not `Description_…`, which is empty for all 22): `XIX century`, `Beginning of the century`,
`Civil war`, `Improvement in the Spanish economy`, **`CTE-79`**, `CTE 2006`. **GB and IT carry no
descriptive label at all**, so there is nothing to quote for them. `NBE-CT-79` appears nowhere in the
workbook; `CTE-79` is the file's own wording and is what this project cites.

---

## 3. 🔴 THE HONESTY CLAUSE — what TABULA does NOT give us, measured against the file

Item 8.1: *"Record what TABULA does not give us and what we assumed instead. An assumed value that is
not written down becomes a fact the moment someone reads the code."*

Every sheet header block of `tabula-values.xlsx` was searched for: `schedul`, `hourly`, `sub-hour`,
`tapping`, `window open`, `thermostat`, `set point`, `setpoint`, `zoning`, `zone`, `occupan`,
`appliance`, `plug`, `lighting`, `draw`, `3d`.

🔴 **NOT ONE of them appears anywhere in the workbook.** TABULA is a monthly steady-state
energy-balance method and has no concept of a time series. `RL24`'s B17 list is **CONFIRMED** for
sub-hourly occupant schedules, appliance draw profiles, DHW tapping series and 3D zoning geometry —
and **REFINED**, sharply, for the other two. See §4.

---

## 4. 🔴 THE ARCHETYPES DO NOT USE THE NATIONAL BOUNDARY CONDITIONS

`Tab.BoundaryCond` publishes national rows for our three countries **and** an EU
cross-country-comparison pair. **Every one of the 102 archetype rows kept here points at the EU pair**
— checked, not assumed: `Code_BoundaryCond` takes exactly two values across `es`, `uk` and `it`,
`EU.SUH` for `SFH`/`TH` and `EU.MUH` for `MFH`/`AB`, in all three folds. The builder **refuses to run**
if that stops being true.

| | unit | `EU.SUH` | `EU.MUH` | `ES.SUH` | `ES.MUH` | `GB.Gen` | `IT.SUH` | `IT.MUH` |
|---|---|---|---|---|---|---|---|---|
| `theta_i` | °C | **20** | **20** | 20 | 20 | 21 | 20 | 20 |
| `F_red_htr1` | — | **0.9** | **0.95** | 1 | 1 | 1 | 1 | 1 |
| `F_red_htr4` | — | **0.8** | **0.85** | 1 | 1 | 1 | 1 | 1 |
| `n_air_use` | 1/h | **0.4** | **0.4** | 0.4 | 0.4 | 0.59 | 0.3 | 0.3 |
| `h_room` | m | **2.5** | **2.5** | 2.5 | 2.5 | 2.4 | 3.0 | 2.7 |
| `phi_int` | W/m² | **3** | **3** | 3 | 3 | 4 | 2.8 | 4.1 |
| `c_m` | Wh/(m²K) | **45** | **45** | 45 | 45 | 32.79 | 87 | 72 |
| `q_w_nd` | kWh/(m²a) | **10** | **15** | 11.09 | 21.76 | 15.8 | 14.5 | 17.3 |

**Bold = what the emitted tables actually carry.** All sixteen bold values are asserted against the
file by the builder, so a republished workbook cannot silently make this table fiction.

### 4.1 🔴 `phi_int` is the injection point for the entire campaign

`phi_int` — *average internal heat sources per m² reference area* — is **3.0 W/m² in ALL THREE FOLDS**.
**One number.** No split into occupants / appliances / lighting, no time profile, no weekday/weekend
distinction. **This is precisely the quantity the generated occupancy is meant to replace**, so it is
where the injected campaign differs from the uninjected control, and the control is the run that keeps
it. Nothing else in TABULA is time-varying at all, so nothing else can be injected into.

### 4.2 🔴 There IS an intermittent-heating reduction, and the earlier reading of the national rows was wrong

The national rows all carry `F_red_htr1 = F_red_htr4 = 1`, which reads as "no setback anywhere". **The
rows the archetypes actually use do not**: `0.9`/`0.8` for single-unit housing and `0.95`/`0.85` for
multi-unit. It is a **scalar applied to the transmission heat-transfer coefficient, not a setback
schedule**, and it is identical across the three folds.

**Consequence for item 8.1:** an EnergyPlus model that implements a real night-setback schedule is no
longer computing TABULA's quantity, and its difference from TABULA is then partly the setback rather
than the occupancy. Whatever is done, it is the same in all three folds.

### 4.3 🔴 Why the EU set is KEPT rather than "improved" to the national values

On the EU set, **every non-geometric boundary condition is identical across `es`, `uk` and `it`**, so
any cross-country difference in a simulated result comes from geometry, U-values and weather **alone**.
On the national set it would additionally come from a 1 °C set-point difference (`GB` 21 vs 20) and an
air-change rate differing by a factor of ~2 (`IT` 0.3 vs `GB` 0.59) — **both country-correlated, i.e.
confounded with exactly the LOCO signal this paper measures**.

**Switching to the national rows would be a basis change and is not taken here.** It is recorded as an
available sensitivity, never as a mixture.

### 4.4 🔴 A published unit that contradicts its own column

`Tab.BoundaryCond`'s unit row gives `F_red_htr1` and `F_red_htr4` the unit **°C**. They are
dimensionless reduction factors — the EU rows carry `0.9`/`0.8`, the German rows `0.8796296…` and
`0.7931034…`, which are ratios and not temperatures. **Same class as `FINDING 47` and `FINDING 56`**
(`P139` in ISTAT's own tracciato): a published label that contradicts its own column's values, catchable
only by reading them. Two such defects were found in two different official sources in one day.

---

## 5. The archetype tables

Source: `Calc.Set.Building` in `tabula-calculator.xlsx`. 272 ES/GB/IT rows seen.

* **166 refurbishment variants dropped.** Each archetype appears as `.001` (existing state), `.002`,
  `.003` (two refurbishment levels). 🔴 **Only `.001` is the existing stock**; scoring a refurbished
  variant against a real diary would compare our occupancy against a building that does not exist.
* 🔴 **4 rows dropped for carrying NO construction-year class**: `ES.TestRegion.MUH1..MUH4.SyAv.001.001`.
  They sit under `Code_StatusDataset = Typology` and carry real floor areas (1,034.6–1,499.6 m²), so
  **neither the status column nor a non-null check excludes them** — an extraction keyed on the country
  code alone ships them, and Spain then reports **seven** construction-year classes where the census
  axis has six. The builder drops them on the construction-year class and **refuses** if the set of
  unclassified rows ever changes.
* 44 of 333 columns used.

| fold | TABULA | archetypes | types | periods | type × period cells |
|---|---|---|---|---|---|
| `es` | `ES` | 24 | AB, MFH, SFH, TH | 6 | **24 of 24 — a complete grid** |
| `uk` | `GB` | 36 | AB, MFH, SFH, TH | 8 | 29 of 32 |
| `it` | `IT` | 42 | AB, MFH, SFH, TH | 8 | 42 of 48 |

🔴 **The three folds do not have the same archetype structure, and that is a fourth LOCO asymmetry.**
Spain is a clean 4 × 6. Great Britain carries **two parallel parameterisations** for some cells — both
`GB.ENG.SFH.01.Gen` and `GB.ENG.SFH.01.Detached`, plus merged-period codes such as
`GB.ENG.SFH.04-08.Detached`. Italy carries **composite types** (`MFH-AB`, `SFH-TH`) and **composite
periods** (`.01-03`, `.04-05`). **Which row represents a cell is a campaign-design decision and it is
NOT taken here** — see §6.

### 5.1 🔴 TABULA's `GB` typology is ENGLAND, not Great Britain, and certainly not the UK

The recorded limitation was *"`GB` is Great Britain, not the United Kingdom; Northern Ireland is
outside it"*. The file is stricter than that. Every GB archetype code is `GB.ENG.…` and the region
census is:

| country | `Code_ClimateRegion` | region token | rows |
|---|---|---|---|
| ES | `ES.ME` | `ME` (Mediterranean) | 72 (+4 TestRegion) |
| GB | `GB.Temperate` | **`ENG`** | 90 |
| IT | `IT.MidClim` | `MidClim` | 106 |

**There is no Scotland or Wales row anywhere in the workbook.** So the `uk` fold's diaries are UK-wide
while its building stock is English. That is a bigger gap than the Northern Ireland one and it belongs
in the same table as `D-S6-2`'s wave gap and `D-S5-1`'s census-year gap.

⚪ Spain and Italy each have exactly one climate region, so no regional choice arises — but
`IT.MidClim` representing a country spanning Alpine to Mediterranean is a declared simplification, and
`ES.ME` likewise.

### 5.2 Columns carried

`Code_BuildingVariant`, `Code_Building`, `Code_Country`, `Code_BuildingType`, `Code_BuildingSizeClass`,
`Code_ConstructionYearClass`, `Code_ClimateRegion`, `Code_BoundaryCond`, `Code_StatusDataset`,
`Code_TypeVariant`, `Number_BuildingVariant`; **geometry** `A_C_Ref`, `V_C`, `n_Storey`,
`n_Storey_effective`, `h_room`, `A_Roof_1..2`, `A_Wall_1..3`, `A_Floor_1..2`, `A_Window_1..2`,
`A_Door_1`, `A_Window_Horizontal/East/South/West/North`; **fabric** `U_Roof_1..2`, `U_Wall_1..3`,
`U_Floor_1..2`, `U_Window_1..2`, `U_Door_1`, `delta_U_ThermalBridging_Original`; **loads** `phi_int`,
`q_w_nd`.

Reference floor areas span `es` 55.0–7,507.5 m² (median 747.7), `uk` 74.3–4,357.1 (median 149.4),
`it` 89.0–3,506.2 (median 549.9). 🔴 **The UK median is a fifth of Spain's and a fourth of Italy's**,
because the GB set is dominated by single dwellings while ES/IT carry whole apartment blocks. Any
per-m² comparison across folds has to say which.

---

## 6. 🔴 What is NOT decided here, and must be before an IDF exists

1. **Geometry.** `Calc.Set.Building` gives envelope AREAS and a conditioned volume — enough for a box
   model, **not** a 3D geometry. Footprint aspect ratio, orientation of the box, and how
   `A_Window_East/South/West/North` map onto its faces are ours to assume and to declare.
2. ~~**Zoning.**~~ 🟢 **CLOSED 2026-08-21 by the author: ONE THERMAL ZONE PER DWELLING. See §10.**
3. **Construction layer build-up.** TABULA gives U-values, not layers. Thermal mass enters as `c_m`
   (45 Wh/m²K on the EU set); reproducing that with real layers is an inverse problem with many
   answers, and which one is chosen changes the dynamics even when the U-value matches.
4. **Which archetype represents a `uk`/`it` cell** where two parameterisations exist (§5) — and what to
   do with the 3 empty GB cells and 6 empty IT cells.
5. ~~**`phi_int` decomposition.**~~ 🟢 **CLOSED 2026-08-21 by `D-S8-2` item 5, ruled (c): it becomes a
   PRE-REGISTERED SENSITIVITY, not a chosen number. See §9.**
6. ~~**Weather.**~~ 🟢 **RULED 2026-08-21 by the author: DIARY-SURVEY-YEAR ACTUAL WEATHER, not a
   typical year. See §11 — the ruling is recorded, the files are NOT yet acquired, and §11 states the
   confound the ruling accepts.**

## 7. Still owed

* 🔴 **The licence was NOT verified.** `RL24`'s claim (IEE / IWU, redistribution of derived tables
  permitted with attribution) remains unchecked; the quoted terms were not located. **Verify before any
  derived parameter table is published**, not before it is used internally.
* 🔴 `G8.1`–`G8.4` still have no reference series. `D-S8-1` (a) re-pointed them to REPRODUCIBILITY
  gates on 2026-08-20; nothing here changes that and nothing here has been gated.

## 8. Re-derive

```
curl -L -o Step8_docs/outputs_step8/raw/tabula-values.xlsx \
  "https://episcope.eu/fileadmin/tabula/public/calc/tabula-values.xlsx"
curl -L -o Step8_docs/outputs_step8/raw/tabula-calculator.xlsx \
  "https://episcope.eu/fileadmin/tabula/public/calc/tabula-calculator.xlsx"
python tools/4thJ_step8_tabula.py Step8_docs/outputs_step8
```

The builder verifies both digests, both workbooks' structure, all 22 construction-year bands, the
sixteen quoted EU boundary-condition values, the boundary-condition pointer on every archetype, and the
exact identity of the four unclassified rows — and **writes nothing if any of them fails**.

---

## 9. 🟢 `D-S8-2` item 5 — RULED (c): the `phi_int` split becomes a PRE-REGISTERED SENSITIVITY, not a chosen number

**Author, 2026-08-21: "sensitivity across splits".** §6 item 5 is therefore closed. Items 1–4 and 6
of §6 remain open.

### 9.1 The problem, stated exactly

TABULA gives internal gains as **one** annual constant, `phi_int = 3.0 W/m²`, identical in all three
folds (`FINDING 57`). It is the only time-invariant load in the model and therefore the only place
generated occupancy can enter — but occupancy drives only *part* of internal gains, and TABULA
publishes no decomposition into occupant / appliance / lighting.

Choosing a split from an outside standard would put a **free parameter nobody pre-registered** at the
centre of the campaign, and its value would be doing work the paper never declared. That is the
option the author declined.

### 9.2 The form that was adopted, and why it is a one-parameter sweep

Let `f` be the fraction of `phi_int` that occupancy drives. The injected model is

```
phi_int(t)  =  (1 - f) * 3.0                          <- flat, appliance + lighting + standby
             +  f * 3.0 * g(t) / mean_year( g(t) )    <- occupant-driven, from our schedules
```

where `g(t)` is the generated presence signal (`G7.13`'s `presence_minutes`, aggregated to the
simulation timestep).

Three properties make this the honest form, and each is a constraint, not a convenience:

1. 🟢 **The annual mean of `phi_int(t)` is exactly 3.0 W/m² for every `f`.** The normalisation by
   `mean_year(g)` guarantees it. So no run in the sweep is quietly adding or removing energy relative
   to TABULA's own balance; **every difference between runs is redistribution in TIME, which is the
   entire claim of the paper.**
2. 🟢 **`f = 0` IS the uninjected control.** It reduces to the flat 3.0 W/m². The control is not a
   separate model with separate assumptions — it is one endpoint of the same sweep, which removes a
   whole class of "the control was built differently" objection.
3. 🟢 **`f = 1` is the upper bound**, where all internal gains follow occupancy. It is physically
   unreasonable and is included precisely because it **brackets** the effect: if the result is
   qualitatively the same at `f = 0.15` and at `f = 1`, the missing split does not decide the
   conclusion, and that is a stronger statement than any single chosen split could support.

### 9.3 🔴 THE PRE-REGISTERED GRID — fixed now, before any run

```
f  ∈  { 0.00,  0.15,  0.30,  0.50,  1.00 }
```

Five levels, `f = 0` being the control. **Written down before a single simulation exists**, so it
cannot be widened after seeing a result and it cannot be narrowed to the levels that behave.

⚪ The levels are **not** derived from any literature value, deliberately. They are a spanning grid
over the admissible interval `[0, 1]`, denser at the low end because that is where a residential
occupant fraction plausibly sits and where the curve is steepest.

🔴 **The reporting rule, also pre-registered:** the headline result is quoted at **every** level of
`f`, never at one. Any statement of the form "occupancy injection changes annual heating demand by
X %" must carry the range over the grid. A single-`f` number may not appear in the paper.

### 9.4 What this costs, stated plainly

The campaign is **multiplied by five**. That is the real price of the author's ruling and it should
not be discovered later: every fold, every archetype, every weather year runs five times instead of
once. With 24 / 36 / 42 archetypes across `es` / `uk` / `it` (102 archetypes), the injected campaign
is 102 × 5 = **510 archetype-runs per weather specification**, against 102 for a single-split design.

⚪ It is still cheaper than it looks, because the four injected levels share everything except one
scalar: same IDF, same weather, same schedules. Only the gains object changes.

### 9.5 🔴 What is still NOT decided, and why the sweep does not rescue it

The sweep spans the split. It does **not** span:

* **The shape of `g(t)`** — that is the model's output and the object under test, not a parameter.
* **§6 items 1–4 and 6** — geometry, zoning, layer build-up, archetype selection, weather. Those are
  unchanged and still open; none is turned into a sensitivity by this ruling.
* 🔴 **The `F_red_htr` interaction.** TABULA applies an intermittent-heating reduction as a **scalar**
  (0.9/0.8 SUH, 0.95/0.85 MUH — `FINDING 57`). If the EnergyPlus model implements a real setback
  schedule *and* an occupancy-driven gains profile, the two are no longer separable and the
  difference from TABULA stops being attributable to occupancy. **The campaign must keep the scalar
  and must not add a setback schedule**, or the sweep measures two things at once.

---

## 10. 🟢 §6 item 2 — RULED: ONE THERMAL ZONE PER DWELLING

**Author, 2026-08-21: "single thermal zone per dwelling".** §6 item 2 is closed.

### 10.1 Why this one is forced rather than preferred

TABULA's calculation is a whole-dwelling monthly quasi-steady-state energy balance. It has **no
internal partition at all**: `c_m` is a single dwelling-wide thermal capacity (45 Wh/m²K on the EU
set), `theta_i` is a single set-point (20 °C SUH / MUH, 21 °C on the GB national row), `n_air_use`
is one dwelling-wide air-change rate, and `F_red_htr` is one scalar on the whole transmission
coefficient. **There is no second zone anywhere in the parameter set to give a second zone its
values.**

So a multi-zone EnergyPlus model could not be parameterised from TABULA. It would have to be
parameterised from an *assumption about how dwellings are divided*, and that assumption would then be
sitting between our occupancy schedules and the number we report, doing work nobody declared. The
single zone is the only zoning that keeps the EnergyPlus result comparable to the TABULA figure it is
being validated against.

⚪ This is the same shape of argument as `FINDING 60`'s convention A (forced by `QS112UK`, not
chosen) and `§4.3`'s decision to keep the EU boundary conditions rather than "improve" them to the
national rows. Where the source cannot express a distinction, adopting the distinction anyway means
inventing it.

### 10.2 🔴 What the single zone COSTS, stated now

The generated diaries carry `LOC == at_home` and **nothing finer** — `LOC` has four classes and no
room resolution (`FINDING 45` also noted it has no workplace class). So the model could not have
driven a room-level zoning even if TABULA had supported one. The two limitations coincide, which is
convenient, but they are independent and both must be declared:

* **From TABULA:** no zone-level parameters exist.
* **From our own data:** no zone-level occupancy exists.

The consequence for the claim: this paper can say that occupancy redistributes internal gains in
TIME. It **cannot** say anything about where in the dwelling those gains land, and no sentence in the
paper may imply that it can.

### 10.3 What is NOT closed by this

§6 items 1, 3 and 4 — geometry, layer build-up and archetype selection — are untouched. In
particular the single zone still needs a **box geometry** (item 1) before an IDF exists: one zone is
not the same as one shoebox, and the aspect ratio, orientation and window-to-face mapping remain ours
to assume and to declare.

---

## 11. 🟢 §6 item 6 — RULED: DIARY-SURVEY-YEAR ACTUAL WEATHER

**Author, 2026-08-21: "diary-survey-year actual weather".** §6 item 6 is closed as a DECISION.
It is **not** closed as a work item: no weather file has been acquired and item 8.2 remains open.

### 11.1 The ruling

Each fold is simulated on the actual meteorological year covering its own HETUS fieldwork window:

```
es   fieldwork 2009-2010
uk   fieldwork 2014-2015
it   fieldwork 2013-2014
```

not on a typical-year file (TMYx / IWEC), and not on one shared year.

### 11.2 🔴 THE CONFOUND THE RULING ACCEPTS, RECORDED BEFORE ANY RUN EXISTS

This was **not** the recommended option, and the reason it was not is a real property of the design
rather than a preference. It is written down here so that it is a declared limitation in the paper
and not a discovery in review.

Under a fixed shared weather year, the only thing that differs between the three folds is the
country's population and the model's transfer to it. Under diary-year weather, **two things differ at
once**: the country AND the meteorological year. The three windows are five years apart at the
extremes (2009-10 vs 2014-15), so:

* 🔴 **A cross-fold difference in heating demand can no longer be attributed to the LOCO
  transfer.** Part of it is that Spain's window and the UK's window were different winters. The
  design already carries country-correlated asymmetries — `FINDING 53`'s three different day
  bases, `D-S6-2`'s Italian wave gap, `FINDING 51`'s missing Spanish `homemaker` band, `FINDING 60`'s
  two household conventions — and this adds one more to a list that is already long enough to need
  a table in the paper.
* ⚪ **What the ruling buys in exchange is real:** each fold's occupancy and its weather come from
  the same months, so a diary recorded in a cold January is simulated in that January. If any
  downstream analysis conditions on season or on outdoor temperature, that internal consistency is
  what makes it legitimate.

### 11.3 🔴 THE CONTAINMENT, which is what makes the ruling safe to use

**The `phi_int` sweep is unaffected, and it is the paper's actual claim.** `D-S8-2` fixed
`f ∈ {0, 0.15, 0.30, 0.50, 1.00}`, and every level of `f` within one fold runs on **the same
weather file**. So:

* Differences **across `f`, within a fold** — the occupancy effect — are weather-free by
  construction. `f = 0` is the control and it sees exactly the same year as `f = 1`.
* Differences **across folds** carry the weather-year confound and must never be read as a transfer
  result on their own.

🔴 **Pre-registered reporting rule, added here:** the headline occupancy effect is quoted
**within fold**, as a difference across `f`. Any cross-fold comparison of absolute demand must state
the meteorological year alongside the country, in the same sentence.

### 11.4 What is now owed, and it is a DATA-ACQUISITION task

Like item 5.1 and item 8.1, this is a fetch-and-verify job and is **not attempted blind**:

1. **The fieldwork calendars.** "Diary-survey-year" is not yet a year: each national fieldwork window
   spans parts of two calendar years, and the rule needs pinning to a definite 12 months. The rule
   proposed here, to be confirmed when the calendars are on disk: **the 12 consecutive months that
   contain the most diaries in that fold**, measured from the corpus's own dates rather than from a
   methodology PDF's prose.
2. **An AMY source with an open licence**, per country, per year, at the archetypes' locations. TMYx
   is open; actual-year files generally are not, and the ERA5-derived route needs its licence checked
   before anything derived from it is published — the same check §7 still owes for TABULA.
3. ⚪ **A location.** TABULA's typologies are national-with-a-region-tag (`ES.ME`, `GB.ENG`,
   `IT.MidClim`), so the weather station is a choice this ruling does not make.

🔴 Until 1–3 are on disk, **no weather-driven number may be quoted at all** — not even a
provisional one on a typical year, because a provisional TMY run is exactly the thing that would
later be mistaken for the pre-registered design.
