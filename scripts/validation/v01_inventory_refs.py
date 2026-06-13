"""V01: Reference IDF inventory + E+ 23.1 compatibility smoke.

Catalogue all 31 reference IDFs -> %TEMP%/ubem_validation/level2/ref_inventory.csv
Columns: filename, version, building_type, vintage, conditioned_floor_area_m2,
         storeys, has_hvactemplate, smoke_status (set for the one smoke-run IDF).

Then copy ASHRAE901_OfficeMedium_STD2022_Buffalo.idf to refs_work/ and run it
through local E+ 23.1 with the V02 EPW path (written by V02; here we use a
placeholder path arg or skip the smoke if EPW not yet present).
STOP-AND-REPORT if the smoke run exits with a version-mismatch fatal.
"""
from __future__ import annotations

import csv
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from shapely.geometry import Polygon

REPO = Path(__file__).parent.parent.parent
REF_DIR = REPO / "docs" / "validations" / "Level 2 DOE round-trip" / "00.BaselineBuildings_NUs"
OUT_BASE = Path(tempfile.gettempdir()) / "ubem_validation" / "level2"
REFS_WORK = OUT_BASE / "refs_work"
EP_EXE = Path(r"C:\EnergyPlusV23-1-0") / "energyplus.exe"
EXPAND_EXE = Path(r"C:\EnergyPlusV23-1-0") / "ExpandObjects.exe"
SMOKE_TARGET = "ASHRAE901_OfficeMedium_STD2022_Buffalo.idf"


def _parse_idf_clean(idf_path: Path) -> list[list[str]]:
    txt = idf_path.read_text(encoding="utf-8", errors="replace")
    lines = []
    for line in txt.splitlines():
        line = line.split("!")[0].strip()
        if line:
            lines.append(line)
    clean = " ".join(lines)
    raw_objects = [o.strip() for o in clean.split(";") if o.strip()]
    result = []
    for obj in raw_objects:
        fields = [f.strip() for f in obj.split(",")]
        result.append(fields)
    return result


def _get_version(objects: list[list[str]]) -> str:
    for fields in objects:
        if fields[0].upper() == "VERSION" and len(fields) > 1:
            return fields[1]
    return "unknown"


def _has_hvactemplate(objects: list[list[str]]) -> bool:
    for fields in objects:
        if fields[0].upper().startswith("HVACTEMPLATE:"):
            return True
    return False


def _conditioned_floor_area(objects: list[list[str]]) -> float:
    total = 0.0
    for fields in objects:
        if fields[0].upper() != "BUILDINGSURFACE:DETAILED":
            continue
        if len(fields) < 5:
            continue
        surf_type = fields[2].lower()
        if surf_type != "floor":
            continue
        try:
            nv_field = fields[11] if len(fields) > 11 else ""
            if nv_field.isdigit() and int(nv_field) > 0:
                nv = int(nv_field)
                coords = []
                for i in range(nv):
                    x = float(fields[12 + i * 3])
                    y = float(fields[12 + i * 3 + 1])
                    coords.append((x, y))
            else:
                remaining = fields[12:]
                n_triplets = len(remaining) // 3
                coords = []
                for i in range(n_triplets):
                    x = float(remaining[i * 3])
                    y = float(remaining[i * 3 + 1])
                    coords.append((x, y))
            if len(coords) >= 3:
                poly = Polygon(coords)
                total += abs(poly.area)
        except (ValueError, IndexError):
            pass
    return total


def _floor_count_from_zones(objects: list[list[str]]) -> int:
    zone_names = []
    for fields in objects:
        if fields[0].upper() == "ZONE" and len(fields) > 1:
            zone_names.append(fields[1])

    if not zone_names:
        return 1

    floor_nums: set[int] = set()
    pat_fprefix = re.compile(r"^F(\d+)\s", re.IGNORECASE)
    pat_numeric = re.compile(r"(?:floor|fl|level|lvl|story|storey)[ _]?(\d+)", re.IGNORECASE)
    pat_suffix = re.compile(r"_F(\d+)_", re.IGNORECASE)

    for zn in zone_names:
        zl = zn.lower()
        m = pat_fprefix.match(zn) or pat_suffix.search(zn) or pat_numeric.search(zl)
        if m:
            floor_nums.add(int(m.group(1)))

    keyword_map = {"bottom": 1, "bot": 1, "mid": 2, "top": 3, "ground": 1}
    for zn in zone_names:
        zl = zn.lower()
        for kw, fn in keyword_map.items():
            if kw in zl:
                floor_nums.add(fn)
                break

    if not floor_nums:
        non_plenum = [zn for zn in zone_names if "plenum" not in zn.lower()]
        return max(1, len(non_plenum))

    return max(floor_nums)


def _building_type_from_filename(fname: str) -> str:
    name = fname.replace(".idf", "")
    for prefix in ["ASHRAE901_", "ASHRAE_", "IECC_"]:
        name = name.replace(prefix, "")
    for suffix in [
        "_STD2022_Buffalo", "_STD2019", "_STD2019_Buffalo",
        "_90.1-2019_6A_Buffalo_v221", "_90.1-2019_6A_Buffalo",
        "_V22.1", "_v221", "_V2210",
        "_Buffalo", "_6A",
        "_50pct_downscaled",
        "_Geometric",
    ]:
        name = name.replace(suffix, "")
    return name


