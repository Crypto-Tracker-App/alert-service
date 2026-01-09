import requests
from typing import Optional
import logging
from flask import current_app

logger = logging.getLogger(__name__)

def get_pricing_service_url():
    """Get pricing service URL from config or use default."""
    try:
        url = current_app.config.get("PRICING_SERVICE_URL", "http://pricing-service:12000")
        logger.debug(f"[COIN] Using PRICING_SERVICE_URL from config: {url}")
        return url
    except RuntimeError:
        url = "http://pricing-service:12000"
        logger.debug(f"[COIN] Using default PRICING_SERVICE_URL: {url}")
        return url

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
        url = f"{pricing_service_url}/coin/{coin_id}"
        logger.info(f"[COIN] Fetching price from {url} (timeout: 5s)")
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
