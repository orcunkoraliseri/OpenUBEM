from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

import pandas as pd

from scripts.cluster.harvest_eu11_district import (
    EVIDENCE_ROOT,
    WIN5_TAG,
    WIN6_TAG,
    MANIFEST_COLUMNS,
    harvest_district,
)

MERGE_DATE = "2026-09-07"
FINAL_TAG = f"final_{MERGE_DATE}"
DELTA_TAG = f"delta_{MERGE_DATE}"
CEILING_TAG = "ceiling82_2026-09-05"
RECUT_TAG = "recut_2026-09-08"
FIX_TAG = "fix_2026-09-29"
FIX3_TAG = "fix_2026-10-01"
WIN_TAG = "win_2026-10-01"
WIN_TAGS = (WIN_TAG, WIN5_TAG, WIN6_TAG)
WIN5_EXTRA_COLUMNS = ["dwellings_used", "dwellings_source"]
UNDIVIDED_CSV_PARTS_WIN5 = ("division_residual_2026-09-29", "undivided_excluded_2026-10-05.csv")
UNDIVIDED_CSV_COLUMNS = ["district", "building_id", "stem", "geometry_outcome", "storeys", "gross_area_m2", "fleet_index"]
_ZONE_NAME_RE = re.compile(r"^[ \t]*ZONE,[ \t]*(?:![^\n]*)?\n[ \t]*([^,;!\n]+)", re.IGNORECASE | re.MULTILINE)
NOWIN_MERGED_TAG = "merged_2026-10-01"
WIN_EXTRA_COLUMNS = ["window_m2", "outdoor_wall_m2", "share_achieved", "fallback", "source_tree"]
HELD_BACK_FINDING280_STEMS = {
    "ES-MAD-BERRUGUETE": ["d0787f31dc827e89", "b56bda9013da5b2d", "d342db5179c1ac49"],
    "IT-BOL-GALVANI2": ["d32f27af52ecab2c", "a53d307eac631355"],
}
BASE_MERGED_TAG = "merged_2026-09-08"
UNDIVIDED_REASON = "UNDIVIDED_NOT_SIMULATED_D-EU-139"
GEOMETRY_FAULT_REASON = "GEOMETRY_FAULT_FINDING_291"
GEOMETRY_FAULT_CSV_PARTS = ("division_residual_2026-09-29", "geometry_fault_excluded_2026-10-06.csv")
UNDIVIDED_CSV_PARTS = ("division_residual_2026-09-29", "undivided_excluded_2026-10-01.csv")

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


def _undivided_ids(district: str) -> set[str]:
    path = EVIDENCE_ROOT.joinpath(*UNDIVIDED_CSV_PARTS)
    if not path.exists():
        raise FileNotFoundError(f"missing {path}")
    df = pd.read_csv(path, dtype=str)
    return set(df.loc[df["district"] == district, "building_id"].astype(str))


def _undivided_ids_win5(district: str) -> set[str]:
    path = EVIDENCE_ROOT.joinpath(*UNDIVIDED_CSV_PARTS_WIN5)
    if not path.exists():
        raise FileNotFoundError(f"missing {path}")
    df = pd.read_csv(path, dtype=str)
    return set(df.loc[df["district"] == district, "building_id"].astype(str))


def _geometry_fault_ids(district: str) -> set[str]:
    path = EVIDENCE_ROOT.joinpath(*GEOMETRY_FAULT_CSV_PARTS)
    if not path.exists():
        raise FileNotFoundError(f"missing {path}")
    df = pd.read_csv(path, dtype=str)
    return set(df.loc[df["district"] == district, "building_id"].astype(str))


def _stems_without_dwelling_zone(idf_dir: Path) -> list[str]:
    out = []
    for p in sorted(idf_dir.glob("*.idf")):
        names = _ZONE_NAME_RE.findall(p.read_text(encoding="utf-8", errors="replace"))
        if not any("_dwelling_" in n.lower() for n in names):
            out.append(p.stem)
    return out


