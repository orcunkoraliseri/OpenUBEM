"""Re-verify a preserved simulation corpus against its INVENTORY.json (ruling R6).

R6 requires an inventory that is *checked*, not written once. Run this against a corpus root:

    py -3 scripts/analysis/corpus_inventory_check_2026-08-20.py C:/Users/o_iseri/OpenUBEM_corpora/open61_census_2026-08-20

Exit 0 if the corpus still matches its manifest, 1 otherwise.
"""
import json
import os
import sys


def scan(root):
    cells = {}
    for cell in sorted(os.listdir(root)):
        cd = os.path.join(root, cell)
        if not os.path.isdir(cd):
            continue
        n_dirs = n_sql = n_bytes = 0
        for stem in os.listdir(cd):
            n_dirs += 1
            sim_out = os.path.join(cd, stem, "sim_out")
            if not os.path.isdir(sim_out):
                continue
            for name in os.listdir(sim_out):
                try:
                    n_bytes += os.path.getsize(os.path.join(sim_out, name))
                except OSError:
                    continue
                if name.lower().endswith(".sql"):
                    n_sql += 1
        cells[cell] = {"building_dirs": n_dirs, "sql_files": n_sql, "bytes": n_bytes}
    return cells


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    root = sys.argv[1]
    manifest_path = os.path.join(root, "INVENTORY.json")
    if not os.path.isdir(root):
        print("FAIL corpus root missing: %s" % root)
        return 1
    if not os.path.isfile(manifest_path):
        print("FAIL no INVENTORY.json at %s" % root)
        return 1
    with open(manifest_path, encoding="utf-8") as handle:
        manifest = json.load(handle)

    found = scan(root)
    problems = []

    missing = sorted(set(manifest["cells"]) - set(found))
    extra = sorted(set(found) - set(manifest["cells"]))
    if missing:
        problems.append("cells missing: %s" % ", ".join(missing))
    if extra:
        problems.append("cells not in manifest: %s" % ", ".join(extra))

    for cell, want in sorted(manifest["cells"].items()):
        have = found.get(cell)
        if have is None:
            continue
        for key in ("building_dirs", "sql_files", "bytes"):
            if have[key] != want[key]:
                problems.append(
                    "%s %s: manifest %d, on disk %d" % (cell, key, want[key], have[key])
                )

    total_dirs = sum(c["building_dirs"] for c in found.values())
    total_sql = sum(c["sql_files"] for c in found.values())
    total_bytes = sum(c["bytes"] for c in found.values())
    print("corpus      : %s" % root)
    print("cells       : %d" % len(found))
    print("building dirs: %d (manifest %d)" % (total_dirs, manifest["total_building_dirs"]))
    print("sql files   : %d (manifest %d)" % (total_sql, manifest["total_sql_files"]))
    print("size        : %.1f GB (manifest %.1f GB)" % (total_bytes / 1e9, manifest["total_gb"]))
    print("coverage    : %.1f%% of the %d ok census rows"
          % (100.0 * total_dirs / manifest["census_ok_rows"], manifest["census_ok_rows"]))

    if problems:
        print("\nFAIL - %d discrepancies:" % len(problems))
        for problem in problems[:40]:
            print("  - %s" % problem)
        return 1
    print("\nPASS - corpus matches its manifest.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
