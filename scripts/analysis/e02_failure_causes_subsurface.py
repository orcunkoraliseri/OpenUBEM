r"""T02 -- Causes of the 45 E02 failures (OPEN-41) and the layout_assign
subsurface geometry census (OPEN-38), from one streaming pass over the
E02 harvest corpus's eplusout.err files.

For every building directory under ubem_e02_harvest, read eplusout.err once,
then:
  (a) test for a two-space fatal (r"\*\*\s+Fatal\s+\*\*"); if present, walk
      backwards from the fatal's position for "** Severe **" lines and record
      the first and last one found before the fatal, plus a cause_group.
  (b) test for the substring "Base surface does not surround subsurface"
      anywhere in the file, fleet-wide, in all five modes -- not only in the
      44 fatals.

Plan: docs/docs_ACTIVE/openings/implemenation/PLAN_e02-audit-and-closure.md, T02.
"""

import csv
import os
import re

CORPUS_ROOT = r"C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest"
OUT_41 = r"C:\Users\o_iseri\Desktop\OpenUBEM\openubem\outputs\comparisons\open41_failure_causes.csv"
OUT_38 = r"C:\Users\o_iseri\Desktop\OpenUBEM\openubem\outputs\comparisons\open38_subsurface_census.csv"

CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]
MODES = ["auto", "building", "fast_zone", "floor", "layout_assign"]

FATAL_RE = re.compile(r"\*\*\s+Fatal\s+\*\*")
SEVERE_RE = re.compile(r"\*\*\s+Severe\s+\*\*")
SUBSURFACE_MSG = "Base surface does not surround subsurface"
SEVERE_PREFIX_RE = re.compile(r"^\*\*\s+Severe\s+\*\*\s*")


def array_to_cell_mode():
    mapping = {}
    for cell in CELLS:
        for mode in MODES:
            mapping[f"{cell}_{mode}"] = (cell, mode)
    return mapping


def line_at(text, pos):
    start = text.rfind("\n", 0, pos) + 1
    end = text.find("\n", pos)
    if end == -1:
        end = len(text)
    return text[start:end].strip()


BRACKET_RE = re.compile(r"\[[^\]]*\]")
QUOTED_RE = re.compile(r'"[^"]*"')


def cause_group_of(severe_line):
    body = SEVERE_PREFIX_RE.sub("", severe_line).strip()
    if ":" in body:
        return body.split(":", 1)[0].strip()
    normalized = BRACKET_RE.sub("[...]", body)
    normalized = QUOTED_RE.sub('"..."', normalized)
    return normalized[:60].strip()


