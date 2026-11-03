"""
T04 (PLAN_ten-live-items-2026-08-20-evening.md) -- OPEN-38's first measurement.

Re-scan the fatal .err files in the e02 harvest corpus, capture the ** Severe **
lines that precede each **  Fatal  ** (two-space form; the one-space form is the
OPEN-45 defect and finds nothing), classify them, and check whether the same
la_rural buildings fail across fast_zone / auto / floor.

Read-only. Writes two CSVs and reports counts. Does not write a remedy.
"""
import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

CORPUS = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest")
OUT_DIR = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\openubem\outputs\comparisons")
FATAL_CSV = OUT_DIR / "open38_fatal_causes_2026-08-20.csv"
INTERSECT_CSV = OUT_DIR / "open38_la_rural_intersection_2026-08-20.csv"

FATAL_MARK = "**  Fatal  **"
SEVERE_MARK = "** Severe"
GENERIC_TRAILER = "Program terminates due to preceding condition."

KNOWN_MODES = ["auto", "building", "fast_zone", "floor", "layout_assign"]
LA_RURAL_MODES = ["fast_zone", "auto", "floor"]


def split_cell_mode(dirname: str):
    for mode in sorted(KNOWN_MODES, key=len, reverse=True):
        suffix = "_" + mode
        if dirname.endswith(suffix):
            return dirname[: -len(suffix)], mode
    return dirname, "unknown"


def normalise_class(line: str) -> str:
    msg = line.strip()
    msg = re.sub(r"\*\*\s*Severe\s*\*\*", "", msg, count=1).strip()
    msg = re.sub(r'zone="[^"]*"', 'zone="<ZONE>"', msg)
    msg = re.sub(r'surface="[^"]*"', 'surface="<SURFACE>"', msg)
    msg = re.sub(r"zone=\S+", "zone=<ZONE>", msg)
    msg = re.sub(r"surface=\S+", "surface=<SURFACE>", msg)
    msg = re.sub(r"[-+]?\d+\.\d+", "<NUM>", msg)
    msg = re.sub(r"\[<NUM>\]|\(<NUM>\]|\[<NUM>\)|\(<NUM>\)", "<BOUND>", msg)
    msg = re.sub(r"\b\d+\b", "<NUM>", msg)
    msg = re.sub(r"\s+", " ", msg).strip()
    return msg


def main():
    err_files = sorted(CORPUS.glob("*/*/eplusout.err"))

    fatal_rows = []
    class_counter = Counter()
    no_preceding_severe = 0
    la_rural_fail = defaultdict(set)
    fatal_dir_keys = set()

    for err_path in err_files:
        stem_dir = err_path.parent
        stem = stem_dir.name
        cell_mode_dir = stem_dir.parent.name
        cell, mode = split_cell_mode(cell_mode_dir)

        text = err_path.read_text(errors="replace")
        if FATAL_MARK not in text:
            continue

        fatal_dir_keys.add(cell_mode_dir + "/" + stem)

        lines = text.splitlines()
        fatal_idx = None
        for i, ln in enumerate(lines):
            if FATAL_MARK in ln:
                fatal_idx = i
                break

        severe_lines_all = [ln for ln in lines if SEVERE_MARK in ln and "*************" not in ln]

        preceding_window = lines[max(0, fatal_idx - 5): fatal_idx] if fatal_idx is not None else []
        preceding_severe = [ln for ln in preceding_window if SEVERE_MARK in ln]

        candidate_severes = preceding_severe if preceding_severe else [
            ln for ln in severe_lines_all if "*************" not in ln
        ]

        if not candidate_severes:
            severe_class = "no_preceding_severe"
            raw_first = GENERIC_TRAILER
            no_preceding_severe += 1
        else:
            first_severe = candidate_severes[0]
            severe_class = normalise_class(first_severe)
            raw_first = first_severe.strip()

        class_counter[severe_class] += 1

        fatal_rows.append({
            "cell": cell,
            "mode": mode,
            "stem": stem,
            "severe_class": severe_class,
            "raw_first_severe_line": raw_first[:300],
        })

        if cell == "la_rural" and mode in LA_RURAL_MODES:
            la_rural_fail[stem].add(mode)

    all_dirs = {p.parent.name + "/" + p.name for p in CORPUS.glob("*/*") if p.is_dir()}
    end_files = {p.parent.parent.name + "/" + p.parent.name for p in CORPUS.glob("*/*/eplusout.end")}
    corpus_missing_end_dirs = all_dirs - end_files
    fatal_missing_end = fatal_dir_keys & corpus_missing_end_dirs
    missing_end = len(corpus_missing_end_dirs)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with FATAL_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["cell", "mode", "stem", "severe_class", "raw_first_severe_line"])
        w.writeheader()
        for row in fatal_rows:
            w.writerow(row)

    all_la_rural_stems = sorted(la_rural_fail.keys())
    with INTERSECT_CSV.open("w", newline="", encoding="utf-8") as f:
        fieldnames = ["stem"] + LA_RURAL_MODES + ["n_modes_failed", "fails_in_all_three"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for stem in all_la_rural_stems:
            modes_failed = la_rural_fail[stem]
            row = {"stem": stem}
            for m in LA_RURAL_MODES:
                row[m] = 1 if m in modes_failed else 0
            row["n_modes_failed"] = len(modes_failed)
            row["fails_in_all_three"] = 1 if len(modes_failed) == len(LA_RURAL_MODES) else 0
            w.writerow(row)

    intersection = [s for s, modes in la_rural_fail.items() if len(modes) == len(LA_RURAL_MODES)]
    union = list(la_rural_fail.keys())

    n_fatal = len(fatal_rows)

    print(f"fatal_files_found={n_fatal}")
    print(f"fatal_dirs_also_missing_end={len(fatal_missing_end)} (expect 0 -- fatal runs still write .end)")
    print(f"corpus_wide_dirs_missing_end={missing_end} (matches F8's 875 harvest-custody shortfall population, OPEN-53 scope)")
    print("NOTE: F9's '1 missing .end' building (the 45th sacct-FAILED member) cannot be distinguished "
          "from the other 874 harvest-custody-missing dirs without sacct status data -- that is T05's scope.")
    print("severe_class_counts:")
    for cls, cnt in class_counter.most_common(15):
        print(f"  {cnt}: {cls}")
    print(f"no_preceding_severe_count={no_preceding_severe}")
    print(f"la_rural_union_failing_stems={len(union)}")
    print(f"la_rural_intersection_all_three_modes={len(intersection)}")
    for m in LA_RURAL_MODES:
        cnt = sum(1 for modes in la_rural_fail.values() if m in modes)
        print(f"  la_rural_{m}_fail_count={cnt}")

    return {
        "n_fatal": n_fatal,
        "missing_end": missing_end,
        "class_counter": class_counter,
        "no_preceding_severe": no_preceding_severe,
        "la_rural_union": len(union),
        "la_rural_intersection": len(intersection),
    }


if __name__ == "__main__":
    main()
