"""EU-07/T06: turn acquired ERA5 archives into a registry promotion decision.

Per fold (es/uk/it -- the three ``RULED_NOT_PINNED`` targets in
``openubem/data/weather/weather_registry.json``):

1. Count the fold's archives (``scripts.convert_era5_eu_folds_to_epw.archive_completeness``).
   Incomplete -> ``SKIP_INCOMPLETE <fold> <have>/<need>``, no conversion attempted.
2. Convert every complete calendar year in the fold's window via the existing converter's
   own per-year function (``convert_fold_year`` -- the same function ``--all-years`` calls;
   its physics and archive handling are never reimplemented here).
3. Run the six DR08 gates on each emitted EPW. Gates 1-4 and 6 come straight from
   ``openubem.acquisition.european_weather``. Gate 5 needs a local monthly benchmark file
   named ``<fold>_<year>_monthly_ghi_benchmark.json`` under ``--benchmark-dir``; when it is
   absent, gate 5 is recorded as ``PENDING_FILE_AND_BENCHMARK`` -- never a pass by omission
   (``evaluate_monthly_benchmark_gate`` itself raises on a missing file, so that composition
   is done here rather than through ``evaluate_six_gates``, which cannot express "pending").
4. Write one report per (fold, year) to
   ``openubem/outputs/eu_evidence/EU-07/t06_<fold>_<year>_six_gates.json``.
5. Promote the fold to ``RULED_PINNED`` only if exactly one candidate year exists, or the
   fold's own ``diary_window_status`` is already ``RULED_PINNED``, AND all six gates pass for
   that year (gate 5 may be ``PASS_WITH_DOCUMENTED_EXCEPTION`` only when
   ``--approve-gate5-exception <fold>[:<year>] <month>...`` named those exact months). Otherwise the
   fold stays ``RULED_NOT_PINNED``, ``acquisition_status`` is set to a truthful terminal value,
   and ``STOP <fold> <reason>`` is printed.
6. A fold with two candidate years and no ruled diary window is never promoted, even if both
   years pass every gate: ``STOP <fold> YEAR_NOT_RULED_TWO_CANDIDATES`` (FINDING EU-S2-03,
   deliberate).
7. ``--dry-run`` (default) prints every decision and still writes the per-year gate reports,
   but never touches the registry. ``--commit`` is required to write it, atomically (temp file
   then ``os.replace``), preserving every pre-existing field on the fold's entry.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import scripts.convert_era5_eu_folds_to_epw as convert_module
from openubem.acquisition import european_weather as ew
from openubem.config import ENERGYPLUS_PATH

DEFAULT_BENCHMARK_DIR = Path("openubem/data/weather/benchmarks")
DEFAULT_EVIDENCE_DIR = Path("openubem/outputs/eu_evidence/EU-07")
DEFAULT_TOLERANCE_PCT = 10.0

REPO_ROOT = Path(__file__).resolve().parents[1]


def _repo_relative_posix(path: Path | str) -> str:
    """Serialise a path the way every other EU evidence artefact does."""
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()

_GATE_KEYS = (
    "gate_1_header",
    "gate_2_8760_continuity",
    "gate_3_no_missing_mandatory_fields",
    "gate_4_physical_and_solar_bounds",
    "gate_5_monthly_national_benchmark",
    "gate_6_energyplus_smoke",
)


def evaluate_fold_year_gates(
    epw_path: Path,
    fold: str,
    year: int,
    *,
    benchmark_dir: Path,
    energyplus_root: Path,
    tolerance_pct: float,
    approved_exception_months: list[int],
    no_deu18: bool = False,
) -> dict[str, object]:
    """Run the six DR08 gates for one emitted EPW, tolerating an absent gate-5 benchmark.

    D-EU-18: when no explicit ``--approve-gate5-exception`` was given for this fold-year and
    the fold is pre-authorised (``ew.DEU18_PREAUTHORISED_FOLDS``), evaluate a gate-5-exception
    pre-authorisation automatically; a grant re-derives the gate-5 verdict as
    ``PASS_WITH_DOCUMENTED_EXCEPTION`` and is recorded under ``deu18_pre_authorisation``.
    """
    preflight = ew.validate_epw_preflight(epw_path)
    benchmark_path = Path(benchmark_dir) / f"{fold}_{year}_monthly_ghi_benchmark.json"
    deu18_pre_authorisation: dict[str, object] | None = None
    if benchmark_path.is_file():
        gate_5 = ew.evaluate_monthly_benchmark_gate(
            epw_path, benchmark_path,
            tolerance_pct=tolerance_pct,
            approved_exception_months=approved_exception_months,
        )
        gate_5_verdict = gate_5["verdict"]
        benchmark_file = _repo_relative_posix(benchmark_path)
        benchmark_missing_reason = None
    else:
        gate_5 = None
        gate_5_verdict = "PENDING_FILE_AND_BENCHMARK"
        benchmark_file = None
        benchmark_missing_reason = f"benchmark file not found: {benchmark_path}"
    gate_6 = ew.evaluate_energyplus_smoke_gate(epw_path, energyplus_root=energyplus_root)

    if (
        gate_5 is not None
        and not no_deu18
        and not approved_exception_months
        and fold in ew.DEU18_PREAUTHORISED_FOLDS
    ):
        other_gate_verdicts = {
            "gate_1_header": preflight["gate_1_header"],
            "gate_2_8760_continuity": preflight["gate_2_8760_continuity"],
            "gate_3_no_missing_mandatory_fields": preflight["gate_3_no_missing_mandatory_fields"],
            "gate_4_physical_and_solar_bounds": preflight["gate_4_physical_and_solar_bounds"],
            "gate_6_energyplus_smoke": gate_6["verdict"],
        }
        deu18_pre_authorisation = ew.evaluate_deu18_pre_authorisation(
            gate_5, fold=fold, other_gate_verdicts=other_gate_verdicts,
        )
        if deu18_pre_authorisation["granted"]:
            gate_5_verdict = "PASS_WITH_DOCUMENTED_EXCEPTION"
            months = deu18_pre_authorisation["granted_exception_months"]
            annual = deu18_pre_authorisation["annual_delta_pct"]
            print(f"DEU18_GRANTED {fold} {year} months={months} annual={annual:.4f}%")
        elif deu18_pre_authorisation["refusal_reasons"] != ["NO_EXCEPTION_NEEDED"]:
            reasons = ";".join(deu18_pre_authorisation["refusal_reasons"])
            print(f"DEU18_REFUSED {fold} {year} {reasons}")

    return {
        "fold": fold,
        "year": year,
        "epw_file": _repo_relative_posix(epw_path),
        "epw_sha256": convert_module.sha256_of(Path(epw_path)),
        "gate_1_header": preflight["gate_1_header"],
        "gate_2_8760_continuity": preflight["gate_2_8760_continuity"],
        "gate_3_no_missing_mandatory_fields": preflight["gate_3_no_missing_mandatory_fields"],
        "gate_4_physical_and_solar_bounds": preflight["gate_4_physical_and_solar_bounds"],
        "gate_5_monthly_national_benchmark": gate_5_verdict,
        "gate_6_energyplus_smoke": gate_6["verdict"],
        "benchmark_file": benchmark_file,
        "benchmark_missing_reason": benchmark_missing_reason,
        "deu18_pre_authorisation": deu18_pre_authorisation,
    }


def _all_gates_pass(report: dict[str, object]) -> bool:
    for key in _GATE_KEYS:
        if key == "gate_5_monthly_national_benchmark":
            if report[key] not in ("PASS", "PASS_WITH_DOCUMENTED_EXCEPTION"):
                return False
        elif report[key] != "PASS":
            return False
    return True


def _blocking_reason(report: dict[str, object]) -> str:
    if report["gate_5_monthly_national_benchmark"] == "PENDING_FILE_AND_BENCHMARK":
        return "GATE5_PENDING_BENCHMARK"
    if report["gate_6_energyplus_smoke"] != "PASS":
        return f"GATE6_{report['gate_6_energyplus_smoke']}"
    if report["gate_5_monthly_national_benchmark"] not in ("PASS", "PASS_WITH_DOCUMENTED_EXCEPTION"):
        return f"GATE5_{report['gate_5_monthly_national_benchmark']}"
    for key in (
        "gate_1_header", "gate_2_8760_continuity",
        "gate_3_no_missing_mandatory_fields", "gate_4_physical_and_solar_bounds",
    ):
        if report[key] != "PASS":
            return f"{key.upper()}_{report[key]}"
    return "GATES_NOT_ALL_PASS"


def _write_report(evidence_dir: Path, fold: str, year: int, report: dict[str, object]) -> Path:
    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    output = evidence_dir / f"t06_{fold}_{year}_six_gates.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return output


def _write_registry_atomic(registry_path: Path, registry: dict[str, object]) -> None:
    registry_path = Path(registry_path)
    tmp = registry_path.with_name(registry_path.name + ".tmp")
    tmp.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, registry_path)


def _update_fold_entry(registry_path: Path, fold: str, updates: dict[str, object]) -> None:
    registry_path = Path(registry_path)
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    for entry in registry["targets"]:
        if entry.get("fold") == fold:
            entry.update(updates)
            break
    else:
        raise ValueError(f"fold {fold!r} not present in registry {registry_path}")
    _write_registry_atomic(registry_path, registry)


def process_fold(
    fold: str,
    target: dict[str, object],
    *,
    benchmark_dir: Path,
    energyplus_root: Path,
    tolerance_pct: float,
    approved_months: dict[str, list[int]],
    evidence_dir: Path,
    registry_path: Path,
    commit: bool,
    no_deu18: bool = False,
) -> str:
    """Run the T06 decision for one fold and return a short decision tag (for tests)."""
    have, need, _missing = convert_module.archive_completeness(target)
    if have < need:
        print(f"SKIP_INCOMPLETE {fold} {have}/{need}")
        return "SKIP_INCOMPLETE"

    start_year, end_year = convert_module.window_years(target)
    candidate_years: list[int] = []
    epw_paths: dict[int, Path] = {}
    for year in dict.fromkeys([start_year, end_year]):
        epw_path = convert_module.convert_fold_year(target, year)
        if epw_path is not None:
            candidate_years.append(year)
            epw_paths[year] = epw_path

    reports: dict[int, dict[str, object]] = {}
    for year in candidate_years:
        report = evaluate_fold_year_gates(
            epw_paths[year], fold, year,
            benchmark_dir=benchmark_dir, energyplus_root=energyplus_root,
            tolerance_pct=tolerance_pct,
            approved_exception_months=_approved_for(approved_months, fold, year),
            no_deu18=no_deu18,
        )
        reports[year] = report
        _write_report(evidence_dir, fold, year, report)

    if not candidate_years:
        print(f"STOP {fold} NO_YEAR_CONVERTED")
        return "STOP"

    if len(candidate_years) == 1:
        ruled_year = candidate_years[0]
    elif target.get("diary_window_status") == "RULED_PINNED":
        resolved = convert_module.resolve_year(target, None)
        if resolved not in candidate_years:
            print(f"STOP {fold} YEAR_NOT_RULED_TWO_CANDIDATES")
            return "STOP"
        ruled_year = resolved
    else:
        print(f"STOP {fold} YEAR_NOT_RULED_TWO_CANDIDATES")
        return "STOP"

    report = reports[ruled_year]
    if not _all_gates_pass(report):
        reason = _blocking_reason(report)
        print(f"STOP {fold} {reason}")
        if commit:
            _update_fold_entry(registry_path, fold, {
                "acquisition_status": f"BLOCKED_{reason}",
                "validation": {key: report[key] for key in _GATE_KEYS},
            })
        return "STOP"

    if commit:
        updates: dict[str, object] = {
            "status": "RULED_PINNED",
            "weather_file": str(epw_paths[ruled_year]).replace("\\", "/"),
            "sha256": report["epw_sha256"],
            "diary_window": f"{ruled_year}-01-01/{ruled_year}-12-31",
            "diary_window_status": "RULED_PINNED",
            "acquisition_status": "ACQUIRED_CONVERTED",
            "validation": {key: report[key] for key in _GATE_KEYS},
        }
        grant = report.get("deu18_pre_authorisation")
        if grant and grant.get("granted"):
            updates["gate5_exception"] = {
                "ruling": "D-EU-18",
                "months": grant["granted_exception_months"],
                "annual_delta_pct": grant["annual_delta_pct"],
                "measured": grant["measured"],
            }
        _update_fold_entry(registry_path, fold, updates)
        print(f"PROMOTED {fold} {ruled_year}")
        return "PROMOTED"

    print(f"WOULD_PROMOTE {fold} {ruled_year}")
    return "WOULD_PROMOTE"


def _parse_approved_exceptions(raw: list[list[str]] | None) -> dict[str, list[int]]:
    """Parse ``FOLD MONTH...`` or ``FOLD:YEAR MONTH...`` into a keyed approval table.

    The offending month differs between candidate years of the same fold (FINDING EU-S2-06),
    so the approval has to be addressable per fold-year. The bare-fold form is kept: it means
    "these months for every year of this fold", and a ``fold:year`` key overrides it.
    """
    result: dict[str, list[int]] = {}
    for tokens in raw or []:
        if len(tokens) < 2:
            raise SystemExit("--approve-gate5-exception requires FOLD[:YEAR] and at least one MONTH")
        key_token, *month_tokens = tokens
        fold_token, _, year_token = key_token.partition(":")
        if year_token and not year_token.isdigit():
            raise SystemExit(f"--approve-gate5-exception: {key_token!r} is not FOLD or FOLD:YEAR")
        months = [int(month) for month in month_tokens]
        if any(month < 1 or month > 12 for month in months):
            raise SystemExit(f"--approve-gate5-exception: months must be 1-12, got {months}")
        result[f"{fold_token}:{year_token}" if year_token else fold_token] = months
    return result


def _approved_for(approved: dict[str, list[int]], fold: str, year: int) -> list[int]:
    """Fold-year approval wins over a fold-wide one; absent means no exception is granted."""
    return approved.get(f"{fold}:{year}", approved.get(fold, []))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fold", action="append", choices=["es", "uk", "it"], help="repeatable")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--benchmark-dir", type=Path, default=DEFAULT_BENCHMARK_DIR)
    parser.add_argument("--energyplus-root", type=Path, default=ENERGYPLUS_PATH)
    parser.add_argument("--tolerance-pct", type=float, default=DEFAULT_TOLERANCE_PCT)
    parser.add_argument(
        "--approve-gate5-exception", action="append", nargs="+", metavar=("FOLD[:YEAR]", "MONTH"),
        help="repeatable; FOLD or FOLD:YEAR, e.g. --approve-gate5-exception es:2009 12",
    )
    parser.add_argument("--registry", type=Path, default=convert_module.REGISTRY_PATH)
    parser.add_argument("--evidence-dir", type=Path, default=DEFAULT_EVIDENCE_DIR)
    parser.add_argument("--commit", action="store_true")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument(
        "--no-deu18", action="store_true",
        help="disable the D-EU-18 automatic gate-5 pre-authorisation path entirely",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.all and not args.fold:
        parser.error("pass --all or at least one --fold")
    commit = bool(args.commit)

    approved = _parse_approved_exceptions(args.approve_gate5_exception)
    targets = convert_module.load_fold_targets(args.registry)
    folds = list(targets) if args.all else list(dict.fromkeys(args.fold or []))
    for fold in folds:
        process_fold(
            fold, targets[fold],
            benchmark_dir=args.benchmark_dir,
            energyplus_root=args.energyplus_root,
            tolerance_pct=args.tolerance_pct,
            approved_months=approved,
            evidence_dir=args.evidence_dir,
            registry_path=args.registry,
            commit=commit,
            no_deu18=args.no_deu18,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
