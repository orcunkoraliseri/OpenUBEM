"""T07 — Stage and submit the fleet re-simulation to Speed.

Builds the 8,152-building case list (8,160 minus the 8 CP-2-excluded
buildings), packs it into one tarball (idfs + weather + fleet.lst),
ships it to Speed, and submits ONE sbatch --array=1-8152%32.
Fire-and-forget: this script never polls.

Usage:
    .venv/Scripts/python.exe scripts/cluster/t07_submit_resim.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import tarfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
REMOTE_HOST = "o_iseri@speed.encs.concordia.ca"
REMOTE_FLEET_BASE = "/speed-scratch/o_iseri/openubem/fleets"
FLEET_TAG = "t07_resim_2026-09-09"
REMOTE_FLEET_DIR = f"{REMOTE_FLEET_BASE}/{FLEET_TAG}"
REMOTE_SBATCH_DIR = "/speed-scratch/o_iseri/openubem/scripts/cluster"

WORK_BASE = Path(os.environ["TEMP"]) / "ubem_validation" / "t06_rebuild_2026-09-09"

CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]

EXCLUDED = {
    ("nyc_centre", "way_266170758"),
    ("la_centre", "way_425993506"),
    ("la_urban", "way_388772955"),
    ("austin_urban", "way_199742458"),
    ("austin_urban", "way_381803065"),
    ("austin_urban", "way_381805563"),
    ("austin_urban", "way_381810576"),
    ("austin_urban", "way_381810583"),
}

EXPECTED_TOTAL = 8152

LOCAL_TAR = Path(os.environ["TEMP"]) / f"{FLEET_TAG}.tar.gz"


def _ssh(cmd: str, timeout: int = 300) -> str:
    r = subprocess.run(
        ["ssh", REMOTE_HOST, f"bash -lc '{cmd}'"],
        capture_output=True, text=True, timeout=timeout,
    )
    return r.stdout + r.stderr


def build_case_list() -> tuple[list[tuple[str, str, Path]], dict[str, Path]]:
    cases: list[tuple[str, str, Path]] = []
    epw_by_cell: dict[str, Path] = {}
    for cell in CELLS:
        idf_dir = WORK_BASE / cell / "step3" / "idfs"
        idfs = sorted(idf_dir.glob("*.idf"))
        excluded_here = 0
        for idf in idfs:
            stem = idf.stem
            if (cell, stem) in EXCLUDED:
                excluded_here += 1
                continue
            cases.append((cell, stem, idf))
        epws = list((WORK_BASE / cell).rglob("*.epw"))
        if len(epws) != 1:
            raise SystemExit(f"STOP: expected exactly 1 epw for {cell}, found {len(epws)}: {epws}")
        epw_by_cell[cell] = epws[0]
        print(f"  {cell}: {len(idfs)} idfs, {excluded_here} excluded, epw={epws[0].name}")
    return cases, epw_by_cell


def main() -> None:
    print("T07 — building case list ...")
    cases, epw_by_cell = build_case_list()
    n = len(cases)
    print(f"Total case count: {n}")
    if n != EXPECTED_TOTAL:
        print(
            f"STOP: case count {n} != expected {EXPECTED_TOTAL}. "
            f"Not proceeding — report this discrepancy.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    unique_epws_by_name: dict[str, Path] = {}
    for p in epw_by_cell.values():
        unique_epws_by_name.setdefault(p.name, p)
    print(f"Unique EPWs to ship: {len(unique_epws_by_name)}")

    print(f"Packing tarball -> {LOCAL_TAR}")
    fleet_lst_lines = []
    with tarfile.open(LOCAL_TAR, "w:gz", compresslevel=4) as tf:
        for epw_name, epw in unique_epws_by_name.items():
            tf.add(str(epw), arcname=f"weather/{epw_name}")

        for cell, stem, idf_path in cases:
            tf.add(str(idf_path), arcname=f"idfs/{stem}.idf")
            fleet_lst_lines.append(f"{stem}\t{epw_by_cell[cell].name}")

        fleet_lst_bytes = ("\n".join(fleet_lst_lines) + "\n").encode("utf-8")
        import io
        info = tarfile.TarInfo(name="fleet.lst")
        info.size = len(fleet_lst_bytes)
        tf.addfile(info, io.BytesIO(fleet_lst_bytes))

    tar_size_mb = LOCAL_TAR.stat().st_size / 1e6
    print(f"Tarball built: {tar_size_mb:.1f} MB, {len(fleet_lst_lines)} fleet.lst lines")
    if len(fleet_lst_lines) != EXPECTED_TOTAL:
        raise SystemExit(f"STOP: fleet.lst line count {len(fleet_lst_lines)} != {EXPECTED_TOTAL}")

    print(f"Staging remote dir: {REMOTE_FLEET_DIR}")
    out = _ssh(f"mkdir -p {REMOTE_FLEET_DIR} {REMOTE_SBATCH_DIR}")
    print(out)

    print("Uploading tarball ...")
    r = subprocess.run(
        ["scp", str(LOCAL_TAR), f"{REMOTE_HOST}:{REMOTE_FLEET_DIR}/fleet.tar.gz"],
        capture_output=True, text=True, timeout=3600,
    )
    print(r.stdout, r.stderr)
    if r.returncode != 0:
        raise SystemExit(f"STOP: scp failed rc={r.returncode}")

    print("Uploading sbatch script ...")
    local_sbatch = REPO / "scripts" / "cluster" / "submit_fleet_t07.sbatch"
    r = subprocess.run(
        ["scp", str(local_sbatch), f"{REMOTE_HOST}:{REMOTE_SBATCH_DIR}/submit_fleet_t07.sbatch"],
        capture_output=True, text=True, timeout=300,
    )
    print(r.stdout, r.stderr)
    if r.returncode != 0:
        raise SystemExit(f"STOP: scp of sbatch script failed rc={r.returncode}")

    print("Extracting remotely ...")
    out = _ssh(
        f"cd {REMOTE_FLEET_DIR} && tar -xzf fleet.tar.gz && mkdir -p out && "
        f"echo IDF_COUNT=$(ls idfs | wc -l) && echo EPW_COUNT=$(ls weather | wc -l) && "
        f"echo FLEETLST_COUNT=$(wc -l < fleet.lst)",
        timeout=600,
    )
    print(out)

    print(f"Total case count: {n}. Parallel width (array throttle): 32.")
    print(f"Submitting sbatch --array=1-{n}%32 --time=7-00:00:00 ...")
    submit_cmd = (
        f"sbatch --array=1-{n}%32 --time=7-00:00:00 "
        f"--export=FLEET_DIR={REMOTE_FLEET_DIR} "
        f"{REMOTE_SBATCH_DIR}/submit_fleet_t07.sbatch"
    )
    out = _ssh(submit_cmd, timeout=120)
    print(out)

    LOCAL_TAR.unlink(missing_ok=True)
    print("Done. Poll with: sacct -u o_iseri --format=JobID,State,Elapsed,ExitCode")


if __name__ == "__main__":
    main()
