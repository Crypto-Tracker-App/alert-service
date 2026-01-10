from flask import Flask
from os import getenv
from flasgger import Swagger

from .config import DevelopmentConfig, ProductionConfig, TestingConfig
from .extensions import db, mail, scheduler


def create_app():
    app = Flask(__name__)
    
    # Load configuration based on environment
    env = getenv('FLASK_ENV', 'development')
    if env == 'production':
        app.config.from_object(ProductionConfig)
    elif env == 'testing':
        app.config.from_object(TestingConfig)
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
            'BearerAuth': {
                'type': 'apiKey',
                'name': 'Authorization',
                'scheme': 'bearer',
                'bearerFormat': 'bearer',
                'in': 'header',
                'description': 'Type in the *\'Value\'* input box below: **\'Bearer &lt;JWT&gt;\'**, where JWT is the token',
            }
        },
        "security": [
            {"BearerAuth": []}
        ],
        "tags": [
            {
                "name": "Health",
                "description": "Health and readiness endpoints"
            }
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
    mail.init_app(app)
    
    # Register blueprints
    from .api import alerts_blueprint
    from .api.health import health_bp
    app.register_blueprint(health_bp)
    app.register_blueprint(alerts_blueprint, url_prefix='/api')
    
    # Create tables
    with app.app_context():
        db.create_all()
        
        # Start scheduler for daily price checks (only in production/development)
        if not app.config.get('TESTING', False) and not scheduler.running:
            from .services.alert_service import check_all_alerts
            scheduler.add_job(check_all_alerts, 'cron', hour=0, minute=0, id='check_alerts_daily', args=[app])
            scheduler.start()
    
    return app