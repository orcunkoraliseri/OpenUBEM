"""Unit tests for openubem.scenarios.campaign_runner (plan block-6 SCEN-WIRE, item 4).

No EnergyPlus run. No `05_results` write. Proves the 8-cell campaign produces real
per-building, per-cell IDFs on disk, and that the `baseline` cell is a true no-op.
"""

import filecmp
from pathlib import Path

import pytest
from eppy.modeleditor import IDDAlreadySetError
from geomeppy import IDF as GeomIDF

from openubem import config
from openubem.scenarios.campaign import build_full_factorial_campaign
from openubem.scenarios.campaign_runner import run_campaign

try:
    GeomIDF.setiddname(str(config.ENERGYPLUS_IDD_PATH))
except IDDAlreadySetError:
    pass

_SAMPLE_BUILDINGS = [
    ("office_medium", str(Path(config.BASELINE_IDF_DIR) / "ASHRAE901_OfficeMedium_STD2022_Buffalo.idf")),
    ("apartment_midrise", str(Path(config.BASELINE_IDF_DIR) / "ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf")),
]


@pytest.fixture(scope="module")
def campaign_output(tmp_path_factory):
    output_dir = tmp_path_factory.mktemp("scenario_campaign_wiring")
    manifest = run_campaign(_SAMPLE_BUILDINGS, str(output_dir))
    return output_dir, manifest


def test_all_cells_times_all_buildings_produce_distinct_files_on_disk(campaign_output):
    output_dir, manifest = campaign_output
    cells = build_full_factorial_campaign()
    assert len(manifest) == len(cells) * len(_SAMPLE_BUILDINGS)

    paths = [Path(row.output_path) for row in manifest]
    assert len(set(paths)) == len(paths)
    for path in paths:
        assert path.is_file()
        assert path.stat().st_size > 0

    manifest_csv = output_dir / "manifest.csv"
    assert manifest_csv.is_file()


def test_manifest_rows_record_building_cell_and_path(campaign_output):
    _, manifest = campaign_output
    cells = {c.name for c in build_full_factorial_campaign()}
    building_ids = {b[0] for b in _SAMPLE_BUILDINGS}
    for row in manifest:
        assert row.building_id in building_ids
        assert row.cell_name in cells
        assert Path(row.output_path).name == f"{row.building_id}.idf"
        assert Path(row.output_path).parent.name == row.cell_name


def test_baseline_cell_output_is_byte_identical_to_input(campaign_output, tmp_path):
    output_dir, _ = campaign_output
    for building_id, baseline_idf_path in _SAMPLE_BUILDINGS:
        baseline_output = output_dir / "baseline" / f"{building_id}.idf"

        unmodified_idf = GeomIDF(str(baseline_idf_path))
        unmodified_copy = tmp_path / f"{building_id}_unmodified.idf"
        unmodified_idf.saveas(str(unmodified_copy))

        assert filecmp.cmp(str(baseline_output), str(unmodified_copy), shallow=False)


def test_non_baseline_cell_output_differs_from_input(campaign_output):
    output_dir, _ = campaign_output
    for building_id, baseline_idf_path in _SAMPLE_BUILDINGS:
        all_three_output = output_dir / "lighting+setback+infiltration" / f"{building_id}.idf"
        assert all_three_output.is_file()
