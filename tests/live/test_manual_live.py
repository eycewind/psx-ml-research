import json
from pathlib import Path

import pandas as pd

from psx_ml.live.account_state import load_manual_account_state
from psx_ml.live.render import render_order_ticket


def test_manual_state(tmp_path: Path):
    p = tmp_path / "state.json"
    p.write_text(json.dumps({"cash_pkr": 50000, "positions": {"DGKC": 200}}))
    state = load_manual_account_state(p)
    assert state.cash_pkr == 50000
    assert dict(zip(state.positions.symbol, state.positions.shares)) == {"DGKC": 200}


def test_order_render_contains_no_chase():
    x = pd.DataFrame([{
        "execution_date": pd.Timestamp("2026-08-10"),
        "order_side": "BUY",
        "symbol": "AAA",
        "order_shares": 10,
        "status": "LIMIT_WAIT",
        "reason": "OPEN_ABOVE_LIMIT_WAIT_FOR_TOUCH",
        "reference_open": 103.0,
        "buy_limit_price": 102.0,
        "cash_after_planned_orders": 1000.0,
    }])
    msg = render_order_ticket(x, cash_before=5000)
    assert "LIMIT 102.00 DAY" in msg
    assert "NO CHASE" in msg