def build_undivided_win5(district: str) -> pd.DataFrame:
    win_dir = _dist_dir(district, WIN5_TAG)
    prepared = pd.read_csv(win_dir / "prepared_buildings.csv", dtype=str)
    by_stem = prepared.drop_duplicates("stem").set_index("stem", drop=False)
    old = pd.read_csv(EVIDENCE_ROOT.joinpath(*UNDIVIDED_CSV_PARTS), dtype=str)
    rows = old.loc[old["district"] == district, UNDIVIDED_CSV_COLUMNS].to_dict(orient="records")
    have = {r["building_id"] for r in rows}
    fleet = [s.strip() for s in (win_dir / "fleet.lst").read_text(encoding="utf-8").splitlines() if s.strip()]
    fleet_index = {s: str(i) for i, s in enumerate(fleet, start=1)}
    buildings_path = REPO / "openubem" / "outputs" / "3D" / f"eu_{district}_data" / "buildings.csv"
    bmap = {}
    if buildings_path.exists():
        b = pd.read_csv(buildings_path, dtype=str).drop_duplicates("building_id").set_index("building_id")
        bmap = b.to_dict(orient="index")
    for stem in _stems_without_dwelling_zone(win_dir / "idfs"):
        prow = by_stem.loc[stem]
        bid = str(prow["building_id"])
        if bid in have:
            continue
        have.add(bid)
        info = bmap.get(bid, {})
        rows.append({
            "district": district, "building_id": bid, "stem": stem,
            "geometry_outcome": prow["geometry_outcome"],
            "storeys": info.get("storey_count", ""), "gross_area_m2": info.get("gross_area_m2", ""),
            "fleet_index": fleet_index.get(stem, ""),
        })
    return pd.DataFrame(rows, columns=UNDIVIDED_CSV_COLUMNS)


def write_undivided_win5() -> Path:
    path = EVIDENCE_ROOT.joinpath(*UNDIVIDED_CSV_PARTS_WIN5)
    df = pd.concat([build_undivided_win5(d) for d in DISTRICTS], ignore_index=True)
    df.to_csv(path, index=False)
    return path


def _build_fix_manifest(district: str, dry_run: bool) -> tuple[pd.DataFrame, dict]:
    base = _load_manifest(district, BASE_MERGED_TAG)
    if base is None:
        raise FileNotFoundError(f"missing {_manifest_path(district, BASE_MERGED_TAG)}")
    fix_prepared_path = _dist_dir(district, FIX_TAG) / "prepared_buildings.csv"
    if not fix_prepared_path.exists():
        raise FileNotFoundError(f"missing {fix_prepared_path}")
    fix_prepared_ids = set(pd.read_csv(fix_prepared_path, dtype=str)["building_id"].astype(str))

    if not dry_run:
        work_base = Path(tempfile.gettempdir()) / "ubem_eu11_harvest"
        work_base.mkdir(parents=True, exist_ok=True)
        harvest_district(district, work_base, tag=FIX_TAG)

    fix_ok = _rc_zero_index(_load_manifest(district, FIX_TAG))
    counts = {FIX_TAG: 0, "fix_failed_carry": 0, "merged_2026-09-08_carry": 0, "pending_resimulation": 0}

    rows = []
    for _, brow in base.iterrows():
        building_id = str(brow["building_id"])
        row = {c: brow.get(c, pd.NA) for c in MANIFEST_COLUMNS}
        base_source = brow.get("eui_source", pd.NA)
        if base_source == "pending_resimulation":
            eui_source = "pending_resimulation"
        elif building_id in fix_ok:
            eui_source = FIX_TAG
            for c in MANIFEST_COLUMNS:
                row[c] = fix_ok[building_id][c]
        elif building_id in fix_prepared_ids:
            eui_source = "fix_failed_carry"
        else:
            eui_source = "merged_2026-09-08_carry"
        counts[eui_source] += 1
        row["eui_source"] = eui_source
        row["idf_sha256_matches_ceiling82"] = brow.get("idf_sha256_matches_ceiling82", pd.NA)
        row["base_eui_source"] = base_source
        rows.append(row)

    columns = MANIFEST_COLUMNS + ["eui_source", "idf_sha256_matches_ceiling82", "base_eui_source"]
    return pd.DataFrame(rows, columns=columns), counts


