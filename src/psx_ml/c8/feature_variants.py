from __future__ import annotations

def build_feature_variants(c7,market,sector,relative):
    stock_market=[x for x in relative if "_market_" in x]
    stock_sector=[x for x in relative if "_sector_" in x]
    rolling_market=[x for x in relative if x.endswith("_market_60obs")]
    rolling_sector=[x for x in relative if x.endswith("_sector_60obs")]
    market_relative=list(dict.fromkeys(stock_market+rolling_market))
    sector_relative=list(dict.fromkeys(stock_sector+rolling_sector))
    context=list(dict.fromkeys(market+sector+relative))
    return {
        "A_c7_only":list(c7),
        "B_market_context":list(dict.fromkeys(c7+market+market_relative)),
        "C_sector_context":list(dict.fromkeys(c7+sector+sector_relative)),
        "D_full_context":list(dict.fromkeys(c7+context)),
        "E_context_only":context,
    }

def stage1_matrix():
    return [
        ("absolute","A_c7_only"),("absolute","D_full_context"),
        ("market_relative","A_c7_only"),("market_relative","B_market_context"),
        ("market_relative","D_full_context"),("market_relative","E_context_only"),
    ]

def stage2_matrix():
    return [(family,variant) for family in ("sector_strict_5_peer","sector_relaxed_3_peer","sector_shrunk_3_peer") for variant in ("A_c7_only","C_sector_context","D_full_context")]
