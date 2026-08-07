import pandas as pd

from psx_ml.c10.p5_selection import (
    P5Config,
    _select_one_date,
)


def _frame():
    return pd.DataFrame(
        {
            "trade_date": pd.to_datetime(["2025-01-06"] * 8),
            "symbol": list("ABCDEFGH"),
            "prediction": [.9, .8, .7, .6, .5, .4, .3, .2],
            "sector": ["X", "X", "X", "Y", "Y", "Z", "Z", "Q"],
            "turnover_median_20obs_adj": [
                800, 700, 600, 500, 400, 300, 200, 100
            ],
        }
    )


def test_liquidity_filter_excludes_bottom_quarter():
    selected = _select_one_date(
        _frame(),
        P5Config(selection_fraction=1.0, sector_cap=99),
    )
    assert set(selected["symbol"]) == set("ABCDEF")


def test_sector_cap_is_enforced():
    selected = _select_one_date(
        _frame(),
        P5Config(selection_fraction=1.0, sector_cap=2),
    )
    assert selected.groupby("sector").size().max() <= 2


def test_selection_is_deterministic():
    first = _select_one_date(_frame(), P5Config())
    second = _select_one_date(
        _frame().sample(frac=1.0, random_state=123),
        P5Config(),
    )
    assert first["symbol"].tolist() == second["symbol"].tolist()
