"""C04 parity check: compare cluster pilot8 results vs local R1 reference.

Usage:
    python check_parity.py <cluster_results_dir>

cluster_results_dir: directory containing <osm_id>/eplusout.sql subdirs (fetched from cluster).
R1 reference: %TEMP%/ubem_boston_r1/sim/<osm_id>/eplusout.sql
Parity tolerance: <=1.0% relative per §4.
"""

import sys
import sqlite3
import tempfile
from pathlib import Path

R1_SIM = Path(tempfile.gettempdir()) / "ubem_boston_r1" / "sim"
OSM_IDS = [
    "29716487", "240391795", "241978446", "1281831066",
    "29573070", "241186243", "788015166", "458718877",
]
J2K = 1.0 / 3.6e6
TOLERANCE = 0.01  # 1.0%


def query_energies(sql_path: Path) -> dict[str, float]:
    conn = sqlite3.connect(f"file:{sql_path}?mode=ro", uri=True)
    def gj(var):
        return conn.execute(
            "SELECT COALESCE(SUM(r.Value),0.0) FROM ReportData r "
            "JOIN ReportDataDictionary d ON r.ReportDataDictionaryIndex=d.ReportDataDictionaryIndex "
            "WHERE d.Name=? AND d.ReportingFrequency='Hourly'",
            (var,)
        ).fetchone()[0]
    h = gj("Zone Ideal Loads Zone Total Heating Energy")
    c = gj("Zone Ideal Loads Zone Total Cooling Energy")
    l = gj("Zone Lights Electricity Energy")
    e = gj("Zone Electric Equipment Electricity Energy")
    conn.close()
    return {"heating_kWh": h * J2K, "cooling_kWh": c * J2K, "total_elec_kWh": (l + e) * J2K}


def parse_end_status(end_path: Path) -> tuple[str, int]:
    """Return (status_str, n_severe) from eplusout.end."""
    if not end_path.exists():
        return "MISSING", -1
    text = end_path.read_text(errors="replace")
    import re
    sev_m = re.search(r"(\d+)\s+Severe", text)
    n_sev = int(sev_m.group(1)) if sev_m else 0
    if "EnergyPlus Completed Successfully" in text:
        return "SUCCESS", n_sev
    return "FAILED", n_sev


def main(cluster_dir: Path):
    print("=== PARITY CHECK: cluster pilot8 vs local R1 ===")
    print(f"Cluster results: {cluster_dir}")
    print(f"R1 reference:    {R1_SIM}")
    print()

    header = f"{'osm_id':<15} {'metric':<18} {'R1':>15} {'cluster':>15} {'delta%':>9} {'pass':>5}"
    print(header)
    print("-" * len(header))

    all_pass = True
    severe_issues = []

    for oid in OSM_IDS:
        r1_sql = R1_SIM / oid / "eplusout.sql"
        cl_sql = cluster_dir / oid / "eplusout.sql"
        cl_end = cluster_dir / oid / "eplusout.end"

        cl_status, cl_sev = parse_end_status(cl_end)
        r1_sev_ref = 16 if oid == "458718877" else 0

        if cl_status != "SUCCESS":
            print(f"{oid:<15} {'[STATUS]':<18} {'':>15} {cl_status:>15} {'N/A':>9} {'FAIL':>5}")
            all_pass = False
            severe_issues.append(f"{oid}: cluster status={cl_status}")
            continue

        if cl_sev != r1_sev_ref:
            severe_issues.append(f"{oid}: severe count cluster={cl_sev} vs R1={r1_sev_ref}")

        if not r1_sql.exists():
            print(f"{oid:<15} {'[R1 SQL MISSING]':<18}")
            all_pass = False
            continue
        if not cl_sql.exists():
            print(f"{oid:<15} {'[cluster SQL MISSING]':<18}")
            all_pass = False
            continue

        r1 = query_energies(r1_sql)
        cl = query_energies(cl_sql)

        for metric in ("heating_kWh", "cooling_kWh", "total_elec_kWh"):
            r1_val = r1[metric]
            cl_val = cl[metric]
            if r1_val != 0:
                delta_pct = abs(cl_val - r1_val) / abs(r1_val) * 100
            else:
                delta_pct = 0.0 if cl_val == 0 else float("inf")
            ok = delta_pct <= TOLERANCE * 100
            if not ok:
                all_pass = False
            print(f"{oid:<15} {metric:<18} {r1_val:>15.2f} {cl_val:>15.2f} {delta_pct:>8.4f}% {'PASS' if ok else 'FAIL':>5}")

    print()
    print(f"=== SEVERE COUNT ISSUES: {len(severe_issues)} ===")
    for s in severe_issues:
        print(f"  {s}")

    print()
    print(f"=== OVERALL: {'ALL PASS' if all_pass else 'SOME FAILED'} ===")
    return 0 if all_pass else 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        cluster_dir = Path(tempfile.gettempdir()) / "ubem_cluster_pilot8" / "results"
    else:
        cluster_dir = Path(sys.argv[1])
    sys.exit(main(cluster_dir))
