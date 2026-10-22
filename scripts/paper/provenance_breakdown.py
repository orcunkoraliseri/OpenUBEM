from __future__ import annotations

import glob
from pathlib import Path

import geopandas as gpd
import pandas as pd

from openubem.semantic.provenance import parse_token

ROOT = Path(__file__).resolve().parents[2]
CMP = ROOT / "openubem" / "outputs" / "comparisons"
OUT_DIR = ROOT / "openubem" / "outputs"
EVID = OUT_DIR / "eu_evidence" / "EU-11"
RES = ROOT / "docs" / "docs_ACTIVE" / "europeanLocations" / "results"
PHASEE = ROOT / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE"
FLEET_CSV = CMP / "paper_adopted_fleet_per_building_2026-10-21.csv"
OUT_CSV = CMP / "paper_provenance_breakdown_2026-10-21.csv"
OUT_PNG = OUT_DIR / "paper_provenance_breakdown.png"

CATEGORIES = ["observed", "fused", "spatial", "statistical_default", "missing_not_tokenised", "unknown_token"]
US_ATTRS = {
    "levels": "provenance_levels", "height_m": "provenance_height_m", "year_built": "provenance_year_built",
    "function_tag": "provenance_function_tag", "building_tag": "provenance_building_tag",
}
EU_ATTRS = {"construction_period": "construction_period_provenance", "storeys": "storey_provenance",
            "dwellings": "dwellings_source"}
US_YEAR_TOKENS = {
    "HOTDECK_NEIGHBOR_HIGH": "spatial", "HOTDECK_NEIGHBOR_MED": "spatial",
    "GROUPMODE_MED": "statistical_default", "VINTAGE_NAN_PERMISSIVE_DEFAULT": "statistical_default",
}
EU_SITES = {
    "ES-MAD-BERRUGUETE": "win_2026-10-06", "FR-LYO-HAUTCOEURPENTES": "win_2026-10-06",
    "GB-LDN-STDUNSTANS": "win_2026-10-06", "IT-BOL-GALVANI2": "win_2026-10-06",
    "CA-MTL-PLATEAU": "win_2026-10-09", "AM-EVN-NORNORK": "win_2026-10-09", "ZA-CPT-WOODSTOCK": "win_2026-10-09",
    "FI-HEL-KALLIO": "win_2026-10-10", "AT-VIE-RUDOLFSHEIM": "win_2026-10-10", "HU-BUD-ERZSEBETVAROS": "win_2026-10-10",
}
INTERNAL_ONLY = {"ZA-CPT-WOODSTOCK"}
VINTAGE = {"US": "adopted fleet 2026-09-30, inputs of the 2026-08 Step 1 run",
           "EU-4": "results 2026-10-08, inputs of the 2026-10-06 tree", "EU-6": "results 2026-10-09/10"}


def classify_token(token) -> str:
    if token is None or (isinstance(token, float) and pd.isna(token)):
        return "observed"
    t = str(token).strip()
    if not t:
        return "observed"
    t = t.split("+")[0]
    u = t.upper()
    if t in ("observed", "observed_split", "single"):
        return "observed"
    if u.endswith("_OBSERVED") or u == "OBSERVED":
        return "observed"
    if u.startswith("FUSED_") or u.startswith("EPC_") or u.startswith("SAP_") or u.endswith("_DERIVED"):
        return "fused"
    if u.startswith("IMPUTED_NEIGHBOUR") or u.startswith("INFERRED_TERRACE_NEIGHBOUR") or u.startswith("HOTDECK_NEIGHBOR"):
        return "spatial"
    if (u.startswith("IMPUTED_DISTRICT_MODE") or u.startswith("IMPUTED_CENSUS") or u.startswith("GROUPMODE")
            or u.startswith("VINTAGE_NAN") or t == "area_imputed" or u.startswith("DEFAULT_")):
        return "statistical_default"
    if u.endswith("_MISSING") or u.endswith("_GENERIC"):
        return "missing_not_tokenised"
    p = parse_token(t)
    if p is not None:
        return "statistical_default" if p[0] in ("DEFAULT", "GROUPMODE") else "unknown_token"
    return "unknown_token"


def us_category(prov: str, attr: str, flag: str) -> str:
    base = classify_token(prov)
    if base != "missing_not_tokenised":
        return base
    if attr == "year_built":
        for tok in str(flag).split("|")[1:]:
            if tok in US_YEAR_TOKENS:
                return US_YEAR_TOKENS[tok]
    return base


def tally(site: str, scope: str, attr: str, cats: pd.Series, vintage: str, source: str) -> list[dict]:
    n = len(cats)
    counts = cats.value_counts()
    return [dict(site=site, scope=scope, attribute=attr, category=c, n=int(counts.get(c, 0)),
                 share_pct=round(100.0 * counts.get(c, 0) / n, 4) if n else None, n_buildings=n,
                 vintage=vintage, source=source) for c in CATEGORIES]


