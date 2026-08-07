from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from psx_ml.c10.inputs import load_p5_selections


def _write(frame: pd.DataFrame, path: Path) -> None:
    table = pa.Table.from_pandas(frame, preserve_index=False)
    with path.open("wb") as handle:
        pq.write_table(table, handle)


def _frame(policy_id: str = "P5_shariah_screened") -> pd.DataFrame:
    return pd.DataFrame({
        "policy_id": [policy_id],
        "trade_date": ["2025-01-06"],
        "symbol": ["AAA"],
        "fold_id": ["fold_2025"],
        "horizon": [5],
        "target_family": ["market_relative"],
        "feature_variant": ["B_market_context"],
        "model_name": ["lightgbm_cpu"],
        "prediction": [0.9],
        "sector": ["TEST"],
        "selection_date": ["2025-01-06"],
    })


def test_p5_loader_normalizes_selection_tail(tmp_path: Path) -> None:
    path = tmp_path / "p5.parquet"
    _write(_frame(), path)
    result = load_p5_selections(path)
    assert result.loc[0, "selection_tail"] == "top"


def test_p5_loader_rejects_wrong_policy(tmp_path: Path) -> None:
    path = tmp_path / "p5.parquet"
    _write(_frame("P1_broad_canonical"), path)
    with pytest.raises(ValueError, match="P5 selection file"):
        load_p5_selections(path)


def test_p5_loader_rejects_holdout(tmp_path: Path) -> None:
    frame = _frame()
    frame["trade_date"] = "2026-01-05"
    frame["selection_date"] = "2026-01-05"
    path = tmp_path / "p5.parquet"
    _write(frame, path)
    with pytest.raises(ValueError, match="holdout"):
        load_p5_selections(path)
