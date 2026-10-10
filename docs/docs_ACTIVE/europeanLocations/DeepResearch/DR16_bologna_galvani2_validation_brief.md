# DR16 — Brief: External validation of the **Bologna / Galvani 2** district heating-EUI

- **Validates**: the `IT-BOL-GALVANI2` fold of work package `EU-11` — **the weakest-attributed of the four
  districts**. Read §"What is missing" before anything else.
- **Companion**: [`DR12_eui_external_validation_brief.md`](DR12_eui_external_validation_brief.md) — DR12's hard rules govern.
- **Report to be saved as**: `DR16_bologna_galvani2_validation.md`, next to this brief, unchanged.
- **Executor**: Gemini Antigravity (deep research). **Date of brief**: 2026-08-28.

---

## Task (paste everything below this line into the deep-research tool)

You are validating a simulated **residential space-heating demand** for one named urban district, and you are
also being asked to find the data that would make that simulation possible at all. Produce a
publication-grade report.

### The object under validation

| Item | Value |
|---|---|
| District | **Galvani 2**, **centro storico**, Bologna, Italy |
| Perimeter | **1,220 residential buildings** (of 1,257 footprints; 37 excluded as non-residential) |
| Footprints | Comune di Bologna `rifter_edif_pl` (CC BY 4.0), EPSG:32632 |
| Height provenance | **1,257 of 1,257 `assumed 9.0 m`** — no measured height, no storey count |
| Construction year | **0 of 1,220** |
| Storeys | **0 of 1,220** |
| Archetypes | TABULA/EPISCOPE **IT** existing-state rows |
| Weather | ERA5-derived actual-year EPW, **2013–2014**, Bologna |
| Engine | EnergyPlus 23.1 on a Linux HPC cluster |

Physics actually simulated: mass-less envelope with an explicit lumped internal heat capacity; constant air
change `n_air_use + n_air_infiltration`; **heating-only** ideal loads at a constant **20 °C** set-point;
internal gains **3 W/m², all convective**; **no cooling, no DHW, no appliances or lighting in the reported
figure**. The reported quantity is **net space-heating demand per unit of conditioned reference floor area
(kWh/m²·year)**. Bologna is climate zone **E** (2,259 GG under DPR 412/93), heating season legally limited;
the centro storico is a protected, thermally heavy, largely pre-1919 masonry fabric.

### 🔴 What is missing, and what you are asked to do about it

The project has established, by direct measurement of the open sources, that **no open dataset provides a
per-building construction year for Bologna**, and that the municipal footprint layer carries no storey count.
A statistical prior (an ISTAT census-tract construction epoch) is **not an observed year** and the project
will not impute one.

**§0 — Data recovery (do this first).** Search for and report, with URL, licence and retrieval date, any
source that would supply, at **building level**, for the Bologna centro storico:
(a) construction year or construction epoch — the Comune di Bologna open-data portal, the *Agenzia delle
Entrate* / catasto (state exactly what is and is not publicly obtainable), the regional **APE / Attestati di
Prestazione Energetica** register of Emilia-Romagna (`SACE`), the **Piano Strutturale Comunale** and
*Regolamento Urbanistico Edilizio* schedules, and any research dataset;
(b) building **height or storeys** — the portal layer `c_a944ctc_edifici_pl` (`altezza_gr`, `quota_gron`,
`quota_pied`, `volume`; ~65,744 records) is known to exist: confirm its licence, its coverage of the centro
storico, and the definition of each field;
(c) any **LiDAR / DSM** product for Bologna or Emilia-Romagna usable to derive heights, with its licence.
For each: say whether it is per-building or aggregated, its coverage, and whether its licence permits
**published derived results**. **If a source only offers a tract-level epoch, label it a statistical prior
and say it cannot license a per-building year.**

### What the report must then contain

**§1 — Italian benchmarks, one table.** Every published source carrying a residential space-heating intensity
usable as a check. Per row: exact quantity (energia finale / utile / primaria / fabbisogno), floor-area basis
(superficie utile riscaldata vs lorda vs `A_C_Ref`), reference year, geographic resolution, population,
measured vs modelled vs climate-normalised, licence, URL, retrieval date. Cover at minimum: **ENEA** Rapporto
Annuale Efficienza Energetica and its APE statistics (*Rapporto APE*, per-region, per-class fabbisogno);
**ISTAT** *I consumi energetici delle famiglie*; the **SIAPE** national APE database; **Odyssee-MURE**; the
**EU Building Stock Observatory**; the **TABULA IT** brochure's own calculated demand values for its example
buildings (give them per building type and construction period — these are the closest comparator to what is
being simulated); and **UNI/TS 11300** or DM 26/06/2015 reference values, labelled regulatory.

