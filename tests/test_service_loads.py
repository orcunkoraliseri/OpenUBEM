"""Unit + integration tests for openubem.results.service_loads (T07 + T12)."""
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_AUSTIN_CENTRE_GPKG = (
    _REPO_ROOT / "runtime" / "ubem_validation" / "cases" / "austin_centre" / "results" / "05_results.gpkg"
)
_OUT_CSV = _REPO_ROOT / "docs" / "validations" / "overAll" / "results" / "r7_service_loads.csv"

# ---------------------------------------------------------------------------
# LargeOffice hand-calc fixture
# heating=30, cooling=14, lighting=12, equip=27, total=83, status=success
# modeled_frac = 0.30+0.14+0.12+0.27 = 0.83
# E_total_est  = 83/0.83 = 100.0
# vent_fans=11.0  pumps=3.5  swh_dhw=1.5  refrig=0.5  cooking_other=0.5
# total_recon = 83 + 17 = 100.0
# ---------------------------------------------------------------------------
_LO_ROW = {
    "osm_id": "way/1",
    "archetype_id": "LargeOffice",
    "heating_eui_kwh_m2": 30.0,
    "cooling_eui_kwh_m2": 14.0,
    "lighting_eui_kwh_m2": 12.0,
    "equipment_eui_kwh_m2": 27.0,
    "total_eui_kwh_m2": 83.0,
    "simulation_status": "success",
}

_EXPECTED_LO = {
    "reconstruction_applied": True,
    "archetype_mapped_to": "large_office",
    "reconstruction_basis": "table4_fraction_split",
    "vent_fans_eui_recon_kwh_m2": 11.0,
    "pumps_eui_recon_kwh_m2": 3.5,
    "swh_dhw_eui_recon_kwh_m2": 1.5,
    "refrig_eui_recon_kwh_m2": 0.5,
    "cooking_other_eui_recon_kwh_m2": 0.5,
    "total_eui_reconstructed_kwh_m2": 100.0,
}


# ---------------------------------------------------------------------------
# T01/T02: coefficients load and sum
# ---------------------------------------------------------------------------

class TestCoefficientsLoadAndSum:
    def test_load_returns_two_keys(self):
        from openubem.results.service_loads import load_coefficients
        data = load_coefficients()
        assert set(data.keys()) == {"fractions", "archetype_map"}

    def test_eleven_archetypes_in_fractions(self):
        from openubem.results.service_loads import load_coefficients
        data = load_coefficients()
        assert len(data["fractions"]) == 11

    def test_each_archetype_sums_to_one(self):
        from openubem.results.service_loads import load_coefficients
        data = load_coefficients()
        for key, fracs in data["fractions"].items():
            total = sum(fracs.values())
            assert abs(total - 1.0) < 1e-3, f"'{key}' sums to {total}"

    def test_nine_end_uses_per_archetype(self):
        from openubem.results.service_loads import load_coefficients
        data = load_coefficients()
        expected_keys = {"space_heat", "space_cool", "vent_fans", "pumps", "swh_dhw",
                         "lighting", "equip_plug", "refrig", "cooking_other"}
        for key, fracs in data["fractions"].items():
            assert set(fracs.keys()) == expected_keys, f"'{key}' has wrong end-use keys"

    def test_archetype_map_covers_known_ids(self):
        from openubem.results.service_loads import load_coefficients
        data = load_coefficients()
        amap = data["archetype_map"]
        required = {"LargeOffice", "SmallOffice", "MidriseApartment", "FullServiceRestaurant",
                    "PrimarySchool", "MediumOffice", "HighriseApartment", "QuickServiceRestaurant",
                    "RetailStandalone", "Courthouse", "TallBuilding", "SuperTallBuilding",
                    "OpenUBEMUnknown"}
        for archetype_id in required:
            assert archetype_id in amap, f"{archetype_id!r} missing from archetype_map"

    def test_bad_json_raises_value_error(self, tmp_path):
        import json
        from openubem.results.service_loads import load_coefficients
        bad = {"fractions": {"bad_arch": {"a": 0.5, "b": 0.3}}, "archetype_map": {}}
        p = tmp_path / "bad.json"
        p.write_text(json.dumps(bad))
        with pytest.raises(ValueError, match="bad_arch"):
            load_coefficients(p)


# ---------------------------------------------------------------------------
# T03: single-building reconstruction
# ---------------------------------------------------------------------------

