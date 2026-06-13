"""Local driver: pack pilot8 IDFs → scp → sbatch → poll → fetch results."""

import os
import subprocess
import sys
import time
import tempfile
import tarfile
import shutil
from pathlib import Path

REMOTE_HOST = "o_iseri@speed.encs.concordia.ca"
REMOTE_BASE = "/speed-scratch/o_iseri/openubem"
LOCAL_CLUSTER_TMP = Path(tempfile.gettempdir()) / "ubem_cluster_pilot8"
SBATCH_SCRIPT = Path(__file__).parent / "submit_fleet.sbatch"

PILOT_IDF_DIR = Path(tempfile.gettempdir()) / "ubem_boston_r1" / "step3" / "idfs"
EPW_CACHE = Path(os.environ["LOCALAPPDATA"]) / "openubem" / "epw_cache"
EPW_NAME = "USA_MA_Boston.994971_TMYx.2011-2025.epw"

POLL_INTERVAL_S = 60


def ssh(cmd: str) -> str:
    result = subprocess.run(
        ["ssh", REMOTE_HOST, f"bash -lc '{cmd}'"],
        capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def scp_to(local: str, remote: str) -> None:
    subprocess.run(["scp", local, f"{REMOTE_HOST}:{remote}"], check=True)


def pack_pilot(fleet_dir: Path, osm_ids: list[str]) -> Path:
    """Stage IDFs + EPW locally, return staging dir."""
    fleet_dir.mkdir(parents=True, exist_ok=True)
    idf_dir = fleet_dir / "idfs"
    wx_dir = fleet_dir / "weather"
    idf_dir.mkdir(exist_ok=True)
    wx_dir.mkdir(exist_ok=True)

    for osm_id in osm_ids:
        src = PILOT_IDF_DIR / f"{osm_id}.idf"
        shutil.copy2(src, idf_dir / f"{osm_id}.idf")

    shutil.copy2(EPW_CACHE / EPW_NAME, wx_dir / EPW_NAME)

    lst = fleet_dir / "fleet.lst"
    lst.write_text("\n".join(osm_ids) + "\n")

    tarball = fleet_dir / "pilot8.tar.gz"
    with tarfile.open(tarball, "w:gz") as tf:
        tf.add(idf_dir, arcname="idfs")
        tf.add(wx_dir, arcname="weather")
        tf.add(lst, arcname="fleet.lst")
    return tarball


def submit_array(fleet_dir_remote: str, n: int, throttle: int = 8) -> str:
    remote_sbatch = f"{REMOTE_BASE}/scripts/submit_fleet.sbatch"
    result = subprocess.run(
        ["ssh", REMOTE_HOST,
         f"bash -lc 'sbatch --array=1-{n}%{throttle} --export=FLEET_DIR={fleet_dir_remote} {remote_sbatch}'"],
        capture_output=True, text=True, check=True
    )
    line = result.stdout.strip()
    # "Submitted batch job 123456"
    job_id = line.split()[-1]
    print(f"Submitted job array: {job_id}")
    return job_id


def poll_until_done(job_id: str) -> list[dict]:
    """Poll sacct every POLL_INTERVAL_S until all array tasks reach a terminal state."""
    while True:
        out = subprocess.run(
            ["ssh", REMOTE_HOST,
             f"bash -lc 'sacct -j {job_id} --format=JobID,State,Elapsed,ExitCode --noheader 2>&1'"],
            capture_output=True, text=True
        ).stdout.strip()
        rows = [r for r in out.splitlines() if r.strip() and "." not in r.split()[0].split("_")[0].replace(job_id, "X")]
        # Filter to array task rows only (contain job_id_N format)
        task_rows = [r for r in out.splitlines() if "_" in r.split()[0] and "." not in r.split()[0]]
        if not task_rows:
            # fall back to batch row
            task_rows = [r for r in out.splitlines() if r.strip()]

        states = [r.split()[1] for r in task_rows if len(r.split()) >= 2]
        terminal = {"COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "NODE_FAIL"}
        print(f"[poll] job {job_id}: {len(task_rows)} tasks, states: {set(states)}")

        if states and all(s in terminal for s in states):
            parsed = []
            for r in task_rows:
                parts = r.split()
                if len(parts) >= 4:
                    parsed.append({
                        "job_id": parts[0],
                        "state": parts[1],
                        "elapsed": parts[2],
                        "exit_code": parts[3],
                    })
            return parsed

        time.sleep(POLL_INTERVAL_S)


def fetch_results(fleet_dir_remote: str, osm_ids: list[str], local_out: Path) -> None:
    for osm_id in osm_ids:
        dest = local_out / osm_id
        dest.mkdir(parents=True, exist_ok=True)
        for fname in ("eplusout.sql", "eplusout.err", "eplusout.end"):
            src = f"{REMOTE_HOST}:{fleet_dir_remote}/out/{osm_id}/{fname}"
            subprocess.run(["scp", src, str(dest / fname)], check=False)


def main():
    osm_ids = [
        "29716487", "240391795", "241978446", "1281831066",
        "29573070", "241186243", "788015166", "458718877"
    ]
    fleet_remote = f"{REMOTE_BASE}/fleets/pilot8"
    scripts_remote = f"{REMOTE_BASE}/scripts"

    print("=== C02: Pack and ship pilot8 ===")
    LOCAL_CLUSTER_TMP.mkdir(parents=True, exist_ok=True)
    tarball = pack_pilot(LOCAL_CLUSTER_TMP / "stage", osm_ids)
    print(f"Packed: {tarball}")

    scp_to(str(tarball), f"{fleet_remote}/pilot8.tar.gz")
    ssh(f"cd {fleet_remote} && tar -xzf pilot8.tar.gz && mkdir -p out")
    count = ssh(f"ls {fleet_remote}/idfs | wc -l")
    print(f"Remote IDF count: {count}")
    assert count.strip() == "8", f"Expected 8 IDFs, got {count}"

    print("=== C03: Submit array job ===")
    # Ensure sbatch script is on remote
    ssh(f"mkdir -p {scripts_remote}")
    scp_to(str(SBATCH_SCRIPT), f"{scripts_remote}/submit_fleet.sbatch")
    job_id = submit_array(fleet_remote, n=8, throttle=8)

    print(f"Polling job {job_id}...")
    task_results = poll_until_done(job_id)
    print("All tasks terminal:")
    for tr in task_results:
        print(f"  {tr}")

    print("=== Fetch results ===")
    fetch_results(fleet_remote, osm_ids, LOCAL_CLUSTER_TMP / "results")
    print(f"Results fetched to {LOCAL_CLUSTER_TMP / 'results'}")


if __name__ == "__main__":
    main()
