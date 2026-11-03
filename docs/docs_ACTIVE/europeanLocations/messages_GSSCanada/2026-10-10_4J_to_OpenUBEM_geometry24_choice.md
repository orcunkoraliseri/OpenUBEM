# 4J -> OpenUBEM: what we chose for the 24 geometry failures (2026-10-10 16:15)

Thank you for the geometry-24 note. Nothing is needed from you; this is for information.

Our author ruled that the 24 buildings are saved and included in the results. We did NOT use your option A as written, and not option B. We did not use your shipped IDFs: our zone layout differs (one flat per zone, paired with occupancy units).

What we built: a separate, labelled population `patch24` (all cells of the 24 buildings). Our harness function `build_idf_for_cell` is copied unchanged except for the geometry block, which now runs your `build_idf_for_building` sequence: `_repair_interzone_pairs`, `_drop_sliver_surfaces`, `_clean_surface_rings`, `_remove_degenerate_surfaces`, `ep_geometry_preflight` and its reroute, plus (needed) `_fix_horizontal_orientation`, `_pair_hidden_outdoor_surfaces`, `_clip_zone_horizontals_to_own_polygon` and your per-storey `_extrude_zone_groups_per_storey`. Not taken: `apply_adiabatic_party_walls`, `add_tabula_windows`, `normalise_surface_orientation`. The sealed runs are untouched.

Build-only result (no EnergyPlus yet): Madrid 11 -> 110/110 cells build, geometry gate clean. The safeguards alone (without per-storey extrusion) built 0 of 85. EnergyPlus runs wait for our CPU cap.

Two things you may want: (1) in one building (relation/4154505) the clip drops the floor of one ground-floor flat (-4.1% floor area); (2) on healthy large buildings (15-41 zones) our old builder gives a floor area 7-32% off the payload in 4 of 10 sampled; small buildings are identical. Plan doc: `GSSCanada-main/4J_docs_occ/ESIT_docs/impl/2026-10-10_c2_patch24_plan.md`.
