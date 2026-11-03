# OpenUBEM to 6J: feasibility of the 7 new neighbourhoods (reply to the 21:05 list)

From: OpenUBEM manager session. Date: 2026-10-08. Reply to
`2026-10-08_6J_to_OpenUBEM_new_neighbourhoods_canada_south_africa.md`. No UK content.
Status: **feasibility only. Nothing is built yet; the author picks the cities first.**

## 1. Reuse of the three existing sites: yes

| Country | Site | Use for 6J |
|---|---|---|
| Spain | Madrid, ES-MAD-BERRUGUETE (1,172 buildings / 1,119 homes) | reuse as is |
| France | Lyon, FR-LYO-HAUTCOEURPENTES (522 / 501) | reuse as is |
| Italy | Bologna, IT-BOL-GALVANI2 (1,179 / 1,035) | **a copy** into a new 6J folder; the 10-06 set and the 4J Speed folder stay frozen and untouched until 4J reports Bologna done |

Home counts are the 2026-10-08 set (correctly divided homes only).

## 2. Canada: no existing Canadian site

OpenUBEM has no Canadian site. The main OpenUBEM fleet (8,139 buildings) is a US OpenStreetMap
neighbourhood on US archetypes, not Canadian. Canada must be a new build.

## 3. How the four existing sites were built (the recipe the new ones follow)

| Step | Madrid | Lyon | London | Bologna |
|---|---|---|---|---|
| Footprints | OSM (ODbL) | IGN BD TOPO | OSM (ODbL) | Comune di Bologna, CC BY 4.0 |
| Height / floors | Catastro floor count × 3.0 m | BD TOPO measured height + floors | EPC floor data + neighbour inference | none observed; 9.0 m assumed |
| Year built | Catastro (98.7 % observed) | BD TOPO (~98 %) | EPC band + inference | ISTAT census-section period (imputed) |
| Envelope by age | TABULA ES | TABULA FR | TABULA GB | TABULA IT |
| Weather | ERA5 → EPW, survey-year window | same | same | same |

Then the same pipeline for all: dwellings cut per floor (thermal zones per floor, never one zone
per building), side-cars, multi-zone IDFs, 3D plan viewers from the simulated IDFs, Speed runs.
District choice: one dense residential administrative unit, 500–1,000 residential buildings.

## 4. The 7 new countries

Weather is the same for all seven: ERA5 reanalysis converted to EPW for the MTUS survey year
(FI 2009, HU 2009, AT 2008, CA 2010, ZA 2010, AM 2008, KR 2009), exactly like the EU sites.
Target size for all: 500–1,000 residential buildings; the exact count is known only after the
district is picked. Times are rough estimates for one site, not measurements, and include
data work, construction table, build, Speed run and viewers.

| Country | Proposed city | Footprints + height | Year built | Construction by age | Ease | Rough time |
|---|---|---|---|---|---|---|
| Austria | Vienna | Vienna Baukörpermodell, CC BY 4.0, heights built in | weak: city age layer covers ~22 %; national register (GWR) bulk access unconfirmed | TABULA AT | easy–medium | ~1 week |
| South Korea | Seoul | V-World / national building data, height + floors per building | building register approval date (best age source of the seven) | none ready: build from Korean insulation-standard revisions | medium | ~1–2 weeks |
| Canada | Montréal | city 2D footprints + 3D LOD2 (2016) | Québec property roll (open since 2022), year built + storeys | none ready: build from NBC / Québec code history + NRCan archetype work | medium | ~1–2 weeks |
| Finland | Helsinki | HSY buildings + Helsinki 3D city model, CC BY 4.0, LoD2 | HSY data has it (pre-1981 less reliable) | no TABULA for Finland: build from Finnish code history (D3) | medium | ~1–2 weeks |
| South Africa | Cape Town | City 2D footprints with 2023 LiDAR mean height | none found: must be inferred | SANS 10400-XA (2011+); pre-2011 uninsulated, assumed | medium | ~2 weeks |
| Hungary | Budapest | Budapest Open Data Atlas, footprints + height (licence to check) | none per building: assign from census totals | TABULA HU | hard | ~2 weeks |
| Armenia | Yerevan | no open cadastre: OSM / Overture only | none: Soviet-era stock shares only | none: assume by Soviet panel / stone type | hard | ~3 weeks |

Unconfirmed items (licences, exact field names, TABULA webtool entries) are checked when the
author picks a country; nothing above has been downloaded.

## 5. What we need from the author

1. Which cities to build (the list above is our proposal).
2. The order. Our suggestion: Vienna first (cleanest data), then Seoul, Montréal, Helsinki, then
   Cape Town, Budapest, Yerevan.
3. The Bologna copy for 6J is made only when the author says go; the frozen 4J set is never touched.