class TestReconstructLargeOfficeMatchesHandCalc:
    def _run(self):
        from openubem.results.service_loads import load_coefficients, reconstruct_building
        coeffs = load_coefficients()
        return reconstruct_building(_LO_ROW, coeffs)

    def test_reconstruction_applied_true(self):
        assert self._run()["reconstruction_applied"] is True

    def test_archetype_mapped_to(self):
        assert self._run()["archetype_mapped_to"] == "large_office"

    def test_vent_fans(self):
        assert math.isclose(self._run()["vent_fans_eui_recon_kwh_m2"], 11.0, rel_tol=1e-6)

    def test_pumps(self):
        assert math.isclose(self._run()["pumps_eui_recon_kwh_m2"], 3.5, rel_tol=1e-6)

    def test_swh_dhw(self):
        assert math.isclose(self._run()["swh_dhw_eui_recon_kwh_m2"], 1.5, rel_tol=1e-6)

    def test_refrig(self):
        assert math.isclose(self._run()["refrig_eui_recon_kwh_m2"], 0.5, rel_tol=1e-6)

    def test_cooking_other(self):
        assert math.isclose(self._run()["cooking_other_eui_recon_kwh_m2"], 0.5, rel_tol=1e-6)

    def test_total_recon(self):
        assert math.isclose(self._run()["total_eui_reconstructed_kwh_m2"], 100.0, rel_tol=1e-6)

    def test_total_recon_equals_e_total_est(self):
        # For LargeOffice with these values, E_total_est == 100.0 == total_recon
        result = self._run()
        assert math.isclose(result["total_eui_reconstructed_kwh_m2"], 100.0, rel_tol=1e-6)

    def test_reconstructed_ge_simulated(self):
        result = self._run()
        assert result["total_eui_reconstructed_kwh_m2"] >= _LO_ROW["total_eui_kwh_m2"]


class TestPassthroughForUnmapped:
    def _make_row(self, archetype_id, status="success", total_eui=50.0):
        return {
            "osm_id": "way/99",
            "archetype_id": archetype_id,
            "heating_eui_kwh_m2": 10.0,
            "cooling_eui_kwh_m2": 10.0,
            "lighting_eui_kwh_m2": 10.0,
            "equipment_eui_kwh_m2": 10.0,
            "total_eui_kwh_m2": total_eui,
            "simulation_status": status,
        }

    def test_unknown_archetype_is_passthrough(self):
        from openubem.results.service_loads import load_coefficients, reconstruct_building
        coeffs = load_coefficients()
        row = self._make_row("DataCenter")
        result = reconstruct_building(row, coeffs)
        assert result["reconstruction_applied"] is False

    def test_failed_status_is_passthrough(self):
        from openubem.results.service_loads import load_coefficients, reconstruct_building
        coeffs = load_coefficients()
        row = self._make_row("LargeOffice", status="failed_parse")
        result = reconstruct_building(row, coeffs)
        assert result["reconstruction_applied"] is False

    def test_passthrough_recon_columns_are_zero(self):
        from openubem.results.service_loads import load_coefficients, reconstruct_building
        coeffs = load_coefficients()
        row = self._make_row("DataCenter", total_eui=50.0)
        result = reconstruct_building(row, coeffs)
        for col in ("vent_fans_eui_recon_kwh_m2", "pumps_eui_recon_kwh_m2",
                    "swh_dhw_eui_recon_kwh_m2", "refrig_eui_recon_kwh_m2",
                    "cooking_other_eui_recon_kwh_m2"):
            assert result[col] == 0.0, f"{col} not zero for passthrough"

    def test_passthrough_total_equals_simulated(self):
        from openubem.results.service_loads import load_coefficients, reconstruct_building
        coeffs = load_coefficients()
        row = self._make_row("DataCenter", total_eui=50.0)
        result = reconstruct_building(row, coeffs)
        assert math.isclose(result["total_eui_reconstructed_kwh_m2"], 50.0, rel_tol=1e-9)

    def test_success_cached_status_is_reconstructed(self):
        from openubem.results.service_loads import load_coefficients, reconstruct_building
        coeffs = load_coefficients()
        row = self._make_row("LargeOffice", status="success_cached")
        result = reconstruct_building(row, coeffs)
        assert result["reconstruction_applied"] is True


# ---------------------------------------------------------------------------
# T04: DataFrame reconstruction
# ---------------------------------------------------------------------------

