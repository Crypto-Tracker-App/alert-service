from flask import Blueprint, request, jsonify, g, current_app
from app.services.alert_service import create_alert, get_user_alerts, deactivate_alert
from app.middleware.auth_middleware import require_auth
import logging

alerts_blueprint = Blueprint('alerts', __name__)
logger = logging.getLogger(__name__)

@alerts_blueprint.route('/set-alert', methods=['POST'])
@require_auth
def set_alert():
    """
    Set a custom price alert for a coin.
    ---
    tags:
      - Alerts
    security:
      - BearerAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            coin_id:
              type: string
              description: The ID of the cryptocurrency
              example: "bitcoin"
            threshold_price:
              type: number
              format: float
              description: The price threshold to trigger the alert
              example: 50000
          required:
            - coin_id
            - threshold_price
    responses:
      201:
        description: Alert successfully created
        schema:
          type: object
          properties:
            id:
              type: integer
              example: 1
            coin_id:
              type: string
              example: "bitcoin"
            threshold_price:
              type: number
              format: float
              example: 50000
            is_active:
              type: boolean
              example: true
            created_at:
              type: string
              format: date-time
              example: "2026-01-04T12:34:56"
      400:
        description: Invalid request data
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Missing required fields: coin_id, threshold_price"
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
    """
    try:
        data = request.get_json()
        
        if not data or 'coin_id' not in data or 'threshold_price' not in data:
            return jsonify({"error": "Missing required fields: coin_id, threshold_price"}), 400
        
        coin_id = data['coin_id'].lower().strip()
        threshold_price = float(data['threshold_price'])
        
        logger.debug(f"[ALERT] Setting alert: coin_id={coin_id}, threshold_price={threshold_price}")
        
        if threshold_price <= 0:
            logger.warning(f"[ALERT] Invalid threshold price: {threshold_price}")
            return jsonify({"error": "threshold_price must be greater than 0"}), 400
        
        # Get user_id from auth middleware
        user_id = g.current_user['user_id']
        logger.debug(f"[ALERT] User ID: {user_id}")
        
        # Get user email from user-service current-user endpoint
        user_email = user_email = g.current_user.get('username', '')
        if not user_email:
            logger.error(f"[ALERT] Could not retrieve user email for user {user_id}")
            return jsonify({"error": "Could not retrieve user email from user-service"}), 400
        
        logger.info(f"[ALERT] Creating alert for user {user_id} ({user_email}): {coin_id} at ${threshold_price}")
        alert, _ = create_alert(user_id, user_email, coin_id, threshold_price)
        logger.info(f"[ALERT] Alert created with ID: {alert.id}")
        
        # Check if alert threshold is already met and trigger notification immediately
        from app.services.alert_service import check_alert_and_notify
        try:
            logger.debug(f"[ALERT] Checking alert immediately: alert_id={alert.id}")
            notification_sent = check_alert_and_notify(alert, user_email)
            logger.info(f"[ALERT] Immediate alert check for alert {alert.id}: notification_sent={notification_sent}")
        except Exception as e:
            logger.error(f"[ALERT] Error checking alert immediately: {e}", exc_info=True)
            # Don't fail the entire request if immediate check fails
        
        return jsonify({
            "id": alert.id,
            "coin_id": alert.coin_id,
            "threshold_price": alert.threshold_price,
            "is_active": alert.is_active,
            "created_at": alert.created_at.isoformat()
        }), 201
    except ValueError as e:
        return jsonify({"error": f"Invalid value: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@alerts_blueprint.route('/alerts', methods=['GET'])
@require_auth
def get_alerts():
    """
    Retrieve all active alerts for the current user.
    ---
    tags:
      - Alerts
    security:
      - BearerAuth: []
    responses:
      200:
        description: Successfully retrieved user alerts
        schema:
          type: object
          properties:
            alerts:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 1
                  coin_id:
                    type: string
                    example: "bitcoin"
                  threshold_price:
                    type: number
                    format: float
                    example: 50000
                  is_active:
                    type: boolean
                    example: true
                  created_at:
                    type: string
                    format: date-time
                    example: "2026-01-04T12:34:56"
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
    """
    try:
        user_id = g.current_user['user_id']
        logger.debug(f"[ALERT] Fetching alerts for user: {user_id}")
        alerts = get_user_alerts(user_id)
        logger.debug(f"[ALERT] Found {len(alerts)} active alerts for user {user_id}")
        
        return jsonify({
            "alerts": [
                {
                    "id": alert.id,
                    "coin_id": alert.coin_id,
                    "threshold_price": alert.threshold_price,
                    "is_active": alert.is_active,
                    "created_at": alert.created_at.isoformat()
                }
                for alert in alerts
            ]
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@alerts_blueprint.route('/alerts/<alert_id>', methods=['DELETE'])
@require_auth
def delete_alert(alert_id):
    """
    Deactivate an alert by ID.
    ---
    tags:
      - Alerts
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: alert_id
        type: string
        required: true
        description: The ID of the alert to deactivate
        example: "1"
    responses:
      200:
        description: Alert successfully deactivated
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Alert deactivated successfully"
      404:
        description: Alert not found
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Alert not found"
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
    """
    try:
        logger.info(f"[ALERT] Deactivating alert: {alert_id}")
        success = deactivate_alert(alert_id)
        
        if not success:
            logger.warning(f"[ALERT] Alert not found for deactivation: {alert_id}")
            return jsonify({"error": "Alert not found"}), 404
        
        logger.info(f"[ALERT] Alert {alert_id} deactivated successfully")
        return jsonify({"message": "Alert deactivated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@alerts_blueprint.route('/check-alerts', methods=['POST'])
def check_alerts():
    """
    Internal endpoint called by pricing-service after market data updates.
    Performs batch check on all active alerts and triggers notifications if thresholds are met.
    ---
    tags:
      - Alerts
    responses:
      200:
        description: Alert check completed successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Alert check completed"
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
    """
    try:
        logger.info("[ALERT] Starting batch alert check")
        from app.services.alert_service import check_all_alerts
        check_all_alerts(current_app)
        logger.info("[ALERT] Batch alert check completed")
        return jsonify({"message": "Alert check completed"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
