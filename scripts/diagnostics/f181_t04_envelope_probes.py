"""FINDING 181 / T04 -- one-variable probes on the equivalent envelope.

Diagnostic only. No change under openubem/. Calls run_campaign_cell unmodified to build
each cell once (dry_run=True); every probe mutates a *copy* of that built IDF with
eppy/geomeppy, never the repo source. Nothing here is adopted.

Writes:
  docs/docs_ACTIVE/europeanLocations/outputs/f181_t04_probes.csv
"""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from openubem.campaign.eu_cell_runner import (  # noqa: E402
    _run_energyplus,
    _sha256_file,
    run_campaign_cell,
)

SPEC_PATH = ROOT / "openubem/data/campaign/eu_campaign_cell_spec_v1.1.json"
SPEC_SHA256 = "16d3fbd62a9f79265c08c5746bbc70f5130cd30cb673c1a68c74755c79aa65f6"
GSS_ROOT = Path("C:/Users/o_iseri/Desktop/GSSCanada/GSSCanada-main/4J_docs_occ")
BINDING_PATH = GSS_ROOT / "Step10_docs/outputs_step10/eu_cell_presence_binding_v2.json"
NOTICE_PATH = GSS_ROOT / "Step10_docs/docs/2026-08-26_10.1_chaining-closure-notice.md"
SCHEDULES_ROOT = GSS_ROOT / "Step7_docs/outputs_step7/schedules"

BASE_RUN_ROOT = ROOT / "openubem/outputs/_tmp_f181/t04"
BUILD_ROOT = BASE_RUN_ROOT / "_built"
OUT_DIR = ROOT / "docs/docs_ACTIVE/europeanLocations/outputs"
PROBES_CSV = OUT_DIR / "f181_t04_probes.csv"

N_REPLICATES = 3
MASSLESS_MINIMUM_R = 0.001

CELLS = [
    "uk__GB.ENG.AB.03.Gen.ReEx.001.001__f000",
    "uk__GB.ENG.AB.03.Gen.ReEx.001.001__f050",
    "es__ES.ME.AB.01.Gen.ReEx.001.001__f000",
    "it__IT.MidClim.AB.01.Gen.ReEx.001.001__f050",
    "it__IT.MidClim.SFH.07.Gen.ReEx.001.001__f000",
    "uk__GB.ENG.TH.05.Gen.ReEx.001.001__f015",
    "it__IT.MidClim.AB.01.Gen.ReEx.001.001__f000",
    "es__ES.ME.AB.01.Gen.ReEx.001.001__f030",
]

PROBES = ["P0", "P1", "P2", "P3", "P4", "P5"]

ERR_MARKERS = {
    "marker_psy": "Temperature out of range",
    "marker_inside_hb": "Inside surface heat balance did not converge",
    "marker_calchb": "CalcHeatBalanceInsideSurf",
}

FIELDS = [
    "cell_id", "survey_fold", "probe", "replicate", "applied",
    "completed", "completion_status", "return_code", "severe_count", "fatal_count",
    "heating_kwh", "runtime_s", "marker_psy", "marker_inside_hb", "marker_calchb", "error",
]


