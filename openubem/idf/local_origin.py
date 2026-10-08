from __future__ import annotations

import math
import re
from io import StringIO
from pathlib import Path

COORD_CLASSES = (
    "BUILDINGSURFACE:DETAILED",
    "FENESTRATIONSURFACE:DETAILED",
    "SHADING:SITE:DETAILED",
    "SHADING:BUILDING:DETAILED",
)
_X = re.compile(r"^Vertex_\d+_Xcoordinate$")
_Y = re.compile(r"^Vertex_\d+_Ycoordinate$")
_LINE = re.compile(r"^\s*([-+0-9.eE]+)\s*[,;]\s*!- Vertex \d+ ([XY])coordinate")


def _load(idf_text_or_obj):
    if not isinstance(idf_text_or_obj, str):
        return idf_text_or_obj
    from eppy.modeleditor import IDDAlreadySetError
    from geomeppy import IDF

    from scripts.run_eu_s2_campaign import ENERGYPLUS_IDD_PATH

    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass
    return IDF(StringIO(idf_text_or_obj))


def _number(value):
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def shift_to_local_origin(idf_text_or_obj, dx: float, dy: float):
    idf = _load(idf_text_or_obj)
    for zone in idf.idfobjects["ZONE"]:
        for field in ("X_Origin", "Y_Origin"):
            value = _number(getattr(zone, field, 0))
            if value:
                raise ValueError(f"ZONE {zone.Name} has non-zero {field} {value}")
    for kind in COORD_CLASSES:
        for obj in idf.idfobjects[kind]:
            for i, name in enumerate(obj.fieldnames[: len(obj.obj)]):
                if _X.match(name):
                    delta = dx
                elif _Y.match(name):
                    delta = dy
                else:
                    continue
                value = _number(obj.obj[i])
                if value is not None:
                    obj.obj[i] = value - delta
    return idf


def scan_min_xy(path: Path) -> tuple[float, float]:
    min_x = math.inf
    min_y = math.inf
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            m = _LINE.match(line)
            if m is None:
                continue
            v = float(m.group(1))
            if m.group(2) == "X":
                min_x = min(min_x, v)
            else:
                min_y = min(min_y, v)
    return min_x, min_y


def offset_from_min(min_x: float, min_y: float) -> tuple[float, float]:
    return math.floor(min_x / 1000.0) * 1000.0, math.floor(min_y / 1000.0) * 1000.0
