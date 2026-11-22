import csv
import difflib
import json
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import sys
import time

try:
    from scripts.gpusim import make_golden
except ImportError:
    import make_golden

REPO_ROOT = make_golden.REPO_ROOT
REP2_DIR = make_golden.REP2_DIR
BASE_CELL_ID = make_golden.BASE_CELL_ID
TIMING_ROOT = REPO_ROOT / "openubem/outputs/gpusim_golden_runs/timing"
TIMING_CSV_PATH = REPO_ROOT / "openubem/outputs/gpusim_m0_timing.csv"
ENERGYPLUS_BIN = Path("/Applications/EnergyPlus-23-1-0/energyplus")
ENERGYPLUS_J_TO_KWH = 1.0 / 3.6e6
ELAPSED_RE = re.compile(
    r"Elapsed Time=\s*(\d+)hr\s+(\d+)min\s+([0-9.]+)sec"
)


def prepare_timing_folders() -> tuple[Path, Path, float]:
    """Create the as_built and sizing_off folders for timing cell 1.

    Returns:
        Tuple of ``(as_built_dir, sizing_off_dir, manifest_heating_kwh)``.

    Raises:
        FileNotFoundError: If required source inputs are missing.
        ValueError: If SimulationControl fields do not match the expected baseline.
    """
    manifest_path = REP2_DIR / "manifests" / f"{BASE_CELL_ID}.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_heating_kwh = float(manifest["heating_kwh"])

    epw_src = make_golden.map_windows_path(manifest["epw_path"])
    idf_src = REP2_DIR / "idfs" / f"{BASE_CELL_ID}.idf"
    sched_src = REP2_DIR / "schedules" / f"{BASE_CELL_ID}.csv"
    for path in (idf_src, epw_src, sched_src):
        if not path.exists():
            raise FileNotFoundError(f"Missing required input: {path}")

    raw_idf = idf_src.read_text(encoding="utf-8")
    as_built_idf = make_golden.rewrite_schedule_paths_to_basename(raw_idf)

    objects = make_golden.parse_idf(as_built_idf)
    sim_ctrls = [o for o in objects if o.obj_type == "SIMULATIONCONTROL"]
    if len(sim_ctrls) != 1:
        raise ValueError(f"Expected 1 SimulationControl, found {len(sim_ctrls)}")
    sc = sim_ctrls[0]
    actual = [f.value for f in sc.fields[1:8]]
    expected = ["Yes", "Yes", "Yes", "No", "Yes", "No", "1"]
    if actual != expected:
        raise ValueError(
            f"Unexpected SimulationControl fields: {actual} != {expected}"
        )
    edits: list[tuple[int, int, str]] = []
    for idx in (1, 2, 3):
        make_golden.replace_field(edits, sc, idx, "No")
    sizing_off_idf = make_golden.apply_edits(as_built_idf, edits)

    diff = list(
        difflib.unified_diff(
            as_built_idf.splitlines(),
            sizing_off_idf.splitlines(),
            fromfile="as_built/in.idf",
            tofile="sizing_off/in.idf",
            n=0,
            lineterm="",
        )
    )
    print("=== Timing pair IDF diff ===")
    for line in diff:
        print(f"  {line}")

    as_built_dir = TIMING_ROOT / "as_built"
    sizing_off_dir = TIMING_ROOT / "sizing_off"
    for folder, idf_text in (
        (as_built_dir, as_built_idf),
        (sizing_off_dir, sizing_off_idf),
    ):
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "in.idf").write_text(idf_text, encoding="utf-8")
        shutil.copy2(epw_src, folder / "in.epw")
        shutil.copy2(sched_src, folder / sched_src.name)

    return as_built_dir, sizing_off_dir, manifest_heating_kwh


def clean_run_outputs(run_dir: Path) -> None:
    """Remove prior EnergyPlus output files while keeping run inputs.

    Args:
        run_dir: Run directory to clean before invoking EnergyPlus.
    """
    keep = {"in.idf", "in.epw", f"{BASE_CELL_ID}.csv"}
    for item in run_dir.iterdir():
        if item.name not in keep:
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()


def parse_elapsed_seconds(run_dir: Path) -> float:
    """Extract EnergyPlus internal elapsed seconds from eplusout.end or .err.

    Args:
        run_dir: Completed EnergyPlus run directory.

    Returns:
        Elapsed time reported by EnergyPlus in seconds.

    Raises:
        ValueError: If Elapsed Time cannot be parsed.
    """
    for filename in ("eplusout.end", "eplusout.err"):
        path = run_dir / filename
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        match = ELAPSED_RE.search(text)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            seconds = float(match.group(3))
            return hours * 3600.0 + minutes * 60.0 + seconds
    raise ValueError(f"Could not parse Elapsed Time in {run_dir}")


def extract_heating_kwh(csv_path: Path) -> float:
    """Sum hourly ideal loads heating energy from eplusout.csv in kWh.

    Args:
        csv_path: Path to ``eplusout.csv``.

    Returns:
        Annual heating energy in kWh.

    Raises:
        ValueError: If the hourly heating column is missing.
    """
    with csv_path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError(f"Empty eplusout.csv header: {csv_path}")
        columns = [
            field
            for field in reader.fieldnames
            if "zone ideal loads zone total heating energy" in field.casefold()
            and "[j]" in field.casefold()
            and "(hourly)" in field.casefold()
        ]
        if not columns:
            raise ValueError(f"Missing hourly heating column in {csv_path}")
        total_j = 0.0
        for row in reader:
            total_j += sum(float(row[col]) for col in columns)
    return total_j * ENERGYPLUS_J_TO_KWH


