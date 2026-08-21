"""PLAN_open61-census-open03-storeys-2026-08-20.md T05 -- OPEN-03 storey-count census, Arc B.

For every one of the 8,160 fleet buildings, record three storey counts side by side: what the
source data says (`levels`), what `auto` builds, and what `layout_assign` builds. NO SIMULATION is
run and NO per-building `layout_assign` IDF is generated -- Route 1 (a lookup), not Route 2
(generate-and-read), per the director's first-decision instruction. Why Route 1 is available and
correct, in order:

1. `layout_assign` selects one of 26 pre-built DOE-prototype baseline IDFs by archetype
   (`ARCHETYPE_IDF_MAP`, openubem/geometry/layout_assigner.py:23-61) and loads it as `self.idf`
   BEFORE any per-building geometry work (`_layout_assign_baseline_path` / `openubem/idf/builder.py:228-230`).
2. The only per-building operations applied to that loaded baseline are (a) `scale_baseline_idf`,
   which scales X/Y vertex coordinates by a planar factor and explicitly leaves Z UNCHANGED
   (`_GEOMETRY_SURFACE_CLASSES` docstring, layout_assigner.py:658-664), and (b) `match_storeys`,
   which -- when it applies at all -- writes ONLY the `Zone.Multiplier` field
   (layout_assigner.py:649, `z_obj.Multiplier = residual_multiplier`); grepped fleet-wide, this is
   the ONLY `.Multiplier =` write in `openubem/geometry/*.py` or `openubem/idf/*.py`. Neither
   operation ever adds a wall surface at a new Z elevation.
3. Therefore the GEOMETRY-measured storey count (distinct wall Z elevations, defined identically
   to the predecessor script -- see below) of a `layout_assign` IDF is a function of the ARCHETYPE
   ALONE, not of the individual building's `num_floors` input. This was verified empirically before
   writing this script: joining `open03_envelope_decomposition.csv`'s 48-sample against archetype,
   `storey_count` has `nunique==1` per archetype for every one of the 7 baseline-mapped archetypes
   present in that sample (MidriseApartment, SmallOffice, LargeOffice, MediumOffice, LargeHotel,
   Warehouse, RetailStandalone).
4. For the 2 archetypes with NO baseline mapping in this fleet (`Courthouse`, `OpenUBEMUnknown`),
   `builder.py`'s `layout_assign` branch degrades to the plain "auto" zoning pipeline on the exact
   same inputs (footprint, archetype, num_floors) as the real auto build
   (`openubem/idf/builder.py:468-475`, tag `layout_assign_fallback_auto`) -- verified exactly equal,
   per-building, on all 5 Courthouse/OpenUBEMUnknown rows of the 48-sample (both arms' storey_count
   identical to the row).

So: for the 18 baseline-mapped archetypes present in this fleet, `layout_assign` storey_count is
looked up ONCE per archetype from that archetype's own baseline IDF (loaded via geomeppy, saved once
to reformat vertices, then parsed with the SAME regex method as the predecessor script -- the raw
baseline library files on disk use a different vertex-comment format
(`!- X,Y,Z ==> Vertex N {m}`, one line per vertex) than the fleet's own eppy-saved IDFs
(`!- Vertex N Xcoordinate`, one line per axis), so the raw files must be re-saved through geomeppy
once before the predecessor's regex can read them -- this is a geometry-only `.save()`, not a
simulation). For the 2 non-mapped archetypes, `layout_assign` storey_count = that SAME building's
own `auto` storey_count (no lookup needed, no simulation, no generation).

`auto` storey_count is read directly off the 8,160 real, on-disk auto-arm IDFs
(`evidence/open48_refleet4/<cell>/fleet_staging/idfs/*.idf`) with the SAME parser.

storey_count DEFINITION -- reused VERBATIM from
scripts/analysis/open03_envelope_decomposition_2026-08-20.py (required for C9 to reproduce that
file's own numbers exactly): distinct min-Z elevations (rounded to 0.1 m) among Surface Type "wall"
objects belonging to zones whose ZONE field "Part of Total Floor Area" != "No". Debug-reference
chapter 16 (object-boundary parsing bug, Attic-zone floor double-count) was read before writing this
script; the Attic exclusion the predecessor script already carries is preserved here by importing
its `parse_idf()` unchanged rather than reimplementing it.

*** CAVEAT, discovered while building this census -- FIXED 2026-08-20 (T01/T02,
PLAN_open62-z-origin-and-three-rulings-2026-08-20.md), then found INSUFFICIENT the same day
(T02/CP-2), then PARTIALLY ADDRESSED (T06). Registered in OpenUBEM_debug_References.md chapter 16.
Do not read this as still-open in its original form -- it has moved twice: ***

Symptom 1 (fixed, T01/ruling R1): the wall-vertex method above did not add each zone's own
Z_Origin when GlobalGeometryRules Coordinate System == Relative, so it under-read storey_count for
any archetype whose baseline encodes a repeated floor band's elevation in the ZONE object's own
Z_Origin field while every wall vertex stays LOCAL (near Z=0) to that origin. Measured zone-by-zone
across all 18 baseline-mapped archetypes: SEVERE in MidriseApartment (18/27 zones),
HighriseApartment (18/27), TallBuilding (145/164), SuperTallBuilding (232/256), Outpatient
(59/118), SecondarySchool (21/46) -- 2,983 of 8,160 buildings (36.6 %). `parse_idf()`
(`open03_envelope_decomposition_2026-08-20.py:118-236`) now reads GlobalGeometryRules' Coordinate
System and each ZONE's own X/Y/Z Origin and adds it back into the wall-vertex minimum, additively:
`storey_count` is the corrected value, `storey_count_naive` (this CSV's
`layout_assign_storey_count_naive`) is the untouched pre-fix value, byte-identical to the original
`open03_storey_census.csv` (C9a, 8,160/8,160). At the whole-building level only 4 of those 6
archetypes actually moved (HighriseApartment, MidriseApartment, SuperTallBuilding, TallBuilding);
Outpatient and SecondarySchool hold at delta 0 because their mixed wall-vertex encodings put the
corrected band on top of a band the naive set already held (CP-1's amendment to the register's
6-move/12-hold prediction).

Symptom 2 (found by the very control the fix was checked against, T02/CP-2, and NOT fully fixed):
even origin-corrected, `layout_assign_storey_count` is not a storey count -- it is the number of
distinct base elevations of EXTERIOR walls in floor-area-counting zones, which only equals the true
storey count when every floor starts its own facade. A curtain wall spanning several floors
contributes one elevation, not several. Checked against `layout_assigner.compute_band_map()`
(FLOOR-surface bands, already origin-aware, never imported `parse_idf()`), the corrected value
agrees on only 12 of 18 archetypes; 6 disagree over 3,734 buildings fleet-wide (`TallBuilding` 11 v
20, `SuperTallBuilding` 16 v 30, `Warehouse` 2 v 1, and 1 v 2 on `FullServiceRestaurant` /
`QuickServiceRestaurant` / `SmallOffice`). Any value read from `layout_assign_storey_count` is a
LOWER BOUND, not a value.

Symptom 2's remedy (T06, ruling R7 -- "a storey count is to be derived from FLOOR SURFACES"):
`layout_assign_storey_count_floor` in this CSV counts distinct origin-corrected elevations among
ALL FLOOR-surface objects, unfiltered by zone (R7's own definition carries no zone filter). See
control C14 in this script's own output and the T06 report for its agreement rate against
`compute_band_map()`'s `n_proto` over the 18 baseline-mapped archetypes.
`layout_assign_storey_count` and `layout_assign_storey_count_naive` are unchanged by T06 (additive
only); `layout_assign_z_origin_collapse_risk` still flags the 6 archetypes named under Symptom 1,
which is a DIFFERENT set of archetypes from Symptom 2's 6 -- do not conflate the two flags.
"""
import csv
import importlib.util
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