**§2 — District-level evidence for the centro storico.** What exists **below city level**: the Comune di
Bologna open-data portal (consumi energetici, teleriscaldamento, censimento), the **PAESC / Piano per
l'Energia Sostenibile** of Bologna, ISTAT census-section data for the centro storico (dwelling epoch,
heating type, dwelling size), Emilia-Romagna APE aggregates by comune or quartiere, and any published UBEM,
measurement campaign or district-heating study of the Bologna centro storico. Give each value with its
population. **If nothing exists below city level, say so plainly.**

**§3 — Weather-year correction for 2013–2014.** Bologna HDD for the 2013 and 2014 heating seasons against the
long-run normal and against the legal **2,259 GG** zone-E value, from a named source (Eurostat `nrg_chdd`,
ARPAE Emilia-Romagna), base temperature stated. **The 2013–2014 winter was exceptionally mild in northern
Italy — quantify it, with the source.** Give the multiplier and its uncertainty.

**§4 — The correction chain, stated explicitly.** For each §1 benchmark: generation and distribution
efficiency for the Italian stock mix (autonomo a gas, centralizzato, teleriscaldamento — Bologna has a large
district-heating network, state its share where published); DHW and cooking separation from a bundled
"riscaldamento" figure; superficie utile vs the model's reference area; the legally limited heating season
against a model that heats whenever the set-point is unmet; the §3 degree-day step. Unsourceable step →
`NOT COMPARABLE`, with the reason.

**§5 — Italy-specific biases, and the defects specific to this district.** From the literature:
(a) the **prebound effect** in the Italian stock and the calculated-vs-measured gap by APE class;
(b) 🔴 **the heavy-masonry / mass-less-model mismatch** — the centro storico is thermally very heavy and the
model uses a mass-less envelope with a lumped internal capacity; what is the reported effect on annual demand
and on peak?
(c) 🔴 **the assumed 9.0 m height, applied to every building** — what error does an assumed uniform height
introduce in volume, in surface-to-volume ratio, and hence in per-m² heating demand for a dense historic
fabric? Quantify from the literature if anything exists;
(d) the effect of a **massing-box zoning fallback** against dwelling-partitioned models for attached blocks;
(e) a constant 20 °C over the whole floor area against Italian partial heating and against the legal season
limit;
(f) the effect of **assigning an archetype without an observed construction year** — what do published
archetype-UBEM studies report when the age band is drawn from a tract prior instead of an observation?

**§6 — Expected range and acceptance test.** From §0–§5 only, give the range in which a net space-heating
demand for this stock, this climate and 2013–2014 would be **unsurprising**, both ends sourced. State it as a
range, never a single number, never a verdict. Then give the checking protocol: which benchmark, in which
direction, with which corrections, and what deviation counts as *consistent*, as *worth investigating*, and
as *incompatible* — every threshold justified. Finally, state explicitly **what this district's result may
not be used for** given §0's data gaps.

### Hard rules

1. **No invented numbers, tables, clauses or URLs.** Source or `UNVERIFIED`.
2. Never present a modelled national average as a measurement; **APE/fabbisogno figures are calculated, not
   measured — say so every time you use one.**
3. A tract-level construction epoch is a **statistical prior**, never an observed building year. Never
   present one as the latter.
4. Separate **facts**, **inferences** and **recommendations** with explicit labels.
5. Paywalled or moved source: say so, give the last working reference, never silently substitute.
6. A benchmark that measures a different quantity is more dangerous than no benchmark.

### Acceptance test this report must pass

§0 names every candidate source with licence, coverage and a per-building-vs-aggregate verdict, and states
plainly whether a per-building construction year is obtainable at all; every §1 row carries a quantity
definition, a floor-area basis, a population and a licence; §2 separates district-level from city-level
evidence; §3 names its degree-day source and base temperature and quantifies the 2013–2014 mildness; every §4
entry gives a sourced chain or says `NOT COMPARABLE`; §5(c) and §5(f) each cite at least one study or state
that none was found; §6's range has both ends sourced and ends with the explicit not-to-be-used-for statement.
