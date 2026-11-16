"""T12.6 CP-4 LIVE_SMOKE -- ONE manually-run real Overture query + fusion-tier
report (PLAN_phaseD_fusion.md §6 T12.6). NOT part of the pytest suite (rule 6).

Run from repo root:
    .venv/Scripts/python.exe scratchpad/t12_cp4_live_smoke.py

What it does (plan §6 T12.6 (a)-(e)):
  1. Loads a real fixture cell (nyc_centre, 738 real OSM buildings) and
     computes its EPSG:4326 bbox.
  2. Runs a REAL live Overture query (DuckDB httpfs+spatial against the
     public `overturemaps-us-west-2` S3 bucket, release 2026-06-17.0 --
     the latest available at run time) for that bbox.
  3. Commits the raw (pre-normalization) result as a small offline fixture
     under openubem/data/fixtures/fusion/ + a LICENSES.md manifest row.
  4. Re-reads that fixture through the normal `fetch_overture(slice_path=...)`
     path and runs `fusion.fuse` / `imputation.impute_missing` against the
     real target cell for height_m / levels / year_built / use_class,
     reporting join hit-rate, token correctness, miss->imputation fallback,
     fill-rate lift, and the use_class crosswalk hit-rate on real Overture
     class/subtype values.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from types import SimpleNamespace

import contextlib

import numpy as np
import pandas as pd
import geopandas as gpd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from openubem import config  # noqa: E402
from openubem.semantic import fusion  # noqa: E402
from openubem.semantic import imputation as imp  # noqa: E402
from openubem.semantic.imputation import ImputeConfig, impute_missing  # noqa: E402
from openubem.semantic.building_classifier import _normalise_use_class  # noqa: E402
from openubem.acquisition.overture_fetcher import fetch_overture  # noqa: E402

CELL = "nyc_centre"
CELL_GPKG = ROOT / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE" / CELL / "01_buildings.gpkg"
FIXTURES_DIR = ROOT / "openubem" / "data" / "fixtures" / "fusion"
SLICE_FIXTURE = FIXTURES_DIR / f"overture_{CELL}_slice.parquet"
LICENSES_MD = FIXTURES_DIR / "LICENSES.md"

OVERTURE_ENDPOINT = (
    "s3://overturemaps-us-west-2/release/2026-06-17.0/theme=buildings/type=building/*"
)


def hr(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


# ── Step 1: real fixture cell + bbox ────────────────────────────────────────

def load_cell() -> gpd.GeoDataFrame:
    hr(f"STEP 1 -- load real fixture cell: {CELL}")
    gdf = gpd.read_file(CELL_GPKG)
    print(f"loaded {len(gdf)} real buildings, CRS={gdf.crs}")
    bbox4326 = tuple(gdf.to_crs(4326).total_bounds)
    print(f"bbox EPSG:4326 = {bbox4326}")
    return gdf, bbox4326


# ── Step 2: REAL live Overture query ────────────────────────────────────────

def run_live_query(bbox4326):
    """Mirrors `overture_fetcher._fetch_live` internals but returns the RAW
    (pre-normalization) frame so it can be committed as an offline fixture
    in the same raw schema shape as the existing T12.2 synthetic fixture."""
    hr("STEP 2 -- REAL live Overture query (DuckDB httpfs + spatial)")
    import duckdb
    import shapely

    con = duckdb.connect()
    t0 = time.time()
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute("LOAD httpfs;")
    print(f"httpfs installed+loaded ({time.time() - t0:.2f}s)")
    t0 = time.time()
    con.execute("INSTALL spatial; LOAD spatial;")
    print(f"spatial installed+loaded ({time.time() - t0:.2f}s)")
    con.execute("SET s3_region='us-west-2';")

    minx, miny, maxx, maxy = bbox4326
    where = (
        f"WHERE bbox.xmin <= {maxx} AND bbox.xmax >= {minx} "
        f"AND bbox.ymin <= {maxy} AND bbox.ymax >= {miny}"
    )
    query = (
        "SELECT id, height, num_floors, class, subtype, ST_AsWKB(geometry) AS geometry "
        f"FROM read_parquet('{OVERTURE_ENDPOINT}') {where}"
    )
    print(f"endpoint: {OVERTURE_ENDPOINT}")
    print("query:", query)
    t0 = time.time()
    try:
        arrow_tbl = con.execute(query).fetch_arrow_table()
    finally:
        con.close()
    elapsed = time.time() - t0
    df = arrow_tbl.to_pandas()
    geoms = shapely.from_wkb(df["geometry"].to_numpy())
    raw = gpd.GeoDataFrame(df.drop(columns=["geometry"]), geometry=geoms, crs="EPSG:4326")
    print(f"LIVE QUERY OK -- {len(raw)} Overture buildings returned in {elapsed:.1f}s")
    print("raw columns:", list(raw.columns))
    print(raw.head(3))
    return raw


# ── Step 3: commit as an offline fixture + LICENSES.md manifest row ────────

def commit_fixture(raw: gpd.GeoDataFrame) -> None:
    hr("STEP 3 -- commit fetched real slice as an offline fixture")
    raw.to_parquet(SLICE_FIXTURE)
    size = SLICE_FIXTURE.stat().st_size
    print(f"wrote {SLICE_FIXTURE} ({size:,} bytes)")
    assert size <= 5 * 1024 * 1024, "fixture exceeds the 5MB license-guard cap"

    manifest = LICENSES_MD.read_text(encoding="utf-8")
    row = (
        f"| {SLICE_FIXTURE.name} | REAL Overture Buildings theme, release 2026-06-17.0, "
        f"bbox-clipped to the {CELL} fixture cell (T12.6 CP-4 LIVE_SMOKE) "
        f"| CDLA-Permissive-2.0 | {size} |\n"
    )
    if SLICE_FIXTURE.name not in manifest:
        LICENSES_MD.write_text(manifest.rstrip("\n") + "\n" + row, encoding="utf-8")
        print(f"appended manifest row to {LICENSES_MD}")
    else:
        # re-run: refresh the row (size may have changed if the release moved on)
        lines = manifest.splitlines(keepends=True)
        lines = [ln for ln in lines if not ln.startswith(f"| {SLICE_FIXTURE.name} ")]
        lines.append(row)
        LICENSES_MD.write_text("".join(lines), encoding="utf-8")
        print(f"refreshed manifest row in {LICENSES_MD}")
    return size


# ── Step 4: fusion tier report on the real cell ─────────────────────────────

def _cfg(sources_for_attr, attr):
    return SimpleNamespace(
        FUSION_SOURCES_BY_TARGET={attr: sources_for_attr},
        FUSION_OVERTURE_SLICE_PATH=str(SLICE_FIXTURE),
        FUSION_OVERTURE_ENDPOINT=None,
        FUSION_LIDAR_NDSM_PATH=None,
        FUSION_ASSESSOR_PATH=None,
        FUSION_ASSESSOR_FIELDS={},
    )


@contextlib.contextmanager
def _patched_real_config(attr, sources_for_attr):
    """`_fusion_tier` calls `fusion.fuse(gdf, attr)` with cfg=None, which
    resolves lazily to the REAL `openubem.config` module (not whatever cfg
    object a caller happens to hold) -- so exercising fusion through
    `impute_missing`/`ImputeConfig.per_input_tiers` (the T12.4 tier contract,
    not just the T12.1 `fusion.fuse` internal) requires monkeypatching the
    actual config module for the call's duration, exactly like
    `tests/test_fusion.py::TestFusionTier` does with `monkeypatch.setattr`.
    Restores the original values afterward (manual driver -- no pytest
    monkeypatch fixture available)."""
    orig_sources = config.FUSION_SOURCES_BY_TARGET
    orig_slice = config.FUSION_OVERTURE_SLICE_PATH
    config.FUSION_SOURCES_BY_TARGET = {attr: sources_for_attr}
    config.FUSION_OVERTURE_SLICE_PATH = str(SLICE_FIXTURE)
    try:
        yield
    finally:
        config.FUSION_SOURCES_BY_TARGET = orig_sources
        config.FUSION_OVERTURE_SLICE_PATH = orig_slice


def report_fusion(gdf: gpd.GeoDataFrame) -> None:
    hr("STEP 4 -- fusion tier report on the real cell (re-read via fetch_overture(slice_path=...))")

    layer = fetch_overture(slice_path=str(SLICE_FIXTURE))
    print(f"re-read normalized Overture layer: {len(layer)} rows, CRS={layer.crs}")
    print("normalized columns:", list(layer.columns))

    gdf = gdf.copy()
    uc_pairs = gdf.apply(lambda r: _normalise_use_class(r), axis=1)
    uc_value = uc_pairs.apply(lambda t: t[0])
    uc_score = uc_pairs.apply(lambda t: t[1])
    # a score==0.0 "unknown" classification (no OSM tag matched at all) is a
    # genuine semantic gap -- NaN it out so it is something for fusion/
    # imputation to actually fill, rather than pre-filling every row with the
    # literal string "unknown" (which would make missing_before==0 for
    # use_class and defeat the point of this smoke test).
    gdf["use_class"] = uc_value.where(uc_score > 0.0, other=np.nan)
    print("\nuse_class (derived from building_tag/function_tag, score==0 -> NaN gap) value counts:")
    print(gdf["use_class"].value_counts(dropna=False))

    attrs = ["height_m", "levels", "year_built", "use_class"]
    n = len(gdf)
    results = {}

    for attr in attrs:
        hr(f"attribute: {attr}")
        missing_before = int(gdf[attr].isna().sum())
        print(f"N={n}, missing before fusion = {missing_before} ({missing_before / n:.1%})")

        # (a) raw fuse() over ALL rows -- join hit-rate against the whole cell
        cfg = _cfg(("overture",), attr)
        value, token = fusion.fuse(gdf, attr, cfg)
        hit_all = int(value.notna().sum())
        print(f"join hit-rate (all {n} buildings, regardless of prior nullness): "
              f"{hit_all}/{n} = {hit_all / n:.1%}")
        tok_counts = token.value_counts(dropna=True)
        print("tokens on hit rows:", dict(tok_counts))
        bad_tokens = [t for t in tok_counts.index if t not in (f"FUSED_OVERTURE_HIGH", f"FUSED_OVERTURE_MED")]
        assert not bad_tokens, f"unexpected token(s) for {attr}: {bad_tokens}"

        # (b) fusion-only impute_missing on the REAL gaps
        gdf_fusion_only = gdf.copy()
        with _patched_real_config(attr, ("overture",)):
            out_fusion_only = impute_missing(
                gdf_fusion_only, targets=[attr],
                cfg=ImputeConfig(per_input_tiers={attr: ("fusion",)}),
            )
        prov_col = f"provenance_{attr}"
        filled_by_fusion = out_fusion_only.loc[gdf[attr].isna(), attr].notna().sum()
        still_missing_fusion_only = out_fusion_only[attr].isna().sum()
        fused_tokens_seen = (
            out_fusion_only.loc[gdf[attr].isna() & out_fusion_only[attr].notna(), prov_col].unique().tolist()
            if prov_col in out_fusion_only.columns else []
        )
        print(f"fusion-only fill of the {missing_before} REAL gaps: "
              f"{filled_by_fusion} filled, {still_missing_fusion_only} still missing")
        print(f"provenance tokens on fusion-filled gap rows: {fused_tokens_seen}")
        assert all(t is not None and t.startswith("FUSED_OVERTURE_") for t in fused_tokens_seen), (
            f"non-FUSED token leaked into fusion-only fill for {attr}: {fused_tokens_seen}"
        )

        # (c) fusion + spatial + statistical -- misses must fall through
        tiers = ("fusion", "spatial", "statistical") if attr != "use_class" else ("fusion", "statistical")
        gdf_full = gdf.copy()
        with _patched_real_config(attr, ("overture",)):
            out_full = impute_missing(
                gdf_full, targets=[attr],
                cfg=ImputeConfig(per_input_tiers={attr: tiers}),
            )
        filled_total = out_full.loc[gdf[attr].isna(), attr].notna().sum()
        still_missing_full = out_full[attr].isna().sum()
        gap_rows = gdf[attr].isna()
        prov_on_gaps = out_full.loc[gap_rows, prov_col] if prov_col in out_full.columns else pd.Series(dtype=object)
        prov_counts = prov_on_gaps.value_counts(dropna=True)
        n_fusion_tok = int(sum(c for t, c in prov_counts.items() if str(t).startswith("FUSED_OVERTURE_")))
        n_fallback_tok = int(sum(c for t, c in prov_counts.items() if not str(t).startswith("FUSED_OVERTURE_")))
        print(f"fusion+imputation combined fill of the {missing_before} REAL gaps: "
              f"{filled_total} filled ({tiers}), {still_missing_full} still missing")
        print(f"  -> of which {n_fusion_tok} carry a FUSED_OVERTURE_* token (ground truth), "
              f"{n_fallback_tok} carry a non-FUSED fallback token (imputation carried the miss)")
        print("  provenance token breakdown on the real gap rows:", dict(prov_counts))
        non_fused_examples = prov_on_gaps[~prov_on_gaps.astype(str).str.startswith("FUSED_OVERTURE_") & prov_on_gaps.notna()]
        if len(non_fused_examples) > 0:
            sample_tok = non_fused_examples.iloc[0]
            assert "FUSED" not in str(sample_tok), "fallback row unexpectedly carries a FUSED token"
            print(f"  miss-falls-through sample: row {non_fused_examples.index[0]} -> token {sample_tok!r}")

        results[attr] = dict(
            n=n, missing_before=missing_before,
            join_hit_all=hit_all,
            fusion_only_filled=int(filled_by_fusion),
            fusion_only_still_missing=int(still_missing_fusion_only),
            combined_filled=int(filled_total),
            combined_still_missing=int(still_missing_full),
            n_fusion_token=n_fusion_tok,
            n_fallback_token=n_fallback_tok,
        )

    # (e) spot-check >=1 fused value against the external source directly
    hr("spot-check: fused value vs. the raw Overture record it came from")
    matched_pos = fusion._spatial_join_positions(gdf, layer)
    hit_idx = matched_pos.index[matched_pos.notna()][:3]
    for idx in hit_idx:
        pos = int(matched_pos.loc[idx])
        ov_row = layer.iloc[pos]
        print(f"target row {idx}: OSM id={gdf.at[idx, 'osm_id']!r}, "
              f"original height_m={gdf.at[idx, 'height_m']!r}, original levels={gdf.at[idx, 'levels']!r}")
        print(f"  -> matched Overture id={ov_row['id']!r}, height={ov_row['height']!r}, "
              f"levels={ov_row['levels']!r}, use_class(raw)={ov_row['use_class']!r}")
        fused_h_val, fused_h_tok = fusion.fuse(gdf.loc[[idx]], "height_m", _cfg(("overture",), "height_m"))
        print(f"  -> fuse('height_m') for this row: value={fused_h_val.iloc[0]!r}, token={fused_h_tok.iloc[0]!r}"
              f" (matches Overture height directly: {fused_h_val.iloc[0] == ov_row['height']})")

    # use_class crosswalk hit-rate on REAL Overture class/subtype values
    hr("use_class crosswalk hit-rate on REAL Overture class/subtype raw values")
    hit_idx_all = matched_pos.index[matched_pos.notna()]
    raw_vals = layer["use_class"].iloc[matched_pos.loc[hit_idx_all].astype(int)]
    mapped = raw_vals.dropna().map(lambda v: str(v).lower() in fusion._USE_CLASS_CROSSWALK)
    n_raw = len(raw_vals.dropna())
    n_mapped = int(mapped.sum())
    n_unmapped = n_raw - n_mapped
    print(f"of {n_raw} matched target rows with a non-null Overture class/subtype value: "
          f"{n_mapped} mapped ({n_mapped / n_raw:.1%}), {n_unmapped} did NOT map "
          f"({n_unmapped / n_raw:.1%}) via osm_to_use_class.json")
    unmapped_vals = sorted(set(
        str(v).lower() for v in raw_vals.dropna()
        if str(v).lower() not in fusion._USE_CLASS_CROSSWALK
    ))
    print(f"unmapped raw Overture class/subtype values ({len(unmapped_vals)} distinct): {unmapped_vals}")

    hr("SUMMARY -- per-attribute join hit-rate / fill-rate lift")
    for attr, r in results.items():
        print(f"{attr:12s} N={r['n']:4d} missing_before={r['missing_before']:4d} "
              f"join_hit(all)={r['join_hit_all']:4d} "
              f"fusion_only_fill={r['fusion_only_filled']:4d} "
              f"combined_fill={r['combined_filled']:4d} "
              f"(of which fusion={r['n_fusion_token']}, fallback={r['n_fallback_token']}) "
              f"still_missing_combined={r['combined_still_missing']:4d}")

    return results


def main():
    gdf, bbox4326 = load_cell()
    raw = run_live_query(bbox4326)
    size = commit_fixture(raw)
    results = report_fusion(gdf)

    hr("DONE -- CP-4 LIVE_SMOKE complete")
    print(f"Overture release queried: 2026-06-17.0 (latest available at run time)")
    print(f"Fixture committed: {SLICE_FIXTURE} ({size:,} bytes)")
    print("Re-run the license guard + fusion suite next:")
    print("  .venv/Scripts/python.exe -m pytest tests/test_fusion.py tests/test_fusion_license_guard.py -q")


if __name__ == "__main__":
    main()
