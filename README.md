# Alert Service

A microservice for managing cryptocurrency price alerts in the Azure Crypto Tracker Application. This service monitors cryptocurrency prices and triggers alerts when specified conditions are met.

## Overview

The Alert Service is part of the Azure Crypto Tracker ecosystem and provides the following functionality:
- Create, update, and delete cryptocurrency price alerts
- Monitor price changes and trigger notifications
- Send alerts via email and push notifications
- JWT-based authentication
- Full Swagger/OpenAPI documentation

## Prerequisites

- Python 3.11+
- Docker (for containerization)
- Azure CLI (for deployment to AKS)
- kubectl (for Kubernetes management)
- Git

## Installation

### Local Development Setup

1. **Clone the repository**
```bash
cd /Users/matjazmadon/Development/crypto_tracker/alert-service
```

2. **Create a Python virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
Create a `.env` file in the root directory with the necessary environment variables:
```bash
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your_secret_key
JWT_SECRET=your_jwt_secret
DATABASE_URL=your_database_url
```

## Running the Application

### Local Development

Run the Flask development server:
```bash
python wsgi.py
```

The application will be available at `http://localhost:5000`

### Docker

Build and run the Docker image locally:
```bash
docker build -t alert-service:latest .
docker run -p 5000:5000 alert-service:latest
```

## Testing

Run the test suite using pytest:
```bash
PYTHONPATH="${PYTHONPATH}:$(pwd)" pytest tests/ -v
```

Run specific test file:
```bash
PYTHONPATH="${PYTHONPATH}:$(pwd)" pytest tests/test_health.py -v
```

## API Documentation

Once the service is running, access the Swagger/OpenAPI documentation:
- **Interactive UI**: `http://localhost:5000/apidocs/`
- **API Specification**: `http://localhost:5000/apispec.json`

## Project Structure

```
alert-service/
├── app/
│   ├── __init__.py           # Flask app initialization
│   ├── config.py             # Configuration settings
│   ├── extensions.py         # Flask extensions
│   ├── api/
│   │   ├── alerts.py         # Alert endpoints
│   │   └── health.py         # Health check endpoint
│   ├── middleware/
│   │   └── auth_middleware.py # JWT authentication middleware
│   ├── models/
│   │   └── models.py         # Database models
│   ├── services/
│   │   ├── alert_service.py  # Alert business logic
│   │   ├── coin_service.py   # Cryptocurrency data service
│   │   ├── email_service.py  # Email notification service
│   │   ├── jwt_service.py    # JWT token management
│   │   └── push_service.py   # Push notification service
│   └── utils/
│       └── resilience.py     # Resilience patterns
├── tests/                     # Test suite
├── Dockerfile                 # Container image definition
├── requirements.txt          # Python dependencies
├── wsgi.py                   # Application entry point
└── pytest.ini                # Pytest configuration
```

## Authentication

The Alert Service uses JWT (JSON Web Tokens) for authentication. Include the JWT token in the Authorization header:

```bash
Authorization: Bearer <your_jwt_token>
```

## Production Deployment

### Automated Deployment with GitHub Actions

The project uses GitHub Actions for CI/CD with the `build-and-push-acr.yml` workflow. This workflow automates the entire deployment process:

#### How It Works

1. **Trigger**: Every push to the `main` branch triggers the workflow
2. **Test**: Runs the full test suite to ensure code quality
3. **Build**: Builds a Docker image and pushes it to Azure Container Registry (ACR)
4. **Deploy**: Automatically deploys the new image to the Azure Kubernetes Service (AKS) cluster

#### Workflow Stages

**1. Test Stage**
- Checks out the code
- Sets up Python 3.11
- Installs dependencies
- Runs all tests with pytest

**2. Build and Push Stage** (runs after tests pass)
- Sets up Docker Buildx for multi-platform builds
- Logs in to ACR using stored credentials
- Builds and pushes the image to `cryptotracker.azurecr.io/alert-service` with tags:
  - `<commit_sha>` (specific commit)
  - `latest` (most recent)

**3. Deploy to AKS Stage** (runs after image is pushed)
- Authenticates to Azure using OIDC
- Sets the AKS cluster context
- Restarts the alert-service deployment to pull the new image
- Waits for the rollout to complete (max 3 minutes)

#### Committing to Production

To deploy to production, follow these steps:

1. **Make your changes and commit**
```bash
git add .
git commit -m "feat: add new alert feature"
```

2. **Push to main branch**
```bash
git push origin main
```

3. **Monitor the deployment**
   - Go to GitHub Actions in your repository
   - Click on the triggered workflow to see real-time logs
   - The workflow will:
     - Run all tests
     - Build and push the Docker image to ACR
     - Deploy to the AKS cluster in the `crypto-tracker` resource group

#### Required GitHub Secrets

The workflow requires the following GitHub secrets to be configured:
- `ACR_USERNAME`: Azure Container Registry username
- `ACR_PASSWORD`: Azure Container Registry password
- `AZURE_CLIENT_ID`: Azure service principal client ID
- `AZURE_TENANT_ID`: Azure tenant ID
- `AZURE_SUBSCRIPTION_ID`: Azure subscription ID

#### Required GitHub Variables

- `AKS_NAME`: Name of the AKS cluster (crypto-tracker)
- `AKS_RG`: Resource group name (crypto-tracker)

#### Deployment Verification

After the workflow completes:

```bash
# Check the deployment status
kubectl get deployment alert-service
kubectl get pods -l app=alert-service

# View recent logs
kubectl logs -l app=alert-service --tail=50
```

#### Rollback

If issues occur, rollback to the previous version:

```bash
kubectl rollout undo deployment/alert-service
kubectl rollout status deployment/alert-service
```

## Contributing

1. Create a feature branch from `main`
2. Make your changes and write tests
3. Run the test suite locally to ensure all tests pass
4. Commit and push to your branch
5. Create a pull request

## Support

For issues or questions, contact the development team or open an issue in the repository.