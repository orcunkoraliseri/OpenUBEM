"""Phase-E DHW emitter: WaterHeater:Mixed + WaterUse:Equipment/Connections (T09, D7).

Deviation: uses Site:WaterMainsTemperature CorrelationFromWeatherFile instead of
Correlation with per-city inputs — avoids EPW-path city detection and is more accurate.
"""
import json
import math
from pathlib import Path

from openubem.semantic import provenance

_DHW_DATA = json.loads(
    (Path(__file__).parent.parent / "data/loads/dhw_by_archetype.json").read_text()
)


def _resolve_area(row, flags):
    """footprint_area_m2 with provenance (T03). absent/None -> 400.0 (+DEFAULT token);
    stored 0 -> kept (+SUSPECT_ZERO token); real value -> unchanged."""
    v = row.get("footprint_area_m2", None)
    if v is None or (isinstance(v, float) and math.isnan(v)):
        flags.add(provenance.impute_token("DEFAULT", "GEOMETRY_AREA", "LOW"))
        return 400.0
    fv = float(v)
    if fv == 0:
        flags.add("SUSPECT_ZERO_FOOTPRINT_AREA_M2")
        return fv
    return fv


def _total_floor_area(row, zones, flags=None):
    """Footprint × unique-floor count extracted from zone names.

    A missing footprint (→400 m²) or a missing floor count (→1 floor) records a
    provenance token in `flags`; default VALUES are unchanged (T03, instrumentation).
    """
    if flags is None:
        flags = set()
    footprint = _resolve_area(row, flags)
    explicit = max((int(z.get("num_floors", 0) or 0) for z in zones), default=0)
    if explicit > 0:
        return footprint * explicit
    floor_idx = set()
    for z in zones:
        parts = z.get("name", "").split("_F")
        if len(parts) >= 2:
            fi = parts[1].split("_")[0]
            if fi.isdigit():
                floor_idx.add(fi)
    if len(floor_idx) == 0:
        flags.add(provenance.impute_token("DEFAULT", "GEOMETRY_FLOORS", "LOW"))
    return footprint * max(len(floor_idx), 1)


def _sched_constant_once(idf, name, value):
    if not any(s.Name == name for s in idf.idfobjects.get("SCHEDULE:CONSTANT", [])):
        s = idf.newidfobject("SCHEDULE:CONSTANT")
        s.Name = name
        s.Hourly_Value = value


def assign_dhw(idf, row, zones):
    """Emit standalone WaterHeater:Mixed + WaterUse:Equipment/Connections (D7).

    Returns the sorted geometry-default provenance tokens (T03); they are also
    appended in place to ``row['data_quality_flag']``. The table-driven no_dhw /
    no-peak-flow skip is preserved and runs BEFORE any geometry resolution, so a
    no_dhw archetype emits no area/floors default token.
    """
    if not zones:  # degenerate geometry: no zone to host the heater (D4a defensive guard)
        return []
    arch = str(row["archetype_id"])
    data = _DHW_DATA.get(arch, {})
    if data.get("no_dhw") or not data.get("peak_flow_l_h_m2"):
        return []

    flags: set = set()
    total_area = _total_floor_area(row, zones, flags)
    for tok in sorted(flags):
        row["data_quality_flag"] = provenance.append_flag_token(
            row.get("data_quality_flag"), tok
        )
    peak_flow_l_h = data["peak_flow_l_h_m2"] * total_area
    if peak_flow_l_h <= 0:
        return sorted(flags)
    peak_flow_m3_s = peak_flow_l_h / 3_600_000.0  # L/h → m³/s (÷3600 s/h ÷1000 L/m³)

    annual_vol = data["annual_hw_vol_l_m2_yr"] * total_area
    avg_frac = min(annual_vol / (peak_flow_l_h * 8760.0), 1.0)

    zone_name = zones[0]["name"]
    fuel = data["heater_fuel"]
    eff = data["heater_efficiency"]
    standby_ua = data["standby_loss_w_k"]

    # Site:WaterMainsTemperature — once per IDF
    if not idf.idfobjects["SITE:WATERMAINSTEMPERATURE"]:
        wmt = idf.newidfobject("SITE:WATERMAINSTEMPERATURE")
        wmt.Calculation_Method = "CorrelationFromWeatherFile"

    _sched_constant_once(idf, "OpenUBEM_DHW_Setpoint", 60.0)
    flow_sched = f"OpenUBEM_DHW_FlowFrac_{arch}"
    _sched_constant_once(idf, flow_sched, round(avg_frac, 6))
    _sched_constant_once(
        idf, "OpenUBEM_DHW_SensibleFrac", _DHW_DATA["_zone_gain"]["sensible_fraction"]
    )
    _sched_constant_once(
        idf, "OpenUBEM_DHW_LatentFrac", _DHW_DATA["_zone_gain"]["latent_fraction"]
    )

    # WaterHeater:Mixed — standalone (Peak_Use_Flow_Rate mode, no PlantLoop nodes)
    # Capacity: size to heat peak flow from 5 °C mains floor to setpoint (standalone can't autosize)
    _rho_cp = 4_186_000.0  # J/(m³·K)
    heater_capacity_w = max(peak_flow_m3_s * _rho_cp * (data["setpoint_c"] - 5.0) * 1.5, 1000.0)

    wh = idf.newidfobject("WATERHEATER:MIXED")
    wh.Name = f"DHW_Heater_{arch}"
    wh.Tank_Volume = 0.3785  # 100-gal commercial default
    wh.Setpoint_Temperature_Schedule_Name = "OpenUBEM_DHW_Setpoint"
    wh.Heater_Control_Type = "Cycle"
    wh.Heater_Maximum_Capacity = round(heater_capacity_w, 0)
    wh.Heater_Fuel_Type = fuel
    wh.Heater_Thermal_Efficiency = eff
    wh.Off_Cycle_Parasitic_Fuel_Type = fuel
    wh.Ambient_Temperature_Indicator = "Zone"
    wh.Ambient_Temperature_Zone_Name = zone_name
    wh.Off_Cycle_Loss_Coefficient_to_Ambient_Temperature = standby_ua
    wh.On_Cycle_Loss_Coefficient_to_Ambient_Temperature = standby_ua
    wh.Peak_Use_Flow_Rate = peak_flow_m3_s
    wh.Use_Flow_Rate_Fraction_Schedule_Name = flow_sched
    wh.EndUse_Subcategory = "DHW"

    # WaterUse:Equipment — zone heat-gain split 0.20 sensible / 0.05 latent (D7)
    wu_name = f"DHW_WaterUse_{arch}"
    wu = idf.newidfobject("WATERUSE:EQUIPMENT")
    wu.Name = wu_name
    wu.EndUse_Subcategory = "DHW"
    wu.Peak_Flow_Rate = peak_flow_m3_s
    wu.Flow_Rate_Fraction_Schedule_Name = flow_sched
    wu.Target_Temperature_Schedule_Name = "OpenUBEM_DHW_Setpoint"
    wu.Zone_Name = zone_name
    wu.Sensible_Fraction_Schedule_Name = "OpenUBEM_DHW_SensibleFrac"
    wu.Latent_Fraction_Schedule_Name = "OpenUBEM_DHW_LatentFrac"

    # WaterUse:Connections — standalone mode (blank node names)
    wc = idf.newidfobject("WATERUSE:CONNECTIONS")
    wc.Name = f"DHW_WaterConn_{arch}"
    wc.Hot_Water_Supply_Temperature_Schedule_Name = "OpenUBEM_DHW_Setpoint"
    wc.Water_Use_Equipment_1_Name = wu_name

    return sorted(flags)
