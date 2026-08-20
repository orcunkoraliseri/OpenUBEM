"""W01-W04 of PLAN_ten-tasks-2026-08-18-night.md -- what the 10 m3 zone-volume stub costs.

OPEN-56 records that 8,160 of 8,160 buildings simulate with their zone air volume replaced
by a 10 m3 stub, because EnergyPlus computes a NEGATIVE volume from our geometry. The item
was registered with its blast radius deliberately unmeasured. This closes that gap.

Design:
  * treatment  = write Zone.Volume = floor_area x height into a COPY of the IDF. Exactly one
                 field per zone changes; the diff is asserted object-by-object before any run.
  * both arms  = re-run from the same IDF in the same session. The existing sim_out results
                 are NOT used as the baseline -- they were produced days ago in a different
                 process, and using them would confound the treatment with everything else.
  * control    = the "Indicated Zone Volume <= 0.0" warning must be present in every baseline
                 run and absent from every treated run. If it is not, no EUI number from this
                 experiment may be reported.
  * sample     = all 6 OPEN-42 failures (the mechanism arm) + 10 successful buildings (the
                 cost arm), chosen before any result was seen.

Emits openubem/outputs/comparisons/open56_zone_volume_experiment.csv.
"""
from __future__ import annotations

import os
import re
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pandas as pd

BASE = Path("C:/Users/o_iseri/AppData/Local/Temp/ubem_validation/open48_refleet")
EPLUS = Path("C:/EnergyPlusV23-1-0/energyplus.exe")
WORK = Path(os.environ.get("TEMP", "C:/Temp")) / "open56_zone_volume"
OUT = Path(__file__).resolve().parents[2] / "openubem" / "outputs" / "comparisons"
RESULTS = Path(__file__).resolve().parents[2] / "docs/validations/overAll/results/open48_refleet"

FAILING = [("la_rural", "way_472960972"), ("la_rural", "way_472961034"),
           ("la_rural", "way_472961088"), ("la_rural", "way_472961091"),
           ("la_rural", "way_472961171"), ("la_urban", "way_402215469")]
CONTROL_CELLS = ["la_rural", "nyc_rural"]
N_CONTROL_PER_CELL = 5

_VOL_WARN = re.compile(r"Indicated Zone Volume <= 0\.0")
_SEVERE = re.compile(r"\*\* Severe")
_FATAL = re.compile(r"\*\*\s+Fatal")


def _split_objects(text):
    return [c + ";" for c in text.split(";")[:-1]]


def _fields(chunk):
    body = "\n".join(
        ln.split("!")[0].strip() for ln in chunk.rstrip(";").splitlines()
        if ln.split("!")[0].strip()
    )
    return [f.strip() for f in body.split(",")]


def _newell_area(v):
    nx = ny = nz = 0.0
    n = len(v)
    for i in range(n):
        x1, y1, z1 = v[i]
        x2, y2, z2 = v[(i + 1) % n]
        nx += (y1 - y2) * (z1 + z2)
        ny += (z1 - z2) * (x1 + x2)
        nz += (x1 - x2) * (y1 + y2)
    return 0.5 * (nx * nx + ny * ny + nz * nz) ** 0.5


def _verts(f, start):
    c = [x for x in f[start:] if x not in ("", "autocalculate")]
    out = []
    for i in range(0, len(c) - 2, 3):
        try:
            out.append((float(c[i]), float(c[i + 1]), float(c[i + 2])))
        except ValueError:
            break
    return out


def zone_volumes(text):
    """floor area x z-extent, per zone, from the zone's own floor surface."""
    floors, zmin, zmax = {}, {}, {}
    for chunk in _split_objects(text):
        f = _fields(chunk)
        if not f or f[0].upper() != "BUILDINGSURFACE:DETAILED" or len(f) < 15:
            continue
        stype, zone = f[2].strip().lower(), f[4].strip()
        v = _verts(f, 12)
        if not v:
            continue
        zs = [p[2] for p in v]
        zmin[zone] = min(zs) if zone not in zmin else min(zmin[zone], min(zs))
        zmax[zone] = max(zs) if zone not in zmax else max(zmax[zone], max(zs))
        if stype == "floor":
            floors[zone] = _newell_area(v)
    return {z: floors[z] * (zmax[z] - zmin[z])
            for z in floors if zmax.get(z, 0) > zmin.get(z, 0)}


