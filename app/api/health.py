from flask import Blueprint, jsonify
from sqlalchemy import text
from app import db
import logging

health_bp = Blueprint('health', __name__)
logger = logging.getLogger(__name__)


@health_bp.route('/ready', methods=['GET'])
def ready():
    """Readiness probe endpoint
    ---
    tags:
      - Health
    summary: Check if service is ready to accept requests
    description: Returns OK if the service is running. Does not check database connectivity.
    responses:
      200:
        description: Service is ready
        schema:
          type: object
          properties:
            status:
              type: string
              example: ok
            detail:
              type: string
              example: service ready
    """
    return jsonify({
        'status': 'ok',
        'detail': 'service ready'
    }), 200


@health_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint with database connectivity
    ---
    tags:
      - Health
    summary: Check service and database health
    description: Verifies that the service is running and can connect to the database
    responses:
      200:
        description: Service and database are healthy
        schema:
          type: object
          properties:
            status:
              type: string
              example: ok
            detail:
              type: string
              example: database connection ok
      503:
        description: Service is unhealthy (database connection failed)
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            detail:
              type: string
              example: Database connection failed
    """
    try:
        # Attempt database connectivity check
        db.session.execute(text('SELECT 1'))
        return jsonify({
            'status': 'ok',
            'detail': 'database connection ok'
        }), 200
    except Exception as exc:
        logger.error("Health check failed", exc_info=True)
        return jsonify({ 
            'status': 'error',
            'detail': str(exc)
        }), 503
