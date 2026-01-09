from app.models import Alert, AlertTriggerHistory
from app.extensions import db
from app.services.coin_service import get_coin_price
from app.services.email_service import send_alert_email
from sqlalchemy import and_

def create_alert(user_id: str, user_email: str, coin_id: str, threshold_price: float) -> tuple:
    """Create a new price alert.
    
    Args:
        user_id: The user's ID
        user_email: The user's email address
        coin_id: The cryptocurrency ID
        threshold_price: The price threshold for the alert
    
    Returns:
        tuple: (alert object, user_email) for subsequent operations
    """
    alert = Alert(
        user_id=user_id,
        user_email=user_email,
        coin_id=coin_id,
        threshold_price=threshold_price,
        is_active=True
    )
    db.session.add(alert)
    db.session.commit()
    return alert, user_email 

def check_alert_and_notify(alert: Alert, user_email: str = None) -> bool:
    """
    Check a single alert and trigger a notification if the threshold is met.
    
    Args:
        alert: Alert object to check
        user_email: User email address (required for notifications)
        
    Returns:
        bool: True if notification was triggered, False otherwise
    """
    if not user_email:
        print(f"check_alert_and_notify: No user email provided for alert {alert.id}")
        return False
    
    try:
        current_price = get_coin_price(alert.coin_id)
        print(f"check_alert_and_notify: Got price for {alert.coin_id}: {current_price}")
        
        if current_price is None:
            print(f"check_alert_and_notify: Could not fetch price for {alert.coin_id}")
            return False
        
        if current_price >= alert.threshold_price:
            print(f"check_alert_and_notify: Alert threshold met! {current_price} >= {alert.threshold_price}")
            return trigger_alert_email(
                user_id=alert.user_id,
                user_email=user_email,
                coin_id=alert.coin_id,
                current_price=current_price,
                threshold_price=alert.threshold_price,
                alert_id=alert.id
            )
        else:
            print(f"check_alert_and_notify: Threshold not met. {current_price} < {alert.threshold_price}")
        return False
    except Exception as e:
        print(f"check_alert_and_notify: Error checking alert {alert.id}: {e}")
        return False

def trigger_alert_email(user_id: str, user_email: str, coin_id: str, 
                        current_price: float, threshold_price: float, 
                        alert_id: str) -> bool:
    """
    Trigger an email notification when an alert threshold is met.
    
    Args:
        user_id: The user's ID
        user_email: The user's email address
        coin_id: The cryptocurrency ID
        current_price: The current price
        threshold_price: The alert threshold price
        alert_id: The alert ID for tracking
    
    Returns:
        bool: True if email was sent successfully
    """
    email_sent = send_alert_email(
        recipient_email=user_email,
        coin_id=coin_id,
        current_price=current_price,
        threshold_price=threshold_price
    )
    
    # Record this trigger in history
    history = AlertTriggerHistory(
        alert_id=alert_id,
        user_id=user_id,
        coin_id=coin_id,
        current_price=current_price,
        threshold_price=threshold_price,
        email_sent=email_sent
    )
    db.session.add(history)
    db.session.commit()
    
    return email_sent

def get_user_alerts(user_id: str):
    """Get all active alerts for a user."""
    return Alert.query.filter(
        and_(Alert.user_id == user_id, Alert.is_active == True)
    ).all()

def deactivate_alert(alert_id: str) -> bool:
    """Deactivate an alert."""
    alert = Alert.query.get(alert_id)
    if alert:
        alert.is_active = False
        db.session.commit()
        return True
    return False

def check_all_alerts(app):
    """
    Check all active alerts and trigger email notifications if thresholds are met.
    This function is called by the pricing-service after market data updates.
    
    Args:
        app: Flask application instance
    """
    with app.app_context():
        active_alerts = Alert.query.filter(Alert.is_active == True).all()
        
        alerts_triggered = 0
        for alert in active_alerts:
            try:
                current_price = get_coin_price(alert.coin_id)
                
                if current_price is None:
                    print(f"check_all_alerts: Could not fetch price for {alert.coin_id}")
                    continue
                
                # Check if threshold is met
                if current_price >= alert.threshold_price:
                    print(f"check_all_alerts: Alert triggered for user {alert.user_id}, coin {alert.coin_id} at price {current_price}")
                    
                    # Trigger the email notification
                    email_sent = trigger_alert_email(
                        user_id=alert.user_id,
                        user_email=alert.user_email,
                        coin_id=alert.coin_id,
                        current_price=current_price,
                        threshold_price=alert.threshold_price,
                        alert_id=alert.id
                    )
                    
                    if email_sent:
                        alerts_triggered += 1
                        print(f"check_all_alerts: Email sent successfully for alert {alert.id}")
                    else:
                        print(f"check_all_alerts: Failed to send email for alert {alert.id}")
                        
            except Exception as e:
                print(f"check_all_alerts: Error checking alert {alert.id}: {e}")
        
        print(f"check_all_alerts: Completed. {alerts_triggered} alert(s) triggered.")

