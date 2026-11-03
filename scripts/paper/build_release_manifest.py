from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CMP = ROOT / "openubem" / "outputs" / "comparisons"
EVID = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-11"
EU02 = ROOT / "openubem" / "outputs" / "eu02"
RES = ROOT / "docs" / "docs_ACTIVE" / "europeanLocations" / "results"
FIXED = EVID / "rulebook_2026-09-30" / "partner_fixed_homes_2026-10-08"
PHASE_E = ROOT / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE"
OUT_CSV = CMP / "paper_release_manifest_2026-10-21.csv"

COLUMNS = ["path", "site", "region", "category", "n_files", "bytes", "licence", "licence_source",
           "release", "reason", "conditions", "vintage"]

SITES = {
    "ES-MAD-BERRUGUETE": {"tag": "2026-10-06", "fixed": True, "vintage": "2026-10-08"},
    "FR-LYO-HAUTCOEURPENTES": {"tag": "2026-10-06", "fixed": True, "vintage": "2026-10-08"},
    "IT-BOL-GALVANI2": {"tag": "2026-10-06", "fixed": True, "vintage": "2026-10-08"},
    "CA-MTL-PLATEAU": {"tag": "2026-10-09", "fixed": False, "vintage": "2026-10-09"},
    "AM-EVN-NORNORK": {"tag": "2026-10-09", "fixed": False, "vintage": "2026-10-09"},
    "ZA-CPT-WOODSTOCK": {"tag": "2026-10-09", "fixed": False, "vintage": "2026-10-09"},
    "FI-HEL-KALLIO": {"tag": "2026-10-10", "fixed": False, "vintage": "2026-10-10"},
    "AT-VIE-RUDOLFSHEIM": {"tag": "2026-10-10", "fixed": False, "vintage": "2026-10-10"},
    "HU-BUD-ERZSEBETVAROS": {"tag": "2026-10-10", "fixed": False, "vintage": "2026-10-10"},
}

NO_SITE_REASON = {
    "ZA-CPT-WOODSTOCK": "Cape Town: City of Cape Town footprint use limitation forbids redistribution (plan F13); internal only",
    "AM-EVN-NORNORK": "Armenia: census-derived, Armstat 'All rights reserved' (plan F13)",
}

CONDITIONS = {
    "ES-MAD-BERRUGUETE": "attribute OpenStreetMap contributors; ODbL share-alike on the derived database",
    "FR-LYO-HAUTCOEURPENTES": "attribute IGN - BD TOPO",
    "IT-BOL-GALVANI2": "attribute Comune di Bologna; frozen until the partner reports Bologna done, listed only",
    "CA-MTL-PLATEAU": "attribute Ville de Montreal; Statistics Canada under Open Government Licence - Canada",
    "FI-HEL-KALLIO": "attribute 'Buildings in Helsinki', City of Helsinki",
    "AT-VIE-RUDOLFSHEIM": "attribute 'Datenquelle: Stadt Wien - data.wien.gv.at'",
    "HU-BUD-ERZSEBETVAROS": "attribute OpenStreetMap contributors (ODbL share-alike) and KSH, Census 2011",
}

SKIP_TOP = {"speed_jobs.txt", "changed_stems.txt", "fleet.lst", "fleet_t06s_build.lst", "summary_prerun.json"}
SKIP_DIRS = {"weather", "idfs", "schedules", "layouts"}
US_CITIES = ("nyc", "la", "austin")
US_SUPERSEDED = "superseded vintage (2026-06-27 run, before the 2026-09-30 adoption and the 2026-10-21 hot-water fix)"


def rel(p: Path) -> str:
    return p.resolve().relative_to(ROOT).as_posix()


def read_licence(site: str) -> tuple[str, str]:
    p = EU02 / site / "01_source.json"
    with open(p, encoding="utf-8") as fh:
        lic = str(json.load(fh).get("licence", "")).strip()
    return lic, rel(p)


def dir_stats(d: Path) -> tuple[int, int]:
    n = 0
    b = 0
    for dirpath, _dirs, files in os.walk(d):
        for f in files:
            n += 1
            b += os.path.getsize(os.path.join(dirpath, f))
    return n, b


def category_of_top(name: str) -> str:
    if name.endswith("_manifest.csv"):
        return "result_per_building"
    if name in ("prepared_buildings.csv", "sidecar_population.csv"):
        return "provenance"
    if name == "summary.json":
        return "result_summary"
    return "support_table"


def decide(site: str, licence: str, mixed: bool = False) -> tuple[str, str, str]:
    if site in NO_SITE_REASON:
        return "no", NO_SITE_REASON[site], ""
    if not licence:
        return "no", "licence not found in any sidecar", ""
    if mixed:
        return "no", "file mixes several districts and one of them is outside this release; split by district first", ""
    return "yes", "licence permits redistribution with the conditions stated", CONDITIONS.get(site, "")


def row(path: Path, site: str, region: str, category: str, licence: str, lic_src: str, vintage: str,
        n_files: int | None = None, nbytes: int | None = None, mixed: bool = False) -> dict:
    if n_files is None:
        n_files = 1
        nbytes = path.stat().st_size
    release, reason, cond = decide(site, licence, mixed)
    return {"path": rel(path), "site": site, "region": region, "category": category, "n_files": n_files,
            "bytes": nbytes, "licence": licence, "licence_source": lic_src, "release": release,
            "reason": reason, "conditions": cond, "vintage": vintage}


