"""T15 - pedestrian wind field (PLAN §7 T15).

Two tiers, selected by config.UTCI_WIND_TIER:

- "cost730" (default). Open-terrain logarithmic profile, the COST Action 730 UTCI operational
  convention: v_1.1 = v_10 * ln(1.1/z0)/ln(10/z0), z0 = 0.01 m (U02 §2.2 line 97; Broede et al.
  2012). Spatially uniform.
- "macdonald". Macdonald, Griffiths & Hall (1998) empirical morphometric in-canopy drag model,
  using plan-area density (lambda_p) and frontal-area density (lambda_f) derived from the
  building footprints on a moving window (U02 §2.2 lines 100-105). Captures the general
  reduction of pedestrian wind in built-up areas relative to open terrain. It does NOT resolve
  corner vortices, downdrafts, or recirculating canyon eddies -- those need CFD (U02 §3.2 line
  129; U04 §3.1 line 144; §12 of the plan). This is a stated limitation, not a hidden one.

Binding OpenUBEM wind convention (§4.2 of the plan) -- applies identically to BOTH tiers:

1. v_1.1 is the physically meaningful pedestrian field: computed spatially, exported, plotted.
2. Before entering the UTCI polynomial, convert each cell back to its 10 m open-terrain
   equivalent using the SAME COST-730 log profile: va10_eq = v_1.1 / 0.680, where
   0.680 = ln(1.1/0.01)/ln(10/0.01) at z0 = 0.01 m (U02 §2.2 line 97) -- computed here from the
   cited z0 and pedestrian-height constants, not hardcoded, so the 0.680 figure stays derived.
3. Clamp AFTER conversion, to [0.5, 17.0] m/s (P-01's polynomial domain).
4. Export both v_1.1 and va10_eq.

Macdonald (1998) morphometric constants (Macdonald, R.W., Griffiths, R.F., & Hall, D.J. (1998).
"An Empirical Model for the Estimation of Mean Velocity Profiles Within and Above Urban
Canopies." Atmospheric Environment, 32(11), 1857-1865):
    d/H  = 1 + alpha^(-lambda_p) * (lambda_p - 1)                         [displacement height]
    z0/H = (1 - d/H) * exp( -[0.5*beta*(Cd/kappa^2)*(1-d/H)*lambda_f]^-0.5 )   [roughness length]
    a    = 0.5 * lambda_f^0.5 * (H/z0)^0.25                          [in-canopy attenuation coeff]
    v(z) = v_H * exp(a*(z/H - 1))                                        [in-canopy profile]
with alpha=4.43, beta=1.0 (staggered-array fit, Macdonald et al. 1998, verified directly against
the primary paper's own reproduced equations), Cd=1.2 (assumed bluff-body building drag
coefficient, same source), kappa=0.4 (von Karman constant -- standard boundary-layer
meteorology, Oke 1987, already the primary source cited for domain.py's material properties).
v_H (wind speed at canopy top H) is obtained by extrapolating the open-terrain log profile to
height H using the SAME displaced/roughened (d, z0) pair: v_H = v10 * ln((H-d)/z0)/ln((10-d)/z0).

Where a window has no buildings (lambda_p ~ 0), d/H's own formula already evaluates to 0
(alpha^0 * (0-1) + 1 = 0) but z0/H degenerates (0/0) with lambda_f also ~0 -- guarded explicitly
by falling back to (d=0, z0=z0_open_m), which makes v_H's log-law and the in-canopy profile's
z<=H branch below both collapse EXACTLY onto the cost730 open-field formula. This is the
required "lambda_p=0 -> reduces to the log profile" behaviour (T15 "How to test"), not a patch
over a bug.

E-UTCI-07 domain-validity fallback (manager-adjudicated 2026-07-24, PLAN §7 T15 / §10): v_H's
own extrapolation ("v10 * ln((H-d)/z0)/ln((10-d)/z0)") implicitly assumes the 10 m meteorological
reference sits ABOVE the urban canopy -- i.e. that d stays well below 10 m. Real mid/high-rise
stock (e.g. nyc_centre, mean height 41.9 m) routinely violates that: d approaches or exceeds 10 m,
and the denominator log_10_over_z0 -> 0, producing values orders of magnitude outside physical
plausibility (measured up to ~400,000 m/s on real data). The code already has a floor that stops
the log argument going negative: `max(10.0 - d, ped_height_m)`. Per the adjudication, whenever
THAT SAME existing floor condition would engage (10.0 - d <= ped_height_m) -- exactly the point
where "10 m sits above the canopy" stops being true -- the in-canopy macdonald formula is not
evaluated for that cell at all; the cell falls back to the cost730 open-terrain log profile
instead (a documented degradation to the tier's own safer baseline, not a new physical model, and
not a new tunable constant -- the threshold IS the formula's own pre-existing floor). Every
caller must count how often this fires (wind_macdonald_domain_invalid_cell_hours in the run
manifest) -- the same "honest gap, not a silent default" convention as T09's DSM-height-exclusion
count.

E-UTCI-08 postcondition sanity check (manager-adjudicated 2026-07-24, PLAN §7 T15 / §10): the
E-UTCI-07 fallback above catches one specific route to log_10_over_z0 -> 0 (the floor colliding
with a large d), but not a structurally different second route -- z0 landing coincidentally close
to (10-d) by numerical accident, reachable even where d is nowhere near 10 m and the domain-
validity trigger never fires (measured on nyc_centre: up to ~142,000 m/s at cells where
domain_invalid=False). Rather than chase further routes to the same catastrophic-cancellation
class one at a time, a POSTCONDITION check is applied after v_1p1 is computed (and after the
E-UTCI-07 fallback substitution above): if v_1p1 violates the physically-necessary bound
`0 <= v_1p1 <= v10` (in-canopy wind cannot exceed or reverse the free-stream reference), it is
discarded and the cost730 value is used instead -- regardless of which numerical route produced
the violation. This is a strict superset of the E-UTCI-07 fallback (anything that trigger catches
also violates this bound) and does not depend on enumerating every route to the cancellation. It
is NOT the "clamp log_10_over_z0 directly" pattern E-UTCI-07 rejected as candidate (c): that
pattern still trusted and used a value computed from an ill-conditioned division; this pattern
discards the macdonald output entirely once it has already shown to violate a bound that is
physically required. Counted separately from the E-UTCI-07 fallback
(wind_macdonald_numerical_anomaly_cell_hours in the run manifest, kept DISTINCT from
wind_macdonald_domain_invalid_cell_hours) -- one reports genuine physical-domain inapplicability,
the other reports numerical near-singularities caught by this safety net; conflating them would
lose real diagnostic information about how much of a domain this tier can actually serve.
"""
from __future__ import annotations

