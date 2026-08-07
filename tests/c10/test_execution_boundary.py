from pathlib import Path

import pandas as pd

from psx_ml.c10.inputs import (
    LAST_PRE_HOLDOUT_DATE,
    load_execution_prices,
)


def _price_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "trade_date": [
                "2025-12-29",
                "2025-12-30",
                "2025-12-31",
                "2026-01-02",
            ],
            "symbol": ["AAA"] * 4,
            "open_adj": [100.0, 101.0, 102.0, 103.0],
            "high_adj": [101.0, 102.0, 103.0, 104.0],
            "low_adj": [99.0, 100.0, 101.0, 102.0],
            "close_adj": [100.5, 101.5, 102.5, 103.5],
            "volume_adj": [1000.0] * 4,
            "adj_factor": [1.0] * 4,
        }
    )


def test_prices_extend_beyond_signal_but_stop_before_holdout(
    monkeypatch,
) -> None:
    frame = _price_frame()

    def fake_read_parquet(path, columns=None):
        assert Path(path) == Path("dummy.parquet")
        if columns is None:
            return frame.copy()
        return frame.loc[:, columns].copy()

    monkeypatch.setattr(pd, "read_parquet", fake_read_parquet)

    loaded = load_execution_prices(
        path=Path("dummy.parquet"),
        maximum_date=LAST_PRE_HOLDOUT_DATE,
    )

    assert loaded["trade_date"].max() == pd.Timestamp("2025-12-31")
    assert not (loaded["trade_date"] >= pd.Timestamp("2026-01-01")).any()


def test_requested_maximum_is_hard_capped_before_holdout(
    monkeypatch,
) -> None:
    frame = _price_frame()

    def fake_read_parquet(path, columns=None):
        assert Path(path) == Path("dummy.parquet")
        if columns is None:
            return frame.copy()
        return frame.loc[:, columns].copy()

    monkeypatch.setattr(pd, "read_parquet", fake_read_parquet)

    loaded = load_execution_prices(
        path=Path("dummy.parquet"),
        maximum_date=pd.Timestamp("2026-12-31"),
    )

    assert loaded["trade_date"].max() == pd.Timestamp("2025-12-31")
    assert loaded["trade_date"].tolist() == [
        pd.Timestamp("2025-12-29"),
        pd.Timestamp("2025-12-30"),
        pd.Timestamp("2025-12-31"),
    ]