def us_rows() -> list[dict]:
    fleet = pd.read_csv(FLEET_CSV, usecols=["cell", "city", "osm_id", "data_quality_flag"])
    frames = []
    for f in sorted(glob.glob(str(PHASEE / "*" / "01_buildings.gpkg"))):
        g = gpd.read_file(f, ignore_geometry=True)
        frames.append(g[["osm_id"] + list(US_ATTRS.values())])
    prov = pd.concat(frames).drop_duplicates("osm_id")
    df = fleet.merge(prov, on="osm_id", how="left")
    rows = []
    for city, g in df.groupby("city"):
        for attr, col in US_ATTRS.items():
            cats = pd.Series([us_category(p, attr, fl) for p, fl in zip(g[col], g["data_quality_flag"].fillna(""))],
                             index=g.index)
            rows += tally(city, "united_states", attr, cats, VINTAGE["US"], "01_buildings.gpkg provenance_* + data_quality_flag")
    return rows


def eu_ids(site: str) -> set[str]:
    if site in ("ES-MAD-BERRUGUETE", "FR-LYO-HAUTCOEURPENTES", "GB-LDN-STDUNSTANS", "IT-BOL-GALVANI2"):
        p = pd.read_csv(RES / "EU11_results_2026-10-08_per_home.csv", usecols=["district", "building_id"], dtype=str)
        return set(p.loc[p["district"] == site, "building_id"])
    f = glob.glob(str(RES / f"EU22_results_{site}_*_per_home.csv"))[0]
    return set(pd.read_csv(f, usecols=["building_id"], dtype=str)["building_id"])


def eu_rows() -> list[dict]:
    rows = []
    for site, tag in EU_SITES.items():
        pb = pd.read_csv(EVID / f"{site}_{tag}" / "prepared_buildings.csv", dtype={"building_id": str})
        pb = pb[pb["building_id"].isin(eu_ids(site))]
        vint = VINTAGE["EU-4"] if tag == "win_2026-10-06" else VINTAGE["EU-6"]
        for attr, col in EU_ATTRS.items():
            cats = pb[col].map(classify_token)
            rows += tally(site, "international", attr, cats, vint, f"{site}_{tag}/prepared_buildings.csv {col}")
    return rows


def figure(df: pd.DataFrame) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = {"observed": "#0072B2", "fused": "#009E73", "spatial": "#E69F00", "statistical_default": "#D55E00",
              "missing_not_tokenised": "#999999", "unknown_token": "#CC79A7"}
    pub = df[~df["site"].isin(INTERNAL_ONLY)]
    us = pub[pub["scope"] == "united_states"]
    eu = pub[pub["scope"] == "international"]
    attrs = [("united_states", a) for a in US_ATTRS] + [("international", a) for a in EU_ATTRS]
    fig, axes = plt.subplots(2, 5, figsize=(18, 8), constrained_layout=True)
    for ax in axes.flat:
        ax.set_visible(False)
    for i, (scope, attr) in enumerate(attrs):
        r, c = (0, i) if i < 5 else (1, i - 5)
        ax = axes[r, c]
        ax.set_visible(True)
        sub = (us if scope == "united_states" else eu)
        sub = sub[sub["attribute"] == attr]
        sites = list(dict.fromkeys(sub["site"]))
        bottom = pd.Series(0.0, index=sites)
        for cat in CATEGORIES:
            v = sub[sub["category"] == cat].set_index("site")["share_pct"].reindex(sites).fillna(0.0)
            ax.bar(range(len(sites)), v.values, bottom=bottom.values, color=colors[cat], label=cat, width=0.8)
            bottom += v
        ax.set_xticks(range(len(sites)))
        ax.set_xticklabels([s.split("-")[0] if scope == "international" else s.upper() for s in sites],
                           rotation=45, ha="right", fontsize=8)
        ax.set_ylim(0, 100)
        ax.set_title(f"{'U.S.' if scope == 'united_states' else 'Intl.'}: {attr}", fontsize=10)
        if c == 0:
            ax.set_ylabel("share of buildings (%)")
    h, l = axes[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower right", ncol=1, fontsize=9, frameon=False, bbox_to_anchor=(0.99, 0.08))
    n_us = int(us[(us["attribute"] == "levels") & (us["category"] == "observed")]["n_buildings"].sum())
    n_eu = int(eu[(eu["attribute"] == "storeys") & (eu["category"] == "observed")]["n_buildings"].sum())
    fig.suptitle(f"Input provenance: U.S. {n_us:,} adopted buildings; international {n_eu:,} correctly divided homes "
                 "(Cape Town omitted, internal only)", fontsize=11)
    fig.savefig(OUT_PNG, dpi=150)
    plt.close(fig)


def main() -> None:
    rows = us_rows() + eu_rows()
    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)
    chk = df.groupby(["site", "attribute"])["share_pct"].sum()
    print("rows", len(df), "share sums min/max", round(chk.min(), 4), round(chk.max(), 4))
    print("unknown tokens", int(df.loc[df["category"] == "unknown_token", "n"].sum()))
    figure(df)
    p = df.pivot_table(index=["scope", "site", "attribute"], columns="category", values="share_pct")
    print(p.round(1).to_string())


if __name__ == "__main__":
    main()
