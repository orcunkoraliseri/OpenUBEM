"""C08 fetch step: Download R3 cluster results and build 04_simulation_manifest.parquet.

Usage: python scripts/cluster/fetch_r3_results.py <JOB_ID>
  JOB_ID: SLURM array job ID (e.g. 955200)
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

REMOTE = "o_iseri@speed.encs.concordia.ca"
FLEET_REMOTE = "/speed-scratch/o_iseri/openubem/fleets/r3"
R3_BASE = Path(tempfile.gettempdir()) / "ubem_boston_r3"
LOCAL_SIM = R3_BASE / "sim"
IDF_DIR = R3_BASE / "step3" / "idfs"
EPW_PATH = Path(r"C:\Users\o_iseri\AppData\Local\openubem\epw_cache\USA_MA_Boston.994971_TMYx.2011-2025.epw")
MANIFEST_OUT = R3_BASE / "04_simulation_manifest.parquet"
REPO = Path(__file__).parent.parent.parent

JOB_ID = sys.argv[1] if len(sys.argv) > 1 else ""

LOCAL_SIM.mkdir(parents=True, exist_ok=True)

def ssh(cmd: str) -> str:
    result = subprocess.run(
        ["ssh", REMOTE, f"bash -lc '{cmd}'"],
        capture_output=True, text=True, timeout=60
    )
    return result.stdout.strip()

def scp_file(remote_path: str, local_path: Path) -> bool:
    r = subprocess.run(
        ["scp", "-q", f"{REMOTE}:{remote_path}", str(local_path)],
        capture_output=True, text=True, timeout=120
    )
    return r.returncode == 0


print(f"[C08-fetch] Reading fleet.lst from cluster...")
fleet_lst_text = ssh(f"cat {FLEET_REMOTE}/fleet.lst")
osm_ids = [line.strip() for line in fleet_lst_text.splitlines() if line.strip()]
N = len(osm_ids)
print(f"[C08-fetch] {N} buildings to fetch")

(LOCAL_SIM / "fleet.lst").write_text("\n".join(osm_ids) + "\n")

success = 0
failed = []
for i, osm_id in enumerate(osm_ids, 1):
    bdir = LOCAL_SIM / osm_id
    bdir.mkdir(parents=True, exist_ok=True)
    for f in ("eplusout.sql", "eplusout.err", "eplusout.end"):
        scp_file(f"{FLEET_REMOTE}/out/{osm_id}/{f}", bdir / f)
    end_path = bdir / "eplusout.end"
    if end_path.exists() and "Completed Successfully" in end_path.read_text(errors="replace"):
        success += 1
    else:
        failed.append(osm_id)
    if i % 50 == 0 or i == N:
        print(f"  fetched {i}/{N} (success={success} fail={len(failed)})")

print(f"\n[C08-fetch] Fetch complete: {success} success, {len(failed)} failed")
if failed:
    print(f"[C08-fetch] Failed buildings: {failed[:20]}")

print(f"\n[C08-fetch] Building manifest...")
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location("make_manifest_from_cluster", REPO / "scripts" / "cluster" / "make_manifest_from_cluster.py")
_mod = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
build_manifest = _mod.build_manifest

df = build_manifest(
    fleet_dir=LOCAL_SIM,
    idf_source_dir=IDF_DIR,
    epw_path=EPW_PATH,
    job_id=JOB_ID,
)
print(df[["osm_id", "status", "n_warnings", "n_severe", "wall_clock_s"]].to_string())

MANIFEST_OUT.parent.mkdir(parents=True, exist_ok=True)
df.to_parquet(str(MANIFEST_OUT), index=False)
print(f"\n[C08-fetch] Manifest written: {MANIFEST_OUT} ({len(df)} rows)")
n_success_mf = (df["status"] == "success").sum()
n_failed_mf = (df["status"] != "success").sum()
print(f"[C08-fetch] Manifest: {n_success_mf} success, {n_failed_mf} failed")

if n_failed_mf > 0:
    failed_rows = df[df["status"] != "success"]
    print(f"[C08-fetch] Failed rows:")
    for _, r in failed_rows.iterrows():
        print(f"  osm_id={r['osm_id']} status={r['status']} err={r['error_summary'][:100]}")

print(f"\n[C08-fetch] Cleaning remote out/ dir...")
ssh(f"rm -rf {FLEET_REMOTE}/out")
print(f"[C08-fetch] Remote out/ cleaned.")
print(f"[C08-fetch] DONE.")
