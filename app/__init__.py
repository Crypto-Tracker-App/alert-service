from flask import Flask
from os import getenv
from flasgger import Swagger

from .config import DevelopmentConfig, ProductionConfig
from .extensions import db, scheduler


def create_app():
    app = Flask(__name__)
    
    # Load configuration based on environment
    env = getenv('FLASK_ENV', 'development')
    if env == 'production':
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(DevelopmentConfig)
    
    # Configure Swagger/OpenAPI
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "Alert Service API",
            "description": "Microservice for managing cryptocurrency price alerts",
            "version": "1.0.0"
        },
        "securityDefinitions": {
            "BearerAuth": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT Bearer token for authentication. Format: Bearer <token>"
            }
        },
        "security": [
            {"BearerAuth": []}
        ]
    }
    
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec",
                "route": "/apispec.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs/"
    }
    
    Swagger(app, template=swagger_template, config=swagger_config)
    
    # Initialize extensions
    db.init_app(app)
    
    # Register blueprints
    from .api import alerts_blueprint
    app.register_blueprint(alerts_blueprint, url_prefix='/api')
    
    # Create tables
    with app.app_context():
        db.create_all()
        
        # Start scheduler for daily price checks
        if not scheduler.running:
            from .services.alert_service import check_all_alerts
            scheduler.add_job(check_all_alerts, 'cron', hour=0, minute=0, id='check_alerts_daily')
            scheduler.start()
    
    return app