from psx_ml.c10.build_kmi_all_share_baseline_2022 import (
    EXPECTED_DEFAULTERS,
    EXPECTED_INDEX_COUNT,
    EXPECTED_SCREENED_COMPLIANT,
)


def test_baseline_reconciliation_constants() -> None:
    assert EXPECTED_SCREENED_COMPLIANT == 256
    assert EXPECTED_INDEX_COUNT == 250
    assert EXPECTED_DEFAULTERS == {
        "CLOV",
        "DMTX",
        "JUBS",
        "LMSM",
        "NCML",
        "RUBY",
    }
    assert (
        EXPECTED_SCREENED_COMPLIANT
        - len(EXPECTED_DEFAULTERS)
        == EXPECTED_INDEX_COUNT
    )
