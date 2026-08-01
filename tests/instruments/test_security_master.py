from psx_ml.instruments.security_master import build_snapshot

def test_master_priority_and_categories():
    listing=b'<table><tr><th>Symbol</th><th>Name</th><th>Sector</th></tr><tr><td>ABC</td><td>ABC Limited</td><td>CHEMICAL</td></tr><tr><td>RGT</td><td>ABC (Right)</td><td>CHEMICAL</td></tr></table>'
    empty=b'<table><tr><th>Symbol</th><th>Name</th><th>Sector</th></tr></table>'
    eligible=b'<table id="REGTable"><tr><th>Symbol</th><th>Name</th></tr><tr><td>ABC</td><td>ABC Limited</td></tr></table>'
    debt=b'<table><tr><th>Security Code</th><th>Security Name</th></tr><tr><td>D1</td><td>GoP Sukuk</td></tr></table>'
    raw={"listings-table-main-nc.html":listing,"listings-table-main-dc.html":empty,"listings-table-gem-nc.html":empty,"listings-table-gem-dc.html":empty,"eligible-scrips.html":eligible,"debt-market.html":debt}
    table,prov=build_snapshot(raw,"2026-08-01"); rows={r["symbol"]:r for r in table.to_pylist()}
    assert rows["ABC"]["instrument_family"]=="ordinary_equity" and rows["ABC"]["eligible_scrip_categories"]=="regular_deliverable_equity"
    assert rows["RGT"]["instrument_family"]=="right_or_entitlement" and rows["D1"]["instrument_family"]=="sukuk"
    assert prov["historical_semantics"].startswith("Current snapshot")

def test_reit_sector_is_explicit_master_family():
    listing=b'<table><tr><th>Symbol</th><th>Name</th><th>Sector</th></tr><tr><td>DCR</td><td>Dolmen City REIT</td><td>REAL ESTATE INVESTMENT TRUST</td></tr></table>'
    empty=b'<table><tr><th>Symbol</th><th>Name</th><th>Sector</th></tr></table>'
    raw={"listings-table-main-nc.html":listing,"listings-table-main-dc.html":empty,"listings-table-gem-nc.html":empty,"listings-table-gem-dc.html":empty,"eligible-scrips.html":empty,"debt-market.html":b'<table><tr><th>Code</th><th>Name</th></tr></table>'}
    assert build_snapshot(raw,"2026-08-01")[0].to_pylist()[0]["instrument_family"]=="REIT"
