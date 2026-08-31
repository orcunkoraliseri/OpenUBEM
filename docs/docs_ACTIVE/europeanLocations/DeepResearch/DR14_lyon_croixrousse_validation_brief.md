# DR14 — Brief: External validation of the **Lyon / Haut Cœur des Pentes** district heating-EUI

- **Validates**: the `FR-LYO-HAUTCOEURPENTES` fold of work package `EU-11`, **and** the already-produced
  31-building run `s2_campaign_v3` (area-pooled **60.7087 kWh/m² heating** over **19,823.6173 m²**).
- **Companion**: [`DR12_eui_external_validation_brief.md`](DR12_eui_external_validation_brief.md) — DR12's hard rules govern.
- **Report to be saved as**: `DR14_lyon_croixrousse_validation.md`, next to this brief, unchanged.
- **Executor**: Gemini Antigravity (deep research). **Date of brief**: 2026-08-28.

---

## Task (paste everything below this line into the deep-research tool)

You are validating a simulated **residential space-heating demand** for one named urban district. Produce a
publication-grade report. You are not asked to endorse or reject the number; you are asked to build the
independent evidence against which it can be judged.

### The object under validation

| Item | Value |
|---|---|
| District | **Haut Cœur des Pentes**, **Pentes de la Croix-Rousse**, Lyon 1er/4e, France |
| Perimeter | **530 residential buildings** (of 768 footprints; 238 excluded as non-residential) |
| Footprints | **IGN BD TOPO** (Licence Ouverte / Etalab 2.0), EPSG:32631 |
| Height provenance | **764 of 768 measured** from the source — the only one of the four districts with real heights |
| Construction year | **522 of 530** present |
| Archetypes | TABULA/EPISCOPE **FR** existing-state rows |
| Weather | ERA5-derived actual-year EPW, **2023**, Lyon-Bron |
| Engine | EnergyPlus 23.1 (a first 31-building run on Windows; the full 530 re-run on a Linux HPC cluster) |
| **Already measured** | **60.7087 kWh/m²** heating, pooled over 31 buildings / 19,823.6173 m². **26 of those 31 were one-zone-per-floor massing boxes**, only 5 dwelling-partitioned. |

Physics actually simulated: mass-less envelope with an explicit lumped internal heat capacity; constant air
change `n_air_use + n_air_infiltration`; **heating-only** ideal loads at a constant **20 °C** set-point;
internal gains **3 W/m², all convective**; **no cooling, no DHW, no appliances or lighting in the reported
figure**. The reported quantity is **net space-heating demand per unit of conditioned reference floor area
(kWh/m²·year)**. Lyon is climate zone **H1c**. The Pentes are a dense, pre-1948 masonry *canut* fabric,
largely within a **Site Patrimonial Remarquable / UNESCO** perimeter, which constrains external insulation —
say what that implies for refurbishment rates.

### What the report must contain

**§1 — French benchmarks, one table.** Every published source carrying a residential space-heating intensity
usable as a check. Per row: exact quantity (énergie finale / utile / primaire), floor-area basis (surface
habitable vs SHON vs SHAB vs `A_C_Ref`), reference year, geographic resolution, population, measured vs
modelled vs climate-corrected, licence, URL, retrieval date. Cover at minimum: **CEREN** consommation
unitaire de chauffage du résidentiel, **ADEME** and **SDES / Ministère de la Transition écologique** (bilan
de l'énergie, enquête **TREMI**, *Chiffres clés du climat*), the **base DPE ADEME** open dataset (per-DPE
consumption and label distribution — note the 3CL-DPE **conventional** basis explicitly),
**Odyssee-MURE**, the **EU Building Stock Observatory**, the **TABULA FR** brochure's own calculated demand
values, and the **RT2012 / RE2020** reference values (label them regulatory, never stock averages).

