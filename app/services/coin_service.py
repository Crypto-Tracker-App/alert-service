import requests
from typing import Optional
import logging
from flask import current_app
from app.utils.resilience import retry, circuit_breaker

logger = logging.getLogger(__name__)

def get_pricing_service_url():
    """Get pricing service URL from config or use default."""
    try:
        url = current_app.config.get("PRICING_SERVICE_URL", "http://pricing-service:12000")
        logger.info(f"[COIN] App context available. Using PRICING_SERVICE_URL from config: {url}")
        return url
    except RuntimeError as e:
        url = "http://pricing-service:12000"
        logger.warning(f"[COIN] No app context (RuntimeError: {str(e)}). Using fallback PRICING_SERVICE_URL: {url}")
        return url

@retry(max_attempts=3, delay=1)
@circuit_breaker(failure_threshold=5, recovery_timeout=60, name="pricing_service")
def _fetch_coin_price(url: str) -> dict:
    """Internal method to fetch coin price with resilience."""
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    return response.json()

def get_coin_price(coin_id: str) -> Optional[float]:
    """
    Fetch the current price of a coin from the pricing-service.
    
    Args:
        coin_id: The coin ID (e.g., 'bitcoin', 'ethereum')
    
    Returns:
        The current price in USD or None if fetch fails
    """
    try:
        pricing_service_url = get_pricing_service_url()
        url = f"{pricing_service_url}/api/coin/{coin_id}"
        logger.info(f"[COIN] Fetching price from {url} (timeout: 5s)")
        
        data = _fetch_coin_price(url)
        
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
        pricing_service_url = get_pricing_service_url()
        logger.error(f"[COIN] Timeout fetching price for {coin_id} from {pricing_service_url} (timeout: 5s)")
        return None
    except requests.exceptions.ConnectionError as e:
        pricing_service_url = get_pricing_service_url()
        logger.error(f"[COIN] Connection error fetching price for {coin_id} from {pricing_service_url}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"[COIN] Error fetching price for {coin_id}: {str(e)}", exc_info=True)
        return None