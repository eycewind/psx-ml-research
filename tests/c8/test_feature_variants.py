from psx_ml.c8.feature_variants import build_feature_variants,stage1_matrix,stage2_matrix

def test_feature_variants_are_fixed_and_nonoverwriting():
    v=build_feature_variants(["base"],["market"],["sector"],["stock_minus_market_ret_1obs","stock_minus_sector_ret_1obs","rolling_beta_market_60obs"])
    assert v["A_c7_only"]==["base"]
    assert "sector" not in v["B_market_context"] and "market" not in v["C_sector_context"]
    assert len(stage1_matrix())==6 and len(stage2_matrix())==9
