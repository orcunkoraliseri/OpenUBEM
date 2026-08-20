"""OPEN-35 T04 (PLAN_board-17-ready-2026-08-19.md, director ruling 4.4a): unit tests
proving `derive_num_floors()` (openubem/geometry/footprint.py) and `_impute_levels()`
(openubem/semantic/building_classifier.py) agree on the Scope B population -- buildings
with no observed `levels` and no `height_m`, whose fired archetype rule actually
consumed the group-/global-median levels fallback (archetype_source carries a
GROUPMEDIAN_LEVELS_MED token) -- while leaving every other row (Scope B's complement)
on the old, unaffected behaviour.
"""
import math

import pandas as pd

from openubem.geometry.footprint import derive_num_floors
from openubem.semantic.building_classifier import _impute_levels


def _row(**kwargs) -> pd.Series:
    base = {"levels": float("nan"), "height_m": float("nan"), "archetype_source": None}
    base.update(kwargs)
    return pd.Series(base)


class TestStoreyFallbackAgreement:
    def test_both_fallbacks_agree_no_storeys_no_height(self):
        row = _row(archetype_source="RULE_RESIDENTIAL_TIER,GROUPMEDIAN_LEVELS_MED")
        group_median = {"residential": 7}
        global_median = 5

        lev, lev_src = _impute_levels(
            row,
            use_class="residential",
            levels_group_median=group_median,
            levels_global_median=global_median,
        )
        n_floors = derive_num_floors(
            row,
            use_class="residential",
            levels_group_median=group_median,
            levels_global_median=global_median,
        )

        assert lev_src == "GROUPMEDIAN_LEVELS_MED"
        assert lev == 7
        assert n_floors == 7
        assert n_floors == lev

    def test_both_fallbacks_agree_falls_back_to_global_median(self):
        row = _row(archetype_source="RULE_LODGING_TIER,GROUPMEDIAN_LEVELS_MED")
        group_median: dict = {}
        global_median = 12

        lev, lev_src = _impute_levels(
            row, use_class="commercial",
            levels_group_median=group_median, levels_global_median=global_median,
        )
        n_floors = derive_num_floors(
            row, use_class="commercial",
            levels_group_median=group_median, levels_global_median=global_median,
        )

        assert lev_src == "GROUPMEDIAN_LEVELS_MED"
        assert n_floors == lev == 12

    def test_building_with_storey_data_unaffected(self):
        row_levels = _row(levels=5, archetype_source="RULE_RESIDENTIAL_TIER,GROUPMEDIAN_LEVELS_MED")
        group_median = {"residential": 7}
        assert derive_num_floors(row_levels, use_class="residential", levels_group_median=group_median) == 5
        lev, lev_src = _impute_levels(row_levels, use_class="residential", levels_group_median=group_median)
        assert (lev, lev_src) == (5, "OSM_OBSERVED")

        row_height = _row(height_m=10.5, archetype_source="RULE_LODGING_TIER,GROUPMEDIAN_LEVELS_MED")
        assert derive_num_floors(row_height, use_class="commercial", levels_group_median={"commercial": 20}) == 3
        lev2, lev_src2 = _impute_levels(row_height, use_class="commercial", levels_group_median={"commercial": 20})
        assert (lev2, lev_src2) == (3, "HEURISTIC_HEIGHT")

    def test_cell_with_no_storey_data_at_all_returns_1_from_both(self):
        row = _row(archetype_source="RULE_RESIDENTIAL_TIER,LEVELS_DEFAULT_LOW")
        lev, lev_src = _impute_levels(row, use_class="residential", levels_group_median={}, levels_global_median=None)
        n_floors = derive_num_floors(row, use_class="residential", levels_group_median={}, levels_global_median=None)

        assert lev_src == "LEVELS_DEFAULT_LOW"
        assert lev == 1
        assert n_floors == 1

        row_no_kwargs = _row(archetype_source="RULE_RESIDENTIAL_TIER,LEVELS_DEFAULT_LOW")
        assert derive_num_floors(row_no_kwargs) == 1

    def test_scope_b_excludes_rules_that_never_consumed_the_median(self):
        # RULE_USE_CLASS_SIZE never reads levels_imputed at all (not in _LEVELS_CONSUMING),
        # so archetype_source never carries a GROUPMEDIAN_LEVELS_MED token for it, even
        # though both levels and height_m are missing here. This is the Scope A/Scope B
        # boundary (director ruling 4.4a): Scope A would apply the median to every
        # both-missing row regardless of archetype_source; Scope B must not.
        row = _row(archetype_source="RULE_USE_CLASS_SIZE")
        n_floors = derive_num_floors(
            row, use_class="commercial",
            levels_group_median={"commercial": 30}, levels_global_median=30,
        )
        assert n_floors == 1

    def test_scope_b_excludes_osm_observed_levels_source(self):
        # If archetype_source somehow lacked the GROUPMEDIAN token but levels/height were
        # both missing (shouldn't happen given the classifier's own invariant, but the
        # gate must not assume it), the fallback must not fire.
        row = _row(archetype_source="RULE_HIGHRISE")
        n_floors = derive_num_floors(
            row, use_class="residential",
            levels_group_median={"residential": 40}, levels_global_median=40,
        )
        assert n_floors == 1

    def test_missing_archetype_source_key_is_safe(self):
        # Pre-existing callers/tests never populate archetype_source at all.
        row = pd.Series({"levels": float("nan"), "height_m": float("nan")})
        assert derive_num_floors(row) == 1
        assert derive_num_floors(row, use_class="residential", levels_group_median={"residential": 7}) == 1
