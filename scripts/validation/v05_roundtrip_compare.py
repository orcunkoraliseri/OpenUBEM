"""V05: Submit counterpart IDFs to cluster (sbatch array, fleets/val2c/),
fetch results, and produce the round-trip report.

Two-phase script:
  Phase A (--submit): pack + ship + submit sbatch array for counterparts.
  Phase B (--report): fetch results + produce roundtrip_report.csv + markdown table.

Usage:
  python v05_roundtrip_compare.py --submit
  python v05_roundtrip_compare.py --report [--job-id <JOB_ID>]
"""
from __future__ import annotations

import argparse
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

import pandas as pd

REPO = Path(__file__).parent.parent.parent
OUT_BASE = Path(tempfile.gettempdir()) / "ubem_validation" / "level2"
COUNTERPARTS_DIR = OUT_BASE / "counterparts"
REF_EUI_PARQUET = OUT_BASE / "reference_eui.parquet"
MAPPING_CSV = OUT_BASE / "mapping.csv"
REPORT_CSV = OUT_BASE / "roundtrip_report.csv"
REPORT_MD = OUT_BASE / "roundtrip_report.md"
JOB_ID_FILE = OUT_BASE / "val2c_job_id.txt"

REMOTE = "o_iseri@speed.encs.concordia.ca"
REMOTE_BASE = "/speed-scratch/o_iseri/openubem"
REMOTE_FLEET = f"{REMOTE_BASE}/fleets/val2c"
REMOTE_SBATCH = f"{REMOTE_BASE}/scripts/submit_fleet.sbatch"
SBATCH_LOCAL = REPO / "scripts" / "cluster" / "submit_fleet.sbatch"

THROTTLE = 32
TIME_LIMIT = "01:30:00"

GJ_TO_KWH = 1e9 / 3.6e6
FUEL_COLS = ["Electricity", "Natural Gas", "Additional Fuel", "District Cooling",
             "District Heating Water", "District Heating Steam", "Steam", "Water"]


def _ssh(cmd: str, check: bool = True) -> str:
    result = subprocess.run(
        ["ssh", REMOTE, f"bash -lc '{cmd}'"],
        capture_output=True, text=True, timeout=60, check=check,
    )
    return result.stdout.strip()


def _query_eui(sql_path: Path, floor_area: float) -> dict[str, float] | None:
    if not sql_path.exists():
        return None
    try:
        conn = sqlite3.connect(f"file:{sql_path}?mode=ro", uri=True)
        rows = conn.execute("""
            SELECT RowName, ColumnName, CAST(Value AS REAL)
            FROM TabularDataWithStrings
            WHERE ReportName = 'AnnualBuildingUtilityPerformanceSummary'
              AND TableName = 'End Uses'
              AND Units = 'GJ'
        """).fetchall()
        conn.close()
    except Exception:
        return None

    totals: dict[str, float] = {}
    for row_name, col_name, val in rows:
        if col_name not in FUEL_COLS:
            continue
        totals[row_name] = totals.get(row_name, 0.0) + (val or 0.0)

    def _eui(rn: str) -> float:
        return totals.get(rn, 0.0) * GJ_TO_KWH / floor_area

    heat = _eui("Heating")
    cool = _eui("Cooling")
    light = _eui("Interior Lighting")
    equip = _eui("Interior Equipment")
    known = {"Heating", "Cooling", "Interior Lighting", "Interior Equipment"}
    other = sum(v for k, v in totals.items() if k not in known) * GJ_TO_KWH / floor_area
    total = heat + cool + light + equip + other
    return {"heat": heat, "cool": cool, "light": light, "equip": equip, "other": other, "total": total}