def _sha256_file_bytes(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(Path(path).read_bytes())
    return digest.hexdigest()


NOTICE_SHA256 = _sha256_file_bytes(NOTICE_PATH)


def _load_spec_cells() -> dict[str, dict]:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    assert spec["spec_status"] == "FROZEN_PINNED"
    assert spec["n_cells"] == 510
    by_id = {c["cell_id"]: c for c in spec["cells"]}
    for cell_id in CELLS:
        assert cell_id in by_id, f"cell not in spec: {cell_id}"
    return by_id


def _err_markers(run_dir: Path) -> dict[str, bool]:
    err_path = run_dir / "eplusout.err"
    text = ""
    if err_path.exists():
        try:
            text = err_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
    return {name: (needle in text) for name, needle in ERR_MARKERS.items()}


def _build_once(cell: dict) -> tuple[Path, Path]:
    """Build the cell's IDF once via run_campaign_cell(dry_run=True). Returns (idf_path, epw_path)."""
    run_root = BUILD_ROOT / str(cell["cell_id"])
    manifest = run_campaign_cell(
        cell,
        spec_path=SPEC_PATH, spec_sha256=SPEC_SHA256,
        binding_path=BINDING_PATH, chaining_notice_path=NOTICE_PATH,
        chaining_notice_sha256=NOTICE_SHA256,
        schedules_root=SCHEDULES_ROOT,
        run_root=run_root, dry_run=True,
    )
    return Path(manifest["idf_path"]), Path(manifest["epw_path"])


def _load_idf(idf_path: Path):
    from geomeppy import IDF
    from eppy.modeleditor import IDDAlreadySetError
    from openubem.campaign.eu_cell_runner import ENERGYPLUS_IDD_PATH

    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass
    return IDF(str(idf_path))


def _apply_probe(probe: str, idf_path: Path) -> bool:
    """Mutate the copy at idf_path in place for the given probe. Returns applied (True/False)."""
    if probe == "P0":
        return True

    idf = _load_idf(idf_path)

    if probe == "P1":
        timesteps = idf.idfobjects["TIMESTEP"]
        if not timesteps:
            return False
        timesteps[0].Number_of_Timesteps_per_Hour = 12
        idf.saveas(str(idf_path))
        return True

    if probe == "P2":
        existing = idf.idfobjects["SURFACECONVECTIONALGORITHM:INSIDE"]
        if existing:
            existing[0].Algorithm = "Simple"
        else:
            idf.newidfobject("SURFACECONVECTIONALGORITHM:INSIDE", Algorithm="Simple")
        idf.saveas(str(idf_path))
        return True

    if probe == "P3":
        zones = idf.idfobjects["ZONE"]
        if not zones:
            return False
        zone_name = zones[0].Name
        surface_names = [s.Name for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]]
        surface_names += [s.Name for s in idf.idfobjects["FENESTRATIONSURFACE:DETAILED"]]
        surface_names += [s.Name for s in idf.idfobjects["INTERNALMASS"]]
        n = len(surface_names)
        if n < 2:
            return False
        pairs = [(a, b) for a in surface_names for b in surface_names if a != b]
        # object has 1472 fields total: 1 key-slot header field + 3 per pair; cap is (1472-2)//3
        max_pairs = (1472 - 2) // 3
        if len(pairs) > max_pairs:
            return False
        existing = idf.idfobjects["ZONEPROPERTY:USERVIEWFACTORS:BYSURFACENAME"]
        for obj in list(existing):
            idf.removeidfobject(obj)
        vf_obj = idf.newidfobject(
            "ZONEPROPERTY:USERVIEWFACTORS:BYSURFACENAME",
            Zone_or_ZoneList_or_Space_or_SpaceList_Name=zone_name,
        )
        uniform_view_factor = 1.0 / (n - 1)
        for i, (from_surf, to_surf) in enumerate(pairs, start=1):
            setattr(vf_obj, f"From_Surface_{i}", from_surf)
            setattr(vf_obj, f"To_Surface_{i}", to_surf)
            setattr(vf_obj, f"View_Factor_{i}", uniform_view_factor)
        idf.saveas(str(idf_path))
        return True

    if probe == "P4":
        masses = idf.idfobjects["INTERNALMASS"]
        if not masses:
            return False
        masses[0].Surface_Area = float(masses[0].Surface_Area) * 3.0
        idf.saveas(str(idf_path))
        return True

    if probe == "P5":
        nomass = idf.idfobjects["MATERIAL:NOMASS"]
        below = [m for m in nomass if float(m.Thermal_Resistance) < MASSLESS_MINIMUM_R]
        if not below:
            return False
        for m in below:
            m.Thermal_Resistance = MASSLESS_MINIMUM_R
        idf.saveas(str(idf_path))
        return True

    raise ValueError(f"unknown probe: {probe}")