def _build_fix3_manifest(district: str, dry_run: bool) -> tuple[pd.DataFrame, dict]:
    base = _load_manifest(district, BASE_MERGED_TAG)
    if base is None:
        raise FileNotFoundError(f"missing {_manifest_path(district, BASE_MERGED_TAG)}")
    fix_dir = _dist_dir(district, FIX3_TAG)
    fix_prepared_path = fix_dir / "prepared_buildings.csv"
    if not fix_prepared_path.exists():
        raise FileNotFoundError(f"missing {fix_prepared_path}")
    fix_prepared = pd.read_csv(fix_prepared_path, dtype=str)
    stem_to_id = dict(zip(fix_prepared["stem"].astype(str), fix_prepared["building_id"].astype(str)))
    fleet_stems = [
        s.strip() for s in (fix_dir / "fleet.lst").read_text(encoding="utf-8").splitlines() if s.strip()
    ]
    missing = [s for s in fleet_stems if s not in stem_to_id]
    if missing:
        raise ValueError(f"fleet.lst stems not in prepared_buildings.csv for {district}: {missing[:5]}")
    fix_prepared_ids = {stem_to_id[s] for s in fleet_stems}

    if not dry_run:
        work_base = Path(tempfile.gettempdir()) / "ubem_eu11_harvest"
        work_base.mkdir(parents=True, exist_ok=True)
        harvest_district(district, work_base, tag=FIX3_TAG)

    fix_manifest = _load_manifest(district, FIX3_TAG)
    fix_ok = _rc_zero_index(fix_manifest)
    counts = {FIX3_TAG: 0, "fix3_failed_carry": 0, "merged_2026-09-08_carry": 0, "pending_resimulation": 0}

    undivided = _undivided_ids(district)
    excluded = []
    rows = []
    for _, brow in base.iterrows():
        building_id = str(brow["building_id"])
        if building_id in undivided:
            excluded.append(
                {"building_id": building_id, "stage": "harvest", "blocker": UNDIVIDED_REASON, "detail": ""}
            )
            continue
        row = {c: brow.get(c, pd.NA) for c in MANIFEST_COLUMNS}
        base_source = brow.get("eui_source", pd.NA)
        idf_variant = pd.NA
        if building_id in fix_ok:
            eui_source = FIX3_TAG
            for c in MANIFEST_COLUMNS:
                row[c] = fix_ok[building_id][c]
            idf_variant = fix_ok[building_id].get("idf_variant", pd.NA)
        elif base_source == "pending_resimulation":
            eui_source = "pending_resimulation"
        elif building_id in fix_prepared_ids:
            eui_source = "fix3_failed_carry"
        else:
            eui_source = "merged_2026-09-08_carry"
        counts[eui_source] += 1
        row["eui_source"] = eui_source
        row["idf_sha256_matches_ceiling82"] = brow.get("idf_sha256_matches_ceiling82", pd.NA)
        row["base_eui_source"] = base_source
        row["idf_variant"] = idf_variant
        rows.append(row)

    columns = MANIFEST_COLUMNS + ["eui_source", "idf_sha256_matches_ceiling82", "base_eui_source", "idf_variant"]
    manifest = pd.DataFrame(rows, columns=columns)
    manifest.attrs["excluded_undivided"] = pd.DataFrame(
        excluded, columns=["building_id", "stage", "blocker", "detail"]
    )
    return manifest, counts


