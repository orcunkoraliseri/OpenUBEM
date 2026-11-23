from pathlib import Path, PureWindowsPath

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]


def resolve_schedule_path(
    raw_path: str, search_dirs: list[Path] | None = None
) -> Path:
    """Resolve an IDF Schedule:File path to a local filesystem path.

    Args:
        raw_path: Path string from the IDF (Windows path or bare filename).
        search_dirs: Optional ordered list of directories to search for basenames.

    Returns:
        Existing ``Path`` to the schedule CSV file.

    Raises:
        FileNotFoundError: If no matching file can be found.
    """
    direct = Path(raw_path)
    if direct.is_file():
        return direct

    marker = "openubem\\"
    lower = raw_path.casefold()
    idx = lower.find(marker)
    if idx >= 0:
        rel_win = raw_path[idx + len(marker) :]
        candidate = REPO_ROOT.joinpath(*PureWindowsPath(rel_win).parts)
        if candidate.is_file():
            return candidate

    basename = PureWindowsPath(raw_path).name
    for directory in search_dirs or []:
        candidate = directory / basename
        if candidate.is_file():
            return candidate

    raise FileNotFoundError(f"Could not locate Schedule:File '{raw_path}'")


def load_schedule_file_hourly(
    csv_path: Path,
    column_number: int = 1,
    rows_to_skip: int = 0,
    num_hours: int = 8760,
    delimiter: str = ",",
) -> np.ndarray:
    """ScheduleManager.cc::ProcessScheduleInput"""
    lines = csv_path.read_text(encoding="utf-8", errors="replace").splitlines()
    data_lines = lines[rows_to_skip:]
    col_idx = column_number - 1
    values: list[float] = []
    for line in data_lines:
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split(delimiter)
        values.append(float(parts[col_idx].strip()))
        if len(values) == num_hours:
            break
    if len(values) != num_hours:
        raise ValueError(
            f"{csv_path}: expected {num_hours} hourly schedule entries, "
            f"got {len(values)}"
        )
    return np.asarray(values, dtype=np.float64)


def expand_hourly_to_timestep(
    hourly: np.ndarray, steps_per_hour: int = 12
) -> np.ndarray:
    """ScheduleManager.cc::UpdateScheduleValues"""
    return np.repeat(hourly, steps_per_hour).astype(np.float64, copy=False)


_MONTH_DAYS: tuple[int, ...] = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MONTH_START_DOY: tuple[int, ...] = (0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334)
_DOW_NAMES: dict[str, int] = {
    "sunday": 0,
    "monday": 1,
    "tuesday": 2,
    "wednesday": 3,
    "thursday": 4,
    "friday": 5,
    "saturday": 6,
}


def _parse_md_to_doy(md: str) -> int:
    """Convert 'MM/DD' to 0-based day-of-year (0..364)."""
    m_s, d_s = md.strip().split("/")
    m = max(1, min(12, int(m_s)))
    d = max(1, min(_MONTH_DAYS[m - 1], int(d_s)))
    return _MONTH_START_DOY[m - 1] + (d - 1)


def _match_day_types(for_clause: str, dow: int) -> bool:
    """Check if EnergyPlus 'For:' clause matches day-of-week (0=Sun..6=Sat)."""
    tokens = [t.strip().casefold() for t in for_clause.split()]
    if any(t in ("alldays", "allotherdays") for t in tokens):
        return True
    if "weekdays" in tokens and 1 <= dow <= 5:
        return True
    if "weekends" in tokens and dow in (0, 6):
        return True
    for name, idx in _DOW_NAMES.items():
        if name in tokens and dow == idx:
            return True
    return False


def compile_schedule_compact_hourly(
    fields: list[str],
    start_day_of_week: int = 0,
) -> np.ndarray:
    """Compile an EnergyPlus ``Schedule:Compact`` into an 8,760-hour float64 array.

    Args:
        fields: Fields of ``Schedule:Compact`` (starting at field 0 = Name).
        start_day_of_week: Day-of-week of Jan 1 (0=Sunday .. 6=Saturday).

    Returns:
        NumPy array of shape ``(8760,)`` in float64.
    """
    out = np.zeros((365, 24), dtype=np.float64)
    filled = np.zeros((365, 24), dtype=bool)

    idx = 2
    n = len(fields)
    doy_start = 0
    while idx < n:
        tok = fields[idx].strip()
        low = tok.casefold()
        if low.startswith("through:"):
            doy_end = _parse_md_to_doy(tok.split(":", 1)[1])
            idx += 1
            while idx < n and not fields[idx].strip().casefold().startswith("through:"):
                sub = fields[idx].strip()
                if sub.casefold().startswith("for:"):
                    for_str = sub.split(":", 1)[1]
                    is_other = "allotherdays" in for_str.casefold()
                    idx += 1
                    day_vals = np.zeros(24, dtype=np.float64)
                    hr_prev = 0
                    while idx < n:
                        nxt = fields[idx].strip()
                        nlow = nxt.casefold()
                        if nlow.startswith("through:") or nlow.startswith("for:"):
                            break
                        if nlow.startswith("interpolate:"):
                            idx += 1
                            continue
                        if nlow.startswith("until:"):
                            time_str = nxt.split(":", 1)[1].strip()
                            hh, mm = time_str.split(":")
                            hr_end = int(hh) + (1 if int(mm) > 0 else 0)
                            hr_end = max(hr_prev, min(24, hr_end))
                            val = float(fields[idx + 1].strip())
                            day_vals[hr_prev:hr_end] = val
                            hr_prev = hr_end
                            idx += 2
                        else:
                            idx += 1
                    for d in range(doy_start, doy_end + 1):
                        dow = (start_day_of_week + d) % 7
                        if is_other:
                            if not np.all(filled[d]):
                                out[d] = day_vals
                                filled[d] = True
                        elif _match_day_types(for_str, dow):
                            out[d] = day_vals
                            filled[d] = True
                else:
                    idx += 1
            doy_start = doy_end + 1
        else:
            idx += 1
    return out.reshape(8760)
