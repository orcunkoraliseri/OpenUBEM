"""CLI: run service-loads reconstruction across all 12 validation cells.

Usage:
    py -3 scripts/reconstruct_service_loads.py [--cells nyc_centre la_urban ...]
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from openubem.results.service_loads import reconstruct_cell, load_coefficients

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

_ALL_CELLS = [
    "nyc_centre", "nyc_urban", "nyc_suburban", "nyc_rural",
    "la_centre",  "la_urban",  "la_suburban",  "la_rural",
    "austin_centre", "austin_urban", "austin_suburban", "austin_rural",
]

_OUT_PATH = _ROOT / "docs" / "validations" / "overAll" / "results" / "r7_service_loads.csv"
_ROUNDTRIP_IN  = _ROOT / "docs" / "validations" / "overAll" / "results" / "roundtrip_report.csv"
_ROUNDTRIP_OUT = _ROOT / "docs" / "validations" / "overAll" / "results" / "r7_roundtrip_recon.csv"


def roundtrip_reeval() -> None:
    """Building-fixed round-trip re-evaluation (T12 correction).

    For each success row (not DataCenter) in roundtrip_report.csv:
        dev_simulated     = original dev_pct (counter vs ref)
        modeled_frac      = f_heat+f_cool+f_light+f_equip for the mapped archetype
        recon_total       = counter_total_eui / modeled_frac   (if mapped)
        dev_reconstructed = (recon_total - ref_total_eui) / ref_total_eui * 100
    Genuinely unmapped (not in archetype_map): recon_total = counter_total_eui (dev unchanged).
    """
    import pandas as pd

    df = pd.read_csv(_ROUNDTRIP_IN)
    coeffs = load_coefficients()
    amap = coeffs["archetype_map"]
    fracs = coeffs["fractions"]

    _FOOD = {"FullServiceRestaurant", "QuickServiceRestaurant"}
    _DATA_CENTER_SUBSTR = "DataCenter"

    rows_out = []
    for _, row in df.iterrows():
        arch = str(row["openuben_archetype"])
        status = str(row["counter_status"])
        if _DATA_CENTER_SUBSTR in arch:
            continue
        if status != "success":
            continue

        ref_total = float(row["ref_total_eui"])
        counter_total = float(row["counter_total_eui"])
        dev_sim = float(row["dev_pct"])  # (counter-ref)/ref*100

        mapped_to = amap.get(arch)
        apply_recon = mapped_to is not None and mapped_to != "passthrough"
        if apply_recon:
            f = fracs[mapped_to]
            modeled_frac = f["space_heat"] + f["space_cool"] + f["lighting"] + f["equip_plug"]
            recon_total = counter_total / modeled_frac
        else:
            recon_total = counter_total  # genuinely unmapped

        dev_recon = (recon_total - ref_total) / ref_total * 100

        rows_out.append({
            "archetype": arch,
            "mapped_to": mapped_to if apply_recon else "passthrough",
            "dev_simulated": dev_sim,
            "dev_reconstructed": dev_recon,
        })

    out_df = pd.DataFrame(rows_out)
    out_df.to_csv(_ROUNDTRIP_OUT, index=False)
    logger.info("Wrote %d rows to %s", len(out_df), _ROUNDTRIP_OUT)

    # Median |dev| -- all archetypes and excluding food-service
    all_abs_sim   = out_df["dev_simulated"].abs()
    all_abs_recon = out_df["dev_reconstructed"].abs()
    nofood = out_df[~out_df["archetype"].isin(_FOOD)]
    nf_abs_sim   = nofood["dev_simulated"].abs()
    nf_abs_recon = nofood["dev_reconstructed"].abs()

    print("\nRound-trip re-evaluation (building-fixed, T12):")
    print(f"  All archetypes (n={len(out_df)}):         median|dev_sim|={all_abs_sim.median():.1f}%  "
          f"median|dev_recon|={all_abs_recon.median():.1f}%")
    print(f"  Excl. food-service (n={len(nofood)}):  median|dev_sim|={nf_abs_sim.median():.1f}%  "
          f"median|dev_recon|={nf_abs_recon.median():.1f}%")

    print("\nPer-archetype dev_simulated vs dev_reconstructed:")
    for _, r in out_df.sort_values("archetype").iterrows():
        print(f"  {r['archetype']:<30} dev_sim={r['dev_simulated']:+.1f}%  "
              f"dev_recon={r['dev_reconstructed']:+.1f}%  mapped_to={r['mapped_to']}")


def main(cells: list[str] | None = None) -> None:
    cells = cells or _ALL_CELLS
    frames = []
    for cell in cells:
        try:
            df = reconstruct_cell(cell)
            frames.append(df)
            logger.info("Loaded %s: %d rows", cell, len(df))
        except FileNotFoundError as exc:
            logger.warning("Skipping %s: %s", cell, exc)

    if not frames:
        logger.error("No cells produced data; nothing written.")
        return

    import pandas as pd
    combined = pd.concat(frames, ignore_index=True)
    _OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(_OUT_PATH, index=False)
    logger.info("Wrote %d rows to %s", len(combined), _OUT_PATH)

    _FOOD_SERVICE_IDS = {"FullServiceRestaurant", "QuickServiceRestaurant"}
    _BAND_UPPER = 1000.0  # R5 plausibility-band upper bound (kWh/m2/yr)

    print("\nPer-cell summary:")
    hdr = (f"{'Cell':<22} {'n_success':>9} {'mean_sim_total':>14} "
           f"{'mean_recon_total':>16} {'mean_%_uplift':>13} {'n_food_svc':>10} {'n_>1000':>7}")
    print(hdr)
    for cell, grp in combined.groupby("cell"):
        success = grp[grp["reconstruction_applied"] == True]
        n_food = len(grp[grp["archetype_id"].isin(_FOOD_SERVICE_IDS)])
        n_over = int((grp["total_eui_reconstructed_kwh_m2"] > _BAND_UPPER).sum())
        if len(success) == 0:
            print(f"{cell:<22} {'0':>9} {'--':>14} {'--':>16} {'--':>13} {n_food:>10} {n_over:>7}")
            continue
        mean_sim = success["total_eui_kwh_m2"].mean()
        mean_recon = success["total_eui_reconstructed_kwh_m2"].mean()
        pct_uplift = (mean_recon - mean_sim) / mean_sim * 100 if mean_sim > 0 else float("nan")
        print(f"{cell:<22} {len(success):>9} {mean_sim:>14.2f} {mean_recon:>16.2f} "
              f"{pct_uplift:>12.1f}% {n_food:>10} {n_over:>7}")

    # Food-service archetypes aggregate line
    fs_rows = combined[combined["archetype_id"].isin(_FOOD_SERVICE_IDS)]
    fs_recon = fs_rows[fs_rows["reconstruction_applied"] == True]
    if len(fs_recon) > 0:
        fs_sim = fs_recon["total_eui_kwh_m2"].mean()
        fs_mean_recon = fs_recon["total_eui_reconstructed_kwh_m2"].mean()
        fs_uplift = (fs_mean_recon - fs_sim) / fs_sim * 100 if fs_sim > 0 else float("nan")
        fs_over = int((fs_rows["total_eui_reconstructed_kwh_m2"] > _BAND_UPPER).sum())
        print(f"\n{'[ALL food-service]':<22} {len(fs_recon):>9} {fs_sim:>14.2f} {fs_mean_recon:>16.2f} "
              f"{fs_uplift:>12.1f}% {len(fs_recon):>10} {fs_over:>7}")
        print("  (FullServiceRestaurant + QuickServiceRestaurant combined across all cells)")

    total_over = int((combined["total_eui_reconstructed_kwh_m2"] > _BAND_UPPER).sum())
    print(f"\nTotal rows with reconstructed total > {_BAND_UPPER:.0f} kWh/m2/yr: {total_over} "
          f"(reported only, NOT clipped)")

    # Passthrough audit among success rows
    passthrough_among_success = combined[
        (combined["simulation_status"].str.startswith("success")) &
        (combined["reconstruction_applied"] == False)
    ]
    print(f"\nPassthrough among success rows: {len(passthrough_among_success)} "
          f"(expect 0 after T12 map corrections)")

    # Round-trip building-fixed re-evaluation
    if _ROUNDTRIP_IN.exists():
        roundtrip_reeval()
    else:
        logger.warning("roundtrip_report.csv not found; skipping T09 re-evaluation.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reconstruct service loads across validation cells.")
    parser.add_argument("--cells", nargs="+", metavar="CELL", help="Subset of cells to process.")
    args = parser.parse_args()
    main(args.cells)