def _build_win_manifest(district: str, dry_run: bool, win_tag: str = WIN_TAG) -> tuple[pd.DataFrame, dict]:
    base = _load_manifest(district, BASE_MERGED_TAG)
    if base is None:
        raise FileNotFoundError(f"missing {_manifest_path(district, BASE_MERGED_TAG)}")
    win_dir = _dist_dir(district, win_tag)
    win_prepared_path = win_dir / "prepared_buildings.csv"
    if not win_prepared_path.exists():
        raise FileNotFoundError(f"missing {win_prepared_path}")
    win_prepared = pd.read_csv(win_prepared_path, dtype=str)
    stem_to_id = dict(zip(win_prepared["stem"].astype(str), win_prepared["building_id"].astype(str)))
    is_win5 = win_tag in (WIN5_TAG, WIN6_TAG)
    if is_win5:
        fleet_stems = sorted(p.stem for p in (win_dir / "idfs").glob("*.idf"))
    else:
        fleet_stems = [
            s.strip() for s in (win_dir / "fleet.lst").read_text(encoding="utf-8").splitlines() if s.strip()
        ]
    missing = [s for s in fleet_stems if s not in stem_to_id]
    if missing:
        raise ValueError(f"win stems not in prepared_buildings.csv for {district}: {missing[:5]}")
    win_ids = {stem_to_id[s] for s in fleet_stems}
    prepared_by_id = win_prepared.drop_duplicates("building_id").set_index("building_id", drop=False)

    windows_path = win_dir / "windows.csv"
    if not windows_path.exists():
        raise FileNotFoundError(f"missing {windows_path}")
    windows = pd.read_csv(windows_path, dtype=str).drop_duplicates("stem").set_index("stem", drop=False)

    if not dry_run:
        work_base = Path(tempfile.gettempdir()) / "ubem_eu11_harvest"
        work_base.mkdir(parents=True, exist_ok=True)
        harvest_district(district, work_base, tag=win_tag)

    win_ok = _rc_zero_index(_load_manifest(district, win_tag))
    nowin_manifest = _load_manifest(district, NOWIN_MERGED_TAG)
    nowin_eui: dict[str, object] = {}
    if nowin_manifest is not None:
        sel = nowin_manifest[nowin_manifest["eui_source"] == FIX3_TAG]
        nowin_eui = dict(zip(sel["building_id"].astype(str), sel["eui_kwh_m2"]))

    counts = {win_tag: 0, "win_failed": 0}
    undivided = _undivided_ids_win5(district) if is_win5 else _undivided_ids(district)
    geometry_fault = _geometry_fault_ids(district) if win_tag == WIN6_TAG else set()
    excluded = []
    rows = []
    for _, brow in base.iterrows():
        building_id = str(brow["building_id"])
        if building_id in undivided:
            excluded.append(
                {"building_id": building_id, "stage": "harvest", "blocker": UNDIVIDED_REASON, "detail": ""}
            )
            continue
        if building_id in geometry_fault:
            excluded.append(
                {"building_id": building_id, "stage": "harvest", "blocker": GEOMETRY_FAULT_REASON, "detail": ""}
            )
            continue
        row = {c: pd.NA for c in MANIFEST_COLUMNS}
        if building_id in win_ok:
            eui_source = win_tag
            for c in MANIFEST_COLUMNS:
                row[c] = win_ok[building_id][c]
        elif building_id in win_ids:
            eui_source = "win_failed"
            prow = prepared_by_id.loc[building_id]
            for c in IDENTITY_COLUMNS:
                row[c] = prow.get(c, pd.NA)
        else:
            raise ValueError(f"{district}: building {building_id} is neither undivided nor in the win fleet")
        counts[eui_source] += 1
        row["eui_source"] = eui_source
        stem = str(prepared_by_id.loc[building_id, "stem"])
        for c in WIN_EXTRA_COLUMNS:
            row[c] = windows.loc[stem, c] if stem in windows.index and c in windows.columns else pd.NA
        row["eui_0908"] = brow.get("eui_kwh_m2", pd.NA)
        row["eui_source_0908"] = brow.get("eui_source", pd.NA)
        row["eui_nowin"] = nowin_eui.get(building_id, pd.NA)
        if is_win5:
            for c in WIN5_EXTRA_COLUMNS:
                row[c] = prepared_by_id.loc[building_id].get(c, pd.NA)
        rows.append(row)

    columns = MANIFEST_COLUMNS + ["eui_source"] + WIN_EXTRA_COLUMNS + ["eui_0908", "eui_source_0908", "eui_nowin"]
    if is_win5:
        columns = columns + WIN5_EXTRA_COLUMNS
    manifest = pd.DataFrame(rows, columns=columns)
    manifest.attrs["excluded_undivided"] = pd.DataFrame(
        excluded, columns=["building_id", "stage", "blocker", "detail"]
    )
    return manifest, counts


