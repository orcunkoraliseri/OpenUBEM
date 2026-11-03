"""X04/X08 of PLAN_ten-items-2026-08-18-overnight.md.

X04 -- OPEN-35's CONSEQUENCE. The item's mechanism is proved and its population is exact
       (2,611 buildings with neither `levels` nor `height_m`, all persisted at levels = 1.0,
       re-derived exactly last pass). What has never been measured is what that costs. Compare
       the EUI distribution of the 2,611 against the rest of the fleet, and separately the
       subset given a mid- or high-rise archetype and built as a single storey.
       CONFOUND, stated up front: these buildings are data-poor BY DEFINITION, so a raw EUI
       gap is not a causal estimate. It is reported as a gap with the confound named.

X08 -- OPEN-10's DENOMINATOR. MEASUREMENT_open-10_zonegroup-capability.md §4 names the exact
       experiment that would settle the "90 buildings" reach figure and declines to run it,
       because that plan forbade CPU-bound work: "load the fleet, join to ARCHETYPE_IDF_MAP,
       and call the current compute_band_map()/match_storeys() pair once per building for the
       two apartment archetypes only". This plan does not carry that constraint. This is that
       experiment, run.

       Note on method: match_storeys() mutates the idf in place only when it returns "applied",
       but the STATUS it returns is a pure function of (band_map, n_real) -- band_map is passed
       in, not recomputed from the idf. So one loaded prototype per archetype is reused across
       n_real values without affecting any status. The mutated in-memory idf is discarded.

Emits open35_eui_consequence.csv and open10_storey_expressibility_fleet.csv.
"""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

BASE = Path("C:/Users/o_iseri/AppData/Local/Temp/ubem_validation/open48_refleet")
RESULTS = ROOT / "docs/validations/overAll/results/open48_refleet"
OUT = ROOT / "openubem" / "outputs" / "comparisons"

CELLS = ["nyc_centre", "nyc_urban", "nyc_suburban", "nyc_rural",
         "la_centre", "la_urban", "la_suburban", "la_rural",
         "austin_centre", "austin_urban", "austin_suburban", "austin_rural"]

MIDHIGH = {"MidriseApartment", "HighriseApartment", "LargeOffice", "LargeOfficeDetailed",
           "LargeHotel", "Hospital", "TallBuilding", "SuperTallBuilding"}
APARTMENT = {"MidriseApartment", "HighriseApartment"}


def load_fleet() -> pd.DataFrame:
    frames = []
    for cell in CELLS:
        gp, rp = BASE / cell / "01_buildings.gpkg", RESULTS / cell / "05_results.csv"
        if not gp.exists() or not rp.exists():
            print("MISSING %s" % cell)
            continue
        g = gpd.read_file(gp)[["osm_id", "levels", "height_m", "footprint_area_m2"]]
        g = g.rename(columns={"levels": "in_levels", "height_m": "in_height_m",
                              "footprint_area_m2": "in_footprint_m2"})
        r = pd.read_csv(rp)
        d = r.merge(g, on="osm_id", how="left")
        d["cell"] = cell
        frames.append(d)
    return pd.concat(frames, ignore_index=True)


def x04(df: pd.DataFrame) -> None:
    print("\n" + "=" * 78)
    print("X04 -- OPEN-35: what building 2,611 buildings as one storey costs")
    print("=" * 78)
    df["neither"] = df["in_levels"].isna() & df["in_height_m"].isna()
    n = int(df["neither"].sum())
    print("population with neither `levels` nor `height_m`: %d / %d (%.2f %%)"
          % (n, len(df), 100.0 * n / len(df)))
    print("  of those, persisted at levels = 1.0 in the results: %d"
          % int((df.loc[df["neither"], "levels"] == 1.0).sum()))

    df["midhigh_at_one_storey"] = (df["neither"] & (df["levels"] == 1.0)
                                   & df["archetype_id"].isin(MIDHIGH))
    m = int(df["midhigh_at_one_storey"].sum())
    print("  of those, given a mid-/high-rise archetype and built as ONE storey: %d" % m)

    ok = df[(df["simulation_status"] == "success") & df["total_eui_kwh_m2"].notna()].copy()
    print("\nsuccessful, EUI present: %d" % len(ok))
    grp = ok.groupby("neither")["total_eui_kwh_m2"]
    print("\n--- total EUI, affected vs rest (kWh/m2) ---")
    print(grp.agg(["count", "mean", "median", "std",
                   lambda s: s.quantile(0.25), lambda s: s.quantile(0.75)])
          .rename(columns={"<lambda_0>": "p25", "<lambda_1>": "p75"}).round(2).to_string())

    a = ok.loc[ok["neither"], "total_eui_kwh_m2"]
    b = ok.loc[~ok["neither"], "total_eui_kwh_m2"]
    if len(a) and len(b):
        print("\n  median gap: %+.2f kWh/m2 (%+.2f %%)  |  mean gap: %+.2f kWh/m2 (%+.2f %%)"
              % (a.median() - b.median(), 100.0 * (a.median() / b.median() - 1),
                 a.mean() - b.mean(), 100.0 * (a.mean() / b.mean() - 1)))

    sub = ok[ok["midhigh_at_one_storey"]]
    if len(sub):
        print("\n--- the mid-/high-rise-archetype-at-one-storey subset ---")
        print("  n = %d   median %.2f   mean %.2f   vs rest-of-fleet median %.2f"
              % (len(sub), sub["total_eui_kwh_m2"].median(),
                 sub["total_eui_kwh_m2"].mean(), b.median()))
        print(sub.groupby("archetype_id")["total_eui_kwh_m2"]
              .agg(["count", "median", "mean"]).round(2).to_string())

    print("\n--- per cell ---")
    per = (ok.groupby(["cell", "neither"])["total_eui_kwh_m2"]
           .agg(["count", "median"]).round(2).unstack())
    print(per.to_string())

    print("\n--- failure rate, affected vs rest (a separate question from EUI) ---")
    df["failed"] = df["simulation_status"] != "success"
    print(pd.crosstab(df["neither"], df["failed"]).to_string())

    cols = ["cell", "osm_id", "neither", "midhigh_at_one_storey", "archetype_id", "levels",
            "in_levels", "in_height_m", "footprint_area_m2", "simulation_status",
            "total_eui_kwh_m2", "heating_eui_kwh_m2", "cooling_eui_kwh_m2"]
    df[[c for c in cols if c in df.columns]].to_csv(
        OUT / "open35_eui_consequence.csv", index=False)
    print("\nwrote %s" % (OUT / "open35_eui_consequence.csv"))


