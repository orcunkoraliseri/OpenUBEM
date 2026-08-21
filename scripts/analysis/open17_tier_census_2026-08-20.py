"""OPEN-17 T09(a) -- tier census over run 4's persisted fleet inputs.

Reads run 4's `<cell>/01_buildings.gpkg` (D1: `C:\\Users\\o_iseri\\AppData\\Local\\
Temp\\ubem_validation\\open48_refleet4`, 12 cells) and tabulates every token found
in its `provenance_*` columns plus `data_quality_flag`, mapped against the
project's known imputation-provenance vocabulary:

  * T07 tier tokens (`openubem/semantic/imputation.py`, `_TIER_HANDLER_NAMES`):
    fusion -> `FUSED_*`, spatial -> `HOTDECK_NEIGHBOR_HIGH`/`_MED`,
    statistical -> `GROUPMODE_MED`, ml -> `ML_<METHOD>_HIGH`/`_MED`,
    draw -> `DRAW_<METHOD>_HIGH`/`_MED` (`openubem/semantic/draw_methods.py:42-53`).
  * The production year_built-only 3-tier system
    (`openubem/semantic/construction_sets.py:resolve_vintage`), which reuses the
    `HOTDECK_NEIGHBOR_HIGH`/`_MED` and `GROUPMODE_MED` token spellings for tier 1/2
    and a legacy default `VINTAGE_NAN_PERMISSIVE_DEFAULT` for tier 3.
  * Legacy `CANONICAL_PROVENANCE` tokens (`openubem/semantic/provenance.py:27`):
    `ASHRAE_STANDARD`, `HEURISTIC`, `KDE_IMPUTED`, `PDE_GENERATED`.

`01_buildings.gpkg` is the raw Step-2.1 acquisition output (23 columns, no
`archetype_id`/`use_class`/`climate_zone`) -- it predates classification, so it
cannot be run through `openubem.semantic.enrich_semantics` (which requires a
29-column classified frame, `openubem/semantic/__init__.py:334`
`_validate_input_schema`). This script therefore reads exactly what is
persisted in run 4's inputs, per the plan's D3 (call production parsers,
never re-implement) -- it does not re-run classification or enrichment.
No imputation tier is enabled, promoted or wired here.
"""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from openubem.semantic.provenance import CANONICAL_PROVENANCE  # noqa: E402

RUN4_ROOT = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\open48_refleet4")
CELLS = (
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
)
OUT_CSV = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\openubem\outputs\comparisons\open17_tier_census_2026-08-20.csv")

_TIER_PREFIXES = {
    "FUSED": "fusion",
    "HOTDECK_NEIGHBOR": "spatial",
    "GROUPMODE": "statistical",
    "ML": "ml",
    "DRAW": "draw",
}
_LEGACY_TOKENS = set(CANONICAL_PROVENANCE) | {"VINTAGE_NAN_PERMISSIVE_DEFAULT"}
_ACQUISITION_TOKENS = {"OSM_OBSERVED", "OSM_MISSING", "OSM_GENERIC"}


def classify_token(token: str) -> str:
    if token in _ACQUISITION_TOKENS:
        return "ACQUISITION (not an imputation tier)"
    if token in _LEGACY_TOKENS:
        return "legacy_default"
    for prefix, tier in _TIER_PREFIXES.items():
        if token == prefix or token.startswith(prefix + "_"):
            return tier
    return "UNMAPPED"


def main() -> None:
    prov_cols = None
    rows = []
    dqf_token_counts: dict[str, int] = {}
    unmapped_tokens: dict[str, int] = {}
    total_rows = 0

    for cell in CELLS:
        gpkg_path = RUN4_ROOT / cell / "01_buildings.gpkg"
        gdf = gpd.read_file(gpkg_path)
        total_rows += len(gdf)
        if prov_cols is None:
            prov_cols = [c for c in gdf.columns if c.startswith("provenance_")]
            print("provenance columns:", prov_cols)

        for col in prov_cols:
            target = col[len("provenance_"):]
            vc = gdf[col].fillna("").astype(str).value_counts()
            for token, count in vc.items():
                tier = classify_token(token) if token else "EMPTY"
                rows.append({"target": target, "token": token, "tier": tier,
                              "count": int(count), "cell": cell})
                if tier == "UNMAPPED":
                    unmapped_tokens[token] = unmapped_tokens.get(token, 0) + int(count)

        if "data_quality_flag" in gdf.columns:
            for cell_val in gdf["data_quality_flag"].fillna("").astype(str):
                for tok in [t for t in cell_val.split(",") if t]:
                    dqf_token_counts[tok] = dqf_token_counts.get(tok, 0) + 1

    df = pd.DataFrame(rows)
    agg = (
        df.groupby(["target", "tier"], as_index=False)["count"].sum()
        .sort_values(["target", "tier"])
    )
    agg.to_csv(OUT_CSV, index=False)
    print(f"wrote {OUT_CSV} rows={len(agg)}")

    print("\n=== target x tier x count (summed over 12 cells) ===")
    print(agg.to_string(index=False))

    print("\n=== denominator per target (rows needing a value = ACQUISITION missing/generic) ===")
    denom = (
        df[df["tier"] == "ACQUISITION (not an imputation tier)"]
        .assign(is_gap=lambda d: d["token"].isin(["OSM_MISSING", "OSM_GENERIC"]))
    )
    denom_by_target = (
        denom[denom["is_gap"]].groupby("target")["count"].sum()
    )
    print(denom_by_target.to_string())
    print(f"\ntotal rows across 12 cells = {total_rows}")

    fused_count = int(agg.loc[agg["tier"] == "fusion", "count"].sum())
    print(f"\nFUSED count (tier=='fusion', all targets) = {fused_count}")

    print(f"\nunmapped provenance tokens: {unmapped_tokens if unmapped_tokens else 'NONE'}")

    print("\n=== data_quality_flag comma-split token census (top 20) ===")
    dqf_series = pd.Series(dqf_token_counts).sort_values(ascending=False)
    print(dqf_series.head(20).to_string())
    dqf_unmapped = {t: c for t, c in dqf_token_counts.items() if classify_token(t) == "UNMAPPED"}
    print(f"\ndata_quality_flag tokens matching a known tier/legacy vocabulary: "
          f"{[t for t in dqf_token_counts if classify_token(t) != 'UNMAPPED'] or 'NONE'}")


if __name__ == "__main__":
    main()
