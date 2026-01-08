import json
import logging
from os import getenv
from webpush import webpush, WebPushException
from app.models import PushSubscription
from app.extensions import db

logger = logging.getLogger(__name__)

# Get VAPID keys from environment variables
VAPID_PUBLIC_KEY = getenv('VAPID_PUBLIC_KEY')
VAPID_PRIVATE_KEY = getenv('VAPID_PRIVATE_KEY')
VAPID_CLAIMS = {
    'sub': f"mailto:{getenv('VAPID_EMAIL', 'admin@cryptotracker.com')}"
}

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

def send_push_notification(user_id: str, title: str, body: str, data: dict = None) -> bool:
    """Send a push notification to all active subscriptions for a user using Web Push Protocol."""
    subscriptions = get_user_subscriptions(user_id)
    
    if not subscriptions:
        logger.warning(f"No active push subscriptions found for user {user_id}")
        return False
    
    # Prepare the notification payload
    payload = {
        "title": title,
        "body": body,
        "icon": "/crypto-icon.png",
        "badge": "/crypto-badge.png",
        "data": data or {}
    }
    
    success = False
    for sub in subscriptions:
        try:
            subscription_data = json.loads(sub.subscription_data)
            
            # Send using Web Push Protocol with proper encryption
            webpush(
                subscription_info=subscription_data,
                data=json.dumps(payload),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS,
                timeout=10
            )
            logger.info(f"Push notification sent successfully to user {user_id}")
            success = True
        except WebPushException as e:
            # Handle specific push exceptions (e.g., invalid subscription)
            if e.response.status_code == 410:
                # Subscription is no longer valid, deactivate it
                sub.is_active = False
                db.session.commit()
                logger.warning(f"Subscription for user {user_id} is invalid, deactivated")
            else:
                logger.error(f"Web Push error: {e}")
        except Exception as e:
            logger.error(f"Failed to send push notification to user {user_id}: {e}")
            continue
    
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
