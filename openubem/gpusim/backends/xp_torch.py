from collections.abc import Sequence
from typing import Any

import numpy as np
import torch


class TorchNamespace:
    """Array-API-like namespace bridging frozen Stage A physics to PyTorch.

    Attributes:
        device: Target PyTorch device (for example ``cpu`` or ``mps``).
        dtype: Working floating-point dtype (``torch.float64`` or ``torch.float32``).
        float64: Alias for the working floating-point dtype used by physics calls.
    """

    def __init__(
        self,
        device: str | torch.device = "cpu",
        dtype: torch.dtype = torch.float64,
    ) -> None:
        """Initialize the PyTorch namespace shim.

        Args:
            device: Target PyTorch device.
            dtype: Working floating-point dtype.
        """
        self.device: torch.device = torch.device(device)
        self.dtype: torch.dtype = dtype
        self.float64: torch.dtype = dtype
        self._scalar_cache: dict[
            tuple[bool, bool | int | float, torch.dtype], torch.Tensor
        ] = {}

    def _to_tensor(
        self,
        value: Any,
        dtype: torch.dtype | None = None,
    ) -> torch.Tensor:
        """Convert a scalar, NumPy array, sequence, or tensor onto target device.

        Args:
            value: Input value to convert.
            dtype: Optional explicit PyTorch dtype override.

        Returns:
            Tensor on ``self.device`` with the resolved dtype.
        """
        if type(value) is torch.Tensor:
            target = dtype if dtype is not None else value.dtype
            if value.device == self.device and value.dtype == target:
                return value
            if self.device.type == "mps" and value.dtype == torch.float64:
                return value.to(dtype=target).to(device=self.device)
            return value.to(device=self.device, dtype=target)

        if isinstance(value, bool):
            target = dtype if dtype is not None else torch.bool
            key = (True, value, target)
            cached = self._scalar_cache.get(key)
            if cached is None:
                cached = torch.tensor(value, dtype=target, device=self.device)
                self._scalar_cache[key] = cached
            return cached

        if isinstance(value, (int, float)):
            target = dtype if dtype is not None else self.dtype
            key = (False, value, target)
            cached = self._scalar_cache.get(key)
            if cached is None:
                cached = torch.tensor(value, dtype=target, device=self.device)
                self._scalar_cache[key] = cached
            return cached

        if isinstance(value, np.ndarray):
            if dtype is not None:
                target = dtype
            elif value.dtype == np.bool_:
                target = torch.bool
            elif np.issubdtype(value.dtype, np.integer):
                target = torch.int32 if value.dtype == np.int32 else torch.int64
            else:
                target = self.dtype
            return torch.as_tensor(value, dtype=target).to(device=self.device)

        target = dtype if dtype is not None else self.dtype
        return torch.as_tensor(value, dtype=target).to(device=self.device)

    def abs(self, x: Any) -> torch.Tensor:
        """Return elementwise absolute value."""
        return torch.abs(self._to_tensor(x))

    def any(self, x: Any, axis: int | None = None) -> torch.Tensor:
        """Return whether any element is truthy, optionally along an axis."""
        t = self._to_tensor(x, dtype=torch.bool)
        if axis is None:
            return torch.any(t)
        return torch.any(t, dim=axis)

    def asarray(
        self,
        x: Any,
        dtype: torch.dtype | None = None,
    ) -> torch.Tensor:
        """Convert input to a tensor on the target device and dtype."""
        return self._to_tensor(x, dtype=dtype)

    def clip(self, x: Any, a_min: Any, a_max: Any) -> torch.Tensor:
        """Clamp tensor elements to ``[a_min, a_max]``."""
        t = self._to_tensor(x)
        lo = a_min if isinstance(a_min, (int, float)) else self._to_tensor(a_min)
        hi = a_max if isinstance(a_max, (int, float)) else self._to_tensor(a_max)
        return torch.clamp(t, min=lo, max=hi)

    def concatenate(
        self,
        arrays: Sequence[Any],
        axis: int = 0,
    ) -> torch.Tensor:
        """Concatenate tensors along ``axis``."""
        return torch.cat([self._to_tensor(a) for a in arrays], dim=axis)

    def exp(self, x: Any) -> torch.Tensor:
        """Return elementwise exponential."""
        return torch.exp(self._to_tensor(x))

    def full_like(
        self,
        x: Any,
        fill_value: Any,
        dtype: torch.dtype | None = None,
    ) -> torch.Tensor:
        """Return a tensor with the same shape as ``x`` filled with ``fill_value``."""
        return torch.full_like(self._to_tensor(x), fill_value, dtype=dtype)

    def log(self, x: Any) -> torch.Tensor:
        """Return elementwise natural logarithm."""
        return torch.log(self._to_tensor(x))

    def maximum(self, x: Any, y: Any) -> torch.Tensor:
        """Return elementwise maximum of two inputs."""
        tx = self._to_tensor(x)
        ty = self._to_tensor(y, dtype=tx.dtype)
        return torch.maximum(tx, ty)

    def minimum(self, x: Any, y: Any) -> torch.Tensor:
        """Return elementwise minimum of two inputs."""
        tx = self._to_tensor(x)
        ty = self._to_tensor(y, dtype=tx.dtype)
        return torch.minimum(tx, ty)

    def power(self, x: Any, y: Any) -> torch.Tensor:
        """Return elementwise ``x ** y``."""
        tx = self._to_tensor(x)
        if isinstance(y, (int, float)):
            return torch.pow(tx, y)
        return torch.pow(tx, self._to_tensor(y, dtype=tx.dtype))

    def sqrt(self, x: Any) -> torch.Tensor:
        """Return elementwise square root."""
        return torch.sqrt(self._to_tensor(x))

    def stack(self, arrays: Sequence[Any], axis: int = 0) -> torch.Tensor:
        """Stack tensors along a new ``axis``."""
        return torch.stack([self._to_tensor(a) for a in arrays], dim=axis)

    def sum(
        self,
        x: Any,
        axis: int | None = None,
        keepdims: bool = False,
        dtype: torch.dtype | None = None,
    ) -> torch.Tensor:
        """Sum tensor elements, optionally along an axis."""
        t = self._to_tensor(x)
        if axis is None:
            if dtype is None:
                return torch.sum(t)
            return torch.sum(t, dtype=dtype)
        if dtype is None:
            return torch.sum(t, dim=axis, keepdim=keepdims)
        return torch.sum(t, dim=axis, keepdim=keepdims, dtype=dtype)

    def where(self, condition: Any, x: Any, y: Any) -> torch.Tensor:
        """Select elements from ``x`` where ``condition`` is True, else ``y``."""
        cond = self._to_tensor(condition, dtype=torch.bool)
        if isinstance(x, torch.Tensor) and isinstance(y, torch.Tensor):
            tx = self._to_tensor(x)
            ty = self._to_tensor(y, dtype=tx.dtype)
        elif isinstance(x, torch.Tensor):
            tx = self._to_tensor(x)
            ty = self._to_tensor(y, dtype=tx.dtype)
        elif isinstance(y, torch.Tensor):
            ty = self._to_tensor(y)
            tx = self._to_tensor(x, dtype=ty.dtype)
        elif isinstance(x, bool) and isinstance(y, bool):
            tx = self._to_tensor(x, dtype=torch.bool)
            ty = self._to_tensor(y, dtype=torch.bool)
        else:
            tx = self._to_tensor(x, dtype=self.dtype)
            ty = self._to_tensor(y, dtype=self.dtype)
        return torch.where(cond, tx, ty)
