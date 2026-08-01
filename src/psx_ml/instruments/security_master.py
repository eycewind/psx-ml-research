from __future__ import annotations
import argparse, hashlib, json, urllib.request
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq

BASE="https://dps.psx.com.pk"
LISTING_ENDPOINTS={
    "listings-table-main-nc.html":("main","listed"),
    "listings-table-main-dc.html":("main","non_compliant"),
    "listings-table-gem-nc.html":("gem","listed"),
    "listings-table-gem-dc.html":("gem","non_compliant"),
}
ELIGIBLE_CATEGORIES={"REGTable":"regular_deliverable_equity","FUTTable":"future_deliverable_contract","IPOTable":"initial_public_offering","CSFTable":"cash_settled_future","SIFTable":"stock_index_future","BNBTable":"bills_and_bonds","NDMTable":"negotiated_deal","ODLTable":"odd_lot","SQRTable":"square_up_buy_in"}

class Tables(HTMLParser):
    def __init__(self): super().__init__(); self.table=None; self.cell=False; self.row=None; self.tables=defaultdict(list); self.attrs={}
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="table": self.table=a.get("id","table"); self.attrs[self.table]=a
        elif tag=="tr" and self.table: self.row=[]
        elif tag in {"td","th"} and self.row is not None: self.cell=True; self.row.append("")
    def handle_data(self,data):
        if self.cell and self.row is not None: self.row[-1]+=(" "+data.strip() if data.strip() else "")
    def handle_endtag(self,tag):
        if tag in {"td","th"}: self.cell=False
        elif tag=="tr" and self.table and self.row:
            self.tables[self.table].append([" ".join(x.split()) for x in self.row]); self.row=None
        elif tag=="table": self.table=None

def _tables(data: bytes):
    p=Tables(); p.feed(data.decode("utf-8",errors="replace")); return p.tables

def _family(name,sector,fixed=False):
    n=name.lower(); s=sector.lower()
    if fixed:
        if "sukuk" in n: return "sukuk"
        if "government" in n or "gop" in n or "pakistan investment bond" in n or "treasury bill" in n: return "government_security"
        return "debt_security"
    if "exchange traded fund" in s or "(etf)" in n: return "ETF"
    if "reit" in s or "real estate investment trust" in s or "real estate investment trust" in n: return "REIT"
    if "(right)" in n or "right issue" in n: return "right_or_entitlement"
    if "preference" in n: return "preference_share"
    return "ordinary_equity"

def build_snapshot(raw: dict[str,bytes], snapshot_date: str) -> tuple[pa.Table,dict]:
    records={}; sources=defaultdict(set); eligible=defaultdict(set); eligible_names={}
    for filename,(board,status) in LISTING_ENDPOINTS.items():
        rows=_tables(raw[filename]).get("table",[])
        for row in rows[1:]:
            if len(row)<3: continue
            symbol,name,sector=row[:3]; records[symbol]={"symbol":symbol,"security_name":name,"instrument_family":_family(name,sector),"board":board,"listing_status":status,"sector":sector}
            sources[symbol].add(f"{BASE}/listings-table/{board}/{'nc' if status=='listed' else 'dc'}")
    for table_id,category in ELIGIBLE_CATEGORIES.items():
        rows=_tables(raw["eligible-scrips.html"]).get(table_id,[])
        for row in rows[1:]:
            if row:
                eligible[row[0]].add(category); sources[row[0]].add(f"{BASE}/eligible-scrips#{table_id}")
                if len(row)>1 and row[1]: eligible_names.setdefault(row[0],row[1])
    debt_tables=_tables(raw["debt-market.html"])
    debt_rows=max(debt_tables.values(),key=len)
    for row in debt_rows[1:]:
        if len(row)<2: continue
        symbol,name=row[:2]; existing=records.get(symbol,{})
        records[symbol]={"symbol":symbol,"security_name":name,"instrument_family":_family(name,"",True),"board":existing.get("board","fixed_income"),"listing_status":existing.get("listing_status","listed"),"sector":existing.get("sector","FIXED INCOME")}
        sources[symbol].add(f"{BASE}/debt-market"); sources[symbol].add(f"{BASE}/debt/{symbol}")
    for symbol in eligible:
        if symbol not in records:
            categories=eligible[symbol]
            family="derivative_contract" if categories & {"future_deliverable_contract","cash_settled_future","stock_index_future"} else ("debt_security" if "bills_and_bonds" in categories else "unknown")
            records[symbol]={"symbol":symbol,"security_name":eligible_names.get(symbol,""),"instrument_family":family,"board":"eligible_scrips_only","listing_status":"eligible_category_only","sector":""}
    rows=[]
    for symbol,r in sorted(records.items()):
        rows.append({**r,"eligible_scrip_categories":"|".join(sorted(eligible[symbol])),"source_page":"|".join(sorted(sources[symbol])),"snapshot_date":snapshot_date})
    table=pa.Table.from_pylist(rows,schema=pa.schema([(x,pa.string()) for x in ("symbol","security_name","instrument_family","board","listing_status","sector","eligible_scrip_categories","source_page","snapshot_date")]))
    provenance={"snapshot_date":snapshot_date,"source_base":BASE,"endpoints":[f"/listings-table/{b}/{'nc' if s=='listed' else 'dc'}" for b,s in LISTING_ENDPOINTS.values()]+["/eligible-scrips","/debt-market","/company/<symbol>","/etf/<symbol>","/debt/<symbol>"],"raw_response_sha256":{k:hashlib.sha256(v).hexdigest() for k,v in sorted(raw.items())},"rows":table.num_rows,"schema":table.schema.names,"historical_semantics":"Current snapshot only; must not be projected backward as authoritative classification."}
    return table,provenance

def fetch_raw():
    paths={**{k:f"/listings-table/{b}/{'nc' if s=='listed' else 'dc'}" for k,(b,s) in LISTING_ENDPOINTS.items()},"eligible-scrips.html":"/eligible-scrips","debt-market.html":"/debt-market"}
    out={}
    for name,path in paths.items():
        req=urllib.request.Request(BASE+path,headers={"User-Agent":"Mozilla/5.0 PSX-ML-Research/1.0"}); out[name]=urllib.request.urlopen(req,timeout=60).read()
    return out

def main():
    p=argparse.ArgumentParser(); p.add_argument("--snapshot-date",required=True); p.add_argument("--output",type=Path,required=True); p.add_argument("--provenance",type=Path,required=True); p.add_argument("--raw-dir",type=Path)
    a=p.parse_args(); raw={name:(a.raw_dir/name).read_bytes() for name in [*LISTING_ENDPOINTS,"eligible-scrips.html","debt-market.html"]} if a.raw_dir else fetch_raw()
    table,provenance=build_snapshot(raw,a.snapshot_date); a.output.parent.mkdir(parents=True,exist_ok=True); pq.write_table(table,a.output,compression="zstd",use_dictionary=False); a.provenance.write_text(json.dumps(provenance,indent=2,sort_keys=True)+"\n"); print(f"security master: {table.num_rows} rows")

if __name__=="__main__": main()
