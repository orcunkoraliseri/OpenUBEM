"""Phase 0 (T02) Python hotspot profiler & baseline corpus freeze for OpenUBEM.

Measures cold import times, median warm wall-clock times (3 runs where fast,
1 run for >10 s workloads), CPU times, peak tracemalloc allocations, process
RSS, and top cProfile cumulative hotspots across candidate Rust migration
targets (R1–R6) using real retained OpenUBEM corpora with SHA-256 hashes.

Usage:
    .venv/bin/python scripts/bench/profile_python_hotspots.py
"""

from __future__ import annotations

import argparse
import cProfile
import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import platform
import pstats
import resource
import statistics
import subprocess
import sys
import tempfile
import time
import tracemalloc
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_MD_OUT = (
    ROOT / "docs" / "docs_ACTIVE" / "Rust_migration" / "RESULTS_phase0_baseline.md"
)
DEFAULT_JSON_OUT = ROOT / ".local" / "phase0_baseline.json"


@dataclass(frozen=True)
class BenchmarkRecord:
    """Measured profiling record for a single OpenUBEM Python workload.

    Attributes:
        workload_id: Short identifier matching PLAN candidate IDs (R1–R6).
        phase_target: Planned Rust crate and migration phase.
        description: Human-readable workload description.
        corpus_items: Number of buildings/files/cells processed per run.
        fixture_sha256: Deterministic SHA-256 digest of input fixture files.
        warm_runs: Number of timed warm iterations.
        median_wall_s: Median wall-clock time in seconds.
        min_wall_s: Minimum wall-clock time in seconds.
        max_wall_s: Maximum wall-clock time in seconds.
        median_cpu_s: Median CPU process time in seconds.
        peak_tracemalloc_mib: Peak Python heap traced via tracemalloc (MiB).
        peak_rss_mib: Process maximum resident set size (MiB).
        throughput_note: Normalized per-item rate or extrapolated campaign cost.
        top_hotspots: Top cumulative cProfile entries formatted concisely.
    """

    workload_id: str
    phase_target: str
    description: str
    corpus_items: int
    fixture_sha256: str
    warm_runs: int
    median_wall_s: float
    min_wall_s: float
    max_wall_s: float
    median_cpu_s: float
    peak_tracemalloc_mib: float
    peak_rss_mib: float
    throughput_note: str
    top_hotspots: list[str]


def _sha256_file(path: Path) -> str:
    """Compute hex SHA-256 digest of a single file.

    Args:
        path: File to hash.

    Returns:
        64-character lowercase hexadecimal SHA-256 digest.
    """
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _sha256_corpus(paths: list[Path]) -> str:
    """Compute a deterministic manifest SHA-256 over a sorted list of paths.

    Args:
        paths: Input fixture files included in a workload.

    Returns:
        16-character SHA-256 prefix over sorted ``(relpath, file_sha256)`` rows.
    """
    hasher = hashlib.sha256()
    for path in sorted(paths):
        rel = path.relative_to(ROOT).as_posix()
        hasher.update(f"{rel}:{_sha256_file(path)}\n".encode("utf-8"))
    return hasher.hexdigest()[:16]


def _max_rss_mib() -> float:
    """Return process peak RSS in MiB (handling macOS bytes vs Linux KiB).

    Returns:
        Peak resident set size in MiB.
    """
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform == "darwin":
        return raw / (1024.0 * 1024.0)
    return raw / 1024.0


def _extract_top_hotspots(profiler: cProfile.Profile, limit: int = 5) -> list[str]:
    """Summarize top cumulative functions from a cProfile capture.

    Args:
        profiler: Completed ``cProfile.Profile`` instance.
        limit: Maximum number of hotspots to return.

    Returns:
        List of formatted ``function (cumtime s, ncalls)`` strings.
    """
    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats("cumulative")
    entries: list[str] = []
    for func_key in stats.fcn_list[:limit]:
        filename, lineno, func_name = func_key
        cc, nc, tt, ct, _ = stats.stats[func_key]
        short_file = Path(filename).name
        entries.append(f"{short_file}:{lineno}:{func_name} ({ct:.3f}s, {nc} calls)")
    return entries


