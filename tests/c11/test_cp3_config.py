from psx_ml.c11.checkpoint3 import (
    CAPITAL_GRID,
    POLICIES,
    PRIMARY_SCENARIO_ID,
    SCENARIOS,
)


def test_cp3_reuses_cp1_capital_grid_and_policy_set() -> None:
    assert CAPITAL_GRID == (
        50_000.0,
        100_000.0,
        250_000.0,
        500_000.0,
        1_000_000.0,
    )
    assert set(POLICIES) == {
        "P1_broad_canonical",
        "P2_conservative_consensus",
        "P4_kmi30_strict",
        "P5_shariah_screened",
    }


def test_cp3_primary_rule_is_frozen_at_two_percent_touch_fill() -> None:
    primary = [row for row in SCENARIOS if row[0] == PRIMARY_SCENARIO_ID]
    assert primary == [
        ("touch_2pct_primary", "touch_fill", 0.02, True)
    ]


def test_cp3_sensitivities_do_not_mark_another_primary() -> None:
    assert sum(bool(row[3]) for row in SCENARIOS) == 1
    assert {row[2] for row in SCENARIOS} == {0.01, 0.02, 0.03}
    assert {row[1] for row in SCENARIOS} == {"touch_fill", "open_only"}
