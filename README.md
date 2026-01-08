# Alert Service

A microservice for managing cryptocurrency price alerts and push notifications.

## Setup

### Environment Variables

The alert service requires the following environment variables to be set:

```bash
# Database Configuration
POSTGRES_USER=your_postgres_user
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_DB=alert_service_db
DB_HOST=localhost
DB_PORT=5432

# Application Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
PORT=5001

# Service URLs
AUTH_SERVICE_URL=http://localhost:5000
FRONTEND_URL=http://localhost:3000

# Web Push Notification Configuration (REQUIRED for push notifications)
VAPID_PUBLIC_KEY=your_vapid_public_key
VAPID_PRIVATE_KEY=your_vapid_private_key
VAPID_EMAIL=admin@cryptotracker.com
```

### Generating VAPID Keys

Web Push notifications require VAPID (Voluntary Application Server Identification) keys. Generate them using:

```bash
python -c "from pywebpush import generate_keys; keys = generate_keys(); print(f'Public: {keys[\"public_key\"]}'); print(f'Private: {keys[\"private_key\"]}')"
```

Or use this Python script:

```python
from pywebpush import generate_keys

keys = generate_keys()
print(f"VAPID_PUBLIC_KEY={keys['public_key']}")
print(f"VAPID_PRIVATE_KEY={keys['private_key']}")
```

Copy the output and set these as environment variables.

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations (if applicable)
# ...

# Start the service
python wsgi.py
```

## API Endpoints

### Set Alert
`POST /api/set-alert`

Create a new price alert for a cryptocurrency.

**Request:**
```json
{
  "coin_id": "bitcoin",
  "threshold_price": 50000
}
```

**Response:**
```json
{
  "id": 1,
  "coin_id": "bitcoin",
  "threshold_price": 50000,
  "is_active": true,
  "created_at": "2026-01-08T12:00:00"
}
```

### Get Alerts
`GET /api/alerts`

Retrieve all active alerts for the current user.

### Delete Alert
`DELETE /api/alerts/<alert_id>`

Deactivate an alert.

### Subscribe to Notifications
`POST /api/subscribe-notifications`

Register a push notification subscription.

**Request:**
```json
{
  "subscription": {
    "endpoint": "...",
    "keys": {
      "p256dh": "...",
      "auth": "..."
    }
  }
}
```

### Check Alerts
`POST /api/check-alerts`

Internal endpoint called by the pricing service to check and trigger alerts.

## Push Notifications

Push notifications are triggered automatically when:

1. A new alert is created and the current price already meets the threshold
2. The scheduler checks all alerts once daily (at midnight)

The push notification includes:
- Alert title with coin name
- Current price information
- Threshold price for reference

## Architecture

- **Alert Service**: Manages price alerts and coordinates with other services
- **Push Service**: Handles Web Push Protocol communication with client subscriptions
- **Coin Service**: Fetches current cryptocurrency prices
- **Scheduler**: Runs periodic checks for alert conditions
