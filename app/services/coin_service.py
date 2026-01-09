import requests
from typing import Optional
import logging

logger = logging.getLogger(__name__)

PRICING_SERVICE_URL = "http://20.251.246.218/pricing-service"

def get_coin_price(coin_id: str) -> Optional[float]:
    """
    Fetch the current price of a coin from the pricing-service.
    
    Args:
        coin_id: The coin ID (e.g., 'bitcoin', 'ethereum')
    
    Returns:
        The current price in USD or None if fetch fails
    """
    try:
        url = f"{PRICING_SERVICE_URL}/coin/{coin_id}"
        logger.debug(f"[COIN] Fetching price from {url}")
        response = requests.get(url, timeout=5)
        
        # Check for HTTP errors first
        if response.status_code != 200:
            logger.warning(f"[COIN] HTTP {response.status_code} fetching price for {coin_id}. Response: {response.text[:200]}")
            return None
        
        # Check if response body is empty
        if not response.text or not response.text.strip():
            logger.error(f"[COIN] Empty response body for {coin_id} from {url}")
            return None
        
        # Try to parse JSON response
        try:
            data = response.json()
        except Exception as json_error:
            logger.error(f"[COIN] Failed to parse JSON response for {coin_id}: {str(json_error)}")
            logger.error(f"[COIN] Response text: {response.text[:500]}")
            return None
        
        # Check if response has the expected structure
        if data.get("status") != "success" or "data" not in data:
            logger.warning(f"[COIN] Invalid response structure for {coin_id}: {data}")
            return None
        
        coin_data = data.get("data", {})
        price = coin_data.get("current_price")
        
        if price is not None:
            logger.debug(f"[COIN] Successfully fetched price for {coin_id}: ${price}")
            return price
        else:
            logger.warning(f"[COIN] No price data in response for {coin_id}: {coin_data}")
            return None
            
    except requests.exceptions.Timeout:
        logger.error(f"[COIN] Timeout fetching price for {coin_id}")
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"[COIN] Connection error fetching price for {coin_id} from {PRICING_SERVICE_URL}")
        return None
    except Exception as e:
        logger.error(f"[COIN] Error fetching price for {coin_id}: {str(e)}", exc_info=True)
        return None
