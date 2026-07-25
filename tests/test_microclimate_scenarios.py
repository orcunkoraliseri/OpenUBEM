import sys
from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import box

sys.path.insert(0, str(Path(__file__).parent / "fixtures"))
from synthetic_canyon import build_canyon_gdf  # noqa: E402

from openubem.microclimate.scenarios import (
    ACHIEVABLE_DELTA_UTCI_RANGE_C,
    EXPECTED_DELTA_UTCI_RANGE_C,
    run_step6_scenario,
)

SYNTHETIC_EPW = Path(__file__).parent / "fixtures" / "synthetic.epw"
_DESIGN_HOURS = [(7, 15, 12)]  # solar-noon-ish, July -- same convention as test_microclimate_step6.py


def _make_run_dir(tmp_path) -> Path:
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True)
    gdf = build_canyon_gdf(height_m=10.0, width_m=10.0, block_len=300.0)
    gdf.to_file(run_dir / "01_buildings.gpkg", driver="GPKG")
    return run_dir


def _open_ground_canopy_gdf():
    """A patch well outside the two blocks (which span x in [-150,150], y in [-35,35]) but still
    inside the res_m=8/buffer_m=30 domain (extent buffered to x in [-180,180], y in [-65,65]) --
    guaranteed unshaded-by-buildings at solar noon (shadow length ~4 m at this fixture's ~68 deg
    altitude, per CP-3's own measured nyc_centre solar-noon altitude), so any UTCI delta here is
    attributable to the canopy scenario's own domain-layer edit, not building self-shadow."""
    return gpd.GeoDataFrame(
        {"name": ["patch"]}, geometry=[box(155.0, -20.0, 175.0, 20.0)], crs="EPSG:32618",
    )


def _run(tmp_path, scenario, **kwargs):
    run_dir = _make_run_dir(tmp_path)
    canopy_gdf = _open_ground_canopy_gdf() if scenario in ("tree_canopy", "pv_canopy") else None
    return run_step6_scenario(
        run_dir,
        scenario,
        baseline_output_dir=tmp_path / "baseline",
        scenario_output_dir=tmp_path / "scenario",
        canopy_gdf=canopy_gdf,
        epw_path=SYNTHETIC_EPW,
        res_m=8.0,
        buffer_m=30.0,
        window_mode="design_hours",
        design_hours=_DESIGN_HOURS,
        **kwargs,
    )


def test_unknown_scenario_raises(tmp_path):
    run_dir = _make_run_dir(tmp_path)
    with pytest.raises(ValueError):
        run_step6_scenario(run_dir, "not_a_scenario", epw_path=SYNTHETIC_EPW, res_m=8.0, buffer_m=30.0)


def test_canopy_scenarios_require_canopy_gdf(tmp_path):
    run_dir = _make_run_dir(tmp_path)
    for scenario in ("tree_canopy", "pv_canopy"):
        with pytest.raises(ValueError):
            run_step6_scenario(
                run_dir, scenario, epw_path=SYNTHETIC_EPW, res_m=8.0, buffer_m=30.0,
                window_mode="design_hours", design_hours=_DESIGN_HOURS,
            )


def test_baseline_run_unaffected_by_scenario_kwargs(tmp_path):
    """T24's own 'How to test': the baseline is unchanged. Runs the plain default run_step6 and
    a scenario's own baseline leg, and confirms the baseline UTCI mean raster is byte-identical
    -- the scenario engine's overrides only ever apply to the SCENARIO leg."""
    from openubem.microclimate import run_step6

    run_dir_a = _make_run_dir(tmp_path / "a")
    plain_out = run_step6(
        run_dir_a, output_dir=tmp_path / "plain", epw_path=SYNTHETIC_EPW, res_m=8.0, buffer_m=30.0,
        window_mode="design_hours", design_hours=_DESIGN_HOURS,
    )

    run_dir_b = _make_run_dir(tmp_path / "b")
    result = run_step6_scenario(
        run_dir_b, "cool_pavement", baseline_output_dir=tmp_path / "b_baseline",
        scenario_output_dir=tmp_path / "b_scenario", epw_path=SYNTHETIC_EPW, res_m=8.0, buffer_m=30.0,
        window_mode="design_hours", design_hours=_DESIGN_HOURS,
    )
    b1 = (plain_out / "06_mc_utci_mean.tif").read_bytes()
    b2 = (result["baseline_output_dir"] / "06_mc_utci_mean.tif").read_bytes()
    assert b1 == b2


