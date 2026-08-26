"""Submit and poll the direct-ERA5 Lyon--Bron 2023 acquisition.

The reference location is Lyon--Bron WMO 07480 (45.72 N, 4.95 E).  ERA5 is a
gridded reanalysis, so the request uses the smallest non-zero crop that returns
the nearest grid point; the returned coordinate is preserved by the converter.
The target local-standard year is 2023 (CET, UTC+1, no DST).  2022-12-31 is
retrieved only as the UTC boundary day required to form the first CET hour.

Use ``--submit`` once, then rerun ``--poll`` until all files are downloaded.
No credential is accepted as an argument: cdsapi reads the user's configured
CDS credentials itself.
"""
from __future__ import annotations

import argparse
from calendar import monthrange
from datetime import datetime, timezone
import json
import time
from pathlib import Path
from typing import Iterable

from cdsapi.api import get_url_key_verify
from ecmwf.datastores.client import Client as DatastoresClient


DATASET = "reanalysis-era5-single-levels"
RAW_DIR = Path("openubem/data/weather/raw/era5_lyon_bron_2023")
JOB_DIR = RAW_DIR / "jobs"
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
AREA = [45.80, 4.90, 45.70, 5.00]  # north, west, south, east; yields one ERA5 grid point.


def _request(year: int, month: int, days: Iterable[int]) -> dict[str, object]:
    return {
        "product_type": "reanalysis",
        "variable": VARIABLES,
        "year": str(year),
        "month": f"{month:02d}",
        "day": [f"{day:02d}" for day in days],
        "time": [f"{hour:02d}:00" for hour in range(24)],
        "area": AREA,
        "data_format": "netcdf",
        "download_format": "unarchived",
    }


def _jobs() -> list[tuple[str, dict[str, object], Path]]:
    jobs = [("2022-12-31", _request(2022, 12, [31]), RAW_DIR / "era5_lyon_bron_2022-12-31.zip")]
    for month in range(1, 13):
        days = range(1, monthrange(2023, month)[1] + 1)
        jobs.append((f"2023-{month:02d}", _request(2023, month, days), RAW_DIR / f"era5_lyon_bron_2023-{month:02d}.zip"))
    return jobs


def _job_path(label: str) -> Path:
    return JOB_DIR / f"{label}.json"


def _next_retry_path(label: str) -> Path:
    """Keep a rejected CDS request as evidence and allocate a new retry manifest."""
    retry = 1
    while _job_path(f"{label}-retry{retry}").exists():
        retry += 1
    return _job_path(f"{label}-retry{retry}")


def _write_json(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _client() -> DatastoresClient:
    """Build the current CDS client from the configured cdsapi credentials."""
    url, key, verify = get_url_key_verify(None, None, None)
    return DatastoresClient(url=url, key=key, verify=verify, progress=False, cleanup=False)


def submit(labels: set[str] | None = None) -> None:
    """Submit missing CDS jobs without waiting for processing or downloading."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    client = _client()
    for label, request, target in _jobs():
        if labels is not None and label not in labels:
            continue
        manifest = _job_path(label)
        if target.is_file() and target.stat().st_size:
            print(f"ACQUIRED {label} {target.stat().st_size}")
            continue
        related = sorted(JOB_DIR.glob(f"{label}*.json"))
        if related:
            statuses = {
                json.loads(path.read_text(encoding="utf-8")).get("reply", {}).get("status")
                for path in related
            }
            if statuses - {"rejected", "failed"}:
                print(f"ALREADY_SUBMITTED {label}")
                continue
            manifest = _next_retry_path(label)
        result = client.submit(DATASET, request)
        _write_json(manifest, {
            "dataset": DATASET,
            "label": label,
            "submitted_at_utc": datetime.now(timezone.utc).isoformat(),
            "target": target.as_posix(),
            "request": request,
            "reply": result.json,
        })
        print(f"SUBMITTED {label} {result.request_id}")


def poll() -> None:
    """Update submitted jobs and download exactly those CDS marks completed."""
    client = _client()
    for manifest in sorted(JOB_DIR.glob("*.json")):
        state = json.loads(manifest.read_text(encoding="utf-8"))
        target = Path(state["target"])
        if target.is_file() and target.stat().st_size:
            print(f"ACQUIRED {state['label']} {target.stat().st_size}")
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
            print(f"{status.upper()} {state['label']}")
            continue
        result.download(str(target))
        print(f"ACQUIRED {state['label']} {target.stat().st_size}")


def run_sequential(interval: int = 20) -> None:
    """Acquire missing jobs one at a time, polling until each is downloaded."""
    for label, _request_data, target in _jobs():
        if target.exists():
            continue
        submit({label})
        while not target.exists():
            poll()
            if not target.exists():
                time.sleep(interval)
        print(f"SEQUENTIAL_COMPLETE {label}")


def main() -> None:
    parser = argparse.ArgumentParser()
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--submit", action="store_true")
    actions.add_argument("--poll", action="store_true")
    actions.add_argument("--run-sequential", action="store_true", help="acquire all missing jobs serially")
    parser.add_argument("--label", action="append", help="submit only this job label; repeatable")
    parser.add_argument("--interval", type=int, default=20)
    args = parser.parse_args()
    if args.submit:
        submit(set(args.label) if args.label else None)
    elif args.poll:
        poll()
    else:
        run_sequential(max(5, args.interval))


if __name__ == "__main__":
    main()
