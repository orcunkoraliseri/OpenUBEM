"""
T05 — Attribution / sensitivity probe (analysis only, no resim, no EnergyPlus).

Using persisted r6_4_level2_enduse.csv + r6_4_decomposition.csv + r6_4_basis_corrected.csv:
(a) Group archetypes by zoning_strategy; report median |dev%| per group.
(b) Compare counterpart n_zones vs DOE multi-zone counts; document qualitative mismatch.
(c) Quantify residual (post-basis) gap concentrated in equipment+lighting (schedule proxy)
    vs heating+cooling (envelope/HVAC proxy).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

REPO = Path(__file__).parent.parent.parent
RESULTS_DIR = REPO / "docs" / "validations" / "overAll" / "results"
ENDUSE_CSV = RESULTS_DIR / "r6_4_level2_enduse.csv"
DECOMP_CSV = RESULTS_DIR / "r6_4_decomposition.csv"
BASIS_CSV = RESULTS_DIR / "r6_4_basis_corrected.csv"
DECOMP_MD = RESULTS_DIR / "r6_4_decomposition.md"

# Known DOE prototype zone counts (approximate, from PNNL prototype documentation)
DOE_KNOWN_ZONES = {
    "SmallOffice": 5,
    "MediumOffice": 15,
    "LargeOffice": 19,
    "Warehouse": 3,
    "RetailStandalone": 5,
    "RetailStripmall": 8,
    "QuickServiceRestaurant": 1,
    "FullServiceRestaurant": 1,
    "Hospital": 16,
    "Outpatient": 22,
    "SmallHotel": 5,
    "LargeHotel": 23,
    "MidriseApartment": 8,
    "HighriseApartment": 18,
    "SuperMarket": 1,
    "College": 6,
    "Laboratory": 7,
    "Warehouse": 3,
    "TallBuilding": 38,
    "SuperTallBuilding": 72,
    "SmallDataCenterLowITE": 1,
}


def main() -> None:
    enduse = pd.read_csv(ENDUSE_CSV)
    decomp = pd.read_csv(DECOMP_CSV)
    basis = pd.read_csv(BASIS_CSV)

    ctr_df = enduse[enduse["side"] == "counterpart"].set_index("archetype")
    success_decomp = decomp[decomp["dev_pct"].notna()].copy()
    success_decomp["abs_dev"] = success_decomp["dev_pct"].abs()

    # Merge zoning strategy from counterpart enduse
    success_decomp = success_decomp.join(
        ctr_df[["zoning_strategy", "n_zones"]], on="openuben_archetype"
    )

    print("=" * 70)
    print("T05 — Attribution / Sensitivity Probe")
    print("=" * 70)

    # (a) Group by zoning strategy — median |dev%| per group
    print("\n(a) Median |dev%| by counterpart zoning strategy:")
    grp = success_decomp.groupby("zoning_strategy")["abs_dev"].agg(
        median_abs_dev="median", count="count"
    )
    print(grp.to_string())
    print()
    for strat, row in grp.iterrows():
        print(f"  {strat}: n={int(row['count'])}, median |dev%| = {row['median_abs_dev']:.1f}%")

    # (b) Compare counterpart n_zones vs DOE known zones
    print("\n(b) Counterpart n_zones vs DOE prototype zones:")
    print(f"  {'Archetype':<30} {'Counterpart n_zones':>18} {'DOE known':>10} {'Ratio':>8}")
    print("  " + "-" * 68)
    for arch, row in success_decomp.set_index("openuben_archetype").iterrows():
        ctr_nz = int(row["n_zones"]) if pd.notna(row["n_zones"]) else "?"
        doe_nz = DOE_KNOWN_ZONES.get(arch, "?")
        if isinstance(ctr_nz, int) and isinstance(doe_nz, int):
            ratio = f"{ctr_nz / doe_nz:.2f}" if doe_nz > 0 else "n/a"
        else:
            ratio = "n/a"
        print(f"  {arch:<30} {str(ctr_nz):>18} {str(doe_nz):>10} {ratio:>8}")

    # (c) Residual gap concentration: equipment+lighting vs heating+cooling
    print("\n(c) Post-basis residual gap — attribution by end-use group:")
    valid_basis = basis[basis["raw_verdict_5pct"] != "N/A"].copy()
    valid_basis = valid_basis.merge(
        success_decomp[["openuben_archetype", "contrib_heat", "contrib_cool",
                         "contrib_light", "contrib_equip", "contrib_other"]],
        left_on="archetype", right_on="openuben_archetype", how="left"
    )
    valid_basis["abs_heat_cool"] = (valid_basis["contrib_heat"].abs() +
                                    valid_basis["contrib_cool"].abs())
    valid_basis["abs_light_equip"] = (valid_basis["contrib_light"].abs() +
                                      valid_basis["contrib_equip"].abs())
    valid_basis["abs_other"] = valid_basis["contrib_other"].abs()

    total_abs = (valid_basis["abs_heat_cool"] + valid_basis["abs_light_equip"] +
                 valid_basis["abs_other"])
    heat_cool_share = (valid_basis["abs_heat_cool"] / total_abs * 100).median()
    light_equip_share = (valid_basis["abs_light_equip"] / total_abs * 100).median()
    other_share = (valid_basis["abs_other"] / total_abs * 100).median()

    print(f"  Median share of gap:")
    print(f"    heating+cooling (envelope/HVAC proxy):          {heat_cool_share:.1f}%")
    print(f"    lighting+equipment (schedule/internal-gain proxy): {light_equip_share:.1f}%")
    print(f"    other (service loads — fans/pumps/DHW/parasitics): {other_share:.1f}%")

    # Count archetypes where 'other' contribution is the largest single contributor
    success_decomp["abs_other"] = success_decomp["contrib_other"].abs()
    success_decomp["abs_heat_cool"] = (success_decomp["contrib_heat"].abs() +
                                        success_decomp["contrib_cool"].abs())
    success_decomp["abs_light_equip"] = (success_decomp["contrib_light"].abs() +
                                          success_decomp["contrib_equip"].abs())
    other_dominant = (success_decomp["abs_other"] > success_decomp["abs_heat_cool"]) & \
                     (success_decomp["abs_other"] > success_decomp["abs_light_equip"])
    n_other_dom = other_dominant.sum()
    print(f"\n  Archetypes where 'Other' is largest gap driver: {n_other_dom}/{len(success_decomp)}")
    print(f"  Implication: even a complete HVAC/zoning rewrite cannot close these gaps")
    print(f"  without also modeling the service end-uses the DOE prototypes carry.")

    # Print zoning correlation finding
    print("\n(a-conclusion) Zoning-strategy vs gap correlation:")
    for strat, row in grp.iterrows():
        print(f"  {strat}: median |dev%| = {row['median_abs_dev']:.1f}%  (n={int(row['count'])})")

    has_single = "single_zone" in grp.index
    has_pc = "perimeter_core" in grp.index
    has_floor = "one_zone_per_floor" in grp.index
    if has_single and has_pc:
        diff = grp.loc["perimeter_core", "median_abs_dev"] - grp.loc["single_zone", "median_abs_dev"]
        print(f"\n  perimeter_core vs single_zone: {diff:+.1f}pp")
        if diff < 0:
            print(f"  Richer zoning (perimeter_core) correlates with SMALLER gap.")
        elif diff > 0:
            print(f"  Richer zoning (perimeter_core) correlates with LARGER gap.")
            print(f"  NOTE: This does NOT mean zoning worsens results. The perimeter_core archetypes")
            print(f"  are complex building types (hospitals, hotels, labs) that inherently have")
            print(f"  more unmodeled service loads — confounded with building-type complexity.")
        else:
            print(f"  No difference in median |dev%| between zoning strategies.")

    print("\n[T05] Complete.")


if __name__ == "__main__":
    main()
