"""Extract CBECS 2018 New England site EUI reference for OpenUBEM validation gates.

OQ-1 resolution per DESIGN §5.1 (line 257) and M-R2-1.

Usage:
    python scripts/extract_cbecs_reference.py
    python scripts/extract_cbecs_reference.py --force   # re-download
"""
from __future__ import annotations

import argparse
import os
import shutil
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
OUT_CSV = OUT_DIR / "cbecs_2018_new_england_eui.csv"
OUT_PROV = OUT_DIR / "cbecs_2018_new_england_PROVENANCE.md"

# M-R2-1: unit conversion kBtu/ft² → kWh/m²·yr
KBTU_FT2_TO_KWH_M2 = 3.15459

# New England census division code (M-R2-1)
NEW_ENGLAND_CENDIV = 1

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


def _extract(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Filter, clean, and compute per-building EUI. Returns (result_df, provenance_counts)."""
    n_total = len(df)

    # Filter New England
    ne = df[df["CENDIV"] == NEW_ENGLAND_CENDIV].copy()
    n_ne = len(ne)

    # Drop rows with missing/zero SQFT or MFBTU
    ne["SQFT"] = pd.to_numeric(ne["SQFT"], errors="coerce")
    ne["MFBTU"] = pd.to_numeric(ne["MFBTU"], errors="coerce")
    ne["FINALWT"] = pd.to_numeric(ne["FINALWT"], errors="coerce")
    ne["PBA"] = pd.to_numeric(ne["PBA"], errors="coerce")

    bad_sqft = ne["SQFT"].isna() | (ne["SQFT"] <= 0)
    bad_mfbtu = ne["MFBTU"].isna()
    bad_wt = ne["FINALWT"].isna()
    dropped = bad_sqft | bad_mfbtu | bad_wt
    n_dropped = int(dropped.sum())

    clean = ne[~dropped].copy()
    n_clean = len(clean)

    # M-R2-1: site EUI = MFBTU / SQFT (kBtu/ft²) × 3.15459 → kWh/m²·yr
    clean["eui_kwh_m2"] = (clean["MFBTU"] / clean["SQFT"]) * KBTU_FT2_TO_KWH_M2

    result = clean[["PBA", "SQFT", "eui_kwh_m2", "FINALWT"]].rename(
        columns={"PBA": "pba_code", "SQFT": "sqft", "FINALWT": "finalwt"}
    )
    result["pba_label"] = result["pba_code"].map(PBA_LABELS).fillna("Unknown")
    result = result[["pba_code", "pba_label", "sqft", "eui_kwh_m2", "finalwt"]].reset_index(drop=True)

    # Weighted mean EUI
    wmean = float(
        np.average(result["eui_kwh_m2"].values, weights=result["finalwt"].values)
    )

    counts = {
        "n_total": n_total,
        "n_new_england": n_ne,
        "n_dropped": n_dropped,
        "n_clean": n_clean,
        "weighted_mean_eui_kwh_m2": wmean,
    }
    return result, counts


def _write_provenance(counts: dict, url: str) -> None:
    lines = [
        "# CBECS 2018 New England EUI — Provenance",
        "",
        f"- **Source URL:** `{url}`",
        f"- **Download date:** {date.today().isoformat()}",
        f"- **Census division filter:** CENDIV == {NEW_ENGLAND_CENDIV} (New England)",
        f"- **Unit conversion:** kBtu/ft² × {KBTU_FT2_TO_KWH_M2} → kWh/m²·yr (M-R2-1)",
        "",
        "## Row counts",
        "",
        f"| Stage | Count |",
        f"|---|---|",
        f"| Total rows in national file | {counts['n_total']} |",
        f"| New England rows (CENDIV=1) | {counts['n_new_england']} |",
        f"| Dropped (missing/zero SQFT or MFBTU or FINALWT) | {counts['n_dropped']} |",
        f"| Clean rows used | {counts['n_clean']} |",
        "",
        "## Summary statistics",
        "",
        f"- **Weighted mean site EUI (New England):** {counts['weighted_mean_eui_kwh_m2']:.1f} kWh/m²·yr",
        "",
        "## Dropped-row reasons",
        "",
        "- SQFT missing (NaN) or zero",
        "- MFBTU missing (NaN)",
        "- FINALWT missing (NaN)",
        "",
        "_This file is auto-generated by `scripts/extract_cbecs_reference.py`._",
    ]
    OUT_PROV.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Extract CBECS 2018 New England EUI reference")
    parser.add_argument("--force", action="store_true", help="Re-download even if cached")
    args = parser.parse_args()

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

    result, counts = _extract(df)
    print(f"  New England rows (clean): {counts['n_clean']}")
    print(f"  Weighted mean EUI: {counts['weighted_mean_eui_kwh_m2']:.1f} kWh/m²·yr")

    wmean = counts["weighted_mean_eui_kwh_m2"]
    if wmean < 30 or wmean > 1000:
        raise SystemExit(
            f"STOP: weighted mean EUI {wmean:.1f} kWh/m²·yr is wildly implausible "
            f"(expected 30–1000). Check the data."
        )

    result.to_csv(OUT_CSV, index=False)
    _write_provenance(counts, used_url)

    print(f"Written: {OUT_CSV}")
    print(f"Written: {OUT_PROV}")


if __name__ == "__main__":
    main()
