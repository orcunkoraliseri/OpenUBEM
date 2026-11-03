import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

from scripts.paper import retrofit_check as rc


def test_population_is_8129():
    n_all, pop = rc.load_population()
    assert n_all == 8139
    assert len(pop) == rc.EXPECTED_POPULATION
    assert pop["osm_id"].is_unique


def test_setback_rule_matches_logged_counts():
    rows, total, changed, mean_hours, per_arch = rc.build_rows()
    assert total == 8129
    by = {r["archetype_id"]: r for r in rows if r["row_type"] == "archetype_population"}
    assert sum(r["n_buildings"] for r in by.values()) == 8129
    cross = next(r for r in rows if r["row_type"] == "crosscheck")
    assert cross["n_buildings"] == rc.LOGGED_FLEET07B["setback_changed"]
    gated = sum(by[a]["n_buildings"] for a, r in per_arch.items() if r["status"].startswith("gate_no_setback_block"))
    assert gated + 10 * 0 == rc.LOGGED_FLEET07B["setback_gate_no_setback_block"]


def test_heating_change_is_a_few_hundredths_of_a_kelvin():
    r = rc.setback_on_archetype("SmallOffice")
    assert r["status"] == "applied"
    assert r["cooling_status"] == "already_compliant"
    assert abs((r["before"] - r["after"]) - 0.0556) < 1e-3
    assert r["hours_lowered"] == 2860.0
