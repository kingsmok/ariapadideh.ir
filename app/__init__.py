"""
Flask Application Factory
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request
from werkzeug.middleware.proxy_fix import ProxyFix
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.config import config
from app.extensions import (
    db, migrate, login_manager, csrf, cache, compress, 
    moment, babel, assets, init_redis
)


def create_app(config_name: str = None) -> Flask:
    """Create and configure Flask application"""
    
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize Redis
    if config_name != 'testing':
        init_redis(app)
    
    # Proxy fix for reverse proxy
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    
    # Initialize extensions
    init_extensions(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register context processors
    register_context_processors(app)
    
    # Register commands
    register_commands(app)
    
    # Setup logging
    setup_logging(app)
    
    # Create upload directories
    create_directories(app)
    
    return app


def init_extensions(app: Flask) -> None:
    """Initialize Flask extensions"""
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    cache.init_app(app)
    compress.init_app(app)
    moment.init_app(app)
    babel.init_app(app)
    assets.init_app(app)
    
    # Setup Babel locales (for older versions)
    if hasattr(babel, 'localeselector'):
        @babel.localeselector
        def get_locale():
            lang = request.args.get('lang')
            if lang in ['fa', 'en']:
                return lang
            lang = request.cookies.get('lang')
            if lang in ['fa', 'en']:
                return lang
            return request.accept_languages.best_match(['fa', 'en'])
    
    # Set Jinja2 environment
    app.jinja_env.add_extension('jinja2.ext.i18n')
    app.jinja_env.auto_reload = app.debug


def register_blueprints(app: Flask) -> None:
    """Register Flask blueprints"""
    
    from app.blueprints.public import public_bp
    from app.blueprints.user import user_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.api import api_bp
    from app.blueprints.blog import blog_bp
    
    # Public routes
    app.register_blueprint(public_bp, url_prefix='/')
    
    # User panel
    app.register_blueprint(user_bp, url_prefix='/user')
    
    # Admin panel
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # REST API
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    
    # Blog/CMS
    app.register_blueprint(blog_bp, url_prefix='/blog')


def register_error_handlers(app: Flask) -> None:
    """Register error handlers"""
    
    from app.errors.handlers import (
        handle_404, handle_500, handle_403, handle_405
    )
    
    app.register_error_handler(404, handle_404)
    app.register_error_handler(500, handle_500)
    app.register_error_handler(403, handle_403)
    app.register_error_handler(405, handle_405)


def register_context_processors(app: Flask) -> None:
    """Register Jinja2 context processors and filters"""
    
    from app.services.setting_service import SettingService
    from app.utils.helpers import (
        format_price, time_ago, truncate_text, get_cdn_url
    )
    
    # Register Jinja Filters
    app.jinja_env.filters['format_price'] = format_price
    app.jinja_env.filters['toman_format'] = format_price
    app.jinja_env.filters['time_ago'] = time_ago
    app.jinja_env.filters['truncate_text'] = truncate_text

    @app.context_processor
    def inject_globals():
        """Inject global variables into templates"""
        settings = SettingService.get_public_settings()
        
        return {
            'site_settings': settings,
            'current_year': __import__('datetime').datetime.now().year,
        }
    
    @app.context_processor
    def utility_processor():
        """Add utility functions to templates"""
        return {
            'format_price': format_price,
            'time_ago': time_ago,
            'truncate_text': truncate_text,
            'get_cdn_url': get_cdn_url,
        }


def register_commands(app: Flask) -> None:
    """Register Flask CLI commands"""
    
    from app.commands import register_commands as attach_commands
    attach_commands(app)


def setup_logging(app: Flask) -> None:
    """Setup application logging"""
    
    if not app.debug and not app.testing:
        
        # Ensure log directory exists
        log_dir = app.config.get('LOG_FILE', 'logs/app.log').rsplit('/', 1)[0]
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # File handler
        file_handler = RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        console_handler.setLevel(logging.DEBUG if app.debug else logging.INFO)
        app.logger.addHandler(console_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Flask Pro startup')


def create_directories(app: Flask) -> None:
    """Create necessary directories"""
    
    directories = [
        app.config['UPLOAD_FOLDER'],
        app.config['UPLOAD_FOLDER'] / 'products',
        app.config['UPLOAD_FOLDER'] / 'categories',
        app.config['UPLOAD_FOLDER'] / 'banners',
        app.config['UPLOAD_FOLDER'] / 'posts',
        app.config['UPLOAD_FOLDER'] / 'resumes',
        app.config['BASE_DIR'] / 'logs',
        app.config['BASE_DIR'] / 'instance',
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
