"""T02/T03 — Tier-B silent-default provenance closure.

Load-bearing properties:
  (1) an absent default (no cooling_cop) -> DEFAULT token + LOW confidence;
  (2) a stored 0 is flagged DISTINCTLY and NOT promoted to the default value;
  (3) a real value -> no default flag AND its emitted number is unchanged
      (instrumentation only — EUI must not move);
  (4) the table-driven no_dhw / no_cooking skip is preserved (no geometry token).
"""
from pathlib import Path

import pandas as pd
import pytest
from geomeppy import IDF
from eppy.modeleditor import IDDAlreadySetError

from openubem.config import ENERGYPLUS_IDD_PATH
from openubem.idf import hvac
from openubem.idf.hvac import assign_hvac, _emit_ptac, _default_flag, _zero_flag
from openubem.idf.dhw import assign_dhw
from openubem.idf.cooking import assign_cooking
from openubem.idf.refrigeration import assign_refrigeration
from openubem.semantic import provenance as prov

TEMPLATES_DIR = Path(__file__).parent.parent / "openubem" / "idf" / "templates"
_BASE_TPL = str(TEMPLATES_DIR / "commercial_base.idf")


def _fresh_idf():
    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass
    return IDF(_BASE_TPL)


def _zones(n=1, osm="b"):
    return [{"name": f"{osm}_F{i}_whole"} for i in range(n)]


def _ptac_cop(idf):
    return float(idf.idfobjects["HVACTEMPLATE:ZONE:PTAC"][0].Cooling_Coil_Gross_Rated_Cooling_COP)


# ── T02: HVAC ────────────────────────────────────────────────────────────────

class TestHVACDefaultProvenance:
    def test_absent_cop_uses_default_with_low_token(self):
        idf = _fresh_idf()
        flags: set = set()
        _emit_ptac(idf, _zones(1), {"heating_coil_type": "Electric"}, flags)
        # value falls back to 3.0
        assert _ptac_cop(idf) == 3.0
        # DEFAULT token present, ends in _LOW
        tok = _default_flag("cooling_cop")
        assert tok in flags
        assert tok == "DEFAULT_ASHRAE901_COOLING_COP_LOW"
        method, source, tier = prov.parse_token(tok)
        assert (method, tier) == ("DEFAULT", "LOW")

    def test_stored_zero_is_kept_and_flagged_distinctly(self):
        idf = _fresh_idf()
        flags: set = set()
        _emit_ptac(idf, _zones(1), {"cooling_cop": 0, "heating_coil_type": "Electric"}, flags)
        # the real 0 is preserved — NOT promoted to 3.0
        assert _ptac_cop(idf) == 0.0
        # flagged distinctly (SUSPECT_ZERO), and NOT with the DEFAULT token
        assert _zero_flag("cooling_cop") in flags
        assert _default_flag("cooling_cop") not in flags

    def test_real_cop_no_flag_and_value_unchanged(self):
        idf = _fresh_idf()
        flags: set = set()
        _emit_ptac(idf, _zones(1), {"cooling_cop": 3.81, "heating_coil_type": "Gas",
                                    "heating_efficiency": 0.8}, flags)
        # byte-identical to the input value (instrumentation only)
        assert _ptac_cop(idf) == 3.81
        assert flags == set()

    def test_assign_hvac_clean_archetype_emits_no_flag(self):
        """SmallHotel PTAC reads only cooling_cop (present in the table) -> no default flag."""
        idf = _fresh_idf()
        row = pd.Series({"archetype_id": "SmallHotel"})
        emitted = assign_hvac(idf, row, _zones(2))
        assert emitted == []
        assert "data_quality_flag" not in row or not str(row.get("data_quality_flag") or "")

    def test_assign_hvac_records_default_on_row(self):
        """The single-zone LargeOffice downgrade strips the VAV fan fields to force PSZ
        defaults (622.5 Pa / 0.55575) — a real default-firing path. The tokens are returned
        AND appended to the row, and the fan VALUES are the unchanged PSZ defaults."""
        idf = _fresh_idf()
        row = pd.Series({"archetype_id": "LargeOffice", "data_quality_flag": "existing_flag"})
        emitted = assign_hvac(idf, row, _zones(1, "lo"))  # 1 zone -> downgrade to PSZ-AC
        fan_pa_tok = _default_flag("fan_static_pa")
        assert fan_pa_tok in emitted
        assert _default_flag("fan_total_efficiency") in emitted
        # appended in place, preserving the pre-existing flag
        assert "existing_flag" in row["data_quality_flag"]
        assert fan_pa_tok in row["data_quality_flag"]
        # value unchanged: PSZ default fan static 622.5 Pa
        s = idf.idfobjects["HVACTEMPLATE:SYSTEM:UNITARY"][0]
        assert abs(float(s.Supply_Fan_Delta_Pressure) - 622.5) < 1e-9

    def test_no_stored_zero_in_bundled_cop_table(self):
        """Guard: the production COP table has no 0 in the instrumented keys, so the
        stored-0 branch never fires in a real run (EUI byte-identical)."""
        cop = hvac._load_cop_table()
        for arch, e in cop.items():
            for k in ("cooling_cop", "heating_efficiency", "chiller_cop_phaseE"):
                if k in e and e[k] is not None:
                    assert e[k] != 0, f"{arch}.{k} == 0 would trip the zero branch"


