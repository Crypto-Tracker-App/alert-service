from app.models import Alert, AlertTriggerHistory
from app.extensions import db
from app.services.coin_service import get_coin_price
from app.services.email_service import send_alert_email
from sqlalchemy import and_

def create_alert(user_id: str, user_email: str, coin_id: str, threshold_price: float) -> tuple:
    """Create a new price alert.
    
    Returns:
        tuple: (alert object, user_email) for subsequent operations
    """
    alert = Alert(
        user_id=user_id,
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
        return False
        
    current_price = get_coin_price(alert.coin_id)
    
    if current_price is not None and current_price >= alert.threshold_price:
        return trigger_alert_email(
            user_id=alert.user_id,
            user_email=user_email,
            coin_id=alert.coin_id,
            current_price=current_price,
            threshold_price=alert.threshold_price,
            alert_id=alert.id
        )
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
    This function is called by the scheduler.
    
    Args:
        app: Flask application instance
    """
    with app.app_context():
        active_alerts = Alert.query.filter(Alert.is_active == True).all()
        
        for alert in active_alerts:
            # Note: For batch checks, user_email is not available.
            # Email notifications should be triggered when alerts are created.
            # To support batch notifications, user_email would need to be
            # fetched from a user service or stored separately.
            current_price = get_coin_price(alert.coin_id)
            
            if current_price is not None and current_price >= alert.threshold_price:
                # Placeholder: In production, retrieve user_email from user service
                print(f"Alert triggered for user {alert.user_id}, coin {alert.coin_id} at price {current_price}")
