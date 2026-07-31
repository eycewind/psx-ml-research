import numpy as np

from psx_ml.features.config import FeatureConfig
from psx_ml.features.pipeline import compute_features
from tests.features.conftest import tables


def cfg(tmp_path):
    p=tmp_path/"x"
    return FeatureConfig(p,p,p,p,p,p,"adjusted","adjusted",(1,5,20),(5,20,60),20,5,2,"cpu","float64")


def col(table,name): return table[name].to_numpy(zero_copy_only=False)


def test_known_trailing_values_psx_conventions_and_missing_distinctions(panel_rows,tmp_path):
    table,registry,q=compute_features(*tables(panel_rows),cfg(tmp_path))
    keys=list(zip(table["trade_date"].to_pylist(),table["symbol"].to_pylist()))
    i=keys.index(("2024-01-10","CCC")); j=keys.index(("2024-01-11","CCC"))
    assert table.num_rows==len(panel_rows)
    assert table["close_to_open_1obs_adj"][i].as_py()==10/12-1  # open outside range preserved
    assert table["zero_volume_flag"][i].as_py()==1
    assert table["missing_volume_flag"][j].as_py()==1
    assert table["strict_high_below_low_flag"][j].as_py()==1
    assert table["true_range_1obs_adj"][j].as_py() is None
    a=keys.index(("2024-01-21","AAA"))
    assert np.isclose(table["ret_20obs_adj"][a].as_py(),121/101-1)
    assert table["ret_20obs_adj"][keys.index(("2024-01-20","AAA"))].as_py() is None
    assert q["infinity_after_sanitation"]==0
    assert len(registry)==len([x for x in table.column_names if x not in {"trade_date","symbol","point_in_time_eligible","source_observation_present","listing_age_observations"}])


def test_gap_stale_and_exact_pit_eligibility(panel_rows,tmp_path):
    table,_,_=compute_features(*tables(panel_rows),cfg(tmp_path)); keys=list(zip(table["trade_date"].to_pylist(),table["symbol"].to_pylist()))
    b=keys.index(("2024-01-05","BBB")); assert table["days_since_previous_observation"][b].as_py()==2
    assert table["point_in_time_eligible"][keys.index(("2024-01-02","AAA"))].as_py() is False
    assert table["point_in_time_eligible"][keys.index(("2024-01-03","AAA"))].as_py() is True
    c0=keys.index(("2024-01-10","CCC")); c1=keys.index(("2024-01-11","CCC"))
    assert table["stale_close_run_length"][c0].as_py()==0
    assert table["stale_close_run_length"][c1].as_py()==1


def test_raw_family_uses_raw_columns_without_adjusted_mixing(panel_rows,tmp_path):
    rows=[]
    for r in panel_rows:
        x=dict(r); x["close_adj"]=r["close"]*0.5; x["open_adj"]=r["open"]*0.5; x["high_adj"]=r["high"]*0.5; x["low_adj"]=r["low"]*0.5
        x["volume_adj"]=None if r["volume"] is None else r["volume"]*2; rows.append(x)
    raw=cfg(tmp_path)
    raw=FeatureConfig(raw.daily_path,raw.universe_path,raw.input_manifest_path,raw.feature_path,raw.output_manifest_path,raw.report_path,"raw","raw",raw.return_windows,raw.rolling_windows,raw.minimum_history,raw.stale_run_threshold,raw.minimum_cross_section_size,raw.engine,raw.float_precision)
    table,registry,_=compute_features(*tables(rows),raw)
    keys=list(zip(table["trade_date"].to_pylist(),table["symbol"].to_pylist())); i=keys.index(("2024-01-02","AAA"))
    assert np.isclose(table["turnover_1obs_raw"][i].as_py(),102*1002)
    assert all(d.field_family=="raw" for d in registry)
