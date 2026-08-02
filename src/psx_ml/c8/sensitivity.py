from __future__ import annotations
from collections import defaultdict
import numpy as np

VARIANTS={
    "strict_5_peer":("sector_loo_median_ret_{h}s","fwd_sector_relative_ret_{h}s"),
    "relaxed_3_peer":("sector_loo_median_ret_{h}s_relaxed_3_peer","fwd_sector_relative_ret_{h}s_relaxed_3_peer"),
    "shrunk_3_peer":("sector_market_shrunk_benchmark_ret_{h}s","fwd_sector_relative_ret_{h}s_shrunk_3_peer"),
}

def sensitivity_audit(rows,horizons,derived):
    summary=[]; coverage=[]
    for h in horizons:
        strict=np.asarray([x is not None for x in derived[f"fwd_sector_relative_ret_{h}s"]])
        strict_sectors={rows[i].get("sector") for i,x in enumerate(strict) if x}
        for variant,(benchmark_pattern,target_pattern) in VARIANTS.items():
            benchmarks=derived[benchmark_pattern.format(h=h)]; targets=derived[target_pattern.format(h=h)]
            natural=np.asarray([x is not None for x in targets])
            natural_sectors={rows[i].get("sector") for i,x in enumerate(natural) if x}
            for subset,mask in (("natural_coverage",natural),("strict_5_peer_matched",natural&strict)):
                idx=np.flatnonzero(mask); b=np.asarray([benchmarks[i] for i in idx],float); t=np.asarray([targets[i] for i in idx],float)
                summary.append({"horizon":h,"variant":variant,"comparison_subset":subset,"valid_rows":int(len(idx)),"symbol_count":len({rows[i]["symbol"] for i in idx}),"date_count":len({rows[i]["trade_date"] for i in idx}),"sector_count":len({rows[i].get("sector") for i in idx}),"benchmark_variance":float(np.var(b)) if len(b) else None,"target_variance":float(np.var(t)) if len(t) else None,"newly_usable_sector_count":len(natural_sectors-strict_sectors) if subset=="natural_coverage" else 0,"newly_usable_sectors":"|".join(sorted(x for x in natural_sectors-strict_sectors if x)) if subset=="natural_coverage" else ""})
            grouped=defaultdict(list)
            for i,valid in enumerate(natural):
                sector=rows[i].get("sector")
                if sector is not None: grouped[sector].append(valid)
            for sector,flags in sorted(grouped.items()): coverage.append({"horizon":h,"variant":variant,"sector":sector,"eligible_rows":len(flags),"valid_rows":int(sum(flags)),"coverage_fraction":float(np.mean(flags))})
    return summary,coverage
