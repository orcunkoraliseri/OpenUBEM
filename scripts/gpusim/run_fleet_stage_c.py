import csv
import json
import sys
import time
from pathlib import Path

import numpy as np

from openubem.gpusim.backends.kernel.pack import deduplicate_weather, pack
from openubem.gpusim.backends.numpy_ref import run_stage_a_batch
from openubem.gpusim.backends.stage_c import run_packed_stage_c_mps
from openubem.gpusim.compile import BatchSpec, compile_expidf_batch
from openubem.gpusim.weather import WeatherSeries, load_epw_weather

REPO_ROOT = Path(__file__).resolve().parents[2]
REP2_DIR = REPO_ROOT / "openubem/outputs/eu_certified_rerun_2026-08-28/rep2"
SCHED_DIR = REP2_DIR / "schedules"
M1_FLEET_CSV = REPO_ROOT / "openubem/outputs/gpusim_m1_fleet.csv"
M1_RECHECK_CSV = REPO_ROOT / "openubem/outputs/gpusim_m1_recheck.csv"
OUT_CSV = REPO_ROOT / "openubem/outputs/gpusim_m3_fleet.csv"

EPW_SEARCH_DIRS: tuple[Path, ...] = (
    REPO_ROOT / "openubem/data/weather",
    REP2_DIR / "weather",
    REPO_ROOT / "tests/fixtures/gpusim/golden/weather",
    REPO_ROOT / "data/weather",
)


def resolve_epw_path(epw_file_name: str) -> Path:
    """Resolve an EPW filename across repository weather directories.

    Args:
        epw_file_name: Basename of the EPW weather file.

    Returns:
        Resolved filesystem path to the EPW file.

    Raises:
        FileNotFoundError: If no matching EPW file exists in the repository.
    """
    for directory in EPW_SEARCH_DIRS:
        candidate = directory / epw_file_name
        if candidate.is_file():
            return candidate
    for found in REPO_ROOT.rglob(epw_file_name):
        if found.is_file():
            return found
    raise FileNotFoundError(f"EPW file not found: {epw_file_name}")


def load_m1_fleet_reference(csv_path: Path) -> dict[str, dict[str, float | int]]:
    """Load Stage A annual outputs, published values, and warm-up days.

    Args:
        csv_path: Path to ``gpusim_m1_fleet.csv``.

    Returns:
        Mapping from ``cell`` id to reference metrics.
    """
    ref: dict[str, dict[str, float | int]] = {}
    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            ref[str(row["cell"])] = {
                "annual_published_kwh": float(row["annual_eplus_kwh"]),
                "annual_stage_a_kwh": float(row["annual_stage_a_kwh"]),
                "warmup_days_stage_a": int(row["warmup_days_stage_a"]),
            }
    return ref


def load_m1_recheck_reference(csv_path: Path) -> dict[str, float]:
    """Load Mac EnergyPlus reference annual heating for the re-checked cells.

    Args:
        csv_path: Path to ``gpusim_m1_recheck.csv``.

    Returns:
        Mapping from ``cell`` id to ``mac_eplus_kwh``.
    """
    recheck: dict[str, float] = {}
    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            recheck[str(row["cell"])] = float(row["mac_eplus_kwh"])
    return recheck


def load_completed_fleet_entries() -> list[dict[str, object]]:
    """Discover all completed fleet cells from ``rep2/manifests/*.json``.

    Returns:
        List of cell metadata dicts sorted deterministically by ``cell_id``.

    Raises:
        FileNotFoundError: If a completed cell lacks ``eplusout.expidf``.
    """
    entries: list[dict[str, object]] = []
    for manifest_path in sorted((REP2_DIR / "manifests").glob("*.json")):
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not data.get("completed"):
            continue
        cell_id = str(data["cell_id"])
        expidf_path = REP2_DIR / cell_id / "eplusout.expidf"
        if not expidf_path.is_file():
            raise FileNotFoundError(f"Missing expidf for cell {cell_id}")
        raw_epw = str(data["epw_path"]).replace("\\", "/")
        entries.append(
            {
                "cell_id": cell_id,
                "expidf_path": expidf_path,
                "epw_name": Path(raw_epw).name,
                "manifest_heating_kwh": float(data["heating_kwh"]),
            }
        )
    entries.sort(key=lambda item: str(item["cell_id"]))
    return entries