import numpy as np

from openubem import config

# Macdonald, Griffiths & Hall (1998) -- staggered-array fit, verified against the primary paper's
# own reproduced displacement-height/roughness-length equations.
ALPHA_MACDONALD = 4.43
BETA_MACDONALD = 1.0
CD_MACDONALD = 1.2       # assumed bluff-body building drag coefficient, same source
KAPPA_VON_KARMAN = 0.4   # Oke (1987) -- standard boundary-layer-meteorology constant

_TINY = 1e-9


def cost730_factor(ped_height_m: float = config.UTCI_PEDESTRIAN_HEIGHT_M,
                    z0_open_m: float = config.UTCI_Z0_OPEN_M) -> float:
    """ln(ped_height/z0)/ln(10/z0) -- derived from the cited constants, not hardcoded (U02 §2.2
    line 97 quotes the resulting ratio as ~0.680 at the default 1.1 m / 0.01 m values)."""
    return float(np.log(ped_height_m / z0_open_m) / np.log(10.0 / z0_open_m))


def pedestrian_wind_cost730(v10_ms, shape,
                             ped_height_m: float = config.UTCI_PEDESTRIAN_HEIGHT_M,
                             z0_open_m: float = config.UTCI_Z0_OPEN_M):
    """Open-terrain COST-730 log profile, spatially uniform. v10_ms: scalar or array broadcastable
    to shape."""
    factor = cost730_factor(ped_height_m, z0_open_m)
    v10 = np.asarray(v10_ms, dtype=np.float64)
    v_1p1 = np.full(shape, 1.0, dtype=np.float64) * v10 * factor
    return v_1p1


