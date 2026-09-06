"""EU-21 T05a: the engine's own building-level census (`FINDING 246`, `D-EU-95`).

`_r5`'s census cuts each building once, at a single declared `k = round(dwellings_total
/ storeys)` (`08_district_viewer.py:146`, `01_cut_group_plans.py:155`). The engine
(`generate_european_building_dwelling_layout`, `european_residential.py:2639`) instead
conserves the declared dwelling total per storey via `allocate_european_dwellings` --
`tot // storeys` with the first `tot % storeys` storeys getting one more -- and cuts
each *distinct* per-storey count separately (cached by count, `:2664-2684`). The two
counts disagree by construction on any building whose dwellings do not divide evenly
across its storeys.

This script reproduces the engine's own per-storey allocation and per-count cut for
every one of the 2,544 `EU-20/morphology_census.csv` rows, and classifies each building
exactly as `generate_european_building_dwelling_layout` would:
  - REFUSED_K_GT_12  -- `max(floor_allocations[*].dwelling_count) > 12`; the caller-level
    refusal at `european_residential.py:2657`, applied *before* any cut is attempted.
  - FALLBACK         -- every count `<= 12`, but at least one distinct count fails
    `cut_storey_nocore`'s seven checks (or the cutter raises).
  - EMITTED          -- every distinct count passes.

Never calls `generate_european_nocore_storey_layout` (the IDF-path wrapper) -- calls
`cut_storey_nocore` directly, the same call that wrapper itself makes, so this script
never depends on the engine's zone-spec plumbing. Never edits `07_nocore_tests.py` /
`01`-`06` / `08`, never edits or regenerates any `_r5` JSON (read-only oracle, D-EU-85).

Per `D-EU-95`/`FINDING 246`: this is *additional* information about what the engine
will actually emit, reported beside `_r5`'s per-plate `PASS` count -- never a
replacement for it, and never adjusted to make the two agree.
"""
import collections
import importlib.util as ilu
import json
import pathlib
import time

