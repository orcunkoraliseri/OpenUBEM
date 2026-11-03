"""Extract CBECS 2018 site EUI reference for OpenUBEM validation gates.

OQ-1 resolution per DESIGN §5.1 (line 257) and M-R2-1.

Usage:
    python scripts/extract_cbecs_reference.py
    python scripts/extract_cbecs_reference.py --force   # re-download
    python scripts/extract_cbecs_reference.py --cendiv 2 --region-slug middle_atlantic
"""
from __future__ import annotations

import argparse
import tempfile
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

# ── constants ────────────────────────────────────────────────────────────────

PRIMARY_URL = (
    "https://www.eia.gov/consumption/commercial/data/2018/xls/"
    "cbecs2018_final_public.csv"
)
FALLBACK_PAGE = "https://www.eia.gov/consumption/commercial/data/2018/index.php?view=microdata"

OUT_DIR = Path(__file__).parent.parent / "inputs" / "reports"

# M-R2-1: unit conversion kBtu/ft² → kWh/m²·yr
KBTU_FT2_TO_KWH_M2 = 3.15459

# Default census division: New England (M-R2-1)
NEW_ENGLAND_CENDIV = 1
DEFAULT_REGION_SLUG = "new_england"

# Census division code → human name (for provenance)
CENDIV_NAMES = {
    1: "New England", 2: "Middle Atlantic", 3: "East North Central",
    4: "West North Central", 5: "South Atlantic", 6: "East South Central",
    7: "West South Central", 8: "Mountain", 9: "Pacific",
}

# PBA code labels for provenance
PBA_LABELS = {
    1: "Vacant", 2: "Office", 4: "Laboratory", 5: "Nonrefrigerated warehouse",
    6: "Food sales", 7: "Public order and safety", 8: "Outpatient health care",
    11: "Refrigerated warehouse", 12: "Religious worship", 13: "Public assembly",
    14: "Education", 15: "Food service", 16: "Inpatient health care",
    17: "Nursing", 18: "Lodging", 23: "Strip shopping mall",
    24: "Enclosed mall", 25: "Retail other than mall",
    26: "Service", 91: "Other",
}


# ── helpers ──────────────────────────────────────────────────────────────────

def _download_csv(url: str, dest: Path) -> bool:
    """Download url to dest. Returns True on success."""
    import urllib.request
    try:
        print(f"Downloading {url} …")
        urllib.request.urlretrieve(url, dest)
        return True
    except Exception as exc:
        print(f"  Failed: {exc}")
        return False


def _load_raw(tmp_csv: Path) -> pd.DataFrame:
    return pd.read_csv(tmp_csv, low_memory=False)


def _verify_columns(df: pd.DataFrame) -> None:
    required = {"CENDIV", "PBA", "SQFT", "MFBTU", "FINALWT"}
    missing = required - set(df.columns)
    if missing:
        raise RuntimeError(
            f"STOP: required columns {sorted(missing)} not found in CBECS CSV. "
            f"Available: {sorted(df.columns)[:30]}"
        )


def _extract(df: pd.DataFrame, cendiv: int) -> tuple[pd.DataFrame, dict]:
    """Filter by cendiv, clean, and compute per-building EUI. Returns (result_df, provenance_counts)."""
    n_total = len(df)

    region = df[df["CENDIV"] == cendiv].copy()
    n_region = len(region)

    region["SQFT"] = pd.to_numeric(region["SQFT"], errors="coerce")
    region["MFBTU"] = pd.to_numeric(region["MFBTU"], errors="coerce")
    region["FINALWT"] = pd.to_numeric(region["FINALWT"], errors="coerce")
    region["PBA"] = pd.to_numeric(region["PBA"], errors="coerce")

    bad_sqft = region["SQFT"].isna() | (region["SQFT"] <= 0)
    bad_mfbtu = region["MFBTU"].isna()
    bad_wt = region["FINALWT"].isna()
    dropped = bad_sqft | bad_mfbtu | bad_wt
    n_dropped = int(dropped.sum())

    clean = region[~dropped].copy()
    n_clean = len(clean)

    # M-R2-1: site EUI = MFBTU / SQFT (kBtu/ft²) × 3.15459 → kWh/m²·yr
    clean["eui_kwh_m2"] = (clean["MFBTU"] / clean["SQFT"]) * KBTU_FT2_TO_KWH_M2

    result = clean[["PBA", "SQFT", "eui_kwh_m2", "FINALWT"]].rename(
        columns={"PBA": "pba_code", "SQFT": "sqft", "FINALWT": "finalwt"}
    )
    result["pba_label"] = result["pba_code"].map(PBA_LABELS).fillna("Unknown")
    result = result[["pba_code", "pba_label", "sqft", "eui_kwh_m2", "finalwt"]].reset_index(drop=True)

    wmean = float(
        np.average(result["eui_kwh_m2"].values, weights=result["finalwt"].values)
    )

    counts = {
        "n_total": n_total,
        "n_region": n_region,
        "n_dropped": n_dropped,
        "n_clean": n_clean,
        "weighted_mean_eui_kwh_m2": wmean,
    }
    return result, counts


