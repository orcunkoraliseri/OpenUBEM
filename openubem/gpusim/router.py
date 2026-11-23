from dataclasses import asdict, dataclass
import csv
import hashlib
import json
from pathlib import Path
import time
from typing import Any

import numpy as np

from openubem.gpusim.backends.kernel.pack import deduplicate_weather, pack
from openubem.gpusim.backends.numpy_ref import SimulationResult, run_stage_a_batch
from openubem.gpusim.compile import BatchSpec, compile_expidf_batch
from openubem.gpusim.subset import ParsedIdfObject, SubsetCheckResult, check_s0_subset, parse_expidf
from openubem.gpusim.weather import WeatherSeries, load_epw_weather
from openubem.gpusim.writer import annual_heating_kwh, write_eplusout_csv

GPUSIM_VERSION: str = "0.1.0"
VALID_SIM_ENGINES: frozenset[str] = frozenset({"energyplus", "gpusim", "auto"})
CUDA_MAX_SUBBATCH: int = 384

_GPUSIM_ROOT = Path(__file__).resolve().parent
_CONFORMANCE_SOURCE_FILES: tuple[str, ...] = (
    "subset.py",
    "compile.py",
    "weather.py",
    "schedules.py",
    "ctf.py",
    "viewfactors.py",
    "physics/convection.py",
    "physics/lwr.py",
    "physics/psychro.py",
    "physics/surface_hb.py",
    "physics/window.py",
    "physics/zone_air.py",
    "backends/numpy_ref.py",
    "backends/stage_c.py",
    "backends/kernel/pack.py",
    "backends/kernel/s0_common.h",
)


def conformance_hash() -> str:
    """Compute a deterministic SHA-256 prefix over the gpusim physics & kernel sources."""
    h = hashlib.sha256()
    for rel in _CONFORMANCE_SOURCE_FILES:
        p = _GPUSIM_ROOT / rel
        if p.is_file():
            h.update(rel.encode("utf-8"))
            h.update(b"\0")
            h.update(p.read_bytes())
            h.update(b"\0")
    return h.hexdigest()[:16]


def select_device(requested: str = "auto") -> str:
    """Resolve GPU/CPU execution device (``cuda``, ``mps``, or ``cpu``)."""
    req = requested.strip().lower()
    if req not in {"auto", "cuda", "mps", "cpu"}:
        raise ValueError(f"Unsupported gpusim device {requested!r}")
    if req == "cpu":
        return "cpu"
    try:
        import torch

        if req == "cuda":
            if torch.cuda.is_available():
                return "cuda"
            raise RuntimeError("Requested gpusim device 'cuda' is unavailable")
        if req == "mps":
            if torch.backends.mps.is_available():
                return "mps"
            raise RuntimeError("Requested gpusim device 'mps' is unavailable")
        if torch.cuda.is_available():
            return "cuda"
        if torch.backends.mps.is_available():
            return "mps"
    except ImportError:
        if req != "auto":
            raise
    return "cpu"


def _field(obj: ParsedIdfObject, index: int, default: str = "") -> str:
    if index >= len(obj.fields):
        return default
    val = obj.fields[index].strip()
    return val if val else default


