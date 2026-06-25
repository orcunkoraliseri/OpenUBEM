"""T01 diagnostic: reproduce degenerate-surface pathology on way_428643335.

Reads the cached pre-fix IDF and counts surfaces with <3 distinct vertices.
Then runs local EnergyPlus to confirm the Fatal.
"""
from __future__ import annotations
import subprocess
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent.parent
IDF_PATH = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\phaseC\la_urban\step3\idfs\way_428643335.idf")
EPW_PATH = (
    Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\phaseC\la_urban\weather\weather")
    / "USA_CA_Los.Angeles.Downtown-USC.Campus.722874_TMYx.2011-2025.epw"
)
EP_EXE  = Path(r"C:\EnergyPlusV23-1-0\energyplus.exe")
EP_IDD  = EP_EXE.parent / "Energy+.idd"
WORK_DIR = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_t01_run")


def count_degenerate_surfaces(idf_path: Path) -> tuple[int, int]:
    """Return (degenerate_count, total_surface_count).

    Parses BUILDINGSURFACE:DETAILED blocks and counts those with <3 distinct (x,y,z) vertices.
    """
    text = idf_path.read_text(encoding="utf-8", errors="replace")
    blocks = text.split("BuildingSurface:Detailed,")
    degenerate = 0
    total = 0
    for block in blocks[1:]:  # skip header before first object
        # Each block ends at the next blank line or semicolon
        end = block.find(";")
        if end == -1:
            continue
        body = block[:end]
        lines = [l.strip().rstrip(",").strip() for l in body.splitlines()]
        # Vertices start after field index ~10; each vertex is 3 consecutive fields (X,Y,Z)
        # Fields: Name, SurfType, ConstructionName, ZoneName, SpaceName, OutsideBCond,
        # OutsideBCondObj, SunExposure, WindExposure, ViewFactorToGround, NumVertices, X1,Y1,Z1,...
        fields = []
        for l in lines:
            if l and not l.startswith("!"):
                fields.append(l.split("!")[0].strip().rstrip(",").strip())
        fields = [f for f in fields if f]
        # Find the NumVertices field (index 10, 0-based)
        try:
            num_verts = int(float(fields[10]))
        except (IndexError, ValueError):
            continue
        if num_verts < 3:
            degenerate += 1
        # Also check for duplicate coords that reduce distinct vertices below 3
        try:
            coords = []
            for vi in range(num_verts):
                base = 11 + vi * 3
                x = float(fields[base])
                y = float(fields[base + 1])
                z = float(fields[base + 2])
                coords.append((round(x, 6), round(y, 6), round(z, 6)))
            distinct = len(set(coords))
            if distinct < 3:
                degenerate += 1 if num_verts >= 3 else 0  # already counted if num_verts<3
        except (IndexError, ValueError):
            pass
        total += 1
    return degenerate, total


def run_ep(idf_path: Path) -> tuple[bool, str, str]:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    idd_dest = WORK_DIR / "Energy+.idd"
    if not idd_dest.exists():
        shutil.copy2(EP_IDD, idd_dest)
    cmd = [str(EP_EXE), "-w", str(EPW_PATH), "-d", str(WORK_DIR), "-x", "-r", str(idf_path)]
    subprocess.run(cmd, capture_output=True, timeout=300, cwd=str(WORK_DIR))
    end_file = WORK_DIR / "eplusout.end"
    err_file = WORK_DIR / "eplusout.err"
    end_text = end_file.read_text(errors="replace") if end_file.exists() else ""
    err_text = err_file.read_text(errors="replace") if err_file.exists() else ""
    success = "EnergyPlus Completed Successfully" in end_text
    return success, end_text, err_text


def main():
    assert IDF_PATH.exists(), f"Cached IDF not found: {IDF_PATH}"
    assert EPW_PATH.exists(), f"EPW not found: {EPW_PATH}"
    assert EP_EXE.exists(),   f"EnergyPlus not found: {EP_EXE}"

    print("=== T01: Reproduce degenerate-surface pathology on way_428643335 ===")
    print(f"IDF: {IDF_PATH}")

    degen, total = count_degenerate_surfaces(IDF_PATH)
    print(f"\nSurface count:        {total}")
    print(f"Degenerate (<3 verts): {degen}")
    assert degen > 0, "FAIL: no degenerate surfaces found — pathology not reproduced"
    print("CONFIRMED: degenerate surfaces present in cached IDF")

    print(f"\nRunning EnergyPlus from {WORK_DIR} ...")
    ok, end_text, err_text = run_ep(IDF_PATH)
    print(f"EP success: {ok}")
    print(f"end file: {end_text[:200]}")

    # Extract Severe/Fatal lines
    severe_lines = [l for l in err_text.splitlines()
                    if any(kw in l for kw in ("** Severe **", "**  Fatal **", "** Fatal  **"))]
    print("\nSevere/Fatal lines from eplusout.err:")
    for l in severe_lines[:30]:
        print(" ", l)

    assert not ok, "FAIL: EnergyPlus succeeded — E+ fatal not reproduced"
    assert any("degenerate" in l.lower() for l in severe_lines), \
        "FAIL: no degenerate-surface severe line found in eplusout.err"
    print("\nT01 PASSED: degenerate pathology confirmed end-to-end.")


if __name__ == "__main__":
    main()
