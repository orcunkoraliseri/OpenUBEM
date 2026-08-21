import pandas as pd

ERR_CSV = r"C:\Users\o_iseri\Desktop\OpenUBEM\openubem\outputs\comparisons\open56_open09_run4_err_census_2026-08-20.csv"
FATAL_CSV = r"C:\Users\o_iseri\Desktop\OpenUBEM\openubem\outputs\comparisons\open38_fatal_causes_2026-08-20.csv"
OUT = r"C:\Users\o_iseri\Desktop\OpenUBEM\openubem\outputs\comparisons\open09_open38_overlap_2026-08-21.csv"
HARVEST_ROOT = r"C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest"

err = pd.read_csv(ERR_CSV)
fatal = pd.read_csv(FATAL_CSV)


def norm(s):
    return str(s).strip().lower().replace("/", "_")


A = err[err["has_converge"] == True].copy()
A["stem_norm"] = A["stem"].apply(norm)
assert len(A) == 16, f"C22 failed: |A|={len(A)}"
print("C22:", len(A), A["cell"].value_counts().to_dict())

B = fatal.copy()
B["stem_norm"] = B["stem"].apply(norm)
assert len(B) == 44, f"C23 failed: |B|={len(B)}"
print("C23:", len(B))

B_auto = B[B["mode"] == "auto"].copy()
print("B restricted to mode=='auto': n =", len(B_auto))

set_A = set(zip(A["cell"], A["stem_norm"]))
set_B = set(zip(B["cell"], B["stem_norm"]))
set_B_auto = set(zip(B_auto["cell"], B_auto["stem_norm"]))

overlap_all = set_A & set_B
overlap_auto = set_A & set_B_auto

print(f"|A x B| (any mode) = {len(overlap_all)}")
print(f"|A x B| (B restricted to mode=='auto') = {len(overlap_auto)}")

print("\n=== Population A, full (16 rows) ===")
print(A[["cell", "stem", "osm_id", "archetype_id"]].to_string(index=False))

print("\n=== A members that ARE in B (any mode) ===")
in_b = A[A.apply(lambda r: (r["cell"], r["stem_norm"]) in set_B, axis=1)]
print(in_b[["cell", "stem", "osm_id", "archetype_id"]].to_string(index=False) if len(in_b) else "(none)")

not_in_b = A[~A.apply(lambda r: (r["cell"], r["stem_norm"]) in set_B, axis=1)]
print(f"\n=== A members NOT in B: n = {len(not_in_b)} ===")


def has_calcheatbalance_line(cell, stem):
    import os
    err_path = os.path.join(HARVEST_ROOT, f"{cell}_auto", stem, "eplusout.err")
    if not os.path.exists(err_path):
        return "err_file_missing"
    try:
        with open(err_path, "r", errors="replace") as f:
            for line in f:
                if "CalcHeatBalanceInsideSurf" in line:
                    return True
        return False
    except Exception as e:
        return f"read_error:{e}"


rows_out = []
for _, r in A.iterrows():
    in_b_flag = (r["cell"], r["stem_norm"]) in set_B
    in_b_auto_flag = (r["cell"], r["stem_norm"]) in set_B_auto
    rec = {
        "cell": r["cell"], "stem": r["stem"], "osm_id": r["osm_id"],
        "archetype_id": r["archetype_id"], "in_fatal_44": in_b_flag,
        "in_fatal_44_auto_mode": in_b_auto_flag,
    }
    if not in_b_flag:
        rec["calcheatbalance_in_auto_err"] = has_calcheatbalance_line(r["cell"], r["stem"])
    rows_out.append(rec)

out_df = pd.DataFrame(rows_out)
out_df.to_csv(OUT, index=False)
print(f"\nWritten: {len(out_df)} rows -> {OUT}")

print("\n=== full out table ===")
print(out_df.to_string(index=False))
