"""Module 12b: task-list builder, resume, joblib fan-out, purge, manifest (DESIGN §3A–§3D, §3F)."""
from __future__ import annotations

import os
import traceback
from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import pandas as pd
from joblib import Parallel, delayed

from openubem import config
from openubem._rust_bridge import get_rust_backend_mode, load_rust_module
from openubem.simulation.runner import (
    _version_handshake,
    classify_outcome,
    run_energyplus,
    _SUCCESS_MARKER,
    _parse_end_counts,
)


class PrepPhaseFailedError(RuntimeError):
    pass


# ── 3A: SimTask (F2) ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SimTask:
    osm_id: str
    idf_path: str
    epw_path: str
    work_dir: str


def build_task_list(
    idf_manifest: pd.DataFrame,
    enriched_gdf: gpd.GeoDataFrame,
    sim_root: Path,
) -> tuple[list[SimTask], pd.DataFrame]:
    """Build SimTask list from simulable rows; return (tasks, skipped_df) (DESIGN §3A, F2)."""
    epw_map = enriched_gdf[["osm_id", "epw_path"]].set_index("osm_id")["epw_path"]

    simulable = idf_manifest[idf_manifest["generation_status"] == "success"]
    skipped = idf_manifest[idf_manifest["generation_status"] != "success"]

    # Fail-fast: any simulable row with no epw_path (F2)
    missing = [
        row.osm_id for row in simulable.itertuples()
        if row.osm_id not in epw_map or pd.isna(epw_map[row.osm_id])
    ]
    if missing:
        raise ValueError(
            f"build_task_list: missing epw_path for {len(missing)} simulable buildings: "
            f"{missing[:5]}{'...' if len(missing) > 5 else ''}"
        )

    tasks = [
        SimTask(
            osm_id=row.osm_id,
            idf_path=str(row.idf_path),
            epw_path=str(epw_map[row.osm_id]),
            work_dir=str(sim_root / row.osm_id),
        )
        for row in simulable.itertuples()
    ]
    return tasks, skipped


# ── 3B: resume detection + work-dir provisioning (F3, P6) ────────────────────

def is_completed(work_dir: Path) -> bool:
    """True iff eplusout.end + eplusout.sql both exist and .end contains success marker (F3)."""
    end_file = work_dir / "eplusout.end"
    sql_file = work_dir / "eplusout.sql"
    if not (end_file.exists() and sql_file.exists()):
        return False
    return _SUCCESS_MARKER in end_file.read_text(errors="replace")


def _safe_rmtree(path: Path, sim_root: Path) -> None:
    """Delete path only if it is strictly under sim_root (P6: guard against mis-joined paths)."""
    import shutil
    path = path.resolve()
    sim_root = sim_root.resolve()
    assert path != sim_root and sim_root in path.parents, (
        f"_safe_rmtree: {path} is not strictly under {sim_root} — refusing to delete"
    )
    shutil.rmtree(path)


def _split_resume(
    tasks: list[SimTask],
    force_rerun: bool,
    sim_root: Path,
) -> tuple[list[SimTask], list[SimTask]]:
    """
    Partition tasks into (fresh, cached).
    force_rerun=True → delete+recreate every work_dir, all tasks are fresh.
    Existing but incomplete dirs → delete+recreate (stale crash debris must not survive).
    Returns (fresh_tasks, cached_tasks).
    """
    fresh, cached = [], []
    for task in tasks:
        wd = Path(task.work_dir)
        if force_rerun:
            if wd.exists():
                _safe_rmtree(wd, sim_root)
            fresh.append(task)
        elif is_completed(wd):
            cached.append(task)
        else:
            if wd.exists():
                _safe_rmtree(wd, sim_root)
            fresh.append(task)
    return fresh, cached


# ── 3F: purge + manifest ──────────────────────────────────────────────────────

def _purge_work_dir(work_dir: Path) -> None:
    """Delete files not in config.SIM_RETAIN_FILES from a success work_dir (DESIGN §3F, F9)."""
    retain = set(config.SIM_RETAIN_FILES) | {"gpusim_provenance.json"}
    for f in work_dir.iterdir():
        if f.is_file() and f.name not in retain:
            f.unlink()


def _build_cached_row(task: SimTask, ep_version: str) -> dict:
    """Re-parse counts from existing .end for a resume hit (F8 success_cached)."""
    wd = Path(task.work_dir)
    end_text = (wd / "eplusout.end").read_text(errors="replace")
    n_warn, n_sev = _parse_end_counts(end_text)
    sql_path = str(wd / "eplusout.sql")
    return {
        "osm_id": task.osm_id,
        "idf_path": task.idf_path,
        "work_dir": task.work_dir,
        "sql_path": sql_path,
        "status": "success_cached",
        "n_warnings": n_warn,
        "n_severe": n_sev,
        "wall_clock_s": 0.0,
        "ep_version": ep_version,
        "epw_path": task.epw_path,
        "error_summary": "",
    }


