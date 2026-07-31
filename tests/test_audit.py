from psx_ml.data.sqlite import connect_readonly
from psx_ml.validation.audit import audit_daily


def test_quality_metrics_are_reproducible(source_db):
    with connect_readonly(source_db) as con:
        one=audit_daily(con,stale_run_sessions=2)
        two=audit_daily(con,stale_run_sessions=2)
    assert one == two
    assert one["duplicates"] == 1
    assert one["quality_metrics"]["invalid_dates"] == 1
    assert one["quality_metrics"]["zero_volume"] == 1
    assert one["quality_metrics"]["missing_volume"] == 1
    assert one["quality_metrics"]["open_outside_range"] == 1
    assert one["quality_metrics"]["close_outside_range"] == 1
    assert one["quality_metrics"]["adjusted_price_factor_mismatch"] >= 1
    assert one["quality_metrics"]["stale_close_transitions"] >= 1