AUTO_ROOT = os.path.join(REPO, "evidence", "open48_refleet4")
RESULTS_ROOT = AUTO_ROOT
OUT_CSV = os.path.join(REPO, "openubem", "outputs", "comparisons", "open03_storey_census_zfix.csv")
PRE_FIX_CSV = os.path.join(REPO, "openubem", "outputs", "comparisons", "open03_storey_census.csv")
ENV_DECOMP_CSV = os.path.join(REPO, "openubem", "outputs", "comparisons", "open03_envelope_decomposition.csv")
SCRATCH_PROTO_DIR = os.path.join(
    r"C:\Users\o_iseri\AppData\Local\Temp\claude\C--Users-o-iseri-Desktop-OpenUBEM",
    "89a28ab2-bc04-4d19-9e55-89a800c96691", "scratchpad", "open03_proto_saved",
)

CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]

# ---- reuse the predecessor's exact storey_count / parse_idf method (PLAN_open62-z-origin-and-
# three-rulings-2026-08-20.md T02, ruling R1: the fix and the restated C9 land in the same task,
# so this script imports parse_idf() -- now origin-aware, additive per D1 -- rather than
# reimplementing it, exactly as before) ----
_spec = importlib.util.spec_from_file_location(
    "open03env", os.path.join(REPO, "scripts", "analysis", "open03_envelope_decomposition_2026-08-20.py")
)
envmod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(envmod)