def add_idfs_and_schedules(rows: list, root: Path, site: str, region: str, lic: str, lic_src: str, vintage: str):
    idfs = root / "idfs"
    if idfs.is_dir():
        for f in sorted(idfs.glob("*.idf")):
            rows.append(row(f, site, region, "idf", lic, lic_src, vintage))
    sch = root / "schedules"
    if sch.is_dir():
        for d in sorted(p for p in sch.iterdir() if p.is_dir()):
            n, b = dir_stats(d)
            rows.append(row(d, site, region, "schedule_dir", lic, lic_src, vintage, n_files=n, nbytes=b))
    lay = root / "layouts"
    if lay.is_dir():
        for f in sorted(lay.rglob("*")):
            if f.is_file():
                rows.append(row(f, site, region, "layout", lic, lic_src, vintage))


def site_rows(site: str, cfg: dict) -> list[dict]:
    rows: list[dict] = []
    lic, lic_src = read_licence(site)
    vintage = cfg["vintage"]
    region = "EU-international"
    rows.append(row(EU02 / site / "01_source.json", site, region, "provenance", lic, lic_src, vintage))
    for kind in ("win", "merged_win"):
        tree = EVID / f"{site}_{kind}_{cfg['tag']}"
        if not tree.is_dir():
            continue
        for f in sorted(tree.iterdir()):
            if f.is_file() and f.name not in SKIP_TOP and f.suffix in (".csv", ".json", ".txt"):
                rows.append(row(f, site, region, category_of_top(f.name), lic, lic_src, vintage))
        if kind == "win":
            add_idfs_and_schedules(rows, tree, site, region, lic, lic_src, vintage)
    if cfg["fixed"]:
        fx = FIXED / site
        if fx.is_dir():
            add_idfs_and_schedules(rows, fx, site, region, lic, lic_src, "2026-10-08")
    if not cfg["fixed"]:
        for f in sorted(RES.glob(f"EU22_results_{site}_*")):
            if f.suffix in (".csv", ".json"):
                cat = "result_per_building" if "per_home" in f.name else "result_summary"
                rows.append(row(f, site, region, cat, lic, lic_src, vintage))
    return rows


def eu11_result_rows() -> list[dict]:
    lics = []
    for s in ("ES-MAD-BERRUGUETE", "FR-LYO-HAUTCOEURPENTES", "IT-BOL-GALVANI2"):
        lics.append(read_licence(s))
    lic = " | ".join(x[0] for x in lics)
    src = " ; ".join(x[1] for x in lics)
    rows = []
    for f in sorted(RES.glob("EU11_results_2026-10-08_*")):
        if f.suffix in (".csv", ".json"):
            cat = "result_per_building" if "per_home" in f.name else "result_summary"
            rows.append(row(f, "EU11-four-district-set", "EU-international", cat, lic, src, "2026-10-08", mixed=True))
    return rows


def us_rows() -> list[dict]:
    rows: list[dict] = []
    lic = "NOT_FOUND_IN_SIDECARS"
    src = "none"
    region = "US"
    site = "US-NYC-LA-AUSTIN"
    adopted = CMP / "paper_adopted_fleet_dhw-fix_per_building_2026-10-21.csv"
    first = CMP / "paper_adopted_fleet_per_building_2026-10-21.csv"
    for f, cat, note in ((adopted, "result_per_building", None),
                         (first, "result_per_building", "superseded by the hot-water-corrected table (2026-10-21)")):
        if f.exists():
            r = row(f, site, region, cat, lic, src, "2026-10-21")
            r["release"] = "no"
            r["reason"] = "licence not found in any sidecar" + (f"; {note}" if note else "")
            rows.append(r)
    for city in US_CITIES:
        for dens in ("centre", "urban", "suburban", "rural"):
            cell = f"{city}_{dens}"
            d = PHASE_E / cell
            for name, cat in (("01_buildings.gpkg", "provenance"), (f"{cell}_step3_idfs_archive.zip", "idf")):
                f = d / name
                if f.exists():
                    r = row(f, cell, region, cat, lic, src, "2026-06-27")
                    r["release"] = "no"
                    r["reason"] = f"licence not found in any sidecar; {US_SUPERSEDED}"
                    rows.append(r)
    return rows


def build() -> pd.DataFrame:
    rows: list[dict] = []
    for site, cfg in SITES.items():
        rows.extend(site_rows(site, cfg))
    rows.extend(eu11_result_rows())
    rows.extend(us_rows())
    return pd.DataFrame(rows, columns=COLUMNS)


def checks(df: pd.DataFrame) -> dict:
    cape = df["path"].str.contains("ZA-CPT", case=False) | df["site"].str.contains("ZA-CPT", case=False)
    arm = df["path"].str.contains("AM-EVN", case=False) | df["site"].str.contains("AM-EVN", case=False)
    empty = df["licence"].isna() | (df["licence"].astype(str).str.strip() == "")
    return {
        "rows": int(len(df)),
        "yes": int((df["release"] == "yes").sum()),
        "no": int((df["release"] == "no").sum()),
        "cape_town_rows": int(cape.sum()),
        "cape_town_yes": int((cape & (df["release"] == "yes")).sum()),
        "armenia_rows": int(arm.sum()),
        "armenia_yes": int((arm & (df["release"] == "yes")).sum()),
        "empty_licence": int(empty.sum()),
        "restricted_path_rows": int(df["path"].str.contains("resources/UK", case=False).sum()),
    }


def main() -> None:
    df = build()
    df.to_csv(OUT_CSV, index=False)
    print(json.dumps(checks(df)))
    print(df.groupby(["licence", "release"]).size().to_string())


if __name__ == "__main__":
    main()
