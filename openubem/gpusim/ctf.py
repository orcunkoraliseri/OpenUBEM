from dataclasses import dataclass
import math
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class LayerSpec:
    """One opaque construction layer ordered outside -> inside.

    Either a massive ``Material`` (``thickness > 0, conductivity > 0, density > 0, specific_heat > 0``)
    or a massless ``Material:NoMass`` / air-gap layer (``r_value > 0, is_nomass=True``).
    """

    name: str
    is_nomass: bool
    r_value: float
    thickness: float = 0.0
    conductivity: float = 0.0
    density: float = 0.0
    specific_heat: float = 0.0


@dataclass(frozen=True)
class ModalConductionModel:
    """Exact diagonal modal state-space conduction model (float32-safe for thick walls).

    For piecewise-linear boundary temperatures ``u = [T_out, T_in]`` over ``dt``:
      ``z_free = decay * z_prev + g_old_out * T_out_prev + g_old_in * T_in_prev``
      ``const_out = sum(c_out * z_free) + lag_oo * T_out_prev + lag_oi * T_in_prev``
      ``const_in  = sum(c_in  * z_free) + lag_io * T_out_prev + lag_ii * T_in_prev``
      ``q_out = ctf_out0 * T_out - ctf_cross0 * T_in + const_out``
      ``q_in  = ctf_cross0 * T_out - ctf_in0 * T_in + const_in``
      ``z_new = z_free + g_new_out * T_out + g_new_in * T_in``
    """

    construction_name: str
    num_modes: int
    dt_sec: float
    u_steady: float
    ctf_out0: float
    ctf_cross0: float
    ctf_in0: float
    decay: np.ndarray        # [K] exp(-lam_k * dt) in (0, 1)
    g_new_out: np.ndarray    # [K]
    g_new_in: np.ndarray     # [K]
    g_old_out: np.ndarray    # [K]
    g_old_in: np.ndarray     # [K]
    c_out: np.ndarray        # [K]
    c_in: np.ndarray         # [K]
    steady_out: np.ndarray   # [K] B_m[:, 0] / lam_k for steady initialization
    steady_in: np.ndarray    # [K] B_m[:, 1] / lam_k for steady initialization
    lag_oo: float = 0.0      # folded fast-mode 1-step lag terms
    lag_oi: float = 0.0
    lag_io: float = 0.0
    lag_ii: float = 0.0