import pandas as pd  # noqa: E402
from openubem.idf.builder import GeomIDF  # noqa: E402  (also locks the IDD, builder.py:50-53)
from openubem.geometry.layout_assigner import get_registry, compute_band_map, match_storeys  # noqa: E402

ZONE_MULT_RE = re.compile(r'^\s*ZONE\s*,', re.IGNORECASE)

# Archetypes whose baseline was measured (module docstring) to encode floor-band elevation in the
# ZONE Z_Origin field while wall vertices stay local (~0) to it -- the naive wall-Z-band method
# under-reads storey_count for these, severely. Not a guess: counted zone-by-zone against each
# baseline's own ZONE/BUILDINGSURFACE:DETAILED objects.
Z_ORIGIN_COLLAPSE_RISK_ARCHETYPES = {
    "MidriseApartment", "HighriseApartment", "TallBuilding", "SuperTallBuilding",
    "Outpatient", "SecondarySchool",
}


def zone_multiplier_gt1(idf_path):
    """Returns (any_gt1: bool, max_value: float|None) by reading ZONE objects' Multiplier field
    directly out of the IDF text -- same block-splitting convention as parse_idf()."""
    txt = open(idf_path, encoding="utf-8", errors="replace").read()
    blocks = envmod.split_blocks(txt)
    vals = []
    for b in blocks:
        if not ZONE_MULT_RE.match(b):
            continue
        for ln in b.split("\n"):
            if "!- Multiplier" in ln:
                raw = ln.split(",")[0].strip()
                try:
                    v = float(raw)
                except ValueError:
                    continue
                vals.append(v)
    gt1 = [v for v in vals if v > 1]
    return (len(gt1) > 0, max(gt1) if gt1 else None)


