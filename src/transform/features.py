def calculate_ltv(borrowed_usd: float, collateral_usd: float)-> float:
    if collateral_usd > 0:
        return float(borrowed_usd/collateral_usd)
    return 0.0

def assign_risk_profile(net_worth: float, tx_count: int, ltv: float)-> str:
    if ltv > 0.75 or (net_worth < 2000 and tx_count < 10):
        return 'High Risk / Liquidation Candidate'
    elif net_worth > 50000 and tx_count <= 20:
        return 'Medium Risk / Inactive Whale'
    elif net_worth > 10000 and tx_count > 50:
        return 'Low Risk / Prime DeFi User'
    else:
        return 'Medium Risk / Standard Active'