def run_once(run_dir: Path) -> tuple[float, float, float]:
    """Run EnergyPlus once synchronously and collect timing and heating kWh.

    Args:
        run_dir: Prepared run folder containing ``in.idf`` and ``in.epw``.

    Returns:
        Tuple of ``(wall_seconds, eplus_elapsed_seconds, heating_kwh)``.

    Raises:
        RuntimeError: If EnergyPlus fails or logs severe/fatal errors.
    """
    clean_run_outputs(run_dir)
    idf_path = run_dir / "in.idf"
    epw_path = run_dir / "in.epw"
    cmd = [
        str(ENERGYPLUS_BIN),
        "-x",
        "-r",
        "-w",
        str(epw_path),
        "-d",
        str(run_dir),
        str(idf_path),
    ]
    t0 = time.perf_counter()
    proc = subprocess.run(
        cmd,
        cwd=run_dir,
        capture_output=True,
        text=True,
        timeout=300,
    )
    wall_s = time.perf_counter() - t0

    end_path = run_dir / "eplusout.end"
    end_text = (
        end_path.read_text(encoding="utf-8", errors="replace")
        if end_path.exists()
        else ""
    )
    err_path = run_dir / "eplusout.err"
    err_text = (
        err_path.read_text(encoding="utf-8", errors="replace")
        if err_path.exists()
        else ""
    )
    severe = err_text.count("** Severe  **")
    fatal = err_text.count("**  Fatal  **")

    if (
        proc.returncode != 0
        or "EnergyPlus Completed Successfully" not in end_text
        or severe > 0
        or fatal > 0
    ):
        raise RuntimeError(
            f"EnergyPlus failed in {run_dir}: rc={proc.returncode}, "
            f"severe={severe}, fatal={fatal}, end={end_text.strip()!r}"
        )

    eplus_s = parse_elapsed_seconds(run_dir)
    heating_kwh = extract_heating_kwh(run_dir / "eplusout.csv")
    return wall_s, eplus_s, heating_kwh


def run_timing_pair() -> int:
    """Execute the 6-run serial timing pair and write gpusim_m0_timing.csv.

    Returns:
        Process exit code (0 on success, 1 on heating parity failure).
    """
    if not ENERGYPLUS_BIN.exists():
        raise FileNotFoundError(f"EnergyPlus binary missing: {ENERGYPLUS_BIN}")

    as_built_dir, sizing_off_dir, manifest_kwh = prepare_timing_folders()
    folders = {"as_built": as_built_dir, "sizing_off": sizing_off_dir}
    rows: list[dict[str, object]] = []

    print("\n=== Running 6 serial EnergyPlus timing runs ===")
    for repeat in (1, 2, 3):
        for variant in ("as_built", "sizing_off"):
            wall_s, eplus_s, heating_kwh = run_once(folders[variant])
            rel_diff_pct = (heating_kwh - manifest_kwh) / manifest_kwh * 100.0
            row = {
                "variant": variant,
                "repeat": repeat,
                "wall_s": round(wall_s, 6),
                "eplus_elapsed_s": round(eplus_s, 4),
                "heating_kwh": repr(heating_kwh),
                "manifest_heating_kwh": repr(manifest_kwh),
                "rel_diff_pct": f"{rel_diff_pct:.8f}",
            }
            rows.append(row)
            print(
                f"  repeat={repeat} {variant:10s}: "
                f"wall={wall_s:.3f}s, eplus={eplus_s:.2f}s, "
                f"heating={heating_kwh:.6f} kWh (diff={rel_diff_pct:+.6f}%)"
            )

    TIMING_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "variant",
        "repeat",
        "wall_s",
        "eplus_elapsed_s",
        "heating_kwh",
        "manifest_heating_kwh",
        "rel_diff_pct",
    ]
    with TIMING_CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote {len(rows)} rows to {TIMING_CSV_PATH}")

    by_variant: dict[str, list[dict[str, object]]] = {
        "as_built": [r for r in rows if r["variant"] == "as_built"],
        "sizing_off": [r for r in rows if r["variant"] == "sizing_off"],
    }
    med_wall_ab = statistics.median(float(r["wall_s"]) for r in by_variant["as_built"])
    med_wall_so = statistics.median(
        float(r["wall_s"]) for r in by_variant["sizing_off"]
    )
    med_ep_ab = statistics.median(
        float(r["eplus_elapsed_s"]) for r in by_variant["as_built"]
    )
    med_ep_so = statistics.median(
        float(r["eplus_elapsed_s"]) for r in by_variant["sizing_off"]
    )
    wall_diff = med_wall_ab - med_wall_so
    ep_diff = med_ep_ab - med_ep_so

    print("=== Summary ===")
    print(
        f"  as_built   median wall={med_wall_ab:.3f}s, "
        f"eplus_elapsed={med_ep_ab:.2f}s"
    )
    print(
        f"  sizing_off median wall={med_wall_so:.3f}s, "
        f"eplus_elapsed={med_ep_so:.2f}s"
    )
    print(
        f"  savings    wall={wall_diff:.3f}s ({wall_diff / med_wall_ab * 100:.1f}%), "
        f"eplus_elapsed={ep_diff:.2f}s ({ep_diff / med_ep_ab * 100:.1f}%)"
    )

    max_diff = max(abs(float(r["rel_diff_pct"])) for r in rows)
    print(f"  max |rel_diff_pct| vs manifest: {max_diff:.8f}%")
    if max_diff > 0.01:
        print("FAIL: heating difference exceeds 0.01%", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(run_timing_pair())