class TestPTACGasHeatingEfficiencyProvenance:
    """wave-2a residual A: `_emit_ptac`'s `Gas_Heating_Coil_Efficiency` default (0.8) was
    a silent `if is not None else` substitution with no provenance — now routed through
    `_resolve`, only for Gas coils (Electric coils never read the key)."""

    def _gas_eff(self, idf):
        return float(idf.idfobjects["HVACTEMPLATE:ZONE:PTAC"][0].Gas_Heating_Coil_Efficiency)

    def test_absent_heating_efficiency_uses_default_with_low_token(self):
        idf = _fresh_idf()
        flags: set = set()
        _emit_ptac(idf, _zones(1), {"cooling_cop": 3.81, "heating_coil_type": "Gas"}, flags)
        assert self._gas_eff(idf) == 0.8
        tok = _default_flag("heating_efficiency")
        assert tok in flags
        assert tok == "DEFAULT_ASHRAE901_HEATING_EFFICIENCY_LOW"

    def test_stored_zero_heating_efficiency_kept_and_flagged_distinctly(self):
        idf = _fresh_idf()
        flags: set = set()
        _emit_ptac(idf, _zones(1), {"cooling_cop": 3.81, "heating_coil_type": "Gas",
                                    "heating_efficiency": 0}, flags)
        # the real 0 is preserved — NOT promoted to 0.8
        assert self._gas_eff(idf) == 0.0
        assert _zero_flag("heating_efficiency") in flags
        assert _default_flag("heating_efficiency") not in flags

    def test_real_heating_efficiency_no_flag_and_value_unchanged(self):
        idf = _fresh_idf()
        flags: set = set()
        _emit_ptac(idf, _zones(1), {"cooling_cop": 3.81, "heating_coil_type": "Gas",
                                    "heating_efficiency": 0.85}, flags)
        assert self._gas_eff(idf) == 0.85
        assert flags == set()

    def test_electric_coil_never_reads_heating_efficiency(self):
        """Electric PTAC coils don't use Gas_Heating_Coil_Efficiency at all — no default
        or zero token should fire even though `heating_efficiency` is absent from the entry."""
        idf = _fresh_idf()
        flags: set = set()
        _emit_ptac(idf, _zones(1), {"cooling_cop": 3.81, "heating_coil_type": "Electric"}, flags)
        assert flags == set()


# ── T03: DHW / cooking geometry defaults ─────────────────────────────────────

_AREA_TOK = prov.impute_token("DEFAULT", "GEOMETRY_AREA", "LOW")
_FLOORS_TOK = prov.impute_token("DEFAULT", "GEOMETRY_FLOORS", "LOW")
_ZERO_AREA_TOK = "SUSPECT_ZERO_FOOTPRINT_AREA_M2"


class TestDHWGeometryProvenance:
    def test_no_dhw_archetype_emits_no_area_flag(self):
        """no_dhw skip runs before geometry resolution -> no area/floors token even
        when footprint_area_m2 is absent."""
        idf = _fresh_idf()
        row = pd.Series({"archetype_id": "SmallDataCenterHighITE"})  # no footprint
        emitted = assign_dhw(idf, row, [{"name": "b_zone"}])
        assert emitted == []
        assert _AREA_TOK not in emitted and _FLOORS_TOK not in emitted
        assert len(idf.idfobjects["WATERHEATER:MIXED"]) == 0

    def test_absent_area_and_floors_flagged(self):
        idf = _fresh_idf()
        row = pd.Series({"archetype_id": "SmallOffice"})  # has DHW, no footprint
        emitted = assign_dhw(idf, row, [{"name": "b_zone"}])  # name has no _F -> floors->1
        assert _AREA_TOK in emitted
        assert _FLOORS_TOK in emitted
        assert _AREA_TOK in row["data_quality_flag"]
        assert _FLOORS_TOK in row["data_quality_flag"]

    def test_stored_zero_area_kept_and_flagged(self):
        idf = _fresh_idf()
        row = pd.Series({"archetype_id": "SmallOffice", "footprint_area_m2": 0})
        emitted = assign_dhw(idf, row, _zones(1))  # F0 in name -> floors from name, no floors flag
        assert _ZERO_AREA_TOK in emitted
        assert _AREA_TOK not in emitted  # distinct from the absent-default token
        # 0 area -> 0 peak flow -> no water heater emitted (real 0 not promoted to 400)
        assert len(idf.idfobjects["WATERHEATER:MIXED"]) == 0

    def test_real_area_and_floors_no_flag(self):
        idf = _fresh_idf()
        row = pd.Series({"archetype_id": "SmallOffice", "footprint_area_m2": 250.0})
        emitted = assign_dhw(idf, row, _zones(1))  # F0 -> floors from name
        assert emitted == []


