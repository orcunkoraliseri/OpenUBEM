"""Anthropic-style shadow-diffing and mismatch fingerprinting for Rust parity.

Implements three numeric/structural comparison buckets (DR01 §5 / Guardrail 3):
  - ``B1``: bit-exact equality for parsers, schemas, provenance, and accounting.
  - ``B2``: float64 numerical kernels (``rtol=1e-12``, ``atol=1e-12``).
  - ``B3``: float32/BVH/raster approximations (default ``atol=1e-4``).

In ``OPENUBEM_RUST_BACKEND="shadow"`` mode, both Python and Rust execute on the
same input, any divergence is canonically fingerprinted and logged to JSONL
(if configured), and the Python output is ALWAYS returned unchanged.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import logging
import math
import os
from pathlib import Path
import time
from typing import Any, Literal, TypeVar

import numpy as np

from openubem import config
from openubem._rust_bridge import (
    RustBackendMode,
    get_rust_backend_mode,
    is_rust_available,
)

T = TypeVar("T")
ToleranceBucket = Literal["B1", "B2", "B3"]

_LOGGER = logging.getLogger(__name__)

BUCKET_TOLERANCES: dict[ToleranceBucket, tuple[float, float]] = {
    "B1": (0.0, 0.0),
    "B2": (1e-12, 1e-12),
    "B3": (0.0, 1e-4),
}


@dataclass(frozen=True)
class ShadowMismatch:
    """Structured record of a Python-vs-Rust shadow comparison divergence.

    Attributes:
        component: Logical subsystem name (e.g., ``"openubem.shading"``).
        bucket: Tolerance bucket applied (``"B1"``, ``"B2"``, or ``"B3"``).
        category: Coarse mismatch taxonomy label.
        fingerprint: Deterministic SHA-256 prefix grouping equivalent diffs.
        detail: Human-readable summary of the first or worst divergence.
        max_abs_diff: Maximum absolute numeric difference if applicable.
        max_rel_diff: Maximum relative numeric difference if applicable.
        py_elapsed_ms: Python reference runtime in milliseconds.
        rust_elapsed_ms: Rust implementation runtime in milliseconds.
        timestamp_utc: ISO-8601 UTC timestamp of the comparison.
        context: Optional metadata (e.g., building ID or district code).
    """

    component: str
    bucket: ToleranceBucket
    category: str
    fingerprint: str
    detail: str
    max_abs_diff: float | None = None
    max_rel_diff: float | None = None
    py_elapsed_ms: float = 0.0
    rust_elapsed_ms: float = 0.0
    timestamp_utc: str = ""
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ShadowCompareResult:
    """Outcome of comparing a Python output against a Rust candidate output.

    Attributes:
        matched: ``True`` when outputs agree within the bucket's tolerance.
        mismatch: Populated ``ShadowMismatch`` when ``matched`` is ``False``.
    """

    matched: bool
    mismatch: ShadowMismatch | None = None


def _make_fingerprint(
    component: str,
    bucket: ToleranceBucket,
    category: str,
    path: str,
    signature: str,
) -> str:
    """Compute a stable 16-hex-char fingerprint for a mismatch class.

    Args:
        component: Subsystem name.
        bucket: Tolerance bucket.
        category: Mismatch category.
        path: Structural path (e.g., ``"root[0].eui_kwh_m2"``).
        signature: Structural or type signature excluding volatile values.

    Returns:
        16-character hexadecimal SHA-256 digest prefix.
    """
    payload = f"{component}|{bucket}|{category}|{path}|{signature}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def _resolve_log_path(log_path: Path | None) -> Path | None:
    """Resolve the JSONL shadow mismatch log destination.

    Args:
        log_path: Explicit override path, or ``None`` to inspect environment.

    Returns:
        Resolved ``Path`` if logging is enabled, else ``None``.
    """
    if log_path is not None:
        return log_path
    env_val = os.environ.get("OPENUBEM_RUST_SHADOW_LOG")
    if env_val:
        return Path(env_val)
    return config.RUST_SHADOW_LOG_PATH


def record_shadow_mismatch(
    mismatch: ShadowMismatch,
    log_path: Path | None = None,
) -> None:
    """Emit a shadow mismatch warning and optionally append it to a JSONL log.

    Args:
        mismatch: Structured divergence record.
        log_path: Optional override path for the JSONL mismatch log.
    """
    _LOGGER.warning(
        "Rust shadow mismatch [%s/%s %s fp=%s]: %s",
        mismatch.component,
        mismatch.bucket,
        mismatch.category,
        mismatch.fingerprint,
        mismatch.detail,
    )
    target = _resolve_log_path(log_path)
    if target is None:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(mismatch), sort_keys=True) + "\n")


def _compare_scalars(
    py_val: float,
    rust_val: float,
    rtol: float,
    atol: float,
) -> tuple[bool, str, float | None, float | None]:
    """Compare two floats under NaN/Inf and ``(rtol, atol)`` rules.

    Args:
        py_val: Reference Python float value.
        rust_val: Candidate Rust float value.
        rtol: Relative tolerance.
        atol: Absolute tolerance.

    Returns:
        Tuple ``(ok, category, abs_diff, rel_diff)``.
    """
    py_nan = math.isnan(py_val)
    rust_nan = math.isnan(rust_val)
    if py_nan and rust_nan:
        return True, "ok", 0.0, 0.0
    if py_nan != rust_nan:
        return False, "nan_mismatch", None, None
    if math.isinf(py_val) or math.isinf(rust_val):
        if py_val == rust_val:
            return True, "ok", 0.0, 0.0
        return False, "inf_mismatch", None, None
    abs_diff = abs(py_val - rust_val)
    denom = max(abs(py_val), abs(rust_val))
    rel_diff = abs_diff / denom if denom > 0.0 else 0.0
    if rtol == 0.0 and atol == 0.0:
        return py_val == rust_val, "value_drift", abs_diff, rel_diff
    ok = abs_diff <= (atol + rtol * abs(py_val))
    return ok, "value_drift", abs_diff, rel_diff


def _compare_arrays(
    py_arr: np.ndarray,
    rust_arr: np.ndarray,
    rtol: float,
    atol: float,
    path: str,
) -> tuple[bool, str, str, str, float | None, float | None]:
    """Compare two NumPy arrays for shape, dtype-kind, NaN, and value parity.

    Args:
        py_arr: Reference NumPy array.
        rust_arr: Candidate NumPy array.
        rtol: Relative tolerance.
        atol: Absolute tolerance.
        path: Structural path string.

    Returns:
        Tuple ``(ok, category, signature, detail, max_abs, max_rel)``.
    """
    if py_arr.shape != rust_arr.shape:
        sig = f"shape:{py_arr.shape}!={rust_arr.shape}"
        return (
            False,
            "shape_mismatch",
            sig,
            f"{path}: shape {py_arr.shape} != {rust_arr.shape}",
            None,
            None,
        )
    if np.issubdtype(py_arr.dtype, np.floating) or np.issubdtype(
        rust_arr.dtype, np.floating
    ):
        a = np.asarray(py_arr, dtype=np.float64)
        b = np.asarray(rust_arr, dtype=np.float64)
        nan_a = np.isnan(a)
        nan_b = np.isnan(b)
        if not np.array_equal(nan_a, nan_b):
            n_diff = int(np.count_nonzero(nan_a != nan_b))
            return (
                False,
                "nan_mismatch",
                f"nan_mask:{a.shape}",
                f"{path}: NaN mask differs at {n_diff} element(s)",
                None,
                None,
            )
        inf_a = np.isinf(a)
        inf_b = np.isinf(b)
        if not np.array_equal(inf_a, inf_b) or not np.array_equal(
            a[inf_a], b[inf_b]
        ):
            return (
                False,
                "inf_mismatch",
                f"inf_mask:{a.shape}",
                f"{path}: Inf values differ",
                None,
                None,
            )
        finite = np.isfinite(a)
        if not np.any(finite):
            return True, "ok", "", "", 0.0, 0.0
        fa = a[finite]
        fb = b[finite]
        abs_diff = np.abs(fa - fb)
        max_abs = float(np.max(abs_diff))
        denom = np.maximum(np.abs(fa), np.abs(fb))
        with np.errstate(divide="ignore", invalid="ignore"):
            rel = np.where(denom > 0.0, abs_diff / denom, 0.0)
        max_rel = float(np.max(rel))
        if rtol == 0.0 and atol == 0.0:
            ok = bool(np.array_equal(fa, fb))
        else:
            ok = bool(np.allclose(fa, fb, rtol=rtol, atol=atol, equal_nan=True))
        if ok:
            return True, "ok", "", "", max_abs, max_rel
        return (
            False,
            "value_drift",
            f"float_array:{a.shape}:{py_arr.dtype}->{rust_arr.dtype}",
            f"{path}: max_abs={max_abs:.3e}, max_rel={max_rel:.3e} "
            f"(rtol={rtol:.1e}, atol={atol:.1e})",
            max_abs,
            max_rel,
        )
    if np.array_equal(py_arr, rust_arr):
        return True, "ok", "", "", 0.0, 0.0
    n_diff = int(np.count_nonzero(py_arr != rust_arr))
    return (
        False,
        "value_drift",
        f"exact_array:{py_arr.shape}:{py_arr.dtype}",
        f"{path}: {n_diff} element(s) differ",
        None,
        None,
    )


def _compare_recursive(
    py_val: Any,
    rust_val: Any,
    rtol: float,
    atol: float,
    path: str,
) -> tuple[bool, str, str, str, float | None, float | None]:
    """Recursively compare arbitrary Python/NumPy nested outputs.

    Args:
        py_val: Reference Python value.
        rust_val: Candidate Rust value.
        rtol: Relative tolerance.
        atol: Absolute tolerance.
        path: Structural path string.

    Returns:
        Tuple ``(ok, category, signature, detail, max_abs, max_rel)``.
    """
    if isinstance(py_val, np.ndarray) or isinstance(rust_val, np.ndarray):
        if not (isinstance(py_val, np.ndarray) and isinstance(rust_val, np.ndarray)):
            sig = f"type:{type(py_val).__name__}!={type(rust_val).__name__}"
            return (
                False,
                "type_mismatch",
                sig,
                f"{path}: {type(py_val).__name__} != {type(rust_val).__name__}",
                None,
                None,
            )
        return _compare_arrays(py_val, rust_val, rtol, atol, path)

    if isinstance(py_val, dict) and isinstance(rust_val, dict):
        py_keys = set(py_val.keys())
        rust_keys = set(rust_val.keys())
        if py_keys != rust_keys:
            missing = sorted(map(str, py_keys - rust_keys))
            extra = sorted(map(str, rust_keys - py_keys))
            return (
                False,
                "schema_mismatch",
                f"keys:missing={missing}:extra={extra}",
                f"{path}: dict keys differ (missing={missing}, extra={extra})",
                None,
                None,
            )
        worst_abs: float | None = None
        worst_rel: float | None = None
        for key in sorted(py_keys, key=str):
            ok, cat, sig, detail, a_diff, r_diff = _compare_recursive(
                py_val[key], rust_val[key], rtol, atol, f"{path}.{key}"
            )
            if not ok:
                return False, cat, sig, detail, a_diff, r_diff
            if a_diff is not None:
                worst_abs = a_diff if worst_abs is None else max(worst_abs, a_diff)
            if r_diff is not None:
                worst_rel = r_diff if worst_rel is None else max(worst_rel, r_diff)
        return True, "ok", "", "", worst_abs, worst_rel

    if isinstance(py_val, (list, tuple)) and isinstance(rust_val, (list, tuple)):
        if len(py_val) != len(rust_val):
            return (
                False,
                "shape_mismatch",
                f"len:{len(py_val)}!={len(rust_val)}",
                f"{path}: length {len(py_val)} != {len(rust_val)}",
                None,
                None,
            )
        worst_abs = None
        worst_rel = None
        for idx, (lhs, rhs) in enumerate(zip(py_val, rust_val)):
            ok, cat, sig, detail, a_diff, r_diff = _compare_recursive(
                lhs, rhs, rtol, atol, f"{path}[{idx}]"
            )
            if not ok:
                return False, cat, sig, detail, a_diff, r_diff
            if a_diff is not None:
                worst_abs = a_diff if worst_abs is None else max(worst_abs, a_diff)
            if r_diff is not None:
                worst_rel = r_diff if worst_rel is None else max(worst_rel, r_diff)
        return True, "ok", "", "", worst_abs, worst_rel

    if isinstance(py_val, bool) or isinstance(rust_val, bool):
        if type(py_val) is not type(rust_val) or py_val != rust_val:
            return (
                False,
                "value_drift",
                f"bool:{type(py_val).__name__}!={type(rust_val).__name__}",
                f"{path}: {py_val!r} != {rust_val!r}",
                None,
                None,
            )
        return True, "ok", "", "", 0.0, 0.0

    if isinstance(py_val, (int, float, np.number)) and isinstance(
        rust_val, (int, float, np.number)
    ):
        if (
            isinstance(py_val, (int, np.integer))
            and isinstance(rust_val, (int, np.integer))
            and rtol == 0.0
            and atol == 0.0
        ):
            if int(py_val) == int(rust_val):
                return True, "ok", "", "", 0.0, 0.0
            diff = float(abs(int(py_val) - int(rust_val)))
            return (
                False,
                "value_drift",
                "int_mismatch",
                f"{path}: {py_val!r} != {rust_val!r}",
                diff,
                None,
            )
        ok, cat, a_diff, r_diff = _compare_scalars(
            float(py_val), float(rust_val), rtol, atol
        )
        if ok:
            return True, "ok", "", "", a_diff, r_diff
        return (
            False,
            cat,
            f"scalar:{cat}",
            f"{path}: {py_val!r} vs {rust_val!r} (abs={a_diff}, rel={r_diff})",
            a_diff,
            r_diff,
        )

    if py_val == rust_val:
        return True, "ok", "", "", None, None
    return (
        False,
        "value_drift",
        f"exact:{type(py_val).__name__}:{type(rust_val).__name__}",
        f"{path}: {py_val!r} != {rust_val!r}",
        None,
        None,
    )


def shadow_compare(
    component: str,
    py_result: Any,
    rust_result: Any,
    *,
    bucket: ToleranceBucket = "B1",
    rtol: float | None = None,
    atol: float | None = None,
    py_elapsed_ms: float = 0.0,
    rust_elapsed_ms: float = 0.0,
    context: dict[str, Any] | None = None,
) -> ShadowCompareResult:
    """Compare a Python reference output against a Rust candidate output.

    Args:
        component: Logical subsystem name (e.g., ``"openubem.results.sql"``).
        py_result: Reference result produced by the Python implementation.
        rust_result: Candidate result produced by the Rust implementation.
        bucket: Tolerance bucket (``"B1"``, ``"B2"``, or ``"B3"``).
        rtol: Optional relative tolerance override.
        atol: Optional absolute tolerance override.
        py_elapsed_ms: Python runtime in milliseconds.
        rust_elapsed_ms: Rust runtime in milliseconds.
        context: Optional metadata recorded with any mismatch.

    Returns:
        ``ShadowCompareResult`` indicating parity or containing a fingerprinted
        ``ShadowMismatch``.
    """
    default_rtol, default_atol = BUCKET_TOLERANCES[bucket]
    eff_rtol = default_rtol if rtol is None else rtol
    eff_atol = default_atol if atol is None else atol

    ok, category, signature, detail, max_abs, max_rel = _compare_recursive(
        py_result, rust_result, eff_rtol, eff_atol, "root"
    )
    if ok:
        return ShadowCompareResult(matched=True, mismatch=None)

    mismatch = ShadowMismatch(
        component=component,
        bucket=bucket,
        category=category,
        fingerprint=_make_fingerprint(component, bucket, category, "root", signature),
        detail=detail,
        max_abs_diff=max_abs,
        max_rel_diff=max_rel,
        py_elapsed_ms=py_elapsed_ms,
        rust_elapsed_ms=rust_elapsed_ms,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        context=dict(context or {}),
    )
    return ShadowCompareResult(matched=False, mismatch=mismatch)


def dispatch_with_rust(
    component: str,
    py_fn: Callable[[], T],
    rust_fn: Callable[[], T] | None,
    *,
    bucket: ToleranceBucket = "B1",
    rtol: float | None = None,
    atol: float | None = None,
    mode_override: RustBackendMode | None = None,
    log_path: Path | None = None,
    context: dict[str, Any] | None = None,
) -> T:
    """Execute ``py_fn`` and/or ``rust_fn`` according to ``OPENUBEM_RUST_BACKEND``.

    Semantics:
        - ``"off"``: Calls ``py_fn`` only.
        - ``"on"``: Calls ``rust_fn`` if ``openubem._rust`` is available and
          ``rust_fn`` is provided; otherwise gracefully falls back to ``py_fn``.
        - ``"shadow"``: Runs ``py_fn`` and ``rust_fn`` (if available), logs any
          mismatch or Rust exception via ``record_shadow_mismatch``, and ALWAYS
          returns the Python result unchanged.

    Args:
        component: Subsystem name for shadow telemetry.
        py_fn: Zero-argument callable running the reference Python path.
        rust_fn: Optional zero-argument callable running the Rust path.
        bucket: Tolerance bucket for shadow comparison.
        rtol: Optional relative tolerance override.
        atol: Optional absolute tolerance override.
        mode_override: Optional mode override for tests.
        log_path: Optional JSONL mismatch log override.
        context: Optional metadata dictionary.

    Returns:
        Result of ``py_fn`` (in ``"off"``, ``"shadow"``, or fallback) or
        ``rust_fn`` (in ``"on"`` when available).
    """
    mode = get_rust_backend_mode(mode_override)
    if mode == "off" or rust_fn is None or not is_rust_available():
        return py_fn()
    if mode == "on":
        return rust_fn()

    # mode == "shadow": always return Python result; never fail on Rust diff
    t0 = time.perf_counter()
    py_result = py_fn()
    py_ms = (time.perf_counter() - t0) * 1000.0

    t1 = time.perf_counter()
    try:
        rust_result = rust_fn()
    except Exception as exc:
        rust_ms = (time.perf_counter() - t1) * 1000.0
        mismatch = ShadowMismatch(
            component=component,
            bucket=bucket,
            category="exception_mismatch",
            fingerprint=_make_fingerprint(
                component, bucket, "exception_mismatch", "root", type(exc).__name__
            ),
            detail=f"Rust raised {type(exc).__name__}: {exc}",
            py_elapsed_ms=py_ms,
            rust_elapsed_ms=rust_ms,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            context=dict(context or {}),
        )
        record_shadow_mismatch(mismatch, log_path=log_path)
        return py_result

    rust_ms = (time.perf_counter() - t1) * 1000.0
    comp = shadow_compare(
        component,
        py_result,
        rust_result,
        bucket=bucket,
        rtol=rtol,
        atol=atol,
        py_elapsed_ms=py_ms,
        rust_elapsed_ms=rust_ms,
        context=context,
    )
    if not comp.matched and comp.mismatch is not None:
        record_shadow_mismatch(comp.mismatch, log_path=log_path)
    return py_result
