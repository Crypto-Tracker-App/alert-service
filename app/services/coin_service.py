import requests
from typing import Optional
import logging
from flask import current_app
from app.utils.resilience import retry, circuit_breaker
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# Create a session with no built-in retries to avoid confusion with @retry decorator
session = requests.Session()
adapter = HTTPAdapter(max_retries=Retry(total=0))  # Disable urllib3 retries
session.mount('http://', adapter)
session.mount('https://', adapter)

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

@circuit_breaker(failure_threshold=5, recovery_timeout=15, name="pricing_service")
@retry(max_attempts=3, delay=1)
def _fetch_coin_price(url: str) -> dict:
    """
    Fetch coin price from pricing service with resilience patterns.
    
    Decorator order (outermost to innermost):
    1. @circuit_breaker: Fails fast when service is down (prevents cascading failures)
    2. @retry: Retries transient failures up to 3 times with exponential backoff
    
    This order ensures: circuit breaker can reject requests immediately without retry interference.
    """
    # Use session without built-in retries (we have @retry decorator for that)
    response = session.get(url, timeout=5)
    response.raise_for_status()
    return response.json()

def get_coin_price(coin_id: str) -> Optional[float]:
    """
    Fetch the current price of a coin from the pricing-service.
    
    This function demonstrates circuit breaker and retry patterns:
    - If pricing service is down, _fetch_coin_price() will retry 3 times
    - After 5 consecutive failures, circuit breaker opens and raises immediately
    
    Args:
        coin_id: The coin ID (e.g., 'bitcoin', 'ethereum')
    
    Returns:
        The current price in USD, or None if unavailable
    """
    pricing_service_url = get_pricing_service_url()
    url = f"{pricing_service_url}/api/coin/{coin_id}"
    logger.info(f"[COIN] Fetching price from {url} (timeout: 5s)")
    
    try:
        # _fetch_coin_price() handles retries and circuit breaker
        data = _fetch_coin_price(url)
        
        # Check if response has the expected structure
        if data.get("status") != "success" or "data" not in data:
            logger.warning(f"[COIN] Invalid response structure for {coin_id}: {data}")
            return None
        
        coin_data = data.get("data", {})
        price = coin_data.get("current_price")
        
        if price is not None:
            logger.info(f"[COIN] Successfully fetched price for {coin_id}: ${price}")
            return price
        else:
            logger.warning(f"[COIN] No price data in response for {coin_id}: {coin_data}")
            return None
            
    except Exception as e:
        error_msg = str(e)
        # Check if it's a circuit breaker error
        if "is OPEN" in error_msg:
            logger.error(f"[COIN] Circuit breaker is OPEN - pricing service unavailable")
        elif "Max retries exceeded" in error_msg or "Connection refused" in error_msg:
            logger.error(f"[COIN] Pricing service unavailable - retry mechanism exhausted")
        else:
            logger.error(f"[COIN] Error fetching price: {error_msg}")
        return None