def morphometric_parameters(buildings_gdf, domain, wind_direction_deg: float,
                             window_radius_m: float = 50.0):
    """Plan-area density (lambda_p), frontal-area density (lambda_f, direction-dependent) and
    mean building height (H), each as a raster on domain's grid, from a square moving window of
    half-width window_radius_m (a spatial-averaging SCALE the caller chooses, like the domain's
    own grid resolution -- not a cited physical constant).

    lambda_p: standard plan-area-density definition (Grimmond & Oke 1999) -- building footprint
    area / window plan area, from domain.building_mask.
    lambda_f: frontal-area-density definition (Grimmond & Oke 1999; Burian et al. 2002,
    "Morphological Analyses Using 3D Building Databases") -- for each building, its footprint is
    projected onto the axis perpendicular to the wind's direction of travel; the projected width
    times the building height is its frontal area. Per-building frontal area is spread evenly
    over its own footprint pixels (a raster discretisation choice, not a new physical parameter),
    then summed over the moving window and divided by the window's plan area.
    wind_direction_deg: EPW convention -- degrees clockwise from north, direction the wind is
    blowing FROM.
    """
    from rasterio import features
    from scipy.ndimage import uniform_filter

    shape = domain.shape
    transform = domain.transform
    res_m = domain.res_m
    window_px = max(1, int(round((2.0 * window_radius_m) / res_m)))

    mask_f = domain.building_mask.astype(np.float64)
    lambda_p = uniform_filter(mask_f, size=window_px, mode="constant")

    theta = np.radians(wind_direction_deg)
    travel = np.array([-np.sin(theta), -np.cos(theta)])   # (east, north) -- direction air travels
    perp = np.array([travel[1], -travel[0]])              # perpendicular axis, for frontal width

    frontal_raster = np.zeros(shape, dtype=np.float64)
    height_raster = np.zeros(shape, dtype=np.float64)
    if buildings_gdf is not None and len(buildings_gdf) > 0 and "height_m" in buildings_gdf.columns:
        gdf = buildings_gdf[buildings_gdf["height_m"].notna()]
        for geom, height in zip(gdf.geometry, gdf["height_m"].astype(float)):
            footprint_mask = features.rasterize(
                [(geom, 1)], out_shape=shape, transform=transform, fill=0, dtype="uint8"
            ).astype(bool)
            n_px = int(footprint_mask.sum())
            if n_px == 0:
                continue
            xs, ys = np.asarray(geom.exterior.coords).T
            proj = xs * perp[0] + ys * perp[1]
            frontal_width_m = float(proj.max() - proj.min())
            frontal_area = height * frontal_width_m
            frontal_raster[footprint_mask] += frontal_area / n_px
            height_raster[footprint_mask] = height

    window_area_m2 = (window_px * res_m) ** 2
    frontal_sum = uniform_filter(frontal_raster, size=window_px, mode="constant") * (window_px ** 2)
    lambda_f = frontal_sum / window_area_m2

    height_weighted = uniform_filter(height_raster * mask_f, size=window_px, mode="constant")
    mean_height_m = np.divide(
        height_weighted, lambda_p, out=np.zeros_like(lambda_p), where=lambda_p > _TINY
    )

    return lambda_p, lambda_f, mean_height_m


