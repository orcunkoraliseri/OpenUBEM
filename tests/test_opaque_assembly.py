"""Unit tests for openubem/idf/opaque_assembly.py (plan E-LA-20 multilayer-fix,
F04/F07). Binding rule: plan §4-quinquies. Frozen constants: T_ENGAGE = 0.868,
T_MASS_MAX = 0.35 -- never re-derived, never recomputed from `u` in these
tests (a test that recomputes the cap from `u` would pass against a re-tuned
constant; assertions here use the literal values).
"""

from pathlib import Path

import pytest
from eppy.modeleditor import IDDAlreadySetError
from geomeppy import IDF as GeomIDF

from openubem import config
from openubem.idf import opaque_assembly
from openubem.idf.opaque_assembly import T_ENGAGE, T_MASS_MAX, build_opaque_assembly

try:
    GeomIDF.setiddname(str(config.ENERGYPLUS_IDD_PATH))
except IDDAlreadySetError:
    pass

_TEMPLATE = Path(__file__).resolve().parent.parent / "openubem" / "idf" / "templates" / "residential_base.idf"

_K = 0.12  # mirrors opaque_assembly._K -- only used here to derive total_t for test setup

# u grid per F07: spans both sides of T_ENGAGE and includes the real fleet
# operating point (0.119, F-19) and the synthetic stress point (0.097).
# Bucket membership is derived from the literal rule (total_t <= T_ENGAGE),
# not asserted from the plan's illustrative prose -- see F07 progress-log
# deviation note: at u=0.138, total_t = (1/0.138)*0.12 = 0.869565 m, which is
# *above* T_ENGAGE = 0.868 m, so it engages the cap. (Plan §6 F07 lists 0.138
# in the uncapped group; that grouping is inconsistent with its own adjacent
# statement "u < 0.1382 engages" -- 0.138 < 0.1382 -- and with the binding
# §4-quinquies formula. Flagged for the manager at CP-B.)
_U_GRID = (0.097, 0.119, 0.138, 0.182, 0.5, 2.0)


def _total_t(u):
    return max(0.01, (1.0 / u) * _K)


def _capped_us():
    return [u for u in _U_GRID if _total_t(u) > T_ENGAGE]


def _uncapped_us():
    return [u for u in _U_GRID if _total_t(u) <= T_ENGAGE]


def _new_idf():
    return GeomIDF(str(_TEMPLATE))


class TestUPreserved:
    @pytest.mark.parametrize("u", _U_GRID)
    def test_u_preserved_exactly(self, u):
        idf = _new_idf()
        cname = build_opaque_assembly(idf, "Roof_Assembly", u, thermal_mass=True)
        cons = next(c for c in idf.idfobjects["CONSTRUCTION"] if c.Name == cname)
        mats = {m.Name: m for m in idf.idfobjects["MATERIAL"]}
        nomasses = {m.Name: m for m in idf.idfobjects["MATERIAL:NOMASS"]}

        outside = mats["Roof_Assembly"]
        r_from_outside = float(outside.Thickness) / float(outside.Conductivity)
        if cons.Layer_2:
            residual = nomasses[cons.Layer_2]
            r_total = r_from_outside + float(residual.Thermal_Resistance)
        else:
            r_total = r_from_outside
        assert abs(r_total - 1.0 / u) < 1e-9


class TestEngagementPredicate:
    @pytest.mark.parametrize("u", _capped_us())
    def test_capped_us_produce_two_layers(self, u):
        idf = _new_idf()
        cname = build_opaque_assembly(idf, "Roof_Assembly", u, thermal_mass=True)
        cons = next(c for c in idf.idfobjects["CONSTRUCTION"] if c.Name == cname)
        assert cons.Outside_Layer == "Roof_Assembly"
        assert cons.Layer_2 == "Roof_Assembly_L2"
        assert not cons.Layer_3
        l2_names = {m.Name for m in idf.idfobjects["MATERIAL:NOMASS"]}
        assert "Roof_Assembly_L2" in l2_names

    @pytest.mark.parametrize("u", _uncapped_us())
    def test_uncapped_us_produce_single_material_no_layer_2(self, u):
        idf = _new_idf()
        cname = build_opaque_assembly(idf, "Roof_Assembly", u, thermal_mass=True)
        cons = next(c for c in idf.idfobjects["CONSTRUCTION"] if c.Name == cname)
        assert cons.Outside_Layer == "Roof_Assembly"
        assert not cons.Layer_2
        # No MATERIAL:NOMASS residual object exists at all -- do not infer
        # absence from the layer count alone (F07 point 2).
        l2_names = {m.Name for m in idf.idfobjects["MATERIAL:NOMASS"]}
        assert "Roof_Assembly_L2" not in l2_names


