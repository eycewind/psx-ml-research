from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class CapacityScenario:
    scenario_id: str
    portfolio_capital: float
    participation_rate: float
    base_capital: float = 1_000_000.0

    def to_dict(self) -> dict[str, float | str]:
        return asdict(self)


CAPITAL_LEVELS = (
    1_000_000.0,
    5_000_000.0,
    10_000_000.0,
    25_000_000.0,
    50_000_000.0,
)

PARTICIPATION_RATES = (
    0.05,
    0.10,
    0.20,
)


CAPACITY_SCENARIOS = tuple(
    CapacityScenario(
        scenario_id=(
            f"capital_{int(capital):d}"
            f"_participation_{int(rate * 100):d}pct"
        ),
        portfolio_capital=capital,
        participation_rate=rate,
    )
    for capital in CAPITAL_LEVELS
    for rate in PARTICIPATION_RATES
)


def validate_scenario(
    scenario: CapacityScenario,
) -> None:
    numeric = {
        "portfolio_capital": scenario.portfolio_capital,
        "participation_rate": scenario.participation_rate,
        "base_capital": scenario.base_capital,
    }

    for name, value in numeric.items():
        if not np.isfinite(value) or value <= 0:
            raise ValueError(
                f"{name} must be finite and greater than zero"
            )

    if scenario.participation_rate > 1:
        raise ValueError(
            "participation_rate cannot exceed 1"
        )


def attach_point_in_time_liquidity(
    trades: pd.DataFrame,
    liquidity: pd.DataFrame,
) -> pd.DataFrame:
    """
    Attach the latest valid symbol liquidity observation available on or
    before each trade's signal date.

    This is a backward as-of join and therefore never uses execution-day
    or future turnover. Missing/non-positive observations are excluded
    before matching. A trade receives zero capacity only when no valid
    prior observation exists for that symbol.
    """
    required_trades = {
        "policy_id",
        "signal_date",
        "trade_date",
        "symbol",
        "notional",
    }
    missing_trades = sorted(
        required_trades - set(trades.columns)
    )
    if missing_trades:
        raise ValueError(
            f"Trade ledger missing required columns: {missing_trades}"
        )

    required_liquidity = {
        "trade_date",
        "symbol",
        "turnover_median_20obs_adj",
    }
    missing_liquidity = sorted(
        required_liquidity - set(liquidity.columns)
    )
    if missing_liquidity:
        raise ValueError(
            "Liquidity frame missing required columns: "
            f"{missing_liquidity}"
        )

    trade_frame = trades.copy()
    trade_frame["signal_date"] = pd.to_datetime(
        trade_frame["signal_date"],
        errors="raise",
    ).dt.normalize()
    trade_frame["trade_date"] = pd.to_datetime(
        trade_frame["trade_date"],
        errors="raise",
    ).dt.normalize()

    trade_frame["_original_order"] = np.arange(
        len(trade_frame),
        dtype=np.int64,
    )

    liquidity_frame = liquidity.copy()
    liquidity_frame["trade_date"] = pd.to_datetime(
        liquidity_frame["trade_date"],
        errors="raise",
    ).dt.normalize()

    if liquidity_frame.duplicated(
        ["trade_date", "symbol"]
    ).any():
        raise ValueError(
            "Liquidity frame contains duplicate date-symbol rows"
        )

    turnover = pd.to_numeric(
        liquidity_frame["turnover_median_20obs_adj"],
        errors="coerce",
    )

    liquidity_frame = liquidity_frame.loc[
        turnover.notna()
        & np.isfinite(turnover)
        & (turnover > 0),
        ["trade_date", "symbol", "turnover_median_20obs_adj"],
    ].copy()

    liquidity_frame = liquidity_frame.rename(
        columns={
            "trade_date": "liquidity_date",
            "turnover_median_20obs_adj": (
                "reference_turnover_20obs"
            ),
        }
    )

    # pandas.merge_asof requires both sides to be ordered by the
    # as-of key, with the grouping key used as a secondary sort.
    left = trade_frame.sort_values(
        ["signal_date", "symbol", "_original_order"]
    ).reset_index(drop=True)

    right = liquidity_frame.sort_values(
        ["liquidity_date", "symbol"]
    ).reset_index(drop=True)

    result = pd.merge_asof(
        left,
        right,
        left_on="signal_date",
        right_on="liquidity_date",
        by="symbol",
        direction="backward",
        allow_exact_matches=True,
    )

    future_liquidity = (
        result["liquidity_date"].notna()
        & (
            result["liquidity_date"]
            > result["signal_date"]
        )
    )
    if future_liquidity.any():
        raise ValueError(
            "Future liquidity data was joined to trades"
        )

    reference = pd.to_numeric(
        result["reference_turnover_20obs"],
        errors="coerce",
    )

    result["liquidity_available"] = (
        result["liquidity_date"].notna()
        & reference.notna()
        & np.isfinite(reference)
        & (reference > 0)
    )

    result["reference_turnover_20obs"] = (
        reference.where(
            result["liquidity_available"],
            0.0,
        )
    )

    result["liquidity_age_calendar_days"] = np.where(
        result["liquidity_available"],
        (
            result["signal_date"]
            - result["liquidity_date"]
        ).dt.days,
        np.nan,
    )

    result["liquidity_exact_date_match"] = (
        result["liquidity_available"]
        & (
            result["liquidity_date"]
            == result["signal_date"]
        )
    )

    result["liquidity_missing_reason"] = pd.NA
    result.loc[
        ~result["liquidity_available"],
        "liquidity_missing_reason",
    ] = "no_valid_current_or_prior_turnover"

    result = (
        result.sort_values("_original_order")
        .drop(columns=["_original_order"])
        .reset_index(drop=True)
    )

    return result



