from pathlib import Path

import numpy as np

from openubem.gpusim.compile import compile_expidf_batch
from openubem.gpusim.ctf import load_ctf_from_eio
from openubem.gpusim.viewfactors import compute_batch_view_factors

REPO_ROOT = Path(__file__).resolve().parents[2]
REP2_DIR = REPO_ROOT / "openubem/outputs/eu_certified_rerun_2026-08-28/rep2"
GOLDEN_ROOT = REPO_ROOT / "tests/fixtures/gpusim/golden"

GOLDEN_CELL_IDS: tuple[str, ...] = (
    "it__IT.MidClim.SFH.02.Gen.ReEx.001.001__f100",
    "uk__GB.ENG.AB.03.Gen.ReEx.001.001__f000",
    "es__ES.ME.AB.01.Gen.ReEx.001.001__f000",
)


def _half_last_digit(token: str) -> float:
    """Return half a unit of the last decimal digit printed in a numeric token.

    Args:
        token: Raw numeric string parsed from ``eplusout.eio``.

    Returns:
        Half of one ULP in the printed decimal representation (plus tiny slack).
    """
    clean = token.strip().lower()
    if "e" in clean:
        mantissa, exp_str = clean.split("e", 1)
        exp = int(exp_str)
    else:
        mantissa, exp = clean, 0
    if "." in mantissa:
        frac_digits = len(mantissa.split(".", 1)[1])
    else:
        frac_digits = 0
    return 0.5 * (10.0 ** (exp - frac_digits)) + 1.0e-12


def _parse_eio_vf_and_scriptf(
    eio_path: Path,
) -> tuple[list[str], np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Parse Final ViewFactors and Script F Factors matrices from ``eplusout.eio``.

    Args:
        eio_path: Path to golden ``eplusout.eio``.

    Returns:
        Tuple ``(surface_names, f_mat, sf_mat, f_tol, sf_tol)``.
    """
    lines = eio_path.read_text(encoding="utf-8", errors="replace").splitlines()

    vf_names: list[str] = []
    vf_rows: dict[str, list[float]] = {}
    vf_tols: dict[str, list[float]] = {}
    sf_names: list[str] = []
    sf_rows: dict[str, list[float]] = {}
    sf_tols: dict[str, list[float]] = {}

    mode = ""
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("Final ViewFactors,"):
            parts = [p.strip() for p in stripped.split(",")]
            vf_names = [name.upper() for name in parts[4:]]
            mode = "vf"
            continue
        if stripped.startswith("Script F Factors,"):
            parts = [p.strip() for p in stripped.split(",")]
            sf_names = [name.upper() for name in parts[2:]]
            mode = "sf"
            continue
        if mode == "vf" and stripped.startswith("View Factor,"):
            parts = [p.strip() for p in stripped.split(",")]
            key = parts[1].upper()
            vf_rows[key] = [float(x) for x in parts[4:]]
            vf_tols[key] = [_half_last_digit(x) for x in parts[4:]]
        elif mode == "sf" and stripped.startswith("Script F Factor,"):
            parts = [p.strip() for p in stripped.split(",")]
            key = parts[1].upper()
            sf_rows[key] = [float(x) for x in parts[2:]]
            sf_tols[key] = [_half_last_digit(x) for x in parts[2:]]
        elif mode and not stripped.startswith(("View Factor,", "Script F Factor,")):
            mode = ""

    assert vf_names == sf_names
    n_surf = len(vf_names)
    f_mat = np.zeros((n_surf, n_surf), dtype=np.float64)
    sf_mat = np.zeros((n_surf, n_surf), dtype=np.float64)
    f_tol = np.zeros((n_surf, n_surf), dtype=np.float64)
    sf_tol = np.zeros((n_surf, n_surf), dtype=np.float64)
    for i, name in enumerate(vf_names):
        f_mat[i, :] = vf_rows[name]
        sf_mat[i, :] = sf_rows[name]
        f_tol[i, :] = vf_tols[name]
        sf_tol[i, :] = sf_tols[name]
    return vf_names, f_mat, sf_mat, f_tol, sf_tol


def test_view_factors_and_scriptf_match_eio() -> None:
    """Verify Final ViewFactors and ScriptF match golden .eio for all 3 cells."""
    paths = [GOLDEN_ROOT / cid / "eplusout.expidf" for cid in GOLDEN_CELL_IDS]
    batch = compile_expidf_batch(
        paths,
        cell_ids=list(GOLDEN_CELL_IDS),
        schedule_dirs=[REP2_DIR / "schedules"],
    )
    f_batch, sf_batch = compute_batch_view_factors(batch)

    for b_idx, cid in enumerate(GOLDEN_CELL_IDS):
        eio_names, eio_f, eio_sf, f_tol, sf_tol = _parse_eio_vf_and_scriptf(
            GOLDEN_ROOT / cid / "eplusout.eio"
        )
        n_surf = int(np.sum(batch.surf_mask[b_idx]))
        assert n_surf == len(eio_names)
        comp_names = batch.surf_names[b_idx][:n_surf]
        perm = [comp_names.index(name) for name in eio_names]

        comp_f = f_batch[b_idx, :n_surf, :n_surf][np.ix_(perm, perm)]
        comp_sf = sf_batch[b_idx, :n_surf, :n_surf][np.ix_(perm, perm)]

        f_diff = np.abs(comp_f - eio_f)
        sf_diff = np.abs(comp_sf - eio_sf)
        assert np.all(f_diff <= f_tol), f"{cid} F exceeded print precision"
        assert np.all(sf_diff <= sf_tol), f"{cid} ScriptF exceeded print precision"
        assert float(np.max(f_diff)) <= 5.0e-5, f"{cid} F max={np.max(f_diff)}"
        assert float(np.max(sf_diff)) <= 5.0e-5, f"{cid} SF max={np.max(sf_diff)}"


def test_internal_mass_ctf_properties() -> None:
    """Verify internal-mass CTF sums and steady conductance match k/L = 10."""
    for cid in GOLDEN_CELL_IDS:
        ctf = load_ctf_from_eio(GOLDEN_ROOT / cid / "eplusout.eio")
        sum_out = float(np.sum(ctf.outside))
        sum_cross = float(np.sum(ctf.cross))
        sum_in = float(np.sum(ctf.inside))
        denom = 1.0 - float(np.sum(ctf.flux))

        assert abs(sum_out - sum_in) <= 1.0e-5
        assert abs(sum_out - sum_cross) <= 1.0e-5
        assert abs(sum_in - sum_cross) <= 1.0e-5

        u_steady = sum_in / denom
        assert abs(u_steady - 10.0) / 10.0 <= 1.0e-3