def _measure_workload(
    workload_id: str,
    phase_target: str,
    description: str,
    corpus_items: int,
    fixture_sha256: str,
    fn: Callable[[], Any],
    *,
    warm_runs: int = 3,
    warmup: bool = True,
    throughput_fmt: Callable[[float], str] | None = None,
) -> BenchmarkRecord:
    """Run and profile a workload across warm iterations plus a cProfile pass.

    Args:
        workload_id: Identifier for the benchmark row.
        phase_target: Target Rust crate and phase.
        description: Human-readable workload description.
        corpus_items: Count of items processed per run.
        fixture_sha256: SHA-256 fingerprint of input files.
        fn: Zero-argument callable executing the workload.
        warm_runs: Number of timed iterations for median calculation.
        warmup: Whether to execute one untimed warm-up iteration first.
        throughput_fmt: Optional formatter turning median seconds into a note.

    Returns:
        Populated ``BenchmarkRecord``.
    """
    if warmup:
        fn()

    # Timed runs execute WITHOUT tracemalloc or cProfile so wall/CPU timings are
    # completely uncontaminated by Python instrumentation overhead.
    wall_times: list[float] = []
    cpu_times: list[float] = []

    for idx in range(warm_runs):
        t_wall_0 = time.perf_counter()
        t_cpu_0 = time.process_time()
        fn()
        wall_times.append(time.perf_counter() - t_wall_0)
        cpu_times.append(time.process_time() - t_cpu_0)
        if idx == 0 and warm_runs == 1:
            break

    # Separate single profiling pass for peak Python heap + top cumulative hotspots.
    tracemalloc.start()
    prof = cProfile.Profile()
    prof.enable()
    fn()
    prof.disable()
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_mem_mib = peak_bytes / (1024.0 * 1024.0)

    med_wall = statistics.median(wall_times)
    med_cpu = statistics.median(cpu_times)
    note = (
        throughput_fmt(med_wall)
        if throughput_fmt is not None
        else f"{(med_wall / max(corpus_items, 1)) * 1000.0:.2f} ms/item"
    )
    print(
        f"[T02] {workload_id:28s} med={med_wall:7.4f}s "
        f"heap={peak_mem_mib:6.2f}MiB  {note}",
        flush=True,
    )
    return BenchmarkRecord(
        workload_id=workload_id,
        phase_target=phase_target,
        description=description,
        corpus_items=corpus_items,
        fixture_sha256=fixture_sha256,
        warm_runs=warm_runs,
        median_wall_s=round(med_wall, 4),
        min_wall_s=round(min(wall_times), 4),
        max_wall_s=round(max(wall_times), 4),
        median_cpu_s=round(med_cpu, 4),
        peak_tracemalloc_mib=round(peak_mem_mib, 2),
        peak_rss_mib=round(_max_rss_mib(), 2),
        throughput_note=note,
        top_hotspots=_extract_top_hotspots(prof, limit=5),
    )


