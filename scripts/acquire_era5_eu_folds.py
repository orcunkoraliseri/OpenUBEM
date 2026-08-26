"""Submit and poll the ES/GB/IT direct-ERA5 acquisitions (D-EU-07, generalised).

Generalises ``acquire_era5_lyon_bron_2023.py`` to the three remaining
``RULED_NOT_PINNED`` targets of ``openubem/data/weather/weather_registry.json``:
Madrid 2009-2010, London 2014-2015 and Bologna 2013-2014.  Coordinates and
windows are read from the registry itself -- never retyped.  Each fold's
24-month window plus its one UTC boundary day (2023-12-31-style local-standard
offset) is submitted one CDS job at a time: concurrent CDS jobs were rejected
during the Lyon acquisition, so every fold and every month is queued through
the exact same sequential submit/poll/download loop.

Use ``--submit`` once, then rerun ``--poll`` until all files are downloaded, or
``--run-sequential`` to acquire every missing job across all three folds one
at a time without leaving the process.  No credential is accepted as an
argument: cdsapi reads the user's configured CDS credentials itself.
"""
from __future__ import annotations

import argparse
import json
import time
from calendar import monthrange
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from cdsapi.api import get_url_key_verify
from ecmwf.datastores.client import Client as DatastoresClient


DATASET = "reanalysis-era5-single-levels"
REGISTRY_PATH = Path("openubem/data/weather/weather_registry.json")
VARIABLES = [
    "2m_temperature",
    "2m_dewpoint_temperature",
    "surface_pressure",
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
    "surface_solar_radiation_downwards",
    "total_sky_direct_solar_radiation_at_surface",
    "total_cloud_cover",
    "total_precipitation",
]
_GRID_STEP_DEG = 0.25
_GRID_MARGIN_DEG = 0.1


def _grid_area(latitude: float, longitude: float) -> list[float]:
    """Return the smallest non-zero crop enclosing exactly one 0.25° ERA5 grid point."""
    grid_lat = round(float(latitude) / _GRID_STEP_DEG) * _GRID_STEP_DEG
    grid_lon = round(float(longitude) / _GRID_STEP_DEG) * _GRID_STEP_DEG
    return [
        round(grid_lat + _GRID_MARGIN_DEG, 3),
        round(grid_lon - _GRID_MARGIN_DEG, 3),
        round(grid_lat - _GRID_MARGIN_DEG, 3),
        round(grid_lon + _GRID_MARGIN_DEG, 3),
    ]


def _load_targets(registry_path: Path = REGISTRY_PATH) -> list[dict[str, object]]:
    """Read every RULED_NOT_PINNED target's fold, city, coordinates and window."""
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    targets: list[dict[str, object]] = []
    for entry in registry["targets"]:
        if entry.get("status") != "RULED_NOT_PINNED":
            continue
        start_str, end_str = str(entry["raw_era5_window"]).split("/")
        start_year = int(start_str[:4])
        end_year = int(end_str[:4])
        targets.append({
            "fold": entry["fold"],
            "city": entry["city"],
            "latitude": float(entry["latitude"]),
            "longitude": float(entry["longitude"]),
            "start_year": start_year,
            "end_year": end_year,
            "raw_dir": Path(f"openubem/data/weather/raw/era5_{entry['city'].lower()}_{start_year}_{end_year}"),
        })
    return targets


def _request(area: list[float], year: int, month: int, days: Iterable[int]) -> dict[str, object]:
    return {
        "product_type": "reanalysis",
        "variable": VARIABLES,
        "year": str(year),
        "month": f"{month:02d}",
        "day": [f"{day:02d}" for day in days],
        "time": [f"{hour:02d}:00" for hour in range(24)],
        "area": area,
        "data_format": "netcdf",
        "download_format": "unarchived",
    }


def _jobs(target: dict[str, object]) -> list[tuple[str, dict[str, object], Path]]:
    """Return the boundary day plus every month of the target's 24-month window."""
    area = _grid_area(target["latitude"], target["longitude"])
    raw_dir: Path = target["raw_dir"]
    start_year = int(target["start_year"])
    end_year = int(target["end_year"])
    city = str(target["city"]).lower()
    jobs = [
        (
            f"{start_year - 1}-12-31",
            _request(area, start_year - 1, 12, [31]),
            raw_dir / f"era5_{city}_{start_year - 1}-12-31.zip",
        )
    ]
    for year in (start_year, end_year):
        for month in range(1, 13):
            days = range(1, monthrange(year, month)[1] + 1)
            jobs.append((
                f"{year}-{month:02d}",
                _request(area, year, month, days),
                raw_dir / f"era5_{city}_{year}-{month:02d}.zip",
            ))
    return jobs


def _job_dir(target: dict[str, object]) -> Path:
    return target["raw_dir"] / "jobs"


def _job_path(target: dict[str, object], label: str) -> Path:
    return _job_dir(target) / f"{label}.json"


def _next_retry_path(target: dict[str, object], label: str) -> Path:
    """Keep a rejected CDS request as evidence and allocate a new retry manifest."""
    retry = 1
    while _job_path(target, f"{label}-retry{retry}").exists():
        retry += 1
    return _job_path(target, f"{label}-retry{retry}")