**§2 — District-level evidence for the Pentes / Croix-Rousse.** What exists **below city level**:
data.grandlyon.com (the Métropole open-data portal — DPE extracts, consommation de gaz et d'électricité par
IRIS, réseau de chaleur), the **IRIS** statistics of INSEE for Lyon 1er/4e (dwelling age, heating energy,
dwelling size), the *Plan Climat Air Énergie Territorial* of the Métropole de Lyon, the **OPAH / SPR**
studies of the Pentes, and any published UBEM or measured campaign covering the Pentes or the Presqu'île.
Give each value with its population. **If nothing exists below city level, say so plainly.**

**§3 — Weather-year correction for 2023.** Lyon HDD for 2023 against the long-run normal, from a named source
(Eurostat `nrg_chdd`, Météo-France, or the DJU 18 °C series used by CEREN), with the base temperature stated.
Give the multiplier to move a normal-year benchmark onto 2023 and its uncertainty. **2023 was a warm year in
France — quantify by how much, with the source.**

**§4 — The correction chain, stated explicitly.** For each §1 benchmark: seasonal efficiency and distribution
losses (French stock mix — gaz individuel/collectif, électrique direct, PAC, réseau de chaleur; Lyon has a
substantial *réseau de chaleur*, state its share where published); DHW separation from a bundled "chauffage"
figure; surface basis conversion; the §3 degree-day step. Unsourceable step → `NOT COMPARABLE`, with the
reason.

**§5 — France-specific biases, and the two known defects of this run.**
(a) The **prebound effect** in the French stock and the **rebound** after renovation — quantify from studies,
including the well-documented gap between DPE-conventional and measured consumption.
(b) 🔴 **The zoning fallback.** 26 of the 31 simulated buildings were **one-zone-per-floor massing boxes**
rather than dwelling-partitioned models. What does the literature say about the effect of zoning resolution
(one zone per floor vs per dwelling vs per thermal exposure) on annual heating demand for dense mid-rise
blocks — in direction and magnitude?
(c) 🔴 **Geometric sensitivity.** In this pipeline, changing only the **vertex order** of the footprint moved
total heating by **11.8 %** with every reported area and volume byte-identical. Is anything comparable
reported in the literature (surface-orientation / azimuth / self-shading sensitivity in archetype UBEMs)?
(d) The effect of a **mass-less envelope with lumped capacity** on annual demand and on peak, for heavy
masonry construction specifically — the Pentes stock is thermally heavy and the model is not.
(e) A constant 20 °C over the whole floor area against French partial-heating behaviour.

**§6 — Expected range, acceptance test, and a direct verdict on 60.7087.** From §1–§5 only, give the range in
which a net space-heating demand for this stock, this climate and 2023 would be **unsurprising**, both ends
sourced, as a range. Then: state where **60.7087 kWh/m²** falls relative to that range, **with the explicit
caveat that it is pooled over 31 of 530 buildings, 26 of them massing boxes**, and say what would have to be
true for it to be plausible and what would have to be true for it to be wrong. Finally give the checking
protocol: which benchmark, which direction, which corrections, and what deviation counts as *consistent*,
*worth investigating*, *incompatible* — each threshold justified from §1–§5.

### Hard rules

1. **No invented numbers, tables, clauses or URLs.** Source or `UNVERIFIED`.
2. Never present a modelled national average as a measurement; label every row measured / modelled /
   normalised. The DPE is **conventional**, not measured — say so every time you use it.
3. Separate **facts**, **inferences** and **recommendations** with explicit labels.
4. Paywalled or moved source: say so, give the last working reference, never silently substitute.
5. A benchmark that measures a different quantity is more dangerous than no benchmark.

### Acceptance test this report must pass

Every §1 row carries a quantity definition, a floor-area basis, a population and a licence; §2 separates
district-level from city-level evidence; §3 names its degree-day source and base temperature; every §4 entry
gives a sourced chain or says `NOT COMPARABLE`; §5(b) and §5(c) each cite at least one study or say that none
was found; §6's range has both ends sourced, and its statement about 60.7087 repeats the 31-of-530 and
26-massing-box caveats.
