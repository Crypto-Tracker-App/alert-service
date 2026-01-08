import json
import requests
from app.models import PushSubscription
from app.extensions import db

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
    """Send a push notification to all active subscriptions for a user."""
    subscriptions = get_user_subscriptions(user_id)
    
    if not subscriptions:
        return False
    
    success = False
    for sub in subscriptions:
        try:
            subscription_data = json.loads(sub.subscription_data)
            # Using web push protocol - can be replaced with actual web push library
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
                
                # In production, use pywebpush library for proper encryption
                # For now, send to local endpoint
                requests.post(
                    endpoint,
                    json=payload,
                    timeout=5
                )
                success = True
        except Exception as e:
            print(f"Failed to send push notification: {e}")
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
