"""T03 stage A (PLAN_four-board-items-2026-08-20.md) -- OPEN-53 evidence inventory.

Inventories %LOCALAPPDATA%\\Temp\\ubem_validation by corpus (top-level subdirectory) and
extension: file count and bytes. No deletion, no copy -- inventory only.

Writes: openubem/outputs/comparisons/open53_evidence_inventory_2026-08-20.csv
"""
import csv
import os

TEMP_ROOT = os.path.join(os.path.expandvars(r"%LOCALAPPDATA%"), "Temp", "ubem_validation")

EXT_CLASSES = [".sql", ".err", ".eio", ".end", ".gpkg", ".csv", ".geojson", ".parquet",
               ".json", ".idf"]

REPO = r"C:\Users\o_iseri\Desktop\OpenUBEM"
OUT_CSV = os.path.join(REPO, "openubem", "outputs", "comparisons",
                        "open53_evidence_inventory_2026-08-20.csv")


def ext_of(name):
    lname = name.lower()
    for e in EXT_CLASSES:
        if lname.endswith(e):
            return e
    return "other"


def scan_corpus(root):
    n_dirs = 0
    n_files = 0
    total_size = 0
    per_ext_count = {e: 0 for e in EXT_CLASSES + ["other"]}
    per_ext_size = {e: 0 for e in EXT_CLASSES + ["other"]}
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


def main():
    if not os.path.isdir(TEMP_ROOT):
        raise SystemExit(f"TEMP_ROOT missing: {TEMP_ROOT}")

    corpora = sorted(
        d for d in os.listdir(TEMP_ROOT) if os.path.isdir(os.path.join(TEMP_ROOT, d))
    )

    rows = []
    for corpus in corpora:
        root = os.path.join(TEMP_ROOT, corpus)
        result = scan_corpus(root)
        for e in EXT_CLASSES + ["other"]:
            rows.append({
                "corpus": corpus,
                "extension": e,
                "n_files": result["per_ext_count"][e],
                "size_bytes": result["per_ext_size"][e],
                "size_gb": round(result["per_ext_size"][e] / 1e9, 6),
            })
        rows.append({
            "corpus": corpus,
            "extension": "TOTAL",
            "n_files": result["n_files"],
            "size_bytes": result["total_size"],
            "size_gb": round(result["total_size"] / 1e9, 6),
        })

    grand_total_files = sum(r["n_files"] for r in rows if r["extension"] == "TOTAL")
    grand_total_bytes = sum(r["size_bytes"] for r in rows if r["extension"] == "TOTAL")
    rows.append({
        "corpus": "ALL_CORPORA",
        "extension": "TOTAL",
        "n_files": grand_total_files,
        "size_bytes": grand_total_bytes,
        "size_gb": round(grand_total_bytes / 1e9, 6),
    })

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["corpus", "extension", "n_files", "size_bytes", "size_gb"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"TEMP_ROOT = {TEMP_ROOT}")
    print(f"corpora found: {corpora}")
    print()
    for corpus in corpora:
        crows = [r for r in rows if r["corpus"] == corpus and r["n_files"] > 0]
        print(f"--- {corpus} ---")
        for r in crows:
            print(f"  {r['extension']:10s} n={r['n_files']:8d}  {r['size_gb']:10.4f} GB")
    print()
    print(f"GRAND TOTAL: n_files={grand_total_files}  {grand_total_bytes / 1e9:.4f} GB")
    print(f"wrote {OUT_CSV}")


if __name__ == "__main__":
    main()
