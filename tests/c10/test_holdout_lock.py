import pandas as pd
import pytest

from psx_ml.c10.inputs import assert_no_holdout


def test_holdout_rows_are_rejected() -> None:
    frame = pd.DataFrame(
        {
            "trade_date": [
                "2025-12-31",
                "2026-01-02",
            ]
        }
    )

    with pytest.raises(ValueError, match="holdout"):
        assert_no_holdout(frame)


def test_pre_holdout_rows_are_allowed() -> None:
    frame = pd.DataFrame(
        {
            "trade_date": [
                "2023-01-02",
                "2025-12-31",
            ]
        }
    )

    assert_no_holdout(frame)
