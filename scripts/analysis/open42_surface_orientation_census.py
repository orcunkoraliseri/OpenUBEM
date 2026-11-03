"""OPEN-42 + OPEN-11 T03 -- surface-orientation ("upside down") census.

Read-only over the local E02 harvest (40,800 building directories). Parses every
`GetVertices: <Floor|Roof/Ceiling> is upside down!` warning line out of each
run's `eplusout.err` and tests whether the signature separates the 16 failing
(building x mode) runs named in `open42_six_failure_causes.csv` from healthy
runs -- the same background sample already pinned by
`scripts/analysis/open42_zone_geometry.py` (reused here via `importlib`, not
retyped, so the two OPEN-42 measurements are directly comparable).

Three questions, each against a control rate:
  4a. Do fatal zones carry the warning more often than their non-fatal sibling
      zones in the same run?
  4b. Is the topmost-storey roof systematically inverted while lower storeys
      are not?
  4c. Do the modes that succeed (building, layout_assign) carry the warning
      for the same six buildings, or only the three modes that fatal?

Then a fleet-wide rate over all 40,800 `.err` files -- the number that decides
the item, reported before any interpretation.

No fix, no code change, no simulation. Diagnosis only.

Emits openubem/outputs/comparisons/open42_surface_orientation.csv: one row per
upside-down warning found, across the fleet-wide scan.
"""

from __future__ import annotations

import csv
import importlib.util
import re
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from openubem.results.err_parse import WARNING_RE  # noqa: E402

HARVEST_ROOT = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest")
CAUSES_CSV = REPO_ROOT / "openubem/outputs/comparisons/open42_six_failure_causes.csv"
OUT_CSV = REPO_ROOT / "openubem/outputs/comparisons/open42_surface_orientation.csv"

MODES = ["auto", "building", "fast_zone", "floor", "layout_assign"]
FAILING_MODES = {"auto", "fast_zone", "floor"}
SUCCEEDING_MODES = {"building", "layout_assign"}

_zg_spec = importlib.util.spec_from_file_location(
    "open42_zone_geometry", REPO_ROOT / "scripts/analysis/open42_zone_geometry.py"
)
zg = importlib.util.module_from_spec(_zg_spec)
_zg_spec.loader.exec_module(zg)

TARGET_CELLS = zg.TARGET_CELLS
TARGET_STEMS = zg.TARGET_STEMS
SEVERE_ZONE_RE = zg.SEVERE_ZONE_RE
FLOOR_SUFFIX_RE = zg.FLOOR_SUFFIX_RE

UPSIDE_DOWN_RE = re.compile(
    r'GetVertices:\s+(Floor|Roof/Ceiling)\s+is upside down!\s+'
    r'Tilt angle=\[(-?\d+\.?\d*)\].*?'
    r'Surface="([^"]+)",\s+in Zone="([^"]+)"',
    re.IGNORECASE,
)


def storey_token(zone_name: str) -> "str | None":
    m = FLOOR_SUFFIX_RE.search(str(zone_name))
    return f"F{m.group(1)}" if m else None


def parse_upside_down(err_path: Path) -> list[dict]:
    if not err_path.is_file():
        return []
    rows = []
    text = err_path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        if not WARNING_RE.match(line):
            continue
        m = UPSIDE_DOWN_RE.search(line)
        if not m:
            continue
        surface_class, tilt, surface_name, zone_name = m.groups()
        rows.append({
            "surface_class": "Roof-Ceiling" if surface_class == "Roof/Ceiling" else surface_class,
            "tilt_reported": float(tilt),
            "surface_name": surface_name,
            "zone_name": zone_name,
            "storey_token": storey_token(zone_name),
        })
    return rows