def pedestrian_wind_macdonald(v10_ms, lambda_p, lambda_f, mean_height_m,
                               ped_height_m: float = config.UTCI_PEDESTRIAN_HEIGHT_M,
                               z0_open_m: float = config.UTCI_Z0_OPEN_M):
    """Macdonald (1998) in-canopy drag profile -> v(1.1 m). See module docstring for the full
    derivation and citations, including the E-UTCI-07 domain-validity fallback and the E-UTCI-08
    postcondition sanity check, both applied below.
    lambda_p, lambda_f, mean_height_m: rasters from morphometric_parameters(); v10_ms: scalar or
    array broadcastable to their shape.

    Returns (v_1p1, domain_invalid_mask, numerical_anomaly_mask):
    - domain_invalid_mask: boolean array, True at every cell where the code's own existing floor
      condition (10.0 - d <= ped_height_m) engaged -- i.e. where the "10 m reference sits above
      the canopy" assumption the extrapolation depends on is no longer physically valid. At those
      cells v_1p1 is the cost730 open-terrain fallback, NOT the in-canopy macdonald formula
      (E-UTCI-07, PLAN §7 T15 / §10, manager-adjudicated 2026-07-24).
    - numerical_anomaly_mask: boolean array, True at every cell where the (already
      domain-invalid-substituted) v_1p1 still violated the physically-necessary bound
      `0 <= v_1p1 <= v10` -- a distinct, numerically-triggered near-singularity, not domain
      inapplicability (E-UTCI-08, PLAN §7 T15 / §10, manager-adjudicated 2026-07-24). At those
      cells v_1p1 is also the cost730 open-terrain fallback. Mutually exclusive with
      domain_invalid_mask by construction: domain-invalid cells already carry the cost730
      fallback, which always satisfies the bound, so they never additionally trip this check.
    """
    lambda_p = np.asarray(lambda_p, dtype=np.float64)
    lambda_f = np.asarray(lambda_f, dtype=np.float64)
    height_m = np.asarray(mean_height_m, dtype=np.float64)
    v10 = np.broadcast_to(np.asarray(v10_ms, dtype=np.float64), lambda_p.shape)

    open_field = lambda_p <= _TINY
    lambda_p_safe = np.clip(lambda_p, _TINY, 1.0 - _TINY)
    lambda_f_safe = np.maximum(lambda_f, _TINY)

    d_over_h = 1.0 + ALPHA_MACDONALD ** (-lambda_p_safe) * (lambda_p_safe - 1.0)
    z0_over_h = (1.0 - d_over_h) * np.exp(
        -1.0 / np.sqrt(0.5 * BETA_MACDONALD * (CD_MACDONALD / KAPPA_VON_KARMAN ** 2)
                       * (1.0 - d_over_h) * lambda_f_safe)
    )
    height_safe = np.maximum(height_m, ped_height_m)
    d = np.where(open_field, 0.0, d_over_h * height_safe)
    z0 = np.where(open_field, z0_open_m, np.maximum(z0_over_h * height_safe, z0_open_m * 1e-3))

    # E-UTCI-07: this IS the pre-existing floor condition -- reused verbatim as the
    # domain-validity trigger, not a new tunable constant. Open-field cells (d=0) never engage it
    # (10.0 > ped_height_m always), so the fallback is confined to the in-canopy branch.
    domain_invalid = (10.0 - d) <= ped_height_m

    log_10_over_z0 = np.log(np.maximum(10.0 - d, ped_height_m) / z0)
    v_h = v10 * np.log(np.maximum(height_safe - d, _TINY) / z0) / log_10_over_z0

    a_coeff = 0.5 * np.sqrt(lambda_f_safe) * (height_safe / z0) ** 0.25
    in_canopy = v_h * np.exp(a_coeff * (ped_height_m / height_safe - 1.0))

    log_law_at_ped = v10 * np.log(np.maximum(ped_height_m - d, _TINY) / z0) / log_10_over_z0

    below_canopy_top = height_safe > ped_height_m
    v_1p1_macdonald = np.where(
        open_field, log_law_at_ped, np.where(below_canopy_top, in_canopy, log_law_at_ped)
    )

    v_1p1_fallback = pedestrian_wind_cost730(v10, lambda_p.shape, ped_height_m, z0_open_m)
    v_1p1_domain_checked = np.where(domain_invalid, v_1p1_fallback, v_1p1_macdonald)

    # E-UTCI-08 postcondition sanity check: discard any output (from either branch above) that
    # violates the physically-necessary bound 0 <= v_1p1 <= v10, regardless of which numerical
    # route produced the violation, and fall back to cost730 -- counted separately from
    # domain_invalid (module docstring). Domain-invalid cells already carry v_1p1_fallback, which
    # always satisfies the bound (factor in [0, 1], v10 >= 0), so `& ~domain_invalid` keeps the
    # two counters strictly non-overlapping rather than relying on that implicitly.
    bound_violated = (v_1p1_domain_checked < 0.0) | (v_1p1_domain_checked > v10 + _TINY)
    numerical_anomaly = bound_violated & ~domain_invalid
    v_1p1 = np.where(numerical_anomaly, v_1p1_fallback, v_1p1_domain_checked)
    return v_1p1, domain_invalid, numerical_anomaly


