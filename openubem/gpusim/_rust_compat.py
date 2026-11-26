"""Self-contained Rust FFI & shadow-parity dispatcher for ``openubem.gpusim``.

Kept strictly free of non-``gpusim`` ``openubem.*`` imports so
``tests/gpusim/test_isolation.py`` remains 100% intact. Reads the same
``OPENUBEM_RUST_BACKEND`` (default ``"off"``) and ``OPENUBEM_RUST_SHADOW_LOG``
environment variables as ``openubem._rust_bridge`` / ``openubem.rust_shadow``.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import time
from typing import Any, Literal, TypeVar

import numpy as np

T = TypeVar("T")
Bucket = Literal["B1", "B2", "B3"]
_LOGGER = logging.getLogger(__name__)
_VALID_MODES = ("off", "shadow", "on")
_TOL: dict[Bucket, tuple[float, float]] = {
    "B1": (0.0, 0.0),
    "B2": (1e-12, 1e-12),
    "B3": (0.0, 1e-4),
}


def get_gpusim_rust_mode() -> str:
    """Return active ``OPENUBEM_RUST_BACKEND`` mode (``off`` | ``shadow`` | ``on``)."""
    mode = os.environ.get("OPENUBEM_RUST_BACKEND", "off").strip().lower()
    return mode if mode in _VALID_MODES else "off"


def load_gpusim_rust_module() -> Any | None:
    """Import top-level ``_openubem_rust`` extension if installed and not forced off."""
    if get_gpusim_rust_mode() == "off":
        return None
    try:
        import _openubem_rust  # type: ignore[import-not-found]
    except ImportError:
        return None
    return _openubem_rust


def _compare_pair(
    py_val: Any, rs_val: Any, rtol: float, atol: float, path: str = "root"
) -> tuple[bool, float | None, float | None, str]:
    """Recursively compare Python vs Rust outputs within ``(rtol, atol)``."""
    if isinstance(py_val, tuple) and isinstance(rs_val, tuple):
        if len(py_val) != len(rs_val):
            return False, None, None, f"{path}: len {len(py_val)} != {len(rs_val)}"
        worst_abs: float | None = None
        worst_rel: float | None = None
        for idx, (pv, rv) in enumerate(zip(py_val, rs_val)):
            ok, a_d, r_d, msg = _compare_pair(pv, rv, rtol, atol, f"{path}[{idx}]")
            if a_d is not None:
                worst_abs = a_d if worst_abs is None else max(worst_abs, a_d)
            if r_d is not None:
                worst_rel = r_d if worst_rel is None else max(worst_rel, r_d)
            if not ok:
                return False, worst_abs, worst_rel, msg
        return True, worst_abs, worst_rel, ""

    if isinstance(py_val, np.ndarray) or isinstance(rs_val, np.ndarray):
        pa = np.asarray(py_val)
        ra = np.asarray(rs_val)
        if pa.shape != ra.shape:
            return False, None, None, f"{path}: shape {pa.shape} != {ra.shape}"
        if pa.size == 0:
            return True, 0.0, 0.0, ""
        p_f = pa.astype(np.float64)
        r_f = ra.astype(np.float64)
        diff = np.abs(p_f - r_f)
        max_abs = float(np.nanmax(diff))
        denom = np.maximum(np.abs(p_f), 1e-30)
        max_rel = float(np.nanmax(diff / denom))
        ok = bool(np.allclose(p_f, r_f, rtol=rtol, atol=atol, equal_nan=True))
        msg = (
            ""
            if ok
            else f"{path}: max_abs={max_abs:.3e}, max_rel={max_rel:.3e} (rtol={rtol:.1e}, atol={atol:.1e})"
        )
        return ok, max_abs, max_rel, msg

    if isinstance(py_val, (int, float, np.floating, np.integer)) and isinstance(
        rs_val, (int, float, np.floating, np.integer)
    ):
        pf, rf = float(py_val), float(rs_val)
        diff_f = abs(pf - rf)
        rel_f = diff_f / max(abs(pf), 1e-30)
        ok = bool(np.isclose(pf, rf, rtol=rtol, atol=atol, equal_nan=True))
        return (
            ok,
            diff_f,
            rel_f,
            "" if ok else f"{path}: {pf} != {rf} (max_abs={diff_f:.3e})",
        )

    if is_dataclass(py_val) and not isinstance(py_val, type) and is_dataclass(rs_val) and not isinstance(rs_val, type):
        return _compare_pair(asdict(py_val), asdict(rs_val), rtol, atol, path)

    if isinstance(py_val, dict) and isinstance(rs_val, dict):
        if set(py_val.keys()) != set(rs_val.keys()):
            return False, None, None, f"{path}: key mismatch"
        w_abs: float | None = None
        w_rel: float | None = None
        for k in py_val:
            ok, a_d, r_d, msg = _compare_pair(py_val[k], rs_val[k], rtol, atol, f"{path}.{k}")
            if a_d is not None:
                w_abs = a_d if w_abs is None else max(w_abs, a_d)
            if r_d is not None:
                w_rel = r_d if w_rel is None else max(w_rel, r_d)
            if not ok:
                return False, w_abs, w_rel, msg
        return True, w_abs, w_rel, ""

    ok = bool(py_val == rs_val)
    return ok, None, None, "" if ok else f"{path}: value mismatch"


def dispatch_gpusim_rust(
    component: str,
    py_fn: Callable[[], T],
    rust_fn: Callable[[], T] | None,
    *,
    bucket: Bucket = "B2",
    rtol: float | None = None,
    atol: float | None = None,
) -> T:
    """Dispatch to ``py_fn`` / ``rust_fn`` honoring ``off``, ``shadow``, ``on``."""
    mode = get_gpusim_rust_mode()
    if mode == "off" or rust_fn is None:
        return py_fn()
    if mode == "on":
        return rust_fn()

    t0 = time.perf_counter()
    py_out = py_fn()
    py_ms = (time.perf_counter() - t0) * 1000.0

    t1 = time.perf_counter()
    try:
        rs_out = rust_fn()
        rs_ms = (time.perf_counter() - t1) * 1000.0
    except Exception as exc:  # noqa: BLE001
        rs_ms = (time.perf_counter() - t1) * 1000.0
        _record_mismatch(
            component,
            bucket,
            "exception",
            f"{type(exc).__name__}: {exc}",
            None,
            None,
            py_ms,
            rs_ms,
        )
        return py_out

    b_rtol, b_atol = _TOL[bucket]
    use_rtol = b_rtol if rtol is None else rtol
    use_atol = b_atol if atol is None else atol
    ok, max_abs, max_rel, msg = _compare_pair(py_out, rs_out, use_rtol, use_atol)
    if not ok:
        _record_mismatch(
            component,
            bucket,
            "value_drift",
            msg,
            max_abs,
            max_rel,
            py_ms,
            rs_ms,
        )
    return py_out


def _record_mismatch(
    component: str,
    bucket: Bucket,
    category: str,
    detail: str,
    max_abs_diff: float | None,
    max_rel_diff: float | None,
    py_elapsed_ms: float,
    rust_elapsed_ms: float,
) -> None:
    fp = hashlib.sha256(f"{component}|{bucket}|{category}|{detail}".encode()).hexdigest()[
        :16
    ]
    _LOGGER.warning("Rust shadow mismatch [%s/%s fp=%s]: %s", component, bucket, fp, detail)
    log_env = os.environ.get("OPENUBEM_RUST_SHADOW_LOG", "").strip()
    if log_env:
        path = Path(log_env)
        path.parent.mkdir(parents=True, exist_ok=True)
        rec = {
            "component": component,
            "bucket": bucket,
            "category": category,
            "fingerprint": fp,
            "detail": detail,
            "max_abs_diff": max_abs_diff,
            "max_rel_diff": max_rel_diff,
            "py_elapsed_ms": round(py_elapsed_ms, 3),
            "rust_elapsed_ms": round(rust_elapsed_ms, 3),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "context": {},
        }
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(rec) + "\n")
