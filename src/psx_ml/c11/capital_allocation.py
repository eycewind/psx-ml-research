from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class AllocationDefinition:
    allocation_id: str
    sleeves: tuple[tuple[str, float], ...]
    category: str

    def validate(self) -> None:
        if not self.sleeves:
            raise ValueError(f"{self.allocation_id}: no sleeves")
        weights = [float(w) for _, w in self.sleeves]
        if any((not np.isfinite(w)) or w <= 0 for w in weights):
            raise ValueError(f"{self.allocation_id}: invalid sleeve weight")
        if not np.isclose(sum(weights), 1.0, atol=1e-12, rtol=0):
            raise ValueError(
                f"{self.allocation_id}: sleeve weights sum to {sum(weights)}"
            )


def build_allocation_targets(
    deployment_selections: pd.DataFrame,
    definition: AllocationDefinition,
) -> pd.DataFrame:
    """Turn policy sleeves into one merged target portfolio.

    Each sleeve is equal-weight internally on each signal date. The predefined
    sleeve allocation is then applied. If multiple sleeves select the same
    symbol, their target weights are added and the symbol appears once.
    """
    definition.validate()

    required = {"policy_id", "trade_date", "symbol", "shariah_eligible"}
    missing = sorted(required - set(deployment_selections.columns))
    if missing:
        raise ValueError(f"Deployment selections missing columns: {missing}")

    source = deployment_selections.copy()
    source["trade_date"] = pd.to_datetime(source["trade_date"]).dt.normalize()
    source["symbol"] = source["symbol"].astype(str)

    pieces = []
    for sleeve_policy, sleeve_weight in definition.sleeves:
        part = source.loc[source["policy_id"] == sleeve_policy].copy()
        if part.empty:
            raise ValueError(
                f"{definition.allocation_id}: no rows for sleeve {sleeve_policy}"
            )
        if not part["shariah_eligible"].astype(bool).all():
            raise ValueError(
                f"{definition.allocation_id}: non-Shariah row in {sleeve_policy}"
            )
        counts = part.groupby("trade_date")["symbol"].transform("count")
        if (counts <= 0).any():
            raise ValueError("Invalid sleeve date count")
        part["sleeve_policy_id"] = sleeve_policy
        part["sleeve_allocation"] = float(sleeve_weight)
        part["sleeve_symbol_count"] = counts.astype(int)
        part["sleeve_symbol_weight"] = float(sleeve_weight) / counts
        pieces.append(
            part[
                [
                    "trade_date",
                    "symbol",
                    "sleeve_policy_id",
                    "sleeve_allocation",
                    "sleeve_symbol_count",
                    "sleeve_symbol_weight",
                ]
            ]
        )

    contributions = pd.concat(pieces, ignore_index=True)
    date_sets = [
        set(
            contributions.loc[
                contributions["sleeve_policy_id"] == sleeve,
                "trade_date",
            ]
        )
        for sleeve, _ in definition.sleeves
    ]
    if any(ds != date_sets[0] for ds in date_sets[1:]):
        raise ValueError(
            f"{definition.allocation_id}: sleeve signal-date sets differ"
        )

    agg = (
        contributions.groupby(["trade_date", "symbol"], as_index=False)
        .agg(
            target_weight=("sleeve_symbol_weight", "sum"),
            sleeve_count=("sleeve_policy_id", "nunique"),
        )
    )
    contributors = (
        contributions.groupby(["trade_date", "symbol"])["sleeve_policy_id"]
        .apply(lambda s: "|".join(sorted(set(map(str, s)))))
        .rename("contributing_policies")
        .reset_index()
    )
    agg = agg.merge(
        contributors,
        on=["trade_date", "symbol"],
        validate="one_to_one",
    )

    agg["policy_id"] = definition.allocation_id
    agg["allocation_id"] = definition.allocation_id
    agg["allocation_category"] = definition.category

    sums = agg.groupby("trade_date")["target_weight"].sum()
    if not np.allclose(sums.to_numpy(), 1.0, atol=1e-10, rtol=0):
        raise ValueError(
            f"{definition.allocation_id}: merged target weights do not sum to 1"
        )

    return agg.sort_values(
        ["trade_date", "target_weight", "symbol"],
        ascending=[True, False, True],
        kind="mergesort",
    ).reset_index(drop=True)
