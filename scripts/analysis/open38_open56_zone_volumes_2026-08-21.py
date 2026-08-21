"""OPEN-38 x OPEN-56 T07 -- are the 44 fatals volume-anomalous?

Measurement only. Reads per-zone Volume {m3} straight out of the .eio files of
the 44 fatal buildings (no re-simulation needed, F5) and of a matched control,
flags volume-degenerate zones, and joins to the OPEN-56 err census on
(cell, stem) to test whether has_volstub co-occurs with fatality.
"""
import csv
import random
import sqlite3
from pathlib import Path

import pandas as pd

HARVEST_ROOT = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest")
FATAL_CSV = "openubem/outputs/comparisons/open38_fatal_causes_2026-08-20.csv"
ERR_CENSUS_CSV = "openubem/outputs/comparisons/open56_open09_run4_err_census_2026-08-20.csv"
OUT_ZONE_CSV = "openubem/outputs/comparisons/open38_open56_zone_volumes_2026-08-21.csv"
OUT_BLDG_CSV = "openubem/outputs/comparisons/open38_open56_zone_volumes_by_building_2026-08-21.csv"

CONTROL_N = 200
SEED = 2026


def parse_eio_zone_information(eio_path: Path):
    header_fields = None
    rows = []
    with open(eio_path, "r", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("! <Zone Information>"):
                parts = line.split(",")
                header_fields = [p.strip().lstrip("!").strip() for p in parts]
                header_fields[0] = "label"
                continue
            if line.startswith(" Zone Information,") or line.startswith("Zone Information,"):
                if header_fields is None:
                    raise RuntimeError(f"data row before header in {eio_path}")
                parts = line.split(",")
                parts = [p.strip() for p in parts]
                if len(parts) != len(header_fields):
                    continue
                row = dict(zip(header_fields, parts))
                rows.append(row)
    return rows


def to_float(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def build_zone_rows(cell, mode, stem, group):
    eio_path = HARVEST_ROOT / f"{cell}_{mode}" / stem / "eplusout.eio"
    if not eio_path.exists():
        return [], f"missing_eio:{eio_path}"
    zone_rows = parse_eio_zone_information(eio_path)
    if not zone_rows:
        return [], "eio_present_no_zone_rows"
    out = []
    for zr in zone_rows:
        zone_name = zr.get("Zone Name")
        volume = to_float(zr.get("Volume {m3}"))
        floor_area = to_float(zr.get("Floor Area {m2}"))
        multiplier = to_float(zr.get("Zone Multiplier"))
        ceiling_height = to_float(zr.get("Ceiling Height {m}"))
        degenerate = False
        if volume is None or volume <= 0:
            degenerate = True
        elif floor_area is not None and ceiling_height is not None:
            expected = floor_area * ceiling_height
            if volume != 0 and abs(volume - expected) / abs(volume) > 0.01:
                degenerate = True
        out.append({
            "group": group,
            "cell": cell,
            "mode": mode,
            "stem": stem,
            "zone_name": zone_name,
            "volume_m3": volume,
            "floor_area_m2": floor_area,
            "multiplier": multiplier,
            "ceiling_height_m": ceiling_height,
            "volume_degenerate": degenerate,
        })
    return out, None


def normalise_stem(s: str) -> str:
    return s.lower().replace("/", "_")


def main():
    total_dirs = 0
    total_has_eio = 0
    for combo_dir in HARVEST_ROOT.iterdir():
        if not combo_dir.is_dir():
            continue
        for sub in combo_dir.iterdir():
            if not sub.is_dir():
                continue
            total_dirs += 1
            if (sub / "eplusout.eio").exists():
                total_has_eio += 1
    print("=== whole-harvest .eio coverage (context for F5) ===")
    print(f"total directories: {total_dirs}; have eplusout.eio: {total_has_eio} "
          f"({100*total_has_eio/total_dirs:.2f}% )")
    print()

    fatal_df = pd.read_csv(FATAL_CSV)
    assert len(fatal_df) == 44, f"C23: expected 44 fatal rows, got {len(fatal_df)}"
    fatal_triples = list(fatal_df[["cell", "mode", "stem"]].itertuples(index=False, name=None))
    fatal_set = set(fatal_triples)

    rng = random.Random(SEED)

    # proportional allocation of CONTROL_N across (cell, mode) combos present in the 44
    from collections import Counter
    combo_counts = Counter((c, m) for c, m, s in fatal_triples)
    total_fatal = len(fatal_triples)
    raw_alloc = {combo: CONTROL_N * cnt / total_fatal for combo, cnt in combo_counts.items()}
    alloc = {combo: int(v) for combo, v in raw_alloc.items()}
    remainder = CONTROL_N - sum(alloc.values())
    remainders_sorted = sorted(raw_alloc.items(), key=lambda kv: (kv[1] - int(kv[1])), reverse=True)
    i = 0
    while remainder > 0 and i < len(remainders_sorted):
        combo = remainders_sorted[i][0]
        alloc[combo] += 1
        remainder -= 1
        i += 1

    # NOTE: the harvest's .eio coverage is sparse fleet-wide (145/40,800 directories,
    # verified separately with a plain existence walk before writing this loop) -- so
    # candidates are filtered to has_eio before sampling, rather than sampled blind and
    # hoping enough resolve. Shortfall against the CONTROL_N target is reported, not hidden.
    control_triples = []
    missing_log = []
    for (cell, mode), n_needed in alloc.items():
        dir_path = HARVEST_ROOT / f"{cell}_{mode}"
        if not dir_path.exists():
            missing_log.append(f"missing_harvest_dir:{dir_path}")
            continue
        candidates = sorted(
            p.name for p in dir_path.iterdir()
            if p.is_dir() and (p / "eplusout.eio").exists()
        )
        candidates = [c for c in candidates if (cell, mode, c) not in fatal_set]
        if len(candidates) < n_needed:
            missing_log.append(
                f"insufficient_eio_candidates:{cell}_{mode} need {n_needed} have {len(candidates)}"
            )
            n_needed = len(candidates)
        picked = rng.sample(candidates, n_needed)
        for stem in picked:
            control_triples.append((cell, mode, stem))

    overlap = set(control_triples) & fatal_set
    assert len(overlap) == 0, f"C17 FAILED: control overlaps fatal set: {overlap}"

    zone_rows = []
    missing_fatal = []
    for cell, mode, stem in fatal_triples:
        rows, err = build_zone_rows(cell, mode, stem, "fatal")
        if err:
            missing_fatal.append((cell, mode, stem, err))
        zone_rows.extend(rows)

    missing_control = []
    for cell, mode, stem in control_triples:
        rows, err = build_zone_rows(cell, mode, stem, "control")
        if err:
            missing_control.append((cell, mode, stem, err))
        zone_rows.extend(rows)

    zdf = pd.DataFrame(zone_rows)
    zdf.to_csv(OUT_ZONE_CSV, index=False)

    # per-building summary
    bldg_rows = []
    for (group, cell, mode, stem), g in zdf.groupby(["group", "cell", "mode", "stem"]):
        bldg_rows.append({
            "group": group,
            "cell": cell,
            "mode": mode,
            "stem": stem,
            "n_zones": len(g),
            "n_degenerate_zones": int(g["volume_degenerate"].sum()),
            "any_degenerate": bool(g["volume_degenerate"].any()),
            "min_volume_m3": g["volume_m3"].min(),
            "max_volume_m3": g["volume_m3"].max(),
            "median_volume_m3": g["volume_m3"].median(),
        })
    bdf = pd.DataFrame(bldg_rows)

    # join to OPEN-56 err census on (cell, stem), auto-arm only per census scope
    err = pd.read_csv(ERR_CENSUS_CSV)
    err["stem_norm"] = err["stem"].astype(str).map(normalise_stem)
    bdf["stem_norm"] = bdf["stem"].astype(str).map(normalise_stem)

    bdf_auto = bdf[bdf["mode"] == "auto"].copy()
    n_bdf_auto = len(bdf_auto)
    merged = bdf_auto.merge(err[["cell", "stem_norm", "has_volstub"]], on=["cell", "stem_norm"], how="left")
    n_unmatched = merged["has_volstub"].isna().sum()

    bdf.to_csv(OUT_BLDG_CSV, index=False)

    print("=== C15: fatal .eio coverage ===")
    print(f"fatal triples: {len(fatal_triples)}; missing/unreadable: {len(missing_fatal)}")
    for m in missing_fatal:
        print("  MISSING:", m)

    print()
    print("=== control build ===")
    print(f"control triples drawn: {len(control_triples)} (target {CONTROL_N})")
    for m in missing_log:
        print("  NOTE:", m)
    print(f"C17 overlap with fatal set: {len(overlap)} (must be 0)")
    print(f"control triples with missing/unreadable eio: {len(missing_control)}")
    for m in missing_control[:10]:
        print("  MISSING (control sample):", m)

    print()
    print("=== zone counts ===")
    print(zdf.groupby("group").size())
    print()
    print("=== volume-degenerate zones by group ===")
    print(zdf.groupby("group")["volume_degenerate"].agg(["sum", "count", "mean"]))

    print()
    print("=== per-building any_degenerate by group ===")
    print(bdf.groupby("group")["any_degenerate"].agg(["sum", "count", "mean"]))

    print()
    print("=== volume distribution (m3) by group, zone-level ===")
    for g in ["fatal", "control"]:
        s = zdf.loc[zdf["group"] == g, "volume_m3"]
        print(f"{g}: n={len(s)} mean={s.mean():.2f} median={s.median():.2f} "
              f"q25={s.quantile(.25):.2f} q75={s.quantile(.75):.2f} min={s.min():.2f} max={s.max():.2f}")

    print()
    print("=== volume distribution (m3) by group, per-building median ===")
    for g in ["fatal", "control"]:
        s = bdf.loc[bdf["group"] == g, "median_volume_m3"]
        print(f"{g}: n_buildings={len(s)} mean_of_medians={s.mean():.2f} "
              f"median_of_medians={s.median():.2f} q25={s.quantile(.25):.2f} q75={s.quantile(.75):.2f}")

    # F7's 86% family: high-temp-out-of-bounds (21) + CalcHeatBalanceInsideSurf (17) = 38/44 = 86.4%
    fatal_df["family_86pct"] = fatal_df["severe_class"].str.startswith(
        ("Temperature (high) out of bounds", "CalcHeatBalanceInsideSurf")
    )
    print()
    print(f"=== F7's 86% family check: {fatal_df['family_86pct'].sum()}/{len(fatal_df)} "
          f"= {100*fatal_df['family_86pct'].mean():.1f}% ===")
    fam_join = bdf[bdf["group"] == "fatal"].merge(
        fatal_df[["cell", "mode", "stem", "family_86pct", "severe_class"]],
        on=["cell", "mode", "stem"], how="left",
    )
    print("median_volume_m3 by family_86pct membership, fatal buildings only:")
    print(fam_join.groupby("family_86pct")["median_volume_m3"].describe()[["count", "mean", "50%", "min", "max"]])
    print("any_degenerate rate by family_86pct membership, fatal buildings only:")
    print(fam_join.groupby("family_86pct")["any_degenerate"].mean())

    print()
    print("=== OPEN-56 join: auto-arm only ===")
    print(f"fatal+control buildings with mode=='auto': {n_bdf_auto}; unmatched to err census: {n_unmatched}")
    if n_bdf_auto - n_unmatched > 0:
        joined = merged.dropna(subset=["has_volstub"])
        tab = pd.crosstab(joined["group"], joined["has_volstub"])
        print(tab)

    print()
    print(f"zone-level csv: {OUT_ZONE_CSV} ({len(zdf)} rows)")
    print(f"building-level csv: {OUT_BLDG_CSV} ({len(bdf)} rows)")


if __name__ == "__main__":
    main()
