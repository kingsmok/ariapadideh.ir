"""
Admin Decorators
"""
from functools import wraps
from flask import redirect, url_for, flash, abort
from flask_login import current_user


def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('admin.login', next=request.url))
        
        if not current_user.is_admin():
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def permission_required(permission):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('admin.login', next=request.url))
            
            if not current_user.can(permission):
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def active_required(f):
    """Decorator to require active user"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('admin.login', next=request.url))
        
        if not current_user.is_active:
            flash('حساب کاربری شما غیرفعال است.', 'warning')
            return redirect(url_for('admin.login'))
        
        return f(*args, **kwargs)
    return decorated_function


from flask import request
