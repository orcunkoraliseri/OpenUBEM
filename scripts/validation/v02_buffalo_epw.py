"""V02: Buffalo, NY EPW resolution.

Resolve and cache the nearest EPW for Buffalo (42.94, -78.73; CZ 6A).
Write the resolved path to %TEMP%/ubem_validation/level2/epw_path.txt.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO))

from openubem.acquisition.epw_manager import fetch_epw, load_stations, resolve_station
from openubem import config

BUFFALO_LAT = 42.94
BUFFALO_LON = -78.73
OUT_BASE = Path(tempfile.gettempdir()) / "ubem_validation" / "level2"


def main() -> None:
    OUT_BASE.mkdir(parents=True, exist_ok=True)

    stations = load_stations()
    station, dist_km = resolve_station(BUFFALO_LAT, BUFFALO_LON, stations)
    print(f"[V02] Nearest station: {station['station_id']} '{station['name']}' ({station['state']})")
    print(f"[V02] Geodesic distance: {dist_km:.2f} km")

    epw_path = fetch_epw(
        station,
        cache_dir=config.EPW_CACHE_DIR,
        output_dir=OUT_BASE,
    )

    sz = epw_path.stat().st_size
    print(f"[V02] EPW resolved: {epw_path}")
    print(f"[V02] File size: {sz/1024:.0f} KB")

    if sz < 1_048_576:
        print(f"[V02] WARNING: EPW file smaller than 1 MB ({sz} bytes) — verify content.")

    with open(epw_path, encoding="utf-8", errors="replace") as fh:
        first_line = fh.readline()
    print(f"[V02] LOCATION header: {first_line.strip()}")

    parts = first_line.strip().split(",")
    loc_name = parts[1].strip() if len(parts) > 1 else ""
    print(f"[V02] Station name in header: '{loc_name}'")

    epw_txt_path = OUT_BASE / "epw_path.txt"
    epw_txt_path.write_text(str(epw_path))
    print(f"[V02] EPW path written to: {epw_txt_path}")
    print("[V02] DONE")


if __name__ == "__main__":
    main()