from openubem.geometry.european_nocore import cut_storey_nocore
from openubem.geometry.european_residential import (
    RULED_GRID_MAX_DWELLINGS_PER_FLOOR,
    allocate_european_dwellings,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
CUTTER_PATH = ROOT / "scripts" / "eu21" / "07_nocore_tests.py"
DISTRICT_PLANS = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-21" / "district_plans"
OUT_DIR = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-21" / "engine_parity"
OUT_PATH = OUT_DIR / "engine_census_2026-09-03.json"

DISTRICT_FILES = [
    "ES-MAD-BERRUGUETE_nocore_2026-09-03_r5.json",
    "FR-LYO-HAUTCOEURPENTES_nocore_2026-09-03_r5.json",
    "GB-LDN-STDUNSTANS_nocore_2026-09-03_r5.json",
    "IT-BOL-GALVANI2_nocore_2026-09-03_r5.json",
]

CHECK_IDS = ("C1", "C3", "C4", "C5", "C6", "C10", "C11")


def _load_module(name, path):
    spec = ilu.spec_from_file_location(name, path)
    mod = ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_r5_status():
    """Per (district, building_id): 'PASS' | 'FAIL' | 'REFUSED_K_GT_12' |
    'UNUSABLE_FOOTPRINT' | 'ERROR', plus the census's own single k, read straight
    from the four accepted `_r5` JSONs (read-only, D-EU-85)."""
    status = {}
    r5_k = {}
    r5_pass_count = {}
    for fname in DISTRICT_FILES:
        data = json.load(open(DISTRICT_PLANS / fname, encoding="utf-8"))
        district = data["district"]
        r5_pass_count[district] = data["summary"]["pass"]
        for p in data["plates"]:
            key = (district, p["building_id"])
            r5_k[key] = p.get("k")
            status[key] = p["verdict"] if p["status"] == "direct" else p["status"]
    return status, r5_k, r5_pass_count


def _engine_status(g, storeys, dwellings_total, cache):
    allocation = allocate_european_dwellings(
        archetype_id="engine_census_T05a", building_type="AB",
        n_apartment=dwellings_total, n_storey=storeys, plate_area_m2=float(g.area),
    )
    counts = [fa.dwelling_count for fa in allocation.floor_allocations]
    max_count = max(counts) if counts else 0
    distinct_counts = sorted({c for c in counts if c > 0})
    if max_count > RULED_GRID_MAX_DWELLINGS_PER_FLOOR:
        return "REFUSED_K_GT_12", distinct_counts, []
    failing = []
    for count in distinct_counts:
        if count not in cache:
            try:
                _plate, _live, checks, verdict = cut_storey_nocore(g, count)
            except Exception as exc:
                cache[count] = ("ERROR", [f"{type(exc).__name__}"])
            else:
                if verdict == "PASS":
                    cache[count] = ("PASS", [])
                else:
                    cache[count] = ("FAIL", [c for c in CHECK_IDS if not checks[c]["pass"]])
        result_status, failed_ids = cache[count]
        if result_status != "PASS":
            failing.append({"count": count, "result": result_status, "failed_checks": failed_ids})
    if failing:
        return "FALLBACK", distinct_counts, failing
    return "EMITTED", distinct_counts, []


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    M07 = _load_module("eu21_m10_m07_nocore_tests", str(CUTTER_PATH))
    geoms, rows, *_ = M07.load_universe()
    r5_status, r5_k, r5_pass_count = _load_r5_status()

    per_district = collections.defaultdict(lambda: {
        "census_rows": 0, "EMITTED": 0, "REFUSED_K_GT_12": 0, "FALLBACK": 0,
        "multi_k_buildings": 0,
    })
    fail_by_check = collections.defaultdict(lambda: {c: 0 for c in CHECK_IDS})
    changed_side = collections.defaultdict(list)

    t0 = time.time()
    for r in rows:
        district = r["district"]
        bid = r["building_id"]
        key = (district, bid)
        g = geoms[key]
        storeys = max(1, int(float(r["storeys"])))
        dwellings_total = max(1, int(float(r["dwellings_total"])))
        per_district[district]["census_rows"] += 1

        cache: dict[int, tuple[str, list[str]]] = {}
        engine_status, distinct_counts, failing = _engine_status(g, storeys, dwellings_total, cache)
        per_district[district][engine_status] += 1
        if len(distinct_counts) > 1:
            per_district[district]["multi_k_buildings"] += 1
        for f in failing:
            for cid in f["failed_checks"]:
                fail_by_check[district][cid] += 1

        r5 = r5_status.get(key, "NOT_IN_R5")
        was_pass = r5 == "PASS"
        now_emitted = engine_status == "EMITTED"
        if was_pass != now_emitted:
            changed_side[district].append({
                "building_id": bid, "r5_status": r5, "r5_k": r5_k.get(key),
                "engine_status": engine_status, "engine_distinct_counts": distinct_counts,
                "engine_failing": failing,
            })

    wall_time_s = round(time.time() - t0, 1)

    districts_out = {}
    fleet = {"census_rows": 0, "EMITTED": 0, "REFUSED_K_GT_12": 0, "FALLBACK": 0,
             "multi_k_buildings": 0, "r5_pass": 0}
    for district, d in per_district.items():
        districts_out[district] = {
            **d,
            "fail_by_check": fail_by_check[district],
            "r5_pass": r5_pass_count.get(district),
            "delta_EMITTED_minus_r5_pass": d["EMITTED"] - r5_pass_count.get(district, 0),
            "changed_side_count": len(changed_side[district]),
            "changed_side": changed_side[district],
        }
        for k in ("census_rows", "EMITTED", "REFUSED_K_GT_12", "FALLBACK", "multi_k_buildings"):
            fleet[k] += d[k]
        fleet["r5_pass"] += r5_pass_count.get(district, 0)
    fleet["delta_EMITTED_minus_r5_pass"] = fleet["EMITTED"] - fleet["r5_pass"]
    fleet["changed_side_count"] = sum(len(v) for v in changed_side.values())

    report = {
        "note": (
            "FINDING 246: the census cuts one k per building; the engine cuts one k per "
            "storey. EMITTED/REFUSED_K_GT_12/FALLBACK are the engine's own building-level "
            "outcome and are reported beside _r5's PASS, never in place of it."
        ),
        "wall_time_s": wall_time_s,
        "districts": districts_out,
        "fleet": fleet,
    }
    OUT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    for district, d in districts_out.items():
        print(f"{district}: census_rows {d['census_rows']} · EMITTED {d['EMITTED']} · "
              f"REFUSED_K_GT_12 {d['REFUSED_K_GT_12']} · FALLBACK {d['FALLBACK']} · "
              f"r5_pass {d['r5_pass']} · delta {d['delta_EMITTED_minus_r5_pass']} · "
              f"multi_k {d['multi_k_buildings']} · changed_side {d['changed_side_count']}")
    print(f"FLEET: census_rows {fleet['census_rows']} · EMITTED {fleet['EMITTED']} · "
          f"REFUSED_K_GT_12 {fleet['REFUSED_K_GT_12']} · FALLBACK {fleet['FALLBACK']} · "
          f"r5_pass {fleet['r5_pass']} · delta {fleet['delta_EMITTED_minus_r5_pass']} · "
          f"multi_k {fleet['multi_k_buildings']} · changed_side {fleet['changed_side_count']}")
    print(f"wall time {wall_time_s} s · json {OUT_PATH}")


if __name__ == "__main__":
    main()
