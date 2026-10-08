# DR13 — Brief: External validation of the **Madrid / Berruguete** district heating-EUI

- **Validates**: the `ES-MAD-BERRUGUETE` fold of work package `EU-11`.
- **Companion**: the cross-country methodology brief [`DR12_eui_external_validation_brief.md`](DR12_eui_external_validation_brief.md). DR13 is the Spain-specific instance; where the two overlap, DR12's hard rules govern.
- **Report to be saved as**: `DR13_madrid_berruguete_validation.md`, next to this brief, unchanged.
- **Executor**: Gemini Antigravity (deep research). **Date of brief**: 2026-08-28.

---

## Task (paste everything below this line into the deep-research tool)

You are validating a simulated **residential space-heating demand** for one named urban district. Produce a
publication-grade report. You are not asked to endorse or reject the number; you are asked to build the
independent evidence against which it can be judged.

### The object under validation

| Item | Value |
|---|---|
| District | **Berruguete**, distrito de **Tetuán**, Madrid, Spain |
| Perimeter | **1,194 residential buildings** (of 1,398 footprints; 204 excluded as non-residential) |
| Footprints | OpenStreetMap / Overpass (ODbL), EPSG:32630 |
| Height provenance | 1,044 buildings `storeys × 3.0 m`, 354 `assumed 9.0 m` — **no measured height at all** |
| Construction year | **0 of 1,194 in OSM**; supplied from a Catastro sidecar with an observed year for **1,183 of 1,194** |
| Archetypes | TABULA/EPISCOPE **ES** existing-state rows |
| Weather | ERA5-derived actual-year EPW, **2009–2010**, Madrid |
| Engine | EnergyPlus 23.1 on a Linux HPC cluster |

Physics actually simulated: mass-less envelope with an explicit lumped internal heat capacity; constant air
change `n_air_use + n_air_infiltration`; **heating-only** ideal loads at a constant **20 °C** set-point;
internal gains **3 W/m², all convective**; **no cooling, no domestic hot water, no appliances or lighting in
the reported figure**. The reported quantity is therefore **net space-heating demand per unit of conditioned
reference floor area (kWh/m²·year)** — not delivered energy, not a bill, not a whole-building EUI. Madrid is
climate zone **D3** under CTE; a large share of the stock predates NBE-CT-79.

### What the report must contain

**§1 — Spanish benchmarks, one table.** Every published source carrying a residential space-heating
intensity usable as a check. Per row: the exact quantity (final / useful / primary / delivered), the
floor-area basis (útil vs construida vs `A_C_Ref`), reference year, geographic resolution, population
covered, measured vs modelled vs climate-normalised, licence, URL, retrieval date. Cover at minimum:
**IDAE SPAHOUSEC I and II** (consumos del sector residencial, and its Mediterranean/Continental split),
IDAE's *Consumos del Sector Residencial en España* series, **Odyssee-MURE** unit consumption per dwelling
for space heating (both raw and climate-corrected), the **EU Building Stock Observatory**, the **TABULA ES**
national brochure's own calculated demand values for its example buildings, **INE** Censo de Población y
Viviendas 2011/2021 heating-installation and dwelling-age tables, the **Certificados de Eficiencia
Energética** register (IDAE national aggregate + Comunidad de Madrid), and any **CTE DB-HE** limit demand
value for zone D3 (state that a limit is a regulatory ceiling, never a stock average).

**§2 — District-level evidence for Berruguete/Tetuán.** What exists **below city level**: the Ayuntamiento
de Madrid open-data portal (consumo energético por distrito, censo de locales, padrón), the *Plan Madrid
360* / *Madrid + Natural* climate documents, INE census-section tables for Tetuán (dwelling age, heating
type, dwelling size), Comunidad de Madrid EPC aggregates by municipality or district, and any published UBEM
or measurement study of Tetuán or an adjacent Madrid district. Give each value with its population. **If
nothing exists below city level, say so plainly — an honest gap is a result.**

**§3 — Weather-year correction for 2009–2010.** Madrid HDD for the 2009, 2010 heating seasons against the
long-run normal, from a named source (Eurostat `nrg_chdd`, AEMET, or Odyssee's own degree-day series), with
the base temperature stated. Give the multiplier that would move a normal-year benchmark onto the simulated
years, and its uncertainty. **Do not manufacture a factor you cannot source.**

**§4 — The correction chain, stated explicitly.** For each §1 benchmark, what must be done to compare it
with a *net demand under a specific weather year*: boiler/system seasonal efficiency and distribution losses
(Spanish stock: individual gas boilers, gas-oil, electric, and the district-heating share in Madrid);
separation of DHW and cooking from a bundled "calefacción" figure; useful-vs-constructed floor area; the §3
degree-day step. Where a step cannot be sourced, write `NOT COMPARABLE` and say why.

**§5 — Spain-specific biases of this modelling route.** From the literature: the **prebound effect** in
Spanish residential stock (measured consumption well below calculated demand — quantify with studies);
**partial heating** — Spanish households heating a subset of rooms for a subset of hours, against this
model's whole-floor-area constant 20 °C; the effect of a **massing-box zoning fallback** and of a **mass-less
envelope with lumped capacity** on annual demand; and the specific risk here that **every height is derived
or assumed, never measured** — what does the literature say about volume error propagating into heating
demand?

**§6 — Expected range and acceptance test.** From §1–§5 only, give the range in which a net space-heating
demand for this stock, this climate and these weather years would be **unsurprising**, both ends sourced.
State it as a range, never a single number, and never as a verdict. Then give a checking protocol: which
benchmark, in which direction, with which corrections, and what deviation counts as *consistent*, as *worth
investigating*, and as *incompatible* — every threshold justified from §1–§5.

### Hard rules

1. **No invented numbers, tables, clauses or URLs.** Every figure carries publication, table/clause, DOI or
   URL and retrieval date, or is marked `UNVERIFIED`.
2. Never present a modelled national average as a measurement. Label every row measured / modelled /
   normalised.
3. Separate **facts**, **inferences** and **recommendations** with explicit labels.
4. Paywalled or moved source: say so, give the last working reference, never silently substitute a secondary
   citation.
5. A benchmark that measures a different quantity is more dangerous than no benchmark. Say so where it
   applies.

### Acceptance test this report must pass

Every §1 row carries a quantity definition, a floor-area basis, a population and a licence; §2 separates
district-level from city-level evidence; §3 names its degree-day source and base temperature; every §4 entry
gives a sourced chain or says `NOT COMPARABLE`; §6's range has both ends sourced and each threshold cites the
§1–§5 material it follows from.
