import numpy as np
from psx_ml.c9.policies import percentile_ranks,select,schedule_dates,apply_liquidity,sector_constraint
from psx_ml.c9.metrics import date_ranking_metrics,candidate_outcomes
from psx_ml.c9.turnover import turnover_metrics,retention,candidate_lifetimes
from psx_ml.c9.agreement import average_rank_ensemble,model_agreement,intersection_union
from psx_ml.c9.concentration import herfindahl,concentration
from psx_ml.c9.bootstrap import moving_block_bootstrap,empirical_p_value
from psx_ml.c9.persistence import rank_persistence,rank_changes
from psx_ml.c9.baselines import deterministic_random_same_count,random_distribution,rank_baseline

def rows(date="2024-01-02"):
    return [{"trade_date":date,"symbol":chr(65+i),"prediction":float(i),"actual_rank_target":i/9,"actual_market_relative_return":i-4.5,"sector":"S"+str(i%3),"turnover_percentile_rank":i/9} for i in range(10)]

def test_date_local_ranks_percentiles_fixed_thresholds_and_ties():
    ranked=percentile_ranks(rows()); assert ranked[0]["prediction_percentile_rank"]==0 and ranked[-1]["prediction_percentile_rank"]==1
    assert [r["symbol"] for r in select(ranked,"fixed",2)]==["J","I"]
    assert len(select(ranked,"percentile",.2))==2 and len(select(ranked,"threshold",.8))==2
    tied=percentile_ranks([{**r,"prediction":1} for r in rows()]); assert [r["symbol"] for r in tied]==list("ABCDEFGHIJ")
    assert [r["symbol"] for r in select(tied,"fixed",2)]==["J","I"]

def test_bottom_direction_liquidity_and_sector_caps():
    ranked=percentile_ranks(rows()); assert [r["symbol"] for r in select(ranked,"fixed",2,"bottom")]==["A","B"]
    assert len(apply_liquidity(ranked,"L1"))==7 and len(apply_liquidity(ranked,"L2"))==5
    selected=select(ranked,"fixed",10); s1,_=sector_constraint(selected,"S1"); s2,_=sector_constraint(selected,"S2"); s3,_=sector_constraint(selected,"S3")
    assert len(s1)==6 and len(s2)==3 and len(s3)==3

def test_schedules_are_session_and_calendar_deterministic():
    d=["2024-01-01","2024-01-02","2024-01-03","2024-01-04","2024-01-05","2024-01-08"]
    assert schedule_dates(d,"every_2_sessions")==d[::2] and schedule_dates(d,"non_overlapping_5_session")==d[::5]
    assert schedule_dates(d,"weekly_first_session")==["2024-01-01","2024-01-08"]
    assert schedule_dates(d,"weekly_last_session")==["2024-01-05","2024-01-08"]

def test_ranking_and_candidate_outcomes_match_perfect_order():
    ranked=percentile_ranks(rows()); m=date_ranking_metrics(ranked)[0]
    assert m["precision_at_5"]==m["recall_at_5"]==1 and np.isclose(m["ndcg_at_5"],1) and m["top_decile_capture"]==1 and m["bottom_decile_rejection"]==1
    o=candidate_outcomes(select(ranked,"fixed",2),ranked)[0]; assert o["candidate_count"]==2 and o["mean_actual_market_relative_return"]==4 and o["top_decile_hit_rate"]==.5

def test_turnover_retention_and_lifetimes_reconcile():
    a=select(percentile_ranks(rows("2024-01-01")),"fixed",2); b=[{**r,"trade_date":"2024-01-02","selection_date":"2024-01-02"} for r in a[1:]]+[dict(a[0],trade_date="2024-01-02",selection_date="2024-01-02",symbol="H")]
    t=turnover_metrics(a+b)[1]; assert t["retained"]==1 and t["entries"]==t["exits"]==1 and np.isclose(t["jaccard"],1/3)
    assert retention(a+b,(1,))[0]["mean_retention"]==.5
    life=candidate_lifetimes(a+b); assert sum(r["sessions"] for r in life)==4

def test_agreement_ensemble_intersection_union():
    a=percentile_ranks(rows()); b=percentile_ranks([{**r,"prediction":9-r["prediction"]} for r in rows()]); e=average_rank_ensemble(a,b)
    assert all(np.isclose(r["prediction_percentile_rank"],.5) for r in e); assert np.isclose(model_agreement(a,b)[0]["rank_correlation"],-1)
    x,u=intersection_union(select(a,"fixed",2),select(b,"fixed",2)); assert len(x)==0 and len(u)==4

def test_concentration_bootstrap_and_empirical_p_value():
    assert np.isclose(herfindahl(["a","a","b","b"]),.5); c=concentration(rows()); assert c["selection_count"]==10 and np.isclose(c["symbol_herfindahl"],.1)
    a=moving_block_bootstrap([1,2,3,4,5],2,100,42); b=moving_block_bootstrap([1,2,3,4,5],2,100,42); assert a==b and a["estimate"]==3
    assert empirical_p_value(3,[1,2,3,4])==.6

def test_rank_persistence_and_changes_use_consecutive_sessions():
    a=percentile_ranks(rows("2024-01-01")); b=[{**r,"trade_date":"2024-01-02"} for r in a]
    p=rank_persistence(a+b,(1,))[0]; assert np.isclose(p["rank_autocorrelation"],1) and p["top_decile_persistence"]==1
    change=rank_changes(a+b); assert change["count"]==10 and change["mean"]==0

def test_random_baseline_preserves_count_and_seed():
    universe=percentile_ranks(rows()); counts={"2024-01-02":3}; a=deterministic_random_same_count(universe,counts,7,0); b=deterministic_random_same_count(universe,counts,7,0)
    assert a==b and len(a)==3
    assert random_distribution(universe,counts,5,7)==random_distribution(universe,counts,5,7)
    momentum=rank_baseline(universe,"actual_market_relative_return","momentum"); assert momentum[-1]["prediction_percentile_rank"]==1
