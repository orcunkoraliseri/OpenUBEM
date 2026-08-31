# DR12 — Brief: External validation of the `EU-11` district heating-EUI results

- **Validates**: the per-district heating EUIs produced by work package `EU-11` (four European residential
  districts, real footprints, TABULA archetypes, pinned ERA5-derived weather, EnergyPlus 23.1 on Speed).
  See [`../STATE_european_locations_v3.md`](../STATE_european_locations_v3.md) §3 head and
  [`../prompts/PROMPT_EU-11_full_district_campaign_speed.md`](../prompts/PROMPT_EU-11_full_district_campaign_speed.md).
- **Report to be saved as**: `DR12_eui_external_validation.md`, next to this brief, unchanged.
- **Date of brief**: 2026-08-28.

---

## Task (paste everything below this line into the deep-research tool)

You are producing a publication-grade research report that answers one question: **what published,
independently sourced values exist against which a simulated residential heating energy-use intensity
(kWh/m²·year) for a specific urban district in Madrid, Lyon, London or Bologna can be checked — and what
does each of them actually measure?**

### Context you must take as given

A building-stock model has produced heating-only, area-pooled energy-use intensities for four residential
districts:

| Fold | District | City, country | Weather year(s) simulated | Buildings |
|---|---|---|---|---|
| `es` | Berruguete (Tetuán) | Madrid, Spain | 2009–2010 | ~1,194 residential |
| `fr` | Haut Cœur des Pentes (Croix-Rousse) | Lyon, France | 2023 | 530 residential |
| `uk` | St Dunstan's (Tower Hamlets) | London, United Kingdom | 2014–2015 | ~1,242 residential |
| `it` | Galvani 2 (centro storico) | Bologna, Italy | 2013–2014 | ~1,220 residential |

Physics: TABULA/EPISCOPE existing-state archetypes; mass-less envelope with an explicit internal heat
capacity; constant air change `n_air_use + n_air_infiltration`; heating-only ideal loads at a constant
20 °C set-point; internal gains 3 W/m² all-convective; **no cooling**, **no domestic hot water**, **no
appliance or lighting electricity in the reported figure**. The reported quantity is therefore **space
heating demand per unit of conditioned reference floor area**, not a metered bill and not a whole-building
EUI. An earlier 31-building Lyon run of the same pipeline returned **60.7087 kWh/m²** heating, of which 26
of 31 buildings were one-zone-per-floor massing boxes rather than dwelling-partitioned models.

### What the report must contain

**§1 — Benchmark inventory, one table per country.** For each of Spain, France, the United Kingdom and
Italy, list every published source that carries a residential space-heating intensity that could serve as a
check, and for each row give: the exact quantity published (final energy? useful/net demand? primary
energy? delivered heat?), its unit and floor-area definition (net vs gross, heated vs total, `A_C_Ref` vs
`SUL`/`GIA`), the reference year, the geographic resolution (national, regional, municipal, district,
building), the population it covers, whether it is measured, modelled or normalised to a standard climate,
the licence, the URL and your retrieval date. Sources to cover at minimum, plus anything better you find:
Odyssee-MURE (unit consumption of dwellings for space heating, climate-corrected and not), EU Building
Stock Observatory, TABULA/EPISCOPE national brochures' own example-building demand values, IDAE / SPAHOUSEC
(Spain), CEREN and ADEME plus the DPE database (France), BEIS/DESNZ NEED and the English Housing Survey and
the domestic EPC register (United Kingdom), ENEA / ISTAT consumi energetici delle famiglie and the APE
regional registers (Italy).

**§2 — Comparability, stated as a correction chain and not as an opinion.** For each benchmark, state
exactly what must be done to compare it with a simulated *net space-heating demand under a specific
weather year*: system efficiency and distribution losses to move between delivered and useful energy; DHW
and cooking separation where the published figure is a bundled "heating" number; floor-area basis
conversion; degree-day normalisation between the published reference year and the simulated year (give the
HDD basis and source used). Where a correction cannot be made from published data, say
`NOT COMPARABLE` and say why. **Do not manufacture a correction factor.**

**§3 — The district question.** For each of the four named districts, report what is published at a
resolution finer than national: municipal energy balances, city climate plans, census/tract statistics on
heating fuel and dwelling age, any local EPC aggregate, and any published UBEM or measurement study of the
same neighbourhood or an adjacent one in the same city. Give the values with their populations. If nothing
exists below city level for a district, state that plainly — an honest gap is a result.

**§4 — Expected magnitude, with its own uncertainty.** From §1–§3 only, give for each district a range in
which a *net space-heating demand* for that stock and that climate would be unsurprising, with the
reasoning and the sources that bound each end. State the range as a range. **Do not produce a single
number, and do not present §4 as a validation verdict** — it is the yardstick, not the measurement.

**§5 — Known biases of this modelling route, from the literature.** What do published comparisons of
TABULA-based archetype models against measured consumption find, in direction and magnitude? Cover at
minimum: the **prebound effect** (measured consumption below calculated demand in poor-performing stock)
and the **rebound effect** in refurbished stock, with the studies that quantify them for these four
countries; the effect of a constant 20 °C set-point and full-floor-area heating against actual partial
heating; the effect of a massing-box zoning fallback against a dwelling-partitioned model; and the effect
of a mass-less envelope with lumped internal capacity on annual demand and on peak.

**§6 — A usable acceptance test.** Propose a checking protocol the project can run: which benchmark to
compare against per district, in which direction, with which corrections, and what deviation should count
as *consistent*, as *worth investigating*, and as *incompatible*. Every threshold must be justified from
§1–§5, never asserted.

### Hard rules

1. **No invented numbers, tables, standard clauses or URLs.** Every figure and every quotation carries its
   source (publication, table or clause number, DOI or URL, retrieval date) or is marked `UNVERIFIED`.
2. Never present a modelled national average as a measurement; label every row measured / modelled /
   normalised.
3. Separate **facts**, **inferences** and **recommendations** with explicit labels.
4. If a source is paywalled or has moved, say so and give the last working reference — do not substitute a
   secondary citation silently.
5. A benchmark that measures a different quantity is more dangerous than no benchmark. Say so where it
   applies.

### Acceptance test this report must pass

Every §1 row carries a quantity definition, a floor-area basis, a population and a licence; every §2 entry
either gives a correction chain with sources or says `NOT COMPARABLE`; §3 distinguishes district-level
evidence from city-level evidence; §4 is a range with both ends sourced; §6's thresholds each cite the §1–§5
material they follow from.