def expand_ideal_loads_templates(idf_text: str) -> str:
    """Expand HVACTemplate:Thermostat + HVACTemplate:Zone:IdealLoadsAirSystem in Python.

    Leaves any other ``HVACTemplate:*`` objects untouched so the fail-closed
    subset whitelist rejects them cleanly.
    """
    objects = parse_expidf(idf_text)
    if not objects:
        return idf_text

    has_ideal = any(o.obj_type == "HVACTEMPLATE:ZONE:IDEALLOADSAIRSYSTEM" for o in objects)
    if not has_ideal:
        return idf_text

    # Fail-closed: if any non-IdealLoads HVACTemplate exists, do not expand.
    allowed_templates = {
        "HVACTEMPLATE:THERMOSTAT",
        "HVACTEMPLATE:ZONE:IDEALLOADSAIRSYSTEM",
    }
    for obj in objects:
        if obj.obj_type.startswith("HVACTEMPLATE:") and obj.obj_type not in allowed_templates:
            return idf_text

    thermostats: dict[str, ParsedIdfObject] = {}
    for obj in objects:
        if obj.obj_type == "HVACTEMPLATE:THERMOSTAT":
            thermostats[_field(obj, 0).casefold()] = obj

    rebuilt_blocks: list[str] = []
    extra_blocks: list[str] = [
        "ScheduleTypeLimits,\n  HVACTemplate Any Number;",
        (
            "Schedule:Compact,\n  HVACTemplate-Always 4,\n  HVACTemplate Any Number,\n"
            "  Through: 12/31,\n  For: AllDays,\n  Until: 24:00,\n  4;"
        ),
    ]
    const_scheds_emitted: set[str] = set()

    for obj in objects:
        if obj.obj_type in allowed_templates:
            continue
        if obj.fields:
            rebuilt_blocks.append(f"{obj.raw_type},\n  " + ",\n  ".join(obj.fields) + ";")
        else:
            rebuilt_blocks.append(f"{obj.raw_type};")

    for obj in objects:
        if obj.obj_type != "HVACTEMPLATE:ZONE:IDEALLOADSAIRSYSTEM":
            continue
        zone_name = _field(obj, 0)
        tstat_name = _field(obj, 1)
        avail_sched = _field(obj, 2, "")
        max_heat_t = _field(obj, 3, "50")
        min_cool_t = _field(obj, 4, "13")
        max_heat_w = _field(obj, 5, "0.0156")
        min_cool_w = _field(obj, 6, "0.0077")
        heat_limit = _field(obj, 7, "NoLimit")
        max_heat_flow = _field(obj, 8, "")
        max_heat_cap = _field(obj, 9, "")
        cool_limit = _field(obj, 10, "NoLimit")
        max_cool_flow = _field(obj, 11, "")
        max_cool_cap = _field(obj, 12, "")
        heat_avail = _field(obj, 13, "")
        cool_avail = _field(obj, 14, "")
        dehum_ctrl = _field(obj, 15, "ConstantSensibleHeatRatio")
        cool_shr = _field(obj, 16, "0.7")
        hum_ctrl = _field(obj, 18, "None")
        oa_method = _field(obj, 20, "None")
        oa_dsoa = _field(obj, 24, "")
        dcv = _field(obj, 25, "None")
        econ = _field(obj, 26, "NoEconomizer")
        hr_type = _field(obj, 27, "None")
        hr_sens = _field(obj, 28, "0.70")
        hr_lat = _field(obj, 29, "0.65")

        oa_inlet = ""
        if oa_method.casefold() not in ("", "none"):
            oa_inlet = f"{zone_name} OA Inlet"

        tstat = thermostats.get(tstat_name.casefold())
        if tstat is not None:
            h_sched = _field(tstat, 1, "")
            h_const = _field(tstat, 2, "")
            c_sched = _field(tstat, 3, "")
            c_const = _field(tstat, 4, "")
            if not h_sched and h_const:
                h_sched = f"HVACTemplate-Always {h_const}"
                if h_sched not in const_scheds_emitted:
                    const_scheds_emitted.add(h_sched)
                    extra_blocks.append(
                        f"Schedule:Compact,\n  {h_sched},\n  HVACTemplate Any Number,\n"
                        f"  Through: 12/31,\n  For: AllDays,\n  Until: 24:00,\n  {h_const};"
                    )
            if not c_sched and c_const:
                c_sched = f"HVACTemplate-Always {c_const}"
                if c_sched not in const_scheds_emitted:
                    const_scheds_emitted.add(c_sched)
                    extra_blocks.append(
                        f"Schedule:Compact,\n  {c_sched},\n  HVACTemplate Any Number,\n"
                        f"  Through: 12/31,\n  For: AllDays,\n  Until: 24:00,\n  {c_const};"
                    )
            extra_blocks.append(
                f"ThermostatSetpoint:DualSetpoint,\n  {tstat_name} Dual SP Control,\n"
                f"  {h_sched},\n  {c_sched};"
            )
            extra_blocks.append(
                f"ZoneControl:Thermostat,\n  {zone_name} Thermostat,\n  {zone_name},\n"
                f"  HVACTemplate-Always 4,\n  ThermostatSetpoint:DualSetpoint,\n"
                f"  {tstat_name} Dual SP Control;"
            )

        extra_blocks.append(
            f"ZoneHVAC:EquipmentConnections,\n  {zone_name},\n  {zone_name} Equipment,\n"
            f"  {zone_name} Ideal Loads Supply Inlet,\n  ,\n"
            f"  {zone_name} Zone Air Node,\n  {zone_name} Return Outlet;"
        )
        extra_blocks.append(
            f"ZoneHVAC:EquipmentList,\n  {zone_name} Equipment,\n  SequentialLoad,\n"
            f"  ZoneHVAC:IdealLoadsAirSystem,\n  {zone_name} Ideal Loads Air System,\n"
            f"  1,\n  1,\n  ,\n  ;"
        )
        ideal_fields = [
            f"{zone_name} Ideal Loads Air System",
            avail_sched,
            f"{zone_name} Ideal Loads Supply Inlet",
            "",
            "",
            max_heat_t,
            min_cool_t,
            max_heat_w,
            min_cool_w,
            heat_limit,
            max_heat_flow,
            max_heat_cap,
            cool_limit,
            max_cool_flow,
            max_cool_cap,
            heat_avail,
            cool_avail,
            dehum_ctrl,
            cool_shr,
            hum_ctrl,
            oa_dsoa,
            oa_inlet,
            dcv,
            econ,
            hr_type,
            hr_sens,
            hr_lat,
        ]
        extra_blocks.append(
            "ZoneHVAC:IdealLoadsAirSystem,\n  " + ",\n  ".join(ideal_fields) + ";"
        )

    return "\n\n".join(rebuilt_blocks + extra_blocks) + "\n"


