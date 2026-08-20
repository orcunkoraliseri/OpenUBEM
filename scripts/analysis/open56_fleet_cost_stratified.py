"""X01/X02/X03 of PLAN_ten-items-2026-08-18-overnight.md -- what the 10 m3 zone-volume stub
costs the WHOLE fleet, and whether the heat-balance non-convergence is downstream of it.

Last pass (W01-W04) proved OPEN-56's mechanism by intervention and bounded its cost at
+0.75 % -- but on ten buildings in `la_rural` and `nyc_rural`, the two smallest and lowest-rise
cells in the fleet. The register's own next step says the remedy "needs a fleet-scale cost
measurement rather than ten buildings". This is that measurement.

X01: 5 successful buildings per cell x 12 cells, both arms, same session, same treatment
     (Zone.Volume = floor_area x height, exactly one field per zone, diff asserted first).
X02: emit the per-building covariates (zone count, storeys, floor area, archetype) so the
     cost can be regressed rather than averaged.
X03: additionally run the 10 buildings that carry a heat-balance non-convergence warning AND
     still succeeded. If writing Zone.Volume clears their non-convergence, OPEN-09 is a
     symptom of OPEN-56; if not, the two are independent. Both answers are reportable.

Control (unchanged, and it voids the numbers if it fails): "Indicated Zone Volume <= 0.0"
present in every baseline run, absent from every treated run.

`-x` is mandatory -- these IDFs use HVACTemplate:*.

Emits openubem/outputs/comparisons/open56_fleet_cost_stratified.csv.
"""
from __future__ import annotations

import os
import re
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from open56_zone_volume_experiment import (  # noqa: E402
    BASE, RESULTS, assert_one_field_diff, epw_for, read_run, run_ep, write_treated,
)

OUT = Path(__file__).resolve().parents[2] / "openubem" / "outputs" / "comparisons"
WORK = Path(os.environ.get("TEMP", "C:/Temp")) / "open56_fleet_cost"

CELLS = ["nyc_centre", "nyc_urban", "nyc_suburban", "nyc_rural",
         "la_centre", "la_urban", "la_suburban", "la_rural",
         "austin_centre", "austin_urban", "austin_suburban", "austin_rural"]
N_PER_CELL = 5
WORKERS = 6

# X03 -- the ten buildings with >=1 heat-balance non-convergence warning that still succeeded
# (from open09_fleet_err_perbuilding.csv, W07 of the previous pass).
NONCONVERGED_SURVIVORS = [
    ("la_centre", "way_427817687"), ("la_centre", "way_428015178"),
    ("la_suburban", "way_442633387"), ("la_suburban", "way_442634081"),
    ("la_suburban", "way_442634778"),
    ("la_rural", "way_472961043"), ("la_rural", "way_472961089"),
    ("la_rural", "way_472961090"), ("la_rural", "way_472961093"),
    ("la_rural", "way_472961164"),
]

_CONVERGE = re.compile(r"Inside surface heat balance did not converge")


def _n_converge(outdir: Path) -> int:
    err = outdir / "eplusout.err"
    if not err.exists():
        return -1
    return len(_CONVERGE.findall(err.read_text(encoding="utf-8", errors="replace")))


def _covariates() -> dict:
    """archetype / levels / area per building, from run 2's own results files."""
    cov = {}
    for cell in CELLS:
        p = RESULTS / cell / "05_results.csv"
        if not p.exists():
            continue
        df = pd.read_csv(p)
        cols = {c.lower(): c for c in df.columns}
        for _, r in df.iterrows():
            stem = str(r["osm_id"]).replace("/", "_")
            rec = {}
            for want in ("archetype_id", "levels", "num_floors", "floor_area_m2",
                         "footprint_area_m2", "area_m2", "eui_kwh_m2"):
                if want in cols:
                    rec[want] = r[cols[want]]
            cov[(cell, stem)] = rec
    return cov


def _one(job):
    cell, stem, tag = job
    src = BASE / cell / "step3" / "idfs" / ("%s.idf" % stem)
    epw = epw_for(cell)
    if not src.exists() or epw is None:
        return {"cell": cell, "stem": stem, "group": tag,
                "diff_check": "SKIP idf=%s epw=%s" % (src.exists(), epw is not None)}
    d = WORK / ("%s__%s" % (cell, stem))
    d.mkdir(parents=True, exist_ok=True)
    base_idf, treat_idf = d / "baseline.idf", d / "treated.idf"
    shutil.copyfile(src, base_idf)
    n_zones, vols = write_treated(base_idf, treat_idf)
    diff = assert_one_field_diff(base_idf, treat_idf)
    rec = {"cell": cell, "stem": stem, "group": tag, "n_zones": n_zones,
           "diff_check": diff,
           "min_written_volume_m3": round(min(vols.values()), 2) if vols else None,
           "max_written_volume_m3": round(max(vols.values()), 2) if vols else None,
           "sum_written_volume_m3": round(sum(vols.values()), 2) if vols else None}
    if diff.startswith("FAIL"):
        return rec

    run_ep(base_idf, epw, d / "base_out")
    run_ep(treat_idf, epw, d / "treat_out")
    b, t = read_run(d / "base_out"), read_run(d / "treat_out")
    rec["base_n_converge"] = _n_converge(d / "base_out")
    rec["treat_n_converge"] = _n_converge(d / "treat_out")
    for name, r in (("base", b), ("treat", t)):
        for k, v in r.items():
            rec["%s_%s" % (name, k)] = v
    if b["eui_kwh_m2"] and t["eui_kwh_m2"]:
        rec["delta_eui"] = t["eui_kwh_m2"] - b["eui_kwh_m2"]
        rec["pct_change"] = 100.0 * rec["delta_eui"] / b["eui_kwh_m2"]
    print("  done %-16s %-16s zones=%-4s base_eui=%-8s treat_eui=%-8s pct=%s"
          % (cell, stem, n_zones,
             None if b["eui_kwh_m2"] is None else round(b["eui_kwh_m2"], 2),
             None if t["eui_kwh_m2"] is None else round(t["eui_kwh_m2"], 2),
             rec.get("pct_change") and round(rec["pct_change"], 3)), flush=True)
    return rec


