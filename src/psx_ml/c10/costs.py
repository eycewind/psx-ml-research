from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class CostSchedule:
    schedule_id: str
    brokerage_rate: float
    brokerage_per_share: float
    sst_rate_on_brokerage: float = 0.0
    cdc_per_share: float = 0.0
    levy_rate_on_notional: float = 0.0
    fixed_cost_per_trade: float = 0.0

    def to_dict(self) -> dict[str, float | str]:
        return asdict(self)


# Regulatory minimum commission only.
PSX_MINIMUM_BROKERAGE = CostSchedule(
    schedule_id="psx_minimum_brokerage_only",
    brokerage_rate=0.0015,
    brokerage_per_share=0.03,
)


# User-observed live broker schedule from actual 2026 transaction records:
# commission = max(0.15% of notional, PKR 0.03/share)
# SST = 15% of commission
# CDC = PKR 0.005/share
ACTUAL_BROKER_ALL_IN = CostSchedule(
    schedule_id="actual_broker_all_in",
    brokerage_rate=0.0015,
    brokerage_per_share=0.03,
    sst_rate_on_brokerage=0.15,
    cdc_per_share=0.005,
)


ACTUAL_BROKER_20_BPS = CostSchedule(
    schedule_id="actual_broker_20bps",
    brokerage_rate=0.0020,
    brokerage_per_share=0.03,
    sst_rate_on_brokerage=0.15,
    cdc_per_share=0.005,
)


ACTUAL_BROKER_25_BPS = CostSchedule(
    schedule_id="actual_broker_25bps",
    brokerage_rate=0.0025,
    brokerage_per_share=0.03,
    sst_rate_on_brokerage=0.15,
    cdc_per_share=0.005,
)


COST_SCENARIOS = {
    schedule.schedule_id: schedule
    for schedule in (
        ACTUAL_BROKER_ALL_IN,
        PSX_MINIMUM_BROKERAGE,
        ACTUAL_BROKER_20_BPS,
        ACTUAL_BROKER_25_BPS,
    )
}


def validate_cost_schedule(schedule: CostSchedule) -> None:
    numeric_fields = {
        "brokerage_rate": schedule.brokerage_rate,
        "brokerage_per_share": schedule.brokerage_per_share,
        "sst_rate_on_brokerage": schedule.sst_rate_on_brokerage,
        "cdc_per_share": schedule.cdc_per_share,
        "levy_rate_on_notional": schedule.levy_rate_on_notional,
        "fixed_cost_per_trade": schedule.fixed_cost_per_trade,
    }

    for name, value in numeric_fields.items():
        if not np.isfinite(value) or value < 0:
            raise ValueError(
                f"Cost schedule field {name} must be finite and non-negative"
            )


def apply_trade_costs(
    trades: pd.DataFrame,
    schedule: CostSchedule,
) -> pd.DataFrame:
    validate_cost_schedule(schedule)

    required = {
        "policy_id",
        "trade_date",
        "symbol",
        "side",
        "shares",
        "notional",
    }
    missing = sorted(required - set(trades.columns))
    if missing:
        raise ValueError(
            f"Trade ledger missing required columns: {missing}"
        )

    result = trades.copy()
    result["trade_date"] = pd.to_datetime(
        result["trade_date"],
        errors="raise",
    ).dt.normalize()

    for column in ("shares", "notional"):
        values = pd.to_numeric(result[column], errors="raise")
        if (
            values.isna().any()
            or (~np.isfinite(values)).any()
            or (values < 0).any()
        ):
            raise ValueError(
                f"Trade ledger contains invalid {column}"
            )
        result[column] = values.astype(float)

    invalid_sides = sorted(
        set(result["side"].dropna().unique()) - {"BUY", "SELL"}
    )
    if invalid_sides:
        raise ValueError(
            f"Unexpected trade sides: {invalid_sides}"
        )

    result["brokerage_by_rate"] = (
        result["notional"] * schedule.brokerage_rate
    )
    result["brokerage_by_share"] = (
        result["shares"] * schedule.brokerage_per_share
    )
    result["brokerage"] = result[
        ["brokerage_by_rate", "brokerage_by_share"]
    ].max(axis=1)

    result["sst"] = (
        result["brokerage"] * schedule.sst_rate_on_brokerage
    )
    result["cdc"] = (
        result["shares"] * schedule.cdc_per_share
    )
    result["notional_levy"] = (
        result["notional"] * schedule.levy_rate_on_notional
    )
    result["fixed_trade_cost"] = schedule.fixed_cost_per_trade

    result["total_transaction_cost"] = (
        result["brokerage"]
        + result["sst"]
        + result["cdc"]
        + result["notional_levy"]
        + result["fixed_trade_cost"]
    )

    result["effective_cost_rate"] = np.where(
        result["notional"] > 0,
        result["total_transaction_cost"] / result["notional"],
        0.0,
    )

    result["cost_schedule_id"] = schedule.schedule_id

    return result


