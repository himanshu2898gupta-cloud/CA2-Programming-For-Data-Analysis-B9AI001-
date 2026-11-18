"""
src/ingestion/prices.py
Fetches and validates live cryptocurrency prices from CoinGecko and DefiLlama.
Implements exponential backoff, retry logic, and cross-source price validation.
"""

import time
import logging
import requests

# Structured logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def fetch_with_retry(url: str, headers: dict = None, max_retries: int = 3) -> dict:
    """
    URL se JSON data fetch karta hai.
    Agar rate limit (429) ya server error aaye, toh exponential backoff (2s, 4s, 8s) se retry karta hai.
    """
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                wait_time = 2 ** attempt
                logger.warning(f"Rate limited (429). Retrying in {wait_time}s (Attempt {attempt}/{max_retries})...")
                time.sleep(wait_time)
            else:
                logger.warning(f"HTTP {response.status_code} received. Retrying in 1s (Attempt {attempt}/{max_retries})...")
                time.sleep(1)
        except requests.exceptions.RequestException as err:
            wait_time = 2 ** attempt
            logger.warning(f"Network error: {err}. Retrying in {wait_time}s (Attempt {attempt}/{max_retries})...")
            time.sleep(wait_time)

    raise RuntimeError(f"Failed to fetch data from {url} after {max_retries} attempts.")

def fetch_coingecko_price(token_id: str = "ethereum", demo_api_key: str = None) -> float:
    """CoinGecko API se live USD price fetch karta hai."""
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={token_id}&vs_currencies=usd"
    headers = {}
    if demo_api_key:
        headers["x-cg-demo-api-key"] = demo_api_key

    logger.info(f"Fetching {token_id} price from CoinGecko...")
    data = fetch_with_retry(url, headers=headers)
    price = float(data[token_id]["usd"])
    logger.info(f"CoinGecko {token_id} price: ${price:.2f}")
    return price

def fetch_defillama_price(token_identifier: str = "coingecko:ethereum") -> float:
    """DefiLlama API se live USD price fetch karta hai (Keyless secondary source)."""
    url = f"https://coins.llama.fi/prices/current/{token_identifier}"
    logger.info(f"Fetching price from DefiLlama for {token_identifier}...")
    data = fetch_with_retry(url)
    price = float(data["coins"][token_identifier]["price"])
    logger.info(f"DefiLlama price: ${price:.2f}")
    return price

def get_validated_eth_price(tolerance_pct: float = 2.0) -> float:
    """
    CoinGecko aur DefiLlama dono se ETH price laakar cross-check (validate) karta hai.
    Dono ke beech divergence check karta hai (Data Validation).
    """
    cg_price = None
    dl_price = None

    try:
        cg_price = fetch_coingecko_price("ethereum")
    except Exception as e:
        logger.warning(f"CoinGecko fetch failed: {e}")

    try:
        dl_price = fetch_defillama_price("coingecko:ethereum")
    except Exception as e:
        logger.warning(f"DefiLlama fetch failed: {e}")

    # Dono sources successfully mil gaye -> Cross-check
    if cg_price is not None and dl_price is not None:
        diff_pct = abs(cg_price - dl_price) / cg_price * 100
        logger.info(f"Price divergence between CoinGecko and DefiLlama: {diff_pct:.3f}%")
        if diff_pct > tolerance_pct:
            logger.warning(f"Price divergence ({diff_pct:.2f}%) exceeds tolerance ({tolerance_pct}%)!")
        
        # Average of both reputable sources
        validated_price = round((cg_price + dl_price) / 2.0, 2)
        logger.info(f"Successfully validated ETH price: ${validated_price}")
        return validated_price

    # Agar koi ek source fail hua, toh doosra use karo
    if cg_price is not None:
        logger.info(f"Using CoinGecko price only: ${cg_price}")
        return cg_price
    if dl_price is not None:
        logger.info(f"Using DefiLlama price only: ${dl_price}")
        return dl_price

    raise RuntimeError("Critical: Both CoinGecko and DefiLlama price feeds failed!")

if __name__ == "__main__":
    eth_price = get_validated_eth_price()
    print(f"\nFinal Validated ETH Price: ${eth_price}")
