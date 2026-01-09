from app.models import Alert, AlertTriggerHistory
from app.extensions import db
from app.services.coin_service import get_coin_price
from app.services.email_service import send_alert_email
from sqlalchemy import and_
import logging

logger = logging.getLogger(__name__)

def create_alert(user_id: str, user_email: str, coin_id: str, threshold_price: float) -> tuple:
    """Create a new price alert.
    
    Returns:
        tuple: (alert object, user_email) for subsequent operations
    """
    logger.debug(f"[ALERT] Creating new alert - User: {user_id}, Email: {user_email}, Coin: {coin_id}, Threshold: ${threshold_price}")
    
    alert = Alert(
        user_id=user_id,
        coin_id=coin_id,
        threshold_price=threshold_price,
        is_active=True
    )
    db.session.add(alert)
    db.session.commit()
    
    logger.info(f"[ALERT] Alert created successfully - Alert ID: {alert.id}, User: {user_id}, Email: {user_email}")
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
        logger.warning(f"[ALERT] No user email provided for alert {alert.id}")
        return False
    
    try:
        current_price = get_coin_price(alert.coin_id)
        logger.debug(f"[ALERT] Got price for {alert.coin_id}: ${current_price}")
        
        if current_price is None:
            logger.warning(f"[ALERT] Could not fetch price for {alert.coin_id}")
            return False
        
        if current_price >= alert.threshold_price:
            logger.info(f"[ALERT TRIGGERED] Alert ID: {alert.id} | User Email: {user_email} | Coin: {alert.coin_id} | Current Price: ${current_price} >= Threshold: ${alert.threshold_price}")
            return trigger_alert_email(
                user_id=alert.user_id,
                user_email=user_email,
                coin_id=alert.coin_id,
                current_price=current_price,
                threshold_price=alert.threshold_price,
                alert_id=alert.id
            )
        else:
            logger.debug(f"[ALERT] Threshold not met for alert {alert.id}. {current_price} < {alert.threshold_price}")
        return False
    except Exception as e:
        logger.error(f"[ALERT] Error checking alert {alert.id}: {e}", exc_info=True)
        return False

def trigger_alert_email(user_id: str, user_email: str, coin_id: str, 
                        current_price: float, threshold_price: float, 
                        alert_id: str, app=None) -> bool:
    """
    Trigger an email notification when an alert threshold is met.
    
    Args:
        user_id: The user's ID
        user_email: The user's email address
        coin_id: The cryptocurrency ID
        current_price: The current price
        threshold_price: The alert threshold price
        alert_id: The alert ID for tracking
        app: Flask app instance (optional)
    
    Returns:
        bool: True if email was sent successfully
    """
    logger.info(f"[EMAIL] Sending alert email - To: {user_email} | Alert ID: {alert_id} | Coin: {coin_id}")
    
    email_sent = send_alert_email(
        recipient_email=user_email,
        coin_id=coin_id,
        current_price=current_price,
        threshold_price=threshold_price,
        app=app
    )
    
    if email_sent:
        logger.info(f"[EMAIL SENT] Successfully sent to {user_email} - Alert ID: {alert_id}")
    else:
        logger.error(f"[EMAIL FAILED] Failed to send email to {user_email} - Alert ID: {alert_id}")
    
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
    
    logger.debug(f"[ALERT] Trigger history recorded - Alert ID: {alert_id}, Email Sent: {email_sent}")
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
    logger.info("[ALERT] Starting batch check of all active alerts")
    
    with app.app_context():
        active_alerts = Alert.query.filter(Alert.is_active == True).all()
        logger.debug(f"[ALERT] Found {len(active_alerts)} active alerts to check")
        
        for alert in active_alerts:
            # Note: For batch checks, user_email is not available.
            # Email notifications should be triggered when alerts are created.
            # To support batch notifications, user_email would need to be
            # fetched from a user service or stored separately.
            current_price = get_coin_price(alert.coin_id)
            
            if current_price is not None and current_price >= alert.threshold_price:
                logger.warning(f"[ALERT BATCH] Alert triggered for user {alert.user_id}, coin {alert.coin_id} at price ${current_price} (threshold: ${alert.threshold_price}) - Alert ID: {alert.id}")
                # Placeholder: In production, retrieve user_email from user service
            else:
                logger.debug(f"[ALERT BATCH] Alert {alert.id} - no trigger. Current: ${current_price}, Threshold: ${alert.threshold_price}")