def _emit_manifest(
    raw_results: list[dict],
    cached_tasks: list[SimTask],
    skipped_df: pd.DataFrame,
    idf_manifest: pd.DataFrame,
    sim_root: Path,
    ep_version: str,
) -> pd.DataFrame:
    """
    Assemble 04_simulation_manifest.parquet from fresh results, cached hits, and skipped rows.
    Enforces F10/P9 schema: N_input rows × 11 cols, nullable Int64 counts, empty str not NaN.
    """
    rows = []

    # Fresh simulated rows
    for r in raw_results:
        osm_id = r["osm_id"]
        # Recover task info from idf_manifest
        m_row = idf_manifest[idf_manifest["osm_id"] == osm_id]
        idf_path = str(m_row.iloc[0]["idf_path"]) if len(m_row) else ""
        work_dir = str(sim_root / osm_id)
        wd = Path(work_dir)

        status = r.get("status", "failed_crash")
        sql_path = str(wd / "eplusout.sql") if status in {"success"} and (wd / "eplusout.sql").exists() else ""

        # Purge only success dirs, after readVarsESO has run
        if status == "success":
            _purge_work_dir(wd)

        rows.append({
            "osm_id": osm_id,
            "idf_path": idf_path,
            "work_dir": work_dir,
            "sql_path": sql_path,
            "status": status,
            "n_warnings": r.get("n_warnings"),
            "n_severe": r.get("n_severe"),
            "wall_clock_s": float(r.get("wall_clock_s", 0.0)),
            "ep_version": ep_version,
            "epw_path": r.get("epw_path", ""),
            "error_summary": r.get("error_summary", "") or "",
        })

    # Cached rows
    for task in cached_tasks:
        rows.append(_build_cached_row(task, ep_version))

    # Skipped rows (not_attempted_invalid_idf)
    for _, sk in skipped_df.iterrows():
        rows.append({
            "osm_id": str(sk["osm_id"]),
            "idf_path": str(sk.get("idf_path", "")) or "",
            "work_dir": "",
            "sql_path": "",
            "status": "not_attempted_invalid_idf",
            "n_warnings": None,
            "n_severe": None,
            "wall_clock_s": 0.0,
            "ep_version": ep_version,
            "epw_path": "",
            "error_summary": str(sk.get("generation_status", "")) or "",
        })

    df = pd.DataFrame(rows, columns=[
        "osm_id", "idf_path", "work_dir", "sql_path", "status",
        "n_warnings", "n_severe", "wall_clock_s", "ep_version", "epw_path", "error_summary",
    ])

    # P9: nullable Int64 for counts; empty string (not NaN) for sql_path / error_summary
    df["n_warnings"] = df["n_warnings"].astype("Int64")
    df["n_severe"] = df["n_severe"].astype("Int64")
    df["sql_path"] = df["sql_path"].fillna("").astype(str)
    df["error_summary"] = df["error_summary"].fillna("").astype(str)

    if get_rust_backend_mode() != "off":
        rust = load_rust_module()
        if rust is not None and hasattr(rust, "schema_validate_sim_manifest_table"):
            import pyarrow as pa

            table = pa.table({
                "osm_id": pa.array(df["osm_id"].astype(str).tolist(), type=pa.string()),
                "idf_path": pa.array(df["idf_path"].astype(str).tolist(), type=pa.string()),
                "work_dir": pa.array(df["work_dir"].astype(str).tolist(), type=pa.string()),
                "sql_path": pa.array(df["sql_path"].astype(str).tolist(), type=pa.string()),
                "status": pa.array(df["status"].astype(str).tolist(), type=pa.string()),
                "n_warnings": pa.array([None if pd.isna(v) else int(v) for v in df["n_warnings"]], type=pa.int64()),
                "n_severe": pa.array([None if pd.isna(v) else int(v) for v in df["n_severe"]], type=pa.int64()),
                "wall_clock_s": pa.array(df["wall_clock_s"].to_numpy(dtype=float), type=pa.float64()),
                "ep_version": pa.array(df["ep_version"].astype(str).tolist(), type=pa.string()),
                "epw_path": pa.array(df["epw_path"].astype(str).tolist(), type=pa.string()),
                "error_summary": pa.array(df["error_summary"].astype(str).tolist(), type=pa.string()),
            })
            rust.schema_validate_sim_manifest_table(table)

    return df


# ── 3D: _worker + run_neighbourhood ──────────────────────────────────────────

def _worker(task: SimTask) -> dict:
    """
    Top-level worker: run one building, classify outcome.
    Any exception → failed_crash dict (DESIGN §3D: worker never raises into joblib).
    """
    try:
        raw = run_energyplus(task)
        classified = classify_outcome(raw, Path(task.work_dir))
        classified["epw_path"] = task.epw_path
        return classified
    except Exception:
        return {
            "osm_id": task.osm_id,
            "status": "failed_crash",
            "wall_clock_s": 0.0,
            "n_warnings": None,
            "n_severe": None,
            "error_summary": traceback.format_exc()[-500:],
            "epw_path": task.epw_path,
        }


