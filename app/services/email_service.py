from flask_mail import Message
from app.extensions import mail
from flask import render_template_string
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def get_alert_email_template(alert_data: dict) -> str:
    """Get the HTML template for the alert email."""
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                background-color: #f9fafb;
            }
            .container {
                max-width: 600px;
                margin: 0 auto;
                background-color: white;
                padding: 0;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                overflow: hidden;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px 20px;
                text-align: center;
            }
            .header h1 {
                margin: 0;
                font-size: 24px;
                font-weight: 600;
            }
            .content {
                padding: 40px 20px;
            }
            .alert-box {
                background-color: #f0f9ff;
                border-left: 4px solid #0284c7;
                padding: 20px;
                border-radius: 4px;
                margin: 20px 0;
            }
            .alert-box h2 {
                margin-top: 0;
                color: #0284c7;
                font-size: 18px;
            }
            .alert-details {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin: 20px 0;
            }
            .detail-item {
                padding: 15px;
                background-color: #f3f4f6;
                border-radius: 4px;
            }
            .detail-label {
                font-size: 12px;
                color: #6b7280;
                text-transform: uppercase;
                font-weight: 600;
                letter-spacing: 0.5px;
                margin-bottom: 5px;
            }
            .detail-value {
                font-size: 20px;
                font-weight: 600;
                color: #1f2937;
            }
            .price-highlight {
                color: #059669;
                font-weight: 700;
            }
            .footer {
                background-color: #f9fafb;
                padding: 20px;
                text-align: center;
                border-top: 1px solid #e5e7eb;
                font-size: 12px;
                color: #6b7280;
            }
            .cta-button {
                display: inline-block;
                background-color: #667eea;
                color: white;
                padding: 12px 30px;
                border-radius: 4px;
                text-decoration: none;
                font-weight: 600;
                margin: 20px 0;
                transition: background-color 0.3s ease;
            }
            .cta-button:hover {
                background-color: #5568d3;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚨 Price Alert Triggered!</h1>
            </div>
            
            <div class="content">
                <p style="font-size: 16px; margin-bottom: 20px;">
                    Your cryptocurrency alert has been triggered. Here are the details:
                </p>
                
                <div class="alert-box">
                    <h2>{{ coin_name | upper }} Alert</h2>
                    <p style="margin: 10px 0 0 0; color: #666;">
                        Your alert for <strong>{{ coin_name | upper }}</strong> has been triggered.
                    </p>
                </div>
                
                <div class="alert-details">
                    <div class="detail-item">
                        <div class="detail-label">Current Price</div>
                        <div class="detail-value price-highlight">${{ current_price | round(2) }}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Alert Threshold</div>
                        <div class="detail-value">${{ threshold_price | round(2) }}</div>
                    </div>
                </div>
                
                <p style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; border-radius: 4px; margin: 20px 0; font-size: 14px;">
                    <strong>📌 Note:</strong> Your alert triggered when the price reached <strong>${{ current_price | round(2) }}</strong>, which is at or above your threshold of <strong>${{ threshold_price | round(2) }}</strong>.
                </p>
                
                <p style="text-align: center; margin-top: 30px;">
                    <a href="{{ portfolio_url }}" class="cta-button">View Your Portfolio</a>
                </p>
                
                <p style="font-size: 14px; color: #666; margin-top: 30px;">
                    You can manage your alerts anytime by visiting your alerts dashboard.
                </p>
            </div>
            
            <div class="footer">
                <p style="margin: 0;">
                    CryptoTracker Price Alerts | {{ timestamp }}<br>
                    <a href="{{ unsubscribe_url }}" style="color: #667eea; text-decoration: none;">Manage Alert Preferences</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    return html_template


def send_alert_email(recipient_email: str, coin_id: str, current_price: float, 
                     threshold_price: float, portfolio_url: str = None, 
                     unsubscribe_url: str = None, app=None) -> bool:
    """
    Send a professional alert email when a price threshold is met.
    
    Args:
        recipient_email: Email address of the recipient
        coin_id: The cryptocurrency ID (e.g., 'bitcoin', 'ethereum')
        current_price: The current price that triggered the alert
        threshold_price: The threshold price the alert was set for
        portfolio_url: URL to the user's portfolio (optional)
        unsubscribe_url: URL to manage alert preferences (optional)
        app: Flask app instance for context (optional, will use current_app if not provided)
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        from flask import current_app
        
        # Get the app instance for context
        app_instance = app or current_app
        
        # Ensure we're in an app context
        if not app_instance:
            logger.error("[EMAIL] No Flask app context available for sending email")
            return False
        
        # Check if SMTP configuration is available
        if not app_instance.config.get('MAIL_SERVER'):
            logger.warning("[EMAIL] MAIL_SERVER not configured - email sending is disabled")
            return False
        
        logger.debug(f"[EMAIL] Preparing alert email - To: {recipient_email}, Coin: {coin_id}, Price: ${current_price}, Threshold: ${threshold_price}")
        
        # Get the template
        template = get_alert_email_template({
            'coin_id': coin_id,
            'current_price': current_price,
            'threshold_price': threshold_price
        })
        
        # Render the template with context
        html_content = render_template_string(
            template,
            coin_name=coin_id,
            current_price=current_price,
            threshold_price=threshold_price,
            portfolio_url=portfolio_url or "#",
            unsubscribe_url=unsubscribe_url or "#",
            timestamp=datetime.utcnow().strftime("%B %d, %Y at %H:%M UTC")
        )
        
        # Create the email message with sender
        mail_username = app_instance.config.get('MAIL_USERNAME', 'noreply@cryptotracker.com')
        msg = Message(
            subject=f"🚨 {coin_id.upper()} Price Alert: ${current_price:.2f}",
            recipients=[recipient_email],
            html=html_content,
            sender=mail_username
        )
        
        logger.debug(f"[EMAIL] Sending message to {recipient_email}")
        
        # Send the email within app context
        with app_instance.app_context():
            mail.send(msg)
        
        logger.info(f"[EMAIL] Successfully sent alert email to {recipient_email} for {coin_id.upper()}")
        return True
        
    except Exception as e:
        logger.error(f"[EMAIL] Failed to send alert email to {recipient_email}: {e}", exc_info=True)
        return False


def send_test_email(recipient_email: str, app=None) -> bool:
    """
    Send a test email to verify SMTP configuration.
    
    Args:
        recipient_email: Email address to send test email to
        app: Flask app instance for context (optional, will use current_app if not provided)
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        from flask import current_app
        
        # Get the app instance for context
        app_instance = app or current_app
        
        # Ensure we're in an app context
        if not app_instance:
            logger.error("[EMAIL] No Flask app context available for sending email")
            return False
        
        # Check if SMTP configuration is available
        if not app_instance.config.get('MAIL_SERVER'):
            logger.warning("[EMAIL] MAIL_SERVER not configured - email sending is disabled")
            return False
        
        logger.info(f"[EMAIL] Sending test email to {recipient_email}")
        
        mail_username = app_instance.config.get('MAIL_USERNAME', 'noreply@cryptotracker.com')
        msg = Message(
            subject="CryptoTracker - Test Email",
            recipients=[recipient_email],
            body="This is a test email to verify SMTP configuration is working correctly.",
            sender=mail_username
        )
        
        with app_instance.app_context():
            mail.send(msg)
        
        logger.info(f"[EMAIL] Test email successfully sent to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"[EMAIL] Failed to send test email to {recipient_email}: {e}", exc_info=True)
        return False
