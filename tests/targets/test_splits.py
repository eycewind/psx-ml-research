import pyarrow as pa

from psx_ml.splits.walk_forward import generate_assignments
from psx_ml.targets.forward_returns import generate_targets
from tests.targets.conftest import DATES,sconfig,tables,target_rows,tconfig

def test_roles_are_date_uniform_purged_embargoed_and_test_safe(target_rows,tmp_path):
    targets,_,cal=generate_targets(*tables(target_rows),tconfig(tmp_path)); assignments,counts=generate_assignments(targets,cal,sconfig(tmp_path),1)
    bydate={}
    for r in assignments.to_pylist(): bydate.setdefault(r["trade_date"],set()).add(r["split_role"])
    assert all(len(v)==1 for v in bydate.values())
    assert bydate["2024-01-06"]=={"purged"} # end is validation start
    assert bydate["2024-01-07"]=={"purged"}
    assert bydate["2024-01-08"]=={"validation"}
    assert bydate["2024-01-11"]=={"embargoed"} and bydate["2024-01-12"]=={"embargoed"}
    assert all(bydate[d]=={"test"} for d in DATES[12:])
    assert counts["fold"]["overlap_violations"]==0

def test_split_assignment_invariant_to_input_order(target_rows,tmp_path):
    targets,_,cal=generate_targets(*tables(target_rows),tconfig(tmp_path)); a,_=generate_assignments(targets,cal,sconfig(tmp_path),1)
    rev=targets.take(pa.array(list(reversed(range(targets.num_rows))))); b,_=generate_assignments(rev,cal,sconfig(tmp_path),1)
    key=lambda r:(r["trade_date"],r["symbol"],r["fold_id"],r["split_role"])
    assert sorted(map(key,a.to_pylist()))==sorted(map(key,b.to_pylist()))