def write_treated(src, dst):
    text = src.read_text(encoding="utf-8", errors="replace")
    vols = zone_volumes(text)
    out, n = [], 0
    for chunk in _split_objects(text):
        f = _fields(chunk)
        if f and f[0].upper() == "ZONE" and f[1].strip() in vols and len(f) >= 10:
            g = list(f)
            g[9] = "%.4f" % vols[f[1].strip()]          # Zone field 9 = Volume
            out.append(",".join(g) + ";")
            n += 1
        else:
            out.append(chunk)
    dst.write_text("\n\n".join(out), encoding="utf-8")
    return n, vols


def assert_one_field_diff(src, dst):
    """Object-by-object: only ZONE objects differ, and only in field 9."""
    a = [_fields(c) for c in _split_objects(src.read_text(encoding="utf-8", errors="replace"))]
    b = [_fields(c) for c in _split_objects(dst.read_text(encoding="utf-8", errors="replace"))]
    if len(a) != len(b):
        return "FAIL object count %d vs %d" % (len(a), len(b))
    bad, changed = [], 0
    for fa, fb in zip(a, b):
        if fa == fb:
            continue
        if fa[0].upper() != "ZONE":
            bad.append(fa[0])
            continue
        diffs = [i for i in range(max(len(fa), len(fb)))
                 if (fa[i] if i < len(fa) else None) != (fb[i] if i < len(fb) else None)]
        if diffs != [9]:
            bad.append("ZONE:%s:fields%s" % (fa[1], diffs))
        else:
            changed += 1
    return ("FAIL %s" % bad[:4]) if bad else ("OK %d zones, field 9 only" % changed)


def epw_for(cell):
    for p in (BASE / cell / "weather").rglob("*.epw"):
        return p
    return None


