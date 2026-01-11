from flask import Blueprint, request, jsonify, g, current_app
from app.services.alert_service import create_alert, get_user_alerts, deactivate_alert
from app.services.coin_service import get_coin_price
from app.middleware.auth_middleware import require_auth
from app.utils.resilience import retry, circuit_breaker
import logging

alerts_blueprint = Blueprint('alerts', __name__)
logger = logging.getLogger(__name__)


# DEMONSTRATION: Simple decorator usage example
@retry(max_attempts=2, delay=1)
@circuit_breaker(failure_threshold=3, recovery_timeout=30, name="demo_service")
def demo_resilient_call(coin_id: str) -> dict:
    """
    Simple demonstration of @retry and @circuit_breaker decorators.
    
    This function shows:
    1. @retry: Automatically retries failed calls up to 2 times with 1 second delays
    2. @circuit_breaker: Opens circuit after 3 failures, recovers after 30 seconds
    
    The decorators are stacked (retry is innermost, circuit_breaker is outermost).
    This means: request → circuit_breaker → retry → actual function call
    """
    price = get_coin_price(coin_id)
    if price is None:
        raise Exception(f"Failed to fetch price for {coin_id}")
    return {"coin_id": coin_id, "price": price}


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




@alerts_blueprint.route('/test-pricing/<coin_id>', methods=['GET'])
@require_auth
def test_pricing(coin_id):
    """
    Test endpoint to demonstrate circuit breaker and retry patterns.
    
    This endpoint helps visualize the resilience decorators in action:
    - Make requests while pricing service is UP → success
    - Scale pricing service DOWN → see retry attempts then circuit breaker open
    - Wait 60 seconds → circuit breaker recovers automatically
    
    Use for live demonstrations of fault tolerance patterns.
    ---
    tags:
      - Testing
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: coin_id
        type: string
        required: true
        description: The coin ID to test (e.g., bitcoin, ethereum)
        example: "bitcoin"
    responses:
      200:
        description: Successfully fetched coin price (service is healthy)
        schema:
          type: object
          properties:
            status:
              type: string
              example: "success"
            coin_id:
              type: string
              example: "bitcoin"
            price:
              type: number
              format: float
              example: 42500.50
      503:
        description: Pricing service is failing - either retrying or circuit breaker is open
        schema:
          type: object
          properties:
            status:
              type: string
              example: "error"
            error:
              type: string
              example: "Circuit breaker is open for 'pricing_service'. Service unavailable."
    """
    try:
        logger.info(f"[TEST] Testing pricing service with coin_id: {coin_id}")
        
        # Call get_coin_price() which has @retry and @circuit_breaker decorators
        # If pricing service is down:
        #   - First 3 requests: @retry will attempt 3 times (with delays)
        #   - After 5 total failures: @circuit_breaker opens
        #   - Subsequent requests: fail instantly with circuit breaker error
        price = get_coin_price(coin_id)
        
        logger.info(f"[TEST] Successfully fetched price for {coin_id}: ${price}")
        return jsonify({
            "status": "success",
            "coin_id": coin_id,
            "price": price
        }), 200
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[TEST] Error calling pricing service: {error_msg}", exc_info=True)
        
        # Check if this is a circuit breaker error (circuit is OPEN)
        if "Circuit" in error_msg and "OPEN" in error_msg:
            logger.warning(f"[TEST] Circuit breaker is OPEN - failing fast without retry")
            return jsonify({
                "status": "error",
                "error": error_msg,
                "note": "🔴 CIRCUIT BREAKER OPEN: Service is unavailable. Will automatically recover in 60 seconds."
            }), 503
        else:
            # Connection errors, timeouts, or retry exhausted (first request hitting a downed service)
            logger.warning(f"[TEST] Pricing service unavailable - retry mechanism exhausted: {error_msg}")
            return jsonify({
                "status": "error",
                "error": error_msg,
                "note": "⚠️ RETRY EXHAUSTED: Service down. Circuit breaker will open after 5 total failures to prevent cascading requests."
            }), 503