def _vintage_from_filename(fname: str) -> str:
    if "STD2022" in fname:
        return "ASHRAE90.1-2022"
    if "STD2019" in fname or "90.1-2019" in fname:
        return "ASHRAE90.1-2019"
    if "IECC" in fname and "2024" in fname:
        return "IECC2024"
    if "v221" in fname or "V22.1" in fname or "V2210" in fname:
        return "EPlus22.1"
    return "unknown"


def _run_smoke(idf_copy: Path, epw_path: Path | None) -> str:
    if epw_path is None or not epw_path.exists():
        return "SKIP_NO_EPW"

    out_dir = OUT_BASE / "smoke_out"
    out_dir.mkdir(parents=True, exist_ok=True)

    ep_idd = EP_EXE.parent / "Energy+.idd"
    shutil.copy2(ep_idd, out_dir / "Energy+.idd")
    shutil.copy2(idf_copy, out_dir / "in.idf")

    if EXPAND_EXE.exists():
        subprocess.run(
            [str(EXPAND_EXE)],
            cwd=str(out_dir),
            capture_output=True,
            timeout=120,
        )

    run_idf = out_dir / "expanded.idf"
    if not run_idf.exists():
        run_idf = out_dir / "in.idf"

    result = subprocess.run(
        [str(EP_EXE), "-w", str(epw_path), "-d", str(out_dir), str(run_idf)],
        capture_output=True,
        text=True,
        timeout=600,
    )

    end_file = out_dir / "eplusout.end"
    err_file = out_dir / "eplusout.err"

    if end_file.exists():
        end_txt = end_file.read_text(errors="replace")
        if "EnergyPlus Completed Successfully" in end_txt:
            return "success"
        if "Fatal" in end_txt or "fatal" in end_txt:
            if err_file.exists():
                err_txt = err_file.read_text(errors="replace")
                if "version" in err_txt.lower() and "mismatch" in err_txt.lower():
                    print("\n[V01] FATAL: E+ version mismatch detected in smoke run.")
                    print("[V01] .err tail:")
                    print("\n".join(err_txt.splitlines()[-30:]))
                    print("\n[V01] STOP — version mismatch. Manager must rule on version-transition strategy.")
                    sys.exit(2)
            return "failed"

    if result.returncode != 0:
        stdout_lower = (result.stdout + result.stderr).lower()
        if "version" in stdout_lower and "mismatch" in stdout_lower:
            print("\n[V01] FATAL: E+ version mismatch in smoke run stdout/stderr.")
            print(result.stdout[-2000:])
            print("\n[V01] STOP — version mismatch. Manager must rule on version-transition strategy.")
            sys.exit(2)
        return f"failed_rc{result.returncode}"

    return "unknown"


def main() -> None:
    OUT_BASE.mkdir(parents=True, exist_ok=True)
    REFS_WORK.mkdir(parents=True, exist_ok=True)

    idf_files = sorted(REF_DIR.glob("*.idf"))
    print(f"[V01] Found {len(idf_files)} IDF files in {REF_DIR}")
    if len(idf_files) != 31:
        print(f"[V01] WARNING: expected 31, found {len(idf_files)}")

    epw_path_file = OUT_BASE / "epw_path.txt"
    epw_path: Path | None = None
    if epw_path_file.exists():
        candidate = Path(epw_path_file.read_text().strip())
        if candidate.exists():
            epw_path = candidate

    rows = []
    for idf_path in idf_files:
        fname = idf_path.name
        print(f"  Parsing {fname} ...", end=" ")
        objects = _parse_idf_clean(idf_path)
        version = _get_version(objects)
        has_hvac = _has_hvactemplate(objects)
        cfa = _conditioned_floor_area(objects)
        storeys = _floor_count_from_zones(objects)
        btype = _building_type_from_filename(fname)
        vintage = _vintage_from_filename(fname)
        print(f"v={version}, area={cfa:.0f}m2, floors={storeys}, hvact={has_hvac}")
        rows.append({
            "filename": fname,
            "version": version,
            "building_type": btype,
            "vintage": vintage,
            "conditioned_floor_area_m2": round(cfa, 2),
            "storeys": storeys,
            "has_hvactemplate": has_hvac,
            "smoke_status": "",
        })

    n_zero_area = sum(1 for r in rows if r["conditioned_floor_area_m2"] == 0.0)
    if n_zero_area > 0:
        print(f"[V01] WARNING: {n_zero_area} IDFs have zero floor area — check parsing.")

    smoke_idf_src = REF_DIR / SMOKE_TARGET
    smoke_idf_dst = REFS_WORK / SMOKE_TARGET
    shutil.copy2(smoke_idf_src, smoke_idf_dst)
    print(f"\n[V01] Running smoke: {SMOKE_TARGET} ...")
    smoke_status = _run_smoke(smoke_idf_dst, epw_path)
    print(f"[V01] Smoke status: {smoke_status}")

    for r in rows:
        if r["filename"] == SMOKE_TARGET:
            r["smoke_status"] = smoke_status

    out_csv = OUT_BASE / "ref_inventory.csv"
    fieldnames = ["filename", "version", "building_type", "vintage",
                  "conditioned_floor_area_m2", "storeys", "has_hvactemplate", "smoke_status"]
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n[V01] Inventory written: {out_csv}  ({len(rows)} rows)")
    print(f"[V01] Zero-area count: {n_zero_area}")
    print(f"[V01] Smoke run on {SMOKE_TARGET}: {smoke_status}")

    if smoke_status not in {"success", "SKIP_NO_EPW"}:
        print(f"\n[V01] WARNING: smoke run result '{smoke_status}' — review before proceeding.")

    print("[V01] DONE")


if __name__ == "__main__":
    main()
