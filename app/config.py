import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    PORT = int(os.environ.get("PORT", 5000))

    DB_USER = os.environ.get("POSTGRES_USER")
    DB_PASS = os.environ.get("POSTGRES_PASSWORD")
    DB_NAME = os.environ.get("POSTGRES_DB")
    DB_PORT = os.environ.get("DB_PORT", os.environ.get("POSTGRES_PORT", "5432"))
    DB_HOST = os.environ.get("DB_HOST")

    SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 3600,
        "pool_timeout": 30,
        "echo": False
    }

    MAX_CONTENT_LENGTH = 1 * 1024 * 1024
    JSON_MAX_CONTENT_LENGTH = 16 * 1024

    AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL", "http://user-service:5000")
    PRICING_SERVICE_URL = os.environ.get("PRICING_SERVICE_URL", "http://pricing-service:5000")
    FRONTEND_URL = os.environ.get("FRONTEND_URL")

    # Email Configuration (SMTP)
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "True") == "True"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False