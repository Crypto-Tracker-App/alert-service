"""Tests for alert service health endpoints."""
import pytest


def test_health_endpoint(client):
    """Test health check endpoint returns 200."""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'
    assert data['detail'] == 'database connection ok'


def test_readiness_endpoint(client):
    """Test readiness endpoint returns 200."""
    response = client.get('/ready')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'
    assert data['detail'] == 'service ready'
