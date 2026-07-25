"""T13 Tier-2 - resim.py: short-window EnergyPlus side-leg for real wall surface temperatures
(PLAN §7 T13, §13 v1.1 redesign).

Owned entirely by Stage 6. Does NOT modify openubem/idf/outputs.py, the IDF builder, the
simulation stage, or the results parser -- it patches COPIES of already-archived IDFs in a
scratch directory and reuses openubem/simulation/runner.py::run_energyplus exactly as-is
(read-only import). No production module is edited and no 04_/05_ artifact is written; the
production-untouched `git status --porcelain` gate (T13's own mandatory check) is what proves
this structurally, not just by assertion.

Sequence (mirrors the plan's five numbered steps):
  1. extract_idf_archive()      -- unzip <cell>_step3_idfs_archive.zip to a scratch dir.
  2. patch_idf_for_resim()      -- append Output:Variable(*, Surface Outside Face Temperature,
                                    Hourly) and narrow RunPeriod1 to the analysis window (+
                                    warm-up margin).
  3. run_resim_side_leg()       -- fan out via joblib through the existing run_energyplus().
  4. harvest_wall_temperatures()-- read eplusout.sql (parse_building_sql, read-only), keep only
                                    exterior wall surfaces, tag each with its geomeppy-computed
                                    azimuth. Projecting onto the domain's per-cell wall view
                                    factors is T14's job (mrt.py) -- this module's contract ends
                                    at "harvested, oriented, per-hour wall surface temperatures."
  5. quarantine_or_delete()     -- clear the scratch tree when done.
"""
from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

import pandas as pd
from geomeppy import IDF as GeomIDF
from joblib import Parallel, delayed

from openubem import config
from openubem.results.parser import parse_building_sql
from openubem.simulation.parallel import SimTask
from openubem.simulation.runner import run_energyplus

# The variable this whole tier exists to harvest -- not requested anywhere in production
# (F-06), injected here into copies only.
RESIM_OUTPUT_VARIABLE = "Surface Outside Face Temperature"

# Warm-up margin: EnergyPlus's own built-in warmup only repeats DAY 1 of the RunPeriod until
# a convergence tolerance is met (EnergyPlus Engineering Reference, "Establishing Initial
# Conditions" / warmup-convergence section) -- it does not re-run the whole target window, so
# if day 1 of a short target window happens to be atypical the rest of the window can still
# start from a poorly-conditioned thermal-mass state. Prepending a few full days of the same
# representative (hot) period gives the facades -- explicitly this arc's thermal-mass focus,
# P-11 -- a better-conditioned start. 3 days is a conservative, commonly-used rule-of-thumb
# margin for exterior envelope surfaces (which equilibrate faster than deep interior mass);
# flagged as engineering judgement, not a specific paper citation.
WARMUP_MARGIN_DAYS = 3


class ResimRefusedError(RuntimeError):
    """Raised when a Tier-2 request would run against config.UTCI_ANALYSIS_WINDOW == 'annual'
    without an explicit override -- the structural trap guard T13's plan text requires
    ('enforce it in code, not a comment')."""


def extract_idf_archive(archive_zip: Path, scratch_dir: Path) -> list[Path]:
    """Unzip <cell>_step3_idfs_archive.zip's step3/idfs/*.idf into scratch_dir. Never touches
    the archive itself or the run directory it lives in."""
    scratch_dir = Path(scratch_dir)
    scratch_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_zip) as z:
        idf_names = [n for n in z.namelist() if n.startswith("step3/idfs/") and n.endswith(".idf")]
        z.extractall(scratch_dir, members=idf_names)
    return sorted((scratch_dir / n).resolve() for n in idf_names)


def _day_of_year_window(start_month: int, start_day: int, n_days: int, warmup_days: int):
    """Returns ((patched_begin_month, patched_begin_day), (end_month, end_day)) covering
    warmup_days before start plus n_days of the target window, using a fixed non-leap
    calendar (EnergyPlus RunPeriod fields are plain month/day, year-agnostic by default)."""
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    def to_doy(month, day):
        return sum(days_in_month[: month - 1]) + day

    def from_doy(doy):
        doy = ((doy - 1) % 365) + 1
        m = 1
        while doy > days_in_month[m - 1]:
            doy -= days_in_month[m - 1]
            m += 1
        return m, doy

    end_doy = to_doy(start_month, start_day) + n_days - 1
    begin_doy = to_doy(start_month, start_day) - warmup_days
    return from_doy(begin_doy), from_doy(end_doy)


