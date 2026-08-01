import pyarrow as pa
from psx_ml.diagnostics.c6_evaluation import evaluate_predictions, loss_concentration

def test_stored_prediction_universe_filter_metrics_and_concentration():
    pred=pa.Table.from_pylist([
      {"trade_date":"2024-01-01","symbol":"A","fold_id":"f","target_name":"fwd_open_to_close_ret_5s_adj","target":1.0,"prediction":0.5,"prediction_probability":None,"model_name":"ridge_fixed_alpha_1"},
      {"trade_date":"2024-01-01","symbol":"B","fold_id":"f","target_name":"fwd_open_to_close_ret_5s_adj","target":2.0,"prediction":0.0,"prediction_probability":None,"model_name":"ridge_fixed_alpha_1"},
    ])
    membership=pa.Table.from_pylist([
      {"trade_date":"2024-01-01","symbol":"A","universe_name":"all","eligible":True,"instrument_type":"ordinary_equity"},
      {"trade_date":"2024-01-01","symbol":"B","universe_name":"all","eligible":True,"instrument_type":"debt_security"},
      {"trade_date":"2024-01-01","symbol":"A","universe_name":"equity","eligible":True,"instrument_type":"ordinary_equity"},
      {"trade_date":"2024-01-01","symbol":"B","universe_name":"equity","eligible":False,"instrument_type":"debt_security"},
    ])
    pit=pa.Table.from_pylist([{"trade_date":"2024-01-01","symbol":"A","median_turnover_pkr":10e6,"stale_fraction":0.0},{"trade_date":"2024-01-01","symbol":"B","median_turnover_pkr":1e6,"stale_fraction":.1}])
    metrics,eligible,family,_=evaluate_predictions(pred,membership,pit,ic_min=2)
    overall={(r["universe_name"],r["scope_value"]):r for r in metrics.to_pylist() if r["scope_dimension"]=="overall"}
    assert overall[("all","all")]["rmse"]>overall[("equity","all")]["rmse"]
    concentration=loss_concentration(pred,eligible,family).to_pylist()
    shares=[r["loss_share"] for r in concentration if r["universe_name"]=="all" and r["aggregation_dimension"]=="symbol"]
    assert abs(sum(shares)-1)<1e-12 and max(shares)==4/4.25
