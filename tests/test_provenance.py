"""T01 — canonical imputation provenance contract (openubem/semantic/provenance.py)."""
import numpy as np
import pandas as pd
import pytest

from openubem.semantic import provenance as prov


class TestImputeToken:
    def test_plan_example_default(self):
        assert prov.impute_token("DEFAULT", "ASHRAE901", "LOW") == "DEFAULT_ASHRAE901_LOW"

    def test_plan_example_hotdeck_med(self):
        # MEDIUM canonical tier -> short 'MED' suffix (M09 §3A / plan T01)
        assert prov.impute_token("HOTDECK", "NEIGHBOR", "MEDIUM") == "HOTDECK_NEIGHBOR_MED"

    def test_uppercases_inputs(self):
        assert prov.impute_token("groupmedian", "levels", "med") == "GROUPMEDIAN_LEVELS_MED"

    def test_invalid_confidence_raises(self):
        with pytest.raises(ValueError):
            prov.impute_token("DEFAULT", "ASHRAE901", "SORTA")

    @pytest.mark.parametrize("method,source,conf", [
        ("DEFAULT", "ASHRAE901", "LOW"),
        ("HOTDECK", "NEIGHBOR", "MEDIUM"),
        ("GROUPMODE", "USE_CLASS", "HIGH"),          # source with an underscore
        ("DEFAULT", "ASHRAE901_COOLING_COP", "LOW"),  # multi-underscore source
    ])
    def test_round_trip(self, method, source, conf):
        tok = prov.impute_token(method, source, conf)
        parsed = prov.parse_token(tok)
        assert parsed == (method.upper(), source.upper(), prov.normalize_confidence(conf))

    def test_parse_non_token_returns_none(self):
        assert prov.parse_token("VINTAGE_NAN_PERMISSIVE_DEFAULT") is None  # no tier suffix
        assert prov.parse_token("ASHRAE_STANDARD") is None
        assert prov.parse_token("") is None


class TestAppendFlag:
    def test_append_to_empty(self):
        assert prov.append_flag_token("", "Z") == "Z"

    def test_append_to_none_and_nan(self):
        assert prov.append_flag_token(None, "Z") == "Z"
        assert prov.append_flag_token(float("nan"), "Z") == "Z"

    def test_append_new(self):
        assert prov.append_flag_token("A", "B") == "A|B"

    def test_idempotent_no_duplicate(self):
        assert prov.append_flag_token("X|Y", "X") == "X|Y"
        assert prov.append_flag_token("X|Y", "Y") == "X|Y"

    def test_append_flag_vectorized_with_mask(self):
        df = pd.DataFrame({"data_quality_flag": ["", "A", "B"]})
        mask = pd.Series([True, False, True])
        out = prov.append_flag(df, "TOK", mask=mask)
        assert list(out["data_quality_flag"]) == ["TOK", "A", "B|TOK"]

    def test_append_flag_creates_column_if_missing(self):
        df = pd.DataFrame({"x": [1, 2]})
        out = prov.append_flag(df, "TOK")
        assert list(out["data_quality_flag"]) == ["TOK", "TOK"]


class TestSetProvenance:
    def test_sets_column_and_confidence(self):
        df = pd.DataFrame({"x": [1, 2, 3]})
        mask = pd.Series([True, False, True])
        tok = prov.impute_token("DEFAULT", "ASHRAE901", "LOW")
        out = prov.set_provenance(df, "cooling_cop", tok, mask=mask, confidence="LOW")
        assert out.loc[0, "provenance_cooling_cop"] == tok
        assert out.loc[2, "provenance_cooling_cop"] == tok
        assert out.loc[0, "confidence_cooling_cop"] == "LOW"


class TestLineageSummary:
    def _frame(self):
        HIGH = prov.impute_token("GROUPMODE", "USECLASS", "HIGH")   # weight 1.0
        MED = prov.impute_token("HOTDECK", "NEIGHBOR", "MEDIUM")    # weight 0.5
        LOW_A = prov.impute_token("DEFAULT", "GEOMETRY_AREA", "LOW")  # weight 0.1
        LOW_L = prov.impute_token("GROUPMEDIAN", "LEVELS", "LOW")     # weight 0.1
        return pd.DataFrame({
            "provenance_a": ["", LOW_A, MED, "ASHRAE_STANDARD", LOW_L],
            "provenance_b": ["", "", HIGH, "", LOW_A],
        })

    def test_counts_and_confidence(self):
        # Row 3 ("ASHRAE_STANDARD" | "") is now imputed-LOW-0.1, not observed-1.0
        # (LEGACY_TOKEN_WEIGHT reweight, T07.1): count 0->1, conf 1.0 -> (0.1+1.0)/2.
        out = prov.add_lineage_summary(self._frame())
        assert list(out["imputed_fields_count"]) == [0, 1, 2, 1, 2]
        expected = [1.0, (0.1 + 1.0) / 2, (0.5 + 1.0) / 2, (0.1 + 1.0) / 2, (0.1 + 0.1) / 2]
        np.testing.assert_allclose(out["mean_imputation_confidence"].to_numpy(), expected)

    def test_observed_only_rows_score_one(self):
        # "ASHRAE_STANDARD" is now imputed-LOW-0.1 (LEGACY_TOKEN_WEIGHT, T07.1), so row 1
        # is no longer observed-only: count 0->1, conf 1.0 -> (0.1+1.0)/2 = 0.55.
        df = pd.DataFrame({
            "provenance_a": ["", "ASHRAE_STANDARD"],
            "provenance_b": [None, ""],
        })
        out = prov.add_lineage_summary(df)
        assert list(out["imputed_fields_count"]) == [0, 1]
        np.testing.assert_allclose(out["mean_imputation_confidence"].to_numpy(), [1.0, (0.1 + 1.0) / 2])

    def test_no_provenance_columns_default_one(self):
        df = pd.DataFrame({"x": [1, 2]})
        out = prov.add_lineage_summary(df)
        assert list(out["imputed_fields_count"]) == [0, 0]
        assert list(out["mean_imputation_confidence"]) == [1.0, 1.0]

    def test_explicit_prov_cols(self):
        df = pd.DataFrame({
            "provenance_x": [prov.impute_token("DEFAULT", "ASHRAE901", "LOW")],
            "other": ["ignored"],
        })
        out = prov.add_lineage_summary(df, prov_cols=["provenance_x"])
        assert out.loc[0, "imputed_fields_count"] == 1
        assert out.loc[0, "mean_imputation_confidence"] == 0.1

    def test_legacy_token_weights_pinned(self):
        # Ratified T07.1 grades: KDE_IMPUTED/HEURISTIC -> MED 0.5; PDE_GENERATED/
        # ASHRAE_STANDARD -> LOW 0.1 (all imputed, none observed-grade 1.0).
        expected = {
            "KDE_IMPUTED": 0.5,
            "HEURISTIC": 0.5,
            "PDE_GENERATED": 0.1,
            "ASHRAE_STANDARD": 0.1,
        }
        for token, weight in expected.items():
            assert prov._field_score(token) == (True, weight)

        df = pd.DataFrame({"provenance_a": list(expected.keys())})
        out = prov.add_lineage_summary(df, prov_cols=["provenance_a"])
        assert list(out["imputed_fields_count"]) == [1, 1, 1, 1]
        np.testing.assert_allclose(
            out["mean_imputation_confidence"].to_numpy(), list(expected.values())
        )