def main():
    array_map = array_to_cell_mode()

    with os.scandir(CORPUS_ROOT) as it:
        array_names = sorted(e.name for e in it if e.is_dir())

    rows_41 = []
    rows_38 = []

    n_buildings_scanned = 0
    n_fatal_total = 0
    fatal_stems = []
    nyc_fast_zone_absent_check = None

    for array_name in array_names:
        if array_name not in array_map:
            continue
        cell, mode = array_map[array_name]
        array_path = os.path.join(CORPUS_ROOT, array_name)

        with os.scandir(array_path) as it:
            stems = sorted(e.name for e in it if e.is_dir())

        for stem in stems:
            err_path = os.path.join(array_path, stem, "eplusout.err")
            if not os.path.isfile(err_path):
                continue
            n_buildings_scanned += 1

            with open(err_path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()

            fatal_match = FATAL_RE.search(text)
            has_fatal = fatal_match is not None

            if has_fatal:
                n_fatal_total += 1
                fatal_stems.append((cell, mode, stem))

                severe_positions = [m.start() for m in SEVERE_RE.finditer(text)
                                     if m.start() < fatal_match.start()]
                n_severe = len(severe_positions)
                if severe_positions:
                    first_severe = line_at(text, severe_positions[0])
                    last_severe_before_fatal = line_at(text, severe_positions[-1])
                    cause_group = cause_group_of(last_severe_before_fatal)
                else:
                    first_severe = ""
                    last_severe_before_fatal = ""
                    cause_group = "(no severe before fatal)"

                fatal_line = line_at(text, fatal_match.start())

                rows_41.append({
                    "cell": cell,
                    "mode": mode,
                    "stem": stem,
                    "n_severe": n_severe,
                    "first_severe": first_severe,
                    "last_severe_before_fatal": last_severe_before_fatal,
                    "fatal_line": fatal_line,
                    "cause_group": cause_group,
                })

            if cell == "nyc_centre" and mode == "fast_zone" and stem == "way_1240348353":
                nyc_fast_zone_absent_check = has_fatal

            n_sub = text.count(SUBSURFACE_MSG)
            if n_sub > 0:
                rows_38.append({
                    "cell": cell,
                    "mode": mode,
                    "stem": stem,
                    "n_occurrences": n_sub,
                    "terminated": has_fatal,
                })

    with open(OUT_41, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "cell", "mode", "stem", "n_severe", "first_severe",
            "last_severe_before_fatal", "fatal_line", "cause_group",
        ])
        writer.writeheader()
        writer.writerows(rows_41)

    with open(OUT_38, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "cell", "mode", "stem", "n_occurrences", "terminated",
        ])
        writer.writeheader()
        writer.writerows(rows_38)

    print(f"Buildings scanned (eplusout.err present): {n_buildings_scanned}")
    print(f"Fatal (two-space) count: {n_fatal_total}")
    print(f"nyc_centre/fast_zone/way_1240348353 has_fatal: {nyc_fast_zone_absent_check}")
    print()

    print("=== Non-vacuity control ===")
    print(f"n_fatal_total = {n_fatal_total} (expect 44, not 0, not 45, not {n_buildings_scanned})")
    print(f"way_1240348353 in fatal_stems: {('nyc_centre', 'fast_zone', 'way_1240348353') in fatal_stems}")
    print()

    print("=== Cause groups (open41) ===")
    group_counts = {}
    for r in rows_41:
        group_counts[r["cause_group"]] = group_counts.get(r["cause_group"], 0) + 1
    for g, c in sorted(group_counts.items(), key=lambda kv: -kv[1]):
        print(f"  {c:3d}  {g}")
    print()

    print("=== Known-cause control: CheckForRunawayPlantTemps in la_centre/auto ===")
    for r in rows_41:
        if r["cell"] == "la_centre" and r["mode"] == "auto":
            print(f"  {r['cell']}/{r['mode']}/{r['stem']}: cause_group={r['cause_group']!r}")
            print(f"    last_severe_before_fatal={r['last_severe_before_fatal']!r}")
    print()

    print("=== Known-severe control: nyc_centre/auto/way_266149332 ===")
    for r in rows_41:
        if r["cell"] == "nyc_centre" and r["mode"] == "auto" and r["stem"] == "way_266149332":
            print(f"  n_severe={r['n_severe']}")
            print(f"  first_severe={r['first_severe']!r}")
            print(f"  last_severe_before_fatal={r['last_severe_before_fatal']!r}")
            print(f"  fatal_line={r['fatal_line']!r}")
    print()

    print("=== la_rural cross-mode intersection (OPEN-41 b) ===")
    la_rural_by_mode = {"auto": set(), "floor": set(), "fast_zone": set()}
    la_rural_all = []
    for r in rows_41:
        if r["cell"] == "la_rural":
            la_rural_all.append((r["mode"], r["stem"]))
            if r["mode"] in la_rural_by_mode:
                la_rural_by_mode[r["mode"]].add(r["stem"])
    for m, s in la_rural_by_mode.items():
        print(f"  la_rural/{m}: {len(s)} failing stems: {sorted(s)}")
    print(f"  la_rural total failures (all modes incl. building/layout_assign): {len(la_rural_all)}")
    inter = la_rural_by_mode["auto"] & la_rural_by_mode["floor"] & la_rural_by_mode["fast_zone"]
    print(f"  intersection(auto, floor, fast_zone) = {sorted(inter)}  (n={len(inter)})")
    union3 = la_rural_by_mode["auto"] | la_rural_by_mode["floor"] | la_rural_by_mode["fast_zone"]
    print(f"  union(auto, floor, fast_zone) = {sorted(union3)}  (n={len(union3)})")
    print()

    print("=== OPEN-38 subsurface census ===")
    print(f"  total rows (building x file occurrences>0): {len(rows_38)}")
    by_mode = {}
    terminated_by_mode = {}
    for r in rows_38:
        by_mode[r["mode"]] = by_mode.get(r["mode"], 0) + 1
        if r["terminated"]:
            terminated_by_mode[r["mode"]] = terminated_by_mode.get(r["mode"], 0) + 1
    for m in MODES:
        total_m = by_mode.get(m, 0)
        term_m = terminated_by_mode.get(m, 0)
        print(f"  mode={m}: n_buildings_with_message={total_m}, terminated={term_m}, "
              f"surviving={total_m - term_m}")
    print()

    print("=== OPEN-38 known 7 terminated layout_assign failures ===")
    known = {("nyc_rural", "layout_assign"): 3, ("la_centre", "layout_assign"): 1,
             ("la_urban", "layout_assign"): 3}
    for (c, m), expected_n in known.items():
        matches = [r for r in rows_38 if r["cell"] == c and r["mode"] == m and r["terminated"]]
        print(f"  {c}/{m}: expected {expected_n}, found {len(matches)} terminated: "
              f"{sorted(r['stem'] for r in matches)}")


if __name__ == "__main__":
    main()
