"""T16 of PLAN_twenty-items-2026-08-19.md -- re-derive OPEN-10's expressibility
census (90 / 1,992 / 1,902 / 497 / 7,442) on run-4 (open48_refleet4) artifacts.

Reuses the exact production functions X08 used (compute_band_map / match_storeys),
called fresh here against run-4's own results/05_results.csv per cell (F2: note
the results/ subdirectory). No production code touched.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

RUN4 = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\open48_refleet4")
OUT = ROOT / "openubem" / "outputs" / "comparisons"

CELLS = ["nyc_centre", "nyc_urban", "nyc_suburban", "nyc_rural",
         "la_centre", "la_urban", "la_suburban", "la_rural",
         "austin_centre", "austin_urban", "austin_suburban", "austin_rural"]


def load_fleet() -> pd.DataFrame:
    frames = []
    for cell in CELLS:
        rp = RUN4 / cell / "results" / "05_results.csv"
        if not rp.exists():
            print("MISSING %s" % rp)
            continue
        r = pd.read_csv(rp)
        r["cell"] = cell
        frames.append(r)
    return pd.concat(frames, ignore_index=True)


def main():
    from openubem import config
    from openubem.geometry.layout_assigner import (ARCHETYPE_IDF_MAP, compute_band_map,
                                                     match_storeys)
    from eppy.modeleditor import IDF

    idd = Path("C:/EnergyPlusV23-1-0/Energy+.idd")
    if not idd.exists():
        print("IDD not found at %s -- cannot load prototypes" % idd)
        return 1
    IDF.setiddname(str(idd))

    df = load_fleet()
    print("run-4 fleet rows loaded: %d" % len(df))

    d = df.copy()
    d["n_real"] = pd.to_numeric(d["levels"], errors="coerce")
    d = d[d["n_real"].notna() & d["archetype_id"].notna()]
    d["n_real"] = d["n_real"].round().astype(int)
    d = d[d["n_real"] >= 1]

    have = d[d["archetype_id"].isin(ARCHETYPE_IDF_MAP)]
    print("fleet rows: %d ; with an ARCHETYPE_IDF_MAP entry (evaluated): %d ; excluded: %d"
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
            has_zg = any(b.get("storeys_in_band", 1) > 1 for b in bm["bands"])
            proposed = res["status"]
            if has_zg and res["status"] == "fallback_not_expressible":
                proposed = "applied_under_zonegroup_overwrite"
            cache[key] = (res["status"], res["n_proto"], proposed, has_zg)
        st, n_proto, proposed, has_zg = cache[key]
        rows.append({"cell": r["cell"], "osm_id": r["osm_id"], "archetype_id": arch,
                      "n_real": n_real, "n_proto": n_proto, "status": st,
                      "proposed_status": proposed, "has_zonegroup": has_zg})

    out = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT / "open10_storey_expressibility_run4.csv", index=False)
    print("wrote %s (%d rows)" % (OUT / "open10_storey_expressibility_run4.csv", len(out)))

    print("\n--- status distribution (evaluated = %d) ---" % len(out))
    print(out["status"].value_counts().to_string())

    not_expr = out[out["status"] == "fallback_not_expressible"]
    print("\nfallback_not_expressible: %d" % len(not_expr))
    print(not_expr["archetype_id"].value_counts().to_string())

    zg_reach = not_expr[not_expr["has_zonegroup"]]
    print("\nof fallback_not_expressible, buildings whose archetype carries a ZoneGroup "
          "(the edit's reach): %d" % len(zg_reach))
    print(zg_reach["archetype_id"].value_counts().to_string())

    applied = out[out["status"] == "applied"]
    print("\napplied (status): %d / %d" % (len(applied), len(out)))

    print("\n--- comparison to the carried figures ---")
    print("carried: 90 = 66 MidriseApartment + 24 HighriseApartment")
    print("re-derived ZoneGroup-reach split:")
    print(zg_reach["archetype_id"].value_counts().to_string())
    print("carried: 1,992 fallback_not_expressible ; re-derived: %d" % len(not_expr))
    print("carried: 1,902 = 1,992 - 90 structurally beyond the edit ; re-derived: %d"
          % (len(not_expr) - len(zg_reach)))
    print("carried: 497 applied ; re-derived: %d" % len(applied))
    print("carried: 7,442 evaluated ; re-derived: %d" % len(have))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