def main() -> int:
    if WORK.exists():
        shutil.rmtree(WORK, ignore_errors=True)
    WORK.mkdir(parents=True, exist_ok=True)

    jobs = []
    seen = set()
    for cell in CELLS:
        p = RESULTS / cell / "05_results.csv"
        if not p.exists():
            print("MISSING %s" % p)
            continue
        res = pd.read_csv(p)
        ok = sorted(res.loc[res["simulation_status"] == "success", "osm_id"]
                    .astype(str).str.replace("/", "_", regex=False))
        for stem in ok[:N_PER_CELL]:
            if (cell, stem) not in seen:
                seen.add((cell, stem))
                jobs.append((cell, stem, "cost"))
    for cell, stem in NONCONVERGED_SURVIVORS:
        if (cell, stem) in seen:
            # already in the cost arm; relabel rather than run twice
            jobs = [(c, s, "cost+nonconverged" if (c, s) == (cell, stem) else t)
                    for c, s, t in jobs]
        else:
            seen.add((cell, stem))
            jobs.append((cell, stem, "nonconverged"))

    print("sample: %d buildings, %d EnergyPlus runs, %d workers"
          % (len(jobs), 2 * len(jobs), WORKERS), flush=True)

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        rows = list(ex.map(_one, jobs))

    cov = _covariates()
    for r in rows:
        r.update({("cov_" + k): v for k, v in cov.get((r["cell"], r["stem"]), {}).items()})

    df = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / "open56_fleet_cost_stratified.csv"
    df.to_csv(dest, index=False)
    print("\nwrote %s" % dest)

    print("\n=== X01 CONTROL ===")
    have = df[df["diff_check"].astype(str).str.startswith("OK")]
    print("diff check OK: %d / %d" % (len(have), len(df)))
    if "base_vol_warnings" in have:
        print("baseline runs with the volume warning: %d / %d"
              % (int((have["base_vol_warnings"] > 0).sum()), len(have)))
        print("treated  runs with the volume warning: %d / %d"
              % (int((have["treat_vol_warnings"] > 0).sum()), len(have)))
        print("baseline completed: %d / %d ; treated completed: %d / %d"
              % (int(have["base_completed"].sum()), len(have),
                 int(have["treat_completed"].sum()), len(have)))

    ok = have[have["pct_change"].notna()] if "pct_change" in have else have.iloc[0:0]
    print("\n=== X01 COST, per cell ===")
    if not ok.empty:
        print(ok.groupby("cell")["pct_change"]
              .agg(["count", "mean", "median", "min", "max"]).round(3).to_string())
        print("\nfleet-stratified, all cells pooled:")
        print(ok["pct_change"].describe().round(4).to_string())
        print("\nsame-direction: %d / %d positive"
              % (int((ok["pct_change"] > 0).sum()), len(ok)))

    print("\n=== X02 what the cost scales with ===")
    if not ok.empty:
        for c in ("n_zones", "sum_written_volume_m3", "cov_levels", "cov_num_floors",
                  "base_floor_area_m2", "base_eui_kwh_m2"):
            if c in ok and ok[c].notna().sum() > 3:
                try:
                    print("  corr(delta_eui , %-24s) = %+.3f   corr(pct_change) = %+.3f"
                          % (c, ok["delta_eui"].corr(ok[c]), ok["pct_change"].corr(ok[c])))
                except Exception:                                        # noqa: BLE001
                    pass
        if "n_zones" in ok:
            per = ok["delta_eui"] / ok["n_zones"]
            print("\n  delta_eui per zone: mean %.4f  sd %.4f  cv %.3f"
                  % (per.mean(), per.std(), per.std() / per.mean() if per.mean() else float("nan")))
            print("  delta_eui         : mean %.4f  sd %.4f  cv %.3f"
                  % (ok["delta_eui"].mean(), ok["delta_eui"].std(),
                     ok["delta_eui"].std() / ok["delta_eui"].mean()))

    print("\n=== X03 is the non-convergence downstream of the stub? ===")
    nc = have[have["group"].astype(str).str.contains("nonconverged")]
    if not nc.empty:
        print(nc[["cell", "stem", "base_n_converge", "treat_n_converge",
                  "base_completed", "treat_completed"]].to_string(index=False))
        print("\n  baseline non-convergence warnings, total: %d"
              % int(nc["base_n_converge"].clip(lower=0).sum()))
        print("  treated  non-convergence warnings, total: %d"
              % int(nc["treat_n_converge"].clip(lower=0).sum()))
    else:
        print("  none ran")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
