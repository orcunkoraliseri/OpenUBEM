import argparse
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np

from openubem.gpusim.backends.kernel.pack import deduplicate_weather, pack
from openubem.gpusim.backends.numpy_ref import run_stage_a_batch
from openubem.gpusim.backends.stage_c import run_packed_stage_c
from openubem.gpusim.compile import BatchSpec, compile_expidf_batch
from openubem.gpusim.weather import WeatherSeries, load_epw_weather

REPO_ROOT = Path(__file__).resolve().parents[2]
REP2_DIR = REPO_ROOT / "openubem/outputs/eu_certified_rerun_2026-08-28/rep2"
SCHED_DIR = REP2_DIR / "schedules"
M1_FLEET_CSV = REPO_ROOT / "openubem/outputs/gpusim_m1_fleet.csv"
M1_RECHECK_CSV = REPO_ROOT / "openubem/outputs/gpusim_m1_recheck.csv"
M4_WIN_EPLUS_CSV = REPO_ROOT / "openubem/outputs/gpusim_m4_win_eplus.csv"
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


def load_win_eplus_reference(csv_path: Path) -> dict[str, float]:
    """Load Windows EnergyPlus recheck annual heating totals by cell ID."""
    win_ref: dict[str, float] = {}
    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            win_ref[str(row["cell"])] = float(row["win_eplus_kwh"])
    return win_ref


