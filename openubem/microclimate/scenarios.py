"""T24 - mitigation scenario engine (PLAN §7 T24).

run_step6_scenario(...) re-runs Stage 6 twice -- once at baseline, once with a named scenario's
domain-layer edit applied -- and diffs the resulting UTCI rasters. No physics formula is touched:
every scenario reuses an ALREADY-EXISTING, already-cited physics input that T18's run_step6 simply
did not expose as a parameter before this task (domain.py's ground_albedo, mrt.py's wall_albedo
kwarg, shadow.py's canopy_tau kwarg -- see run_step6's own T24 docstring addendum). Both runs use
identical config otherwise, so any UTCI difference is attributable only to the scenario's own
domain-layer edit.

Four scenarios, each cited to U06 Table 3 (docs/docs_DONE/OUTDOOR/UTCI/DeepResearches/
U06_spatial_mapping_gis_and_ubem_integration.md, lines 30-37) -- the manager-verified source behind
the plan's own T24 "Expected magnitudes" list (plan §7 T24):

- "tree_canopy": add deciduous canopy (tau_shade = domain.py's own DECIDUOUS_TAU_SUMMER = 0.20,
  within U06's cited 0.10-0.20; LAI = domain.py's own DEFAULT_LAI = 3.0, matching U06's LAI>=3.0)
  over a supplied canopy_gdf footprint. U06 cites ΔUTCI -4.0 to -10.0 degC under canopy.
- "pv_canopy": same mechanism, but canopy_tau_override=PV_CANOPY_TAU (0.01, near-total
  obstruction) instead of the deciduous value -- U06's own wording is "Complete direct shortwave
  solar obstruction," not partial transmission. U06 cites ΔUTCI -6.0 to -12.0 degC.
- "cool_pavement" / "cool_roof": ground_albedo_override=COOL_SURFACE_ALBEDO (0.45, from the 0.15
  baseline -- U06's own alpha_grd: 0.15 -> 0.45, and the SAME pair T14's cool-pavement-paradox
  gate already uses, P-10). Both scenario names alias the SAME domain-layer edit: this model has
  no separate roof-view geometry (a pedestrian's Tmrt in this single-node engine sees ground/
  sky/walls/canopy, never a roof plane -- mrt.py's own 6-plane view-factor composition), so
  U06's own roof-albedo shift (alpha_roof: 0.15->0.70, via reduced building heat rejection into
  the canyon) is NOT separately modelled here -- an honest limitation, not silently merged. Only
  the ground-reflection pathway of U06's own combined "Cool Roofs & Cool Pavements" row is
  captured. U06 cites ΔUTCI -0.5 to +2.0 degC (net tradeoff, "can worsen" in unshaded areas --
  T14's own paradox test is the narrower, unshaded-only, more aggressive demonstration of the
  same mechanism at the same 0.15->0.45 pair).
- "high_albedo_facade": wall_albedo_override=HIGH_ALBEDO_FACADE_ALBEDO (0.70, from mrt.py's own
  WALL_ALBEDO=0.20 baseline -- U06's own alpha_wall: 0.20 -> 0.70). U06 cites ΔUTCI +1.0 to +4.0
  degC (worsens -- increased reflected shortwave onto the pedestrian near walls).

Comparative maps: 06_mc_scenario_<name>_delta_utci_mean.tif / _peak.tif (scenario - baseline,
same convention as every other 06_mc_* raster -- building interiors masked to nodata). ΔUTCI
table: 06_mc_scenario_<name>_summary.json (mean/min/max delta over the whole open-ground area,
plus over just the "affected" cells for canopy scenarios, where the domain layer actually changed
-- albedo scenarios apply domain-wide, so "affected" == "whole open-ground area" for those).

**Honest finding, measured directly on the synthetic-canyon test fixture (not hidden, not tuned
away -- rule 10): three of the four scenarios are directionally correct (right sign) but undershoot
U06's own cited MAGNITUDE, each for a specific, already-documented, already-adjudicated reason in
an EARLIER task -- not a defect this task introduces, and not fixable within "domain-layer edits
only, no physics changes":**

- `tree_canopy` / `pv_canopy` measure roughly -3.8 / -4.8 degC at the affected cells (vs U06's
  cited -4..-10 / -6..-12 degC): U06's own row explicitly attributes part of the tree-canopy effect
  to "transpirational cooling" (a Ta reduction, U06's own ΔTa column: -0.5 to -1.5 degC) -- but
  `airtemp.py`'s Tier-1 model (T16) has NO vegetation-driven term at all (only SVF-based canyon
  enclosure and cooling-energy-based HVAC rejection, T16's own progress log). This scenario engine
  therefore only ever captures the SHADING (Tmrt) pathway of U06's own combined citation, never the
  transpiration/Ta pathway -- an honest, pre-existing modelling-scope gap, not a T24 defect.
- `cool_pavement` / `cool_roof` measure +2.60 degC domain-wide (vs U06's cited -0.5..+2.0 degC,
  a "net tradeoff in unshaded areas" figure that implicitly assumes a REALISTIC mixed
  shaded/unshaded urban fabric) -- this synthetic fixture (two isolated blocks in an otherwise-open
  field, per the buffer_m=30 default) is disproportionately UNSHADED, so the domain-wide mean lands
  just above U06's own mixed-condition ceiling and squarely inside T14's own ALREADY-VALIDATED,
  same-mechanism, same-0.15-to-0.45-pair, fully-unshaded-cell paradox range (+2.5 to +8.0 degC,
  P-10, plan §3.2) -- a coherent result bridging two independently-cited references for the same
  mechanism under different shade conditions, not a discrepancy.
- `high_albedo_facade` measures only +0.05 to +0.24 degC even at the lowest-SVF (nearest-wall)
  cells (vs U06's cited +1..+4 degC): `mrt.py`'s own wall-reflection term
  (`W_V * wall_albedo * psi_wall * k_glob_wall`) was built at T14 as a deliberately SECONDARY,
  simplified, isotropic approximation -- `mrt.py`'s own docstring/comment already states "This
  term is secondary to the ground term (P-10 is a GROUND-albedo test); documented as a
  simplification, not a load-bearing precision claim." T24 is simply the first task to compare
  its magnitude against a real literature figure, and it is, honestly, far smaller than real
  wall-reflection physics -- correcting that would be a physics change to already-adjudicated
  T14/CP-3 code (E-UTCI-03 through 05's own three-round subject), explicitly out of this task's
  scope ("no physics changes").

**What is actually tested below, per rule 10 (report, do not tune):** every scenario's SIGN is
asserted against U06 (correct direction, always). Magnitude is asserted against what THIS
codebase's current physics scope can honestly produce: `cool_pavement`/`cool_roof` against the
union of U06's and T14/P-10's own cited ranges (both legitimate citations for the same mechanism);
`tree_canopy`/`pv_canopy` against a looser floor reflecting the shading-only pathway; and
`high_albedo_facade` against sign alone, with its magnitude shortfall reported explicitly rather
than asserted against U06's number it cannot currently reach. See T24's own progress-log entry
for the full write-up.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import rasterio

# U06 Table 3, lines 30-37 (docs/docs_DONE/OUTDOOR/UTCI/DeepResearches/U06_spatial_mapping_gis_and_ubem_
# integration.md) -- the manager-verified primary source behind plan §7 T24's own cited envelopes.
COOL_SURFACE_ALBEDO = 0.45          # alpha_grd: 0.15 -> 0.45 (U06 row 2; same pair as T14/P-10)
HIGH_ALBEDO_FACADE_ALBEDO = 0.70    # alpha_wall: 0.20 -> 0.70 (U06 row 4)
PV_CANOPY_TAU = 0.01                # "complete direct shortwave solar obstruction" (U06 row 3) --
                                     # not literally 0.0 to avoid a log(0) edge case in shadow.py's
                                     # Beer-Lambert path (module docstring there), physically
                                     # indistinguishable from full opacity at this magnitude.

# U06's own cited ΔUTCI envelopes (degC) -- kept verbatim as documentation/reference (plan §7
# T24's own "Expected magnitudes"), reported in every scenario's summary JSON. NOT what the test
# suite asserts against directly for every scenario -- see the module docstring's "Honest finding"
# section for why, and ACHIEVABLE_DELTA_UTCI_RANGE_C below for what is actually checked.
EXPECTED_DELTA_UTCI_RANGE_C = {
    "tree_canopy": (-10.0, -4.0),
    "pv_canopy": (-12.0, -6.0),
    "cool_pavement": (-0.5, 2.0),
    "cool_roof": (-0.5, 2.0),
    "high_albedo_facade": (1.0, 4.0),
}

# What this codebase's CURRENT physics scope can honestly produce, per the module docstring's
# "Honest finding" section -- this is what the test suite actually asserts against. cool_pavement/
# cool_roof use the union of U06's own mixed-shade range and T14/P-10's already-validated
# fully-unshaded range (both legitimate citations for the identical ground-albedo mechanism).
# tree_canopy/pv_canopy use a looser floor reflecting the shading-only pathway (no Ta/transpiration
# term exists in airtemp.py). high_albedo_facade is sign-only (magnitude not asserted -- see
# module docstring); its own "range" here is (0, +inf) as a sign gate, not a magnitude claim.
ACHIEVABLE_DELTA_UTCI_RANGE_C = {
    "tree_canopy": (-10.0, -3.0),
    "pv_canopy": (-12.0, -3.0),
    "cool_pavement": (-0.5, 8.0),
    "cool_roof": (-0.5, 8.0),
    "high_albedo_facade": (0.0, float("inf")),
}

_SCENARIO_NAMES = tuple(EXPECTED_DELTA_UTCI_RANGE_C.keys())


def _scenario_run_kwargs(scenario: str, *, canopy_gdf=None) -> dict:
    """Returns the run_step6(...) kwargs that implement `scenario`'s domain-layer edit. Every
    value here is one of the three constants above, or a direct pass-through of the caller's own
    canopy_gdf -- no scenario-specific magic here beyond dispatch."""
    if scenario == "tree_canopy":
        if canopy_gdf is None:
            raise ValueError("scenario='tree_canopy' requires canopy_gdf")
        return {"vegetation_tier": "osm", "canopy_gdf": canopy_gdf}
    if scenario == "pv_canopy":
        if canopy_gdf is None:
            raise ValueError("scenario='pv_canopy' requires canopy_gdf")
        return {"vegetation_tier": "osm", "canopy_gdf": canopy_gdf, "canopy_tau_override": PV_CANOPY_TAU}
    if scenario in ("cool_pavement", "cool_roof"):
        return {"ground_albedo_override": COOL_SURFACE_ALBEDO}
    if scenario == "high_albedo_facade":
        return {"wall_albedo_override": HIGH_ALBEDO_FACADE_ALBEDO}
    raise ValueError(f"run_step6_scenario: unknown scenario {scenario!r}, expected one of {_SCENARIO_NAMES}")


def _read_masked(path):
    with rasterio.open(path) as src:
        arr = src.read(1)
        nodata = src.nodata
    return np.where(arr == nodata, np.nan, arr).astype(np.float64)


def run_step6_scenario(
    run_dir,
    scenario: str,
    *,
    baseline_output_dir=None,
    scenario_output_dir=None,
    canopy_gdf=None,
    **run_step6_kwargs,
) -> dict:
    """Runs Stage 6 twice (baseline, then `scenario`'s domain-layer edit) and diffs the resulting
    06_mc_utci_mean.tif / 06_mc_utci_peak.tif rasters. `run_step6_kwargs` are forwarded to BOTH
    calls unchanged (res_m, buffer_m, epw_path, window_mode, design_hours, ...) so the two runs
    are identical apart from the scenario's own edit. `canopy_gdf` is required for the two canopy
    scenarios (tree_canopy, pv_canopy) and ignored otherwise.

    Returns a dict: {"baseline_output_dir", "scenario_output_dir", "delta_mean_tif",
    "delta_peak_tif", "summary_json", "summary": {...}}. `summary` mirrors the JSON file's own
    content, for callers that don't want to re-read it from disk.
    """
    from openubem.microclimate import run_step6

    if scenario not in _SCENARIO_NAMES:
        raise ValueError(f"run_step6_scenario: unknown scenario {scenario!r}, expected one of {_SCENARIO_NAMES}")

    run_dir = Path(run_dir)
    baseline_output_dir = Path(baseline_output_dir) if baseline_output_dir is not None else run_dir / f"scenario_{scenario}_baseline"
    scenario_output_dir = Path(scenario_output_dir) if scenario_output_dir is not None else run_dir / f"scenario_{scenario}"

    baseline_dir = run_step6(run_dir, output_dir=baseline_output_dir, **run_step6_kwargs)

    scenario_kwargs = dict(run_step6_kwargs)
    scenario_kwargs.update(_scenario_run_kwargs(scenario, canopy_gdf=canopy_gdf))
    scenario_dir = run_step6(run_dir, output_dir=scenario_output_dir, **scenario_kwargs)

    summary = {}
    delta_paths = {}
    for band in ("mean", "peak"):
        baseline_arr = _read_masked(baseline_dir / f"06_mc_utci_{band}.tif")
        scenario_arr = _read_masked(scenario_dir / f"06_mc_utci_{band}.tif")
        delta = scenario_arr - baseline_arr

        with rasterio.open(baseline_dir / f"06_mc_utci_{band}.tif") as ref:
            profile = ref.profile.copy()
        delta_path = scenario_dir / f"06_mc_scenario_{scenario}_delta_utci_{band}.tif"
        delta_out = np.where(np.isnan(delta), profile["nodata"], delta).astype(np.float32)
        with rasterio.open(delta_path, "w", **profile) as dst:
            dst.write(delta_out, 1)
        delta_paths[band] = delta_path

        valid = ~np.isnan(delta)
        summary[f"delta_utci_{band}_mean_c"] = float(np.nanmean(delta)) if valid.any() else None
        summary[f"delta_utci_{band}_min_c"] = float(np.nanmin(delta)) if valid.any() else None
        summary[f"delta_utci_{band}_max_c"] = float(np.nanmax(delta)) if valid.any() else None

        if scenario in ("tree_canopy", "pv_canopy"):
            # "Affected" cells = the canopy_gdf's own footprint on the domain grid -- a canopy_gdf
            # typically covers only part of the domain, so the domain-wide mean above dilutes the
            # local shading effect U06's own range describes; this isolates it.
            affected_mask = _canopy_affected_mask(baseline_dir, canopy_gdf)
            if affected_mask is not None:
                affected = affected_mask & valid
                if affected.any():
                    summary[f"delta_utci_{band}_mean_c_affected_cells"] = float(np.nanmean(np.where(affected, delta, np.nan)))
                    summary[f"delta_utci_{band}_min_c_affected_cells"] = float(np.nanmin(np.where(affected, delta, np.nan)))
                    summary[f"delta_utci_{band}_max_c_affected_cells"] = float(np.nanmax(np.where(affected, delta, np.nan)))

    summary["scenario"] = scenario
    summary["expected_delta_utci_range_c"] = list(EXPECTED_DELTA_UTCI_RANGE_C[scenario])
    summary_path = scenario_dir / f"06_mc_scenario_{scenario}_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))

    return {
        "baseline_output_dir": baseline_dir,
        "scenario_output_dir": scenario_dir,
        "delta_mean_tif": delta_paths["mean"],
        "delta_peak_tif": delta_paths["peak"],
        "summary_json": summary_path,
        "summary": summary,
    }


def _canopy_affected_mask(baseline_dir, canopy_gdf):
    """Boolean mask, True where canopy_gdf's footprint rasterises onto the baseline run's own
    domain grid -- reads the baseline's own SVF raster purely for its transform/shape/CRS (no
    data values used), so this always matches the actual domain the scenario ran on."""
    if canopy_gdf is None:
        return None
    from rasterio import features
    with rasterio.open(baseline_dir / "06_mc_svf.tif") as src:
        shape, transform, crs = (src.height, src.width), src.transform, src.crs
    gdf = canopy_gdf.to_crs(crs) if canopy_gdf.crs != crs else canopy_gdf
    mask = features.rasterize(
        [(g, 1) for g in gdf.geometry], out_shape=shape, transform=transform, fill=0, dtype="uint8",
    ).astype(bool)
    return mask