def _submit(manifest: pd.DataFrame, epw_path: str) -> None:
    idf_dir = COUNTERPARTS_DIR / "idfs"
    stems = [str(r["ref_stem"]) for _, r in manifest.iterrows() if r["generation_status"] == "success"]
    n = len(stems)
    print(f"[V05-submit] {n} counterpart IDFs to submit")

    wx_dir = OUT_BASE / "weather"
    fleet_lst = OUT_BASE / "fleet_val2c.lst"
    idf_names = [s + "_counterpart" for s in stems]
    fleet_lst.write_bytes(("\n".join(idf_names) + "\n").encode("utf-8"))

    tarball = OUT_BASE / "val2c.tar.gz"
    print(f"[V05-submit] Packing tarball: {tarball}")
    with tarfile.open(tarball, "w:gz") as tf:
        for name in idf_names:
            src = idf_dir / f"{name}.idf"
            if src.exists():
                tf.add(src, arcname=f"idfs/{name}.idf")
        tf.add(wx_dir, arcname="weather")
        tf.add(fleet_lst, arcname="fleet.lst")

    _ssh(f"mkdir -p {REMOTE_FLEET}")
    subprocess.run(["scp", str(tarball), f"{REMOTE}:{REMOTE_FLEET}/val2c.tar.gz"], check=True)
    _ssh(f"cd {REMOTE_FLEET} && tar -xzf val2c.tar.gz && rm val2c.tar.gz")
    subprocess.run(["scp", str(SBATCH_LOCAL), f"{REMOTE}:{REMOTE_BASE}/scripts/submit_fleet.sbatch"], check=True)

    sbatch_out = subprocess.run(
        ["ssh", REMOTE,
         f"bash -lc 'sbatch --array=1-{n}%{THROTTLE} --time={TIME_LIMIT} "
         f"--export=FLEET_DIR={REMOTE_FLEET} {REMOTE_SBATCH}'"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    print(f"[V05-submit] sbatch output: {sbatch_out}")
    job_id = sbatch_out.split()[-1]
    JOB_ID_FILE.write_text(job_id)
    print(f"[V05-submit] Job ID: {job_id} (written to {JOB_ID_FILE})")
    print(f"[V05-submit] Monitor: ssh {REMOTE} bash -lc 'squeue -j {job_id}'")
    print(f"[V05-submit] When done: python scripts/validation/v05_roundtrip_compare.py --report --job-id {job_id}")
    print("[V05-submit] DONE")


def _fetch_and_report(job_id: str) -> None:
    val2c_out = OUT_BASE / "val2c_out"
    val2c_out.mkdir(parents=True, exist_ok=True)

    fleet_lst_text = _ssh(f"cat {REMOTE_FLEET}/fleet.lst", check=False)
    stems = [l.strip() for l in fleet_lst_text.splitlines() if l.strip()]
    n = len(stems)
    print(f"[V05-report] Fetching {n} results from cluster...")

    success_count, failed = 0, []
    for i, name in enumerate(stems, 1):
        bdir = val2c_out / name
        bdir.mkdir(exist_ok=True)
        for f in ("eplusout.sql", "eplusout.err", "eplusout.end"):
            subprocess.run(
                ["scp", "-q",
                 f"{REMOTE}:{REMOTE_FLEET}/out/{name}/{f}",
                 str(bdir / f)],
                capture_output=True, text=True, timeout=120,
            )
        end_path = bdir / "eplusout.end"
        if end_path.exists() and "Completed Successfully" in end_path.read_text(errors="replace"):
            success_count += 1
        else:
            failed.append(name)
        if i % 10 == 0 or i == n:
            print(f"  fetched {i}/{n}  success={success_count}  fail={len(failed)}")

    print(f"\n[V05-report] Fetch complete: {success_count}/{n} success")

    if failed:
        print(f"[V05-report] FAILED counterparts: {failed}")
        if job_id:
            sacct = _ssh(f"sacct -j {job_id} --format=JobID,State,ExitCode --noheader 2>&1 | head -40", check=False)
            print(f"\nsacct:\n{sacct}")

    mapping = pd.read_csv(MAPPING_CSV)
    ref_eui = pd.read_parquet(REF_EUI_PARQUET)
    manifest = pd.read_parquet(COUNTERPARTS_DIR / "03_idf_manifest.parquet")
    inv_df = pd.read_csv(OUT_BASE / "ref_inventory.csv")

    ref_eui_idx = ref_eui.set_index("filename")

    report_rows = []
    for _, mrow in manifest.iterrows():
        ref_stem = str(mrow["ref_stem"])
        ref_fname = ref_stem + ".idf"
        counter_name = ref_stem + "_counterpart"
        archetype = str(mrow["archetype_id"])
        _inv_match_outer = inv_df[inv_df["filename"] == ref_fname]
        floor_area = float(_inv_match_outer.iloc[0]["conditioned_floor_area_m2"]) if not _inv_match_outer.empty else 1000.0

        inv_row_match = mapping[mapping["filename"] == ref_fname]
        if inv_row_match.empty:
            continue
        openuben_arch = inv_row_match.iloc[0]["openuben_archetype"]
        if openuben_arch == "NOT_MAPPED":
            continue

        bdir = val2c_out / counter_name
        sql_path = bdir / "eplusout.sql"
        status = "failed"
        end_path = bdir / "eplusout.end"
        if end_path.exists() and "Completed Successfully" in end_path.read_text(errors="replace"):
            status = "success"

        inv_match = inv_df[inv_df["filename"] == ref_fname]
        counter_floor_area = float(inv_match.iloc[0]["conditioned_floor_area_m2"]) if not inv_match.empty else 1000.0

        counter_eui = _query_eui(sql_path, counter_floor_area) if status == "success" else None

        ref_total = float(ref_eui_idx.loc[ref_fname, "total_site_eui_kwh_m2"]) if ref_fname in ref_eui_idx.index else None
        ref_heat = float(ref_eui_idx.loc[ref_fname, "heating_eui_kwh_m2"]) if ref_fname in ref_eui_idx.index else None
        ref_cool = float(ref_eui_idx.loc[ref_fname, "cooling_eui_kwh_m2"]) if ref_fname in ref_eui_idx.index else None
        ref_light = float(ref_eui_idx.loc[ref_fname, "lighting_eui_kwh_m2"]) if ref_fname in ref_eui_idx.index else None
        ref_equip = float(ref_eui_idx.loc[ref_fname, "equipment_eui_kwh_m2"]) if ref_fname in ref_eui_idx.index else None

        dev_pct = None
        verdict = "N/A"
        if counter_eui and ref_total:
            dev_pct = (counter_eui["total"] - ref_total) / ref_total * 100
            verdict = "PASS" if abs(dev_pct) <= 5.0 else "FAIL"

        report_rows.append({
            "ref_filename": ref_fname,
            "openuben_archetype": openuben_arch,
            "ref_total_eui": ref_total,
            "counter_total_eui": counter_eui["total"] if counter_eui else None,
            "dev_pct": round(dev_pct, 2) if dev_pct is not None else None,
            "verdict_5pct": verdict,
            "ref_heat": ref_heat, "counter_heat": counter_eui["heat"] if counter_eui else None,
            "ref_cool": ref_cool, "counter_cool": counter_eui["cool"] if counter_eui else None,
            "ref_light": ref_light, "counter_light": counter_eui["light"] if counter_eui else None,
            "ref_equip": ref_equip, "counter_equip": counter_eui["equip"] if counter_eui else None,
            "counter_status": status,
        })

    report_df = pd.DataFrame(report_rows)
    report_df.to_csv(REPORT_CSV, index=False)
    print(f"\n[V05-report] Report CSV: {REPORT_CSV}")

    n_mapped = len(report_df)
    n_pass = (report_df["verdict_5pct"] == "PASS").sum()
    n_fail = (report_df["verdict_5pct"] == "FAIL").sum()
    n_na = (report_df["verdict_5pct"] == "N/A").sum()
    print(f"[V05-report] {n_pass}/{n_mapped} PASS  {n_fail} FAIL  {n_na} N/A (sim failed)")

    md_lines = [
        "# Level-2 DOE Round-Trip Report",
        "",
        f"n_pass / n_mapped = **{n_pass} / {n_mapped}**  (±5% gate, report-only per V-R5-5)",
        "",
        "| Archetype | Ref EUI | OUB EUI | Dev% | Verdict | Ref-H | Ctr-H | Ref-C | Ctr-C | Ref-L | Ctr-L | Ref-E | Ctr-E |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for _, r in report_df.sort_values("openuben_archetype").iterrows():
        def _fmt(v):
            return f"{v:.1f}" if v is not None and str(v) != "nan" else "—"
        md_lines.append(
            f"| {r['openuben_archetype']} | {_fmt(r['ref_total_eui'])} | {_fmt(r['counter_total_eui'])} | "
            f"{_fmt(r['dev_pct'])} | {r['verdict_5pct']} | "
            f"{_fmt(r['ref_heat'])} | {_fmt(r['counter_heat'])} | "
            f"{_fmt(r['ref_cool'])} | {_fmt(r['counter_cool'])} | "
            f"{_fmt(r['ref_light'])} | {_fmt(r['counter_light'])} | "
            f"{_fmt(r['ref_equip'])} | {_fmt(r['counter_equip'])} |"
        )
    md_lines += ["", f"**Summary:** {n_pass}/{n_mapped} PASS, {n_fail} FAIL, {n_na} N/A"]

    REPORT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"[V05-report] Report MD: {REPORT_MD}")

    if len(report_df) > 0 and "dev_pct" in report_df.columns:
        top_dev = report_df.dropna(subset=["dev_pct"]).reindex(
            report_df.dropna(subset=["dev_pct"])["dev_pct"].abs().sort_values(ascending=False).index
        ).head(5)
        print("\n[V05-report] Largest deviations:")
        print(top_dev[["openuben_archetype", "ref_total_eui", "counter_total_eui", "dev_pct", "verdict_5pct"]].to_string(index=False))

    print("[V05-report] DONE")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--submit", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--job-id", default="")
    args = parser.parse_args()

    if not args.submit and not args.report:
        parser.print_help()
        sys.exit(1)

    if args.submit:
        manifest = pd.read_parquet(COUNTERPARTS_DIR / "03_idf_manifest.parquet")
        epw_path = (OUT_BASE / "epw_path.txt").read_text().strip()
        _submit(manifest, epw_path)

    if args.report:
        job_id = args.job_id
        if not job_id and JOB_ID_FILE.exists():
            job_id = JOB_ID_FILE.read_text().strip()
        _fetch_and_report(job_id)


if __name__ == "__main__":
    main()
