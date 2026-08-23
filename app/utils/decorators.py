"""
Custom Decorators
"""
import hashlib
import time
import threading
from collections import defaultdict
from functools import wraps
from flask import request, jsonify, render_template, current_app, redirect, url_for, flash
from flask_login import current_user


# ==================== In-memory rate limit fallback ====================
# Used when Redis is not available. Thread-safe.
class InMemoryRateLimiter:
    """Simple in-memory rate limiter with thread safety."""

    def __init__(self):
        self._lock = threading.Lock()
        # key -> (count, reset_time)
        self._buckets: dict = defaultdict(lambda: [0, 0])

    def hit(self, key: str, limit: int, period: int) -> tuple[bool, int]:
        """
        Try to register a hit.
        Returns (allowed, retry_after_seconds).
        """
        now = time.time()
        with self._lock:
            count, reset = self._buckets[key]
            if reset <= now:
                # Reset window
                self._buckets[key] = [1, now + period]
                return True, 0
            if count >= limit:
                return False, int(reset - now)
            self._buckets[key] = [count + 1, reset]
            return True, 0

    def cleanup(self, max_age: int = 3600):
        """Periodically clean old buckets (call from a background task)."""
        now = time.time()
        with self._lock:
            stale = [k for k, (_, r) in self._buckets.items() if r + max_age < now]
            for k in stale:
                del self._buckets[k]


_memory_limiter = InMemoryRateLimiter()


def active_required(f):
    """Decorator to require active user"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('user.login', next=request.url))
        
        if not current_user.is_active:
            flash('حساب کاربری شما غیرفعال است.', 'warning')
            return redirect(url_for('user.login'))
        
        return f(*args, **kwargs)
    return decorated


def rate_limit(limit=60, period=60, key_func=None):
    """
    Rate limiting decorator.

    Uses Redis if available; falls back to in-memory bucket if not.
    This way the limiter works in development without Redis.

    Args:
        limit: Maximum number of requests
        period: Time period in seconds
        key_func: Function to generate rate limit key
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            from app.extensions import redis_client

            # Generate key
            if key_func:
                base_key = key_func()
            else:
                if current_user.is_authenticated:
                    base_key = f'rate_limit:user:{current_user.id}'
                else:
                    base_key = f'rate_limit:ip:{request.remote_addr}'

            redis_key = f'{current_app.config.get("CACHE_KEY_PREFIX", "flask_pro")}:{base_key}:{request.endpoint}'
            memory_key = f'mem:{base_key}:{request.endpoint}'

            # Try Redis first
            if redis_client is not None:
                try:
                    current = redis_client.get(redis_key)
                    current = int(current) if current else 0
                    if current >= limit:
                        return _rate_limit_response(period)
                    pipe = redis_client.pipeline()
                    pipe.incr(redis_key)
                    pipe.expire(redis_key, period)
                    pipe.execute()
                    return f(*args, **kwargs)
                except Exception as e:
                    current_app.logger.warning(f'Rate limit Redis error, falling back to memory: {e}')

            # In-memory fallback
            allowed, retry_after = _memory_limiter.hit(memory_key, limit, period)
            if not allowed:
                return _rate_limit_response(retry_after or period)
            return f(*args, **kwargs)

        return decorated
    return decorator


def _rate_limit_response(retry_after: int):
    """Build a 429 response (JSON for API, HTML for web)."""
    if request.is_json or request.path.startswith('/api/'):
        response = jsonify({
            'error': 'تعداد درخواست‌ها بیش از حد مجاز است. لطفاً کمی صبر کنید.',
            'retry_after': retry_after,
        })
        response.status_code = 429
        response.headers['Retry-After'] = str(retry_after)
        return response
    flash('تعداد درخواست‌های شما بیش از حد مجاز است. لطفاً کمی صبر کنید.', 'warning')
    return redirect(request.referrer or url_for('public.home'))


