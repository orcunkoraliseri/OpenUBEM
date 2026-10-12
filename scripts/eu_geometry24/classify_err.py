from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
G = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-11" / "geometry_24_2026-10-10"

PATTERNS = {
    "vertex_mismatch": re.compile(r"\*\* Severe  \*\* .*Vertex size mismatch"),
    "zero_or_negative": re.compile(r"\*\* Severe  \*\* GetSurfaceData: Zero or negative"),
    "non_planar": re.compile(r"\*\* Severe  \*\* CheckConvexity: .*non-planar"),
    "invalid_dot_product": re.compile(r"Invalid dot product"),
    "very_small_warn": re.compile(r"Very small surface area"),
    "coincident_warn": re.compile(r"coincident/collinear vertices"),
}
DEGEN = re.compile(r"There are (\d+) degenerate surfaces")


def cell_of(name: str) -> str:
    return re.sub(r"\.eplusout\.err$", "", name)


def building_of(cell: str, fold: str) -> str:
    m = re.match(r"(?:es|it)__(.+?)__case([AB])__f(\d+)", cell)
    b = m.group(1)
    return b.replace("relation-", "relation/").replace("way-", "way/") if fold == "ES" else b


def scan(err_dir: Path, fold: str):
    rows = []
    for f in sorted(err_dir.glob("*.eplusout.err")):
        txt = f.read_text(encoding="utf-8", errors="replace").splitlines()
        r = {"fold": fold, "cell": cell_of(f.name)}
        for k, p in PATTERNS.items():
            r[k] = sum(1 for ln in txt if p.search(ln))
        r["degenerate_surfaces"] = sum(int(m.group(1)) for ln in txt for m in [DEGEN.search(ln)] if m)
        r["fatal"] = int(any("Fatal error" in ln for ln in txt))
        r["err_bytes"] = f.stat().st_size
        r["building_id"] = building_of(r["cell"], fold)
        m = re.search(r"case([AB])__f(\d+)", r["cell"])
        r["case"], r["f"] = m.group(1), m.group(2)
        rows.append(r)
    return rows


def failed(fj_dir: Path, fold: str):
    rows = []
    for f in sorted(fj_dir.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        fl = d.get("failure", {})
        err = str(fl.get("error", ""))
        rows.append({
            "fold": fold, "cell": f.stem, "building_id": str(d.get("building_id")),
            "completion_status": d.get("completion_status"),
            "harness_error": err.split(":")[0] + ":" + err.split(":")[1] if err.count(":") >= 1 and err else "",
            "returncode": fl.get("returncode"), "engine_sha256": d.get("engine_sha256", "")[:12],
            "platform": d.get("platform"), "zone_count_emitted": d.get("zone_count_emitted"),
        })
    return rows


def main():
    err = pd.DataFrame(scan(G / "4J_madrid" / "err", "ES") + scan(G / "4J_bologna" / "err", "IT"))
    fj = pd.DataFrame(failed(G / "4J_madrid" / "cells_failed", "ES") + failed(G / "4J_bologna" / "cells_failed", "IT"))
    err.to_csv(G / "err_signatures_per_cell.csv", index=False)
    fj.to_csv(G / "cells_failed_per_cell.csv", index=False)
    agg = err.groupby(["fold", "building_id"]).agg(
        cells_with_err=("cell", "nunique"),
        vertex_mismatch=("vertex_mismatch", "sum"), zero_or_negative=("zero_or_negative", "sum"),
        non_planar=("non_planar", "sum"), invalid_dot_product=("invalid_dot_product", "sum"),
        degenerate_surfaces=("degenerate_surfaces", "sum"), very_small_warn=("very_small_warn", "sum"),
        fatal_cells=("fatal", "sum"),
    ).reset_index()
    f0 = err[(err["case"] == "A") & (err["f"] == "000")][["fold", "building_id", "vertex_mismatch", "zero_or_negative", "non_planar", "degenerate_surfaces", "invalid_dot_product"]]
    f0 = f0.rename(columns={c: c + "_A_f000" for c in f0.columns if c not in ("fold", "building_id")})
    fja = fj.groupby(["fold", "building_id"]).agg(
        cells_failed_json=("cell", "nunique"),
        statuses=("completion_status", lambda s: "|".join(sorted(set(map(str, s))))),
        harness_error=("harness_error", lambda s: "|".join(sorted(set(x for x in s if x)))),
    ).reset_index()
    out = agg.merge(f0, on=["fold", "building_id"], how="outer").merge(fja, on=["fold", "building_id"], how="outer")
    out.to_csv(G / "err_signatures_per_building.csv", index=False)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    print(out.drop(columns=["harness_error"]).to_string())
    print(out["harness_error"].value_counts().to_string())


if __name__ == "__main__":
    main()
