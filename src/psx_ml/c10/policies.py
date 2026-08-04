from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class FrozenPolicy:
    policy_id: str
    models: tuple[str, ...]
    target: str
    feature_variant: str
    selection: str
    rebalance: str
    sector_cap: int
    liquidity_screen: str

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["models"] = list(self.models)
        return result


P1_BROAD_CANONICAL = FrozenPolicy(
    policy_id="P1_broad_canonical",
    models=("lightgbm_cpu",),
    target="fwd_market_relative_rank_5s",
    feature_variant="B_market_context",
    selection="top_10pct",
    rebalance="weekly_first_session",
    sector_cap=2,
    liquidity_screen="L0",
)


P2_CONSERVATIVE_CONSENSUS = FrozenPolicy(
    policy_id="P2_conservative_consensus",
    models=("lightgbm_cpu", "xgboost_gpu"),
    target="fwd_market_relative_rank_5s",
    feature_variant="B_market_context",
    selection="intersection_top_10pct",
    rebalance="weekly_first_session",
    sector_cap=2,
    liquidity_screen="L1",
)


P4_KMI30_STRICT = FrozenPolicy(
    policy_id="P4_kmi30_strict",
    models=("lightgbm_cpu",),
    target="fwd_market_relative_rank_5s",
    feature_variant="B_market_context",
    selection="top_10pct_within_point_in_time_kmi30",
    rebalance="weekly_first_session",
    sector_cap=2,
    liquidity_screen="KMI30_membership",
)


FROZEN_POLICIES = {
    P1_BROAD_CANONICAL.policy_id: P1_BROAD_CANONICAL,
    P2_CONSERVATIVE_CONSENSUS.policy_id: P2_CONSERVATIVE_CONSENSUS,
    P4_KMI30_STRICT.policy_id: P4_KMI30_STRICT,
}
