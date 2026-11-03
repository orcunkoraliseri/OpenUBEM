"""Acquire the DR08 gate-5 monthly-GHI benchmark files from PVGIS.

Gate 5 compares an EPW's monthly global horizontal irradiation against an independent
monthly reference. That reference is a LOCAL file, deliberately: live fetches at gate
time would make a verdict unreproducible. This script is the one deliberate acquisition
act that materialises those files, with their provenance recorded in the file itself.

One file per fold-year. Candidate years come from the registry's own ``raw_era5_window``
(FINDING EU-S2-03: no fold outside France has a ruled diary year, so both candidate years
are acquired and neither is chosen here). Coordinates come from the registry verbatim --
never re-typed here -- so the benchmark is queried at exactly the point the EPW is built
for.

The France benchmark is not acquired by this script. It was transcribed from the evidence
document the owner ruled on and must never be re-queried: re-querying would silently
replace the numbers the RULED_PINNED_EXCEPTION was granted against.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

from openubem.acquisition.european_weather import NEW_SURVEY_YEARS

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "openubem" / "data" / "weather" / "weather_registry.json"
BENCHMARK_DIR = REPO_ROOT / "openubem" / "data" / "weather" / "benchmarks"

PVGIS_BASE = "https://re.jrc.ec.europa.eu/api/v5_3/MRcalc"
PVGIS_BASE_NSRDB = "https://re.jrc.ec.europa.eu/api/v5_2/MRcalc"
NEW_FOLD_DATABASE_ORDER = (
    ("PVGIS-SARAH3", PVGIS_BASE, "v5_3"),
    ("PVGIS-NSRDB", PVGIS_BASE_NSRDB, "v5_2"),
    ("PVGIS-ERA5", PVGIS_BASE, "v5_3"),
)
RULED_TRANSCRIBED_FOLDS = {"fr"}


def _endpoint(latitude: float, longitude: float, year: int, *, base: str = PVGIS_BASE, database: str | None = None) -> str:
    extra = f"&raddatabase={database}" if database else ""
    return (
        f"{base}?lat={latitude}&lon={longitude}&horirrad=1"
        f"&startyear={year}&endyear={year}{extra}&outputformat=json"
    )


def _candidate_years(window: str) -> list[int]:
    start, _, end = window.partition("/")
    first, last = int(start[:4]), int(end[:4])
    if last < first:
        raise ValueError(f"raw_era5_window is inverted: {window}")
    return list(range(first, last + 1))


def _http_error_text(exc: urllib.error.HTTPError) -> str:
    try:
        return f"HTTP {exc.code}: {exc.read().decode('utf-8', 'replace')[:300]}"
    except Exception:
        return f"HTTP {exc.code}"


def _fetch_monthly_ghi(
    latitude: float, longitude: float, year: int, timeout: float,
    *, base: str = PVGIS_BASE, database: str | None = None,
) -> list[float]:
    url = _endpoint(latitude, longitude, year, base=base, database=database)
    with urllib.request.urlopen(url, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))

    monthly = payload.get("outputs", {}).get("monthly")
    if not isinstance(monthly, list) or len(monthly) != 12:
        raise ValueError(
            f"PVGIS returned {len(monthly) if isinstance(monthly, list) else 'no'} monthly rows "
            f"for {year} at ({latitude}, {longitude}); gate 5 reads exactly twelve"
        )

    ordered: dict[int, float] = {}
    for row in monthly:
        if int(row["year"]) != year:
            raise ValueError(f"PVGIS returned year {row['year']} when {year} was requested")
        ordered[int(row["month"])] = float(row["H(h)_m"])
    if sorted(ordered) != list(range(1, 13)):
        raise ValueError(f"PVGIS months are not 1..12 for {year}: {sorted(ordered)}")
    values = [ordered[month] for month in range(1, 13)]
    if any(value <= 0 for value in values):
        raise ValueError(f"PVGIS returned a non-positive monthly total for {year}: {values}")
    return values


def _benchmark_document(target: dict, year: int, values: list[float]) -> dict:
    return {
        "schema_version": "eu-monthly-ghi-benchmark/1.0",
        "fold": target["fold"],
        "year": year,
        "quantity": "monthly horizontal irradiation H(h)_m",
        "units": "kWh/m2",
        "source": "European Commission Joint Research Centre PVGIS MRcalc (v5_3)",
        "source_endpoint": _endpoint(target["latitude"], target["longitude"], year),
        "latitude": target["latitude"],
        "longitude": target["longitude"],
        "station": target["station"],
        "retrieved_utc": date.today().isoformat(),
        "acquisition_note": (
            "Acquired by scripts/acquire_pvgis_monthly_ghi_benchmarks.py directly from the PVGIS "
            "endpoint recorded above. Values are stored exactly as returned: not rounded, not "
            "re-ordered, not interpolated. Index 0 is January. This file exists so DR08 gate 5 can "
            "be re-run offline against the same numbers for the life of the contract."
        ),
        "candidate_year_note": (
            "This fold has two candidate years (FINDING EU-S2-03). A benchmark is per fold-year; "
            "acquiring both does not choose between them. Year selection is a diary question and "
            "the diary is GSSCanada-owned."
        ),
        "approved_exception_months": [],
        "monthly_ghi_kwh_m2": values,
        "monthly_ghi_order_note": "Index 0 is January; the gate reads exactly twelve ordered values.",
    }


def _fetch_new_fold(target: dict, year: int, timeout: float) -> tuple[list[float], str, str, list[str]]:
    failures: list[str] = []
    for database, base, version in NEW_FOLD_DATABASE_ORDER:
        try:
            values = _fetch_monthly_ghi(
                target["latitude"], target["longitude"], year, timeout, base=base, database=database
            )
        except urllib.error.HTTPError as exc:
            failures.append(f"{database} ({version}): {_http_error_text(exc)}")
            continue
        except (urllib.error.URLError, ValueError, KeyError, TimeoutError) as exc:
            failures.append(f"{database} ({version}): {type(exc).__name__}: {exc}")
            continue
        endpoint = _endpoint(target["latitude"], target["longitude"], year, base=base, database=database)
        return values, database, endpoint, failures
    raise ValueError("no PVGIS database answered: " + " | ".join(failures))


def _new_fold_document(target: dict, year: int, values: list[float], database: str, endpoint: str, failures: list[str]) -> dict:
    independent = database != "PVGIS-ERA5"
    version = "v5_2" if database == "PVGIS-NSRDB" else "v5_3"
    document = _benchmark_document(target, year, values)
    document["source"] = (
        f"European Commission Joint Research Centre PVGIS MRcalc ({version}), radiation database {database}"
        + ("" if independent else "; benchmark is ERA5-derived, not independent")
    )
    document["source_endpoint"] = endpoint
    document["radiation_database"] = database
    document["independent_of_era5"] = independent
    document["database_order"] = [name for name, _base, _version in NEW_FOLD_DATABASE_ORDER]
    document["databases_refused_before_this_one"] = failures
    document["candidate_year_note"] = (
        "Survey-year benchmark (D-EU-155, 2026-10-08): one file for the MTUS survey year only."
    )
    return document


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folds", nargs="*", default=["es", "uk", "it"])
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    targets = {entry["fold"]: entry for entry in registry["targets"]}

    BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)
    written = 0
    failed = 0

    for fold in args.folds:
        if fold in RULED_TRANSCRIBED_FOLDS:
            print(f"REFUSED {fold} RULED_TRANSCRIBED_BENCHMARK_NOT_REQUERIED")
            failed += 1
            continue
        target = targets.get(fold)
        if target is None:
            print(f"REFUSED {fold} NOT_IN_REGISTRY")
            failed += 1
            continue

        if fold in NEW_SURVEY_YEARS:
            year = NEW_SURVEY_YEARS[fold]
            destination = BENCHMARK_DIR / f"{fold}_{year}_monthly_ghi_benchmark.json"
            if destination.exists() and not args.overwrite:
                print(f"SKIP {fold} {year} EXISTS {destination.name}")
                continue
            if args.dry_run:
                print(f"DRY_RUN {fold} {year}")
                continue
            try:
                values, database, endpoint, failures = _fetch_new_fold(target, year, args.timeout)
            except ValueError as exc:
                print(f"FAILED {fold} {year} {exc}")
                failed += 1
                continue
            document = _new_fold_document(target, year, values, database, endpoint, failures)
            destination.write_text(
                json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            written += 1
            print(f"WROTE {fold} {year} {destination.name} db={database} annual={sum(values):.2f} kWh/m2")
            for line in failures:
                print(f"  REFUSED {line}")
            continue
        for year in _candidate_years(target["raw_era5_window"]):
            destination = BENCHMARK_DIR / f"{fold}_{year}_monthly_ghi_benchmark.json"
            if destination.exists() and not args.overwrite:
                print(f"SKIP {fold} {year} EXISTS {destination.name}")
                continue
            if args.dry_run:
                print(f"DRY_RUN {fold} {year} {_endpoint(target['latitude'], target['longitude'], year)}")
                continue
            try:
                values = _fetch_monthly_ghi(
                    target["latitude"], target["longitude"], year, args.timeout
                )
            except (urllib.error.URLError, ValueError, KeyError, TimeoutError) as exc:
                print(f"FAILED {fold} {year} {type(exc).__name__}: {exc}")
                failed += 1
                continue
            document = _benchmark_document(target, year, values)
            destination.write_text(
                json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            written += 1
            print(f"WROTE {fold} {year} {destination.name} annual={sum(values):.2f} kWh/m2")

    print(f"SUMMARY written={written} failed={failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
