from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

import pandas as pd


@dataclass(frozen=True)
class ManualAccountState:
    cash_pkr: float
    deployable_capital_pkr: float | None
    positions: pd.DataFrame


def load_manual_account_state(
    path: str | Path,
    *,
    require_deployable_capital: bool = False,
) -> ManualAccountState:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    cash = float(data["cash_pkr"])
    if cash < 0:
        raise ValueError("cash_pkr must be non-negative")

    raw_deployable = data.get("deployable_capital_pkr")
    deployable_capital = None
    if raw_deployable is not None:
        deployable_capital = float(raw_deployable)
        if deployable_capital <= 0:
            raise ValueError("deployable_capital_pkr must be positive")
    elif require_deployable_capital:
        raise ValueError("deployable_capital_pkr is required for production Phase B")

    raw_positions = data.get("positions", {})
    if not isinstance(raw_positions, dict):
        raise ValueError("positions must be an object mapping symbol -> shares")

    rows = []
    for symbol, shares in raw_positions.items():
        q = int(shares)
        if q < 0:
            raise ValueError(f"negative position for {symbol}")
        if q:
            rows.append({"symbol": str(symbol).upper(), "shares": q})

    positions = pd.DataFrame(rows, columns=["symbol", "shares"])
    if positions["symbol"].duplicated().any():
        raise ValueError("duplicate position symbol")
    return ManualAccountState(
        cash_pkr=cash,
        deployable_capital_pkr=deployable_capital,
        positions=positions,
    )