def run_neighbourhood(
    idf_manifest: pd.DataFrame,
    enriched_gdf: gpd.GeoDataFrame,
    sim_root: Path,
    n_jobs: int = config.N_JOBS,
    backend: str = "loky",
    force_rerun: bool = False,
    sim_engine: str | None = None,
    gpusim_device: str | None = None,
    spot_check_fraction: float | None = None,
) -> pd.DataFrame:
    """
    Fan-out EnergyPlus (and optionally gpusim) over all generation-success IDFs;
    return 04 manifest DataFrame (DESIGN §3D, BUILD_SPEC M5).

    Writes 04_simulation_manifest.parquet into sim_root (plus 04_routing_report.csv
    when ``sim_engine`` is ``"gpusim"`` or ``"auto"``).
    """
    sim_root = Path(sim_root)
    sim_root.mkdir(parents=True, exist_ok=True)

    eff_engine = (
        config.SIM_ENGINE if sim_engine is None else str(sim_engine)
    ).strip().lower()
    if eff_engine not in {"energyplus", "gpusim", "auto"}:
        raise ValueError(f"Unsupported sim_engine={sim_engine!r}")
    eff_device = (
        config.GPUSIM_DEVICE if gpusim_device is None else str(gpusim_device)
    )
    eff_spot = (
        config.GPUSIM_SPOT_CHECK_FRACTION
        if spot_check_fraction is None
        else float(spot_check_fraction)
    )

    if config.PREP_ABORT_ON_FAILURE:
        failed_mask = idf_manifest["generation_status"] != "success"
        n_failed = int(failed_mask.sum())
        if n_failed:
            failed_ids = idf_manifest.loc[failed_mask, "osm_id"].astype(str).tolist()
            raise PrepPhaseFailedError(
                f"{n_failed} building(s) failed IDF generation before simulation: "
                f"{failed_ids[:5]}"
            )

    tasks, skipped = build_task_list(idf_manifest, enriched_gdf, sim_root)
    fresh, cached = _split_resume(tasks, force_rerun, sim_root)

    if eff_engine == "energyplus":
        ep_version = _version_handshake()  # fail-fast before any dispatch (F5)
        raw_results: list[dict] = []
        if fresh:
            raw_results = Parallel(n_jobs=n_jobs, backend=backend, verbose=10)(
                delayed(_worker)(t) for t in fresh
            )
        manifest_df = _emit_manifest(
            raw_results, cached, skipped, idf_manifest, sim_root, ep_version
        )
        manifest_df.to_parquet(
            sim_root / "04_simulation_manifest.parquet",
            engine="pyarrow", index=False,
        )
        return manifest_df

    from openubem.gpusim.router import (
        route_idf_text,
        run_routed_gpusim_batch,
        write_routing_report_csv,
    )

    decisions = []
    ep_tasks: list[SimTask] = []
    gpu_tasks: list[SimTask] = []
    gpu_decisions = []
    for t in fresh:
        idf_text = Path(t.idf_path).read_text(encoding="utf-8", errors="replace")
        dec = route_idf_text(
            idf_text,
            t.osm_id,
            sim_engine=eff_engine,
            device=eff_device,
            spot_check_fraction=eff_spot if eff_engine == "auto" else 0.0,
            eplus_version=config.ENERGYPLUS_VERSION,
        )
        decisions.append(dec)
        if dec.selected_engine == "gpusim":
            gpu_tasks.append(t)
            gpu_decisions.append(dec)
        else:
            ep_tasks.append(t)

    write_routing_report_csv(decisions, sim_root / "04_routing_report.csv")

    ep_version = config.ENERGYPLUS_VERSION
    if ep_tasks:
        ep_version = _version_handshake()

    raw_results = []
    if ep_tasks:
        raw_results.extend(
            Parallel(n_jobs=n_jobs, backend=backend, verbose=10)(
                delayed(_worker)(t) for t in ep_tasks
            )
        )
    if gpu_tasks:
        gpu_rows = run_routed_gpusim_batch(
            idf_paths=[Path(t.idf_path) for t in gpu_tasks],
            epw_paths=[Path(t.epw_path) for t in gpu_tasks],
            work_dirs=[Path(t.work_dir) for t in gpu_tasks],
            building_ids=[t.osm_id for t in gpu_tasks],
            decisions=gpu_decisions,
            device=eff_device,
        )
        raw_results.extend(gpu_rows)

    manifest_df = _emit_manifest(
        raw_results, cached, skipped, idf_manifest, sim_root, ep_version
    )
    manifest_df.to_parquet(
        sim_root / "04_simulation_manifest.parquet",
        engine="pyarrow", index=False,
    )
    return manifest_df
