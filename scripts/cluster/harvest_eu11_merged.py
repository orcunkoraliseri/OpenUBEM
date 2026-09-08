from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

import pandas as pd

from scripts.cluster.harvest_eu11_district import (
    EVIDENCE_ROOT,
    MANIFEST_COLUMNS,
    harvest_district,
)

MERGE_DATE = "2026-09-07"
FINAL_TAG = f"final_{MERGE_DATE}"
DELTA_TAG = f"delta_{MERGE_DATE}"
CEILING_TAG = "ceiling82_2026-09-05"

IDENTITY_COLUMNS = [
    "building_id", "archetype_id", "building_type", "age_band", "geometry_outcome",
    "construction_period_provenance", "idf_sha256", "weather_sha256",
]
RESULT_COLUMNS = [c for c in MANIFEST_COLUMNS if c not in IDENTITY_COLUMNS]

DISTRICTS = [
    "ES-MAD-BERRUGUETE", "FR-LYO-HAUTCOEURPENTES", "GB-LDN-STDUNSTANS", "IT-BOL-GALVANI2",
]

DISCLOSURES = {
    "FR-LYO-HAUTCOEURPENTES": [
        "stem cee45cbc2718154c was rebuilt from 29 dwelling zones to 8 one_zone_per_floor "
        "zones with the courtyard filled, so its floor area and EUI denominator differ from "
        "every earlier manifest.",
    ],
}


def _dist_dir(district: str, tag: str) -> Path:
    return EVIDENCE_ROOT / f"{district}_{tag}"


def _slug(district: str) -> str:
    return district.lower().replace("-", "_")


def _manifest_path(district: str, tag: str) -> Path:
    return _dist_dir(district, tag) / f"{_slug(district)}_manifest.csv"


def _load_manifest(district: str, tag: str) -> pd.DataFrame | None:
    path = _manifest_path(district, tag)
    if not path.exists():
        return None
    return pd.read_csv(path, dtype=str)


def _rc_zero_index(manifest: pd.DataFrame | None) -> dict[str, dict]:
    if manifest is None:
        return {}
    rc = pd.to_numeric(manifest["eplus_return_code"], errors="coerce")
    ok = manifest.loc[rc == 0].set_index("building_id", drop=False)
    return {str(k): v for k, v in ok.to_dict(orient="index").items()}


def build_merged_manifest(district: str, dry_run: bool) -> tuple[pd.DataFrame, dict]:
    final_dir = _dist_dir(district, FINAL_TAG)
    prepared_path = final_dir / "prepared_buildings.csv"
    if not prepared_path.exists():
        raise FileNotFoundError(f"missing {prepared_path}")
    prepared = pd.read_csv(prepared_path, dtype=str)

    if not dry_run:
        work_base = Path(tempfile.gettempdir()) / "ubem_eu11_harvest"
        work_base.mkdir(parents=True, exist_ok=True)
        harvest_district(district, work_base, tag=FINAL_TAG)
        harvest_district(district, work_base, tag=DELTA_TAG)

    final_ok = _rc_zero_index(_load_manifest(district, FINAL_TAG))
    delta_ok = _rc_zero_index(_load_manifest(district, DELTA_TAG))
    ceiling_manifest = _load_manifest(district, CEILING_TAG)
    ceiling_ok = _rc_zero_index(ceiling_manifest)
    ceiling_sha = {}
    if ceiling_manifest is not None:
        ceiling_sha = dict(
            zip(
                ceiling_manifest["building_id"].astype(str),
                ceiling_manifest["idf_sha256"].astype(str),
            )
        )

    rows = []
    counts = {DELTA_TAG: 0, FINAL_TAG: 0, "ceiling82_carry": 0, "pending_resimulation": 0}
    for _, prow in prepared.iterrows():
        building_id = str(prow["building_id"])
        idf_sha256 = str(prow["idf_sha256"])
        matches_ceiling = ceiling_sha.get(building_id) == idf_sha256

        if building_id in delta_ok:
            eui_source, source_row = DELTA_TAG, delta_ok[building_id]
        elif building_id in final_ok:
            eui_source, source_row = FINAL_TAG, final_ok[building_id]
        elif matches_ceiling and building_id in ceiling_ok:
            eui_source, source_row = "ceiling82_carry", ceiling_ok[building_id]
        else:
            eui_source, source_row = "pending_resimulation", None

        counts[eui_source] += 1

        row = {c: prow.get(c, pd.NA) for c in IDENTITY_COLUMNS}
        row["building_id"] = building_id
        row["idf_sha256"] = idf_sha256
        for c in RESULT_COLUMNS:
            row[c] = source_row[c] if source_row is not None else pd.NA
        row["eui_source"] = eui_source
        row["idf_sha256_matches_ceiling82"] = matches_ceiling
        rows.append(row)

    columns = MANIFEST_COLUMNS + ["eui_source", "idf_sha256_matches_ceiling82"]
    manifest = pd.DataFrame(rows, columns=columns)
    return manifest, counts


def build_summary(district: str, manifest: pd.DataFrame, counts: dict) -> dict:
    n_rows = len(manifest)
    n_pending = counts["pending_resimulation"]
    n_with_eui = n_rows - n_pending

    with_eui = manifest[manifest["eui_source"] != "pending_resimulation"]
    heating = pd.to_numeric(with_eui["heating_kwh"], errors="coerce")
    area = pd.to_numeric(with_eui["floor_area_m2"], errors="coerce")
    area_sum = float(area.sum())
    pooled_eui = float(heating.sum() / area_sum) if n_with_eui and area_sum > 0 else None

    ceiling_summary_path = _dist_dir(district, CEILING_TAG) / "summary.json"
    ceiling_pooled_eui = None
    if ceiling_summary_path.exists():
        ceiling_pooled_eui = json.loads(
            ceiling_summary_path.read_text(encoding="utf-8")
        ).get("pooled_eui_kwh_m2")

    delta_eui = (
        pooled_eui - ceiling_pooled_eui
        if pooled_eui is not None and ceiling_pooled_eui is not None
        else None
    )

    return {
        "district": district,
        "counts_by_eui_source": counts,
        "n_rows": n_rows,
        "n_with_eui": n_with_eui,
        "n_pending": n_pending,
        "pooled_eui_kwh_m2": round(pooled_eui, 6) if pooled_eui is not None else None,
        "pooled_eui_population": (
            f"{n_with_eui} of {n_rows} buildings with eui_source in "
            f"{{{FINAL_TAG}, {DELTA_TAG}, ceiling82_carry}}"
        ),
        "ceiling82_pooled_eui_kwh_m2": ceiling_pooled_eui,
        "ceiling82_pooled_eui_kwh_m2_delta": round(delta_eui, 6) if delta_eui is not None else None,
        "disclosures": DISCLOSURES.get(district, []),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--district", required=True, choices=DISTRICTS)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    manifest, counts = build_merged_manifest(args.district, args.dry_run)
    summary = build_summary(args.district, manifest, counts)

    if args.dry_run:
        print(f"EU-11 merged harvest (dry-run) - {args.district}")
        for tag in [DELTA_TAG, FINAL_TAG, "ceiling82_carry", "pending_resimulation"]:
            print(f"  {tag}: {counts[tag]}")
        return

    out_dir = _dist_dir(args.district, "merged_2026-09-07")
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / f"{_slug(args.district)}_manifest.csv"
    manifest.to_csv(manifest_path, index=False)
    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[{args.district}] merged manifest written: {manifest_path} ({len(manifest)} rows)")
    print(f"[{args.district}] merged summary written: {summary_path}")


if __name__ == "__main__":
    main()
