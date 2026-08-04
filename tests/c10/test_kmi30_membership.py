import pandas as pd
from pathlib import Path

CSV=Path("data/reference/kmi30_membership_history.csv")

def load():
    return pd.read_csv(CSV, dtype=str)

def test_every_interval_has_exactly_30_unique_members():
    df=load()
    counts=df.groupby(["effective_from","effective_to"])["symbol"].nunique()
    assert (counts==30).all()

def test_no_duplicate_members_inside_interval():
    df=load()
    assert not df.duplicated(["effective_from","symbol"]).any()

def test_intervals_are_contiguous():
    df=load()
    intervals=(df[["effective_from","effective_to"]].drop_duplicates()
               .sort_values("effective_from").reset_index(drop=True))
    for i in range(len(intervals)-1):
        end=pd.Timestamp(intervals.loc[i,"effective_to"])
        start=pd.Timestamp(intervals.loc[i+1,"effective_from"])
        assert end + pd.Timedelta(days=1) == start

def test_notices_precede_effective_dates():
    df=load()
    assert (pd.to_datetime(df["notice_date"]) <= pd.to_datetime(df["effective_from"])).all()

def test_no_2026_review_data_used():
    df=load()
    assert (pd.to_datetime(df["review_as_of"]) < pd.Timestamp("2026-01-01")).all()
