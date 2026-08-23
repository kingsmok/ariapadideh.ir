"""
Configuration Module
"""
import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def get_env_bool(key: str, default: bool = False) -> bool:
    """Convert string env var to boolean"""
    value = os.getenv(key, str(default)).lower()
    return value in ('true', '1', 'yes', 'on')


def get_env_list(key: str, default: list = None) -> list:
    """Convert comma-separated env var to list"""
    value = os.getenv(key, '')
    if not value:
        return default or []
    return [item.strip() for item in value.split(',')]


class Config:
    """Base Configuration"""
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    WTF_CSRF_HEADERS = ['X-CSRFToken', 'X-CSRF-Token']
    
    # Session
    SESSION_TYPE = 'redis'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'flask_pro:'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Cookie
    COOKIE_SECURE = get_env_bool('COOKIE_SECURE', True)
    COOKIE_HTTPONLY = True
    COOKIE_SAMESITE = 'Lax'
    
    # Database
    BASE_DIR = Path(__file__).parent.parent
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        f'sqlite:///{BASE_DIR / "instance" / "app.db"}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # SQLite doesn't support pool_size/max_overflow
    if not SQLALCHEMY_DATABASE_URI.startswith('sqlite'):
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
            'pool_size': 10,
            'max_overflow': 20
        }
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {}
    
    # Cache
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'RedisCache')
    CACHE_REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    CACHE_REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    CACHE_REDIS_DB = int(os.getenv('REDIS_DB', 0))
    CACHE_REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
    CACHE_DEFAULT_TIMEOUT = 300
    CACHE_KEY_PREFIX = 'flask_pro'
    
    # File Upload
    UPLOAD_FOLDER = BASE_DIR / 'app' / 'static' / 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'doc', 'docx'}
    IMAGE_ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Image Processing
    IMAGE_THUMBNAIL_SIZE = (300, 300)
    IMAGE_MEDIUM_SIZE = (600, 600)
    IMAGE_LARGE_SIZE = (1200, 1200)
    IMAGE_QUALITY = 85
    IMAGE_FORMAT = 'webp'
    
    # Pagination
    ITEMS_PER_PAGE = 20
    ADMIN_ITEMS_PER_PAGE = 50
    
    # Rate Limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', 6379)}/1"
    RATELIMIT_DEFAULT = "200 per day"
    RATELIMIT_HEADERS_ENABLED = True
    
    # Babel
    BABEL_DEFAULT_LOCALE = 'fa'
    BABEL_DEFAULT_TIMEZONE = 'Asia/Tehran'
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = BASE_DIR / 'logs' / 'app.log'
    
    # Celery
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TIMEZONE = 'Asia/Tehran'
    
    # SEO Defaults
    SITE_NAME = os.getenv('SITE_NAME', 'فلاسک پرو')
    SITE_URL = os.getenv('SITE_URL', 'https://example.com')
    SITE_LANGUAGE = 'fa-IR'
    OG_IMAGE_DEFAULT = '/static/images/og-default.jpg'
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_ADMIN_CHAT_ID = os.getenv('TELEGRAM_ADMIN_CHAT_ID')
    
    # Email
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = get_env_bool('MAIL_USE_TLS', True)
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
    
    # Compress
    COMPRESS_ENABLED = True
    COMPRESS_LEVEL = 6
    COMPRESS_MINIZE_HTML = True


class DevelopmentConfig(Config):
    """Development Configuration"""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{Config.BASE_DIR / "instance" / "dev.db"}'
    CACHE_TYPE = 'SimpleCache'
    WTF_CSRF_ENABLED = False
    COOKIE_SECURE = False


class TestingConfig(Config):
    """Testing Configuration"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    CACHE_TYPE = 'SimpleCache'


class ProductionConfig(Config):
    """Production Configuration"""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    CACHE_TYPE = 'RedisCache'
    RATELIMIT_ENABLED = True
    LOG_LEVEL = 'WARNING'


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