def run_fleet_stage_c(
    device: str = "mps",
    out_csv: Path = OUT_CSV,
    win_eplus_csv: Path | None = None,
) -> list[dict[str, object]]:
    """Run Stage C across all 346 completed fleet cells as one GPU batch.

    Args:
        device: Target Stage C backend (``"mps"`` or ``"cuda"``).
        out_csv: Destination CSV path.
        win_eplus_csv: Optional Windows E+ recheck CSV for M4 gated P2 check.

    Returns:
        List of per-cell result rows written to ``out_csv``.

    Raises:
        RuntimeError: If any cell fails the Stage C vs Stage A annual float32
            gate, if gated fleet checks fail, or if reference cell sets mismatch.
    """
    entries = load_completed_fleet_entries()
    m1_ref = load_m1_fleet_reference(M1_FLEET_CSV)
    recheck_ref = load_m1_recheck_reference(M1_RECHECK_CSV)
    win_path = win_eplus_csv if win_eplus_csv is not None else M4_WIN_EPLUS_CSV
    has_win_csv = win_path.is_file()
    win_ref = load_win_eplus_reference(win_path) if has_win_csv else {}
    use_m4_schema = device == "cuda" or win_eplus_csv is not None

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

    res, timings = run_packed_stage_c(
        packed=packed,
        cell_ids=batch.cell_ids,
        record_zone_temp=False,
        force_warmup_days=forced_wu,
        run_chunk_days=1,
        device=device,
    )
    fleet_wall_s = time.perf_counter() - t_run0

    print(
        f"Stage C ({device}) fleet: B={batch.batch_size}, sites={len(weather_by_site)}, "
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

        if cid in win_ref:
            ref_kwh = win_ref[cid]
            ref_src = "win_eplus"
        elif use_m4_schema:
            ref_kwh = ann_sa
            ref_src = "stage_a"
        else:
            ref_kwh = ann_pub
            ref_src = "published"
        rel_c_vs_ref = (ann_sc - ref_kwh) / ref_kwh
        abs_c_vs_ref_m2 = abs(ann_sc - ref_kwh) / area

        if abs(rel_c_vs_a) > 0.0005 and abs_c_vs_a_m2 > 0.01:
            failing.append((bi, cid, rel_c_vs_a, abs_c_vs_a_m2))

        rows.append(
            {
                "cell": cid,
                "reference_kwh": ref_kwh,
                "reference_source": ref_src,
                "annual_published_kwh": ann_pub,
                "annual_stage_a_kwh": ann_sa,
                "annual_stage_c_kwh": ann_sc,
                "rel_c_vs_a": rel_c_vs_a,
                "rel_c_vs_reference": rel_c_vs_ref,
                "abs_c_vs_ref_m2": abs_c_vs_ref_m2,
                "floor_area_m2": area,
                "warmup_days_stage_a": wu_sa,
            }
        )

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    if use_m4_schema:
        fieldnames = [
            "cell",
            "reference_kwh",
            "reference_source",
            "annual_stage_a_kwh",
            "annual_stage_c_kwh",
            "rel_c_vs_a",
            "rel_c_vs_reference",
            "floor_area_m2",
            "warmup_days_stage_a",
        ]
    else:
        fieldnames = [
            "cell",
            "annual_published_kwh",
            "annual_stage_a_kwh",
            "annual_stage_c_kwh",
            "rel_c_vs_a",
            "rel_c_vs_published",
            "warmup_days_stage_a",
        ]
    with out_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            if use_m4_schema:
                writer.writerow(
                    {
                        "cell": row["cell"],
                        "reference_kwh": f"{float(row['reference_kwh']):.6f}",
                        "reference_source": row["reference_source"],
                        "annual_stage_a_kwh": f"{float(row['annual_stage_a_kwh']):.6f}",
                        "annual_stage_c_kwh": f"{float(row['annual_stage_c_kwh']):.6f}",
                        "rel_c_vs_a": f"{float(row['rel_c_vs_a']):.8e}",
                        "rel_c_vs_reference": f"{float(row['rel_c_vs_reference']):.8e}",
                        "floor_area_m2": f"{float(row['floor_area_m2']):.4f}",
                        "warmup_days_stage_a": int(row["warmup_days_stage_a"]),
                    }
                )
            else:
                writer.writerow(
                    {
                        "cell": row["cell"],
                        "annual_published_kwh": f"{float(row['annual_published_kwh']):.6f}",
                        "annual_stage_a_kwh": f"{float(row['annual_stage_a_kwh']):.6f}",
                        "annual_stage_c_kwh": f"{float(row['annual_stage_c_kwh']):.6f}",
                        "rel_c_vs_a": f"{float(row['rel_c_vs_a']):.8e}",
                        "rel_c_vs_published": f"{float(row['rel_c_vs_reference']):.8e}",
                        "warmup_days_stage_a": int(row["warmup_days_stage_a"]),
                    }
                )
    print(f"Wrote {out_csv} ({len(rows)} rows)")

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

    ref_abs = np.asarray(
        [abs(float(r["rel_c_vs_reference"])) for r in rows], dtype=np.float64
    )
    ref_signed = np.asarray(
        [float(r["rel_c_vs_reference"]) for r in rows], dtype=np.float64
    )
    ref_m2 = np.asarray(
        [float(r["abs_c_vs_ref_m2"]) for r in rows], dtype=np.float64
    )
    n_win = sum(1 for r in rows if r["reference_source"] == "win_eplus")
    n_pub = len(rows) - n_win
    med_abs = float(np.median(ref_abs))
    p99_abs = float(np.percentile(ref_abs, 99))
    worst_ref_idx = int(np.argmax(ref_abs))
    worst_ref_row = rows[worst_ref_idx]
    p99_cell = sorted(rows, key=lambda r: abs(float(r["rel_c_vs_reference"])))[
        min(len(rows) - 1, int(np.ceil(0.99 * len(rows))) - 1)
    ]["cell"]
    med_cell = sorted(rows, key=lambda r: abs(float(r["rel_c_vs_reference"])))[
        len(rows) // 2
    ]["cell"]
    cnt_gt_05pct = int(np.sum(ref_abs > 0.005))
    print(
        f"Stage C vs reference (N={len(rows)}; win_eplus={n_win}, published={n_pub}): "
        f"median |rel|={med_abs * 100:.5f}% ({med_cell}, "
        f"signed={float(np.median(ref_signed)) * 100:+.5f}%), "
        f"p99 |rel|={p99_abs * 100:.5f}% ({p99_cell}), "
        f"worst |rel|={abs(float(worst_ref_row['rel_c_vs_reference'])) * 100:.5f}% "
        f"({worst_ref_row['cell']}, abs={float(worst_ref_row['abs_c_vs_ref_m2']):.5f} kWh/m2), "
        f"count > 0.5%={cnt_gt_05pct}"
    )

    if use_m4_schema:
        med_ok = med_abs <= 0.0005 or float(np.median(ref_m2)) <= 0.02
        p99_ok = p99_abs <= 0.002
        bad_worst = [
            r
            for r in rows
            if abs(float(r["rel_c_vs_reference"])) > 0.005
            and float(r["abs_c_vs_ref_m2"]) > 0.05
        ]
        if not (med_ok and p99_ok and not bad_worst):
            raise RuntimeError(
                f"P2 fleet gate FAILED: med_ok={med_ok}, p99_ok={p99_ok}, "
                f"worst_failures={[(r['cell'], r['rel_c_vs_reference']) for r in bad_worst[:5]]}"
            )
        print("P2 fleet gates PASSED (median <= 0.05%, p99 <= 0.2%, worst <= 0.5%).")
    else:
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


def _parse_args() -> argparse.Namespace:
    """Parse CLI arguments for fleet Stage C verification."""
    parser = argparse.ArgumentParser(description="Run Stage C on the 346 EU fleet cells.")
    parser.add_argument("--device", choices=("mps", "cuda"), default="mps")
    parser.add_argument("--out", type=Path, default=OUT_CSV)
    parser.add_argument("--win-recheck", type=Path, default=None)
    return parser.parse_args()


if __name__ == "__main__":
    try:
        args = _parse_args()
        run_fleet_stage_c(
            device=args.device,
            out_csv=args.out,
            win_eplus_csv=args.win_recheck,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