def non_vacuity_control() -> list[str]:
    log = []
    zero_case = HARVEST_ROOT / "la_rural_building" / "way_472960972" / "eplusout.err"
    many_case = HARVEST_ROOT / "la_rural_auto" / "way_472960972" / "eplusout.err"

    zero_parsed = parse_upside_down(zero_case)
    many_parsed = parse_upside_down(many_case)

    zero_grep = sum(1 for l in zero_case.read_text(encoding="utf-8", errors="replace").splitlines()
                     if "upside down" in l)
    many_grep = sum(1 for l in many_case.read_text(encoding="utf-8", errors="replace").splitlines()
                     if "upside down" in l)

    log.append(f"ZERO case {zero_case}: parser={len(zero_parsed)}, grep -c 'upside down'={zero_grep}, "
               f"agree={len(zero_parsed) == zero_grep}")
    log.append(f"MANY case {many_case}: parser={len(many_parsed)}, grep -c 'upside down'={many_grep}, "
               f"agree={len(many_parsed) == many_grep}")
    ok = len(zero_parsed) == 0 == zero_grep and len(many_parsed) == many_grep and many_parsed
    log.append(f"NON-VACUITY CONTROL: {'PASS' if ok else 'FAIL'}")
    return log


def run_target_and_background() -> "tuple[pd.DataFrame, pd.DataFrame, list[str]]":
    causes = pd.read_csv(CAUSES_CSV)
    assert len(causes) == 30, f"expected 30 rows in causes csv, got {len(causes)}"

    def _extract_zone_from_csv_text(text):
        if pd.isna(text):
            return None
        m = SEVERE_ZONE_RE.search(str(text))
        return m.group(1) if m else None

    causes = causes.copy()
    causes["csv_severe_zone"] = causes["severe_line_text"].apply(_extract_zone_from_csv_text)

    target_rows = []
    for _, row in causes.iterrows():
        cell, stem, mode = row["cell"], row["stem"], row["mode"]
        err_path = HARVEST_ROOT / f"{cell}_{mode}" / stem / "eplusout.err"
        eio_path = HARVEST_ROOT / f"{cell}_{mode}" / stem / "eplusout.eio"
        ud = parse_upside_down(err_path)
        zdf = zg.parse_eio_zones(eio_path)
        zdf = zg.add_derived(zdf)
        if not zdf.empty:
            zdf["_g"] = 1
        zdf = zg.mark_top_floor(zdf, ["_g"])
        all_zone_names = set(zdf["zone_name"].astype(str)) if not zdf.empty else set()
        ud_zone_names = {r["zone_name"] for r in ud}
        top_floor_zones = set(zdf.loc[zdf["is_top_floor_zone"] == True, "zone_name"].astype(str)) if not zdf.empty else set()

        for u in ud:
            r = dict(u)
            r.update({
                "cell": cell, "stem": stem, "mode": mode, "run_label": "target",
                "has_fatal": bool(row["has_fatal"]),
                "population": "failing_mode" if mode in FAILING_MODES else "succeeding_mode",
            })
            target_rows.append(r)

        target_rows.append({
            "cell": cell, "stem": stem, "mode": mode, "run_label": "target",
            "has_fatal": bool(row["has_fatal"]),
            "population": "failing_mode" if mode in FAILING_MODES else "succeeding_mode",
            "surface_class": None, "tilt_reported": None, "surface_name": None,
            "zone_name": None, "storey_token": None,
            "_run_summary": True,
            "_n_upside_down": len(ud),
            "_n_zones_total": len(all_zone_names),
            "_n_zones_upside_down": len(ud_zone_names),
            "_fatal_zone": row["csv_severe_zone"],
            "_fatal_zone_upside_down": (row["csv_severe_zone"] in ud_zone_names) if pd.notna(row["csv_severe_zone"]) else None,
            "_n_top_floor_zones": len(top_floor_zones),
            "_n_top_floor_zones_upside_down": len(top_floor_zones & ud_zone_names),
        })

    exclude = {s for stems in TARGET_STEMS.values() for s in stems}
    bg_stems_by_cell = {}
    n_per_cell = 10
    for cell in TARGET_CELLS:
        bg_stems_by_cell[cell] = zg.find_successful_background_buildings(cell, n_per_cell, exclude)

    bg_rows = []
    for cell, stems in bg_stems_by_cell.items():
        for stem in stems:
            for mode in MODES:
                err_path = HARVEST_ROOT / f"{cell}_{mode}" / stem / "eplusout.err"
                eio_path = HARVEST_ROOT / f"{cell}_{mode}" / stem / "eplusout.eio"
                ud = parse_upside_down(err_path)
                zdf = zg.parse_eio_zones(eio_path)
                zdf = zg.add_derived(zdf)
                if not zdf.empty:
                    zdf["_g"] = 1
                zdf = zg.mark_top_floor(zdf, ["_g"])
                all_zone_names = set(zdf["zone_name"].astype(str)) if not zdf.empty else set()
                ud_zone_names = {r["zone_name"] for r in ud}
                top_floor_zones = set(zdf.loc[zdf["is_top_floor_zone"] == True, "zone_name"].astype(str)) if not zdf.empty else set()

                for u in ud:
                    r = dict(u)
                    r.update({
                        "cell": cell, "stem": stem, "mode": mode, "run_label": "background",
                        "has_fatal": False,
                        "population": "background",
                    })
                    bg_rows.append(r)

                bg_rows.append({
                    "cell": cell, "stem": stem, "mode": mode, "run_label": "background",
                    "has_fatal": False, "population": "background",
                    "surface_class": None, "tilt_reported": None, "surface_name": None,
                    "zone_name": None, "storey_token": None,
                    "_run_summary": True,
                    "_n_upside_down": len(ud),
                    "_n_zones_total": len(all_zone_names),
                    "_n_zones_upside_down": len(ud_zone_names),
                    "_fatal_zone": None,
                    "_fatal_zone_upside_down": None,
                    "_n_top_floor_zones": len(top_floor_zones),
                    "_n_top_floor_zones_upside_down": len(top_floor_zones & ud_zone_names),
                })

    target_df = pd.DataFrame(target_rows)
    bg_df = pd.DataFrame(bg_rows)
    log = [f"Background sample for {c}: {len(s)} buildings: {s}" for c, s in bg_stems_by_cell.items()]
    return target_df, bg_df, log