def _diagnose_first_diverging_hour(
    entry: dict[str, object],
    weather: WeatherSeries,
    warmup_days: int,
    stage_c_hourly_j: np.ndarray,
) -> int:
    """Run Stage A on a single failing cell to find its first diverging hour.

    Args:
        entry: Cell metadata entry for the failing cell.
        weather: Weather series for the cell's site.
        warmup_days: Locked warm-up day count from Stage A.
        stage_c_hourly_j: Stage C hourly heating array of shape ``(8760,)``.

    Returns:
        Zero-based hour index with largest divergence when relative difference
        first exceeds ``5e-4`` (or argmax hour if cumulative drift).
    """
    single_batch: BatchSpec = compile_expidf_batch(
        [Path(entry["expidf_path"])],
        cell_ids=[str(entry["cell_id"])],
        epw_ids=[str(entry["epw_name"])],
        schedule_dirs=[SCHED_DIR],
    )
    sa_res = run_stage_a_batch(
        single_batch,
        weather,
        record_zone_temp=False,
        force_warmup_days=np.asarray([warmup_days], dtype=np.int32),
    )
    h_sa = sa_res.hourly_heating_j[0]
    diff = np.abs(stage_c_hourly_j - h_sa)
    thr_j = 1.0 * float(single_batch.zone_floor_area[0]) * 3600.0
    rel = diff / np.maximum(np.abs(h_sa), thr_j)
    hits = np.flatnonzero(rel > 5.0e-4)
    if hits.size > 0:
        return int(hits[0])
    return int(np.argmax(diff))