# flags bitmask (pedestrian_wind / _macdonald_wind, both callers -- keep in sync)
WIND_FLAG_VA10_CLAMPED = 0x01
WIND_FLAG_MACDONALD_DOMAIN_INVALID = 0x02  # E-UTCI-07 fallback engaged this cell/hour
WIND_FLAG_MACDONALD_NUMERICAL_ANOMALY = 0x04  # E-UTCI-08 postcondition check engaged this cell/hour


def pedestrian_wind(v10_ms, shape, *,
                     tier: str = None,
                     buildings_gdf=None, domain=None, wind_direction_deg: float = None,
                     window_radius_m: float = 50.0,
                     ped_height_m: float = config.UTCI_PEDESTRIAN_HEIGHT_M,
                     z0_open_m: float = config.UTCI_Z0_OPEN_M):
    """Dispatcher -- returns (v_1p1, va10_eq, flags), the binding §4.2 pair for every tier.
    flags: uint8 bitmask -- WIND_FLAG_VA10_CLAMPED (0x01) fired below 0.5 m/s or above 17.0 m/s;
    WIND_FLAG_MACDONALD_DOMAIN_INVALID (0x02, macdonald tier only) fired where E-UTCI-07's
    cost730 fallback engaged instead of the in-canopy formula; WIND_FLAG_MACDONALD_NUMERICAL_ANOMALY
    (0x04, macdonald tier only) fired where E-UTCI-08's postcondition sanity check discarded a
    bound-violating macdonald output and used the cost730 fallback instead."""
    tier = tier or config.UTCI_WIND_TIER
    domain_invalid = None
    numerical_anomaly = None
    if tier == "cost730":
        v_1p1 = pedestrian_wind_cost730(v10_ms, shape, ped_height_m, z0_open_m)
    elif tier == "macdonald":
        if buildings_gdf is None or domain is None or wind_direction_deg is None:
            raise ValueError("pedestrian_wind(tier='macdonald') requires buildings_gdf, domain, "
                              "and wind_direction_deg")
        lambda_p, lambda_f, mean_height_m = morphometric_parameters(
            buildings_gdf, domain, wind_direction_deg, window_radius_m
        )
        v_1p1, domain_invalid, numerical_anomaly = pedestrian_wind_macdonald(
            v10_ms, lambda_p, lambda_f, mean_height_m, ped_height_m, z0_open_m
        )
    else:
        raise ValueError(f"pedestrian_wind: unknown tier {tier!r}")

    factor = cost730_factor(ped_height_m, z0_open_m)
    va10_raw = v_1p1 / factor
    va10_eq = np.clip(va10_raw, 0.5, 17.0)
    flags = (np.asarray(va10_raw) != va10_eq).astype(np.uint8) * WIND_FLAG_VA10_CLAMPED
    if domain_invalid is not None:
        flags = flags | (np.asarray(domain_invalid).astype(np.uint8) * WIND_FLAG_MACDONALD_DOMAIN_INVALID)
    if numerical_anomaly is not None:
        flags = flags | (np.asarray(numerical_anomaly).astype(np.uint8) * WIND_FLAG_MACDONALD_NUMERICAL_ANOMALY)
    return v_1p1, va10_eq, flags