def fleet_wide_scan() -> "tuple[int, int, int, int]":
    n_dirs = 0
    n_dirs_with_warning = 0
    n_warning_lines = 0
    n_err_files = 0
    for mode_dir in sorted(HARVEST_ROOT.iterdir()):
        if not mode_dir.is_dir():
            continue
        for stem_dir in mode_dir.iterdir():
            if not stem_dir.is_dir():
                continue
            n_dirs += 1
            err_path = stem_dir / "eplusout.err"
            if not err_path.is_file():
                continue
            n_err_files += 1
            text = err_path.read_text(encoding="utf-8", errors="replace")
            n = text.count("upside down")
            if n > 0:
                n_dirs_with_warning += 1
                n_warning_lines += n
    return n_dirs, n_err_files, n_dirs_with_warning, n_warning_lines


def main():
    print("=== Non-vacuity control ===")
    for line in non_vacuity_control():
        print(line)
    print()

    print("=== Target (30 runs) + background (100 runs) ===")
    target_df, bg_df, bg_log = run_target_and_background()
    for line in bg_log:
        print(line)

    all_df = pd.concat([target_df, bg_df], ignore_index=True, sort=False)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    all_df.to_csv(OUT_CSV, index=False)
    print(f"Wrote {len(all_df)} rows ({len(target_df)} target + {len(bg_df)} background) to {OUT_CSV}")

    target_summary = target_df[target_df.get("_run_summary") == True]
    bg_summary = bg_df[bg_df.get("_run_summary") == True]

    print("\n--- Per-run summary, target (30 runs) ---")
    print(target_summary[["cell", "stem", "mode", "has_fatal", "_n_upside_down",
                           "_fatal_zone", "_fatal_zone_upside_down"]].to_string(index=False))

    print("\n=== Question 4a: fatal zone vs non-fatal sibling zones, same run (16 failing runs) ===")
    fatal_runs = target_summary[target_summary["has_fatal"] == True]
    n_fatal_zone_ud = int(fatal_runs["_fatal_zone_upside_down"].fillna(False).sum())
    n_fatal_runs = len(fatal_runs)
    print(f"Fatal zone carries an upside-down warning: {n_fatal_zone_ud} / {n_fatal_runs} failing runs")

    total_sibling_zones = int((fatal_runs["_n_zones_total"] - 1).clip(lower=0).sum())
    total_sibling_ud = int((fatal_runs["_n_zones_upside_down"] -
                            fatal_runs["_fatal_zone_upside_down"].fillna(False).astype(int)).clip(lower=0).sum())
    sib_rate = total_sibling_ud / total_sibling_zones if total_sibling_zones else float("nan")
    fatal_rate = n_fatal_zone_ud / n_fatal_runs if n_fatal_runs else float("nan")
    print(f"Fatal-zone rate: {fatal_rate:.3f} ({n_fatal_zone_ud}/{n_fatal_runs})")
    print(f"Non-fatal sibling-zone rate (same runs): {sib_rate:.4f} ({total_sibling_ud}/{total_sibling_zones})")

    print("\n=== Question 4b: topmost-storey roof inverted vs lower storeys ===")
    for label, df in [("target", target_df), ("background", bg_df)]:
        summ = df[df.get("_run_summary") == True]
        n_top_ud = int(summ["_n_top_floor_zones_upside_down"].sum())
        n_top_total = int(summ["_n_top_floor_zones"].sum())
        n_ud_total = int(summ["_n_zones_upside_down"].sum())
        n_zones_total = int(summ["_n_zones_total"].sum())
        n_nontop_ud = n_ud_total - n_top_ud
        n_nontop_total = n_zones_total - n_top_total
        top_rate = n_top_ud / n_top_total if n_top_total else float("nan")
        nontop_rate = n_nontop_ud / n_nontop_total if n_nontop_total else float("nan")
        print(f"[{label}] top-floor zone upside-down rate: {top_rate:.4f} ({n_top_ud}/{n_top_total}); "
              f"non-top-floor zone rate: {nontop_rate:.4f} ({n_nontop_ud}/{n_nontop_total})")

    print("\n=== Question 4c: does the warning appear only in failing modes? ===")
    for cell, stem in [(c, s) for c, stems in TARGET_STEMS.items() for s in stems]:
        sub = target_summary[(target_summary["cell"] == cell) & (target_summary["stem"] == stem)]
        parts = []
        for _, r in sub.sort_values("mode").iterrows():
            tag = "FAIL" if r["has_fatal"] else "ok"
            parts.append(f"{r['mode']}={r['_n_upside_down']}({tag})")
        print(f"{cell}/{stem}: " + ", ".join(parts))

    n_runs_failing_modes_with_ud = int(((target_summary["population"] == "failing_mode") &
                                         (target_summary["_n_upside_down"] > 0)).sum())
    n_runs_failing_modes = int((target_summary["population"] == "failing_mode").sum())
    n_runs_succeeding_modes_with_ud = int(((target_summary["population"] == "succeeding_mode") &
                                            (target_summary["_n_upside_down"] > 0)).sum())
    n_runs_succeeding_modes = int((target_summary["population"] == "succeeding_mode").sum())
    print(f"Runs with warning, failing modes (auto/fast_zone/floor): "
          f"{n_runs_failing_modes_with_ud}/{n_runs_failing_modes}")
    print(f"Runs with warning, succeeding modes (building/layout_assign): "
          f"{n_runs_succeeding_modes_with_ud}/{n_runs_succeeding_modes}")

    within_failing = target_summary[target_summary["population"] == "failing_mode"]
    by_mode = within_failing.groupby("mode")["_n_upside_down"].apply(lambda s: int((s > 0).sum()))
    by_mode_total = within_failing.groupby("mode").size()
    print("Within the 3 failing modes, runs with the warning per mode:")
    for mode in ["auto", "fast_zone", "floor"]:
        if mode in by_mode.index:
            print(f"  {mode}: {by_mode[mode]}/{by_mode_total[mode]}")

    print("\n=== Fleet-wide scan (all 40,800 .err) ===")
    n_dirs, n_err_files, n_dirs_ud, n_lines_ud = fleet_wide_scan()
    rate = n_dirs_ud / n_err_files if n_err_files else float("nan")
    print(f"FLEET-WIDE RATE: {n_dirs_ud} / {n_err_files} run directories carry >=1 upside-down warning "
          f"({rate:.4%}), total warning lines = {n_lines_ud}, n_dirs={n_dirs}")


if __name__ == "__main__":
    main()