def x08(df: pd.DataFrame) -> None:
    print("\n" + "=" * 78)
    print("X08 -- OPEN-10: how many fleet buildings the ZoneGroup edit would actually help")
    print("=" * 78)
    from openubem import config
    from openubem.geometry.layout_assigner import (ARCHETYPE_IDF_MAP, compute_band_map,
                                                   match_storeys)
    from eppy.modeleditor import IDF

    idd = Path("C:/EnergyPlusV23-1-0/Energy+.idd")
    if not idd.exists():
        print("IDD not found at %s -- cannot load prototypes" % idd)
        return
    IDF.setiddname(str(idd))

    d = df.copy()
    d["n_real"] = pd.to_numeric(d["levels"], errors="coerce")
    d = d[d["n_real"].notna() & d["archetype_id"].notna()]
    d["n_real"] = d["n_real"].round().astype(int)
    d = d[d["n_real"] >= 1]

    have = d[d["archetype_id"].isin(ARCHETYPE_IDF_MAP)]
    print("fleet rows: %d ; with an ARCHETYPE_IDF_MAP entry: %d ; without: %d"
          % (len(d), len(have), len(d) - len(have)))

    band_maps = {}
    for arch in sorted(have["archetype_id"].unique()):
        p = Path(config.BASELINE_IDF_DIR) / ARCHETYPE_IDF_MAP[arch]
        if not p.exists():
            print("  prototype missing: %s" % p)
            continue
        try:
            idf = IDF(str(p))
            band_maps[arch] = (idf, compute_band_map(idf))
        except Exception as exc:                                       # noqa: BLE001
            print("  load failed %s: %s" % (arch, str(exc)[:90]))

    rows = []
    cache = {}
    for _, r in have.iterrows():
        arch, n_real = r["archetype_id"], int(r["n_real"])
        if arch not in band_maps:
            continue
        key = (arch, n_real)
        if key not in cache:
            idf, bm = band_maps[arch]
            res = match_storeys(idf, n_real, bm)
            # proposed mechanism: overwrite the ZoneGroup's own list multiplier directly,
            # which reaches every n_real >= n_proto for an archetype that HAS a ZoneGroup.
            has_zg = any(b.get("storeys_in_band", 1) > 1 for b in bm["bands"])
            non_middle = sum(b.get("storeys_in_band", 1) for b in bm["bands"][1:-1:1]) \
                if False else None
            proposed = res["status"]
            if has_zg and res["status"] == "fallback_not_expressible":
                proposed = "applied_under_zonegroup_overwrite"
            cache[key] = (res["status"], res["n_proto"], proposed, has_zg)
        st, n_proto, proposed, has_zg = cache[key]
        rows.append({"cell": r["cell"], "osm_id": r["osm_id"], "archetype_id": arch,
                     "n_real": n_real, "n_proto": n_proto, "shipped_status": st,
                     "status_under_zonegroup_overwrite": proposed,
                     "archetype_has_zonegroup": has_zg,
                     "is_apartment": arch in APARTMENT})

    out = pd.DataFrame(rows)
    if out.empty:
        print("no rows evaluated")
        return
    out.to_csv(OUT / "open10_storey_expressibility_fleet.csv", index=False)

    print("\n--- shipped mechanism, status over the evaluated fleet ---")
    print(out["shipped_status"].value_counts().to_string())

    print("\n--- which archetypes actually carry a ZoneGroup ---")
    print(out.groupby("archetype_id")["archetype_has_zonegroup"].first().to_string())

    print("\n--- the reach of the proposed ZoneGroup-overwrite edit ---")
    gain = out[out["status_under_zonegroup_overwrite"] == "applied_under_zonegroup_overwrite"]
    print("buildings that would move fallback_not_expressible -> applied: %d" % len(gain))
    if len(gain):
        print(gain.groupby("archetype_id").size().to_string())
        print("\nper cell:")
        print(gain.groupby("cell").size().to_string())

    nx = out[out["shipped_status"] == "fallback_not_expressible"]
    print("\n--- fallback_not_expressible, and how much of it the edit cannot touch ---")
    print("total fallback_not_expressible: %d" % len(nx))
    print("  in the two apartment archetypes (helped): %d" % int(nx["is_apartment"].sum()))
    print("  everywhere else (structural, NOT helped): %d" % int((~nx["is_apartment"]).sum()))
    print(nx[~nx["is_apartment"]].groupby("archetype_id").size().to_string())
    print("\nwrote %s" % (OUT / "open10_storey_expressibility_fleet.csv"))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    df = load_fleet()
    print("fleet loaded: %d rows across %d cells" % (len(df), df["cell"].nunique()))
    x04(df)
    try:
        x08(df)
    except Exception as exc:                                           # noqa: BLE001
        import traceback
        traceback.print_exc()
        print("X08 FAILED: %s" % str(exc)[:200])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
