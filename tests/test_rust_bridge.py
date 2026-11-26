"""Tests for Phase 0 Rust bridge, rollout flags, and shadow-diffing harness."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from openubem import config
from openubem._rust_bridge import (
    RustBackendError,
    get_rust_backend_mode,
    is_rust_available,
    load_rust_module,
    reset_rust_bridge_cache,
    rust_import_error,
    rust_smoke_info,
)
from openubem.rust_shadow import (
    dispatch_with_rust,
    shadow_compare,
)


def test_default_rust_backend_is_auto_and_off_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Default OPENUBEM_RUST_BACKEND is 'auto' (resolving on/off); 'off' still works."""
    monkeypatch.delenv("OPENUBEM_RUST_BACKEND", raising=False)
    monkeypatch.setattr(config, "RUST_BACKEND", "auto")
    expected_auto = "on" if is_rust_available() else "off"
    assert get_rust_backend_mode() == expected_auto

    monkeypatch.setattr(config, "RUST_BACKEND", "off")
    assert get_rust_backend_mode() == "off"


@pytest.mark.parametrize("raw,expected", [
    ("off", "off"),
    ("OFF", "off"),
    (" shadow ", "shadow"),
    ("On", "on"),
])
def test_rust_backend_mode_parsing(
    monkeypatch: pytest.MonkeyPatch, raw: str, expected: str
) -> None:
    """Valid mode strings normalize cleanly regardless of case or whitespace."""
    monkeypatch.setenv("OPENUBEM_RUST_BACKEND", raw)
    assert get_rust_backend_mode() == expected


def test_invalid_rust_backend_mode_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unknown OPENUBEM_RUST_BACKEND values fail closed with RustBackendError."""
    monkeypatch.setenv("OPENUBEM_RUST_BACKEND", "turbo")
    with pytest.raises(RustBackendError, match="Invalid OPENUBEM_RUST_BACKEND"):
        get_rust_backend_mode()


def test_graceful_fallback_when_rust_extension_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing optional openubem._rust falls back cleanly to Python in all modes."""
    real_import = importlib.import_module

    def _missing_rust(name: str, package: str | None = None) -> Any:
        if name in {"_openubem_rust", "openubem._rust"}:
            raise ImportError("simulated missing _openubem_rust")
        return real_import(name, package)

    reset_rust_bridge_cache()
    monkeypatch.setattr(importlib, "import_module", _missing_rust)
    try:
        assert load_rust_module() is None
        assert is_rust_available() is False
        assert "simulated missing" in (rust_import_error() or "")
        assert rust_smoke_info() is None

        for mode in ("off", "shadow", "on"):
            out = dispatch_with_rust(
                "test.fallback",
                py_fn=lambda: [1.0, 2.0],
                rust_fn=lambda: [99.0, 99.0],
                mode_override=mode,  # type: ignore[arg-type]
            )
            assert out == [1.0, 2.0]
    finally:
        reset_rust_bridge_cache()


def test_shadow_compare_buckets_b1_b2_b3() -> None:
    """B1, B2, and B3 enforce exact, 1e-12, and 1e-4 tolerances respectively."""
    py_arr = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    tiny_drift = py_arr + 5e-13
    medium_drift = py_arr + 5e-5

    assert shadow_compare("c", py_arr, py_arr.copy(), bucket="B1").matched
    assert not shadow_compare("c", py_arr, tiny_drift, bucket="B1").matched

    assert shadow_compare("c", py_arr, tiny_drift, bucket="B2").matched
    assert not shadow_compare("c", py_arr, medium_drift, bucket="B2").matched

    assert shadow_compare("c", py_arr, medium_drift, bucket="B3").matched
    assert not shadow_compare("c", py_arr, py_arr + 2e-4, bucket="B3").matched


def test_shadow_compare_nan_and_schema_fingerprinting() -> None:
    """NaN positions and dict schema diffs yield stable non-empty fingerprints."""
    a = np.array([1.0, np.nan, 3.0])
    b_same = np.array([1.0, np.nan, 3.0])
    b_diff = np.array([1.0, 2.0, 3.0])

    assert shadow_compare("nan_test", a, b_same, bucket="B1").matched
    res1 = shadow_compare("nan_test", a, b_diff, bucket="B1")
    res2 = shadow_compare("nan_test", a, b_diff, bucket="B1")
    assert not res1.matched and res1.mismatch is not None
    assert res1.mismatch.category == "nan_mismatch"
    assert res2.mismatch is not None
    assert res1.mismatch.fingerprint == res2.mismatch.fingerprint

    schema_res = shadow_compare(
        "schema_test",
        {"eui": 100.0, "status": "ok"},
        {"eui": 100.0},
        bucket="B1",
    )
    assert not schema_res.matched and schema_res.mismatch is not None
    assert schema_res.mismatch.category == "schema_mismatch"


def test_dispatch_shadow_preserves_python_and_logs_jsonl(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Shadow mode returns Python output even on drift or Rust crash and logs JSONL."""
    monkeypatch.setattr("openubem.rust_shadow.is_rust_available", lambda: True)
    log_file = tmp_path / "shadow.jsonl"

    out_drift = dispatch_with_rust(
        "demo.drift",
        py_fn=lambda: {"eui": 154.10},
        rust_fn=lambda: {"eui": 155.00},
        bucket="B1",
        mode_override="shadow",
        log_path=log_file,
        context={"building_id": "b001"},
    )
    assert out_drift == {"eui": 154.10}

    def _boom() -> dict[str, float]:
        raise ValueError("rust parse failure")

    out_crash = dispatch_with_rust(
        "demo.crash",
        py_fn=lambda: {"eui": 154.10},
        rust_fn=_boom,
        bucket="B1",
        mode_override="shadow",
        log_path=log_file,
        context={"building_id": "b002"},
    )
    assert out_crash == {"eui": 154.10}

    records = [
        json.loads(line)
        for line in log_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(records) == 2
    assert records[0]["category"] == "value_drift"
    assert records[0]["context"] == {"building_id": "b001"}
    assert records[1]["category"] == "exception_mismatch"
    assert records[1]["context"] == {"building_id": "b002"}


def test_dispatch_on_uses_rust_when_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mode 'on' dispatches to rust_fn when compiled extension is present."""
    monkeypatch.setattr("openubem.rust_shadow.is_rust_available", lambda: True)
    out = dispatch_with_rust(
        "demo.on",
        py_fn=lambda: "python",
        rust_fn=lambda: "rust",
        mode_override="on",
    )
    assert out == "rust"


def test_compiled_rust_extension_smoke() -> None:
    """Verify compiled openubem._rust metadata, py.detach smoke fn, and error map."""
    reset_rust_bridge_cache()
    mod = load_rust_module()
    if mod is None:
        pytest.skip("optional openubem-rust extension not built in this environment")

    info = rust_smoke_info()
    assert info is not None
    assert info["crate_name"] == "openubem-py"
    assert info["pyo3_abi"] == "abi3-py310"
    assert isinstance(info["simd_features"], list)
    assert info["rayon_threads"] >= 1

    py_out = [3.0, -4.0, 8.5]
    rust_out = mod.rust_smoke_scale([1.5, -2.0, 4.25], 2.0)
    assert shadow_compare("smoke.scale", py_out, rust_out, bucket="B1").matched

    with pytest.raises(ValueError, match="non-finite"):
        mod.rust_smoke_scale([1.0, float("nan")], 2.0)
