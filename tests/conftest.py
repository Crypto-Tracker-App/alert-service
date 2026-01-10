import pytest
import os
from app import create_app, db
from app.models.models import Alert, AlertTriggerHistory


@pytest.fixture
def app():
    """Create and configure a test app."""
    # Set test environment
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['SECRET_KEY'] = 'test-secret-key'
    
    app = create_app()
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's CLI commands."""
    return app.test_cli_runner()


@pytest.fixture
def valid_token(app):
    """Generate a valid JWT token for testing."""
    import jwt
    from datetime import datetime, timedelta, timezone
    
    with app.app_context():
        secret_key = app.config.get('SECRET_KEY')
        payload = {
            'user_id': 'test-user-123',
            'sub': 'test-user@example.com',
            'exp': datetime.now(timezone.utc) + timedelta(hours=1)
        }
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        return token


@pytest.fixture
def auth_headers(valid_token):
    """Return authorization headers with valid token."""
    return {'Authorization': f'Bearer {valid_token}'}