def _run_replicate(cell_id: str, survey_fold: str, probe: str, replicate: int,
                    built_idf_path: Path, epw_path: Path) -> dict:
    variant_dir = BASE_RUN_ROOT / cell_id / probe / f"rep{replicate}"
    variant_dir.mkdir(parents=True, exist_ok=True)
    idf_copy = variant_dir / built_idf_path.name
    shutil.copyfile(built_idf_path, idf_copy)

    row = {
        "cell_id": cell_id, "survey_fold": survey_fold, "probe": probe, "replicate": replicate,
        "applied": None,
        "completed": None, "completion_status": None, "return_code": None,
        "severe_count": None, "fatal_count": None, "heating_kwh": None, "runtime_s": None,
        "marker_psy": False, "marker_inside_hb": False, "marker_calchb": False, "error": "",
    }
    try:
        applied = _apply_probe(probe, idf_copy)
    except Exception as exc:
        row["applied"] = False
        row["error"] = f"APPLY_FAILED {type(exc).__name__}: {str(exc)[:300]}"
        return row

    row["applied"] = applied
    if not applied:
        row["completion_status"] = "NOT_APPLICABLE"
        return row

    try:
        energy = _run_energyplus(idf_copy, epw_path, variant_dir, timeout=900)
        row["return_code"] = energy["return_code"]
        row["severe_count"] = energy["severe_count"]
        row["fatal_count"] = energy["fatal_count"]
        row["runtime_s"] = energy["runtime_s"]
        row["heating_kwh"] = repr(energy["heating_kwh"])
        if (
            energy["return_code"] != 0
            or energy["fatal_count"]
            or energy["heating_kwh"] is None
        ):
            row["completed"] = False
            row["completion_status"] = "ENGINE_FAILED"
        else:
            row["completed"] = True
            row["completion_status"] = "COMPLETED"
        row.update(_err_markers(variant_dir))
    except Exception as exc:
        row["error"] = f"RUN_FAILED {type(exc).__name__}: {str(exc)[:300]}"
        row["completed"] = False
        row["completion_status"] = "EXCEPTION"
        if variant_dir.exists():
            row.update(_err_markers(variant_dir))
    return row


def write_csv(rows: list[dict]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with PROBES_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def print_summary(rows: list[dict]) -> None:
    by_key: dict[tuple[str, str], list[dict]] = {}
    for r in rows:
        by_key.setdefault((r["cell_id"], r["probe"]), []).append(r)

    print("\ncell_id | probe | applied | n_completed | n_distinct_heating | max_rel_spread")
    for (cell_id, probe), group in sorted(by_key.items()):
        applied = group[0]["applied"]
        completed = [r for r in group if r["completed"] is True and r["heating_kwh"] not in (None, "None")]
        values = []
        for r in completed:
            try:
                values.append(float(r["heating_kwh"]))
            except (TypeError, ValueError):
                pass
        n_distinct = len({round(v, 9) for v in values})
        if values and min(v for v in values if v != 0) != 0:
            max_rel_spread = (max(values) - min(values)) / abs(max(values)) if max(values) else 0.0
        elif len(values) >= 2:
            max_rel_spread = (max(values) - min(values))
        else:
            max_rel_spread = 0.0
        print(f"{cell_id} | {probe} | {applied} | {len(completed)} | {n_distinct} | {max_rel_spread:.6f}")


def main() -> None:
    by_id = _load_spec_cells()
    rows: list[dict] = []
    t0 = time.time()

    for cell_id in CELLS:
        cell = by_id[cell_id]
        survey_fold = cell["survey_fold"]
        print(f"building {cell_id} ...", flush=True)
        built_idf_path, epw_path = _build_once(cell)

        for probe in PROBES:
            for replicate in range(1, N_REPLICATES + 1):
                row = _run_replicate(cell_id, survey_fold, probe, replicate, built_idf_path, epw_path)
                rows.append(row)
                print(
                    f"  {cell_id} {probe} rep{replicate}: applied={row['applied']} "
                    f"status={row['completion_status']} heating={row['heating_kwh']}",
                    flush=True,
                )
            write_csv(rows)
        print(f"  done {cell_id} in {time.time() - t0:.1f}s total", flush=True)

    write_csv(rows)
    print_summary(rows)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
