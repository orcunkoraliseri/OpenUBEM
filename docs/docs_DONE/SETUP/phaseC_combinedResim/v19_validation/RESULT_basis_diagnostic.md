# RESULT — V19 Basis Diagnostic Sweep

## Grid specification

- `cooling_cop` ∈ [1.0, 2.5, 3.0, 3.5, 4.0]
- `heating_factor` ∈ [1.0, 1.19]
- `lighting_scale` ∈ [1.0, 0.8, 0.6, 0.5]
- `equipment_scale` ∈ [1.0, 0.7, 0.5]
- Total combos: 120 (5 × 2 × 4 × 3)
- Identity combo (1.0, 1.0, 1.0, 1.0) present: True

## Load-scaling caveat (verbatim from plan §3)

> Basis transform is exact for COP/fuel; a lower bound for loads. Dividing thermal cooling by a COP and multiplying thermal heating by a fuel factor are exact in post-processing. Scaling lighting_eui/equipment_eui is only a direct scaling of those columns — it cannot propagate the reduced internal gain into a lower cooling load (that needs a resim). Therefore load-scaling results are a lower bound on the true benefit.

## Top-10 combos by max_abs_delta (ascending)

| cooling_cop | heating_factor | lighting_scale | equipment_scale | nyc_office_delta | nyc_overall_delta | la_office_delta | la_overall_delta | austin_office_delta | austin_overall_delta | max_abs_delta | sumsq_delta | n_within_15 | n_within_20 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2.5 | 1.19 | 0.8 | 0.7 | 12.2 | -7.7 | 11.3 | -13.0 | -12.5 | -11.7 | 13.0 | 797.96 | 6 | 6 |
| 2.5 | 1.0 | 0.6 | 1.0 | 3.7 | -12.6 | 12.3 | -1.3 | -13.5 | -12.8 | 13.5 | 671.52 | 6 | 6 |
| 2.5 | 1.19 | 0.5 | 1.0 | 12.9 | -4.6 | 13.7 | 0.9 | -11.4 | -10.7 | 13.7 | 620.52 | 6 | 6 |
| 3.5 | 1.19 | 0.8 | 1.0 | 13.1 | -5.2 | 11.2 | -3.7 | -14.5 | -13.8 | 14.5 | 738.47 | 6 | 6 |
| 3.0 | 1.19 | 0.6 | 1.0 | 11.6 | -5.6 | 10.5 | -2.4 | -14.6 | -14.0 | 14.6 | 691.09 | 6 | 6 |
| 3.5 | 1.0 | 1.0 | 1.0 | 5.7 | -12.1 | 12.2 | -5.5 | -14.6 | -14.0 | 14.6 | 767.15 | 6 | 6 |
| 4.0 | 1.19 | 1.0 | 1.0 | 14.9 | -4.3 | 13.0 | -4.4 | -13.4 | -12.8 | 14.9 | 772.26 | 6 | 6 |
| 3.0 | 1.0 | 0.8 | 1.0 | 4.2 | -12.8 | 11.4 | -3.9 | -14.9 | -14.2 | 14.9 | 750.3 | 6 | 6 |
| 2.5 | 1.0 | 1.0 | 0.7 | 4.8 | -15.0 | 11.4 | -15.2 | -12.7 | -12.0 | 15.2 | 914.33 | 5 | 6 |
| 2.5 | 1.0 | 0.5 | 1.0 | 2.0 | -13.6 | 9.7 | -2.2 | -15.4 | -14.7 | 15.4 | 741.14 | 5 | 6 |

## Best-global combo

Parameters: cooling_cop=2.5, heating_factor=1.19, lighting_scale=0.8, equipment_scale=0.7
max_abs_delta: 13.00%  |  sumsq_delta: 797.96  |  n_within_15: 6.0  |  n_within_20: 6.0

### Six-segment signed-delta table

| city | segment | signed_delta_pct |
| --- | --- | --- |
| nyc | Office | 12.2 |
| nyc | Overall | -7.7 |
| la | Office | 11.3 |
| la | Overall | -13.0 |
| austin | Office | -12.5 |
| austin | Overall | -11.7 |

## Per-city climate-aware ceiling

(Best max_abs_delta over that city's two anchors, allowing any cooling_cop in the grid.)

| city | best_achievable_max_abs_delta_pct |
| --- | --- |
| nyc | 8.2 |
| la | 6.0 |
| austin | 1.8 |

## Coherence verdict metrics

- Best-global n_within_15 (anchors within ±15%): 6 / 6
- Best-global n_within_20 (anchors within ±20%): 6 / 6
- NYC Overall signed delta (best-global): -7.70%
- LA Overall signed delta (best-global):  -13.00%
- NYC and LA Overall on opposite signs: False
- Identity max_abs_delta: 78.40%
