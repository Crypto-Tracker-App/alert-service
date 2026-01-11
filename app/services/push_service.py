import json
import requests
import logging
from app.models import PushSubscription
from app.extensions import db
from app.utils.resilience import retry, circuit_breaker

logger = logging.getLogger(__name__)

def subscribe_to_push(user_id: str, subscription_data: dict) -> PushSubscription:
    """Store a push notification subscription for a user."""
    subscription = PushSubscription(
        user_id=user_id,
        subscription_data=json.dumps(subscription_data),
        is_active=True
    )
    db.session.add(subscription)
    db.session.commit()
    return subscription

def get_user_subscriptions(user_id: str):
    """Get all active push subscriptions for a user."""
    return PushSubscription.query.filter(
        PushSubscription.user_id == user_id,
        PushSubscription.is_active == True
    ).all()

@retry(max_attempts=2, delay=1)
@circuit_breaker(failure_threshold=5, recovery_timeout=60, name="push_endpoint")
def _send_push_to_endpoint(endpoint: str, payload: dict) -> None:
    """Send push notification to endpoint with resilience."""
    requests.post(endpoint, json=payload, timeout=5)

def send_push_notification(user_id: str, title: str, body: str, data: dict = None) -> bool:
    """Send a push notification to all active subscriptions for a user."""
    subscriptions = get_user_subscriptions(user_id)
    
    if not subscriptions:
        return False
    
    success = False
    for sub in subscriptions:
        try:
            subscription_data = json.loads(sub.subscription_data)
            endpoint = subscription_data.get('endpoint')
            
            if endpoint:
                # Send notification payload
                payload = {
                    "notification": {
                        "title": title,
                        "body": body,
                        "icon": "/crypto-icon.png",
                        "data": data or {}
                    }
                }
                
                _send_push_to_endpoint(endpoint, payload)
                success = True
        except Exception as e:
            logger.warning(f"Failed to send push notification: {e}")
    return success

def trigger_alert_push_notification(user_id: str, coin_id: str, current_price: float, threshold_price: float) -> bool:
    """Trigger a push notification when an alert threshold is met."""
    return send_push_notification(
        user_id=user_id,
        title="Price Alert Triggered!",
        body=f"{coin_id.upper()} reached ${current_price:.2f}",
        data={
            "coin_id": coin_id,
            "current_price": current_price,
            "threshold_price": threshold_price
        }
    )
