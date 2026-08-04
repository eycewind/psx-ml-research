from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from psx_ml.c10.inputs import (
    load_c10_selections,
    load_p4_selections,
)
from psx_ml.c10.policies import FROZEN_POLICIES


def _write_parquet(
    frame: pd.DataFrame,
    path: Path,
) -> None:
    table = pa.Table.from_pandas(
        frame,
        preserve_index=False,
    )
    with path.open("wb") as handle:
        pq.write_table(
            table,
            handle,
        )


def _base_frame(policy_id: str) -> pd.DataFrame:
    return pd.DataFrame(
        {
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
            "selection_tail": ["top"],
        }
    )


def test_frozen_policies_include_p4() -> None:
    assert set(FROZEN_POLICIES) == {
        "P1_broad_canonical",
        "P2_conservative_consensus",
        "P4_kmi30_strict",
    }


def test_load_p4_rejects_nonmember(
    tmp_path: Path,
) -> None:
    frame = _base_frame(
        "P4_kmi30_strict"
    )
    frame["kmi30_member"] = False

    path = tmp_path / "p4.parquet"
    _write_parquet(frame, path)

    with pytest.raises(
        ValueError,
        match="non-KMI-30",
    ):
        load_p4_selections(path)


def test_combined_loader_excludes_old_p3(
    tmp_path: Path,
) -> None:
    c9 = pd.concat(
        [
            _base_frame(
                "P1_broad_canonical"
            ),
            _base_frame(
                "P2_conservative_consensus"
            ),
            _base_frame(
                "P3_high_conviction"
            ),
        ],
        ignore_index=True,
    )

    p4 = _base_frame(
        "P4_kmi30_strict"
    )
    p4["kmi30_member"] = True

    c9_path = tmp_path / "c9.parquet"
    p4_path = tmp_path / "p4.parquet"

    _write_parquet(c9, c9_path)
    _write_parquet(p4, p4_path)

    result = load_c10_selections(
        c9_path=c9_path,
        p4_path=p4_path,
    )

    assert set(
        result["policy_id"]
    ) == {
        "P1_broad_canonical",
        "P2_conservative_consensus",
        "P4_kmi30_strict",
    }
