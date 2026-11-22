from dataclasses import dataclass
from pathlib import Path

import numpy as np

DEFAULT_GOLDEN_EIO = (
    Path(__file__).resolve().parents[2]
    / "tests/fixtures/gpusim/golden"
    / "it__IT.MidClim.SFH.02.Gen.ReEx.001.001__f100/eplusout.eio"
)


@dataclass(frozen=True)
class CtfCoefficients:
    """Conduction transfer function coefficients for one construction.

    Attributes:
        construction_name: Uppercase construction name from ``eplusout.eio``.
        num_terms: Maximum history index ``M`` (coefficients indexed ``0..M``).
        time_step_hours: CTF time step in hours reported in ``eplusout.eio``.
        thermal_conductance: Steady thermal conductance ``U`` in W/m2-K.
        outside: Outside CTF coefficients ``X[0..M]`` in W/m2-K.
        cross: Cross CTF coefficients ``Y[0..M]`` in W/m2-K.
        inside: Inside CTF coefficients ``Z[0..M]`` in W/m2-K.
        flux: Flux history coefficients ``Phi[1..M]`` (dimensionless, length ``M``).
    """

    construction_name: str
    num_terms: int
    time_step_hours: float
    thermal_conductance: float
    outside: np.ndarray
    cross: np.ndarray
    inside: np.ndarray
    flux: np.ndarray


def load_ctf_from_eio(
    eio_path: Path = DEFAULT_GOLDEN_EIO,
    construction_name: str = "EU_INTERNALMASS_CONSTRUCTION",
    steps_per_hour: int = 12,
) -> CtfCoefficients:
    """ConductionTransferFunctionCalc.cc::ReportCTFs"""
    target = construction_name.strip().upper()
    lines = eio_path.read_text(encoding="utf-8", errors="replace").splitlines()

    header_idx: int | None = None
    num_terms = 0
    ts_hours = 0.0
    conductance = 0.0
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("Construction CTF,"):
            continue
        parts = [p.strip() for p in stripped.split(",")]
        if parts[1].upper() == target:
            header_idx = idx
            num_terms = int(parts[4])
            ts_hours = float(parts[5])
            conductance = float(parts[6])
            break

    if header_idx is None:
        raise ValueError(f"{eio_path}: Construction CTF '{target}' not found")

    expected_ts_hours = 1.0 / float(steps_per_hour)
    if abs(ts_hours - expected_ts_hours) > 1.0e-3:
        raise ValueError(
            f"CTF timestep {ts_hours} h != zone timestep {expected_ts_hours:.6f} h "
            f"(S2a scope required)"
        )

    outside = np.zeros(num_terms + 1, dtype=np.float64)
    cross = np.zeros(num_terms + 1, dtype=np.float64)
    inside = np.zeros(num_terms + 1, dtype=np.float64)
    flux = np.zeros(num_terms, dtype=np.float64)
    seen_indices: set[int] = set()

    for line in lines[header_idx + 1 :]:
        stripped = line.strip()
        if stripped.startswith("Construction CTF,") or stripped.startswith("!"):
            break
        if not stripped.startswith("CTF,"):
            continue
        parts = [p.strip() for p in stripped.split(",")]
        k = int(parts[1])
        outside[k] = float(parts[2])
        cross[k] = float(parts[3])
        inside[k] = float(parts[4])
        if k >= 1:
            flux[k - 1] = float(parts[5])
        seen_indices.add(k)

    expected_indices = set(range(num_terms + 1))
    if seen_indices != expected_indices:
        raise ValueError(
            f"{eio_path}: incomplete CTF terms for '{target}': "
            f"got {sorted(seen_indices)}, expected {sorted(expected_indices)}"
        )

    return CtfCoefficients(
        construction_name=target,
        num_terms=num_terms,
        time_step_hours=ts_hours,
        thermal_conductance=conductance,
        outside=outside,
        cross=cross,
        inside=inside,
        flux=flux,
    )