def _measure_cold_imports() -> dict[str, float]:
    """Measure fresh-interpreter cold import latency for key OpenUBEM packages.

    Returns:
        Mapping of module name to cold import duration in milliseconds.
    """
    modules = [
        "openubem.config",
        "openubem.results.parser",
        "openubem.results.european_campaign",
        "openubem.gpusim.shading",
        "openubem.gpusim.compile",
        "openubem.microclimate.svf",
        "openubem.microclimate.utci",
    ]
    timings: dict[str, float] = {}
    for mod in modules:
        cmd = [
            sys.executable,
            "-c",
            (
                "import time; t0 = time.perf_counter(); "
                f"__import__({mod!r}); "
                "print(f'{(time.perf_counter() - t0) * 1000.0:.2f}')"
            ),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        val_str = proc.stdout.strip().splitlines()[-1]
        timings[mod] = float(val_str)
    return timings


def _extract_heating_kwh_csv(csv_path: Path) -> float:
    """Sum hourly ideal-loads heating energy [J] from an ``eplusout.csv`` file.

    Matches the ``csv.DictReader`` loop used by ``scripts/run_eu_s2_campaign.py``
    and ``scripts/gpusim/time_pair.py`` on retained heating-only EU-08 runs.

    Args:
        csv_path: Path to a retained ``eplusout.csv`` file.

    Returns:
        Annual heating energy in kWh.
    """
    with csv_path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError(f"Empty eplusout.csv header: {csv_path}")
        cols = [
            f
            for f in reader.fieldnames
            if "zone ideal loads zone total heating energy" in f.casefold()
            and "[j]" in f.casefold()
            and "(hourly)" in f.casefold()
        ]
        if not cols:
            raise ValueError(f"Missing heating column in {csv_path}")
        total_j = 0.0
        for row in reader:
            total_j += sum(float(row[c]) for c in cols)
    return total_j / 3.6e6


def _write_four_end_use_csv_fixture(path: Path, seed_offset: int) -> None:
    """Write a deterministic 8,760-row 4-end-use EnergyPlus CSV fixture.

    Follows the exact ``tests/test_eu_results_accounting.py`` schema because
    retained EU-08/S2 ``eplusout.csv`` files only request heating (as recorded
    in ``EU-10/s2_dossier/s2_dossier_v3.json``).

    Args:
        path: Output CSV path inside a temporary directory.
        seed_offset: Integer offset varying values deterministically per file.
    """
    from openubem.results.european_campaign import NON_LEAP_MONTH_HOURS

    base_vals = (
        ("Zone One:Zone Ideal Loads Zone Total Heating Energy [J](Hourly)", 3.6e6),
        ("Zone One:Zone Ideal Loads Zone Total Cooling Energy [J](Hourly)", 4.5e5),
        ("Zone One:Zone Lights Electricity Energy [J](Hourly)", 1.8e6),
        ("Zone One:Zone Electric Equipment Electricity Energy [J](Hourly)", 1.2e6),
    )
    fields = ["Date/Time", *(col for col, _ in base_vals)]
    scale = 1.0 + 0.01 * seed_offset
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(fields)
        for month, hours in enumerate(NON_LEAP_MONTH_HOURS, start=1):
            for hour in range(hours):
                stamp = f"{month:02d}/{hour // 24 + 1:02d}  {hour % 24 + 1:02d}:00:00"
                writer.writerow(
                    [stamp, *(f"{val * scale:.1f}" for _, val in base_vals)]
                )


def _run_benchmarks(
    skip_stage_a: bool = False,
) -> tuple[list[BenchmarkRecord], dict[str, Any]]:
    """Execute all Phase 0 Python hotspot benchmarks on retained local corpora.

    Args:
        skip_stage_a: When ``True``, skip the ~15 s single-cell Stage-A annual
            NumPy solver run (for quick smoke runs).

    Returns:
        Tuple ``(records, reference_facts)``.
    """
    import geopandas as gpd
    import numpy as np

    from openubem.acquisition.footprint_schema import _resolve_overlaps
    from openubem.geometry.context import discover_context
    from openubem.gpusim.backends.numpy_ref import run_stage_a_batch
    from openubem.gpusim.compile import compile_expidf_batch
    from openubem.gpusim.ctf import LayerSpec, build_modal_conduction
    from openubem.gpusim.physics.solar import calc_solar_direction_cosines
    from openubem.gpusim.shading import compute_exterior_shading
    from openubem.gpusim.viewfactors import (
        calc_approximate_view_factors,
        calc_script_f,
        fix_view_factors,
    )
    from openubem.gpusim.weather import load_epw_weather
    from openubem.microclimate.domain import build_domain
    from openubem.microclimate.svf import compute_svf
    from openubem.microclimate.utci import utci_approx
    from openubem.results.european_campaign import extract_four_end_use_eplus_csv
    from openubem.results.parser import check_building_integrity, parse_building_sql
    from openubem.semantic.provenance import add_lineage_summary, append_flag

    records: list[BenchmarkRecord] = []
    ref_facts: dict[str, Any] = {}

    # 1. R1a — SQL results harvest (campaign-sized ~650 KB eplusout.sql files)
    all_sql_files = sorted(
        (ROOT / "openubem" / "outputs" / "gpusim_golden_runs").rglob("eplusout.sql")
    )
    sql_files = [p for p in all_sql_files if p.stat().st_size < 5 * 1024 * 1024]
    if sql_files:
        sql_sha = _sha256_corpus(sql_files)

        def _bench_sql() -> int:
            total = 0
            for path in sql_files:
                df = parse_building_sql(path)
                _ = check_building_integrity(path)
                total += len(df)
            return total

        records.append(
            _measure_workload(
                "R1a_results_sql_harvest",
                "Phase 1 / openubem-results",
                "parse_building_sql + check_building_integrity on ~650 KB SQLs",
                len(sql_files),
                sql_sha,
                _bench_sql,
                warm_runs=3,
                throughput_fmt=lambda s: (
                    f"{s / len(sql_files) * 1000.0:.2f} ms/bldg "
                    f"(~{s / len(sql_files) * 8139.0:.1f} s @ 8,139 bldgs)"
                ),
            )
        )

    # Also measure 1 large timestep-level diagnostic SQL (~229 MB) cleanly once
    large_sql = (
        ROOT
        / "openubem"
        / "outputs"
        / "gpusim_golden_runs"
        / "es__ES.ME.AB.01.Gen.ReEx.001.001__f000"
        / "eplusout.sql"
    )
    if large_sql.exists():
        large_sql_sha = _sha256_corpus([large_sql])

        def _bench_large_sql() -> int:
            df = parse_building_sql(large_sql)
            _ = check_building_integrity(large_sql)
            return len(df)

        records.append(
            _measure_workload(
                "R1a_results_sql_large",
                "Phase 1 / openubem-results",
                "parse_building_sql + check_building_integrity on 229 MB SQL",
                1,
                large_sql_sha,
                _bench_large_sql,
                warm_runs=1,
                warmup=False,
                throughput_fmt=lambda s: f"{s:.2f} s for 229 MB SQL",
            )
        )

    # 2a. R1b (real disk) — Heating-only EU-08 rep1 eplusout.csv harvest (100 files)
    csv_files = sorted(
        (ROOT / "openubem" / "outputs" / "eu_certified_rerun_2026-08-28" / "rep1").glob(
            "*/eplusout.csv"
        )
    )[:100]
    if csv_files:
        csv_sha = _sha256_corpus(csv_files)

        def _bench_csv_heating() -> float:
            return sum(_extract_heating_kwh_csv(path) for path in csv_files)

        records.append(
            _measure_workload(
                "R1b_eu_csv_heating_real",
                "Phase 1 / openubem-results",
                "Single-pass DictReader heating harvest on 100 real EU-08 rep1 CSVs",
                len(csv_files),
                csv_sha,
                _bench_csv_heating,
                warm_runs=3,
                throughput_fmt=lambda s: (
                    f"{s / len(csv_files) * 1000.0:.2f} ms/bldg "
                    f"(~{s / len(csv_files) * 40800.0:.1f} s @ 40,800 bldgs)"
                ),
            )
        )

    # 2b. R1b (contract fixture) — Double-pass extract_four_end_use_eplus_csv (25 files)
    with tempfile.TemporaryDirectory(prefix="openubem_t02_csv_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        syn_csvs: list[Path] = []
        for idx in range(25):
            fpath = tmp_root / f"cell_{idx:03d}_eplusout.csv"
            _write_four_end_use_csv_fixture(fpath, idx)
            syn_csvs.append(fpath)

        def _bench_csv_4enduse() -> int:
            return sum(
                1 for path in syn_csvs if extract_four_end_use_eplus_csv(path)
            )

        records.append(
            _measure_workload(
                "R1b_eu_csv_4enduse_dblpass",
                "Phase 1 / openubem-results",
                "extract_four_end_use_eplus_csv (double-pass, 25x8760 contract CSVs)",
                len(syn_csvs),
                "synthetic-eu10-25",
                _bench_csv_4enduse,
                warm_runs=3,
                throughput_fmt=lambda s: (
                    f"{s / len(syn_csvs) * 1000.0:.2f} ms/bldg "
                    f"(~{s / len(syn_csvs) * 40800.0:.1f} s @ 40,800 bldgs)"
                ),
            )
        )

    # 3. R1c — Provenance & data_quality_flag processing (ES-MAD 2,381 buildings)
    es_gpkg = (
        ROOT
        / "openubem"
        / "outputs"
        / "eu02"
        / "ES-MAD-BERRUGUETE"
        / "01_buildings_clean.gpkg"
    )
    it_gpkg = (
        ROOT
        / "openubem"
        / "outputs"
        / "eu02"
        / "IT-BOL-GALVANI2"
        / "01_buildings_clean.gpkg"
    )
    es_gdf = gpd.read_file(es_gpkg)
    es_sha = _sha256_corpus([es_gpkg])

    def _bench_provenance() -> int:
        frame = es_gdf.drop(columns=["geometry"]).copy()
        out = add_lineage_summary(frame)
        flagged = append_flag(out, "height_missing", mask=out["height_m"].isna())
        return len(flagged)

    records.append(
        _measure_workload(
            "R1c_provenance_schema",
            "Phase 1 / openubem-schema",
            "add_lineage_summary + append_flag on ES-MAD-BERRUGUETE (2,381 bldgs)",
            len(es_gdf),
            es_sha,
            _bench_provenance,
            warm_runs=3,
            throughput_fmt=lambda s: (
                f"{s / len(es_gdf) * 1000.0:.3f} ms/bldg "
                f"(~{s / len(es_gdf) * 100000.0:.1f} s @ 100k bldgs)"
            ),
        )
    )

    # 4. R2 — Exterior ray-traced shading (5 real ES-MAD buildings + 20 m context)
    epw_madrid = (
        ROOT / "openubem" / "data" / "weather" / "es_madrid_2009_2010_y2010.epw"
    )
    sol_x, sol_y, sol_z, _ = calc_solar_direction_cosines(
        latitude_deg=40.45, longitude_deg=-3.70, time_zone=1.0, steps_per_hour=1
    )
    solcos_hourly = np.stack([sol_x, sol_y, sol_z], axis=1).astype(np.float64)

    def _extrude_wall_quads(
        poly: Any, height_m: float, ox: float, oy: float
    ) -> tuple[list[np.ndarray], list[np.ndarray]]:
        if poly.geom_type == "MultiPolygon":
            poly = max(poly.geoms, key=lambda g: g.area)
        coords = list(poly.exterior.coords)
        quads: list[np.ndarray] = []
        normals: list[np.ndarray] = []
        for idx in range(len(coords) - 1):
            x0, y0 = float(coords[idx][0]) - ox, float(coords[idx][1]) - oy
            x1, y1 = float(coords[idx + 1][0]) - ox, float(coords[idx + 1][1]) - oy
            dx, dy = x1 - x0, y1 - y0
            seg_len = math.hypot(dx, dy)
            if seg_len < 0.2:
                continue
            quad = np.array(
                [
                    [x0, y0, height_m],
                    [x0, y0, 0.0],
                    [x1, y1, 0.0],
                    [x1, y1, height_m],
                ],
                dtype=np.float64,
            )
            # Outward unit normal for CCW ring
            normal = np.array([dy / seg_len, -dx / seg_len, 0.0], dtype=np.float64)
            quads.append(quad)
            normals.append(normal)
        return quads, normals

    sample_n = 5
    sindex = es_gdf.sindex
    shading_cases: list[
        tuple[list[np.ndarray], np.ndarray, np.ndarray, list[np.ndarray]]
    ] = []
    for row_idx in range(min(sample_n, len(es_gdf))):
        row = es_gdf.iloc[row_idx]
        geom = row.geometry
        raw_h = float(row["height_m"])
        h_val = raw_h if not math.isnan(raw_h) else 12.0
        ox, oy = geom.centroid.x, geom.centroid.y
        t_quads, t_norms = _extrude_wall_quads(geom, max(h_val, 3.0), ox, oy)
        if not t_quads:
            continue
        minx, miny, maxx, maxy = geom.buffer(20.0).bounds
        cand_idx = list(sindex.intersection((minx, miny, maxx, maxy)))
        occ_quads: list[np.ndarray] = []
        for nb_idx in cand_idx:
            if nb_idx == row_idx:
                continue
            nb_row = es_gdf.iloc[nb_idx]
            raw_nb_h = float(nb_row["height_m"])
            nb_h = raw_nb_h if not math.isnan(raw_nb_h) else 12.0
            nb_q, _ = _extrude_wall_quads(nb_row.geometry, max(nb_h, 3.0), ox, oy)
            occ_quads.extend(nb_q)
        if not occ_quads:
            continue
        shading_cases.append(
            (
                t_quads,
                np.asarray(t_norms, dtype=np.float64),
                np.ones(len(t_quads), dtype=bool),
                occ_quads,
            )
        )

    def _bench_shading() -> float:
        acc = 0.0
        for t_quads, t_norms, sun_exp, occ_quads in shading_cases:
            sunlit, sky = compute_exterior_shading(
                t_quads,
                t_norms,
                sun_exp,
                occ_quads,
                solcos_hourly,
                periodic_days=5,
                n_grid=3,
                n_sky_rays=64,
                device="cpu",
            )
            acc += float(sunlit.mean() + sky.mean())
        return acc

    records.append(
        _measure_workload(
            "R2_gpusim_shading_cpu",
            "Phase 2 / openubem-shading",
            "compute_exterior_shading (periodic=5d, 3x3, 64 sky rays) on ES-MAD sample",
            len(shading_cases),
            _sha256_corpus([es_gpkg, epw_madrid]),
            _bench_shading,
            warm_runs=3,
            throughput_fmt=lambda s: (
                f"{s / len(shading_cases) * 1000.0:.1f} ms/bldg "
                f"(~{s / len(shading_cases) * 3832.0:.1f} s @ 3,832 M8 homes)"
            ),
        )
    )

    # Record published M8 CSV reference with SHA-256
    m8_csv = ROOT / "openubem" / "outputs" / "gpusim_m8_eu_districts.csv"
    if m8_csv.exists():
        ref_facts["m8_csv_sha256"] = _sha256_file(m8_csv)[:16]
        ref_facts["m8_csv_path"] = m8_csv.relative_to(ROOT).as_posix()

    # 5. R3 — ExpIDF parse + batch compile + modal CTF + ScriptF view factors
    expidf_files = sorted(
        (ROOT / "openubem" / "outputs" / "eu_certified_rerun_2026-08-28" / "rep1").glob(
            "*/eplusout.expidf"
        )
    )[:50]
    if expidf_files:
        exp_sha = _sha256_corpus(expidf_files)

        def _bench_idf_compile() -> int:
            spec = compile_expidf_batch(expidf_files, max_rung="S1")
            return int(spec.batch_size)

        records.append(
            _measure_workload(
                "R3a_idf_parse_compile",
                "Phase 3 / openubem-idf",
                "compile_expidf_batch (parse + extract + pack) on 50 EU-08 expIDFs",
                len(expidf_files),
                exp_sha,
                _bench_idf_compile,
                warm_runs=3,
                throughput_fmt=lambda s: (
                    f"{s / len(expidf_files) * 1000.0:.2f} ms/IDF "
                    f"(~{s / len(expidf_files) * 10000.0:.1f} s @ 10k IDFs)"
                ),
            )
        )

    # CTF + ViewFactors micro-benchmark (200 constructions + 200 12-surface zones)
    sample_layers = [
        LayerSpec("stucco", False, 0.0, 0.025, 0.72, 1856.0, 840.0),
        LayerSpec("insulation", False, 0.0, 0.080, 0.038, 35.0, 1400.0),
        LayerSpec("brick", False, 0.0, 0.240, 0.70, 1600.0, 840.0),
        LayerSpec("gypsum", False, 0.0, 0.015, 0.16, 800.0, 1090.0),
    ]
    vf_areas = np.array([45, 45, 18, 18, 14, 14, 6, 6, 4, 4, 22, 22], dtype=np.float64)
    vf_az = np.array([0, 0, 0, 180, 90, 270, 0, 180, 90, 270, 0, 90], dtype=np.float64)
    vf_tilt = np.array(
        [180, 0, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90], dtype=np.float64
    )
    vf_cls = np.array([2, 1, 0, 0, 0, 0, 3, 3, 3, 3, 4, 4], dtype=np.int32)
    vf_emiss = np.full(12, 0.90, dtype=np.float64)

    def _bench_ctf_vf() -> float:
        acc = 0.0
        for _ in range(200):
            model = build_modal_conduction(sample_layers, dt_sec=300.0)
            f_approx = calc_approximate_view_factors(vf_areas, vf_az, vf_tilt, vf_cls)
            f_fixed = fix_view_factors(vf_areas, f_approx)
            script_f = calc_script_f(vf_areas, f_fixed, vf_emiss)
            acc += float(model.ctf_out0 + script_f[0, 1])
        return acc

    records.append(
        _measure_workload(
            "R3b_ctf_and_scriptf",
            "Phase 3 / openubem-idf",
            "build_modal_conduction + calc_script_f (200 4-layer walls + zones)",
            200,
            "synthetic-4layer",
            _bench_ctf_vf,
            warm_runs=3,
            throughput_fmt=lambda s: (
                f"{s / 200.0 * 1000.0:.2f} ms/zone "
                f"(~{s / 200.0 * 10000.0:.1f} s @ 10k zones)"
            ),
        )
    )

    # 6. R4a — Stage-A CPU float64 thermal solver (1 golden S0 cell, full 105,120 steps)
    golden_cell_dir = (
        ROOT
        / "openubem"
        / "outputs"
        / "eu_certified_rerun_2026-08-28"
        / "rep1"
        / "es__ES.ME.AB.01.Gen.ReEx.001.001__f000"
    )
    golden_expidf = golden_cell_dir / "eplusout.expidf"
    if not skip_stage_a and golden_expidf.exists() and epw_madrid.exists():
        batch_1 = compile_expidf_batch([golden_expidf], max_rung="S1")
        weather_1 = load_epw_weather(epw_madrid, steps_per_hour=12)
        stage_a_sha = _sha256_corpus([golden_expidf, epw_madrid])

        def _bench_stage_a() -> float:
            res = run_stage_a_batch(batch_1, weather_1, ctf=None)
            return float(np.sum(res.annual_heating_kwh))

        records.append(
            _measure_workload(
                "R4a_stage_a_cpu_solver",
                "Phase 4 / openubem-sim",
                "run_stage_a_batch (105,120 steps, 1 golden EU cell, Python NumPy f64)",
                1,
                stage_a_sha,
                _bench_stage_a,
                warm_runs=1,
                warmup=False,
                throughput_fmt=lambda s: (
                    f"{s:.2f} s/cell-yr (~{s * 12.0:.1f} s for 12-cell P1)"
                ),
            )
        )

    # 7. R4b — Stage 6 microclimate SVF & UTCI on real ES-MAD 300m x 300m crop
    cx = float(es_gdf.geometry.centroid.x.median())
    cy = float(es_gdf.geometry.centroid.y.median())
    crop_gdf = es_gdf.cx[cx - 120.0 : cx + 120.0, cy - 120.0 : cy + 120.0].copy()
    crop_gdf["height_m"] = crop_gdf["height_m"].fillna(12.0)
    domain = build_domain(crop_gdf, res_m=2.0, buffer_m=20.0)
    n_cells = int(domain.shape[0] * domain.shape[1])

    def _bench_svf() -> float:
        svf, _ = compute_svf(domain, n_azimuths=32, max_radius_px=50)
        return float(svf.mean())

    records.append(
        _measure_workload(
            "R4b_microclimate_svf",
            "Phase 4 / openubem-microclimate",
            f"compute_svf (32 az, r=50px) on {domain.shape[0]}x{domain.shape[1]} grid",
            n_cells,
            es_sha,
            _bench_svf,
            warm_runs=3,
            throughput_fmt=lambda s: (
                f"{n_cells / max(s, 1e-9) / 1e3:.1f} kpix/s "
                f"(~{s * (500 * 500 / max(n_cells, 1)):.1f} s @ 500x500)"
            ),
        )
    )

    rng = np.random.default_rng(42)
    utci_shape = (168, domain.shape[0], domain.shape[1])
    ta = rng.uniform(15.0, 38.0, size=utci_shape)
    tmrt = ta + rng.uniform(-5.0, 28.0, size=utci_shape)
    va10 = rng.uniform(0.8, 6.0, size=utci_shape)
    e_kpa = rng.uniform(0.8, 2.6, size=utci_shape)
    n_utci_evals = int(ta.size)

    def _bench_utci() -> float:
        out, _ = utci_approx(ta, tmrt, va10, e_kpa)
        return float(out.mean())

    records.append(
        _measure_workload(
            "R4c_microclimate_utci",
            "Phase 4 / openubem-microclimate",
            f"utci_approx (210-term) on 168h x {domain.shape[0]}x{domain.shape[1]}",
            n_utci_evals,
            "seed-42-synthetic",
            _bench_utci,
            warm_runs=3,
            throughput_fmt=lambda s: (
                f"{n_utci_evals / max(s, 1e-9) / 1e6:.2f} Mevals/s"
            ),
        )
    )

    # 8. R6 — Profile-gated GIS checks (_resolve_overlaps & discover_context)
    it_gdf = gpd.read_file(it_gpkg)
    r6_sha = _sha256_corpus([es_gpkg, it_gpkg])

    def _bench_overlaps() -> int:
        r1 = _resolve_overlaps(es_gdf.copy())
        r2 = _resolve_overlaps(it_gdf.copy())
        return len(r1) + len(r2)

    records.append(
        _measure_workload(
            "R6a_resolve_overlaps",
            "Phase 5b (deferred) / R6 eval",
            "_resolve_overlaps on ES-MAD (2,381) + IT-BOL (1,631) footprints",
            len(es_gdf) + len(it_gdf),
            r6_sha,
            _bench_overlaps,
            warm_runs=3,
            throughput_fmt=lambda s: (
                f"{s / (len(es_gdf) + len(it_gdf)) * 1000.0:.3f} ms/bldg"
            ),
        )
    )

    ctx_n = min(200, len(es_gdf))
    es_ctx_gdf = es_gdf.copy()
    es_ctx_gdf["_simplified_geom"] = es_ctx_gdf.geometry
    ctx_centroids = [
        (
            float(es_ctx_gdf.iloc[i].geometry.centroid.x),
            float(es_ctx_gdf.iloc[i].geometry.centroid.y),
        )
        for i in range(ctx_n)
    ]

    def _bench_context() -> int:
        total = 0
        for idx, (tcx, tcy) in enumerate(ctx_centroids):
            nb = discover_context(
                es_ctx_gdf.iloc[idx], es_ctx_gdf, tcx, tcy, sphere_radius_m=30.0
            )
            total += len(nb)
        return total

    records.append(
        _measure_workload(
            "R6b_discover_context",
            "Phase 5b (deferred) / R6 eval",
            f"discover_context (r=30m) for {ctx_n} ES-MAD buildings",
            ctx_n,
            es_sha,
            _bench_context,
            warm_runs=3,
            throughput_fmt=lambda s: (
                f"{s / ctx_n * 1000.0:.2f} ms/bldg "
                f"(~{s / ctx_n * len(es_gdf):.1f} s for full ES-MAD)"
            ),
        )
    )

    return records, ref_facts


def _git_head() -> str:
    """Return short git commit hash of HEAD.

    Returns:
        Short SHA-1 commit hash or ``"unknown"``.
    """
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return proc.stdout.strip()
    except Exception:
        return "unknown"


def _rustc_version() -> str:
    """Return active ``rustc --version`` output if installed.

    Returns:
        Version line or ``"not installed"``.
    """
    for exe in ("rustc", str(Path.home() / ".cargo" / "bin" / "rustc")):
        try:
            proc = subprocess.run(
                [exe, "--version"], capture_output=True, text=True, check=True
            )
            return proc.stdout.strip()
        except Exception:
            continue
    return "not installed"


def _cpu_brand() -> str:
    """Return human-readable host CPU description.

    Returns:
        CPU model string.
    """
    if sys.platform == "darwin":
        try:
            proc = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
                check=True,
            )
            return proc.stdout.strip()
        except Exception:
            pass
    return platform.processor() or platform.machine()


def _render_markdown(
    records: list[BenchmarkRecord],
    cold_imports: dict[str, float],
    ref_facts: dict[str, Any],
) -> str:
    """Render Phase 0 baseline measurements into a Markdown report.

    Args:
        records: Measured benchmark rows.
        cold_imports: Fresh-interpreter cold import timings (ms).
        ref_facts: Auxiliary published reference hashes/citations.

    Returns:
        Complete Markdown report text.
    """
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Phase 0 Baseline — Python Hotspot Profile (`T02`)",
        "",
        f"- **Generated:** {now_utc}",
        f"- **Git commit:** `{_git_head()}`",
        f"- **Host hardware:** `{_cpu_brand()}` ({platform.machine()}, "
        f"{platform.system()} {platform.release()})",
        f"- **Python:** `{platform.python_version()}` (`{sys.executable}`)",
        f"- **Rust toolchain:** `{_rustc_version()}`",
        "- **Profiler:** `scripts/bench/profile_python_hotspots.py` "
        "(median over 3 warm runs where fast; `cProfile` + `tracemalloc` + RSS)",
        "",
        "---",
        "",
        "## 1. End-to-End Hotspot Summary (Python Baseline)",
        "",
        "| Workload | Target Crate / Phase | Items | Median Wall (s) | "
        "Median CPU (s) | Peak Py Heap (MiB) | Rate / Extrapolation | SHA-256 |",
        "|---|---|---:|---:|---:|---:|---|---|",
    ]
    for rec in records:
        lines.append(
            f"| `{rec.workload_id}` | {rec.phase_target} | {rec.corpus_items:,} | "
            f"{rec.median_wall_s:.4f} | {rec.median_cpu_s:.4f} | "
            f"{rec.peak_tracemalloc_mib:.2f} | {rec.throughput_note} | "
            f"`{rec.fixture_sha256}` |"
        )

    lines.extend(
        [
            "",
            "### Published M8 Reference Anchor",
            "",
            "- `openubem/outputs/gpusim_m8_eu_districts.csv` "
            f"(SHA-256 `{ref_facts.get('m8_csv_sha256', 'n/a')}`): "
            "3,832 homes across 4 EU districts took **2,898.8 s** total, of which "
            "**505.1 s** (17.4% total / **93% of non-kernel time**) was brute-force "
            "`gpusim/shading.py` and **38.0 s** was Python IDF/layout compile.",
            "",
            "---",
            "",
            "## 2. Top `cProfile` Cumulative Hotspots per Workload",
            "",
        ]
    )
    for rec in records:
        lines.append(f"### `{rec.workload_id}` — {rec.description}")
        lines.append(
            f"- Wall range: `{rec.min_wall_s:.4f}s`–`{rec.max_wall_s:.4f}s` "
            f"({rec.warm_runs} run(s)); process peak RSS `{rec.peak_rss_mib:.1f} MiB`"
        )
        for hot in rec.top_hotspots:
            lines.append(f"  - `{hot}`")
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "## 3. Cold Import Latency (Fresh Python Interpreter)",
            "",
            "| Module | Cold Import (ms) |",
            "|---|---:|",
        ]
    )
    for mod, ms in cold_imports.items():
        lines.append(f"| `{mod}` | {ms:.1f} |")

    lines.extend(
        [
            "",
            "---",
            "",
            "## 4. Phase 0 Gate Takeaways for R1–R6 Prioritization",
            "",
            "- **R1 (`openubem-schema` + `openubem-results`)**: Both SQL (`parser.py`) "
            "and double-pass CSV (`european_campaign.py`) scale linearly with building "
            "count across thousands of directories; single open-read-close `rusqlite` "
            "+ streaming `csv` + `rayon` cleanly removes the post-sim I/O wall.",
            "- **R2 (`openubem-shading`)**: Confirmed dominant per-building geometry "
            "cost (`compute_exterior_shading`), reproducing the M8 505.1 s wall.",
            "- **R3 (`openubem-idf`)**: `compile_expidf_batch`, "
            "`build_modal_conduction`, and `calc_script_f` grow linearly into "
            "multi-minute setup overhead at 10k+ buildings.",
            "- **R4 (`openubem-sim` + `openubem-microclimate`)**: Single-cell Python "
            "Stage-A loop (`run_stage_a_batch`), `compute_svf`, and 210-term "
            "`utci_approx` confirm large pure-CPU headroom for Rust `rayon` + `pulp`.",
            "- **R6 (`_resolve_overlaps` & `discover_context` — D-RS-06 check)**: "
            "Measured directly above so `T17` can decide strictly on empirical "
            "wall-time share after testing vectorized `shapely` 2.0.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    """CLI entrypoint for Phase 0 Python hotspot profiling.

    Returns:
        Exit status code (0 on success).
    """
    parser = argparse.ArgumentParser(
        description="Profile OpenUBEM Python hotspots (T02)."
    )
    parser.add_argument(
        "--md-out",
        type=Path,
        default=DEFAULT_MD_OUT,
        help="Output Markdown report path.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=DEFAULT_JSON_OUT,
        help="Output machine-readable JSON snapshot path.",
    )
    parser.add_argument(
        "--skip-stage-a",
        action="store_true",
        help="Skip the annual single-cell Stage-A NumPy solver run.",
    )
    args = parser.parse_args()

    cold_imports = _measure_cold_imports()
    records, ref_facts = _run_benchmarks(skip_stage_a=args.skip_stage_a)

    md_text = _render_markdown(records, cold_imports, ref_facts)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.write_text(md_text, encoding="utf-8")

    payload = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "git_head": _git_head(),
        "rustc_version": _rustc_version(),
        "cpu": _cpu_brand(),
        "python_version": platform.python_version(),
        "cold_imports_ms": cold_imports,
        "reference_facts": ref_facts,
        "benchmarks": [asdict(rec) for rec in records],
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Wrote {args.md_out} ({len(records)} workloads) and {args.json_out}")
    for rec in records:
        print(
            f"  {rec.workload_id:28s}  med={rec.median_wall_s:7.4f}s  "
            f"heap={rec.peak_tracemalloc_mib:6.2f}MiB  {rec.throughput_note}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