class TestCapIsFrozenConstant:
    @pytest.mark.parametrize("u", _capped_us())
    def test_capped_thickness_is_the_literal_0_35(self, u):
        """Asserts the emitted thickness equals the literal frozen constant,
        not a value recomputed from `u` -- a test that recomputes the cap
        would pass against a re-tuned constant; this one must not."""
        idf = _new_idf()
        build_opaque_assembly(idf, "Roof_Assembly", u, thermal_mass=True)
        mat = next(m for m in idf.idfobjects["MATERIAL"] if m.Name == "Roof_Assembly")
        assert float(mat.Thickness) == pytest.approx(0.35, abs=1e-12)
        assert T_MASS_MAX == 0.35
        assert T_ENGAGE == 0.868


class TestMassNotPreserved:
    @pytest.mark.parametrize("u", _capped_us())
    def test_capped_mass_layer_thinner_than_total_t(self, u):
        """F-14: multi-layer splitting that preserves total mass cannot clear
        the fleet worst case -- any fix that preserves total mass is dead on
        arrival (plan §4-ter). This guards against a well-meaning future
        "fix" that restores mass-preserving behaviour."""
        idf = _new_idf()
        build_opaque_assembly(idf, "Roof_Assembly", u, thermal_mass=True)
        mat = next(m for m in idf.idfobjects["MATERIAL"] if m.Name == "Roof_Assembly")
        total_t = _total_t(u)
        assert float(mat.Thickness) < total_t


class TestNoDanglingLayers:
    @pytest.mark.parametrize("u", _U_GRID)
    def test_every_referenced_layer_resolves(self, u):
        idf = _new_idf()
        cname = build_opaque_assembly(idf, "Roof_Assembly", u, thermal_mass=True)
        cons = next(c for c in idf.idfobjects["CONSTRUCTION"] if c.Name == cname)
        mat_names = {m.Name for m in idf.idfobjects["MATERIAL"]}
        nomass_names = {m.Name for m in idf.idfobjects["MATERIAL:NOMASS"]}
        all_names = mat_names | nomass_names
        for field in ("Outside_Layer", "Layer_2", "Layer_3", "Layer_4"):
            value = getattr(cons, field, "")
            if value:
                assert value in all_names, f"{field}={value!r} does not resolve to any MATERIAL(:NOMASS)"


class TestThermalMassFalseUnchanged:
    @pytest.mark.parametrize("u", _U_GRID)
    def test_nomass_single_layer_no_material_object(self, u):
        idf = _new_idf()
        cname = build_opaque_assembly(idf, "Roof_Assembly", u, thermal_mass=False)
        assert len(idf.idfobjects["MATERIAL"]) == 0
        nomasses = idf.idfobjects["MATERIAL:NOMASS"]
        assert len(nomasses) == 1
        assert float(nomasses[0].Thermal_Resistance) == pytest.approx(1.0 / u)
        cons = next(c for c in idf.idfobjects["CONSTRUCTION"] if c.Name == cname)
        assert cons.Outside_Layer == "Roof_Assembly"
        assert not cons.Layer_2


class TestNoTimestepDependence:
    def _build_and_snapshot(self, idf, u):
        build_opaque_assembly(idf, "Roof_Assembly", u, thermal_mass=True)
        mats = [
            (m.Name, float(m.Thickness), float(m.Conductivity), float(m.Density), float(m.Specific_Heat))
            for m in idf.idfobjects["MATERIAL"]
        ]
        nomasses = [(m.Name, float(m.Thermal_Resistance)) for m in idf.idfobjects["MATERIAL:NOMASS"]]
        cons = next(c for c in idf.idfobjects["CONSTRUCTION"] if c.Name == "Roof_Construction")
        return mats, nomasses, (cons.Outside_Layer, cons.Layer_2)

    @pytest.mark.parametrize("u", _U_GRID)
    def test_identical_output_across_timesteps_and_absent(self, u):
        snapshots = []
        for ts in (2, 4, 6):
            idf = _new_idf()
            idf.idfobjects["TIMESTEP"][0].Number_of_Timesteps_per_Hour = ts
            snapshots.append(self._build_and_snapshot(idf, u))

        idf_no_ts = _new_idf()
        idf_no_ts.removeidfobject(idf_no_ts.idfobjects["TIMESTEP"][0])
        assert len(idf_no_ts.idfobjects["TIMESTEP"]) == 0
        snapshots.append(self._build_and_snapshot(idf_no_ts, u))

        first = snapshots[0]
        for other in snapshots[1:]:
            assert other == first


class TestThinAssemblyFloor:
    def test_u_2_0_hits_expected_thickness_no_negative_or_zero(self):
        idf = _new_idf()
        build_opaque_assembly(idf, "Roof_Assembly", 2.0, thermal_mass=True)
        mat = next(m for m in idf.idfobjects["MATERIAL"] if m.Name == "Roof_Assembly")
        expected = max(0.01, (1.0 / 2.0) * _K)
        assert float(mat.Thickness) == pytest.approx(expected)
        assert float(mat.Thickness) > 0.0


class TestModuleConstants:
    def test_frozen_constants_are_the_literal_values(self):
        assert opaque_assembly.T_ENGAGE == 0.868
        assert opaque_assembly.T_MASS_MAX == 0.35
