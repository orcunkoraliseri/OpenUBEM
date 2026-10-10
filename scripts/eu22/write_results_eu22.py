from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

import pandas as pd

from scripts.cluster.harvest_eu11_district import NEW_SITES

EVIDENCE_ROOT = REPO / "openubem" / "outputs" / "eu_evidence" / "EU-11"
DEFAULT_OUT_ROOT = REPO / "openubem" / "outputs" / "eu_evidence" / "EU-22"

PER_HOME_COLUMNS = [
    "district", "building_id", "archetype_id", "building_type", "age_band", "geometry_outcome",
    "floor_area_m2", "heating_kwh", "eui_heating_kwh_m2", "has_result", "eui_source",
    "undivided_excluded_from_2026-10-01", "tag", "supersedes",
]
SUMMARY_COLUMNS = [
    "district", "homes", "homes_with_result", "floor_area_m2", "heating_kwh",
    "eui_heating_kwh_m2", "tag", "supersedes",
]
METRIC = (
    "space-heating demand only; the EU models are heat-only by design (ideal loads, heating 20 C, "
    "cooling setpoint 50 C = never cools; no lighting/DHW objects, internal gains one lump)"
)
EUI_DEFINITION = "sum(heating_kWh) / sum(floor_area_m2) over homes with a completed run"


def _php_json(obj: object) -> str:
    return json.dumps(obj, indent=1, ensure_ascii=False, separators=(",", ":")).replace("/", "\\/") + "\n"


def build_results(site: str, tag: str, evidence_root: Path = EVIDENCE_ROOT) -> dict:
    if site not in NEW_SITES:
        raise ValueError(f"{site}: results are written for {NEW_SITES} only")
    if not tag.startswith("win_"):
        raise ValueError(f"tag {tag!r}: expected win_<date>")
    tree = evidence_root / f"{site}_{tag}"
    manifest_path = tree / f"{site.lower().replace('-', '_')}_manifest.csv"
    left_out_path = tree / "left_out.csv"
    for p in (manifest_path, left_out_path):
        if not p.exists():
            raise FileNotFoundError(f"missing {p}")
    manifest = pd.read_csv(manifest_path, dtype={"building_id": str})
    left_out = pd.read_csv(left_out_path, dtype={"building_id": str})
    if "district" in left_out.columns:
        left_out = left_out[left_out["district"] == site]
    left_out_ids = set(left_out["building_id"])

    kept = manifest[~manifest["building_id"].isin(left_out_ids)].copy()
    left_out_in_manifest = int(manifest["building_id"].isin(left_out_ids).sum())

    rc = pd.to_numeric(kept["eplus_return_code"], errors="coerce")
    heating = pd.to_numeric(kept["heating_kwh"], errors="coerce")
    area = pd.to_numeric(kept["floor_area_m2"], errors="coerce")
    has_result = (rc == 0) & heating.notna() & (area > 0)
    eui = (heating / area).where(has_result)

    per_home = pd.DataFrame({
        "district": site,
        "building_id": kept["building_id"].values,
        "archetype_id": kept["archetype_id"].values,
        "building_type": kept["building_type"].values,
        "age_band": kept["age_band"].values,
        "geometry_outcome": kept["geometry_outcome"].values,
        "floor_area_m2": area.values,
        "heating_kwh": heating.where(has_result).values,
        "eui_heating_kwh_m2": eui.round(6).values,
        "has_result": has_result.values,
        "eui_source": tag,
        "undivided_excluded_from_2026-10-01": False,
        "tag": tag,
        "supersedes": "",
    }, columns=PER_HOME_COLUMNS)

    done = per_home[per_home["has_result"]]
    area_sum = float(done["floor_area_m2"].sum())
    heat_sum = float(done["heating_kwh"].sum())
    summary_row = {
        "district": site,
        "homes": int(len(per_home)),
        "homes_with_result": int(len(done)),
        "floor_area_m2": round(area_sum, 3),
        "heating_kwh": round(heat_sum, 3),
        "eui_heating_kwh_m2": round(heat_sum / area_sum, 6) if area_sum > 0 else None,
        "tag": tag,
        "supersedes": "",
    }
    failed = []
    for i in per_home.index[~per_home["has_result"]]:
        r = kept.iloc[i]
        failed.append({
            "building_id": r["building_id"],
            "reason": f"rc={r['eplus_return_code']},severe={r['severe_errors']},fatal={r['fatal_errors']}",
        })
    return {
        "site": site, "tag": tag, "tree": tree, "per_home": per_home, "summary_row": summary_row,
        "failed": failed, "left_out_total": len(left_out_ids), "left_out_in_manifest": left_out_in_manifest,
        "manifest_rows": int(len(manifest)),
    }


def write_results(result: dict, out_dir: Path) -> list[Path]:
    site, tag = result["site"], result["tag"]
    date = tag[len("win_"):]
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"EU22_results_{site}_{date}"
    per_home = result["per_home"]
    row = result["summary_row"]

    p_csv = out_dir / f"{stem}_per_home.csv"
    per_home.to_csv(p_csv, index=False)

    records = json.loads(per_home.to_json(orient="records"))
    p_json = out_dir / f"{stem}_per_home.json"
    p_json.write_text(_php_json(records), encoding="utf-8")

    s_csv = out_dir / f"{stem}_summary.csv"
    pd.DataFrame([row], columns=SUMMARY_COLUMNS).to_csv(s_csv, index=False)

    summary = {
        "vintage": f"{date} (owner D-EU-149 / D-EU-157: correctly divided homes only)",
        "tag": tag,
        "supersedes": "",
        "metric": METRIC,
        "eui_definition": EUI_DEFINITION,
        "districts": {site: {k: row[k] for k in (
            "homes", "homes_with_result", "floor_area_m2", "heating_kwh", "eui_heating_kwh_m2")}},
        "left_out_not_correctly_divided": result["left_out_in_manifest"],
        "runs_without_result": result["failed"],
    }
    s_json = out_dir / f"{stem}_summary.json"
    s_json.write_text(_php_json(summary), encoding="utf-8")
    return [p_csv, p_json, s_csv, s_json]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", required=True, choices=list(NEW_SITES))
    parser.add_argument("--tag", required=True)
    parser.add_argument("--evidence-root", type=Path, default=EVIDENCE_ROOT)
    parser.add_argument("--out-dir", type=Path, default=None)
    args = parser.parse_args()
    out_dir = args.out_dir or (DEFAULT_OUT_ROOT / args.site / "results")
    result = build_results(args.site, args.tag, args.evidence_root)
    paths = write_results(result, out_dir)
    r = result["summary_row"]
    print(f"[{args.site}] manifest rows {result['manifest_rows']}, left out {result['left_out_in_manifest']}, "
          f"kept {r['homes']}, with result {r['homes_with_result']}, runs without result {len(result['failed'])}")
    print(f"[{args.site}] EUI {r['eui_heating_kwh_m2']} kWh/m2 over {r['floor_area_m2']} m2")
    for p in paths:
        print(f"  {p}")


if __name__ == "__main__":
    main()
