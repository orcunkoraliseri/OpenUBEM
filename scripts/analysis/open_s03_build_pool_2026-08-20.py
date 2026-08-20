import geopandas as gpd
import pandas as pd

files = {
    "boston_downtown_500m": "tests/fixtures/boston_downtown_500m.gpkg",
    "chicago_loop_500m": "tests/fixtures/chicago_loop_500m.gpkg",
}

frames = []
for src, path in files.items():
    gdf = gpd.read_file(path)
    gdf["source_fixture"] = src
    df = pd.DataFrame(gdf.drop(columns=["geometry"]))
    frames.append(df)

all_df = pd.concat(frames, ignore_index=True)
print("total", len(all_df))

def is_tagrich(row):
    bt = row["building_tag"]
    ft = row["function_tag"]
    bt_ok = pd.notna(bt) and str(bt) != "" and str(bt) != "yes"
    ft_ok = pd.notna(ft) and str(ft) != ""
    return bt_ok or ft_ok

mask = all_df.apply(is_tagrich, axis=1)
tagrich = all_df[mask].copy()
tagpoor = all_df[~mask].copy()
print("tagrich total", len(tagrich))
for src in files:
    print(src, "tagrich", (tagrich["source_fixture"]==src).sum())
print("tagpoor total", len(tagpoor))

tagrich.to_csv("scratchpad_open_s03_tagrich_full.csv", index=False)
tagpoor.to_csv("scratchpad_open_s03_tagpoor_full.csv", index=False)
