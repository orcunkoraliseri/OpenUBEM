"""T06 (PLAN_twenty-items-2026-08-19.md) -- OPEN-53 custody re-inventory.

Independently re-scans, against TODAY's disk, the corpora OPEN-53's custody risk names:
  - E02 harvest      : %LOCALAPPDATA%/Temp/ubem_e02_harvest        (12 cells x 5 modes)
  - open48_refleet    : %LOCALAPPDATA%/Temp/ubem_validation/open48_refleet    (run 2)
  - open48_refleet3   : %LOCALAPPDATA%/Temp/ubem_validation/open48_refleet3   (run 3)
  - open48_refleet4   : %LOCALAPPDATA%/Temp/ubem_validation/open48_refleet4   (run 4)

For each corpus: directory count, per-extension file count and total size (bytes), for the
extension classes named in the register's OPEN-53 entry (.sql, .end, .err, .eio, .idf, .gpkg,
.csv, .geojson, .parquet, "other").

Then computes the cited-evidence subset: file paths/extensions actually named by any
extra/*.md or the register itself, restricted to files that still exist on disk, and its
total size.

Writes: openubem/outputs/comparisons/corpus_inventory_2026-08-19.csv
"""
import csv
import os
import re

TEMP = os.path.expandvars(r"%LOCALAPPDATA%\Temp")

CORPORA = {
    "e02_harvest": os.path.join(TEMP, "ubem_e02_harvest"),
    "open48_refleet_run2": os.path.join(TEMP, "ubem_validation", "open48_refleet"),
    "open48_refleet3_run3": os.path.join(TEMP, "ubem_validation", "open48_refleet3"),
    "open48_refleet4_run4": os.path.join(TEMP, "ubem_validation", "open48_refleet4"),
}

EXT_CLASSES = [".sql", ".end", ".err", ".eio", ".idf", ".gpkg", ".csv", ".geojson", ".parquet"]

REPO = r"C:\Users\o_iseri\Desktop\OpenUBEM"
OUT_CSV = os.path.join(REPO, "openubem", "outputs", "comparisons", "corpus_inventory_2026-08-19.csv")


def ext_of(name):
    lname = name.lower()
    for e in EXT_CLASSES:
        if lname.endswith(e):
            return e
    return "other"


def scan_corpus(root):
    n_dirs = 0
    per_ext_count = {e: 0 for e in EXT_CLASSES + ["other"]}
    per_ext_size = {e: 0 for e in EXT_CLASSES + ["other"]}
    n_files = 0
    total_size = 0
    if not os.path.isdir(root):
        return None
    for dirpath, dirnames, filenames in os.walk(root):
        n_dirs += 1
        for fn in filenames:
            n_files += 1
            fp = os.path.join(dirpath, fn)
            try:
                sz = os.path.getsize(fp)
            except OSError:
                sz = 0
            e = ext_of(fn)
            per_ext_count[e] += 1
            per_ext_size[e] += sz
            total_size += sz
    return {
        "n_dirs": n_dirs,
        "n_files": n_files,
        "total_size": total_size,
        "per_ext_count": per_ext_count,
        "per_ext_size": per_ext_size,
    }


def eio_err_check(e02_root):
    """Independent E02 .eio/.err count, matching prior censuses' method (per building dir)."""
    n_building_dirs = 0
    n_eio = 0
    n_err = 0
    n_sql = 0
    n_end = 0
    for cell_mode in sorted(os.listdir(e02_root)):
        cm_path = os.path.join(e02_root, cell_mode)
        if not os.path.isdir(cm_path):
            continue
        with os.scandir(cm_path) as it:
            for entry in it:
                if not entry.is_dir():
                    continue
                n_building_dirs += 1
                if os.path.isfile(os.path.join(entry.path, "eplusout.eio")):
                    n_eio += 1
                if os.path.isfile(os.path.join(entry.path, "eplusout.err")):
                    n_err += 1
                if os.path.isfile(os.path.join(entry.path, "eplusout.sql")):
                    n_sql += 1
                if os.path.isfile(os.path.join(entry.path, "eplusout.end")):
                    n_end += 1
    return n_building_dirs, n_eio, n_err, n_sql, n_end


def find_cited_evidence(repo_root):
    """Scan extra/*.md and the register for file paths that point into one of the four
    corpora above (by cell-mode dir name pattern or explicit path), and check which still
    exist on disk. Returns list of (source_doc, cited_string) and resolved paths found."""
    extra_dir = os.path.join(repo_root, "docs", "docs_ACTIVE", "openings", "extra")
    register = os.path.join(repo_root, "docs", "docs_ACTIVE", "openings",
                             "INVESTIGATION_open-items-register.md")
    md_files = [os.path.join(extra_dir, f) for f in os.listdir(extra_dir) if f.endswith(".md")]
    md_files.append(register)

    patterns = [
        re.compile(r"ubem_e02_harvest[^\s`\"')]*", re.IGNORECASE),
        re.compile(r"open48_refleet4?3?[^\s`\"')]*", re.IGNORECASE),
        re.compile(r"ubem_validation[^\s`\"')]*", re.IGNORECASE),
    ]
    hits = []
    for md in md_files:
        try:
            with open(md, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except OSError:
            continue
        for pat in patterns:
            for m in pat.finditer(text):
                hits.append((os.path.basename(md), m.group(0)))
    return hits


def main():
    rows = []
    for name, root in CORPORA.items():
        result = scan_corpus(root)
        if result is None:
            rows.append({"corpus": name, "root": root, "status": "MISSING", })
            continue
        row = {
            "corpus": name,
            "root": root,
            "status": "present",
            "n_dirs": result["n_dirs"],
            "n_files": result["n_files"],
            "total_size_bytes": result["total_size"],
            "total_size_gb": round(result["total_size"] / 1e9, 4),
        }
        for e in EXT_CLASSES + ["other"]:
            row[f"n{e.replace('.', '_')}"] = result["per_ext_count"][e]
            row[f"size{e.replace('.', '_')}_bytes"] = result["per_ext_size"][e]
        rows.append(row)

    fieldnames = sorted({k for r in rows for k in r.keys()},
                         key=lambda k: (k != "corpus", k != "root", k != "status", k))
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print("=== per-corpus totals ===")
    for r in rows:
        if r.get("status") == "MISSING":
            print(f"{r['corpus']}: MISSING at {r['root']}")
        else:
            print(f"{r['corpus']}: n_dirs={r['n_dirs']} n_files={r['n_files']} "
                  f"total={r['total_size_gb']} GB")

    print("\n=== E02 harvest .eio/.err/.sql/.end independent recount ===")
    e02_root = CORPORA["e02_harvest"]
    n_dirs, n_eio, n_err, n_sql, n_end = eio_err_check(e02_root)
    print(f"n_building_dirs={n_dirs} n_eio={n_eio} n_err={n_err} n_sql={n_sql} n_end={n_end}")

    print("\n=== cited-evidence hits (raw, pre-dedup) ===")
    hits = find_cited_evidence(REPO)
    print(f"total pattern hits across extra/*.md + register: {len(hits)}")
    uniq = sorted(set(h[1] for h in hits))
    for u in uniq[:50]:
        print(" ", u)
    print(f"... {len(uniq)} unique cited strings total")


if __name__ == "__main__":
    main()
