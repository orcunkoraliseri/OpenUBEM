import os
import tempfile
from pathlib import Path

from eppy.iddcurrent import iddcurrent as _iddcurrent


def _resolve_idd_path() -> Path:
    env_val = os.environ.get("OPENUBEM_ENERGYPLUS_IDD_PATH")
    if env_val:
        return Path(env_val)
    # geomeppy.utilities.IDD_PATH does not exist in geomeppy >= 0.12; fall back
    # to eppy's bundled IDD text written to a stable temp file.
    tmp = Path(tempfile.gettempdir()) / "openubem_eppy_bundled.idd"
    if not tmp.exists():
        tmp.write_text(_iddcurrent.iddtxt, encoding="utf-8")
    return tmp


ENERGYPLUS_IDD_PATH: Path = _resolve_idd_path()

SHADING_SPHERE_RADIUS: float = 30.0
DP_TOLERANCE_M: float = 0.5
DP_COARSE_TOLERANCE_M: float = 1.5
MAX_VERTICES: int = 120
FLOOR_TO_FLOOR_M: float = 3.5
PERIMETER_DEPTH_M: float = 4.57
