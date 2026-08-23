"""
Flask Extensions Module
"""
import logging
import socket
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


_log = logging.getLogger(__name__)


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

# Redis client (None when not connected so callers can degrade gracefully)
redis_client = None


def _is_redis_reachable(app) -> bool:
    """Quick TCP-level reachability probe to the configured Redis host.

    Doing this BEFORE handing a socket to redis-py avoids long blocking
    connect timeouts when the user simply doesn't have Redis running.
    """
    host = app.config.get('CACHE_REDIS_HOST', 'localhost')
    port = int(app.config.get('CACHE_REDIS_PORT', 6379))
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except (OSError, socket.timeout):
        return False


def init_redis(app):
    """Initialize Redis client.

    Designed to be non-fatal: if Redis is not reachable (e.g. local
    development without a Redis server installed) we log a warning and
    fall back to in-memory backends. Callers that hold a reference to
    ``redis_client`` should treat ``None`` as "Redis unavailable".
    """
    global redis_client

    # Skip entirely in testing
    if app.config.get('TESTING'):
        redis_client = None
        return None

    # Quick reachability probe so we don't pay redis-py's full connect
    # timeout on every app startup when Redis isn't running.
    if not _is_redis_reachable(app):
        _log.warning(
            "Redis is not reachable at %s:%s. "
            "Continuing without Redis (cache/session will use fallback).",
            app.config.get('CACHE_REDIS_HOST', 'localhost'),
            app.config.get('CACHE_REDIS_PORT', 6379),
        )
        redis_client = None
        return None

    try:
        redis_client = redis.Redis(
            host=app.config.get('CACHE_REDIS_HOST', 'localhost'),
            port=app.config.get('CACHE_REDIS_PORT', 6379),
            db=app.config.get('CACHE_REDIS_DB', 0),
            password=app.config.get('CACHE_REDIS_PASSWORD'),
            decode_responses=True,
            socket_connect_timeout=1.0,
            socket_timeout=1.0,
        )
        redis_client.ping()
        return redis_client
    # redis.RedisError covers redis.ConnectionError, redis.TimeoutError, etc.
    # OSError covers the raw socket errors that bubble up on Windows when
    # the target port is closed (WinError 10061) — these are NOT subclasses
    # of redis.ConnectionError on some platforms/Python versions, so we
    # must catch them explicitly.
    except (redis.RedisError, OSError) as exc:
        _log.warning(
            "Redis connection failed (%s: %s). "
            "Continuing without Redis (cache/session will use fallback).",
            type(exc).__name__, exc,
        )
        redis_client = None
        return None


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    from app.models.user import User
    return User.query.get(int(user_id))


login_manager.login_view = 'user.login'
login_manager.login_message = 'لطفاً وارد حساب کاربری خود شوید.'
login_manager.login_message_category = 'warning'