class TestReconstructFrameAddsColumnsAndPreservesRows:
    def _make_df(self):
        rows = [
            dict(_LO_ROW),
            {
                "osm_id": "way/2",
                "archetype_id": "DataCenter",
                "heating_eui_kwh_m2": 5.0,
                "cooling_eui_kwh_m2": 40.0,
                "lighting_eui_kwh_m2": 2.0,
                "equipment_eui_kwh_m2": 50.0,
                "total_eui_kwh_m2": 97.0,
                "simulation_status": "success",
            },
        ]
        return pd.DataFrame(rows)

    def test_row_count_preserved(self):
        from openubem.results.service_loads import reconstruct_frame
        df = self._make_df()
        out = reconstruct_frame(df, force=True)
        assert len(out) == 2

    def test_new_columns_present(self):
        from openubem.results.service_loads import reconstruct_frame
        out = reconstruct_frame(self._make_df(), force=True)
        expected_cols = {
            "reconstruction_applied", "archetype_mapped_to", "reconstruction_basis",
            "vent_fans_eui_recon_kwh_m2", "pumps_eui_recon_kwh_m2",
            "swh_dhw_eui_recon_kwh_m2", "refrig_eui_recon_kwh_m2",
            "cooking_other_eui_recon_kwh_m2", "total_eui_reconstructed_kwh_m2",
        }
        assert expected_cols.issubset(set(out.columns))

    def test_osm_id_preserved(self):
        from openubem.results.service_loads import reconstruct_frame
        out = reconstruct_frame(self._make_df(), force=True)
        assert set(out["osm_id"]) == {"way/1", "way/2"}

    def test_input_not_mutated(self):
        from openubem.results.service_loads import reconstruct_frame
        df = self._make_df()
        cols_before = set(df.columns)
        reconstruct_frame(df, force=True)
        assert set(df.columns) == cols_before

    def test_large_office_row_reconstructed(self):
        from openubem.results.service_loads import reconstruct_frame
        out = reconstruct_frame(self._make_df(), force=True)
        lo = out[out["osm_id"] == "way/1"].iloc[0]
        assert bool(lo["reconstruction_applied"]) is True

    def test_datacenter_row_passthrough(self):
        from openubem.results.service_loads import reconstruct_frame
        out = reconstruct_frame(self._make_df(), force=True)
        dc = out[out["osm_id"] == "way/2"].iloc[0]
        assert bool(dc["reconstruction_applied"]) is False

    def test_reconstructed_ge_simulated_for_success_rows(self):
        from openubem.results.service_loads import reconstruct_frame
        out = reconstruct_frame(self._make_df(), force=True)
        success = out[out["reconstruction_applied"] == True]
        for _, row in success.iterrows():
            assert row["total_eui_reconstructed_kwh_m2"] >= row["total_eui_kwh_m2"]


# ---------------------------------------------------------------------------
# T15: Phase-E pass-through (RECONSTRUCT_SERVICE_LOADS=False by default)
# ---------------------------------------------------------------------------

class TestPhaseEPassthrough:
    def _make_df(self):
        return pd.DataFrame([dict(_LO_ROW)])

    def test_passthrough_adds_columns(self):
        """Phase-E default: reconstruct_frame adds columns with zeros, no uplift."""
        from openubem.results.service_loads import reconstruct_frame
        out = reconstruct_frame(self._make_df())  # force=False, flag is False by default
        assert "reconstruction_applied" in out.columns
        assert "total_eui_reconstructed_kwh_m2" in out.columns

    def test_passthrough_reconstruction_applied_false(self):
        """Phase-E: no row has reconstruction_applied=True when flag is off."""
        from openubem.results.service_loads import reconstruct_frame
        out = reconstruct_frame(self._make_df())
        assert not out["reconstruction_applied"].any()

    def test_passthrough_service_loads_zero(self):
        """Phase-E: all uplift columns are 0.0 (service loads physically modelled)."""
        from openubem.results.service_loads import reconstruct_frame
        out = reconstruct_frame(self._make_df())
        for col in ("vent_fans_eui_recon_kwh_m2", "pumps_eui_recon_kwh_m2",
                    "swh_dhw_eui_recon_kwh_m2", "refrig_eui_recon_kwh_m2",
                    "cooking_other_eui_recon_kwh_m2"):
            assert out.iloc[0][col] == 0.0, f"{col} not zero in Phase-E pass-through"

    def test_passthrough_total_equals_simulated(self):
        """Phase-E: total_eui_reconstructed_kwh_m2 == total_eui_kwh_m2."""
        from openubem.results.service_loads import reconstruct_frame
        out = reconstruct_frame(self._make_df())
        import math
        assert math.isclose(
            out.iloc[0]["total_eui_reconstructed_kwh_m2"],
            _LO_ROW["total_eui_kwh_m2"],
            rel_tol=1e-9,
        )

    def test_passthrough_basis_label(self):
        """Phase-E pass-through sets reconstruction_basis='disabled_phase_e'."""
        from openubem.results.service_loads import reconstruct_frame
        out = reconstruct_frame(self._make_df())
        assert out.iloc[0]["reconstruction_basis"] == "disabled_phase_e"

    def test_force_true_still_reconstructs(self):
        """force=True overrides the flag and applies reconstruction (test-mode escape hatch)."""
        from openubem.results.service_loads import reconstruct_frame
        out = reconstruct_frame(self._make_df(), force=True)
        assert bool(out.iloc[0]["reconstruction_applied"]) is True