def build_merged_manifest(district: str, dry_run: bool, merged_tag: str = MERGE_DATE) -> tuple[pd.DataFrame, dict]:
    if merged_tag == "2026-09-29":
        return _build_fix_manifest(district, dry_run)
    if merged_tag == "2026-10-01":
        return _build_fix3_manifest(district, dry_run)
    if merged_tag in WIN_TAGS:
        return _build_win_manifest(district, dry_run, merged_tag)
    require_recut = merged_tag == "2026-09-08"
    base_dir = _dist_dir(district, RECUT_TAG) if require_recut else _dist_dir(district, FINAL_TAG)
    prepared_path = base_dir / "prepared_buildings.csv"
    if not prepared_path.exists():
        raise FileNotFoundError(f"missing {prepared_path}")
    prepared = pd.read_csv(prepared_path, dtype=str)

    if not dry_run:
        work_base = Path(tempfile.gettempdir()) / "ubem_eu11_harvest"
        work_base.mkdir(parents=True, exist_ok=True)
        if require_recut:
            harvest_district(district, work_base, tag=RECUT_TAG)
        harvest_district(district, work_base, tag=FINAL_TAG)
        harvest_district(district, work_base, tag=DELTA_TAG)

    recut_ok = _rc_zero_index(_load_manifest(district, RECUT_TAG)) if require_recut else {}
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
    if require_recut:
        counts = {RECUT_TAG: 0, DELTA_TAG: 0, FINAL_TAG: 0, "ceiling82_carry": 0, "pending_resimulation": 0}
    else:
        counts = {DELTA_TAG: 0, FINAL_TAG: 0, "ceiling82_carry": 0, "pending_resimulation": 0}

    for _, prow in prepared.iterrows():
        building_id = str(prow["building_id"])
        idf_sha256 = str(prow["idf_sha256"])
        matches_ceiling = ceiling_sha.get(building_id) == idf_sha256

        if require_recut and building_id in recut_ok:
            eui_source, source_row = RECUT_TAG, recut_ok[building_id]
        elif building_id in delta_ok and (
            not require_recut or str(delta_ok[building_id].get("idf_sha256")) == idf_sha256
        ):
            eui_source, source_row = DELTA_TAG, delta_ok[building_id]
        elif building_id in final_ok and (
            not require_recut or str(final_ok[building_id].get("idf_sha256")) == idf_sha256
        ):
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
    win_tag = next((t for t in WIN_TAGS if t in counts), None)
    is_win = win_tag is not None
    n_pending = counts.get("pending_resimulation", 0)
    if is_win:
        with_eui = manifest[manifest["eui_source"] == win_tag]
        n_with_eui = len(with_eui)
    else:
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

    eui_source_tags = [win_tag] if is_win else [t for t in counts if t != "pending_resimulation"]

    extra = {}
    if is_win:
        extra["n_win_failed"] = counts["win_failed"]
        extra["win_failed_ids"] = sorted(
            manifest.loc[manifest["eui_source"] == "win_failed", "building_id"].astype(str)
        )
    if FIX_TAG in counts:
        extra["fix_failed_ids"] = sorted(
            manifest.loc[manifest["eui_source"] == "fix_failed_carry", "building_id"].astype(str)
        )

    if "fix3_failed_carry" in counts:
        extra["fix_failed_ids"] = sorted(
            manifest.loc[manifest["eui_source"] == "fix3_failed_carry", "building_id"].astype(str)
        )
        prepared = pd.read_csv(_dist_dir(district, FIX3_TAG) / "prepared_buildings.csv", dtype=str)
        stem_to_id = dict(zip(prepared["stem"].astype(str), prepared["building_id"].astype(str)))
        extra["held_back_finding280"] = sorted(
            stem_to_id[s] for s in HELD_BACK_FINDING280_STEMS.get(district, []) if s in stem_to_id
        )

    excluded_undivided = manifest.attrs.get("excluded_undivided")
    if excluded_undivided is not None:
        if win_tag == WIN6_TAG:
            n_fault = int((excluded_undivided["blocker"] == GEOMETRY_FAULT_REASON).sum())
            extra["n_excluded_undivided"] = len(excluded_undivided) - n_fault
            extra["n_excluded_geometry_fault"] = n_fault
        else:
            extra["n_excluded_undivided"] = len(excluded_undivided)

    return {
        **extra,
        "district": district,
        "counts_by_eui_source": counts,
        "n_rows": n_rows,
        "n_with_eui": n_with_eui,
        "n_pending": n_pending,
        "pooled_eui_kwh_m2": round(pooled_eui, 6) if pooled_eui is not None else None,
        "pooled_eui_population": (
            f"{n_with_eui} of {n_rows} buildings with eui_source in "
            f"{{{', '.join(eui_source_tags)}}}"
        ),
        "ceiling82_pooled_eui_kwh_m2": ceiling_pooled_eui,
        "ceiling82_pooled_eui_kwh_m2_delta": round(delta_eui, 6) if delta_eui is not None else None,
        "disclosures": DISCLOSURES.get(district, []),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--district", required=True, choices=DISTRICTS)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--merged-tag", default=MERGE_DATE, help="output tag, e.g. 2026-09-08")
    args = parser.parse_args()

    manifest, counts = build_merged_manifest(args.district, args.dry_run, merged_tag=args.merged_tag)
    summary = build_summary(args.district, manifest, counts)

    if args.dry_run:
        print(f"EU-11 merged harvest (dry-run) - {args.district}")
        for tag in counts:
            print(f"  {tag}: {counts[tag]}")
        return

    out_dir = _dist_dir(args.district, f"merged_{args.merged_tag}")
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / f"{_slug(args.district)}_manifest.csv"
    manifest.to_csv(manifest_path, index=False)
    excluded_undivided = manifest.attrs.get("excluded_undivided")
    if excluded_undivided is not None:
        excluded_undivided.to_csv(out_dir / "excluded_buildings.csv", index=False)
    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[{args.district}] merged manifest written: {manifest_path} ({len(manifest)} rows)")
    print(f"[{args.district}] merged summary written: {summary_path}")


if __name__ == "__main__":
    main()