def build_costed_nav(
    *,
    gross_nav: pd.DataFrame,
    costed_trades: pd.DataFrame,
    starting_capital: float,
) -> pd.DataFrame:
    required_nav = {
        "policy_id",
        "trade_date",
        "nav_close",
        "daily_return",
    }
    missing_nav = sorted(required_nav - set(gross_nav.columns))
    if missing_nav:
        raise ValueError(
            f"Gross NAV missing required columns: {missing_nav}"
        )

    required_costs = {
        "policy_id",
        "trade_date",
        "total_transaction_cost",
        "cost_schedule_id",
    }
    missing_costs = sorted(
        required_costs - set(costed_trades.columns)
    )
    if missing_costs:
        raise ValueError(
            f"Costed trades missing required columns: {missing_costs}"
        )

    nav = gross_nav.copy()
    nav["trade_date"] = pd.to_datetime(
        nav["trade_date"],
        errors="raise",
    ).dt.normalize()

    trades = costed_trades.copy()
    trades["trade_date"] = pd.to_datetime(
        trades["trade_date"],
        errors="raise",
    ).dt.normalize()

    schedule_ids = sorted(
        trades["cost_schedule_id"].dropna().unique()
    )
    if len(schedule_ids) != 1:
        raise ValueError(
            "Costed trade frame must contain exactly one cost schedule"
        )

    daily_costs = (
        trades.groupby(
            ["policy_id", "trade_date"],
            as_index=False,
        )
        .agg(
            transaction_cost=("total_transaction_cost", "sum"),
            brokerage_cost=("brokerage", "sum"),
            sst_cost=("sst", "sum"),
            cdc_cost=("cdc", "sum"),
            notional_levy=("notional_levy", "sum"),
            fixed_trade_cost=("fixed_trade_cost", "sum"),
            traded_notional=("notional", "sum"),
            trade_count=("symbol", "size"),
        )
    )

    result = nav.merge(
        daily_costs,
        on=["policy_id", "trade_date"],
        how="left",
        validate="one_to_one",
    )

    numeric_cost_columns = [
        "transaction_cost",
        "brokerage_cost",
        "sst_cost",
        "cdc_cost",
        "notional_levy",
        "fixed_trade_cost",
        "traded_notional",
        "trade_count",
    ]
    result[numeric_cost_columns] = (
        result[numeric_cost_columns].fillna(0.0)
    )

    output_frames: list[pd.DataFrame] = []

    for policy_id, group in result.groupby(
        "policy_id",
        sort=False,
    ):
        ordered = (
            group.sort_values("trade_date")
            .reset_index(drop=True)
            .copy()
        )

        ordered["gross_nav_previous_close"] = (
            ordered["nav_close"]
            .shift(1)
            .fillna(float(starting_capital))
        )

        ordered["transaction_cost_fraction"] = (
            ordered["transaction_cost"]
            / ordered["gross_nav_previous_close"]
        )

        if (
            ordered["transaction_cost_fraction"] >= 1.0
        ).any():
            raise ValueError(
                f"Transaction costs consume all capital for {policy_id}"
            )

        ordered["net_daily_return"] = (
            (
                1.0
                - ordered["transaction_cost_fraction"]
            )
            * (
                1.0
                + ordered["daily_return"]
            )
            - 1.0
        )

        ordered["net_nav"] = (
            float(starting_capital)
            * (
                1.0
                + ordered["net_daily_return"]
            ).cumprod()
        )

        ordered["net_cumulative_return"] = (
            ordered["net_nav"]
            / float(starting_capital)
            - 1.0
        )

        ordered["cost_schedule_id"] = schedule_ids[0]
        output_frames.append(ordered)

    return (
        pd.concat(output_frames, ignore_index=True)
        .sort_values(
            ["cost_schedule_id", "policy_id", "trade_date"]
        )
        .reset_index(drop=True)
    )


