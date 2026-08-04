from psx_ml.c10.build_kmi_all_share_screened_history import (
    CARRY_FORWARD_DATES,
    SNAPSHOT_DATES,
)


def test_screened_history_dates_are_pre_2026() -> None:
    all_dates = set(SNAPSHOT_DATES) | set(
        CARRY_FORWARD_DATES
    )
    assert len(all_dates) == 9
    assert all(
        not value.startswith("2026")
        for value in all_dates
    )


def test_carry_forward_dates_do_not_overlap_snapshots() -> None:
    assert not (
        set(SNAPSHOT_DATES)
        & set(CARRY_FORWARD_DATES)
    )
