import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from openubem.gpusim.weather import load_epw_weather

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLDEN_ROOT = REPO_ROOT / "tests/fixtures/gpusim/golden"
WEATHER_DIR = REPO_ROOT / "openubem/data/weather"
BASE_CELL_ID = "it__IT.MidClim.SFH.02.Gen.ReEx.001.001__f100"

WEATHER_CASES: tuple[str, ...] = (
    BASE_CELL_ID,
    "uk__GB.ENG.AB.03.Gen.ReEx.001.001__f000",
    "es__ES.ME.AB.01.Gen.ReEx.001.001__f000",
    f"variants/{BASE_CELL_ID}__V10",
    f"variants/{BASE_CELL_ID}__V11",
)

COLUMN_SPECS: tuple[tuple[str, str, float], ...] = (
    (
        "Environment:Site Outdoor Air Drybulb Temperature [C](TimeStep)",
        "dry_bulb",
        1.0e-3,
    ),
    (
        "Environment:Site Outdoor Air Humidity Ratio [kgWater/kgDryAir](TimeStep)",
        "hum_rat",
        1.0e-6,
    ),
    (
        "Environment:Site Outdoor Air Barometric Pressure [Pa](TimeStep)",
        "baro_press",
        1.0,
    ),
    (
        "Environment:Site Sky Temperature [C](TimeStep)",
        "sky_temp",
        1.0e-3,
    ),
    (
        "Environment:Site Horizontal Infrared Radiation Rate per Area [W/m2](TimeStep)",
        "horiz_ir",
        1.0e-2,
    ),
)


@pytest.mark.parametrize("rel_path", WEATHER_CASES)
def test_epw_weather_matches_golden(rel_path: str) -> None:
    """Verify interpolated EPW weather matches E+ timestep Parquet outputs.

    Args:
        rel_path: Golden cell or climate-variant fixture relative path.
    """
    fixture_dir = GOLDEN_ROOT / rel_path
    meta = json.loads((fixture_dir / "meta.json").read_text(encoding="utf-8"))
    epw_path = WEATHER_DIR / str(meta["epw_file_name"])
    weather = load_epw_weather(epw_path, steps_per_hour=12)

    assert weather.dry_bulb.shape == (105_120,)
    assert weather.warmup_dry_bulb.shape == (288,)
    assert np.array_equal(weather.warmup_dry_bulb, weather.dry_bulb[:288])

    cols = [spec[0] for spec in COLUMN_SPECS]
    df = pd.read_parquet(fixture_dir / "timestep.parquet", columns=cols)
    assert len(df) == 105_120

    for col_name, attr_name, tol in COLUMN_SPECS:
        expected = df[col_name].to_numpy(dtype=np.float64)
        actual = getattr(weather, attr_name)
        max_abs = float(np.max(np.abs(actual - expected)))
        assert max_abs <= tol, f"{rel_path} {attr_name}: max_abs={max_abs} > {tol}"