def run_fleet_stage_c() -> list[dict[str, object]]:
    """Run Stage C across all 346 completed fleet cells as one GPU batch.

    Returns:
        List of per-cell result rows written to ``gpusim_m3_fleet.csv``.

    Raises:
        RuntimeError: If any cell fails the Stage C vs Stage A annual float32
            gate or if reference cell sets mismatch.
    """
    entries = load_completed_fleet_entries()
    m1_ref = load_m1_fleet_reference(M1_FLEET_CSV)
    recheck_ref = load_m1_recheck_reference(M1_RECHECK_CSV)

    if len(entries) != len(m1_ref):
        raise RuntimeError(
            f"Fleet count mismatch: manifests={len(entries)}, m1={len(m1_ref)}"
        )

    cell_ids = [str(e["cell_id"]) for e in entries]
    expidf_paths = [Path(e["expidf_path"]) for e in entries]
    epw_names = [str(e["epw_name"]) for e in entries]

    weather_cache: dict[str, WeatherSeries] = {}
    for epw_name in sorted(set(epw_names)):
        weather_cache[epw_name] = load_epw_weather(
            resolve_epw_path(epw_name),
            steps_per_hour=12,
        )
    per_bldg_weather = [weather_cache[name] for name in epw_names]

    t_compile0 = time.perf_counter()
    batch = compile_expidf_batch(
        expidf_paths,
        cell_ids=cell_ids,
        epw_ids=epw_names,
        schedule_dirs=[SCHED_DIR],
    )
    compile_s = time.perf_counter() - t_compile0

    forced_wu = np.asarray(
        [int(m1_ref[cid]["warmup_days_stage_a"]) for cid in cell_ids],
        dtype=np.int32,
    )

    t_run0 = time.perf_counter()
    weather_by_site, site_index = deduplicate_weather(
        per_bldg_weather,
        batch.batch_size,
    )
    packed = pack(batch, weather_by_site, site_index, ctf=None)
    pack_s = time.perf_counter() - t_run0

    res, timings = run_packed_stage_c_mps(
        packed=packed,
        cell_ids=batch.cell_ids,
        record_zone_temp=False,
        force_warmup_days=forced_wu,
        run_chunk_days=1,
    )
    fleet_wall_s = time.perf_counter() - t_run0

    print(
        f"Stage C fleet: B={batch.batch_size}, sites={len(weather_by_site)}, "
        f"compile_s={compile_s:.3f}, pack_s={pack_s:.3f}, "
        f"upload_s={timings['upload_s']:.3f}, gpu_s={timings['gpu_s']:.3f}, "
        f"download_s={timings['download_s']:.3f}, "
        f"max_launch_s={timings['max_launch_s']:.3f}, "
        f"fleet_wall_s={fleet_wall_s:.3f}"
    )

    rows: list[dict[str, object]] = []
    failing: list[tuple[int, str, float, float]] = []

    for bi, cid in enumerate(cell_ids):
        ref = m1_ref[cid]
        ann_pub = float(ref["annual_published_kwh"])
        ann_sa = float(ref["annual_stage_a_kwh"])
        wu_sa = int(ref["warmup_days_stage_a"])
        ann_sc = float(res.annual_heating_kwh[bi])
        area = float(batch.zone_floor_area[bi])

        rel_c_vs_a = (ann_sc - ann_sa) / ann_sa
        abs_c_vs_a_m2 = abs(ann_sc - ann_sa) / area
        rel_c_vs_pub = (ann_sc - ann_pub) / ann_pub

        if abs(rel_c_vs_a) > 0.0005 and abs_c_vs_a_m2 > 0.01:
            failing.append((bi, cid, rel_c_vs_a, abs_c_vs_a_m2))

        rows.append(
            {
                "cell": cid,
                "annual_published_kwh": ann_pub,
                "annual_stage_a_kwh": ann_sa,
                "annual_stage_c_kwh": ann_sc,
                "rel_c_vs_a": rel_c_vs_a,
                "rel_c_vs_published": rel_c_vs_pub,
                "warmup_days_stage_a": wu_sa,
            }
        )

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "cell",
        "annual_published_kwh",
        "annual_stage_a_kwh",
        "annual_stage_c_kwh",
        "rel_c_vs_a",
        "rel_c_vs_published",
        "warmup_days_stage_a",
    ]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "cell": row["cell"],
                    "annual_published_kwh": f"{float(row['annual_published_kwh']):.6f}",
                    "annual_stage_a_kwh": f"{float(row['annual_stage_a_kwh']):.6f}",
                    "annual_stage_c_kwh": f"{float(row['annual_stage_c_kwh']):.6f}",
                    "rel_c_vs_a": f"{float(row['rel_c_vs_a']):.8e}",
                    "rel_c_vs_published": f"{float(row['rel_c_vs_published']):.8e}",
                    "warmup_days_stage_a": int(row["warmup_days_stage_a"]),
                }
            )
    print(f"Wrote {OUT_CSV} ({len(rows)} rows)")

    if failing:
        bi0, cid0, rel0, m20 = failing[0]
        div_hr = _diagnose_first_diverging_hour(
            entries[bi0],
            per_bldg_weather[bi0],
            int(forced_wu[bi0]),
            res.hourly_heating_j[bi0],
        )
        raise RuntimeError(
            f"Gate failed for {len(failing)} cell(s); first={cid0} "
            f"(rel_c_vs_a={rel0:.6e}, abs_kwh_m2={m20:.6f}, "
            f"first_diverging_hour={div_hr})"
        )

    rel_a_arr = np.asarray(
        [abs(float(r["rel_c_vs_a"])) for r in rows],
        dtype=np.float64,
    )
    worst_idx = int(np.argmax(rel_a_arr))
    worst_row = rows[worst_idx]
    print(
        f"Stage C vs Stage A annual gate PASSED (N={len(rows)}): "
        f"worst |rel_c_vs_a|={abs(float(worst_row['rel_c_vs_a'])) * 100:.6f}% "
        f"({float(worst_row['rel_c_vs_a']):+.8e}) on {worst_row['cell']}"
    )

    pub_abs = np.asarray(
        [abs(float(r["rel_c_vs_published"])) for r in rows], dtype=np.float64
    )
    pub_signed = np.asarray(
        [float(r["rel_c_vs_published"]) for r in rows], dtype=np.float64
    )
    cnt_gt_05pct = int(np.sum(pub_abs > 0.005))
    print(
        f"Stage C vs published (N={len(rows)}): "
        f"median |rel|={float(np.median(pub_abs)) * 100:.4f}% "
        f"(signed={float(np.median(pub_signed)) * 100:+.4f}%), "
        f"p99 |rel|={float(np.percentile(pub_abs, 99)) * 100:.4f}%, "
        f"worst |rel|={float(np.max(pub_abs)) * 100:.4f}%, "
        f"count > 0.5%={cnt_gt_05pct}"
    )

    by_cell = {str(r["cell"]): r for r in rows}
    print("Rechecked 5 cells (Stage C vs Mac E+):")
    for cid, mac_kwh in recheck_ref.items():
        row = by_cell[cid]
        sc_kwh = float(row["annual_stage_c_kwh"])
        pub_kwh = float(row["annual_published_kwh"])
        rel_mac = (sc_kwh - mac_kwh) / mac_kwh
        rel_pub = (sc_kwh - pub_kwh) / pub_kwh
        print(
            f"  {cid}: stage_c={sc_kwh:.6f} kWh, mac_eplus={mac_kwh:.6f} kWh, "
            f"rel_c_vs_mac={rel_mac * 100:+.6f}% ({rel_mac:+.8e}), "
            f"rel_c_vs_pub={rel_pub * 100:+.4f}%"
        )

    return rows


if __name__ == "__main__":
    try:
        run_fleet_stage_c()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
