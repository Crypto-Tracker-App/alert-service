import jwt
import os
import logging
from flask import current_app

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"

def get_secret_key():
    """Get SECRET_KEY from Flask app config, fallback to environment."""
    try:
        return current_app.config.get('SECRET_KEY', os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production"))
    except RuntimeError:
        # Outside of app context
        return os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

class JWTService:
    @staticmethod
    def verify_token(token: str) -> dict:
        """Verify and decode a JWT token."""
        try:
            secret_key = get_secret_key()
            payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
            return {
                'user_id': payload.get('user_id'),
                'username': payload.get('username')
            }
        except jwt.ExpiredSignatureError:
            logger.error("Token has expired")
            return None
        except jwt.InvalidTokenError:
            logger.error("Invalid token")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}", exc_info=True)
            return None