class TestCookingGeometryProvenance:
    def test_no_cooking_archetype_emits_no_area_flag(self):
        idf = _fresh_idf()
        row = pd.Series({"archetype_id": "SmallOffice"})  # no_cooking, no footprint
        emitted = assign_cooking(idf, row, [{"name": "b_zone"}])
        assert emitted == []
        assert _AREA_TOK not in emitted and _FLOORS_TOK not in emitted

    def test_absent_area_and_floors_flagged(self):
        idf = _fresh_idf()
        row = pd.Series({"archetype_id": "FullServiceRestaurant"})  # has cooking, no footprint
        emitted = assign_cooking(idf, row, [{"name": "b_zone"}])
        assert _AREA_TOK in emitted
        assert _FLOORS_TOK in emitted
        assert _AREA_TOK in row["data_quality_flag"]

    def test_real_area_no_flag(self):
        idf = _fresh_idf()
        row = pd.Series({"archetype_id": "FullServiceRestaurant", "footprint_area_m2": 300.0})
        emitted = assign_cooking(idf, row, _zones(1))  # F0 -> floors from name
        assert emitted == []


# ── T03 residual (wave 2a): refrigeration geometry defaults ──────────────────
# Same `_total_floor_area` gap as T03 (footprint_area_m2 / num_floors), left
# untouched at T03 because refrigeration.py was not yet in the plan's file list.

class TestRefrigerationGeometryProvenance:
    def test_non_refrig_archetype_emits_no_area_flag(self):
        """SmallOffice is neither SuperMarket nor in the lumped table -> skip runs
        BEFORE geometry resolution, so no area/floors token even with no footprint."""
        idf = _fresh_idf()
        row = pd.Series({"archetype_id": "SmallOffice"})
        emitted = assign_refrigeration(idf, row, [{"name": "b_zone"}])
        assert emitted == []
        assert _AREA_TOK not in emitted and _FLOORS_TOK not in emitted
        assert len(idf.idfobjects["ELECTRICEQUIPMENT"]) == 0
        assert len(idf.idfobjects["REFRIGERATION:CASE"]) == 0

    def test_supermarket_absent_area_and_floors_flagged(self):
        idf = _fresh_idf()
        row = pd.Series({"archetype_id": "SuperMarket"})  # no footprint
        emitted = assign_refrigeration(idf, row, [{"name": "b_zone"}])  # no _F -> floors default
        assert _AREA_TOK in emitted
        assert _FLOORS_TOK in emitted
        assert _AREA_TOK in row["data_quality_flag"]
        # 400 m2 default area is nonzero -> real cases still emitted
        assert len(idf.idfobjects["REFRIGERATION:CASE"]) > 0

    def test_supermarket_stored_zero_area_kept_and_flagged(self):
        idf = _fresh_idf()
        row = pd.Series({"archetype_id": "SuperMarket", "footprint_area_m2": 0})
        emitted = assign_refrigeration(idf, row, _zones(1, "sm"))  # F0 -> floors from name
        assert _ZERO_AREA_TOK in emitted
        assert _AREA_TOK not in emitted  # distinct from the absent-default token
        # 0 area -> 0 case length -> all cases skipped (real 0 not promoted to 400)
        assert len(idf.idfobjects["REFRIGERATION:CASE"]) == 0

    def test_supermarket_real_area_no_flag(self):
        idf = _fresh_idf()
        row = pd.Series({"archetype_id": "SuperMarket", "footprint_area_m2": 4000.0})
        emitted = assign_refrigeration(idf, row, _zones(1, "sm"))  # F0 -> floors from name
        assert emitted == []
        assert len(idf.idfobjects["REFRIGERATION:CASE"]) > 0

    def test_lumped_archetype_absent_area_flagged(self):
        idf = _fresh_idf()
        row = pd.Series({"archetype_id": "LargeHotel"})  # lumped, no footprint
        emitted = assign_refrigeration(idf, row, [{"name": "b_zone"}])
        assert _AREA_TOK in emitted
        assert _FLOORS_TOK in emitted
        assert len(idf.idfobjects["ELECTRICEQUIPMENT"]) == 1

    def test_lumped_archetype_real_area_no_flag(self):
        idf = _fresh_idf()
        row = pd.Series({"archetype_id": "LargeHotel", "footprint_area_m2": 500.0})
        emitted = assign_refrigeration(idf, row, _zones(1, "lh"))  # F0 -> floors from name
        assert emitted == []
        assert len(idf.idfobjects["ELECTRICEQUIPMENT"]) == 1