def patch_idf_for_resim(
    idf_path: Path,
    out_path: Path,
    *,
    window_start_month: int,
    window_start_day: int,
    window_n_days: int = 7,
    warmup_days: int = WARMUP_MARGIN_DAYS,
) -> dict:
    """Patch a COPY of an archived IDF with exactly two changes (plan §7 T13 step 2):
    (a) append Output:Variable(*, Surface Outside Face Temperature, Hourly);
    (b) narrow RunPeriod1 to [window_start - warmup_days, window_start + window_n_days - 1].

    Returns a before/after object-count diff (all IDF object types) so callers can assert
    "nothing else changed" (T13's Tier-2 unit test).
    """
    GeomIDF.setiddname(str(config.ENERGYPLUS_IDD_PATH))
    idf = GeomIDF(str(idf_path))

    counts_before = {k: len(v) for k, v in idf.idfobjects.items()}

    (begin_m, begin_d), (end_m, end_d) = _day_of_year_window(
        window_start_month, window_start_day, window_n_days, warmup_days
    )
    rp = idf.idfobjects["RUNPERIOD"][0]
    rp.Begin_Month = begin_m
    rp.Begin_Day_of_Month = begin_d
    rp.End_Month = end_m
    rp.End_Day_of_Month = end_d

    idf.newidfobject(
        "OUTPUT:VARIABLE",
        Key_Value="*",
        Variable_Name=RESIM_OUTPUT_VARIABLE,
        Reporting_Frequency="Hourly",
    )

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    idf.saveas(str(out_path))

    counts_after = {k: len(v) for k, v in idf.idfobjects.items()}
    diff = {
        k: (counts_before.get(k, 0), counts_after.get(k, 0))
        for k in set(counts_before) | set(counts_after)
        if counts_before.get(k, 0) != counts_after.get(k, 0)
    }
    return {"object_count_diff": diff, "window": (begin_m, begin_d, end_m, end_d)}


def run_resim_side_leg(
    idf_paths: list[Path],
    epw_path: str,
    work_root: Path,
    *,
    window_mode: str,
    window_start_month: int,
    window_start_day: int,
    window_n_days: int = 7,
    n_jobs: int = -1,
    timeout_s: int = 3600,
    override_annual: bool = False,
) -> list[dict]:
    """Patch + run the side-leg for each idf in idf_paths. Refuses `window_mode == "annual"`
    unless override_annual=True (T13's structural trap guard -- per-surface-per-hour output
    across a full year and a `layout_assign` fleet is a multi-terabyte trap, plan §7 T13
    "Why the window restriction is structural")."""
    if window_mode == "annual" and not override_annual:
        raise ResimRefusedError(
            "run_resim_side_leg refused: window_mode='annual' would emit "
            "Surface Outside Face Temperature per surface per hour for a full year -- "
            "pass override_annual=True only if you have deliberately sized for it."
        )

    work_root = Path(work_root).resolve()
    patched_dir = work_root / "patched_idfs"
    sim_dir = work_root / "sim"
    patched_dir.mkdir(parents=True, exist_ok=True)
    sim_dir.mkdir(parents=True, exist_ok=True)
    epw_path = str(Path(epw_path).resolve())  # run_energyplus does cwd=work_dir -- relative
    # paths (idf_path, epw_path) would otherwise be re-resolved against the NEW cwd and double
    # up (found live during T13's own Tier-2 live test -- see progress log).

    tasks = []
    for idf_path in idf_paths:
        building_id = Path(idf_path).stem
        patched_path = (patched_dir / f"{building_id}.idf").resolve()
        patch_idf_for_resim(
            idf_path, patched_path,
            window_start_month=window_start_month, window_start_day=window_start_day,
            window_n_days=window_n_days, warmup_days=WARMUP_MARGIN_DAYS,
        )
        work_dir = (sim_dir / building_id).resolve()
        tasks.append(SimTask(
            osm_id=building_id, idf_path=str(patched_path), epw_path=str(epw_path),
            work_dir=str(work_dir),
        ))

    results = Parallel(n_jobs=n_jobs)(
        delayed(run_energyplus)(task, timeout_s) for task in tasks
    )
    for task, result in zip(tasks, results):
        result["work_dir"] = task.work_dir
    return results


