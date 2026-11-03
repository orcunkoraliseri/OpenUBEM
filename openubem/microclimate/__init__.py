"""Stage 6 — outdoor microclimate & thermal comfort (UTCI).

PLAN docs/docs_DONE/OUTDOOR/UTCI/implementation/PLAN_utci_microclimate_implementation.md.
Separate analysis product (plan §6a) — never imported from Stage 1-5 code paths.
run_step6() is the T18 entry point; every other T0x module is imported lazily by it
so that `import openubem.microclimate` never requires rasterio/scipy at import time.

§6a / T18 "How" (F-08, F-15, F-16) — run_dir vs. output_dir (documented once, loudly):
`run_dir` is Stage 1-5's own artifact root, opened READ-ONLY end to end (buildings, EPW,
05_results.gpkg) — Stage 6 "reads Stage 5 read-only, never writes back" (§6a). `output_dir`
(default = run_dir) is where every 06_mc_* artifact lands, per F-08's "run output-dir root"
convention. The two are the SAME path for a normal fresh Stage 1-5 run (run_dir is the user's
own mutable output tree, exactly what F-08 assumes). They diverge deliberately when run_dir is
a frozen, git-tracked validation snapshot (docs/docs_VALIDATION/.../phaseE/<cell>/, F-15) — CP-4's
own gate requires `git status --porcelain` show NO modification under docs/docs_VALIDATION/, and
that directory was measured git-tracked and clean (2026-07-24, 14 files, nyc_centre); writing
06_mc_* there would trip the gate on the very first live run. Callers running Stage 6 against a
validation cell (scripts/run_step6_microclimate.py, T22) MUST pass an explicit output_dir outside
docs_VALIDATION/ — see that script for the concrete policy.

Wall-azimuth simplification (Tier "empirical", surfaces.py's own single-node isotropic model,
consistent with mrt.py's own k_glob_wall docstring: "no per-orientation wall-irradiance model in
this arc"): a single representative south-facing wall (WALL_AZIMUTH_DEFAULT_DEG = 180.0) is used
for the whole domain, exactly the convention the CP-3 evidence bundle already established
(scratchpad/cp3_nyc_evidence.py) — not a new invention introduced here.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from openubem import config

WALL_AZIMUTH_DEFAULT_DEG = 180.0  # module docstring — south-facing representative wall
MORPH_WIND_DIRECTION_BIN_DEG = 22.5  # 16-point compass — performance cache key for T15's
# macdonald tier (module docstring below in _macdonald_wind): lambda_p/lambda_f/mean_height
# depend on wind direction only through a continuous frontal-projection axis; snapping to a
# 16-point compass bin is a documented, bounded spatial-resolution approximation (same status
# as wind.py's own window_radius_m — a caller-chosen SCALE, not a cited physical constant),
# applied purely to avoid re-rasterizing every building's footprint every single hour.


def _resolve_buildings_path(run_dir: Path) -> Path:
    """F-15: accept both 01_buildings_clean.gpkg (fresh Stage-1 runs) and 01_buildings.gpkg
    (archived phaseE cells), preferring the former."""
    clean = run_dir / "01_buildings_clean.gpkg"
    if clean.exists():
        return clean
    legacy = run_dir / "01_buildings.gpkg"
    if legacy.exists():
        return legacy
    raise FileNotFoundError(
        f"run_step6: neither 01_buildings_clean.gpkg nor 01_buildings.gpkg found under {run_dir}"
    )


def _resolve_epw(run_dir: Path, output_dir: Path, buildings_gdf, epw_path):
    """F-16's 3-step ladder, in the order T18's own "How" specifies:
    1. explicit epw_path; 2. run_dir/weather/*.epw; 3. re-resolve from the building centroid via
    epw_manager.resolve_station + fetch_epw(offline=True), against the global cache. fetch_epw's
    own destination is output_dir (never run_dir — module docstring's read-only invariant), and
    it raises rather than silently falling back to a different city's weather (rule 14)."""
    if epw_path is not None:
        return Path(epw_path), "explicit_epw_path"

    weather_dir = run_dir / "weather"
    if weather_dir.exists():
        candidates = sorted(weather_dir.glob("*.epw"))
        if candidates:
            return candidates[0], "run_dir_weather"

    from openubem.acquisition import epw_manager

    centroid = buildings_gdf.to_crs("EPSG:4326").union_all().centroid
    stations = epw_manager.load_stations()
    station, dist_km = epw_manager.resolve_station(centroid.y, centroid.x, stations)
    dest = epw_manager.fetch_epw(station, offline=True, output_dir=output_dir)
    return dest, f"cache_resolved:station={station['station_id']}:dist_km={dist_km:.1f}"


def _parse_epw_location(epw_path) -> tuple:
    """LOCATION,<name>,<state>,<country>,<source>,<wmo>,<lat>,<lon>,<utc_offset>,<elevation_m>
    — the same 9-field header both epw_manager.py and solar.py's own convention note assume."""
    with open(epw_path, encoding="utf-8", errors="replace") as fh:
        line = fh.readline()
    parts = line.strip().split(",")
    if not line.startswith("LOCATION") or len(parts) < 10:
        raise ValueError(f"run_step6: unparseable EPW LOCATION line in {epw_path}: {line!r}")
    lat, lon, utc_offset_h, elevation_m = (float(parts[i]) for i in (6, 7, 8, 9))
    return lat, lon, utc_offset_h, elevation_m


def _git_commit() -> "str | None":
    try:
        repo_root = Path(__file__).resolve().parents[2]
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo_root, capture_output=True, text=True, timeout=5,
        )
        return out.stdout.strip() if out.returncode == 0 else None
    except Exception:
        return None


def _macdonald_wind(v10_ms, buildings_gdf, domain, wind_direction_deg, morph_cache, *, window_radius_m=50.0):
    """T15's macdonald tier, direction-binned (module docstring) so morphometric_parameters'
    per-building footprint rasterization runs at most once per 16-point compass bin actually
    encountered in the window, not once per hour. flags bitmask matches wind.py's own
    WIND_FLAG_VA10_CLAMPED / WIND_FLAG_MACDONALD_DOMAIN_INVALID / WIND_FLAG_MACDONALD_NUMERICAL_ANOMALY
    convention (E-UTCI-07, E-UTCI-08)."""
    from openubem.microclimate import wind as wind_mod

    bin_deg = float(round(wind_direction_deg / MORPH_WIND_DIRECTION_BIN_DEG) * MORPH_WIND_DIRECTION_BIN_DEG % 360.0)
    if bin_deg not in morph_cache:
        morph_cache[bin_deg] = wind_mod.morphometric_parameters(
            buildings_gdf, domain, bin_deg, window_radius_m=window_radius_m
        )
    lambda_p, lambda_f, mean_height_m = morph_cache[bin_deg]
    v_1p1, domain_invalid, numerical_anomaly = wind_mod.pedestrian_wind_macdonald(
        v10_ms, lambda_p, lambda_f, mean_height_m
    )
    factor = wind_mod.cost730_factor()
    va10_raw = v_1p1 / factor
    va10_eq = np.clip(va10_raw, 0.5, 17.0)
    flags = (va10_raw != va10_eq).astype(np.uint8) * wind_mod.WIND_FLAG_VA10_CLAMPED
    flags = flags | (domain_invalid.astype(np.uint8) * wind_mod.WIND_FLAG_MACDONALD_DOMAIN_INVALID)
    flags = flags | (numerical_anomaly.astype(np.uint8) * wind_mod.WIND_FLAG_MACDONALD_NUMERICAL_ANOMALY)
    return v_1p1, va10_eq, flags


def _run_tier2_wall_temps(
    run_dir, window_index, epw_path, altitude_arr, azimuth_arr, *,
    resim_work_root=None, n_jobs=-1, keep_scratch=False, override_annual=False,
) -> dict:
    """T13 Tier-2 wiring: patch+run the archived IDF copies over the selected window, harvest
    real EnergyPlus exterior wall temperatures, and reduce them to one representative scalar per
    hour via a cos(incidence)-weighted mean across every harvested wall (same Duffie & Beckman
    solar-incidence weight already used by surfaces.py::wall_temperature_empirical) — the
    spatially-uniform-per-hour convention this arc's single-node wall model already uses
    (module docstring), now sourced from real E+ surfaces instead of the empirical formula.
    Returns {timestamp: t_wall_c}; a timestamp absent from the dict means no harvested data for
    that hour (caller falls back to the empirical tier for it)."""
    from openubem.microclimate import resim as resim_mod

    cell_name = Path(run_dir).name
    archive = Path(run_dir) / f"{cell_name}_step3_idfs_archive.zip"
    if not archive.exists():
        raise FileNotFoundError(
            f"run_step6(wall_temp_tier='energyplus'): no IDF archive at {archive} — Tier-2 "
            "requires <cell>_step3_idfs_archive.zip (F-15's archive-naming convention)."
        )
    work_root = Path(resim_work_root) if resim_work_root is not None else Path(tempfile.mkdtemp(prefix="utci_resim_"))
    idf_paths = resim_mod.extract_idf_archive(archive, work_root / "extracted")

    start = window_index[0]
    n_days = int(np.ceil(len(window_index) / 24.0))
    sim_results = resim_mod.run_resim_side_leg(
        idf_paths, str(epw_path), work_root, window_mode="design_hours",
        window_start_month=int(start.month), window_start_day=int(start.day),
        window_n_days=n_days, n_jobs=n_jobs, override_annual=override_annual,
    )

    sql_paths_by_building = {}
    patched_dir = work_root / "patched_idfs"
    for res, idf_path in zip(sim_results, idf_paths):
        status = str(res.get("status", ""))
        sql_path = res.get("sql_path")
        if status.startswith("success") and sql_path:
            building_id = Path(idf_path).stem
            sql_paths_by_building[building_id] = (sql_path, str(patched_dir / f"{building_id}.idf"))

    harvested = resim_mod.harvest_wall_temperatures(sql_paths_by_building)
    resim_mod.quarantine_or_delete(work_root, keep=keep_scratch)
    if harvested.empty:
        return {}

    lookup = {}
    for i, ts in enumerate(window_index):
        sql_hour = ts.hour + 1  # EPW/SQL 1-24 convention, T02's own "hour 24 -> 23:00" mapping inverted
        sub = harvested[
            (harvested["Month"] == ts.month) & (harvested["Day"] == ts.day) & (harvested["Hour"] == sql_hour)
        ]
        if sub.empty:
            continue
        alt, az = float(altitude_arr[i]), float(azimuth_arr[i])
        cos_inc = np.clip(np.cos(np.radians(alt)) * np.cos(np.radians(az - sub["azimuth_deg"].to_numpy())), 0.0, None)
        cos_inc = cos_inc if alt > 0.0 else np.zeros_like(cos_inc)
        if cos_inc.sum() > 1e-9:
            lookup[ts] = float(np.average(sub["t_wall_c"].to_numpy(), weights=cos_inc))
        else:
            lookup[ts] = float(sub["t_wall_c"].mean())
    return lookup


def run_step6(
    run_dir,
    *,
    output_dir=None,
    epw_path=None,
    buildings_path=None,
    res_m: "float | None" = None,
    buffer_m: "float | None" = None,
    n_azimuths: "int | None" = None,
    window_mode: "str | None" = None,
    design_hours: "list[tuple[int, int, int]] | None" = None,
    override_annual_energyplus: bool = False,
    vegetation_tier: "str | None" = None,
    wall_temp_tier: "str | None" = None,
    wind_tier: "str | None" = None,
    ta_tier: str = "tier0",
    tree_points=None,
    canopy_gdf=None,
    landcover_gdf=None,
    cdsm_path=None,
    tdsm_path=None,
    dem_path=None,
    resim_work_root=None,
    resim_n_jobs: int = -1,
    resim_keep_scratch: bool = False,
    ground_albedo_override: "float | None" = None,
    wall_albedo_override: "float | None" = None,
    canopy_tau_override: "float | None" = None,
) -> Path:
    """Stage-6 entry point (T18). See the module docstring for the run_dir/output_dir contract.

    Static geometry (domain, SVF/horizon) is built once and cached to 06_mc_horizon.npz
    (§4.9) — a re-run with the identical domain/resolution/azimuth count reuses it. Every
    other field is per-hour, looped over the selected analysis window (T17). Determinism
    (rule 13): no stochastic operation anywhere in this chain — a re-run with identical inputs
    produces byte-identical rasters.

    ground_albedo_override / wall_albedo_override / canopy_tau_override (T24, plan §7): each
    defaults to None, which reproduces the EXACT prior behaviour (domain_mod.DEFAULT_GROUND_ALBEDO,
    mrt.WALL_ALBEDO, domain_mod.deciduous_transmissivity(ts.month) respectively) — every existing
    caller and the determinism/byte-identical tests are unaffected. When set, they expose three
    ALREADY-EXISTING, already-cited physics inputs (domain.py's ground_albedo, mrt.py's
    wall_albedo kwarg, shadow.py's canopy_tau kwarg) as scenario-engine levers for T24's
    `scenarios.py` — no new physics, no new formula, only parameterising three inputs that were
    previously hardcoded at their default call sites.
    """
    import geopandas as gpd

    from openubem.microclimate import airtemp, domain as domain_mod, exposure, mrt, psychro
    from openubem.microclimate import raster_io, shadow, solar, surfaces
    from openubem.microclimate import svf as svf_mod
    from openubem.microclimate import utci as utci_mod, wind as wind_mod, window as window_mod
    from openubem.microclimate.epw_hourly import read_epw_hourly

    run_dir = Path(run_dir)
    output_dir = Path(output_dir) if output_dir is not None else run_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    res_m = float(res_m) if res_m is not None else config.UTCI_GRID_RES_M
    buffer_m = float(buffer_m) if buffer_m is not None else config.UTCI_DOMAIN_BUFFER_M
    n_azimuths = int(n_azimuths) if n_azimuths is not None else config.UTCI_SVF_AZIMUTHS
    window_mode = window_mode or config.UTCI_ANALYSIS_WINDOW
    vegetation_tier = vegetation_tier or config.UTCI_VEGETATION_TIER
    wall_temp_tier = wall_temp_tier or config.UTCI_WALL_TEMP_TIER
    wind_tier = wind_tier or config.UTCI_WIND_TIER

    manifest: dict = {
        "run_dir": str(run_dir), "output_dir": str(output_dir),
        "started_utc": pd.Timestamp.now("UTC").isoformat(),
    }

    # ---- buildings (F-15) ----
    buildings_path = Path(buildings_path) if buildings_path is not None else _resolve_buildings_path(run_dir)
    buildings_gdf = gpd.read_file(buildings_path)
    manifest["buildings_path"] = str(buildings_path)
    manifest["n_buildings"] = int(len(buildings_gdf))

    # ---- EPW (F-16) ----
    epw_resolved_path, epw_source_step = _resolve_epw(run_dir, output_dir, buildings_gdf, epw_path)
    lat, lon, utc_offset_h, _elev = _parse_epw_location(epw_resolved_path)
    manifest["epw_path"] = str(epw_resolved_path)
    manifest["epw_resolution_step"] = epw_source_step
    manifest["epw_lat"], manifest["epw_lon"], manifest["epw_utc_offset_h"] = lat, lon, utc_offset_h

    epw_df = read_epw_hourly(epw_resolved_path)

    # ---- domain + vegetation (T08/T09) ----
    dom_kwargs = {}
    if ground_albedo_override is not None:
        dom_kwargs["ground_albedo"] = float(ground_albedo_override)
    dom = domain_mod.build_domain(buildings_gdf, res_m=res_m, buffer_m=buffer_m, dem_path=dem_path, landcover_gdf=landcover_gdf, **dom_kwargs)
    manifest["domain_shape"] = list(dom.shape)
    manifest["dem_source"] = dom.dem_source
    manifest["landcover_tier"] = dom.landcover_tier
    manifest["n_excluded_no_height"] = len(dom.excluded_building_ids)
    manifest["excluded_building_ids_no_height"] = list(dom.excluded_building_ids)

    cdsm, tdsm, lai, veg_meta = domain_mod.build_vegetation(
        dom.shape, dom.transform, tier=vegetation_tier, tree_points=tree_points,
        canopy_gdf=canopy_gdf, cdsm_path=cdsm_path, tdsm_path=tdsm_path,
    )
    manifest.update(veg_meta)

    # ---- SVF (T10), cached by domain_hash ----
    svf_cache_path = output_dir / "06_mc_horizon.npz"
    dhash = svf_mod.domain_hash(dom, n_azimuths)
    svf_arr = horizon = None
    if svf_cache_path.exists():
        cached = np.load(svf_cache_path)
        if str(cached["domain_hash"]) == dhash:
            svf_arr, horizon = cached["svf"], cached["horizon_angles"]
    if svf_arr is None:
        svf_arr, horizon = svf_mod.compute_svf(dom, n_azimuths=n_azimuths)
        np.savez_compressed(svf_cache_path, svf=svf_arr, horizon_angles=horizon, domain_hash=dhash)
    manifest["n_azimuths"] = n_azimuths
    outside0 = ~dom.building_mask
    manifest["svf_mean"] = float(np.mean(svf_arr[outside0])) if outside0.any() else None

    raster_io.write_geotiff(output_dir / "06_mc_domain_dsm.tif", dom.dsm, dom, mask_buildings=False)
    raster_io.write_geotiff(output_dir / "06_mc_svf.tif", svf_arr, dom)

    # ---- analysis window (T17) ----
    window_index = window_mod.select_window(
        epw_df, mode=window_mode, design_hours=design_hours, wall_temp_tier=wall_temp_tier,
        override_annual_energyplus=override_annual_energyplus,
    )
    manifest["window_mode"] = window_mode
    manifest["window_start"] = str(window_index[0])
    manifest["window_end"] = str(window_index[-1])
    manifest["window_n_hours"] = int(len(window_index))

    utc_index = window_index - pd.Timedelta(hours=utc_offset_h)  # solar.py's own UTC convention
    altitude_arr, azimuth_arr = solar.solar_position(utc_index, lat, lon)

    # ---- Tier-2 wall temps (T13 resim wiring), opt-in ----
    tier2_wall_lookup = None
    if wall_temp_tier == "energyplus":
        tier2_wall_lookup = _run_tier2_wall_temps(
            run_dir, window_index, epw_resolved_path, altitude_arr, azimuth_arr,
            resim_work_root=resim_work_root, n_jobs=resim_n_jobs, keep_scratch=resim_keep_scratch,
            override_annual=override_annual_energyplus,
        )
        manifest["tier2_n_hours_harvested"] = len(tier2_wall_lookup)

    # ---- hourly loop (T02-T07, T11-T16) — chunked over time (§4.9's own directive): only the
    # UTCI stack is held fully in memory (exposure.py's PHEH/CTSI need the whole window); the
    # other four hourly fields stream straight to disk band-by-band. ----
    n_hours = len(window_index)
    shape = dom.shape
    nodata = config.UTCI_RASTER_NODATA
    band_labels = [str(ts.isoformat()) for ts in window_index]

    def _make_dataset(name):
        import rasterio
        profile = {
            "driver": "GTiff", "height": shape[0], "width": shape[1], "count": n_hours,
            "dtype": "float32", "crs": dom.crs, "transform": dom.transform, "nodata": nodata,
            "compress": "deflate", "tiled": True,
        }
        path = output_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        dst = rasterio.open(path, "w", **profile)
        for i, label in enumerate(band_labels, start=1):
            dst.set_band_description(i, label)
        return dst

    def _write_band(dst, band_idx, arr, *, mask_buildings=True):
        out = np.asarray(arr, dtype=np.float32).copy()
        if mask_buildings:
            out[dom.building_mask] = nodata
        out = np.where(np.isnan(out), nodata, out).astype(np.float32)
        dst.write(out, band_idx)

    dst_tmrt = _make_dataset("06_mc_tmrt_hourly.tif")
    dst_wind = _make_dataset("06_mc_wind_1p1m_hourly.tif")
    dst_ta = _make_dataset("06_mc_ta_hourly.tif")
    dst_flags = _make_dataset("06_mc_flags_hourly.tif")

    utci_stack = np.empty((n_hours, *shape), dtype=np.float32)

    used_measured_l_sky_hours = 0
    wind_clamp_cells = 0
    wind_macdonald_domain_invalid_cells = 0
    wind_macdonald_numerical_anomaly_cells = 0
    ta_clamp_cells = 0
    utci_flag_counts = {"ta": 0, "tmrt": 0, "wind": 0, "vapour": 0}
    morph_cache: dict = {}

    for i, ts in enumerate(window_index):
        row = epw_df.loc[ts]
        alt_deg, az_deg = float(altitude_arr[i]), float(azimuth_arr[i])
        ta_c = float(row["dry_bulb_c"])
        rh_pct = float(row["relative_humidity_pct"])
        e_kpa = float(psychro.vapour_pressure_kpa(ta_c, rh_pct))
        dni = float(row["direct_normal_wm2"]) if pd.notna(row["direct_normal_wm2"]) else 0.0
        dhi = float(row["diffuse_horizontal_wm2"]) if pd.notna(row["diffuse_horizontal_wm2"]) else 0.0
        horizontal_ir_val = row["horizontal_infrared_wm2"]
        horizontal_ir_arg = float(horizontal_ir_val) if pd.notna(horizontal_ir_val) else None
        v10 = float(row["wind_speed_ms"]) if pd.notna(row["wind_speed_ms"]) else 0.0
        wind_dir = float(row["wind_direction_deg"]) if pd.notna(row["wind_direction_deg"]) else 0.0

        if vegetation_tier != "none":
            canopy_tau_arg = (
                float(canopy_tau_override) if canopy_tau_override is not None
                else domain_mod.deciduous_transmissivity(ts.month)
            )
        else:
            canopy_tau_arg = None
        sh_building, sh_veg = shadow.cast_shadows(
            dom, alt_deg, az_deg, horizon_angles=horizon, n_azimuths=n_azimuths,
            cdsm=cdsm if vegetation_tier != "none" else None,
            tdsm=tdsm if vegetation_tier != "none" else None,
            canopy_tau=canopy_tau_arg,
        )

        l_sky, used_measured = mrt.sky_longwave(ta_c, e_kpa, horizontal_ir_arg)
        used_measured_l_sky_hours += int(np.asarray(used_measured).any())
        l_sky_scalar = float(np.asarray(l_sky))

        k_glob_grd = dni * max(np.sin(np.radians(alt_deg)), 0.0) * sh_building * sh_veg + dhi * svf_arr
        t_grd, _converged, _meta = surfaces.ground_temperature(dom, ta_c, k_glob_grd, l_sky_scalar, v10, t_sub_c=ta_c)

        if tier2_wall_lookup is not None and ts in tier2_wall_lookup:
            t_wall_scalar = tier2_wall_lookup[ts]
        else:
            t_wall_scalar = float(surfaces.wall_temperature_empirical(ta_c, alt_deg, az_deg, WALL_AZIMUTH_DEFAULT_DEG))
        t_wall = np.full(shape, t_wall_scalar, dtype=np.float32)

        veg_fraction = np.clip(cdsm > 0, 0, 1).astype(np.float64) if vegetation_tier != "none" else None

        mrt_kwargs = {}
        if wall_albedo_override is not None:
            mrt_kwargs["wall_albedo"] = float(wall_albedo_override)
        tmrt_c, _diag = mrt.compute_tmrt(
            altitude_deg=alt_deg, azimuth_deg=az_deg, dni_wm2=dni, dhi_wm2=dhi,
            svf=svf_arr, sh_building=sh_building, sh_veg=sh_veg,
            t_grd_c=t_grd, t_wall_c=t_wall, ta_c=ta_c, e_kpa=e_kpa,
            ground_albedo=dom.albedo, horizontal_infrared_wm2=l_sky_scalar,
            vegetation_fraction=veg_fraction, **mrt_kwargs,
        )

        if wind_tier == "macdonald":
            v_1p1, va10_eq, wflags = _macdonald_wind(v10, buildings_gdf, dom, wind_dir, morph_cache)
        else:
            v_1p1, va10_eq, wflags = wind_mod.pedestrian_wind(v10, shape, tier="cost730")
        wind_clamp_cells += int(np.sum((wflags & wind_mod.WIND_FLAG_VA10_CLAMPED) != 0))
        wind_macdonald_domain_invalid_cells += int(
            np.sum((wflags & wind_mod.WIND_FLAG_MACDONALD_DOMAIN_INVALID) != 0)
        )
        wind_macdonald_numerical_anomaly_cells += int(
            np.sum((wflags & wind_mod.WIND_FLAG_MACDONALD_NUMERICAL_ANOMALY) != 0)
        )

        ta_field, _ta_offset, taflags = airtemp.air_temperature_field(ta_c, shape, tier=ta_tier, svf=svf_arr, altitude_deg=alt_deg)
        ta_clamp_cells += int(np.sum(taflags))
        e_field = np.full(shape, e_kpa, dtype=np.float64)

        utci_c, uflags = utci_mod.utci_approx(ta_field, tmrt_c, va10_eq, e_field)
        utci_flag_counts["ta"] += int(np.sum((uflags & utci_mod.FLAG_TA) != 0))
        utci_flag_counts["tmrt"] += int(np.sum((uflags & utci_mod.FLAG_TMRT) != 0))
        utci_flag_counts["wind"] += int(np.sum((uflags & utci_mod.FLAG_WIND) != 0))
        utci_flag_counts["vapour"] += int(np.sum((uflags & utci_mod.FLAG_VAPOUR) != 0))

        combined_flags = (
            uflags.astype(np.uint16)
            | np.where(wflags, np.uint16(0x10), np.uint16(0))
            | np.where(taflags, np.uint16(0x20), np.uint16(0))
        ).astype(np.float32)

        band_idx = i + 1
        _write_band(dst_tmrt, band_idx, tmrt_c)
        _write_band(dst_wind, band_idx, v_1p1)
        _write_band(dst_ta, band_idx, ta_field)
        _write_band(dst_flags, band_idx, combined_flags)
        utci_stack[i] = utci_c.astype(np.float32)

    dst_tmrt.close()
    dst_wind.close()
    dst_ta.close()
    dst_flags.close()

    raster_io.write_geotiff(output_dir / "06_mc_utci_hourly.tif", utci_stack, dom, band_descriptions=band_labels)

    outside = ~dom.building_mask
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)  # all-NaN slice under buildings
        utci_masked = np.where(dom.building_mask[np.newaxis, :, :], np.nan, utci_stack)
        utci_peak = np.nanmax(utci_masked, axis=0)
        utci_mean = np.nanmean(utci_masked, axis=0)

    raster_io.write_geotiff(output_dir / "06_mc_utci_peak.tif", utci_peak, dom)
    raster_io.write_geotiff(output_dir / "06_mc_utci_mean.tif", utci_mean, dom)
    raster_io.write_classified_geotiff(output_dir / "06_mc_utci_peak_class.tif", utci_peak, dom)
    raster_io.write_classified_geotiff(output_dir / "06_mc_utci_mean_class.tif", utci_mean, dom)

    # ---- exposure (T20) ----
    dt_hours = np.ones(n_hours, dtype=np.float64)
    pheh_total, pheh_field_name, _pheh_per_cell = exposure.person_hours_extreme_heat(
        utci_masked, res_m=res_m, dt_hours=dt_hours,
    )
    ctsi_raster = exposure.cumulative_thermal_stress_index(utci_masked, dt_hours=dt_hours)
    raster_io.write_geotiff(output_dir / "06_mc_ctsi.tif", ctsi_raster, dom)

    results_df = None
    results_gpkg_path = run_dir / "05_results.gpkg"
    if results_gpkg_path.exists():
        results_df = gpd.read_file(results_gpkg_path)  # read-only open, §6a — never written back to
    parcel_gdf = exposure.aggregate_to_parcels(buildings_gdf, results_df, dom, utci_peak, utci_mean, ctsi_raster)
    parcel_gdf.to_file(output_dir / "06_mc_summary.gpkg", driver="GPKG")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        exposure_metrics = {
            pheh_field_name: pheh_total,
            "ctsi_mean_degc_h": float(np.nanmean(ctsi_raster[outside])) if outside.any() else None,
            "ctsi_max_degc_h": float(np.nanmax(ctsi_raster[outside])) if outside.any() else None,
            "utci_peak_max_c": float(np.nanmax(utci_peak)) if outside.any() else None,
            "utci_mean_mean_c": float(np.nanmean(utci_mean)) if outside.any() else None,
            "threshold_c": exposure.PHEH_THRESHOLD_C,
            "baseline_c": exposure.CTSI_BASELINE_C,
        }
    (output_dir / "06_mc_exposure_metrics.json").write_text(json.dumps(exposure_metrics, indent=2))

    # ---- manifest (T18) ----
    manifest["vegetation_tier"] = vegetation_tier
    manifest["wall_temp_tier"] = wall_temp_tier
    manifest["wind_tier"] = wind_tier
    manifest["ta_tier"] = ta_tier
    manifest["used_measured_l_sky_hour_fraction"] = used_measured_l_sky_hours / n_hours if n_hours else None
    manifest["wind_clamp_cell_hours"] = wind_clamp_cells
    manifest["wind_macdonald_domain_invalid_cell_hours"] = wind_macdonald_domain_invalid_cells
    manifest["wind_macdonald_numerical_anomaly_cell_hours"] = wind_macdonald_numerical_anomaly_cells
    manifest["ta_clamp_cell_hours"] = ta_clamp_cells
    manifest["utci_flag_counts"] = json.dumps(utci_flag_counts)
    manifest["git_commit"] = _git_commit()
    manifest["ended_utc"] = pd.Timestamp.now("UTC").isoformat()
    manifest["config_res_m"] = res_m
    manifest["config_buffer_m"] = buffer_m
    manifest["config_pedestrian_height_m"] = config.UTCI_PEDESTRIAN_HEIGHT_M
    manifest["config_z0_open_m"] = config.UTCI_Z0_OPEN_M
    manifest["config_raster_nodata"] = config.UTCI_RASTER_NODATA
    manifest["ground_albedo_override"] = ground_albedo_override
    manifest["wall_albedo_override"] = wall_albedo_override
    manifest["canopy_tau_override"] = canopy_tau_override
    pd.DataFrame([manifest]).to_parquet(output_dir / "06_mc_manifest.parquet")

    return output_dir
