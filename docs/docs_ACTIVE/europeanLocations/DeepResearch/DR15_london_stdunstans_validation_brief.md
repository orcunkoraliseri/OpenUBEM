# DR15 — Brief: External validation of the **London / St Dunstan's** district heating-EUI

- **Validates**: the `GB-LDN-STDUNSTANS` fold of work package `EU-11`.
- **Companion**: [`DR12_eui_external_validation_brief.md`](DR12_eui_external_validation_brief.md) — DR12's hard rules govern.
- **Report to be saved as**: `DR15_london_stdunstans_validation.md`, next to this brief, unchanged.
- **Executor**: Gemini Antigravity (deep research). **Date of brief**: 2026-08-28.

---

## Task (paste everything below this line into the deep-research tool)

You are validating a simulated **residential space-heating demand** for one named urban district. Produce a
publication-grade report. You are not asked to endorse or reject the number; you are asked to build the
independent evidence against which it can be judged.

### The object under validation

| Item | Value |
|---|---|
| District | **St Dunstan's** ward, **Tower Hamlets**, London, United Kingdom |
| Perimeter | **1,242 residential buildings** (of 1,351 footprints; 109 excluded as non-residential) |
| Footprints | OpenStreetMap / Overpass (ODbL), EPSG:32630 |
| Height provenance | 1,159 buildings `storeys × 3.0 m`, 192 `assumed 9.0 m` — **no measured height at all** |
| Construction year | **1 of 1,242 in OSM**; age bands come from fetched **domestic EPC certificates**, so **only the EPC-covered subset can be simulated** and the rest are excluded, not imputed |
| Archetypes | TABULA/EPISCOPE **GB** existing-state rows |
| Weather | ERA5-derived actual-year EPW, **2014–2015**, London |
| Engine | EnergyPlus 23.1 on a Linux HPC cluster |

Physics actually simulated: mass-less envelope with an explicit lumped internal heat capacity; constant air
change `n_air_use + n_air_infiltration`; **heating-only** ideal loads at a constant **20 °C** set-point;
internal gains **3 W/m², all convective**; **no cooling, no DHW, no appliances or lighting in the reported
figure**. The reported quantity is **net space-heating demand per unit of conditioned reference floor area
(kWh/m²·year)** — not a gas bill, not SAP, not an EPC rating. Tower Hamlets is dense, with a high share of
purpose-built flats, a large social-housing stock and significant post-2000 construction alongside Victorian
terraces.

### What the report must contain

**§1 — UK benchmarks, one table.** Every published source carrying a residential space-heating intensity
usable as a check. Per row: exact quantity (delivered gas/electricity, useful heat, primary, SAP-modelled),
floor-area basis (**GIA / total floor area / SAP TFA**), reference year, geographic resolution, population,
measured vs modelled vs weather-corrected, licence, URL, retrieval date. Cover at minimum: **BEIS/DESNZ
National Energy Efficiency Data-Framework (NEED)** — including its **LSOA-level** and dwelling-type tables;
**sub-national gas and electricity consumption statistics** at **LSOA/MSOA** level (state that gas
consumption bundles space heating with DHW and cooking); the **English Housing Survey** energy reports; the
**domestic EPC register** (`opendatacommunities` / its successor) for Tower Hamlets — `SPACE-HEATING-COST`,
`ENERGY-CONSUMPTION-CURRENT` and the **SAP conventional** basis, stated as conventional; **Odyssee-MURE**;
the **EU Building Stock Observatory**; the **TABULA GB** brochure's own calculated demand values; and the
**Cambridge Housing Model / BREDEM** documentation for what SAP's assumed heating pattern actually is.

**§2 — District-level evidence for St Dunstan's / Tower Hamlets.** What exists **below city level**:
LSOA-level sub-national consumption for the ward's LSOAs, the London Datastore (London Building Stock Model,
London Heat Map, SHINE), Tower Hamlets council climate and retrofit documents, the **Census 2021** tables on
central heating type and accommodation type for the ward, and any published UBEM, smart-meter study or
measured campaign covering Tower Hamlets or an adjacent inner-London borough. Give each value with its
population. **If nothing exists below city level, say so plainly — an honest gap is a result.**

**§3 — Weather-year correction for 2014–2015.** London HDD for the 2014 and 2015 heating seasons against the
long-run normal, from a named source (Eurostat `nrg_chdd`, the Met Office, or the degree-day basis used by
DESNZ), with the base temperature stated (UK convention is 15.5 °C — say which you use and convert
explicitly). **2014 was an exceptionally mild winter in the UK — quantify it, with the source.** Give the
multiplier onto the simulated years and its uncertainty.

**§4 — The correction chain, stated explicitly.** For each §1 benchmark: boiler seasonal efficiency and
distribution losses for the UK stock mix (condensing/non-condensing gas, electric storage heating, communal
and district heating — Tower Hamlets has a notable communal-heating share, state it where published); DHW and
cooking separation from a bundled meter figure; **SAP TFA vs conditioned reference area**; the §3 degree-day
step. Where a step cannot be sourced, write `NOT COMPARABLE` and say why.

**§5 — UK-specific biases of this modelling route.** From the literature:
(a) the **prebound effect** — the UK is where it is best documented; quantify the calculated-vs-measured gap
by SAP band, with studies;
(b) **partial heating and heating patterns** — measured UK internal temperatures and heating-hours (e.g. from
the Energy Follow-Up Survey and smart-meter studies) against this model's constant 20 °C over the whole floor
area, and what that does to demand;
(c) **flats vs houses** — the effect of party-wall and inter-dwelling heat transfer on measured per-m²
intensity in dense flatted stock, which a per-building massing model treats differently;
(d) the **massing-box zoning fallback** and the **mass-less envelope with lumped capacity**;
(e) 🔴 the specific risk that **no height here is measured** — every height is `storeys × 3.0 m` or an assumed
9.0 m; what does the literature report for volume/storey-height error propagating into heating demand?

**§6 — Expected range and acceptance test.** From §1–§5 only, give the range in which a net space-heating
demand for this stock, this climate and 2014–2015 would be **unsurprising**, both ends sourced. State it as a
range, never a single number, never a verdict. Then give the checking protocol: which benchmark, in which
direction, with which corrections, and what deviation counts as *consistent*, as *worth investigating*, and
as *incompatible* — every threshold justified from §1–§5. Add one explicit instruction on how a **partial
population** (only the EPC-covered subset simulated) must be reported alongside any comparison.

### Hard rules

1. **No invented numbers, tables, clauses or URLs.** Source or `UNVERIFIED`.
2. Never present a modelled national average as a measurement. **SAP and EPC figures are conventional, not
   measured — say so every time you use one.**
3. Separate **facts**, **inferences** and **recommendations** with explicit labels.
4. Paywalled or moved source: say so, give the last working reference, never silently substitute.
5. A benchmark that measures a different quantity is more dangerous than no benchmark. Metered gas is not
   space-heating demand — repeat that wherever you use it.

### Acceptance test this report must pass

Every §1 row carries a quantity definition, a floor-area basis, a population and a licence; §2 gives at least
the LSOA-level evidence for the ward or states that it is unavailable; §3 names its degree-day source and base
temperature and quantifies the 2014 mildness; every §4 entry gives a sourced chain or says `NOT COMPARABLE`;
§6's range has both ends sourced, each threshold cites the §1–§5 material it follows from, and the
partial-population reporting rule is explicit.
