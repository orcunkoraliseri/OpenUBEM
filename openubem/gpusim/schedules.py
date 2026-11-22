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
