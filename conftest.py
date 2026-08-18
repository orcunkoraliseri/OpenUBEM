import os
from pathlib import Path

_TEMPROOT = Path(__file__).resolve().parent / ".pytest_tmp"
_TEMPROOT.mkdir(exist_ok=True)
os.environ["PYTEST_DEBUG_TEMPROOT"] = str(_TEMPROOT)
