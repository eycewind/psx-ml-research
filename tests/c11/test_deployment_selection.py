import pandas as pd

from psx_ml.c11.deployment_selection import (
    _sector_capped_scan,
    attach_gate,
)


def _history() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "symbol": ["AAA", "BBB", "CCC", "DDD"],
            "effective_from": pd.to_datetime(
                ["2024-01-01"] * 4
            ),
            "effective_to": [pd.NaT] * 4,
            "screening_snapshot_date": pd.to_datetime(
                ["2024-01-01"] * 4
            ),
            "membership_source": ["fixture"] * 4,
            "membership_confidence": ["high", "high", "low", "high"],
            "is_shariah_screened_eligible": [True, False, True, True],
        }
    )


def test_gate_rejects_non_compliant_and_flags_low_confidence() -> None:
    rows = pd.DataFrame(
        {
            "trade_date": pd.to_datetime(
                ["2025-01-02", "2025-01-02", "2025-01-02"]
            ),
            "symbol": ["AAA", "BBB", "CCC"],
        }
    )
    result = attach_gate(rows, _history())
    assert result["shariah_eligible"].tolist() == [True, False, True]
    assert result["low_confidence_flag"].tolist() == [False, False, True]


def test_gate_rejects_unknown() -> None:
    rows = pd.DataFrame(
        {
            "trade_date": pd.to_datetime(["2025-01-02"]),
            "symbol": ["ZZZ"],
        }
    )
    result = attach_gate(rows, _history())
    assert not bool(result.iloc[0]["shariah_eligible"])
    assert result.iloc[0]["gate_status"] == "rejected_unknown"


def test_sector_capped_scan_continues_down_ranking_to_refill() -> None:
    candidates = pd.DataFrame(
        {
            "symbol": ["A", "B", "C", "D", "E"],
            "sector": ["S1", "S1", "S1", "S2", "S3"],
            "prediction_percentile_rank": [1.00, 0.99, 0.98, 0.97, 0.96],
        }
    )
    selected = _sector_capped_scan(
        candidates,
        target_count=4,
        sector_cap=2,
    )
    assert selected["symbol"].tolist() == ["A", "B", "D", "E"]


def test_sector_cap_never_exceeds_two() -> None:
    candidates = pd.DataFrame(
        {
            "symbol": ["A", "B", "C", "D"],
            "sector": ["S1", "S1", "S1", "S2"],
            "prediction_percentile_rank": [1.00, 0.99, 0.98, 0.97],
        }
    )
    selected = _sector_capped_scan(
        candidates,
        target_count=4,
        sector_cap=2,
    )
    assert selected.groupby("sector").size().max() <= 2
    assert len(selected) == 3


def test_direct_parquet_reader_filters_without_dataset_and_preserves_nulls(
    tmp_path,
) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    from psx_ml.c11.deployment_selection import _read_parquet_rows_direct

    path = tmp_path / "fixture.parquet"
    table = pa.table(
        {
            "task_type": ["rank", "other", "rank"],
            "value": [1, 2, 3],
            "sector": ["CEMENT", "BANK", None],
        }
    )
    with path.open("wb") as handle:
        pq.write_table(table, handle)

    rows = _read_parquet_rows_direct(
        path,
        columns=["value", "sector"],
        filters=[("task_type", "=", "rank")],
    )
    assert rows == [
        {"value": 1, "sector": "CEMENT"},
        {"value": 3, "sector": None},
    ]


def test_p4_authoritative_membership_survives_missing_secondary_history() -> None:
    from psx_ml.c11.deployment_selection import build_p4_authoritative_passthrough

    source = pd.DataFrame(
        {
            "policy_id": ["P4_kmi30_strict"],
            "trade_date": pd.to_datetime(["2025-08-11"]),
            "symbol": ["ENGROH"],
            "kmi30_member": [True],
            "effective_from": pd.to_datetime(["2025-06-02"]),
            "effective_to": ["2025-11-23"],
            "review_as_of": pd.to_datetime(["2024-12-31"]),
            "notice_date": pd.to_datetime(["2025-05-23"]),
            "notice_no": ["PSX/N-545"],
        }
    )
    empty_history = pd.DataFrame(
        {
            "symbol": pd.Series(dtype="str"),
            "effective_from": pd.Series(dtype="datetime64[ns]"),
            "effective_to": pd.Series(dtype="datetime64[ns]"),
            "screening_snapshot_date": pd.Series(dtype="datetime64[ns]"),
            "membership_source": pd.Series(dtype="str"),
            "membership_confidence": pd.Series(dtype="str"),
            "is_shariah_screened_eligible": pd.Series(dtype="bool"),
        }
    )

    selected, audit = build_p4_authoritative_passthrough(
        source,
        empty_history,
    )
    assert len(selected) == 1
    assert selected.iloc[0]["gate_status"] == "eligible_authoritative_kmi30"
    assert selected.iloc[0]["shariah_source"] == "official_psx_kmi30_membership"
    assert audit.iloc[0]["screen_history_gate_status"] == "rejected_unknown"


def test_attach_gate_overwrites_existing_provenance_without_duplicate_columns() -> None:
    rows = pd.DataFrame(
        {
            "trade_date": pd.to_datetime(["2025-01-02"]),
            "symbol": ["AAA"],
            "shariah_eligible": [False],
            "gate_status": ["stale_value"],
            "shariah_source": ["old_source"],
            "shariah_confidence": ["old"],
            "screening_snapshot_date": ["1900-01-01"],
            "screening_effective_from": ["1900-01-01"],
            "screening_effective_to": [None],
            "low_confidence_flag": [False],
            "gate_reason": ["old_reason"],
        }
    )
    result = attach_gate(rows, _history())

    assert result.columns.is_unique
    assert bool(result.iloc[0]["shariah_eligible"])
    assert result.iloc[0]["gate_status"] == "eligible"
    assert result.iloc[0]["shariah_source"] == "fixture"