def _write_json(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _client() -> DatastoresClient:
    """Build the current CDS client from the configured cdsapi credentials."""
    url, key, verify = get_url_key_verify(None, None, None)
    return DatastoresClient(url=url, key=key, verify=verify, progress=False, cleanup=False)


def submit(target: dict[str, object], labels: set[str] | None = None) -> None:
    """Submit this target's missing CDS jobs without waiting for processing."""
    target["raw_dir"].mkdir(parents=True, exist_ok=True)
    client = _client()
    for label, request, dest in _jobs(target):
        if labels is not None and label not in labels:
            continue
        manifest = _job_path(target, label)
        if dest.is_file() and dest.stat().st_size:
            print(f"ACQUIRED {target['fold']} {label} {dest.stat().st_size}")
            continue
        related = sorted(_job_dir(target).glob(f"{label}*.json"))
        if related:
            statuses = {
                json.loads(path.read_text(encoding="utf-8")).get("reply", {}).get("status")
                for path in related
            }
            if statuses - {"rejected", "failed"}:
                print(f"ALREADY_SUBMITTED {target['fold']} {label}")
                continue
            manifest = _next_retry_path(target, label)
        result = client.submit(DATASET, request)
        _write_json(manifest, {
            "dataset": DATASET,
            "fold": target["fold"],
            "label": label,
            "submitted_at_utc": datetime.now(timezone.utc).isoformat(),
            "target": dest.as_posix(),
            "request": request,
            "reply": result.json,
        })
        print(f"SUBMITTED {target['fold']} {label} {result.request_id}")


def poll(target: dict[str, object]) -> None:
    """Update this target's submitted jobs and download exactly those CDS marks completed."""
    client = _client()
    for manifest in sorted(_job_dir(target).glob("*.json")):
        state = json.loads(manifest.read_text(encoding="utf-8"))
        dest = Path(state["target"])
        if dest.is_file() and dest.stat().st_size:
            print(f"ACQUIRED {target['fold']} {state['label']} {dest.stat().st_size}")
            continue
        request_id = state["reply"].get("request_id", state["reply"].get("jobID"))
        if not request_id:
            raise ValueError(f"CDS job manifest has no request ID: {manifest}")
        result = client.get_remote(request_id)
        reply = result.json
        reply["request_id"] = request_id
        state["reply"] = reply
        state["last_polled_at_utc"] = datetime.now(timezone.utc).isoformat()
        _write_json(manifest, state)
        status = reply.get("status", reply.get("state", "UNKNOWN"))
        if status != "successful":
            print(f"{status.upper()} {target['fold']} {state['label']}")
            continue
        try:
            result.download(str(dest))
        except PermissionError as exc:
            # A concurrent poll() in another process (or another invocation of
            # this script) can race on the same target file on Windows; the
            # loser must not crash the whole sequential loop -- the next poll
            # retries naturally since `dest` still will not exist for it.
            print(f"DOWNLOAD_RACE_SKIPPED {target['fold']} {state['label']} {exc}")
            continue
        print(f"ACQUIRED {target['fold']} {state['label']} {dest.stat().st_size}")


def archive_count(target: dict[str, object]) -> int:
    """Count archives actually present on disk for this fold (never a submitted-job count)."""
    return sum(1 for _label, _request_data, dest in _jobs(target) if dest.is_file() and dest.stat().st_size)


def submitted_count(target: dict[str, object]) -> int:
    """Count job manifests written for this fold, across original submissions and retries."""
    return len(list(_job_dir(target).glob("*.json")))


def report(targets: list[dict[str, object]] | None = None) -> None:
    for target in targets if targets is not None else _load_targets():
        print(
            f"FOLD {target['fold']} submitted={submitted_count(target)} "
            f"acquired={archive_count(target)}/{len(_jobs(target))}"
        )


def run_sequential(targets: list[dict[str, object]], interval: int = 20) -> None:
    """Acquire every missing job across all targets, one at a time, in fold order."""
    for target in targets:
        for label, _request_data, dest in _jobs(target):
            if dest.exists():
                continue
            submit(target, {label})
            while not dest.exists():
                poll(target)
                if not dest.exists():
                    time.sleep(interval)
            print(f"SEQUENTIAL_COMPLETE {target['fold']} {label}")


def main() -> None:
    parser = argparse.ArgumentParser()
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--submit", action="store_true")
    actions.add_argument("--poll", action="store_true")
    actions.add_argument("--run-sequential", action="store_true", help="acquire all missing jobs serially")
    parser.add_argument("--fold", action="append", help="restrict to this fold (es/uk/it); repeatable")
    parser.add_argument("--label", action="append", help="submit only this job label; repeatable")
    parser.add_argument("--interval", type=int, default=20)
    args = parser.parse_args()

    targets = _load_targets()
    if args.fold:
        targets = [target for target in targets if target["fold"] in set(args.fold)]

    if args.submit:
        for target in targets:
            submit(target, set(args.label) if args.label else None)
    elif args.poll:
        for target in targets:
            poll(target)
        report(targets)
    else:
        run_sequential(targets, max(5, args.interval))


if __name__ == "__main__":
    main()
