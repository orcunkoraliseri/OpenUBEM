from __future__ import annotations

from pathlib import Path

import pandas as pd

G = Path(__file__).resolve().parents[2] / "openubem" / "outputs" / "eu_evidence" / "EU-11" / "geometry_24_2026-10-10"
S = {"dtype": {"building_id": str, "engine": str, "frame": str}}
parts = {
    "driver_abs": pd.read_csv(G / "rebuild_all.csv", **S).query("frame == 'abs'"),
    "driver_local": pd.read_csv(G / "rebuild_all.csv", **S).query("frame == 'local'"),
    "sidecar_raw": pd.read_csv(G / "rebuild_sidecar_all.csv", **S).query("engine.str.endswith('_raw')", engine="python"),
    "sidecar_stab": pd.read_csv(G / "rebuild_sidecar_all.csv", **S).query("engine.str.endswith('_stab')", engine="python"),
    "fork_abs": pd.read_csv(G / "rebuild_fork_all.csv", **S),
    "fork_local": pd.read_csv(G / "rebuild_fork_local_all.csv", **S),
}
rows = []
for name, df in parts.items():
    df = df.copy()
    df["engine_short"] = df.engine.str.replace("_raw|_stab|_fork|local", "", regex=True).str.replace("^e", "", regex=True)
    df["engine_short"] = df.engine_short.replace({"1006": "pin_1006"})
    for (eng, bid), g in df.groupby(["engine_short", "building_id"]):
        r = g.iloc[0]
        rows.append({
            "variant": name, "engine": eng, "building_id": bid, "status": r["status"],
            "fork_verdict": r.get("fork_verdict", ""),
            "raw_mismatch_pairs": r["raw_count_mismatch_pairs"], "effective_mismatch_pairs": r["effective_count_mismatch_pairs"],
            "neardup_or_collinear_pairs": r["pairs_with_neardup_or_collinear"], "slivers_lt_1e-6": r["surfaces_lt_1e-6_m2"],
            "surfaces": r["surfaces"],
        })
t = pd.DataFrame(rows)
t.to_csv(G / "t04_table.csv", index=False)
for c in ("raw_mismatch_pairs", "effective_mismatch_pairs", "neardup_or_collinear_pairs", "slivers_lt_1e-6"):
    t[c] = pd.to_numeric(t[c])
s = t.groupby(["variant", "engine"]).agg(
    n=("building_id", "count"), built=("status", lambda x: (x == "ok").sum()),
    refused=("fork_verdict", lambda x: x.fillna("").str.startswith("REFUSED").sum()),
    tolerated=("fork_verdict", lambda x: (x == "tolerated_near_duplicate").sum()),
    raw_mismatch=("raw_mismatch_pairs", lambda x: (x > 0).sum()), eff_mismatch=("effective_mismatch_pairs", lambda x: (x > 0).sum()),
    neardup=("neardup_or_collinear_pairs", lambda x: (x > 0).sum()), sliver=("slivers_lt_1e-6", lambda x: (x > 0).sum()),
).reset_index()
s.to_csv(G / "t04_summary.csv", index=False)
print(s.to_string())
