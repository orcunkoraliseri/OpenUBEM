# Comparison figures — provenance & data basis

This folder holds the cross-cell EUI comparison figures. **Which model run each figure is
based on is recorded below**, because the model changed substantially between Phase-D2 and
Phase-E and not every figure could be regenerated for Phase-E.

- **Phase-E** (current physical baseline) — full EnergyPlus re-simulation; all 9 end-uses
  (incl. fans, pumps, DHW, cooking, refrigeration) physically modelled; the V16 reconstruction
  overlay is **retired**. Results: [`docs/.../results/phaseE/`](../../../docs/docs_VALIDATION/validations/overAll/results/phaseE/).
- **Phase-D2** (prior baseline) — blanket PTAC HVAC + post-hoc V16 service-load
  *reconstruction* overlay. Results: [`docs/.../results/phaseD2/`](../../../docs/docs_VALIDATION/validations/overAll/results/phaseD2/).

Background on the shift and why Phase-E scores lower against measured anchors:
[methodology §7](../../../docs/docs_EXPLANATION/simulated_vs_reconstructed_methodology.md) ·
[REPORT_phaseE_final](../../../docs/docs_ACTIVE/hvac-ServiceLoads/REPORT_phaseE_final.md) ·
[INVESTIGATION (why D2 looked closer)](../../../docs/docs_ACTIVE/hvac-ServiceLoads/validation-investigate/INVESTIGATION_phaseD2_vs_phaseE_why_D2_closer.md).

## Based on Phase-E runs ✅

| Figure | What it shows | Data source | Regenerated |
|---|---|---|---|
| `eui_vs_cbecs_reference.png` | Per-cell **mean** modeled EUI vs CBECS-2018 region reference | [phaseE results](../../../docs/docs_VALIDATION/validations/overAll/results/phaseE/) (8,160 bldgs, all 9 end-uses) | 2026-06-28 |
| `eui_cross_cell_summary.png` | Per-cell building EUI **distributions** (boxplots, ranked by median) | [phaseE results](../../../docs/docs_VALIDATION/validations/overAll/results/phaseE/) | 2026-06-28 |
| `phaseE_city_comparison.png` | City-Overall median: Phase-E vs Phase-D2 vs measured anchor | [phaseE results](../../../docs/docs_VALIDATION/validations/overAll/results/phaseE/) | 2026-06-27 |
| `phaseE_enduse_breakdown.png` | Stacked **9-end-use** median per city (the Phase-E successor to `eui_sim_vs_reconstructed.png`) | [phaseE results](../../../docs/docs_VALIDATION/validations/overAll/results/phaseE/) | 2026-06-27 |
| `phaseE_cbecs_scatter.png` | Archetype-level Phase-E mean vs CBECS PBA reference, per region | [phaseE results](../../../docs/docs_VALIDATION/validations/overAll/results/phaseE/) | 2026-06-27 |

## Historical — NOT Phase-E ⚠️

| Figure | Basis | Data source | Why not Phase-E |
|---|---|---|---|
| `eui_overview_grid.png` | Phase-D2 + reconstruction (2026-06-26) | [phaseD2 results](../../../docs/docs_VALIDATION/validations/overAll/results/phaseD2/) | This is a **footprint-polygon map**. Phase-E results store building **centroids only** (no polygons), and the runtime footprint tree (`01_buildings.gpkg`) is not retained locally. The Phase-E EUI *values* exist; rebuilding the polygon map would require re-exporting footprints. |
| `eui_sim_vs_reconstructed.png` | Phase-D2 + V16 reconstruction (2026-06-26) | [phaseD2 results](../../../docs/docs_VALIDATION/validations/overAll/results/phaseD2/) | **Obsolete under Phase-E**: the "reconstructed" overlay was retired (service loads are now physically simulated), so there is no Phase-E counterpart. Kept as a record of the reconstruction methodology. Phase-E successor: `phaseE_enduse_breakdown.png`. See [methodology §7](../../../docs/docs_EXPLANATION/simulated_vs_reconstructed_methodology.md). |

## Regenerating the Phase-E figures

The two regenerable comparison figures read the phased results tree with reconstruction off:

```sh
# from repo root, with OPENUBEM_PHASED_SUBDIR=phaseE and OPENUBEM_RECONSTRUCT_SERVICE_LOADS=0,
# call plot_eui_vs_reference() and plot_cross_cell_eui() (they read total_eui_kwh_m2 directly).
```

⚠️ Do **not** run `python scripts/render_plots.py --only comparison` against Phase-E: it would
also overwrite `eui_sim_vs_reconstructed.png` with an empty chart (no rows satisfy
`reconstruction_applied == True` when the overlay is off). Regenerate only the two valid
figures.