def main():
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    os.makedirs(SCRATCH_PROTO_DIR, exist_ok=True)

    # ---- 1. source data: archetype + levels (source storey count), all 8,160 rows ----
    src_frames = []
    for cell in CELLS:
        df = pd.read_csv(
            os.path.join(RESULTS_ROOT, cell, "results", "05_results.csv"),
            dtype={"osm_id": str},
        )
        df["cell"] = cell
        df["osm_id_key"] = df["osm_id"].str.replace("/", "_", regex=False)
        src_frames.append(df[["cell", "osm_id_key", "osm_id", "archetype_id", "levels", "simulation_status"]])
    src = pd.concat(src_frames, ignore_index=True)
    print(f"[1] source rows (05_results.csv, all cells) = {len(src)}")
    assert src["levels"].isna().sum() == 0, "unexpected NaN in levels -- source storey count must be always-present"

    # ---- 2. auto arm: storey_count + zone-multiplier check, read off all 8,160 on-disk IDFs ----
    auto_rows = {}
    n_auto = 0
    for cell in CELLS:
        idf_dir = os.path.join(AUTO_ROOT, cell, "fleet_staging", "idfs")
        for fn in sorted(os.listdir(idf_dir)):
            if not fn.endswith(".idf"):
                continue
            osm_id_key = fn[:-4]
            path = os.path.join(idf_dir, fn)
            d = envmod.parse_idf(path)
            gt1, maxval = zone_multiplier_gt1(path)
            auto_rows[(cell, osm_id_key)] = {
                "auto_storey_count": d["storey_count"],
                # internal only, not a CSV column (T02 scopes the new column to
                # layout_assign_storey_count_naive) -- used below to derive the naive value
                # for the 2 no-baseline archetypes, which copy the auto arm's count either way.
                "auto_storey_count_naive": d["storey_count_naive"],
                # internal only, not a CSV column (T06 scopes the new column to
                # layout_assign_storey_count_floor) -- used below for the 2 no-baseline archetypes.
                "auto_storey_count_floor": d["storey_count_floor"],
                "auto_attic_zone_count": d["attic_zone_count"],
                "auto_zone_multiplier_gt1": gt1,
                "auto_zone_multiplier_max": maxval,
            }
            n_auto += 1
    print(f"[2] auto-arm IDFs parsed = {n_auto}")

    # ---- 3. layout_assign per-archetype lookup table (18 baseline-mapped archetypes) ----
    fleet_archetypes = sorted(src["archetype_id"].unique().tolist())
    reg = get_registry()
    la_lookup = {}  # archetype -> {"storey_count": int, "band_map": dict, "no_baseline": bool}
    for arch in fleet_archetypes:
        baseline_path = reg.get_baseline_idf(arch)
        if baseline_path is None:
            la_lookup[arch] = {"no_baseline": True}
            continue
        saved_path = os.path.join(SCRATCH_PROTO_DIR, arch + ".idf")
        idf = GeomIDF(str(baseline_path))
        idf.save(saved_path)
        d = envmod.parse_idf(saved_path)
        band_idf = GeomIDF(str(baseline_path))
        band_map = compute_band_map(band_idf)
        la_lookup[arch] = {
            "no_baseline": False,
            "storey_count": d["storey_count"],
            "storey_count_naive": d["storey_count_naive"],
            "storey_count_floor": d["storey_count_floor"],
            "storey_count_floor_zonefiltered": d["storey_count_floor_zonefiltered"],
            "baseline_filename": baseline_path.name,
            "band_idf": band_idf,
            "band_map": band_map,
        }
        print(f"[3] {arch:28s} baseline={baseline_path.name:55s} "
              f"storey_count={d['storey_count']} naive={d['storey_count_naive']} "
              f"floor={d['storey_count_floor']} floor_zonefiltered={d['storey_count_floor_zonefiltered']} "
              f"n_proto={band_map['n_proto']}")

    no_baseline_archs = sorted(a for a, v in la_lookup.items() if v["no_baseline"])
    print(f"[3] no-baseline archetypes (fall back to auto, per-building): {no_baseline_archs}")

    # ---- 4. assemble the census ----
    rows = []
    n_missing_auto = 0
    for _, srow in src.iterrows():
        cell = srow["cell"]
        osm_id_key = srow["osm_id_key"]
        arch = srow["archetype_id"]
        levels = max(1, int(float(srow["levels"])))  # mirrors derive_num_floors()'s levels branch exactly

        a = auto_rows.get((cell, osm_id_key))
        if a is None:
            n_missing_auto += 1
            continue

        lk = la_lookup[arch]
        if lk["no_baseline"]:
            la_storey_count = a["auto_storey_count"]
            la_storey_count_naive = a["auto_storey_count_naive"]
            la_storey_count_floor = a["auto_storey_count_floor"]
            la_mult_gt1 = a["auto_zone_multiplier_gt1"]
            la_mult_val = a["auto_zone_multiplier_max"]
            la_match_status = "no_baseline_fallback_auto"
            no_baseline_fallback = True
        else:
            la_storey_count = lk["storey_count"]
            la_storey_count_naive = lk["storey_count_naive"]
            la_storey_count_floor = lk["storey_count_floor"]
            mr = match_storeys(lk["band_idf"], levels, lk["band_map"])
            la_match_status = mr["status"]
            mult = mr.get("multiplier")
            la_mult_gt1 = bool(mr["status"] == "applied" and mult and mult > 1)
            la_mult_val = mult if (mult and mult > 1) else None
            no_baseline_fallback = False

        rows.append({
            "cell": cell,
            "osm_id": srow["osm_id"],
            "archetype_id": arch,
            "source_storey_count": levels,
            "auto_storey_count": a["auto_storey_count"],
            "layout_assign_storey_count": la_storey_count,
            "layout_assign_storey_count_naive": la_storey_count_naive,
            "layout_assign_storey_count_floor": la_storey_count_floor,
            "agree": bool(la_storey_count == a["auto_storey_count"]),
            "diff_layout_assign_minus_auto": la_storey_count - a["auto_storey_count"],
            "layout_assign_no_baseline_fallback": no_baseline_fallback,
            "layout_assign_match_storeys_status": la_match_status,
            "auto_zone_multiplier_gt1": a["auto_zone_multiplier_gt1"],
            "auto_zone_multiplier_max": a["auto_zone_multiplier_max"],
            "layout_assign_zone_multiplier_gt1": la_mult_gt1,
            "layout_assign_zone_multiplier_max": la_mult_val,
            "auto_attic_zone_count": a["auto_attic_zone_count"],
            "layout_assign_z_origin_collapse_risk": arch in Z_ORIGIN_COLLAPSE_RISK_ARCHETYPES,
        })

    print(f"[4] rows assembled = {len(rows)}  missing_auto_join = {n_missing_auto}")

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"[csv] wrote {len(rows)} rows -> {OUT_CSV}")

    df = pd.DataFrame(rows)

    # ---- C8: row count 8,160, per-cell n sums to 8,160 ----
    print("\n[C8] row count check")
    print(f"[C8] total rows = {len(df)} (expect 8160)")
    per_cell = df.groupby("cell").size()
    print(per_cell.to_string())
    print(f"[C8] per-cell sum = {per_cell.sum()} (expect 8160)")
    c8_pass = (len(df) == 8160) and (per_cell.sum() == 8160)
    print(f"[C8] {'PASS' if c8_pass else 'FAIL'}")

    # ---- C9a: restated legacy control, fleet scale (PLAN_open62-z-origin-and-three-rulings-
    # 2026-08-20.md T02, ruling R1). layout_assign_storey_count_naive must reproduce the pre-fix
    # open03_storey_census.csv's layout_assign_storey_count exactly, 8,160/8,160 -- proves the fix
    # is additive at fleet scale, the same way T01's C9a proved it on the 48-building sample. ----
    print("\n[C9a] legacy fleet-scale reproduction check against pre-fix open03_storey_census.csv")
    prefix_df = pd.read_csv(PRE_FIX_CSV, dtype={"osm_id": str})
    c9a_joined = prefix_df.merge(df, on=["cell", "osm_id"], suffixes=("_prefix", "_zfix"))
    print(f"[C9a] matched {len(c9a_joined)} of {len(prefix_df)} pre-fix rows (expect 8160/8160)")
    c9a_mismatch = c9a_joined[
        c9a_joined["layout_assign_storey_count_prefix"] != c9a_joined["layout_assign_storey_count_naive"]
    ]
    print(f"[C9a] mismatches = {len(c9a_mismatch)} / {len(c9a_joined)}")
    if len(c9a_mismatch):
        print(c9a_mismatch[["cell", "osm_id", "archetype_id_zfix",
                             "layout_assign_storey_count_prefix", "layout_assign_storey_count_naive"]]
              .head(20).to_string())
    c9a_pass = (len(c9a_joined) == 8160) and (len(c9a_mismatch) == 0)
    print(f"[C9a] {'PASS' if c9a_pass else 'FAIL -- STOP, do not reconcile silently'}")

    # ---- C9b: the restated control, D2. Checks the corrected layout_assign_storey_count
    # (parse_idf, wall-Z bands) against a reader that NEVER imported parse_idf():
    # layout_assigner.py's own compute_band_map() (FLOOR-surface bands, already origin-aware,
    # layout_assigner.py:465-495), over the 18 baseline-mapped archetypes. ALLOWED TO FAIL. ----
    print("\n[C9b] independent-reader check: layout_assign_storey_count (wall-Z, parse_idf) vs "
          "compute_band_map n_proto (FLOOR-surface, origin-aware), 18 baseline-mapped archetypes")
    c9b_rows = []
    for arch, lk in sorted(la_lookup.items()):
        if lk["no_baseline"]:
            continue
        n_proto = lk["band_map"]["n_proto"]
        sc = lk["storey_count"]
        c9b_rows.append({
            "archetype_id": arch,
            "layout_assign_storey_count": sc,
            "band_map_n_proto": n_proto,
            "agree": sc == n_proto,
        })
    c9b_df = pd.DataFrame(c9b_rows)
    n_agree = int(c9b_df["agree"].sum())
    print(f"[C9b] agreement = {n_agree} / {len(c9b_df)} archetypes")
    print(c9b_df.to_string(index=False))
    disagree_df = c9b_df[~c9b_df["agree"]]
    if len(disagree_df):
        disagree_archs = set(disagree_df["archetype_id"])
        n_bldgs = int(df[df["archetype_id"].isin(disagree_archs)].shape[0])
        print(f"[C9b] disagreement covers {len(disagree_archs)} archetypes, {n_bldgs} buildings fleet-wide")
        ex = df[df["archetype_id"].isin(disagree_archs)].iloc[0]
        print(f"[C9b] worked example: osm_id={ex['osm_id']} cell={ex['cell']} archetype={ex['archetype_id']} "
              f"layout_assign_storey_count={ex['layout_assign_storey_count']}")
    c9b_pass = (n_agree == len(c9b_df))
    print(f"[C9b] {'PASS' if c9b_pass else 'ALLOWED TO FAIL -- reported honestly, not reconciled'}")

    # ---- C10: fleet-wide disagreement rate, direction, breakdown by archetype/cell ----
    print("\n[C10] fleet-wide disagreement")
    n_disagree = (~df["agree"]).sum()
    print(f"[C10] disagree = {n_disagree} / {len(df)} = {n_disagree/len(df)*100:.2f}%")
    taller_la = (df["diff_layout_assign_minus_auto"] > 0).sum()
    taller_auto = (df["diff_layout_assign_minus_auto"] < 0).sum()
    equal_n = (df["diff_layout_assign_minus_auto"] == 0).sum()
    print(f"[C10] layout_assign taller = {taller_la} ({taller_la/len(df)*100:.2f}%)")
    print(f"[C10] auto taller          = {taller_auto} ({taller_auto/len(df)*100:.2f}%)")
    print(f"[C10] equal                = {equal_n} ({equal_n/len(df)*100:.2f}%)")
    print(f"[C10] mean signed diff (layout_assign - auto) = {df['diff_layout_assign_minus_auto'].mean():.4f}")
    print(f"[C10] median signed diff = {df['diff_layout_assign_minus_auto'].median():.4f}")

    print("\n[C10] by archetype")
    arch_g = df.groupby("archetype_id").agg(
        n=("agree", "size"),
        disagree_n=("agree", lambda s: (~s).sum()),
        mean_diff=("diff_layout_assign_minus_auto", "mean"),
    )
    arch_g["disagree_pct"] = arch_g["disagree_n"] / arch_g["n"] * 100.0
    print(arch_g.to_string())

    print("\n[C10] risk split (layout_assign_z_origin_collapse_risk)")
    risk_g = df.groupby("layout_assign_z_origin_collapse_risk").agg(
        n=("agree", "size"),
        disagree_n=("agree", lambda s: (~s).sum()),
        mean_diff=("diff_layout_assign_minus_auto", "mean"),
    )
    risk_g["disagree_pct"] = risk_g["disagree_n"] / risk_g["n"] * 100.0
    print(risk_g.to_string())

    print("\n[C10] by cell")
    cell_g = df.groupby("cell").agg(
        n=("agree", "size"),
        disagree_n=("agree", lambda s: (~s).sum()),
        mean_diff=("diff_layout_assign_minus_auto", "mean"),
    )
    cell_g["disagree_pct"] = cell_g["disagree_n"] / cell_g["n"] * 100.0
    print(cell_g.to_string())

    # ---- C11: Zone.Multiplier > 1 usage, both arms, fleet-wide ----
    print("\n[C11] Zone.Multiplier > 1 usage, fleet-wide")
    auto_mult_n = df["auto_zone_multiplier_gt1"].sum()
    la_mult_n = df["layout_assign_zone_multiplier_gt1"].sum()
    print(f"[C11] auto:          {auto_mult_n} / {len(df)}  (F7 sample: 0/48)")
    print(f"[C11] layout_assign: {la_mult_n} / {len(df)}  (F7 sample: 2/48)")
    if la_mult_n:
        print(df[df["layout_assign_zone_multiplier_gt1"]][
            ["cell", "osm_id", "archetype_id", "source_storey_count", "layout_assign_zone_multiplier_max"]
        ].to_string())

    # ---- C12: fleet-scale mechanism check, carried from T01 -- storey_count vs
    # storey_count_naive per archetype, 18 baseline-mapped archetypes, with building counts.
    # CP-1 amended the register's 6-move/12-hold prediction to 4-move/14-hold. ----
    print("\n[C12] fleet-scale: storey_count vs storey_count_naive by archetype")
    arch_counts = df["archetype_id"].value_counts()
    moved = []
    held = []
    for arch, lk in sorted(la_lookup.items()):
        if lk["no_baseline"]:
            continue
        delta = lk["storey_count"] - lk["storey_count_naive"]
        n_bldg = int(arch_counts.get(arch, 0))
        print(f"  {arch:28s} naive={lk['storey_count_naive']:3d} corrected={lk['storey_count']:3d} "
              f"delta={delta:+3d} n_buildings={n_bldg}")
        (moved if delta != 0 else held).append(arch)
    print(f"[C12] moved ({len(moved)}): {moved}")
    print(f"[C12] held  ({len(held)}): {held}")
    c12_expected_move = {"HighriseApartment", "MidriseApartment", "SuperTallBuilding", "TallBuilding"}
    c12_pass = set(moved) == c12_expected_move
    print(f"[C12] CP-1 amended expectation (4 move / 14 hold): "
          f"{'PASS' if c12_pass else 'MISMATCH -- report, do not adjust'}")

    # ---- C14 (T06, ruling R7): storey_count_floor (parse_idf(), FLOOR-surface bands, unfiltered
    # by zone) vs compute_band_map()'s n_proto (FLOOR-surface bands, production code, already
    # origin-aware, never imported parse_idf()) -- two independently implemented floor-surface
    # readers, over all 18 baseline-mapped archetypes. Named C14 targets (from CP-2's own
    # "Floor surfaces (the independent reader)" measurement on TallBuilding.idf): TallBuilding 20,
    # SuperTallBuilding 30, Warehouse 1, FullServiceRestaurant/QuickServiceRestaurant/SmallOffice 2.
    print("\n[C14] storey_count_floor (parse_idf, FLOOR-surface, unfiltered) vs "
          "compute_band_map n_proto (FLOOR-surface, production), 18 baseline-mapped archetypes")
    c14_targets = {
        "TallBuilding": 20, "SuperTallBuilding": 30, "Warehouse": 1,
        "FullServiceRestaurant": 2, "QuickServiceRestaurant": 2, "SmallOffice": 2,
    }
    c14_rows = []
    for arch, lk in sorted(la_lookup.items()):
        if lk["no_baseline"]:
            continue
        n_proto = lk["band_map"]["n_proto"]
        sf = lk["storey_count_floor"]
        c14_rows.append({
            "archetype_id": arch,
            "storey_count_floor": sf,
            "band_map_n_proto": n_proto,
            "agree": sf == n_proto,
            "named_target": c14_targets.get(arch),
            "meets_named_target": (c14_targets.get(arch) is None) or (sf == c14_targets[arch]),
        })
    c14_df = pd.DataFrame(c14_rows)
    n_agree_14 = int(c14_df["agree"].sum())
    print(f"[C14] agreement (storey_count_floor == band_map_n_proto) = {n_agree_14} / {len(c14_df)} archetypes")
    print(c14_df.to_string(index=False))
    c14_named = c14_df[c14_df["named_target"].notna()]
    n_named_ok = int(c14_named["meets_named_target"].sum())
    print(f"[C14] named targets met = {n_named_ok} / {len(c14_named)}")
    c14_disagree = c14_df[~c14_df["agree"]]
    if len(c14_disagree):
        print(f"[C14] disagreeing with band_map_n_proto ({len(c14_disagree)}): "
              f"{c14_disagree['archetype_id'].tolist()}")
    c14_pass = (n_agree_14 == len(c14_df))
    print(f"[C14] {'PASS' if c14_pass else 'MISMATCH -- reported honestly, not reconciled'}")

    # ---- C13: restate OPEN-03's published storey headline on the corrected counts.
    # Old numbers verbatim from the register: matched 2,446 (30.0%), unmatched 5,714 (70.0%),
    # unmatched real mean 3.12 (max 105), unmatched built mean 1.21 (max 6). ----
    print("\n[C13] OPEN-03 headline restatement (old -> new)")
    matched_status = {"identity", "applied", "no_baseline_fallback_auto"}
    is_matched = df["layout_assign_match_storeys_status"].isin(matched_status)
    n_matched = int(is_matched.sum())
    n_unmatched = int((~is_matched).sum())
    pct_matched = n_matched / len(df) * 100.0
    pct_unmatched = n_unmatched / len(df) * 100.0
    unmatched = df[~is_matched]
    real_mean = float(unmatched["source_storey_count"].mean())
    real_max = int(unmatched["source_storey_count"].max())
    built_mean = float(unmatched["layout_assign_storey_count"].mean())
    built_max = int(unmatched["layout_assign_storey_count"].max())
    print(f"[C13] matched:    old 2,446 (30.0%)  ->  new {n_matched} ({pct_matched:.1f}%)  "
          f"delta {n_matched - 2446:+d}")
    print(f"[C13] unmatched:  old 5,714 (70.0%)  ->  new {n_unmatched} ({pct_unmatched:.1f}%)  "
          f"delta {n_unmatched - 5714:+d}")
    print(f"[C13] real mean:  old 3.12  ->  new {real_mean:.2f}  delta {real_mean - 3.12:+.2f}")
    print(f"[C13] real max:   old 105   ->  new {real_max}  delta {real_max - 105:+d}")
    print(f"[C13] built mean: old 1.21  ->  new {built_mean:.2f}  delta {built_mean - 1.21:+.2f}")
    print(f"[C13] built max:  old 6     ->  new {built_max}  delta {built_max - 6:+d}")
    print("[C13] CP-2: this restatement (and any restatement using layout_assign_storey_count, "
          "the wall-base method) is a LOWER BOUND, not a value -- see C17 for the floor-surface "
          "restatement.")

    # ---- C16 (T06): storey_count_floor >= storey_count on every row. ALLOWED TO FAIL -- a
    # violation would mean the undercounting story is incomplete, which is reported, not fixed. ----
    print("\n[C16] layout_assign_storey_count_floor >= layout_assign_storey_count, every row")
    c16_bad = df[df["layout_assign_storey_count_floor"] < df["layout_assign_storey_count"]]
    print(f"[C16] violations = {len(c16_bad)} / {len(df)}")
    c16_pass = len(c16_bad) == 0
    if len(c16_bad):
        print(c16_bad[["cell", "osm_id", "archetype_id", "layout_assign_storey_count",
                        "layout_assign_storey_count_floor"]].head(20).to_string())
        print(f"[C16] one osm_id: {c16_bad.iloc[0]['osm_id']}")
    print(f"[C16] {'PASS' if c16_pass else 'FAIL -- ALLOWED, reported, not reconciled'}")

    # ---- C17 (T06): restate C13's built mean/max using layout_assign_storey_count_floor, stated
    # as VALUES (per R7/T06), against the lower bounds C13 could only state as >= 2.25 / >= 16. ----
    print("\n[C17] restate C13's built mean/max with layout_assign_storey_count_floor")
    built_mean_floor = float(unmatched["layout_assign_storey_count_floor"].mean())
    built_max_floor = int(unmatched["layout_assign_storey_count_floor"].max())
    print(f"[C17] built mean (floor-surface): {built_mean_floor:.2f}  (C13 lower bound >= 2.25)")
    print(f"[C17] built max  (floor-surface): {built_max_floor}  (C13 lower bound >= 16)")

    print("\nDONE")
    return 0 if (c8_pass and c9a_pass and c12_pass and c14_pass) else 1


if __name__ == "__main__":
    raise SystemExit(main())
