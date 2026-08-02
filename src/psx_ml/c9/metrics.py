from __future__ import annotations
from collections import defaultdict
import math
import numpy as np
from sklearn.metrics import ndcg_score
def date_ranking_metrics(rows,ks=(5,10,20)):
    grouped=defaultdict(list)
    for r in rows: grouped[r["trade_date"]].append(r)
    out=[]
    for d,part in sorted(grouped.items()):
        pred=sorted(part,key=lambda r:(-r["prediction_percentile_rank"],r["symbol"])); actual=sorted(part,key=lambda r:(-r["actual_rank_target"],r["symbol"])); n=len(part); actual_top=set(r["symbol"] for r in actual[:max(1,math.ceil(.1*n))]); actual_bottom=set(r["symbol"] for r in actual[-max(1,math.ceil(.1*n)):])
        row={"trade_date":d,"row_count":n}
        for k in ks:
            kk=min(k,n); chosen=set(r["symbol"] for r in pred[:kk]); truth=set(r["symbol"] for r in actual[:kk]); row[f"precision_at_{k}"]=len(chosen&truth)/kk; row[f"recall_at_{k}"]=len(chosen&truth)/len(truth)
            y=np.asarray([r["actual_rank_target"] for r in part]); p=np.asarray([r["prediction_percentile_rank"] for r in part]); row[f"ndcg_at_{k}"]=float(ndcg_score(y[None,:],p[None,:],k=kk))
        selected_top=set(r["symbol"] for r in pred[:max(1,math.ceil(.1*n))]); row["top_decile_capture"]=len(selected_top&actual_top)/len(actual_top); row["bottom_decile_rejection"]=1-len(selected_top&actual_bottom)/len(actual_bottom)
        positions=[i+1 for i,r in enumerate(pred) if r["symbol"] in actual_top]; row["mrr_actual_top_decile"]=float(np.mean([1/x for x in positions])); out.append(row)
    return out
def candidate_outcomes(selected,universe):
    by_date=defaultdict(list); chosen=defaultdict(list)
    for r in universe: by_date[r["trade_date"]].append(r)
    for r in selected: chosen[r["trade_date"]].append(r)
    out=[]
    for d,part in sorted(chosen.items()):
        allrows=by_date[d]; values=np.asarray([r["actual_market_relative_return"] for r in part]); ranks=np.asarray([r["actual_rank_target"] for r in part]); universe_values=np.asarray([r["actual_market_relative_return"] for r in allrows]); selected_symbols={x["symbol"] for x in part}; unselected=[r["actual_market_relative_return"] for r in allrows if r["symbol"] not in selected_symbols]
        out.append({"trade_date":d,"candidate_count":len(part),"mean_actual_market_relative_return":float(np.mean(values)),"median_actual_market_relative_return":float(np.median(values)),"mean_actual_rank":float(np.mean(ranks)),"median_actual_rank":float(np.median(ranks)),"top_decile_hit_rate":float(np.mean(ranks>=.9)),"top_quintile_hit_rate":float(np.mean(ranks>=.8)),"bottom_decile_contamination_rate":float(np.mean(ranks<=.1)),"positive_relative_return_fraction":float(np.mean(values>0)),"spread_versus_unselected":float(np.mean(values)-np.mean(unselected)) if unselected else None,"spread_versus_universe_median":float(np.mean(values)-np.median(universe_values))})
    return out
