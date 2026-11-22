import json
from pathlib import Path

import numpy as np

from openubem.gpusim.compile import SURF_FLOOR, compile_expidf_batch
from openubem.gpusim.subset import check_s0_subset

REPO_ROOT = Path(__file__).resolve().parents[2]
REP2_DIR = REPO_ROOT / "openubem/outputs/eu_certified_rerun_2026-08-28/rep2"
GOLDEN_ROOT = REPO_ROOT / "tests/fixtures/gpusim/golden"
BASE_CELL_ID = "it__IT.MidClim.SFH.02.Gen.ReEx.001.001__f100"

GOLDEN_CELL_IDS: tuple[str, ...] = (
    BASE_CELL_ID,
    "uk__GB.ENG.AB.03.Gen.ReEx.001.001__f000",
    "es__ES.ME.AB.01.Gen.ReEx.001.001__f000",
)


def _completed_fleet_ids() -> list[str]:
    """Return sorted cell IDs for all COMPLETED manifests in rep2.

    Returns:
        List of 346 completed cell identifiers.
    """
    ids: list[str] = []
    for mpath in sorted((REP2_DIR / "manifests").glob("*.json")):
        data = json.loads(mpath.read_text(encoding="utf-8"))
        if data.get("completion_status") == "COMPLETED":
            ids.append(str(data["cell_id"]))
    return ids


def _parse_eio_surface_details(
    eio_path: Path,
) -> tuple[
    dict[str, tuple[float, float, float, float]],
    dict[str, tuple[float, float, float]],
    tuple[float, float, float],
]:
    """Parse HeatTransfer Surface, Solar View Factor surface, and Zone centroid.

    Args:
        eio_path: Path to golden ``eplusout.eio``.

    Returns:
        Tuple of ``(ht_surfaces, svf_surfaces, zone_centroid_xyz)``.
    """
    ht_surfaces: dict[str, tuple[float, float, float, float]] = {}
    svf_surfaces: dict[str, tuple[float, float, float]] = {}
    zone_centroid = (0.0, 0.0, 0.0)
    for line in eio_path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if stripped.startswith("HeatTransfer Surface,"):
            parts = [p.strip() for p in stripped.split(",")]
            name = parts[1].upper()
            area_net = float(parts[9])
            area_gross = float(parts[10])
            az = float(parts[12])
            tilt = float(parts[13])
            ht_surfaces[name] = (area_net, area_gross, az, tilt)
        elif stripped.startswith("Solar View Factor - Surface Information,"):
            parts = [p.strip() for p in stripped.split(",")]
            name = parts[1].upper()
            area = float(parts[3])
            az = float(parts[4])
            tilt = float(parts[5])
            svf_surfaces[name] = (area, az, tilt)
        elif stripped.startswith("Zone Information,"):
            parts = [p.strip() for p in stripped.split(",")]
            zone_centroid = (float(parts[6]), float(parts[7]), float(parts[8]))
    return ht_surfaces, svf_surfaces, zone_centroid


def test_all_completed_fleet_expidf_pass_subset() -> None:
    """Verify all 346 completed rep2 .expidf files pass the S0 subset checker."""
    cell_ids = _completed_fleet_ids()
    assert len(cell_ids) == 346
    for cid in cell_ids:
        expidf = (REP2_DIR / cid / "eplusout.expidf").read_text(
            encoding="utf-8", errors="replace"
        )
        res = check_s0_subset(expidf)
        assert res.passed, f"{cid} rejected: {res.reason}"


def test_extra_people_object_fails_subset() -> None:
    """Verify an extra People object is rejected with a reason naming People."""
    expidf_path = GOLDEN_ROOT / BASE_CELL_ID / "eplusout.expidf"
    idf_text = expidf_path.read_text(encoding="utf-8", errors="replace")
    extra_people = (
        "\nPeople,\n"
        "  ExtraOccupants,\n"
        "  EU_Cell_Zone,\n"
        "  EU_AlwaysOn,\n"
        "  People,\n"
        "  2;\n"
    )
    res = check_s0_subset(idf_text + extra_people)
    assert not res.passed
    assert res.reason is not None
    assert "People" in res.reason


def test_v15_fails_and_v14_passes_subset() -> None:
    """Verify V15 fails subset check naming SunExposed and V14 passes."""
    v15_path = GOLDEN_ROOT / f"variants/{BASE_CELL_ID}__V15/eplusout.expidf"
    v14_path = GOLDEN_ROOT / f"variants/{BASE_CELL_ID}__V14/eplusout.expidf"

    res_v15 = check_s0_subset(v15_path.read_text(encoding="utf-8", errors="replace"))
    assert not res_v15.passed
    assert res_v15.reason is not None
    assert "SunExposed" in res_v15.reason

    res_v14 = check_s0_subset(v14_path.read_text(encoding="utf-8", errors="replace"))
    assert res_v14.passed, f"V14 rejected: {res_v14.reason}"


def test_golden_cells_geometry_matches_eio() -> None:
    """Verify compiled surface area, tilt, azimuth, and centroids match .eio."""
    expidf_paths = [GOLDEN_ROOT / cid / "eplusout.expidf" for cid in GOLDEN_CELL_IDS]
    batch = compile_expidf_batch(
        expidf_paths,
        cell_ids=list(GOLDEN_CELL_IDS),
        schedule_dirs=[REP2_DIR / "schedules"],
    )
    assert batch.batch_size == len(GOLDEN_CELL_IDS)

    for b_idx, cid in enumerate(GOLDEN_CELL_IDS):
        eio_path = GOLDEN_ROOT / cid / "eplusout.eio"
        ht_surfs, svf_surfs, eio_zcen = _parse_eio_surface_details(eio_path)

        active_indices = np.where(batch.surf_mask[b_idx])[0]
        assert len(active_indices) == len(ht_surfs)

        floor_seen = False
        for s_idx in active_indices:
            sname = batch.surf_names[b_idx][s_idx]
            assert sname in ht_surfs
            assert sname in svf_surfs

            eio_net, eio_gross, eio_az_ht, eio_tilt_ht = ht_surfs[sname]
            svf_area, svf_az, svf_tilt = svf_surfs[sname]

            assert abs(batch.surf_area[b_idx, s_idx] - svf_area) <= max(
                1.0e-4 * svf_area, 5.1e-5
            )
            assert abs(batch.surf_area[b_idx, s_idx] - eio_net) <= 0.0051
            assert abs(batch.surf_gross_area[b_idx, s_idx] - eio_gross) <= 0.0051
            assert abs(batch.surf_azimuth_deg[b_idx, s_idx] - svf_az) <= 1.0e-4
            assert abs(batch.surf_tilt_deg[b_idx, s_idx] - svf_tilt) <= 1.0e-4
            assert abs(batch.surf_azimuth_deg[b_idx, s_idx] - eio_az_ht) <= 0.0051
            assert abs(batch.surf_tilt_deg[b_idx, s_idx] - eio_tilt_ht) <= 0.0051

            if batch.surf_class[b_idx, s_idx] == SURF_FLOOR:
                floor_seen = True
                assert abs(batch.surf_tilt_deg[b_idx, s_idx] - 180.0) <= 1.0e-6

        assert floor_seen
        for axis in range(3):
            assert abs(batch.zone_centroid_xyz[b_idx, axis] - eio_zcen[axis]) <= 0.0051