def evaluate_capacity_scenario(
    trades_with_liquidity: pd.DataFrame,
    scenario: CapacityScenario,
) -> pd.DataFrame:
    validate_scenario(scenario)

    required = {
        "policy_id",
        "trade_date",
        "signal_date",
        "symbol",
        "notional",
        "reference_turnover_20obs",
        "liquidity_available",
    }
    missing = sorted(
        required - set(trades_with_liquidity.columns)
    )
    if missing:
        raise ValueError(
            f"Capacity input missing required columns: {missing}"
        )

    result = trades_with_liquidity.copy()

    notional = pd.to_numeric(
        result["notional"],
        errors="raise",
    )
    if (
        notional.isna().any()
        or (~np.isfinite(notional)).any()
        or (notional < 0).any()
    ):
        raise ValueError(
            "Trade ledger contains invalid notional"
        )

    capital_multiplier = (
        scenario.portfolio_capital
        / scenario.base_capital
    )

    result["scenario_id"] = (
        scenario.scenario_id
    )
    result["portfolio_capital"] = (
        scenario.portfolio_capital
    )
    result["participation_rate"] = (
        scenario.participation_rate
    )
    result["capital_multiplier"] = (
        capital_multiplier
    )

    result["scaled_trade_notional"] = (
        notional * capital_multiplier
    )

    result["capacity_notional"] = (
        result["reference_turnover_20obs"]
        * scenario.participation_rate
    )

    result["fill_ratio"] = np.where(
        result["scaled_trade_notional"] > 0,
        np.minimum(
            1.0,
            result["capacity_notional"]
            / result["scaled_trade_notional"],
        ),
        1.0,
    )

    result["fill_ratio"] = (
        result["fill_ratio"]
        .clip(lower=0.0, upper=1.0)
    )

    result["capacity_executed_notional"] = (
        result["scaled_trade_notional"]
        * result["fill_ratio"]
    )
    result["capacity_unfilled_notional"] = (
        result["scaled_trade_notional"]
        - result["capacity_executed_notional"]
    )

    result["fully_feasible"] = (
        result["fill_ratio"] >= 1.0 - 1e-12
    )
    result["capacity_breach"] = (
        ~result["fully_feasible"]
    )

    result["participation_required"] = np.where(
        result["reference_turnover_20obs"] > 0,
        (
            result["scaled_trade_notional"]
            / result["reference_turnover_20obs"]
        ),
        np.inf,
    )

    result["maximum_supported_capital"] = np.where(
        notional > 0,
        (
            scenario.base_capital
            * result["capacity_notional"]
            / notional
        ),
        np.inf,
    )

    return result


