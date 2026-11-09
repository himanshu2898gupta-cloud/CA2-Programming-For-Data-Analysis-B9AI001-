import sqlite3
import requests
import pandas as pd
import numpy as np

def run_defi_risk_pipeline():
    print ("Step 1: Fetching Live Market Data From CoinGecko API")
    try:
        coingecko_url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
        res = requests.get(coingecko_url, timeout=10).json()
        eth_price = res.get('ethereum',{}).get('usd', 3000.0)
        print(f"Success! Live ETH Price Fetched: ${eth_price}")
    except Exception as e:
        print(f"API Warning: {e}.Using fallback price of $3000.")
        eth_price = 3000.0
    print("\n--- Step 2: Ingesting Wallet Telemetry & Calculating LTV---")

    raw_wallet_data = [
        {"wallet": "0x111...whale", "eth_balance": 45.5, "tx_count": 320, "borrowed_usdc": 50000},
        {"wallet": "0x222...active", "eth_balance": 3.2, "tx_count": 85, "borrowed_usdc": 1200},
        {"wallet": "0x333...dormant", "eth_balance": 18.0, "tx_count": 4, "borrowed_usdc": 0},
        {"wallet": "0x444...risky", "eth_balance": 1.1, "tx_count": 140, "borrowed_usdc": 2800},
        {"wallet": "0x555...bot", "eth_balance": 0.4, "tx_count": 1250, "borrowed_usdc": 100},
        {"wallet": "0x666...whale2", "eth_balance": 65.0, "tx_count": 15, "borrowed_usdc": 100000}
    ]
    df = pd.DataFrame(raw_wallet_data)
    df['total_collateral_usd'] = df['eth_balance'] * eth_price
    df['ltv_ratio'] = np.where(
        df['total_collateral_usd'] > 0,
        df['borrowed_usdc']/df['total_collateral_usd'],
        0
    )
    print("\n--- Step 3: Applying Behavioral Rule Engine---")
    def assign_risk_profile(row):
        net_worth = row['total_collateral_usd']
        txs = row['tx_count']
        ltv = row['ltv_ratio']

        if ltv > 0.75 or (net_worth < 2000 and txs <10):
            return 'High Risk / Liquidation Candidate'
        elif net_worth > 50000 and txs <=20:
            return 'Medium Risk / Inactive Whale'
        elif net_worth > 10000 and txs >50:
            return 'Low Risk / Prime DeFi User'
        else:
            return  'Medium Risk / Standard Active'

    df['risk_profile'] = df.apply(assign_risk_profile, axis=1)

    print(df[['wallet', 'total_collateral_usd' , 'ltv_ratio' , 'risk_profile']])

    print("\n--- Step 4: Persisting Data to local Sqlite Database---")
    db_name = "automated_defi_risk.db"
    conn = sqlite3.connect(db_name)
    df.to_sql('wallet_risk_analytics', conn, if_exists='replace', index=False)
    conn.close()
    print(f"Success! Cleaned data saved locally to SQLite database file: {db_name}")

if __name__ == "__main__":
    run_defi_risk_pipeline()