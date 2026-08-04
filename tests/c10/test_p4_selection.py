import pandas as pd

from psx_ml.c10.p4_selection import (
    P4SelectionConfig,
    attach_kmi30_membership,
    build_p4_selections,
    select_top_percentile_with_sector_cap,
)


def test_membership_is_point_in_time() -> None:
    predictions = pd.DataFrame(
        {
            "trade_date": [
                "2024-01-01",
                "2024-01-01",
                "2024-07-01",
                "2024-07-01",
            ],
            "symbol": [
                "OLD",
                "NEW",
                "OLD",
                "NEW",
            ],
            "prediction": [
                0.9,
                0.8,
                0.9,
                0.8,
            ],
        }
    )

    membership = pd.DataFrame(
        {
            "symbol": ["OLD", "NEW"],
            "effective_from": [
                "2023-01-01",
                "2024-06-01",
            ],
            "effective_to": [
                "2024-05-31",
                "9999-12-31",
            ],
        }
    )

    result = attach_kmi30_membership(
        predictions,
        membership,
    )

    pairs = set(
        zip(
            result["trade_date"].dt.date.astype(str),
            result["symbol"],
        )
    )

    assert pairs == {
        ("2024-01-01", "OLD"),
        ("2024-07-01", "NEW"),
    }


def test_top_ten_percent_uses_ceiling() -> None:
    rows = pd.DataFrame(
        {
            "symbol": [
                f"S{i:02d}"
                for i in range(21)
            ],
            "prediction": [
                float(100 - i)
                for i in range(21)
            ],
            "sector": [
                f"SEC{i:02d}"
                for i in range(21)
            ],
        }
    )

    result = select_top_percentile_with_sector_cap(
        rows,
        P4SelectionConfig(
            percentile=0.10,
            sector_cap=2,
        ),
    )

    assert len(result) == 3


def test_sector_cap_refills_from_lower_ranked_names() -> None:
    rows = pd.DataFrame(
        {
            "symbol": ["A", "B", "C", "D"],
            "prediction": [4.0, 3.0, 2.0, 1.0],
            "sector": ["X", "X", "X", "Y"],
        }
    )

    result = select_top_percentile_with_sector_cap(
        rows,
        P4SelectionConfig(
            percentile=0.75,
            sector_cap=2,
        ),
    )

    assert result["symbol"].tolist() == [
        "A",
        "B",
        "D",
    ]


def test_p4_never_selects_non_member() -> None:
    predictions = pd.DataFrame(
        {
            "trade_date": [
                "2025-01-06",
                "2025-01-06",
            ],
            "symbol": ["MEM", "NON"],
            "fold_id": ["f", "f"],
            "horizon": [5, 5],
            "target_family": [
                "market_relative_rank",
                "market_relative_rank",
            ],
            "feature_variant": [
                "B_market_context",
                "B_market_context",
            ],
            "model_name": [
                "lightgbm_cpu",
                "lightgbm_cpu",
            ],
            "prediction": [0.5, 0.9],
            "sector": ["A", "B"],
        }
    )

    membership = pd.DataFrame(
        {
            "symbol": ["MEM"],
            "effective_from": ["2024-01-01"],
            "effective_to": ["9999-12-31"],
        }
    )

    result = build_p4_selections(
        predictions=predictions,
        membership=membership,
        weekly_signal_dates=pd.Series(
            ["2025-01-06"]
        ),
    )

    assert result["symbol"].tolist() == [
        "MEM"
    ]
    assert result["kmi30_member"].all()
