from app.models import Alert
from app.extensions import db
from app.services.coin_service import get_coin_price
from app.services.push_service import trigger_alert_push_notification
from sqlalchemy import and_

def create_alert(user_id: str, coin_id: str, threshold_price: float) -> Alert:
    """Create a new price alert."""
    alert = Alert(
        user_id=user_id,
        coin_id=coin_id,
        threshold_price=threshold_price,
        is_active=True
    )
    db.session.add(alert)
    db.session.commit()
    return alert 

def check_alert_and_notify(alert: Alert) -> bool:
    """
    Check a single alert and trigger a notification if the threshold is met.
    
    Args:
        alert: Alert object to check
        
    Returns:
        bool: True if notification was triggered, False otherwise
    """
    current_price = get_coin_price(alert.coin_id)
    
    if current_price is not None and current_price >= alert.threshold_price:
        return trigger_alert_push_notification(
            user_id=alert.user_id,
            coin_id=alert.coin_id,
            current_price=current_price,
            threshold_price=alert.threshold_price
        )
    return False

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
    Check all active alerts and trigger notifications if thresholds are met.
    This function is called by the scheduler once a day.
    
    Args:
        app: Flask application instance
    """
    with app.app_context():
        active_alerts = Alert.query.filter(Alert.is_active == True).all()
        
        for alert in active_alerts:
            current_price = get_coin_price(alert.coin_id)
            
            if current_price is not None and current_price >= alert.threshold_price:
                trigger_alert_push_notification(
                    user_id=alert.user_id,
                    coin_id=alert.coin_id,
                    current_price=current_price,
                    threshold_price=alert.threshold_price
                )