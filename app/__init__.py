from flask import Flask
from os import getenv

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