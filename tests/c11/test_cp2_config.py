from psx_ml.c11.checkpoint2 import CAPITAL_GRID, POLICIES


def test_cp2_capital_grid_is_cp1_frozen_grid() -> None:
    assert CAPITAL_GRID == (50_000.0, 100_000.0, 250_000.0, 500_000.0, 1_000_000.0)


def test_cp2_policy_set_is_frozen_c10_set() -> None:
    assert set(POLICIES) == {
        "P1_broad_canonical",
        "P2_conservative_consensus",
        "P4_kmi30_strict",
        "P5_shariah_screened",
    }


def test_cp2_c10_comparison_is_explicitly_reference_only() -> None:
    source = __import__("inspect").getsource(
        __import__(
            "psx_ml.c11.checkpoint2",
            fromlist=["main"],
        ).main
    )
    assert "annualized_return_delta_vs_c10_reference" in source
    assert "reference/reconciliation metric" in source
    assert "not a pure whole-share drag measurement" in source