def _is_spot_checked(building_id: str, fraction: float, seed: int) -> bool:
    if fraction <= 0.0:
        return False
    if fraction >= 1.0:
        return True
    digest = hashlib.sha256(f"{seed}:{building_id}".encode("utf-8")).digest()
    val = int.from_bytes(digest[:8], "big") / float(1 << 64)
    return val < fraction


@dataclass(frozen=True)
class RoutingDecision:
    """Per-building routing outcome and provenance metadata."""

    building_id: str
    requested_engine: str
    selected_engine: str
    subset_rung: str | None
    reason: str
    spot_checked: bool
    engine_version: str
    conformance_hash: str

    def to_provenance_dict(self) -> dict[str, Any]:
        return {
            "engine": self.selected_engine,
            "engine_version": self.engine_version,
            "subset_rung": self.subset_rung,
            "conformance_hash": self.conformance_hash,
            "requested_engine": self.requested_engine,
            "routing_reason": self.reason,
            "spot_checked": self.spot_checked,
        }


_RUNG_ORDER: dict[str, int] = {"S0": 0, "S1": 1, "S2a": 2, "S3": 3, "S2b": 4}


def check_supported_subset(
    idf_text: str,
    max_rung: str = "S0",
) -> tuple[str | None, SubsetCheckResult]:
    """Evaluate expanded IDF against supported gpusim rungs in order."""
    expanded = expand_ideal_loads_templates(idf_text)
    res_s0 = check_s0_subset(expanded)
    if res_s0.passed:
        return "S0", res_s0
    if max_rung == "S0":
        return None, res_s0
    from openubem.gpusim.general_model import check_general_subset

    rung, res_gen = check_general_subset(idf_text)
    if res_gen.passed and rung is not None:
        if _RUNG_ORDER.get(rung, 99) <= _RUNG_ORDER.get(max_rung, 0):
            return rung, res_gen
        return None, SubsetCheckResult(
            False, f"IDF requires rung {rung} > max_rung={max_rung}"
        )
    return None, res_gen


def route_idf_text(
    idf_text: str,
    building_id: str,
    *,
    sim_engine: str = "energyplus",
    device: str = "auto",
    spot_check_fraction: float = 0.05,
    spot_check_seed: int = 42,
    eplus_version: str = "23.1",
    max_rung: str = "S0",
) -> RoutingDecision:
    """Route a single building IDF fail-closed between EnergyPlus and gpusim."""
    mode = sim_engine.strip().lower()
    if mode not in VALID_SIM_ENGINES:
        raise ValueError(
            f"Invalid SIM_ENGINE={sim_engine!r}; expected one of {sorted(VALID_SIM_ENGINES)}"
        )
    chash = conformance_hash()
    if mode == "energyplus":
        return RoutingDecision(
            building_id=building_id,
            requested_engine=mode,
            selected_engine="energyplus",
            subset_rung=None,
            reason="sim_engine=energyplus",
            spot_checked=False,
            engine_version=f"energyplus-{eplus_version}",
            conformance_hash=chash,
        )

    rung, check = check_supported_subset(idf_text, max_rung=max_rung)
    if not check.passed or rung is None:
        return RoutingDecision(
            building_id=building_id,
            requested_engine=mode,
            selected_engine="energyplus",
            subset_rung=None,
            reason=f"fallback_energyplus:{check.reason}",
            spot_checked=False,
            engine_version=f"energyplus-{eplus_version}",
            conformance_hash=chash,
        )

    if mode == "auto" and _is_spot_checked(building_id, spot_check_fraction, spot_check_seed):
        return RoutingDecision(
            building_id=building_id,
            requested_engine=mode,
            selected_engine="energyplus",
            subset_rung=rung,
            reason="spot_check_sample",
            spot_checked=True,
            engine_version=f"energyplus-{eplus_version}",
            conformance_hash=chash,
        )

    resolved_dev = select_device(device)
    return RoutingDecision(
        building_id=building_id,
        requested_engine=mode,
        selected_engine="gpusim",
        subset_rung=rung,
        reason=f"accepted:{rung}",
        spot_checked=False,
        engine_version=f"gpusim-{GPUSIM_VERSION}-{resolved_dev}",
        conformance_hash=chash,
    )


