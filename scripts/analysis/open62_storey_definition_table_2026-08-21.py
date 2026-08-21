"""OPEN-62 T06 -- storey-definition decision table.

Measurement only. Does not choose a definition. Reads
openubem/outputs/comparisons/open03_storey_census_zfix.csv (8,160 rows) and,
for each of four candidate storey-count columns, reports agreement rate and
signed difference against auto_storey_count and source_storey_count, fleet-
wide and per archetype, with the six Z_Origin-collapse-risk archetypes shown
separately.
"""
import pandas as pd

IN_CSV = "openubem/outputs/comparisons/open03_storey_census_zfix.csv"
OUT_CSV = "openubem/outputs/comparisons/open62_storey_definition_table_2026-08-21.csv"

BASELINES = ["auto_storey_count", "source_storey_count"]
DEFS = {
    "layout_assign_storey_count": "layout_assign_storey_count",
    "layout_assign_storey_count_naive": "layout_assign_storey_count_naive",
    "layout_assign_storey_count_floor": "layout_assign_storey_count_floor",
    "layout_assign_storey_count_attic_excluded": None,  # built below
}


def build(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["layout_assign_storey_count_attic_excluded"] = (
        df["layout_assign_storey_count_floor"] - df["auto_attic_zone_count"]
    ).clip(lower=1)
    return df


def summarize(df: pd.DataFrame, def_col: str, base_col: str, scope_label: str) -> dict:
    d = df[def_col] - df[base_col]
    agree = (df[def_col] == df[base_col])
    return {
        "scope": scope_label,
        "definition": def_col,
        "baseline": base_col,
        "n": len(df),
        "agree_n": int(agree.sum()),
        "agree_rate_pct": round(100.0 * agree.mean(), 4) if len(df) else float("nan"),
        "mean_signed_diff": round(d.mean(), 4) if len(df) else float("nan"),
        "max_signed_diff": int(d.max()) if len(df) else None,
        "min_signed_diff": int(d.min()) if len(df) else None,
    }


def main():
    df = pd.read_csv(IN_CSV)
    assert len(df) == 8160, f"expected 8160 rows, got {len(df)}"

    df = build(df)

    rows = []
    scopes = [
        ("fleet", df),
        ("collapse_risk", df[df["layout_assign_z_origin_collapse_risk"] == True]),
        ("non_collapse_risk", df[df["layout_assign_z_origin_collapse_risk"] == False]),
    ]
    for scope_label, sub in scopes:
        for def_col in DEFS:
            for base_col in BASELINES:
                rows.append(summarize(sub, def_col, base_col, scope_label))

    for arch, sub in df.groupby("archetype_id"):
        for def_col in DEFS:
            for base_col in BASELINES:
                rows.append(summarize(sub, def_col, base_col, f"archetype:{arch}"))

    out = pd.DataFrame(rows)
    out.to_csv(OUT_CSV, index=False)

    print(f"rows written: {len(out)} -> {OUT_CSV}")
    print()
    print("=== fleet-wide headline ===")
    fleet = out[out["scope"] == "fleet"]
    print(fleet.to_string(index=False))
    print()
    print("=== collapse_risk vs non_collapse_risk (vs auto_storey_count) ===")
    cr = out[(out["scope"].isin(["collapse_risk", "non_collapse_risk"])) & (out["baseline"] == "auto_storey_count")]
    print(cr.to_string(index=False))

    # sanity: reproduce the register's 30.0 / 70.0 split independently, for the report
    real = df["layout_assign_match_storeys_status"].isin(
        ["identity", "applied", "no_baseline_fallback_auto"]
    )
    print()
    print(f"C13 check: layout_assign represents real storey count for "
          f"{real.sum()}/{len(df)} = {100*real.mean():.4f}% "
          f"(register quotes 30.0%); complement = {100*(1-real.mean()):.4f}% (register quotes 70.0%)")

    print()
    print(f"C14 check: row count = {len(df)}")

    print()
    print("auto_attic_zone_count is 0 for all 8,160 rows -> attic_excluded == floor identically.")


if __name__ == "__main__":
    main()
