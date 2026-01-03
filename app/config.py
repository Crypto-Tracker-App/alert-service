from redis import Redis


import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
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

    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_HTTPONLY = True

    FRONTEND_URL = os.environ.get("FRONTEND_URL")

class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_TYPE = "filesystem"
    SESSION_COOKIE_SECURE= False
    
class ProductionConfig(Config):
    DEBUG = False
    SESSION_TYPE = "redis"
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = "session:"
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 4
    SESSION_REDIS = Redis(
        host=os.environ.get("REDIS_HOST"),
        port=int(os.environ.get("REDIS_PORT", 6379)),
        password=os.environ.get("REDIS_PASSWORD"),
        socket_connect_timeout=5,
        retry_on_timeout=True
    )