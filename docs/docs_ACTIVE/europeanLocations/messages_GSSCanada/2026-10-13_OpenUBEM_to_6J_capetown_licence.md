# OpenUBEM → 6J — Cape Town (ZA-CPT-WOODSTOCK) licence facts, 2026-10-13

Answer to the five questions relayed by gsscanada-8e. Read-only lookup; nothing was changed and nobody has contacted the City.
Paths are relative to the repo root `C:\Users\o_iseri\Desktop\OpenUBEM`. "NOT KNOWN" = not recorded in our files.

## 1. Which City layer(s), download date, where the height comes from

- **Footprint layer used:** "2D Building Footprints Low Detail" = `https://citymaps.capetown.gov.za/agsext/rest/services/Theme_Based/ODP_SPLIT_12/MapServer/11`. Name set at `scripts/eu22/acquire_capetown.py:29`; the layer is looked up by name across the `ODP_SPLIT_*` services (`acquire_capetown.py:125-141`, `283-298`); the resolved endpoint is recorded at `acquire_capetown.py:667` and in `openubem/outputs/eu02/ZA-CPT-WOODSTOCK/01_source.json` (`source_endpoint`).
- **Not the other layer:** we did **not** use "2D Building Footprint" (ODP_SPLIT_6/MapServer/2), the one marked "All rights reserved" only. NOT KNOWN whether the two layers are the same geometry.
- **Download date:** 2026-10-08, local time 23:48 (footprint pages `openubem/outputs/eu_evidence/EU-22/ZA-CPT-WOODSTOCK/raw/cct_footprints/footprints_page_0000.geojson` onward, file times 23:48:30; study area = bbox of the Official Suburb layer, query `acquire_capetown.py:293-298`). No separate download-date field is stored; the file times are the evidence. The licence text was captured 2026-10-08 (server date header Fri 9 Oct 2026 03:25 UTC).
- **Height:** from the **same footprint layer**, field `BLD_HGHT` (`acquire_capetown.py:309`, `314`). Buildings under 2.0 m are dropped (`MIN_HEIGHT_M`, line 37). Floors = height ÷ 3.0 m (`STOREY_M`, line 38). Our source tag is `CPT_LIDAR_2023` (line 25). The layer also carries `DATA_SRC`, `ACQS_PRD`, `ACQS_MTHD` (line 309). NOT KNOWN: whether `BLD_HGHT` is a "mean" height (we use the field as given; the layer's definition was not read for that point).
- **Counts:** 534 residential buildings, all with measured height; 38 excluded (`outputs_3D/eu_ZA-CPT-WOODSTOCK_data/sources.json`).

## 2. Other City of Cape Town sources, and their licence text

All from the same server (`SERVICE`, `acquire_capetown.py:28`), layer ids resolved by name at run time (`find_layer`, lines 125-136); the ids were **not stored** except where noted.

| Source (layer name) | Used for | Licence text we hold |
|---|---|---|
| Official Suburb (layer id 3, service not stored: `raw/cct_suburbs/layer_meta.json`) | choose the study area (Woodstock, Salt River, Observatory; `NAMED_SUBURBS`, line 36) | NOT KNOWN — metadata never captured |
| Heritage Inventory, Heritage Inventory Objects, Heritage Audit Areas (`HERITAGE_LAYER_NAMES`, line 31; raw pages in `raw/cct_heritage/`, saved 2026-10-08 23:49-23:50) | the construction-period label per building (the "age", not observed) | NOT KNOWN — metadata never captured |
| 2D Building Footprints Low Detail (layer 11) | footprints + height | Captured verbatim: `openubem/outputs/eu_evidence/EU-22/ZA-CPT-WOODSTOCK/licences/CCT_footprints_use_limitation.txt` = the same sentence 6J quotes ("No restrictions on the digital file for non-commercial purposes. All rights reserved. … without permission from the City of Cape Town Geomatics Branch. … acknowledgment … copyright of the CCT."). Raw XML: `licences/layer11_metadata.xml`. |

- No separate LiDAR product was downloaded; the "LiDAR" is only the height inside layer 11.
- **Not City data:** OpenStreetMap (residential tags, roads; Overpass; ODbL 1.0, text in `licences/ODbL-1.0_opendatacommons.html`) and the weather (ERA5 pieces under `openubem/data/weather/raw/era5_capetown_2009_2010/`; Copernicus, not the City).
- Our own licence line in the data (`sources.json`, `acquire_capetown.py:668`): "City of Cape Town: no named licence, metadata use limitation in licences/CCT_footprints_use_limitation.txt; OSM ODbL 1.0".

## 3. Contact with the City / permission

- **No record** of any email, call, reply or permission, in the repo docs or the message folder (searched for `City.Maps` and "Geomatics Branch" next to contact words: no hit).
- The Cape Town plan **forbids** contact: "never email or contact the City" (`docs/docs_ACTIVE/europeanLocations/implementation/PLAN_eu-new-city-ZA-capetown-2026-10-08.md:15`).
- NOT KNOWN: anything the author did outside these files.
- Owner ruling D-EU-160 (2026-10-09, common plan `implementation/PLAN_eu-new-cities-00-common-2026-10-08.md:96`): 6J is the owner's own project, so handing files to 6J is internal use, not redistribution. Conditions kept: non-commercial; no public release of the City footprints without the Geomatics Branch's permission; credit "City of Cape Town".

## 4. What is published or planned for Cape Town

- **Not published:** the Cape Town plan page and 3D viewer were never put on the all-cities page (`prompts/PROMPT_MANAGER_handoff_2026-09-09.md:37`; `messages_GSSCanada/2026-10-12_OpenUBEM_to_6J_six_cities_answers.md:26`). The local page `ALL_CITIES_2026-10-12.html` carries only a Cape Town **status card** (524 of 525 homes correctly divided, status "results", no map, no footprints; its note says the 3D pages stay on this computer). The artifact copy is private by default; whether anyone else has the link: NOT KNOWN.
- 🔴 **Correction to our earlier wording ("stay local"): Cape Town-derived files ARE in the git repository and are pushed.** Repository `origin = https://github.com/orcunkoraliseri/OpenUBEM.git`; `origin/main` contains them (0 commits unpushed). First added in commit 9f00083a1 (2026-10-10). Tracked Cape Town files (from `git ls-files`):
  - footprint data: `openubem/outputs/eu02/ZA-CPT-WOODSTOCK/01_buildings_clean.gpkg`, `02_residential_manifest.gpkg`, `02_excluded_manifest.gpkg`, `01_buildings_clean.schema.json`, `01_source.json`
  - 3D pages: `docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_ZA-CPT-WOODSTOCK_viewer.html`, `outputs_3D/eu_ZA-CPT-WOODSTOCK_data/` (buildings.csv, index.html, sources.json), `plans3D/PLANS_ZA-CPT-WOODSTOCK_2026-10-09.html`, and copies under `openubem/outputs/3D/`
  - models: 1,050 `.idf` files under `openubem/outputs/eu_evidence/EU-11/ZA-CPT-WOODSTOCK_dw_2026-10-09/idfs/` (geometry built from the footprints)
  - results: `docs/docs_ACTIVE/europeanLocations/results/EU22_results_ZA-CPT-WOODSTOCK_2026-10-09_{per_home.csv,per_home.json,summary.csv,summary.json}`
  - (the contents of the viewer/plan HTML were not opened for this answer, so whether they embed footprint coordinates is NOT KNOWN; the gpkg files do.)
- **Is that repo public?** An anonymous call to `https://api.github.com/repos/orcunkoraliseri/OpenUBEM` returns **HTTP 404 on 2026-10-13**, which is what a private repo looks like (or a wrong name). I could not confirm with the `gh` tool (not installed). **The owner must confirm it is private** before the author decides about the City. If it is public, the footprints are already publicly released.
- **Planned:** nothing public for Cape Town; per D-EU-160 the pages stay off any public page.

## 5. Opinion — would per-city aggregate results count as "reproducing" the City's data?

*(Opinion only, not legal advice.)*

- **A neighbourhood total or mean** (e.g. heating kWh/m² for all of Woodstock, no map, no footprints, no building list) does not copy or transmit the City's data file; it is a new number computed from it, plus our own assumptions and OSM data. In my view it is **not** "reproducing" under that wording, and the "no restrictions for non-commercial purposes" sentence points the same way for research use. Credit "City of Cape Town" as the source anyway.
- **Closer to the line:** per-building tables (`per_home.csv`: building ids, areas, heights, per-home results), maps, 3D views, and the geometry-bearing files listed in item 4. Those do reproduce the footprints or something rebuildable into them, and need the City's permission before any public release.
- **Grey area:** floor-area-weighted means over very few buildings; a small area could let a reader back out the footprints. Keep the published unit large (whole neighbourhood, hundreds of buildings).
- If the author wants certainty rather than my reading, the City's own contact is the only authority (City.Maps@capetown.gov.za, as 6J found). Nobody here sends it.
