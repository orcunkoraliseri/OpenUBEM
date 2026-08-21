"""T03 stage A (PLAN_four-board-items-2026-08-20.md) -- OPEN-53 evidence copy verification.

Verifies the robocopy of citable evidence from %LOCALAPPDATA%\\Temp\\ubem_validation to
C:\\Users\\o_iseri\\Desktop\\OpenUBEM\\evidence\\<corpus>\\...:
  - per extension, destination file count == source file count (for the 9 copied extensions;
    .sql and "other" are intentionally excluded from the copy)
  - SHA-256 match on a random 200-file sample plus every .gpkg and .parquet file

No deletion. Writes:
  openubem/outputs/comparisons/open53_evidence_verification_2026-08-20.csv
"""
import csv
import hashlib
import os
import random

TEMP_ROOT = os.path.join(os.path.expandvars(r"%LOCALAPPDATA%"), "Temp", "ubem_validation")
EVID_ROOT = r"C:\Users\o_iseri\Desktop\OpenUBEM\evidence"

COPIED_EXT = [".err", ".eio", ".end", ".gpkg", ".csv", ".geojson", ".parquet", ".json", ".idf"]

REPO = r"C:\Users\o_iseri\Desktop\OpenUBEM"
OUT_CSV = os.path.join(REPO, "openubem", "outputs", "comparisons",
                        "open53_evidence_verification_2026-08-20.csv")

random.seed(20260820)


def ext_of(name):
    lname = name.lower()
    for e in COPIED_EXT:
        if lname.endswith(e):
            return e
    return None


def list_files(root):
    """Return dict ext -> list of (relpath_from_root, abspath)."""
    out = {e: [] for e in COPIED_EXT}
    for dirpath, dirnames, filenames in os.walk(root):
        for fn in filenames:
            e = ext_of(fn)
            if e is None:
                continue
            fp = os.path.join(dirpath, fn)
            rel = os.path.relpath(fp, root)
            out[e].append((rel, fp))
    return out


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    corpora = sorted(
        d for d in os.listdir(TEMP_ROOT) if os.path.isdir(os.path.join(TEMP_ROOT, d))
    )

    count_rows = []
    all_pairs_for_hash = []  # (corpus, ext, rel, src_path, dst_path)
    gpkg_parquet_pairs = []

    grand_src_total = 0
    grand_dst_total = 0

    for corpus in corpora:
        src_root = os.path.join(TEMP_ROOT, corpus)
        dst_root = os.path.join(EVID_ROOT, corpus)
        src_files = list_files(src_root)
        dst_files = list_files(dst_root) if os.path.isdir(dst_root) else {e: [] for e in COPIED_EXT}

        src_rel_by_ext = {e: {rel for rel, _ in src_files[e]} for e in COPIED_EXT}
        dst_rel_by_ext = {e: {rel for rel, _ in dst_files[e]} for e in COPIED_EXT}

        for e in COPIED_EXT:
            n_src = len(src_rel_by_ext[e])
            n_dst = len(dst_rel_by_ext[e])
            missing = src_rel_by_ext[e] - dst_rel_by_ext[e]
            extra = dst_rel_by_ext[e] - src_rel_by_ext[e]
            count_rows.append({
                "corpus": corpus,
                "extension": e,
                "n_source": n_src,
                "n_dest": n_dst,
                "count_match": (n_src == n_dst) and not missing and not extra,
                "n_missing_in_dest": len(missing),
                "n_extra_in_dest": len(extra),
            })
            grand_src_total += n_src
            grand_dst_total += n_dst

            for rel, sp in src_files[e]:
                dp = os.path.join(dst_root, rel)
                pair = (corpus, e, rel, sp, dp)
                all_pairs_for_hash.append(pair)
                if e in (".gpkg", ".parquet"):
                    gpkg_parquet_pairs.append(pair)

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)

    random_sample = random.sample(all_pairs_for_hash, min(200, len(all_pairs_for_hash)))
    hash_targets = {(c, e, r): (sp, dp) for c, e, r, sp, dp in random_sample}
    for c, e, r, sp, dp in gpkg_parquet_pairs:
        hash_targets[(c, e, r)] = (sp, dp)

    hash_rows = []
    n_hash_ok = 0
    n_hash_fail = 0
    n_hash_unreadable = 0
    for (corpus, ext, rel), (sp, dp) in sorted(hash_targets.items()):
        status = "OK"
        src_hash = dst_hash = ""
        try:
            src_hash = sha256_of(sp)
            dst_hash = sha256_of(dp)
            if src_hash != dst_hash:
                status = "HASH_MISMATCH"
                n_hash_fail += 1
            else:
                n_hash_ok += 1
        except OSError as ex:
            status = f"UNREADABLE: {ex}"
            n_hash_unreadable += 1
        hash_rows.append({
            "corpus": corpus, "extension": ext, "relpath": rel,
            "src_sha256": src_hash, "dst_sha256": dst_hash, "status": status,
        })

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["=== COUNT VERIFICATION ==="])
        w.writerow(["corpus", "extension", "n_source", "n_dest", "count_match",
                     "n_missing_in_dest", "n_extra_in_dest"])
        for r in count_rows:
            w.writerow([r["corpus"], r["extension"], r["n_source"], r["n_dest"],
                        r["count_match"], r["n_missing_in_dest"], r["n_extra_in_dest"]])
        w.writerow([])
        w.writerow(["=== HASH VERIFICATION (200 random + all .gpkg/.parquet) ==="])
        w.writerow(["corpus", "extension", "relpath", "src_sha256", "dst_sha256", "status"])
        for r in hash_rows:
            w.writerow([r["corpus"], r["extension"], r["relpath"], r["src_sha256"],
                        r["dst_sha256"], r["status"]])

    print("=== count verification ===")
    all_count_ok = True
    for r in count_rows:
        if r["n_source"] == 0 and r["n_dest"] == 0:
            continue
        flag = "OK" if r["count_match"] else "MISMATCH"
        if not r["count_match"]:
            all_count_ok = False
        print(f"{r['corpus']:24s} {r['extension']:10s} src={r['n_source']:6d} dst={r['n_dest']:6d} {flag}")
    print(f"\ngrand total: src={grand_src_total} dst={grand_dst_total} "
          f"{'MATCH' if grand_src_total == grand_dst_total else 'MISMATCH'}")
    print(f"all per-extension counts match: {all_count_ok}")

    print(f"\n=== hash verification: {len(hash_targets)} files "
          f"({len(random_sample)} random sample + {len(gpkg_parquet_pairs)} gpkg/parquet, "
          f"union) ===")
    print(f"OK={n_hash_ok} MISMATCH={n_hash_fail} UNREADABLE={n_hash_unreadable}")
    if n_hash_fail or n_hash_unreadable:
        print("--- failures ---")
        for r in hash_rows:
            if r["status"] != "OK":
                print(f"  {r['corpus']}/{r['relpath']}: {r['status']}")

    print(f"\nwrote {OUT_CSV}")


if __name__ == "__main__":
    main()
