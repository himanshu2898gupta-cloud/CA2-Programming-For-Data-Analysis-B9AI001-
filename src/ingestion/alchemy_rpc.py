"""
src/ingestion/alchemy_rpc.py
Interacts with Ethereum JSON-RPC via ALchemy.
Fetched live Ethereum gas prices and queries Aave V3 smart contract directly (eth_call)
for verified on-chain collateral, debt, and health factor.
"""

import os
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

#Aave V3 Pool Contract on Ethereum Mainnet
AAVE_V3_POOL_ADDRESS = "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2"
GET_USER_ACCOUNT_DATA_SELECTOR = "0xbf92857c"
def get_rpc_url() -> str:
    api_key = os.getenv("ALCHEMY_API_KEY")
    if not api_key:
        raise ValueError("ALCHEMY_API_KEY missing from environment/.env file!")
    return f"https://eth-mainnet.g.alchemy.com/v2/{api_key}"
def call_json_rpc(method: str, params: list) -> dict:
    url = get_rpc_url()
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params
    }
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise RuntimeError(f"RPC Error: {data['error']}")
    return data["result"]
def get_live_gas_price_gwei() -> float:
    result_hex = call_json_rpc("eth_gasPrice", [])
    wei_price = int(result_hex, 16)
    gwei_price = wei_price / 1e9
    logger.info(f"Live Ethereum Gas Price: {gwei_price:.2f} Gwei")
    return round(gwei_price, 2)
def get_aave_user_account_data(wallet_address: str) -> dict:
    clean_addr = wallet_address.lower().replace("0x", "").zfill(64)
    calldata = GET_USER_ACCOUNT_DATA_SELECTOR + clean_addr
    tx_params = {
        "to": AAVE_V3_POOL_ADDRESS,
        "data": calldata
    }
    result_hex = call_json_rpc("eth_call", [tx_params, "latest"])
    raw = result_hex.replace("0x", "")
    total_collateral_raw = int(raw[0:64], 16)
    total_debt_raw = int(raw[64:128], 16)
    available_borrows_raw = int(raw[128:192], 16)
    current_liq_threshold_raw = int(raw[192:256], 16)
    ltv_raw = int(raw[256:320], 16)
    health_factor_raw = int(raw[320:384], 16)
    collateral_usd = total_collateral_raw / 1e8
    debt_usd = total_debt_raw / 1e8
    available_borrows_usd = available_borrows_raw / 1e8
    liq_threshold_pct = current_liq_threshold_raw / 100.0
    ltv_pct = ltv_raw / 100.0
    if health_factor_raw > 1e30 or debt_usd == 0:
        health_factor = float("inf")
    else:
        health_factor = round(health_factor_raw / 1e18, 4)
    logger.info(f"Wallet {wallet_address[:8]}... On-Chain Collateral: ${collateral_usd:,.2f}, Debt: ${debt_usd:,.2f}, Health Factor: {health_factor}")
    return {
        "wallet": wallet_address,
        "total_collateral_usd": collateral_usd,
        "total_debt_usd": debt_usd,
        "available_borrows_usd": available_borrows_usd,
        "liquidation_threshold_pct": liq_threshold_pct,
        "ltv_pct": ltv_pct,
        "health_factor": health_factor
    }
if __name__ == "__main__":
    print("--- Testing Alchemy Live Gas Price ---")
    gas = get_live_gas_price_gwei()
    print("\n--- Testing Aave V3 On-Chain Smart Contract eth_call ---")
    sample_wallet = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    data = get_aave_user_account_data(sample_wallet)
    print("Decoded Position:", data)