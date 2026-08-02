from collections import Counter
def herfindahl(values):
    c=Counter(values); n=sum(c.values()); return sum((v/n)**2 for v in c.values()) if n else None
def concentration(selected):
    sectors=[r.get("sector") or "missing" for r in selected]; symbols=[r["symbol"] for r in selected]; sc=Counter(sectors); yc=Counter(symbols); n=len(selected)
    return {"selection_count":n,"sector_herfindahl":herfindahl(sectors),"symbol_herfindahl":herfindahl(symbols),"top_sector_share":max(sc.values())/n if n else None,"top_5_sector_share":sum(v for _,v in sc.most_common(5))/n if n else None,"top_symbol_selection_frequency":max(yc.values())/n if n else None,"top_10_symbol_selection_frequency":sum(v for _,v in yc.most_common(10))/n if n else None}
