from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from harvest_eu11_district import EVIDENCE_ROOT, MANIFEST_COLUMNS  # noqa: E402,F401

LOW, HIGH = 0.8, 1.25
FLOOR_LOW, FLOOR_HIGH = 0.98, 1.02


def slug_of(district: str) -> str:
    return district.lower().replace("-", "_")


def _stats(s: pd.Series) -> dict:
    s = s.dropna()
    if s.empty:
        return {"median": None, "p05": None, "p95": None}
    return {
        "median": float(s.median()),
        "p05": float(np.percentile(s, 5)),
        "p95": float(np.percentile(s, 95)),
    }


REASONS = ("t06g_fault", "floor_changed", "outcome_changed", "hidden_0908", "storey_outline", "unexplained")
HIDDEN_SHARE_MIN = 0.02
HIDDEN_TREES = ("noncandidate_2026-09-08", "baseline_2026-09-08")
RESIDUAL_DIR = "division_residual_2026-09-29"


def load_aux(district: str, root: Path = EVIDENCE_ROOT) -> dict:
    d = root / RESIDUAL_DIR
    hid = pd.read_csv(d / "hidden_outdoor_scan.csv")
    hid = hid[(hid["district"] == district) & hid["tree"].isin(HIDDEN_TREES)]
    gate = pd.read_csv(d / f"t06e_gate_{district}.csv")
    t06g = pd.read_csv(d / "t06g_stems_director_2026-10-01.csv")
    t06g = t06g[t06g["district"] == district]
    return {"hidden": hid, "gate": gate, "t06g": t06g}


def _name_reasons(j: pd.DataFrame, aux: dict | None) -> pd.DataFrame:
    j = j.copy()
    j["hidden_share_0908"] = np.nan
    j["union_ratio_vs_0908"] = np.nan
    gate_g4 = pd.Series(True, index=j.index)
    gate_const = pd.Series(True, index=j.index)
    t06g_ids: set = set()
    if aux is not None:
        hid = aux["hidden"].drop_duplicates("building_id").set_index("building_id")
        env = hid["outdoor_wall_m2"] + hid["roof_m2"] + hid["ground_floor_m2"] + hid["outdoor_floor_m2"]
        share = (hid["hidden_outdoor_m2"] + hid["hidden_ground_m2"]) / env.where(env > 0)
        j["hidden_share_0908"] = j["building_id"].map(share)
        gate = aux["gate"].drop_duplicates("building_id").set_index("building_id")
        j["union_ratio_vs_0908"] = j["building_id"].map(gate["union_ratio_vs_0908"])
        gate_g4 = j["building_id"].map(gate["G4"]).map(lambda v: v is not False and v != "False")
        gate_const = j["building_id"].map(gate["constant_outline"]).map(lambda v: v is not False and v != "False")
        t06g_ids = set(aux["t06g"]["building_id"])
    r1 = j["building_id"].isin(t06g_ids) & (j["idf_variant"].astype(str) != "t06g")
    r2 = j["floor_changed"]
    r3 = j["geometry_outcome_new"] != j["geometry_outcome_old"]
    r4 = (j["hidden_share_0908"] >= HIDDEN_SHARE_MIN) & (j["heating_ratio"] < 1)
    ur = j["union_ratio_vs_0908"]
    r5 = ((ur < FLOOR_LOW) | (ur > FLOOR_HIGH)) | (~gate_g4 & ~gate_const)
    reason = pd.Series("unexplained", index=j.index)
    for name, m in reversed(list(zip(REASONS[:5], (r1, r2, r3, r4, r5)))):
        reason[m.fillna(False).astype(bool)] = name
    j["reason"] = np.where(j["flag_out"], reason, "")
    return j


NOWIN_SOURCE = "fix_2026-10-01"


def _spearman(a: pd.Series, b: pd.Series) -> float | None:
    d = pd.DataFrame({"a": a, "b": b}).dropna()
    if len(d) < 3:
        return None
    v = d["a"].rank().corr(d["b"].rank())
    return None if pd.isna(v) else float(v)


def compare_nowin(new: pd.DataFrame, base: pd.DataFrame, label: str = "nowin") -> tuple[pd.DataFrame, dict]:
    new = new.copy()
    new["eplus_return_code"] = pd.to_numeric(new["eplus_return_code"], errors="coerce")
    new = new[new["eplus_return_code"] == 0]
    base = base[base["eui_source"] == NOWIN_SOURCE].copy()
    num = ("heating_kwh", "floor_area_m2", "eui_kwh_m2")
    for c in num:
        new[c] = pd.to_numeric(new[c], errors="coerce")
        base[c] = pd.to_numeric(base[c], errors="coerce")
    base = base[base["eui_kwh_m2"].notna()]
    keep = ["building_id", "geometry_outcome", "idf_variant", *num]
    if "idf_variant" not in new.columns:
        new["idf_variant"] = ""
    extra = [c for c in ("window_m2", "outdoor_wall_m2") if c in new.columns]
    for c in extra:
        new[c] = pd.to_numeric(new[c], errors="coerce")
    j = new[keep + extra].merge(
        base[["building_id", "geometry_outcome", *num]], on="building_id", suffixes=("", f"_{label}"),
    )
    j["eui_ratio"] = j["eui_kwh_m2"] / j[f"eui_kwh_m2_{label}"]
    j["heating_ratio"] = j["heating_kwh"] / j[f"heating_kwh_{label}"]
    j["floor_area_ratio"] = j["floor_area_m2"] / j[f"floor_area_m2_{label}"]
    if "window_m2" in j.columns:
        j["window_m2_per_floor_m2"] = j["window_m2"] / j["floor_area_m2"]
    summary = {
        "n_joined": int(len(j)),
        "eui_ratio": _stats(j["eui_ratio"]),
        "heating_ratio": _stats(j["heating_ratio"]),
        "floor_area_ratio": _stats(j["floor_area_ratio"]),
        "heating_ratio_vs_window_spearman": (
            _spearman(j["heating_ratio"], j["window_m2_per_floor_m2"]) if "window_m2_per_floor_m2" in j.columns else None
        ),
        "n_zero_window_ratio_outside_0.99_1.01": (
            int(((j["window_m2"] == 0) & ((j["heating_ratio"] < 0.99) | (j["heating_ratio"] > 1.01))).sum())
            if "window_m2" in j.columns else None
        ),
        "n_heating_ratio_below_1": int((j["heating_ratio"] < 1.0).sum()),
    }
    return j, summary


