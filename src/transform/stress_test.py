import os
import sys
import sqlite3
import pandas as pd
from datetime import datetime, timezone


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.transform.features import calculate_ltv


def run_stress_test_simulation(db_path: str = "automated_defi_risk.db"):
    print("=" * 60)
    print("🧪 RUNNING DEFI PRICE SHOCK STRESS TEST SIMULATION")
    print("=" * 60)

    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM wallet_risk_analytics", conn)
    run_log = pd.read_sql("SELECT eth_price_usd FROM pipeline_run_log ORDER BY rowid DESC LIMIT 1", conn)
    base_eth_price = float(run_log['eth_price_usd'].iloc[0])

    print(f"\n[Baseline] Current Verified ETH Price: ${base_eth_price:,.2f}")
    print(f"[Baseline] Total Wallets Loaded: {len(df)}")

    scenarios = [
        {"name": "Scenario 1: Mild Market Drop (-15%)", "drop_pct": 0.15},
        {"name": "Scenario 2: Moderate Sell-Off (-25%)", "drop_pct": 0.25},
        {"name": "Scenario 3: Severe Black Swan (-35%)", "drop_pct": 0.35}
    ]

    simulation_results = []

    for sc in scenarios:
        drop = sc["drop_pct"]
        shocked_price = base_eth_price * (1.0 - drop)

        temp_df = df.copy()
        temp_df['shocked_collateral'] = temp_df['eth_collateral'] * shocked_price
        temp_df['shocked_ltv'] = temp_df.apply(
            lambda row: calculate_ltv(row['borrowed_usd'], row['shocked_collateral']), 
            axis=1
        )

        liquidated_wallets = temp_df[temp_df["shocked_ltv"] > 0.75]
        liquidated_count = len(liquidated_wallets)
        total_debt_at_risk = float(liquidated_wallets['borrowed_usd'].sum())

        simulation_results.append({
            "scenario": sc['name'],
            "eth_price_shocked": round(shocked_price, 2),
            "drop_percent": f"-{int(drop * 100)}%",
            "wallets_at_risk": liquidated_count,
            "total_debt_at_risk_usd": round(total_debt_at_risk, 2),
            "simulated_at": datetime.now(timezone.utc).isoformat()
        })

    
    results_df = pd.DataFrame(simulation_results)

    print("\n--- Simulation Stress Test Summary ---")
    display_cols = ["scenario", "eth_price_shocked", "wallets_at_risk", "total_debt_at_risk_usd"]
    print(results_df[display_cols].to_string(index=False))

    results_df.to_sql("stress_test_simulation", conn, if_exists="replace", index=False)
    conn.close()

    print(f"\n✅ Simulation Completed & Persisted to Table 'stress_test_simulation' in {db_path}!")
    return results_df


if __name__ == "__main__":
    run_stress_test_simulation()