def build_modal_conduction(
    layers: list[LayerSpec],
    dt_sec: float,
    construction_name: str = "",
    max_modes: int = 12,
    nodes_per_layer_min: int = 4,
    nodes_per_layer_max: int = 14,
) -> ModalConductionModel:
    """Build an exact diagonal modal state-space conduction model from layers."""
    if not layers:
        raise ValueError(f"Construction '{construction_name}' has no layers")

    total_r = sum(
        (ly.r_value if ly.is_nomass else ly.thickness / ly.conductivity)
        for ly in layers
    )
    u_steady = 1.0 / max(total_r, 1.0e-12)
    has_mass = any(
        (not ly.is_nomass) and (ly.density * ly.specific_heat * ly.thickness > 0.0)
        for ly in layers
    )
    if not has_mass:
        empty = np.zeros(0, dtype=np.float64)
        return ModalConductionModel(
            construction_name=construction_name,
            num_modes=0,
            dt_sec=dt_sec,
            u_steady=u_steady,
            ctf_out0=u_steady,
            ctf_cross0=u_steady,
            ctf_in0=u_steady,
            decay=empty,
            g_new_out=empty,
            g_new_in=empty,
            g_old_out=empty,
            g_old_in=empty,
            c_out=empty,
            c_in=empty,
            steady_out=empty,
            steady_in=empty,
        )

    # Allocate FD sub-nodes across massive layers so total nodes <= max_modes (ZERO truncated modes!)
    massive_indices = [
        idx for idx, ly in enumerate(layers)
        if (not ly.is_nomass) and (ly.density * ly.specific_heat * ly.thickness > 0.0)
    ]
    n_mass = len(massive_indices)
    raw_counts: dict[int, int] = {}
    for idx in massive_indices:
        ly = layers[idx]
        r_ly = ly.thickness / ly.conductivity
        c_ly = ly.density * ly.specific_heat * ly.thickness
        n_sub = int(math.ceil(1.5 * math.sqrt(max(r_ly * c_ly / max(dt_sec, 60.0), 1.0))))
        raw_counts[idx] = max(2, min(max_modes, n_sub))

    # Scale down proportionally if total nodes exceeds max_modes, keeping >= 1 per massive layer
    while sum(raw_counts.values()) > max_modes:
        # Decrement the layer with the largest node count (> 1)
        cand = max((idx for idx in massive_indices if raw_counts[idx] > 1), key=lambda i: raw_counts[i])
        raw_counts[cand] -= 1

    # Discretize massive layers into RC nodes and accumulate inter-node resistances.
    node_caps: list[float] = []
    # r_between[i] holds resistance between node i-1 and node i (i=0 is outside->node 0, i=N is node N-1->inside)
    r_between: list[float] = [0.0]

    for idx, ly in enumerate(layers):
        if idx not in raw_counts:
            r_between[-1] += ly.r_value if ly.is_nomass else (ly.thickness / ly.conductivity)
            continue
        r_ly = ly.thickness / ly.conductivity
        c_ly = ly.density * ly.specific_heat * ly.thickness
        n_sub = raw_counts[idx]
        r_sub = r_ly / float(n_sub)
        c_sub = c_ly / float(n_sub)
        for _ in range(n_sub):
            r_between[-1] += 0.5 * r_sub
            node_caps.append(c_sub)
            r_between.append(0.5 * r_sub)

    n_nodes = len(node_caps)
    caps = np.asarray(node_caps, dtype=np.float64)
    r_arr = np.asarray(r_between, dtype=np.float64)
    g_arr = 1.0 / np.maximum(r_arr, 1.0e-15)

    # Symmetric scaled system matrix M = diag(sqrt(C)) A diag(1/sqrt(C))
    sqrt_c = np.sqrt(caps)
    inv_sqrt_c = 1.0 / sqrt_c
    m_mat = np.zeros((n_nodes, n_nodes), dtype=np.float64)
    for i in range(n_nodes):
        m_mat[i, i] = -(g_arr[i] + g_arr[i + 1]) / caps[i]
        if i + 1 < n_nodes:
            off = g_arr[i + 1] / (sqrt_c[i] * sqrt_c[i + 1])
            m_mat[i, i + 1] = off
            m_mat[i + 1, i] = off

    # eigh returns eigenvalues sorted ascending (most negative first); reverse so slowest mode is index 0
    evals, q_mat = np.linalg.eigh(m_mat)
    order = np.argsort(-evals)  # slowest (least negative) first
    lam = np.maximum(-evals[order], 1.0e-15)
    q_mat = q_mat[:, order]

    # B_m = Q^T * diag(sqrt(C)) * B  where B[0,0] = g_arr[0]/C[0], B[N-1,1] = g_arr[N]/C[N-1]
    b_m = np.zeros((n_nodes, 2), dtype=np.float64)
    b_m[:, 0] = q_mat[0, :] * (g_arr[0] * inv_sqrt_c[0])
    b_m[:, 1] = q_mat[n_nodes - 1, :] * (g_arr[n_nodes] * inv_sqrt_c[n_nodes - 1])

    # C_m = C * diag(1/sqrt(C)) * Q  where C[0,0] = -g_arr[0], C[1,N-1] = +g_arr[N]
    c_m = np.zeros((2, n_nodes), dtype=np.float64)
    c_m[0, :] = -g_arr[0] * inv_sqrt_c[0] * q_mat[0, :]
    c_m[1, :] = +g_arr[n_nodes] * inv_sqrt_c[n_nodes - 1] * q_mat[n_nodes - 1, :]

    # Exact ramp-input discrete weights over dt_sec
    a = lam * dt_sec
    e = np.exp(-a)
    phi0 = np.where(a < 1.0e-4, 1.0 - 0.5 * a + (a * a) / 6.0 - (a**3) / 24.0, (1.0 - e) / a)
    w_new = np.where(
        a < 1.0e-4,
        dt_sec * (0.5 - a / 6.0 + (a * a) / 24.0 - (a**3) / 120.0),
        dt_sec * (1.0 - phi0) / a,
    )
    w_old = np.where(
        a < 1.0e-4,
        dt_sec * (0.5 - a / 3.0 + (a * a) / 8.0 - (a**3) / 30.0),
        dt_sec * (phi0 - e) / a,
    )

    g_new_out = w_new * b_m[:, 0]
    g_new_in = w_new * b_m[:, 1]
    g_old_out = w_old * b_m[:, 0]
    g_old_in = w_old * b_m[:, 1]

    # Instantaneous coefficients (include ALL modes so steady-state and step-0 are exact!)
    ctf_out0 = float(g_arr[0] + np.dot(c_m[0, :], g_new_out))
    ctf_cross0 = float(-np.dot(c_m[0, :], g_new_in))
    ctf_in0 = float(g_arr[n_nodes] - np.dot(c_m[1, :], g_new_in))

    # Keep ALL n_nodes modes (n_nodes <= max_modes guaranteed -> ZERO truncation error, exact U!)
    k_keep = n_nodes
    steady_out = b_m[:, 0] / lam
    steady_in = b_m[:, 1] / lam

    # Verify exact steady-state conservation: T_out=1, T_in=1 -> q_in=0; T_out=1, T_in=0 -> q_in=u_steady
    q_in_iso = (
        ctf_cross0 - ctf_in0
        + float(np.dot(c_m[1, :], e * (steady_out + steady_in) + g_old_out + g_old_in))
    )
    q_in_unit = (
        ctf_cross0
        + float(np.dot(c_m[1, :], e * steady_out + g_old_out))
    )
    if abs(q_in_iso) > 1.0e-7 or abs(q_in_unit - u_steady) > 1.0e-6 * max(1.0, u_steady):
        raise RuntimeError(
            f"Modal conduction conservation check failed for '{construction_name}': "
            f"q_iso={q_in_iso:.3e}, q_unit={q_in_unit:.6f} vs U={u_steady:.6f}"
        )

    return ModalConductionModel(
        construction_name=construction_name,
        num_modes=k_keep,
        dt_sec=dt_sec,
        u_steady=u_steady,
        ctf_out0=ctf_out0,
        ctf_cross0=ctf_cross0,
        ctf_in0=ctf_in0,
        decay=np.ascontiguousarray(e, dtype=np.float64),
        g_new_out=np.ascontiguousarray(g_new_out, dtype=np.float64),
        g_new_in=np.ascontiguousarray(g_new_in, dtype=np.float64),
        g_old_out=np.ascontiguousarray(g_old_out, dtype=np.float64),
        g_old_in=np.ascontiguousarray(g_old_in, dtype=np.float64),
        c_out=np.ascontiguousarray(c_m[0, :], dtype=np.float64),
        c_in=np.ascontiguousarray(c_m[1, :], dtype=np.float64),
        steady_out=np.ascontiguousarray(steady_out, dtype=np.float64),
        steady_in=np.ascontiguousarray(steady_in, dtype=np.float64),
        lag_oo=0.0,
        lag_oi=0.0,
        lag_io=0.0,
        lag_ii=0.0,
    )

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
