import unittest
from src.transform.features import calculate_ltv, assign_risk_profile

class TestDeFiFeatures(unittest.TestCase):

    # 1. Standard LTV Calculation
    def test_calculate_ltv_standard(self):
        result = calculate_ltv(borrowed_usd=50000.0, collateral_usd=100000.0)
        self.assertAlmostEqual(result, 0.5, places=4)

    # 2. Zero borrow amount
    def test_calculate_ltv_zero_borrow(self):
        result = calculate_ltv(borrowed_usd=0.0, collateral_usd=50000.0)
        self.assertEqual(result, 0.0)

    # 3. Insolvency Edge Case: debt exists with zero collateral -> Infinite LTV
    def test_calculate_ltv_zero_collateral_with_debt(self):
        result = calculate_ltv(borrowed_usd=1000.0, collateral_usd=0.0)
        self.assertEqual(result, float('inf'))

    # 4. Zero collateral AND zero debt -> 0.0 LTV
    def test_calculate_ltv_zero_collateral_zero_debt(self):
        result = calculate_ltv(borrowed_usd=0.0, collateral_usd=0.0)
        self.assertEqual(result, 0.0)

    # 5. High Risk profile due to high LTV (> 0.75)
    def test_assign_risk_high_ltv(self):
        profile = assign_risk_profile(net_worth=10000.0, tx_count=100, ltv=0.80)
        self.assertEqual(profile, 'High Risk / Liquidation Candidate')

    # 6. Infinite LTV should trigger High Risk
    def test_assign_risk_infinite_ltv(self):
        profile = assign_risk_profile(net_worth=0.0, tx_count=5, ltv=float('inf'))
        self.assertEqual(profile, 'High Risk / Liquidation Candidate')

    # 7. Boundary value analysis: Exact LTV = 0.75 should NOT trigger high risk
    def test_assign_risk_boundary_ltv(self):
        profile = assign_risk_profile(net_worth=20000.0, tx_count=60, ltv=0.75)
        self.assertEqual(profile, 'Low Risk / Prime DeFi User')

    # 8. High Risk Due to low balance (< 2000) and low transaction (< 10)
    def test_assign_risk_low_balance_low_tx(self):
        profile = assign_risk_profile(net_worth=1500.0, tx_count=5, ltv=0.10)
        self.assertEqual(profile, 'High Risk / Liquidation Candidate')

    # 9. Inactive Whale (> 50,000 collateral and <= 20 txs)
    def test_assign_risk_inactive_whale(self):
        profile = assign_risk_profile(net_worth=80000.0, tx_count=10, ltv=0.20)
        self.assertEqual(profile, 'Medium Risk / Inactive Whale')

    # 10. Prime DeFi User (> 10,000 collateral and > 50 txs)
    def test_assign_risk_prime_user(self):
        profile = assign_risk_profile(net_worth=15000.0, tx_count=80, ltv=0.30)
        self.assertEqual(profile, 'Low Risk / Prime DeFi User')

if __name__ == '__main__':
    unittest.main()