def compare(new: pd.DataFrame, base: pd.DataFrame, aux: dict | None = None) -> tuple[pd.DataFrame, dict]:
    new = new.copy()
    new["eplus_return_code"] = pd.to_numeric(new["eplus_return_code"], errors="coerce")
    new = new[new["eplus_return_code"] == 0]
    base = base.copy()
    base["eui_kwh_m2"] = pd.to_numeric(base["eui_kwh_m2"], errors="coerce")
    base = base[base["eui_kwh_m2"].notna()]
    if "idf_variant" not in new.columns:
        new["idf_variant"] = ""
    for c in ("heating_kwh", "floor_area_m2", "eui_kwh_m2"):
        new[c] = pd.to_numeric(new[c], errors="coerce")
        base[c] = pd.to_numeric(base[c], errors="coerce")
    j = new[["building_id", "geometry_outcome", "idf_variant", "heating_kwh", "floor_area_m2", "eui_kwh_m2"]].merge(
        base[["building_id", "geometry_outcome", "heating_kwh", "floor_area_m2", "eui_kwh_m2"]],
        on="building_id", suffixes=("_new", "_old"),
    )
    j["eui_ratio"] = j["eui_kwh_m2_new"] / j["eui_kwh_m2_old"]
    j["heating_ratio"] = j["heating_kwh_new"] / j["heating_kwh_old"]
    j["floor_area_ratio"] = j["floor_area_m2_new"] / j["floor_area_m2_old"]
    j = j.rename(columns={"geometry_outcome_new": "geometry_outcome_new", "geometry_outcome_old": "geometry_outcome_old"})
    j["flag_out"] = (j["eui_ratio"] < LOW) | (j["eui_ratio"] > HIGH)
    j["floor_changed"] = (j["floor_area_ratio"] < FLOOR_LOW) | (j["floor_area_ratio"] > FLOOR_HIGH)
    j = _name_reasons(j, aux)
    fl = j[j["flag_out"]]
    by_variant = {}
    for v, g in j.groupby("idf_variant"):
        gf = g[g["flag_out"]]
        by_variant[str(v)] = {
            "n": int(len(g)),
            "flag_out": int(len(gf)),
            "flag_floor_changed": int(gf["floor_changed"].sum()),
            "flag_heating_only": int((~gf["floor_changed"]).sum()),
        }
    pooled_new = j["heating_kwh_new"].sum() / j["floor_area_m2_new"].sum() if len(j) else None
    pooled_old = j["heating_kwh_old"].sum() / j["floor_area_m2_old"].sum() if len(j) else None
    summary = {
        "n_joined": int(len(j)),
        "eui_ratio": _stats(j["eui_ratio"]),
        "heating_ratio": _stats(j["heating_ratio"]),
        "floor_area_ratio": _stats(j["floor_area_ratio"]),
        "flag_out": int(len(fl)),
        "flag_floor_changed": int(fl["floor_changed"].sum()),
        "flag_heating_only": int((~fl["floor_changed"]).sum()),
        "by_idf_variant": by_variant,
        "reason_counts": {r: int((fl["reason"] == r).sum()) for r in REASONS},
        "pooled_eui_new": None if pooled_new is None else float(pooled_new),
        "pooled_eui_old_0908": None if pooled_old is None else float(pooled_old),
    }
    return j, summary


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--district", required=True)
    p.add_argument("--manifest", required=True)
    p.add_argument("--out-prefix", default=None)
    p.add_argument("--tag-label", default="early_2026-10-01")
    p.add_argument("--base", default=None)
    p.add_argument("--base-label", default="0908")
    a = p.parse_args()
    slug = slug_of(a.district)
    new = pd.read_csv(a.manifest)
    base_path = Path(a.base) if a.base else EVIDENCE_ROOT / f"{a.district}_merged_2026-09-08" / f"{slug}_manifest.csv"
    base = pd.read_csv(base_path)
    nowin_base = "eui_source" in base.columns and bool((base["eui_source"] == NOWIN_SOURCE).any())
    if nowin_base:
        j, summary = compare_nowin(new, base, a.base_label)
    else:
        j, summary = compare(new, base, load_aux(a.district))
    prefix = Path(a.out_prefix) if a.out_prefix else (
        EVIDENCE_ROOT / "division_residual_2026-09-29" / f"eui_ratio_{slug}_{a.tag_label}"
    )
    prefix.parent.mkdir(parents=True, exist_ok=True)
    j.to_csv(f"{prefix}.csv", index=False)
    Path(f"{prefix}_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if nowin_base:
        print(a.district, json.dumps(summary))
        return
    print(a.district, json.dumps({k: summary[k] for k in ("n_joined", "flag_out", "flag_floor_changed", "flag_heating_only", "reason_counts", "pooled_eui_new", "pooled_eui_old_0908")}))


if __name__ == "__main__":
    main()