def summarize_capacity(
    diagnostics: pd.DataFrame,
) -> pd.DataFrame:
    required = {
        "scenario_id",
        "policy_id",
        "trade_date",
        "symbol",
        "scaled_trade_notional",
        "capacity_executed_notional",
        "capacity_unfilled_notional",
        "fill_ratio",
        "fully_feasible",
        "capacity_breach",
        "liquidity_available",
        "maximum_supported_capital",
    }
    missing = sorted(
        required - set(diagnostics.columns)
    )
    if missing:
        raise ValueError(
            f"Diagnostics missing required columns: {missing}"
        )

    rows: list[dict[str, object]] = []

    for (
        scenario_id,
        policy_id,
    ), group in diagnostics.groupby(
        ["scenario_id", "policy_id"],
        sort=True,
    ):
        scaled_notional = float(
            group["scaled_trade_notional"].sum()
        )
        executed_notional = float(
            group[
                "capacity_executed_notional"
            ].sum()
        )
        unfilled_notional = float(
            group[
                "capacity_unfilled_notional"
            ].sum()
        )

        supported = (
            group.loc[
                np.isfinite(
                    group[
                        "maximum_supported_capital"
                    ]
                ),
                "maximum_supported_capital",
            ]
            .astype(float)
        )

        rows.append(
            {
                "scenario_id": scenario_id,
                "policy_id": policy_id,
                "portfolio_capital": float(
                    group.iloc[0][
                        "portfolio_capital"
                    ]
                ),
                "participation_rate": float(
                    group.iloc[0][
                        "participation_rate"
                    ]
                ),
                "trade_count": int(
                    len(group)
                ),
                "fully_feasible_trades": int(
                    group[
                        "fully_feasible"
                    ].sum()
                ),
                "capacity_breach_trades": int(
                    group[
                        "capacity_breach"
                    ].sum()
                ),
                "fully_feasible_fraction": float(
                    group[
                        "fully_feasible"
                    ].mean()
                ),
                "liquidity_available_fraction": float(
                    group[
                        "liquidity_available"
                    ].mean()
                ),
                "scaled_trade_notional": (
                    scaled_notional
                ),
                "capacity_executed_notional": (
                    executed_notional
                ),
                "capacity_unfilled_notional": (
                    unfilled_notional
                ),
                "notional_fill_fraction": (
                    executed_notional
                    / scaled_notional
                    if scaled_notional > 0
                    else 1.0
                ),
                "mean_fill_ratio": float(
                    group[
                        "fill_ratio"
                    ].mean()
                ),
                "median_fill_ratio": float(
                    group[
                        "fill_ratio"
                    ].median()
                ),
                "breach_date_count": int(
                    group.loc[
                        group["capacity_breach"],
                        "trade_date",
                    ].nunique()
                ),
                "minimum_supported_capital": (
                    float(supported.min())
                    if len(supported)
                    else 0.0
                ),
                "capital_99pct_trades_feasible": (
                    float(supported.quantile(0.01))
                    if len(supported)
                    else 0.0
                ),
                "capital_95pct_trades_feasible": (
                    float(supported.quantile(0.05))
                    if len(supported)
                    else 0.0
                ),
                "median_supported_capital": (
                    float(supported.median())
                    if len(supported)
                    else 0.0
                ),
            }
        )

    return pd.DataFrame(rows)


def build_policy_capacity_limits(
    attached_trades: pd.DataFrame,
    participation_rates: tuple[float, ...] = (
        0.05,
        0.10,
        0.20,
    ),
    base_capital: float = 1_000_000.0,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for rate in participation_rates:
        scenario = CapacityScenario(
            scenario_id=(
                f"capacity_limit_"
                f"{int(rate * 100)}pct"
            ),
            portfolio_capital=base_capital,
            participation_rate=rate,
            base_capital=base_capital,
        )

        diagnostics = evaluate_capacity_scenario(
            attached_trades,
            scenario,
        )

        for policy_id, group in diagnostics.groupby(
            "policy_id",
            sort=True,
        ):
            supported = group.loc[
                np.isfinite(
                    group[
                        "maximum_supported_capital"
                    ]
                ),
                "maximum_supported_capital",
            ].astype(float)

            rows.append(
                {
                    "policy_id": policy_id,
                    "participation_rate": rate,
                    "trade_count": int(
                        len(group)
                    ),
                    "minimum_supported_capital": (
                        float(supported.min())
                        if len(supported)
                        else 0.0
                    ),
                    "capital_99pct_trades_feasible": (
                        float(
                            supported.quantile(0.01)
                        )
                        if len(supported)
                        else 0.0
                    ),
                    "capital_95pct_trades_feasible": (
                        float(
                            supported.quantile(0.05)
                        )
                        if len(supported)
                        else 0.0
                    ),
                    "capital_90pct_trades_feasible": (
                        float(
                            supported.quantile(0.10)
                        )
                        if len(supported)
                        else 0.0
                    ),
                    "median_supported_capital": (
                        float(supported.median())
                        if len(supported)
                        else 0.0
                    ),
                }
            )

    return pd.DataFrame(rows)