def wall_surface_azimuths(idf_path: Path) -> dict:
    """Per-exterior-wall azimuth [deg clockwise from north, T04 convention], from the IDF's
    own BuildingSurface:Detailed vertex geometry via geomeppy's `.azimuth` property (verified
    numerically against a hand cross-product derivation on a real archived wall -- matches to
    <0.01 deg). geomeppy also exposes `.true_azimuth` (folding in the Building object's
    "Direction of Relative North"), but it raises BadEPFieldError on these archived IDFs
    (found live during T13's Tier-2 live test -- a geomeppy/eppy field-lookup issue, not
    something this module can fix). Every archived building in this arc's IDFs is generated
    in its own local-origin frame with zero building rotation (F-05's local-origin-XY
    pattern), so plain `.azimuth` is exactly equivalent here."""
    GeomIDF.setiddname(str(config.ENERGYPLUS_IDD_PATH))
    idf = GeomIDF(str(idf_path))
    walls = [
        s for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]
        if s.Surface_Type.lower() == "wall" and s.Outside_Boundary_Condition.lower() == "outdoors"
    ]
    return {w.Name: float(w.azimuth) for w in walls}


def harvest_wall_temperatures(sql_paths_by_building: dict) -> pd.DataFrame:
    """Read Surface Outside Face Temperature from each building's eplusout.sql (F-07's
    read-only URI pattern via parse_building_sql), keep only exterior wall surfaces (matched
    against wall_surface_azimuths' own key set -- Output:Variable(*, ...) reports every
    surface, walls and roofs and floors alike), and tag each row with the wall's azimuth.

    sql_paths_by_building: {building_id: (sql_path, idf_path)}.
    Returns a long frame: building_id, surface_name, azimuth_deg, Month, Day, Hour, t_wall_c.

    Note: EnergyPlus's SQL output always upper-cases KeyValue, while the IDF's own object
    Name field keeps its original case (e.g. "Block relation/123_whole Storey 0 Wall 0001" in
    the IDF vs. "BLOCK RELATION/123_WHOLE STOREY 0 WALL 0001" in eplusout.sql) -- found live
    during T13's Tier-2 live test. Matched case-insensitively here; the surface_name column in
    the returned frame keeps the SQL's own (upper-case) spelling.
    """
    frames = []
    for building_id, (sql_path, idf_path) in sql_paths_by_building.items():
        azimuths = wall_surface_azimuths(idf_path)
        azimuths_upper = {name.upper(): az for name, az in azimuths.items()}
        df = parse_building_sql(sql_path)
        df = df[df["variable_name"] == RESIM_OUTPUT_VARIABLE]
        df = df[df["key_value"].str.upper().isin(azimuths_upper.keys())].copy()
        if df.empty:
            continue
        df["building_id"] = building_id
        df["azimuth_deg"] = df["key_value"].str.upper().map(azimuths_upper)
        df = df.rename(columns={"key_value": "surface_name", "value": "t_wall_c"})
        frames.append(df[["building_id", "surface_name", "azimuth_deg", "Month", "Day", "Hour", "t_wall_c"]])
    if not frames:
        return pd.DataFrame(columns=["building_id", "surface_name", "azimuth_deg", "Month", "Day", "Hour", "t_wall_c"])
    return pd.concat(frames, ignore_index=True)


def quarantine_or_delete(work_root: Path, keep: bool = False) -> None:
    """Delete the scratch simulation tree (default), or rename it '_quarantined' so it is
    visually unmistakable as a boundary-condition side-leg, never a 04_/05_ artifact."""
    work_root = Path(work_root)
    if not work_root.exists():
        return
    if keep:
        target = work_root.parent / f"{work_root.name}_quarantined"
        if target.exists():
            shutil.rmtree(target)
        work_root.rename(target)
    else:
        shutil.rmtree(work_root)