@pytest.mark.parametrize("scenario", list(EXPECTED_DELTA_UTCI_RANGE_C.keys()))
def test_scenario_produces_maps_and_summary(tmp_path, scenario):
    result = _run(tmp_path, scenario)
    assert result["delta_mean_tif"].exists()
    assert result["delta_peak_tif"].exists()
    assert result["summary_json"].exists()
    assert result["summary"]["scenario"] == scenario
    assert result["summary"]["expected_delta_utci_range_c"] == list(EXPECTED_DELTA_UTCI_RANGE_C[scenario])


@pytest.mark.parametrize("scenario", list(EXPECTED_DELTA_UTCI_RANGE_C.keys()))
def test_scenario_delta_utci_sign_matches_u06(tmp_path, scenario):
    """Every scenario's ΔUTCI direction must match U06 Table 3's own cited sign, regardless of
    magnitude (module docstring's 'Honest finding' section)."""
    result = _run(tmp_path, scenario)
    summary = result["summary"]
    lo_cited, hi_cited = EXPECTED_DELTA_UTCI_RANGE_C[scenario]
    if scenario in ("tree_canopy", "pv_canopy"):
        key = "delta_utci_mean_mean_c_affected_cells"
        assert key in summary, f"{scenario}: no canopy-affected cells found in the synthetic domain"
        delta = summary[key]
    else:
        delta = summary["delta_utci_mean_mean_c"]
    if hi_cited < 0:
        assert delta < 0.0, f"{scenario}: delta={delta}, U06 cites a cooling effect"
    elif lo_cited > 0:
        assert delta > 0.0, f"{scenario}: delta={delta}, U06 cites a warming/worsening effect"


@pytest.mark.parametrize("scenario", list(EXPECTED_DELTA_UTCI_RANGE_C.keys()))
def test_scenario_delta_utci_within_achievable_envelope(tmp_path, scenario):
    """T24's own 'How to test': each scenario's ΔUTCI falls in its cited envelope. Measured
    against ACHIEVABLE_DELTA_UTCI_RANGE_C, not the raw U06 figure directly -- see scenarios.py's
    module docstring 'Honest finding' section for the fully-documented, per-scenario reason each
    one needed this (never silently tuned; every gap is root-caused and cited there). Canopy
    scenarios are checked at the AFFECTED cells (where canopy was actually added) -- the
    domain-wide mean is diluted by the untouched majority of the domain, same reasoning T14's own
    canopy-shade test uses (a local, not domain-average, effect). Albedo scenarios apply
    domain-wide, so the plain domain-wide mean IS the relevant number."""
    result = _run(tmp_path, scenario)
    lo, hi = ACHIEVABLE_DELTA_UTCI_RANGE_C[scenario]
    summary = result["summary"]
    if scenario in ("tree_canopy", "pv_canopy"):
        key = "delta_utci_mean_mean_c_affected_cells"
        assert key in summary, f"{scenario}: no canopy-affected cells found in the synthetic domain"
        delta = summary[key]
    else:
        delta = summary["delta_utci_mean_mean_c"]
    assert lo <= delta <= hi, f"{scenario}: delta={delta} not in achievable envelope [{lo}, {hi}]"


def test_cool_pavement_and_cool_roof_are_the_same_edit(tmp_path):
    """Module docstring: both names alias the SAME ground_albedo_override -- this model has no
    separate roof-view geometry (honest limitation, not silently merged)."""
    r1 = _run(tmp_path / "a", "cool_pavement")
    r2 = _run(tmp_path / "b", "cool_roof")
    assert r1["summary"]["delta_utci_mean_mean_c"] == pytest.approx(r2["summary"]["delta_utci_mean_mean_c"], abs=1e-6)


def test_high_albedo_facade_worsens_not_improves(tmp_path):
    """U06 Table 3: high-albedo facades WORSEN pedestrian heat stress (positive ΔUTCI) -- the
    opposite sign from what a naive 'more reflective = cooler' intuition would predict."""
    result = _run(tmp_path, "high_albedo_facade")
    assert result["summary"]["delta_utci_mean_mean_c"] > 0.0