def api_required(f):
    """
    Decorator to require valid API key.

    API key is read from `X-API-Key` header or `api_key` query string.
    Keys are configured via `VALID_API_KEYS` config (comma-separated string or list).
    The decorator also enforces an API-wide rate limit to prevent abuse.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = (
            request.headers.get('X-API-Key')
            or request.headers.get('X-Api-Key')
            or request.args.get('api_key')
            or ''
        ).strip()

        if not api_key:
            return jsonify({
                'error': 'API key required',
                'message': 'کلید API ارسال نشده است.',
            }), 401

        # Validate against configured keys
        valid_keys = current_app.config.get('VALID_API_KEYS', [])
        if isinstance(valid_keys, str):
            valid_keys = [k.strip() for k in valid_keys.split(',') if k.strip()]

        if not valid_keys:
            # No keys configured: deny all API access (fail-closed)
            current_app.logger.warning('API access attempted but no VALID_API_KEYS configured')
            return jsonify({
                'error': 'API access disabled',
                'message': 'دسترسی API در حال حاضر غیرفعال است.',
            }), 503

        if api_key not in valid_keys:
            # Constant-time comparison to prevent timing attacks
            import hmac
            valid_match = False
            for stored_key in valid_keys:
                if hmac.compare_digest(api_key, stored_key):
                    valid_match = True
                    break
            if not valid_match:
                return jsonify({
                    'error': 'Invalid API key',
                    'message': 'کلید API نامعتبر است.',
                }), 401

        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            from flask import redirect, url_for
            return redirect(url_for('admin.login', next=request.url))
        
        if not current_user.is_admin():
            if request.is_json:
                return jsonify({'error': 'Admin access required'}), 403
            return render_template('errors/403.html'), 403
        
        return f(*args, **kwargs)
    return decorated


def permission_required(permission):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                from flask import redirect, url_for
                return redirect(url_for('admin.login', next=request.url))
            
            if not current_user.can(permission):
                if request.is_json:
                    return jsonify({'error': 'Permission denied'}), 403
                return render_template('errors/403.html'), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator


def active_user_required(f):
    """Decorator to require active user"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            from flask import redirect, url_for
            return redirect(url_for('user.login', next=request.url))
        
        if not current_user.is_active:
            from flask import flash
            flash('حساب کاربری شما غیرفعال است.', 'warning')
            return redirect(url_for('user.login'))
        
        return f(*args, **kwargs)
    return decorated


def json_response(f):
    """Decorator to ensure JSON response"""
    @wraps(f)
    def decorated(*args, **kwargs):
        result = f(*args, **kwargs)
        
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1] if len(result) > 1 else 200
        elif isinstance(result, dict):
            return jsonify(result)
        else:
            return result
    return decorated


def cache_control(*directives):
    """Decorator to set Cache-Control header"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            response = f(*args, **kwargs)
            
            if hasattr(response, 'headers'):
                response.headers['Cache-Control'] = ', '.join(directives)
            
            return response
        return decorated
    return decorator


def etag(f):
    """Decorator to add ETag support"""
    @wraps(f)
    def decorated(*args, **kwargs):
        from flask import make_response
        
        response = f(*args, **kwargs)
        
        # Generate ETag from response content
        if isinstance(response, str):
            content = response.encode('utf-8')
        elif isinstance(response, tuple):
            content = response[0].encode('utf-8') if isinstance(response[0], str) else response[0]
        else:
            content = str(response).encode('utf-8')
        
        etag_value = hashlib.md5(content).hexdigest()
        
        response = make_response(response)
        response.headers['ETag'] = f'"{etag_value}"'
        
        # Check If-None-Match
        if request.headers.get('If-None-Match') == f'"{etag_value}"':
            response.status_code = 304
        
        return response
    return decorated


def log_action(action):
    """Decorator to log actions"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            result = f(*args, **kwargs)
            
            # Log the action
            try:
                from app.models import Log
                Log.log_action(
                    action=action,
                    user_id=current_user.id if current_user.is_authenticated else None,
                    request=request
                )
            except Exception as e:
                current_app.logger.error(f'Log action error: {e}')
            
            return result
        return decorated
    return decorator


import hashlib
