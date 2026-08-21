"""T08 of PLAN_ten-live-items-2026-08-21-night.md.

For each of the six unwired OPEN-17 targets (levels, function_tag, postcode,
building_tag, height_m, geometry), determine whether a source column exists
anywhere in 01_buildings.gpkg (across all 12 cells) that could plausibly feed
it, and how many needs-a-value rows have a usable value in some other column
of the same row.

Measurement only. No imputer run, no config touched.
"""
import json
import geopandas as gpd
import pandas as pd

CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]
EVID = "evidence/open48_refleet4"

TARGETS = ["levels", "function_tag", "postcode", "building_tag", "height_m", "geometry"]

CANDIDATE_KEYS = {
    "levels": ["building:levels", "levels", "building:min_level"],
    "height_m": ["height", "building:height", "height_raw", "ele"],
    "postcode": ["addr:postcode", "postal_code"],
    "function_tag": ["amenity", "shop", "tourism", "office", "leisure", "craft",
                      "healthcare", "landuse"],
    "building_tag": ["building", "building:use"],
}

frames = []
col_lists = {}
for cell in CELLS:
    path = f"{EVID}/{cell}/01_buildings.gpkg"
    gdf = gpd.read_file(path)
    gdf["cell"] = cell
    col_lists[cell] = list(gdf.columns)
    gdf["_geom_is_empty_or_null"] = gdf["geometry"].isna() | gdf["geometry"].is_empty
    frames.append(pd.DataFrame(gdf.drop(columns=["geometry"])))

print("=== column list per cell (head -40 equivalent, capped) ===")
for cell in CELLS:
    cols = col_lists[cell]
    print(f"{cell}: n_cols={len(cols)}")
print("cols_identical_across_cells:", all(col_lists[c] == col_lists[CELLS[0]] for c in CELLS))
print("full column list (from austin_centre, representative):")
for c in col_lists["austin_centre"][:40]:
    print(" ", c)

df = pd.concat(frames, ignore_index=True)
n_total = len(df)
print("\nn_total_buildings:", n_total)

# ---- C16: reproduce F11's seven counts (raw null + provenance needs-value) ----
print("\n=== C16 reproduction (F11) ===")
provenance_targets = ["levels", "height_m", "year_built", "building_tag", "function_tag", "postcode", "geometry"]
placeholder_report = {}
for t in provenance_targets:
    if t == "geometry":
        n_null_raw = int(df["_geom_is_empty_or_null"].sum())
    else:
        n_null_raw = int(df[t].isna().sum())
    prov_col = f"provenance_{t}"
    n_needs_value = int((df[prov_col] != "OSM_OBSERVED").sum())
    placeholders = sorted(df.loc[df[prov_col] != "OSM_OBSERVED", prov_col].unique().tolist())
    placeholder_report[t] = placeholders
    print(f"{t}: n_null_raw={n_null_raw} n_needs_value(provenance)={n_needs_value} pct={100*n_needs_value/n_total:.2f}% placeholders={placeholders}")

# ---- source-column inventory per target ----
print("\n=== T08 source inventory ===")

# parse surplus_tags once
def parse_tags(s):
    if s is None or (isinstance(s, float)):
        return {}
    try:
        return json.loads(s)
    except Exception:
        return {}

df["_tags"] = df["surplus_tags"].apply(parse_tags)

results_rows = []
for target in TARGETS:
    prov_col = f"provenance_{target}"
    needs_mask = df[prov_col] != "OSM_OBSERVED"
    n_needs = int(needs_mask.sum())

    if target == "geometry":
        print(f"\n-- {target} --")
        print(f"n_needs_value={n_needs} of {n_total} (0 needed; no source question applies)")
        results_rows.append({"target": target, "n_needs_value": n_needs,
                              "candidate_keys_checked": "n/a", "n_with_source_in_other_col": 0,
                              "pct_of_needs_value": 0.0, "source_exists": "n/a (0 needed)"})
        continue

    other_cols_present = []
    # direct alternate gpkg columns plausibly carrying the same info
    if target == "height_m":
        other_cols_present.append("roof_height_m")

    keys = CANDIDATE_KEYS[target]
    tag_has_key = df["_tags"].apply(lambda d, keys=keys: any(k in d and str(d[k]).strip() != "" for k in keys))
    n_tag_source = int((needs_mask & tag_has_key).sum())

    other_col_source_n = {}
    n_other_col_any = pd.Series(False, index=df.index)
    for oc in other_cols_present:
        has_val = df[oc].notna() & (df[oc].astype(str).str.strip() != "")
        n_here = int((needs_mask & has_val).sum())
        other_col_source_n[oc] = n_here
        n_other_col_any = n_other_col_any | has_val

    n_any_source = int((needs_mask & (tag_has_key | n_other_col_any)).sum())
    pct = 100 * n_any_source / n_needs if n_needs else 0.0

    print(f"\n-- {target} --")
    print(f"n_needs_value={n_needs} of {n_total}")
    print(f"candidate surplus_tags keys checked: {keys}")
    print(f"n_needs_value with a non-empty value under those keys in surplus_tags: {n_tag_source} ({100*n_tag_source/n_needs:.2f}% of n_needs_value)" if n_needs else "n/a")
    for oc, n_here in other_col_source_n.items():
        print(f"n_needs_value with a non-empty value in gpkg column '{oc}': {n_here} ({100*n_here/n_needs:.2f}% of n_needs_value)" if n_needs else "n/a")
    print(f"n_needs_value with ANY plausible source (surplus_tags key OR alt column): {n_any_source} ({pct:.2f}% of n_needs_value)")

    results_rows.append({
        "target": target,
        "n_needs_value": n_needs,
        "candidate_keys_checked": ";".join(keys) if keys else "",
        "alt_gpkg_columns_checked": ";".join(other_cols_present),
        "n_with_source_in_other_col": n_any_source,
        "pct_of_needs_value": round(pct, 2),
        "source_exists": "yes" if n_any_source > 0 else "no",
    })

out = pd.DataFrame(results_rows)
out_path = "openubem/outputs/comparisons/open17_t08_source_inventory_2026-08-21b.csv"
out.to_csv(out_path, index=False)
print("\nwrote:", out_path, "rows:", len(out))

print("\n=== C17: one line per target, source-exists yes/no + count ===")
for _, r in out.iterrows():
    print(f"{r['target']}: source_exists={r['source_exists']} n_with_source={r['n_with_source_in_other_col']} of n_needs_value={r['n_needs_value']}")