def summarize_costed_nav(
    nav: pd.DataFrame,
    *,
    starting_capital: float,
) -> dict[str, float | int | str]:
    if nav.empty:
        raise ValueError(
            "Cannot summarize an empty costed NAV series"
        )

    ordered = nav.sort_values("trade_date").reset_index(drop=True)

    elapsed_days = int(
        (
            pd.Timestamp(ordered.iloc[-1]["trade_date"])
            - pd.Timestamp(ordered.iloc[0]["trade_date"])
        ).days
    )

    total_return = float(
        ordered.iloc[-1]["net_nav"]
        / starting_capital
        - 1.0
    )

    annualized_return = np.nan
    if elapsed_days > 0 and total_return > -1:
        annualized_return = float(
            (1.0 + total_return)
            ** (365.25 / elapsed_days)
            - 1.0
        )

    daily_returns = ordered["net_daily_return"].astype(float)
    daily_std = float(daily_returns.std(ddof=1))

    annualized_volatility = float(
        daily_std * np.sqrt(252)
    )

    sharpe_zero_rf = np.nan
    if daily_std > 0:
        sharpe_zero_rf = float(
            daily_returns.mean()
            / daily_std
            * np.sqrt(252)
        )

    running_peak = ordered["net_nav"].cummax()
    drawdown = ordered["net_nav"] / running_peak - 1.0

    total_cost = float(
        ordered["transaction_cost"].sum()
    )
    total_traded_notional = float(
        ordered["traded_notional"].sum()
    )

    return {
        "cost_schedule_id": str(
            ordered.iloc[0]["cost_schedule_id"]
        ),
        "policy_id": str(
            ordered.iloc[0]["policy_id"]
        ),
        "start_date": pd.Timestamp(
            ordered.iloc[0]["trade_date"]
        ).date().isoformat(),
        "end_date": pd.Timestamp(
            ordered.iloc[-1]["trade_date"]
        ).date().isoformat(),
        "observations": int(len(ordered)),
        "starting_capital": float(starting_capital),
        "ending_net_nav": float(
            ordered.iloc[-1]["net_nav"]
        ),
        "net_total_return": total_return,
        "net_annualized_return": annualized_return,
        "net_annualized_volatility": annualized_volatility,
        "net_sharpe_zero_rf": sharpe_zero_rf,
        "net_max_drawdown": float(drawdown.min()),
        "total_transaction_cost": total_cost,
        "total_brokerage": float(
            ordered["brokerage_cost"].sum()
        ),
        "total_sst": float(
            ordered["sst_cost"].sum()
        ),
        "total_cdc": float(
            ordered["cdc_cost"].sum()
        ),
        "total_traded_notional": total_traded_notional,
        "weighted_average_cost_rate": (
            total_cost / total_traded_notional
            if total_traded_notional > 0
            else 0.0
        ),
        "cost_days": int(
            (ordered["transaction_cost"] > 0).sum()
        ),
        "trade_count": int(
            ordered["trade_count"].sum()
        ),
    }
