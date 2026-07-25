# LayoutAssigner — Figures Explained (plain language)

A simple guide to the 5 comparison figures in this folder (updated 2026-07-23 with the full 12-cell/8,160-building cluster result). For the full technical write-up (data sources, caveats, exact numbers) see [`OpenUBEM_results_LayoutAssigner.md`](OpenUBEM_results_LayoutAssigner.md) §3/§3a.

---

## Figure 1 — Zone-count fidelity

![Zone-count fidelity by mode](layout_assign_vs_modes_zone_fidelity.png)

*How many thermal zones each resolution mode gives a building, for all 28 building types (log scale — split into two panels just so the labels stay readable).*

- `building` / `floor` / `fast_zone` all use one generic rule for every building type; `layout_assign` instead uses the **real, validated** zone count from that building type's actual reference model.
- `layout_assign` is sometimes far more detailed than the generic modes (tall towers, hospitals) and sometimes less — the point isn't "more zones is better", it's that `layout_assign` matches reality instead of guessing.

---

## Figure 2 — Energy use (EUI) comparison, Los Angeles cells

![LA-climate EUI comparison](layout_assign_vs_modes_eui_la.png)

*Updated 2026-07-23: now real annual energy use of `layout_assign` across the full LA fleet (thousands of buildings) vs. the other 4 modes, for the 4 building types where both numbers exist.*

- Previously this compared a single test building; it now compares real fleet medians on both sides.
- The apartment-building bar is affected by a newly-found bug (see Figure 5 below) — read it together with that caveat.

---

## Figure 3 — Simulation warning/error counts (6-building spot-check)

![E-LA-06 diagnostic severity](layout_assign_vs_modes_severity.png)

*How many warning/error messages EnergyPlus produced while simulating each of 6 test buildings (log scale; red numbers are the more serious "severe" errors). This one figure still reflects the small 6-building spot-check, not the full 8,160-building fleet — the fleet-wide success/fail picture is Figure 6 below.*

- Only `MidriseApartment` (the building closest to its original reference size) ran cleanly; the other 5 produced large numbers of warnings because their equipment (transformers, water heaters, HVAC coils) wasn't resized along with the building.

---

## Figure 5 — Full fleet: energy use by mode, all 12 cells (new, 2026-07-23)

![Full cluster EUI comparison](layout_assign_vs_modes_cluster_eui.png)

*The real result of running `layout_assign` on all 8,160 buildings across all 12 city zones, compared to the other 4 modes.*

- The purple bars (`layout_assign`, all building types) are wildly too high in 2 zones (`nyc_suburban`, `la_suburban`) — traced to a bug: a fixed water-heater flow-rate value that should shrink/grow with the building's size but doesn't. It mostly affects apartment buildings and small offices, which happen to be most of the buildings in those 2 zones.
- The black diamonds show the same cells with those 2 affected building types removed — closer to plausible, though a few zones are still high for other, not-yet-fully-explained reasons.
- **Bottom line: `layout_assign`'s energy numbers are not yet trustworthy at fleet scale until this bug is fixed** — the zone-count fidelity (Figure 1) and the "does it run at all" result (Figure 6) are solid; the energy numbers need more work.

---

## Figure 6 — Full fleet: did the simulation even run? (new, 2026-07-23)

![Cluster success/fail](layout_assign_vs_modes_cluster_success.png)

*Out of 8,160 buildings, how many simulated successfully (green) vs. crashed (red), per city zone.*

- 96.65% succeeded fleet-wide (7,887 of 8,160).
- Crashes are concentrated in a handful of building types (large/tall office towers, a specific hospital-style building) that are more common in dense city centres — that's why `nyc_centre` (80.8%) and `la_centre` (86.3%) have the most red.
- 5 of the 12 zones had zero crashes — those zones simply don't contain any of the problem building types in the real data.
