from flask import Blueprint, request, jsonify, g
from app.services.alert_service import create_alert, get_user_alerts, deactivate_alert
from app.services.push_service import subscribe_to_push
from app.middleware.auth_middleware import require_auth

alerts_blueprint = Blueprint('alerts', __name__)

@alerts_blueprint.route('/set-alert', methods=['POST'])
@require_auth
def set_alert():
    """
    Set a custom price alert for a coin.
    
    Request body:
    {
        "coin_id": "bitcoin",
        "threshold_price": 50000
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'coin_id' not in data or 'threshold_price' not in data:
            return jsonify({"error": "Missing required fields: coin_id, threshold_price"}), 400
        
        coin_id = data['coin_id'].lower().strip()
        threshold_price = float(data['threshold_price'])
        
        if threshold_price <= 0:
            return jsonify({"error": "threshold_price must be greater than 0"}), 400
        
        # Get user_id from auth middleware
        user_id = g.current_user['user_id']
        
        alert = create_alert(user_id, coin_id, threshold_price)
        
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
    """Get all active alerts for the current user."""
    try:
        user_id = g.current_user['user_id']
        alerts = get_user_alerts(user_id)
        
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
    """Deactivate an alert."""
    try:
        success = deactivate_alert(alert_id)
        
        if not success:
            return jsonify({"error": "Alert not found"}), 404
        
        return jsonify({"message": "Alert deactivated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@alerts_blueprint.route('/subscribe-notifications', methods=['POST'])
@require_auth
def subscribe_notifications():
    """Register a push notification subscription."""
    try:
        data = request.get_json()
        
        if not data or 'subscription' not in data:
            return jsonify({"error": "Missing subscription data"}), 400
        
        user_id = g.current_user['user_id']
        subscription = subscribe_to_push(user_id, data['subscription'])
        
        return jsonify({"message": "Subscription registered successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@alerts_blueprint.route('/check-alerts', methods=['POST'])
def check_alerts():
    """
    Internal endpoint called by pricing-service after market data updates.
    No authentication required as it's called from pricing-service.
    """
    try:
        from app.services.alert_service import check_all_alerts
        check_all_alerts()
        return jsonify({"message": "Alert check completed"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