# ---------------------------------------------------------------------------
# Conservation check: reconstructed >= simulated for all reconstructed rows
# ---------------------------------------------------------------------------

class TestGlobalConservation:
    def test_reconstructed_approx_e_total_est(self):
        """total_recon ≈ E_total_est (within float rounding) for a mapped archetype."""
        from openubem.results.service_loads import load_coefficients, reconstruct_building
        coeffs = load_coefficients()
        result = reconstruct_building(_LO_ROW, coeffs)
        # E_total_est = 83/0.83 = 100.0; total_recon = total_sim + sum(recon_j) = 100.0
        assert math.isclose(result["total_eui_reconstructed_kwh_m2"], 100.0, rel_tol=1e-6)


# ---------------------------------------------------------------------------
# T05: per-cell driver (skip if runtime data absent)
# ---------------------------------------------------------------------------

class TestReconstructCellAustinCentre:
    @pytest.mark.skipif(
        not _AUSTIN_CENTRE_GPKG.exists(),
        reason="Runtime data absent: austin_centre/results/05_results.gpkg not found",
    )
    def test_returns_dataframe(self):
        from openubem.results.service_loads import reconstruct_cell
        df = reconstruct_cell("austin_centre")
        assert isinstance(df, pd.DataFrame)

    @pytest.mark.skipif(
        not _AUSTIN_CENTRE_GPKG.exists(),
        reason="Runtime data absent",
    )
    def test_cell_column_added(self):
        from openubem.results.service_loads import reconstruct_cell
        df = reconstruct_cell("austin_centre")
        assert "cell" in df.columns
        assert (df["cell"] == "austin_centre").all()

    @pytest.mark.skipif(
        not _AUSTIN_CENTRE_GPKG.exists(),
        reason="Runtime data absent",
    )
    def test_has_reconstruction_columns(self):
        from openubem.results.service_loads import reconstruct_cell
        df = reconstruct_cell("austin_centre")
        assert "reconstruction_applied" in df.columns
        assert "total_eui_reconstructed_kwh_m2" in df.columns

    @pytest.mark.skipif(
        not _AUSTIN_CENTRE_GPKG.exists(),
        reason="Runtime data absent",
    )
    def test_no_geometry_column(self):
        from openubem.results.service_loads import reconstruct_cell
        import geopandas as gpd
        df = reconstruct_cell("austin_centre")
        assert not isinstance(df, gpd.GeoDataFrame)

    def test_missing_cell_raises_file_not_found(self):
        from openubem.results.service_loads import reconstruct_cell
        with pytest.raises(FileNotFoundError):
            reconstruct_cell("nonexistent_cell_xyz")


# ---------------------------------------------------------------------------
# T06: CLI smoke test (skip if runtime data absent)
# ---------------------------------------------------------------------------

class TestCliSmoke:
    @pytest.mark.skipif(
        not _AUSTIN_CENTRE_GPKG.exists(),
        reason="Runtime data absent",
    )
    def test_main_writes_csv(self, tmp_path, monkeypatch):
        import scripts.reconstruct_service_loads as cli
        out_path = tmp_path / "r7_test.csv"
        monkeypatch.setattr(cli, "_OUT_PATH", out_path)
        cli.main(cells=["austin_centre"])
        assert out_path.exists()
        import pandas as pd
        df = pd.read_csv(out_path)
        assert len(df) > 0
        assert "total_eui_reconstructed_kwh_m2" in df.columns