def write_routing_report_csv(
    decisions: list[RoutingDecision],
    out_path: Path,
) -> Path:
    """Write per-building routing decisions and reasons to CSV."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "building_id",
        "requested_engine",
        "selected_engine",
        "subset_rung",
        "reason",
        "spot_checked",
        "engine_version",
        "conformance_hash",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for dec in decisions:
            row = asdict(dec)
            row["subset_rung"] = row["subset_rung"] or ""
            writer.writerow(row)
    return out_path


def _slice_batch(batch: BatchSpec, start: int, end: int) -> BatchSpec:
    from dataclasses import fields as dc_fields

    target_b = end - start
    kwargs: dict[str, Any] = {}
    for fld in dc_fields(BatchSpec):
        name = fld.name
        val = getattr(batch, name)
        if name == "batch_size":
            kwargs[name] = target_b
        elif name in ("max_surfaces", "steps_per_hour"):
            kwargs[name] = val
        elif isinstance(val, list):
            kwargs[name] = val[start:end]
        elif isinstance(val, np.ndarray):
            kwargs[name] = np.ascontiguousarray(val[start:end])
        else:
            kwargs[name] = val
    return BatchSpec(**kwargs)


def run_routed_gpusim_batch(
    idf_paths: list[Path],
    epw_paths: list[Path],
    work_dirs: list[Path],
    building_ids: list[str],
    decisions: list[RoutingDecision],
    *,
    device: str = "auto",
    schedule_dirs: list[Path] | None = None,
    run_chunk_days: int = 1,
) -> list[dict[str, Any]]:
    """Compile and execute a batch of gpusim-routed buildings, writing eplusout.csv."""
    if not building_ids:
        return []
    resolved_dev = select_device(device)
    t0 = time.perf_counter()

    expidf_paths: list[Path] = []
    extra_sched_dirs: list[Path] = list(schedule_dirs or [])
    for idf_p, wd in zip(idf_paths, work_dirs, strict=True):
        wd.mkdir(parents=True, exist_ok=True)
        raw_text = Path(idf_p).read_text(encoding="utf-8", errors="replace")
        exp_text = expand_ideal_loads_templates(raw_text)
        exp_path = wd / "gpusim_expanded.expidf"
        exp_path.write_text(exp_text, encoding="utf-8")
        expidf_paths.append(exp_path)
        if Path(idf_p).parent not in extra_sched_dirs:
            extra_sched_dirs.append(Path(idf_p).parent)

    weather_cache: dict[Path, WeatherSeries] = {}
    weathers: list[WeatherSeries] = []
    epw_names: list[str] = []
    for epw_p in epw_paths:
        epw_res = Path(epw_p).resolve()
        if epw_res not in weather_cache:
            weather_cache[epw_res] = load_epw_weather(epw_res, steps_per_hour=12)
        weathers.append(weather_cache[epw_res])
        epw_names.append(epw_res.name)

    # Split S0 buildings (ultra-fast S0 kernel) from general S1/S2a/S3/S2b buildings (general CUDA kernel)
    s0_indices = [i for i, d in enumerate(decisions) if (d.subset_rung or "S0") == "S0"]
    gen_indices = [i for i, d in enumerate(decisions) if (d.subset_rung or "S0") != "S0"]

    hourly_all = np.zeros((len(building_ids), 8760), dtype=np.float64)
    wu_all = np.zeros(len(building_ids), dtype=np.int32)

    if s0_indices:
        s0_exp = [expidf_paths[i] for i in s0_indices]
        s0_ids = [building_ids[i] for i in s0_indices]
        s0_epw_names = [epw_names[i] for i in s0_indices]
        s0_weathers = [weathers[i] for i in s0_indices]
        batch = compile_expidf_batch(
            s0_exp,
            cell_ids=s0_ids,
            epw_ids=s0_epw_names,
            schedule_dirs=extra_sched_dirs,
            max_rung="S0",
        )
        b_total = batch.batch_size
        if resolved_dev in {"cuda", "mps"}:
            from openubem.gpusim.backends.stage_c import run_packed_stage_c

            sub_limit = CUDA_MAX_SUBBATCH if resolved_dev == "cuda" else b_total
            hourly_chunks: list[np.ndarray] = []
            wu_chunks: list[np.ndarray] = []
            for s0 in range(0, b_total, sub_limit):
                s1 = min(s0 + sub_limit, b_total)
                sb = _slice_batch(batch, s0, s1) if (s0 > 0 or s1 < b_total) else batch
                sw = s0_weathers[s0:s1]
                w_sites, s_idx = deduplicate_weather(sw, sb.batch_size)
                packed = pack(sb, w_sites, s_idx, ctf=None)
                res_sub, _ = run_packed_stage_c(
                    packed=packed,
                    cell_ids=sb.cell_ids,
                    record_zone_temp=False,
                    force_warmup_days=None,
                    run_chunk_days=run_chunk_days,
                    device=resolved_dev,
                )
                hourly_chunks.append(res_sub.hourly_heating_j)
                wu_chunks.append(res_sub.warmup_days)
            s0_hr = np.concatenate(hourly_chunks, axis=0)
            s0_wu = np.concatenate(wu_chunks, axis=0)
        else:
            res_sa = run_stage_a_batch(batch, s0_weathers, record_zone_temp=False)
            s0_hr = res_sa.hourly_heating_j
            s0_wu = res_sa.warmup_days
        for j, orig_i in enumerate(s0_indices):
            hourly_all[orig_i] = s0_hr[j]
            wu_all[orig_i] = s0_wu[j]

    if gen_indices:
        from openubem.gpusim.backends.general_cuda import run_general_cuda
        from openubem.gpusim.general_model import compile_general_batch

        gen_exp = [expidf_paths[i] for i in gen_indices]
        gen_ids = [building_ids[i] for i in gen_indices]
        gen_weathers = [weathers[i] for i in gen_indices]
        w_sites, s_idx = deduplicate_weather(gen_weathers, len(gen_indices))
        gb = compile_general_batch(
            gen_exp,
            gen_weathers,
            s_idx,
            building_ids=gen_ids,
            schedule_dirs=extra_sched_dirs,
            compute_shading=True,
            shading_device="cuda" if resolved_dev == "cuda" else "cpu",
        )
        res_gen = run_general_cuda(gb, w_sites, record_zone_temp=False, run_chunk_days=run_chunk_days)
        for j, orig_i in enumerate(gen_indices):
            hourly_all[orig_i] = res_gen.hourly_heating_j[j]
            wu_all[orig_i] = res_gen.warmup_days[j]

    b_total = len(building_ids)
    sim_res = SimulationResult(
        cell_ids=list(building_ids),
        hourly_heating_j=hourly_all,
        annual_heating_kwh=np.sum(hourly_all, axis=1, dtype=np.float64) / 3.6e6,
        warmup_days=wu_all,
        zone_air_temp_c=None,
        zone_mean_air_temp_c=None,
    )

    wall_total = time.perf_counter() - t0
    per_bldg_wall = wall_total / float(max(1, b_total))

    results: list[dict[str, Any]] = []
    for bi, (bid, wd, epw_p, dec) in enumerate(
        zip(building_ids, work_dirs, epw_paths, decisions, strict=True)
    ):
        hourly_j = sim_res.hourly_heating_j[bi]
        ann_kwh = float(annual_heating_kwh(hourly_j))
        write_eplusout_csv(wd / "eplusout.csv", hourly_j)
        prov = dec.to_provenance_dict()
        prov["warmup_days"] = int(sim_res.warmup_days[bi])
        prov["heating_kwh"] = ann_kwh
        prov["wall_clock_s"] = round(per_bldg_wall, 6)
        (wd / "gpusim_provenance.json").write_text(
            json.dumps(prov, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (wd / "eplusout.end").write_text(
            f"gpusim Completed Successfully-- 0 Warning; 0 Severe Errors; "
            f"Elapsed Time={per_bldg_wall:.3f}s\n",
            encoding="utf-8",
        )
        results.append(
            {
                "osm_id": bid,
                "status": "success",
                "wall_clock_s": per_bldg_wall,
                "n_warnings": 0,
                "n_severe": 0,
                "error_summary": "",
                "epw_path": str(epw_p),
                "heating_kwh": ann_kwh,
                "warmup_days": int(sim_res.warmup_days[bi]),
                "provenance": prov,
            }
        )
    return results