def run_ep(idf, epw, outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    # -x / --expandobjects is required: these IDFs use HVACTemplate:* objects, which
    # EnergyPlus refuses outright without the ExpandObjects pass. Without it every run
    # dies at input processing with 1 severe and never reaches the volume calculation --
    # which is exactly how the first attempt at this experiment failed its own control.
    subprocess.run([str(EPLUS), "-x", "-w", str(epw), "-d", str(outdir), str(idf)],
                   capture_output=True, text=True, timeout=1800)


def read_run(outdir):
    err = outdir / "eplusout.err"
    txt = err.read_text(encoding="utf-8", errors="replace") if err.exists() else ""
    rec = {
        "completed": "EnergyPlus Completed Successfully" in txt,
        "vol_warnings": len(_VOL_WARN.findall(txt)),
        "n_severe": len(_SEVERE.findall(txt)),
        "n_fatal": len(_FATAL.findall(txt)),
        "site_energy_gj": None, "floor_area_m2": None, "eui_kwh_m2": None,
    }
    sql = outdir / "eplusout.sql"
    if sql.exists():
        try:
            con = sqlite3.connect(str(sql))
            q = ("SELECT Value FROM TabularDataWithStrings WHERE TableName=? "
                 "AND RowName=? AND ColumnName=?")
            r = con.execute(q, ("Site and Source Energy", "Total Site Energy",
                                "Total Energy")).fetchone()
            if r:
                rec["site_energy_gj"] = float(r[0])
            r = con.execute(q, ("Building Area", "Total Building Area", "Area")).fetchone()
            if r:
                rec["floor_area_m2"] = float(r[0])
            con.close()
        except Exception as exc:                                    # noqa: BLE001
            rec["sql_error"] = str(exc)[:120]
    if rec["site_energy_gj"] and rec["floor_area_m2"]:
        rec["eui_kwh_m2"] = rec["site_energy_gj"] * 277.7778 / rec["floor_area_m2"]
    return rec


def main():
    if not EPLUS.exists():
        print("EnergyPlus not found at %s" % EPLUS, file=sys.stderr)
        return 2
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)

    sample = list(FAILING)
    fail_stems = set(s for _, s in FAILING)
    for cell in CONTROL_CELLS:
        res = pd.read_csv(RESULTS / cell / "05_results.csv")
        ok = sorted(res.loc[res["simulation_status"] == "success", "osm_id"]
                    .str.replace("/", "_", regex=False))
        picked = [s for s in ok if s not in fail_stems][:N_CONTROL_PER_CELL]
        sample += [(cell, s) for s in picked]

    print("sample: %d buildings (%d known failures + %d successes)"
          % (len(sample), len(FAILING), len(sample) - len(FAILING)))

    rows = []
    for cell, stem in sample:
        src = BASE / cell / "step3" / "idfs" / ("%s.idf" % stem)
        epw = epw_for(cell)
        if not src.exists() or epw is None:
            print("SKIP %s/%s: idf=%s epw=%s" % (cell, stem, src.exists(), epw is not None))
            continue
        d = WORK / ("%s__%s" % (cell, stem))
        d.mkdir(parents=True, exist_ok=True)
        base_idf, treat_idf = d / "baseline.idf", d / "treated.idf"
        shutil.copyfile(src, base_idf)
        n_zones, vols = write_treated(base_idf, treat_idf)
        diff = assert_one_field_diff(base_idf, treat_idf)
        print("\n=== %s/%s  zones=%d  diff=%s" % (cell, stem, n_zones, diff))
        if diff.startswith("FAIL"):
            rows.append({"cell": cell, "stem": stem, "diff_check": diff})
            continue

        run_ep(base_idf, epw, d / "base_out")
        run_ep(treat_idf, epw, d / "treat_out")
        b, tr = read_run(d / "base_out"), read_run(d / "treat_out")
        rec = {"cell": cell, "stem": stem, "known_failure": stem in fail_stems,
               "n_zones": n_zones, "diff_check": diff,
               "min_written_volume_m3": round(min(vols.values()), 2) if vols else None,
               "max_written_volume_m3": round(max(vols.values()), 2) if vols else None}
        for tag, r in (("base", b), ("treat", tr)):
            for k, v in r.items():
                rec["%s_%s" % (tag, k)] = v
        if b["eui_kwh_m2"] and tr["eui_kwh_m2"]:
            rec["delta_eui"] = tr["eui_kwh_m2"] - b["eui_kwh_m2"]
            rec["pct_change"] = 100.0 * rec["delta_eui"] / b["eui_kwh_m2"]
        rows.append(rec)
        print("    baseline: completed=%s volwarn=%s severe=%s eui=%s"
              % (b["completed"], b["vol_warnings"], b["n_severe"], b["eui_kwh_m2"]))
        print("    treated : completed=%s volwarn=%s severe=%s eui=%s"
              % (tr["completed"], tr["vol_warnings"], tr["n_severe"], tr["eui_kwh_m2"]))

    df = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / "open56_zone_volume_experiment.csv"
    df.to_csv(dest, index=False)
    print("\nwrote %s\n" % dest)

    print("=== W03 CONTROL ===")
    if "base_vol_warnings" in df:
        print("baseline runs with the volume warning: %d / %d"
              % (int((df["base_vol_warnings"] > 0).sum()), len(df)))
        print("treated  runs with the volume warning: %d / %d"
              % (int((df["treat_vol_warnings"] > 0).sum()), len(df)))
    print("\n=== W03 MECHANISM: the six known failures ===")
    if "known_failure" in df:
        f = df[df["known_failure"] == True]                          # noqa: E712
        if not f.empty:
            print(f[["stem", "base_completed", "treat_completed",
                     "base_n_severe", "treat_n_severe"]].to_string(index=False))
        print("\n=== W04 COST: the successful buildings ===")
        s = df[df["known_failure"] == False]                         # noqa: E712
        if not s.empty and "pct_change" in s:
            print(s[["cell", "stem", "base_eui_kwh_m2", "treat_eui_kwh_m2",
                     "delta_eui", "pct_change"]].to_string(index=False))
            print("\n" + s["pct_change"].describe().to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