# ---------------------------------------------------------------------------
# T12: archetype-map coverage + building-fixed round-trip
# ---------------------------------------------------------------------------

class TestArchetypeMapCoversMatrix:
    """All 18 matrix archetype_ids must map to a non-passthrough Table-4 key."""

    _MATRIX_IDS = [
        "LargeOffice", "MediumOffice", "SmallOffice", "Courthouse",
        "TallBuilding", "SuperTallBuilding", "PrimarySchool",
        "FullServiceRestaurant", "QuickServiceRestaurant",
        "RetailStandalone", "Supermarket", "SuperMarket",
        "Warehouse", "Hospital", "LargeHotel", "Hotel",
        "MidriseApartment", "HighriseApartment",
        "Outpatient", "SmallHotel", "College", "Laboratory", "RetailStripmall",
        "OpenUBEMUnknown",
    ]

    def test_all_matrix_ids_non_passthrough(self):
        from openubem.results.service_loads import load_coefficients
        data = load_coefficients()
        amap = data["archetype_map"]
        passthrough_ids = []
        for arch_id in self._MATRIX_IDS:
            mapped = amap.get(arch_id)
            if mapped is None or mapped == "passthrough":
                passthrough_ids.append(arch_id)
        assert passthrough_ids == [], (
            f"These archetype_ids still map to passthrough: {passthrough_ids}"
        )

    def test_new_six_entries_present(self):
        """T12 requires exactly these 6 new entries in archetype_map."""
        from openubem.results.service_loads import load_coefficients
        data = load_coefficients()
        amap = data["archetype_map"]
        expected = {
            "SuperMarket": "supermarket",
            "Outpatient": "hospital",
            "SmallHotel": "large_hotel",
            "College": "secondary_school",
            "Laboratory": "hospital",
            "RetailStripmall": "standalone_retail",
        }
        for arch_id, table4_key in expected.items():
            assert amap.get(arch_id) == table4_key, (
                f"{arch_id!r} → expected {table4_key!r}, got {amap.get(arch_id)!r}"
            )


class TestRoundtripReconBuildingFixed:
    """Building-fixed round-trip: verify math on synthetic rows."""

    def _coeffs(self):
        from openubem.results.service_loads import load_coefficients
        return load_coefficients()

    def test_large_office_recon_total(self):
        """LargeOffice: recon_total = counter_total / 0.83 exactly."""
        coeffs = self._coeffs()
        amap = coeffs["archetype_map"]
        fracs = coeffs["fractions"]
        arch = "LargeOffice"
        mapped = amap[arch]
        f = fracs[mapped]
        modeled_frac = f["space_heat"] + f["space_cool"] + f["lighting"] + f["equip_plug"]
        assert math.isclose(modeled_frac, 0.83, rel_tol=1e-9)
        counter_total = 373.721133362303  # from roundtrip_report.csv
        recon_total = counter_total / modeled_frac
        assert math.isclose(recon_total, counter_total / 0.83, rel_tol=1e-6)

    def test_passthrough_datacenter_dev_unchanged(self):
        """DataCenter is not in archetype_map → recon_total == counter_total → dev unchanged."""
        coeffs = self._coeffs()
        amap = coeffs["archetype_map"]
        arch = "LargeDataCenterHighITE"
        mapped = amap.get(arch)
        # DataCenter not in map → passthrough
        assert mapped is None or mapped == "passthrough"

    def test_supermarket_now_mapped(self):
        """SuperMarket must now map to 'supermarket', not passthrough."""
        coeffs = self._coeffs()
        amap = coeffs["archetype_map"]
        assert amap.get("SuperMarket") == "supermarket"

    def test_supermarket_modeled_frac(self):
        """supermarket modeled_frac = 0.09+0.06+0.13+0.08 = 0.36."""
        coeffs = self._coeffs()
        f = coeffs["fractions"]["supermarket"]
        modeled_frac = f["space_heat"] + f["space_cool"] + f["lighting"] + f["equip_plug"]
        assert math.isclose(modeled_frac, 0.36, rel_tol=1e-9)

    def test_outpatient_mapped_to_hospital(self):
        coeffs = self._coeffs()
        assert coeffs["archetype_map"].get("Outpatient") == "hospital"
