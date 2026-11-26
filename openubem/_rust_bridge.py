"""Optional bridge to the compiled ``openubem._rust`` PyO3 extension.

Provides graceful pure-Python fallback when the optional ``openubem-rust``
package is not installed (D-RS-01 Option (b)) and resolves the three-state
``OPENUBEM_RUST_BACKEND`` rollout flag (``"off"`` | ``"shadow"`` | ``"on"``).
"""

from __future__ import annotations

import importlib
import logging
import os
from types import ModuleType
from typing import Any, Literal

from openubem import config

RustBackendMode = Literal["off", "shadow", "on"]

VALID_RUST_BACKEND_MODES: frozenset[str] = frozenset({"off", "shadow", "on"})

_LOGGER = logging.getLogger(__name__)
_RUST_MODULE_UNLOADED = object()
_CACHED_RUST_MODULE: ModuleType | None | object = _RUST_MODULE_UNLOADED
_CACHED_IMPORT_ERROR: str | None = None


class RustBackendError(RuntimeError):
    """Raised when the Rust backend is invalidly configured or fails fatally."""


def get_rust_backend_mode(mode_override: str | None = None) -> RustBackendMode:
    """Resolve the active Rust backend mode with strict validation.

    Resolution order:
        1. ``mode_override`` if provided.
        2. ``OPENUBEM_RUST_BACKEND`` environment variable if set at call time.
        3. ``openubem.config.RUST_BACKEND`` default (``"off"``).

    Args:
        mode_override: Optional explicit mode override for tests or callers.

    Returns:
        Validated backend mode: ``"off"``, ``"shadow"``, or ``"on"``.

    Raises:
        RustBackendError: If the configured mode is not in
            ``{"off", "shadow", "on"}``.
    """
    if mode_override is not None:
        raw = mode_override
    elif "OPENUBEM_RUST_BACKEND" in os.environ:
        raw = os.environ["OPENUBEM_RUST_BACKEND"]
    else:
        raw = config.RUST_BACKEND
    normalized = raw.strip().lower()
    if normalized not in VALID_RUST_BACKEND_MODES:
        raise RustBackendError(
            f"Invalid OPENUBEM_RUST_BACKEND={raw!r}; "
            "expected one of 'off', 'shadow', or 'on'."
        )
    return normalized  # type: ignore[return-value]


def reset_rust_bridge_cache() -> None:
    """Clear the cached ``openubem._rust`` import state (primarily for tests)."""
    global _CACHED_RUST_MODULE, _CACHED_IMPORT_ERROR
    _CACHED_RUST_MODULE = _RUST_MODULE_UNLOADED
    _CACHED_IMPORT_ERROR = None


def load_rust_module() -> ModuleType | None:
    """Import and cache ``openubem._rust`` if installed, else return ``None``.

    Returns:
        The compiled ``openubem._rust`` extension module, or ``None`` if the
        optional Rust extra is not installed or fails to load.
    """
    global _CACHED_RUST_MODULE, _CACHED_IMPORT_ERROR
    if _CACHED_RUST_MODULE is not _RUST_MODULE_UNLOADED:
        return _CACHED_RUST_MODULE  # type: ignore[return-value]
    try:
        module = importlib.import_module("_openubem_rust")
    except ImportError as exc:
        _CACHED_RUST_MODULE = None
        _CACHED_IMPORT_ERROR = str(exc)
        _LOGGER.debug("Optional _openubem_rust extension unavailable: %s", exc)
        return None
    _CACHED_RUST_MODULE = module
    _CACHED_IMPORT_ERROR = None
    return module


def is_rust_available() -> bool:
    """Return ``True`` when the compiled ``openubem._rust`` module is loadable.

    Returns:
        Boolean indicating whether ``openubem._rust`` can be imported.
    """
    return load_rust_module() is not None


def rust_import_error() -> str | None:
    """Return the cached ``ImportError`` string if ``openubem._rust`` failed.

    Returns:
        Error message string, or ``None`` if loaded or not yet attempted.
    """
    if _CACHED_RUST_MODULE is _RUST_MODULE_UNLOADED:
        load_rust_module()
    return _CACHED_IMPORT_ERROR


def rust_smoke_info() -> dict[str, Any] | None:
    """Fetch diagnostic build metadata from ``openubem._rust.rust_smoke_info``.

    Returns:
        Dictionary with target triple, crate version, and SIMD feature flags,
        or ``None`` when the optional extension is not installed.
    """
    mod = load_rust_module()
    if mod is None:
        return None
    fn = getattr(mod, "rust_smoke_info", None)
    if fn is None:
        return None
    return dict(fn())
