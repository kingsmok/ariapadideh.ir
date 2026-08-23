"""
Custom Decorators
"""
from functools import wraps
from flask import request, jsonify, render_template, current_app, redirect, url_for, flash
from flask_login import current_user


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
    Rate limiting decorator
    
    Args:
        limit: Maximum number of requests
        period: Time period in seconds
        key_func: Function to generate rate limit key
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            from app.extensions import redis_client
            from flask import request
            
            if redis_client is None:
                return f(*args, **kwargs)
            
            # Generate key
            if key_func:
                key = key_func()
            else:
                if current_user.is_authenticated:
                    key = f'rate_limit:user:{current_user.id}'
                else:
                    key = f'rate_limit:ip:{request.remote_addr}'
            
            key = f'{current_app.config.get("CACHE_KEY_PREFIX", "flask_pro")}:{key}:{request.endpoint}'
            
            try:
                # Get current count
                current = redis_client.get(key)
                
                if current is None:
                    current = 0
                else:
                    current = int(current)
                
                if current >= limit:
                    response = jsonify({
                        'error': 'Rate limit exceeded',
                        'retry_after': period
                    })
                    response.status_code = 429
                    response.headers['Retry-After'] = str(period)
                    return response
                
                # Increment counter
                pipe = redis_client.pipeline()
                pipe.incr(key)
                pipe.expire(key, period)
                pipe.execute()
                
            except Exception as e:
                current_app.logger.error(f'Rate limit error: {e}')
            
            return f(*args, **kwargs)
        return decorated
    return decorator


def api_required(f):
    """Decorator to require API key"""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        # Validate API key (you can implement your own logic)
        # For now, we'll skip validation
        
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
