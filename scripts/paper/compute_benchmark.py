from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CMP = ROOT / "openubem" / "outputs" / "comparisons"
EVID = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-11"
SACCT_RAW = ROOT / "docs" / "docs_DONE" / "openings" / "extra" / "r05_sacct_raw.txt"
OUT_CSV = CMP / "paper_compute_benchmark_2026-10-21.csv"

SACCT_COLS = ["jobid", "jobname", "state", "submit", "start", "end", "elapsed", "totalcpu", "maxrss", "reqmem", "exit"]
MODES = ["auto", "building", "floor", "layout_assign", "fast_zone"]
EU_MANIFESTS = {
    "ES-MAD-BERRUGUETE": "ES-MAD-BERRUGUETE_merged_win_2026-10-06/es_mad_berruguete_manifest.csv",
    "FR-LYO-HAUTCOEURPENTES": "FR-LYO-HAUTCOEURPENTES_merged_win_2026-10-06/fr_lyo_hautcoeurpentes_manifest.csv",
    "GB-LDN-STDUNSTANS": "GB-LDN-STDUNSTANS_merged_win_2026-10-06/gb_ldn_stdunstans_manifest.csv",
    "IT-BOL-GALVANI2": "IT-BOL-GALVANI2_merged_win_2026-10-06/it_bol_galvani2_manifest.csv",
    "CA-MTL-PLATEAU": "CA-MTL-PLATEAU_win_2026-10-09/ca_mtl_plateau_manifest.csv",
    "AM-EVN-NORNORK": "AM-EVN-NORNORK_win_2026-10-09/am_evn_nornork_manifest.csv",
    "ZA-CPT-WOODSTOCK": "ZA-CPT-WOODSTOCK_win_2026-10-09/za_cpt_woodstock_manifest.csv",
    "FI-HEL-KALLIO": "FI-HEL-KALLIO_win_2026-10-10/fi_hel_kallio_manifest.csv",
    "AT-VIE-RUDOLFSHEIM": "AT-VIE-RUDOLFSHEIM_win_2026-10-10/at_vie_rudolfsheim_manifest.csv",
    "HU-BUD-ERZSEBETVAROS": "HU-BUD-ERZSEBETVAROS_win_2026-10-10/hu_bud_erzsebetvaros_manifest.csv",
}
COLUMNS = ["source", "scope", "cell_or_site", "mode", "n_cases", "n_completed", "n_failed", "n_with_wall",
           "wall_mean_s", "wall_median_s", "cpu_mean_core_s", "cpu_median_core_s", "maxrss_max_mb",
           "note", "vintage"]


def parse_duration(text) -> float:
    if text is None or (isinstance(text, float) and np.isnan(text)) or str(text).strip() == "":
        return float("nan")
    s = str(text).strip()
    days = 0.0
    if "-" in s:
        d, s = s.split("-", 1)
        days = float(d)
    parts = s.split(":")
    secs = 0.0
    for p in parts:
        secs = secs * 60 + float(p)
    if len(parts) == 2:
        pass
    return days * 86400 + secs


def parse_rss_mb(text) -> float:
    if text is None or (isinstance(text, float) and np.isnan(text)) or str(text).strip() == "":
        return float("nan")
    m = re.fullmatch(r"([0-9.]+)([KMGT]?)", str(text).strip())
    if not m:
        return float("nan")
    scale = {"": 1 / 1024 / 1024, "K": 1 / 1024, "M": 1.0, "G": 1024.0, "T": 1024.0 * 1024}[m.group(2)]
    return float(m.group(1)) * scale


def read_sacct(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep="|", header=None, names=SACCT_COLS, dtype=str, keep_default_na=False)
    main = df[~df["jobid"].str.contains(r"\.", regex=True)].copy()
    batch = df[df["jobid"].str.endswith(".batch")].copy()
    batch["jobid"] = batch["jobid"].str.replace(".batch", "", regex=False)
    main = main.set_index("jobid")
    batch = batch.set_index("jobid")
    out = pd.DataFrame(index=main.index)
    out["jobname"] = main["jobname"]
    out["state"] = main["state"]
    out["wall_s"] = main["elapsed"].map(parse_duration)
    cpu = batch["totalcpu"].map(parse_duration).reindex(out.index)
    out["cpu_s"] = cpu.fillna(main["totalcpu"].map(parse_duration))
    out["maxrss_mb"] = batch["maxrss"].map(parse_rss_mb).reindex(out.index)
    m = out["jobname"].str.extract(r"^r05probe_(?P<cell>.+)_(?P<mode>auto|building|floor|layout_assign|fast_zone)$")
    out["cell"] = m["cell"]
    out["mode"] = m["mode"]
    return out.reset_index()


def sacct_rows(df: pd.DataFrame) -> list[dict]:
    rows = []
    groups = [(c, m, g) for (c, m), g in df.groupby(["cell", "mode"])]
    groups += [("ALL", m, df[df["mode"] == m]) for m in MODES]
    for cell, mode, g in groups:
        rows.append(dict(
            source="r05_sacct_raw.txt (sacct -P -n, 10 arrays)", scope="united_states_rural_probe",
            cell_or_site=cell, mode=mode, n_cases=len(g), n_completed=int((g["state"] == "COMPLETED").sum()),
            n_failed=int((g["state"] != "COMPLETED").sum()), n_with_wall=int(g["wall_s"].notna().sum()),
            wall_mean_s=round(g["wall_s"].mean(), 3), wall_median_s=round(g["wall_s"].median(), 3),
            cpu_mean_core_s=round(g["cpu_s"].mean(), 3), cpu_median_core_s=round(g["cpu_s"].median(), 3),
            maxrss_max_mb=round(g["maxrss_mb"].max(), 1),
            note="per array task, one task = one building; statistics over all tasks incl. failed; ReqMem 6G; MaxRSS max is the reliable ceiling, the median is a sampler artifact and is not reported",
            vintage="2026-08-09"))
    return rows


def eu_rows() -> list[dict]:
    rows = []
    for site, rel in EU_MANIFESTS.items():
        x = pd.read_csv(EVID / rel, usecols=["run_seconds"])
        rs = x["run_seconds"]
        rows.append(dict(
            source=f"{rel} (harvest manifest run_seconds)", scope="international_dwelling_zoning",
            cell_or_site=site, mode="dwelling_zoning", n_cases=len(x), n_completed=None, n_failed=None,
            n_with_wall=int(rs.notna().sum()),
            wall_mean_s=round(rs.mean(), 3) if rs.notna().any() else None,
            wall_median_s=round(rs.median(), 3) if rs.notna().any() else None,
            cpu_mean_core_s=None, cpu_median_core_s=None, maxrss_max_mb=None,
            note="cpu and memory not recorded; wall-clock only where run_seconds was kept (merged manifests mix harvests)",
            vintage=""))
    return rows


def main() -> None:
    df = read_sacct(SACCT_RAW)
    rows = sacct_rows(df) + eu_rows()
    out = pd.DataFrame(rows)[COLUMNS]
    out.to_csv(OUT_CSV, index=False)
    print("sacct tasks", len(df), "modes", df["mode"].value_counts().to_dict())
    a = out[(out["cell_or_site"] == "ALL")]
    print(a[["mode", "n_cases", "n_completed", "n_failed", "wall_mean_s", "cpu_mean_core_s", "maxrss_max_mb"] ].to_string(index=False))
    print("rows", len(out))


if __name__ == "__main__":
    main()
