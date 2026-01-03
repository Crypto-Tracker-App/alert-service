import requests
from typing import Optional, Dict

COINGECKO_API_BASE = "https://api.coingecko.com/api/v3"

def get_coin_price(coin_id: str) -> Optional[float]:
    """
    Fetch the current price of a coin from CoinGecko API.
    
    Args:
        coin_id: The CoinGecko coin ID (e.g., 'bitcoin', 'ethereum')
    
    Returns:
        The current price in USD or None if fetch fails
    """
    try:
        url = f"{COINGECKO_API_BASE}/simple/price"
        params = {
            "ids": coin_id,
            "vs_currencies": "usd"
        }
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        price = data.get(coin_id, {}).get("usd")
        return price
    except Exception as e:
        print(f"Error fetching price for {coin_id}: {str(e)}")
        return None
