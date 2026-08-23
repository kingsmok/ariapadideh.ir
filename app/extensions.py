"""
Flask Extensions Module
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_caching import Cache
from flask_compress import Compress
from flask_moment import Moment
from flask_babel import Babel
from flask_assets import Environment
from sqlalchemy.orm import DeclarativeBase
import redis


class Base(DeclarativeBase):
    pass


# Initialize extensions
db = SQLAlchemy(model_class=Base)
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
cache = Cache()
compress = Compress()
moment = Moment()
babel = Babel()
assets = Environment()

# Redis client
redis_client = None


def init_redis(app):
    """Initialize Redis client"""
    global redis_client
    try:
        redis_client = redis.Redis(
            host=app.config.get('CACHE_REDIS_HOST', 'localhost'),
            port=app.config.get('CACHE_REDIS_PORT', 6379),
            db=app.config.get('CACHE_REDIS_DB', 0),
            password=app.config.get('CACHE_REDIS_PASSWORD'),
            decode_responses=True
        )
        redis_client.ping()
    except redis.ConnectionError:
        app.logger.warning("Redis connection failed. Using fallback cache.")
        redis_client = None


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    from app.models.user import User
    return User.query.get(int(user_id))


login_manager.login_view = 'user.login'
login_manager.login_message = 'لطفاً وارد حساب کاربری خود شوید.'
login_manager.login_message_category = 'warning'
