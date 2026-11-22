from typing import Any

import numpy as np

from openubem.gpusim.physics.psychro import KELVIN_CONV


def calc_interior_rad_exchange(
    t_surf_in: Any,
    script_f_sigma: Any,
    eps_in: Any,
    is_window: Any,
    surf_mask: Any,
    xp: Any = np,
) -> tuple[Any, Any]:
    """HeatBalanceIntRadExchange.cc::CalcInteriorRadExchange"""
    t_k = t_surf_in + KELVIN_CONV
    t_k2 = t_k * t_k
    t_k4 = t_k2 * t_k2

    t_send = t_k[:, None, :]
    t_rec = t_k[:, :, None]
    t_send2 = t_k2[:, None, :]
    t_rec2 = t_k2[:, :, None]
    diff_t4 = (t_send - t_rec) * (t_send + t_rec) * (t_send2 + t_rec2)

    q_net_lw = xp.sum(script_f_sigma * diff_t4, axis=-1)
    q_net_lw = xp.where(surf_mask, q_net_lw, 0.0)

    ir_acc = xp.sum(script_f_sigma * t_k4[:, None, :], axis=-1)
    safe_eps = xp.where(is_window & surf_mask, xp.maximum(eps_in, 1.0e-12), 1.0)
    ir_from_parent = xp.where(is_window & surf_mask, ir_acc / safe_eps, 0.0)

    return q_net_lw, ir_from_parent