def _write_provenance(counts: dict, url: str, cendiv: int, region_slug: str, out_prov: Path) -> None:
    div_name = CENDIV_NAMES.get(cendiv, f"CENDIV {cendiv}")
    lines = [
        f"# CBECS 2018 {div_name} EUI — Provenance",
        "",
        f"- **Source URL:** `{url}`",
        f"- **Download date:** {date.today().isoformat()}",
        f"- **Census division filter:** CENDIV == {cendiv} ({div_name})",
        f"- **Unit conversion:** kBtu/ft² × {KBTU_FT2_TO_KWH_M2} → kWh/m²·yr (M-R2-1)",
        "",
        "## Row counts",
        "",
        f"| Stage | Count |",
        f"|---|---|",
        f"| Total rows in national file | {counts['n_total']} |",
        f"| {div_name} rows (CENDIV={cendiv}) | {counts['n_region']} |",
        f"| Dropped (missing/zero SQFT or MFBTU or FINALWT) | {counts['n_dropped']} |",
        f"| Clean rows used | {counts['n_clean']} |",
        "",
        "## Summary statistics",
        "",
        f"- **Weighted mean site EUI ({div_name}):** {counts['weighted_mean_eui_kwh_m2']:.1f} kWh/m²·yr",
        "",
        "## Dropped-row reasons",
        "",
        "- SQFT missing (NaN) or zero",
        "- MFBTU missing (NaN)",
        "- FINALWT missing (NaN)",
        "",
        f"_This file is auto-generated by `scripts/extract_cbecs_reference.py`._",
    ]
    out_prov.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Extract CBECS 2018 regional EUI reference")
    parser.add_argument("--force", action="store_true", help="Re-download even if cached")
    parser.add_argument(
        "--cendiv", type=int, default=NEW_ENGLAND_CENDIV,
        help=f"Census division code (default: {NEW_ENGLAND_CENDIV} = New England)",
    )
    parser.add_argument(
        "--region-slug", type=str, default=DEFAULT_REGION_SLUG,
        help=f"Region slug used in output filenames (default: {DEFAULT_REGION_SLUG})",
    )
    args = parser.parse_args()

    cendiv: int = args.cendiv
    region_slug: str = args.region_slug

    out_csv = OUT_DIR / f"cbecs_2018_{region_slug}_eui.csv"
    out_prov = OUT_DIR / f"cbecs_2018_{region_slug}_PROVENANCE.md"

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Download to temp dir (keep raw CSV out of git)
    tmp_dir = Path(tempfile.gettempdir()) / "cbecs_2018_raw"
    tmp_dir.mkdir(exist_ok=True)
    tmp_csv = tmp_dir / "cbecs2018_final_public.csv"

    if args.force and tmp_csv.exists():
        tmp_csv.unlink()

    used_url = PRIMARY_URL
    if not tmp_csv.exists():
        ok = _download_csv(PRIMARY_URL, tmp_csv)
        if not ok:
            print(f"Primary URL failed. Try the fallback page manually: {FALLBACK_PAGE}")
            raise SystemExit(1)

    print("Loading CSV …")
    df = _load_raw(tmp_csv)
    _verify_columns(df)
    print(f"  Loaded {len(df)} rows, {len(df.columns)} columns.")

    result, counts = _extract(df, cendiv)
    div_name = CENDIV_NAMES.get(cendiv, f"CENDIV {cendiv}")
    print(f"  {div_name} rows (clean): {counts['n_clean']}")
    print(f"  Weighted mean EUI: {counts['weighted_mean_eui_kwh_m2']:.1f} kWh/m²·yr")

    wmean = counts["weighted_mean_eui_kwh_m2"]
    if wmean < 30 or wmean > 1000:
        raise SystemExit(
            f"STOP: weighted mean EUI {wmean:.1f} kWh/m²·yr is wildly implausible "
            f"(expected 30–1000). Check the data."
        )

    result.to_csv(out_csv, index=False)
    _write_provenance(counts, used_url, cendiv, region_slug, out_prov)

    print(f"Written: {out_csv}")
    print(f"Written: {out_prov}")


if __name__ == "__main__":
    main()
