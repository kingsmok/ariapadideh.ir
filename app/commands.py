"""
Flask CLI Commands
"""
import click
from flask.cli import with_appcontext
from app.extensions import db


def init_db():
    """Initialize database and create tables"""
    db.create_all()
    click.echo('✓ Database tables created')


def create_admin():
    """Create admin user"""
    from app.models import User, Role
    
    admin_role = Role.get_admin_role()
    
    admin = User(
        email='admin@example.com',
        first_name='مدیر',
        last_name='سایت',
        role_id=admin_role.id,
        is_active=True,
        is_verified=True
    )
    admin.set_password('admin123')
    admin.save()
    
    click.echo(f'✓ Admin user created: admin@example.com / admin123')


def seed_data():
    """Seed initial data"""
    from app.models import Category, Product, Brand, Page, Menu, Setting
    from app.services.setting_service import SettingService
    
    click.echo('Seeding initial data...')
    
    # Create default settings
    SettingService.init_default_settings()
    click.echo('✓ Settings initialized')
    
    # Create sample categories
    categories = [
        {'title': 'الکترونیک', 'slug': 'electronics', 'is_menu': True, 'icon': 'fa fa-mobile'},
        {'title': 'پوشاک', 'slug': 'clothing', 'is_menu': True, 'icon': 'fa fa-tshirt'},
        {'title': 'خانه و آشپزخانه', 'slug': 'home-kitchen', 'is_menu': True, 'icon': 'fa fa-couch'},
        {'title': 'ورزش و سفر', 'slug': 'sports-travel', 'is_menu': True, 'icon': 'fa fa-futbol'},
    ]
    
    for cat_data in categories:
        existing = Category.query.filter_by(slug=cat_data['slug']).first()
        if not existing:
            category = Category(**cat_data)
            category.save()
    
    click.echo('✓ Categories created')
    
    # Create sample brands
    brands = ['سامسونگ', 'اپل', 'سونی', 'دل', 'ایسوس']
    for brand_name in brands:
        existing = Brand.query.filter_by(slug=brand_name.lower()).first()
        if not existing:
            brand = Brand(
                name=brand_name,
                slug=brand_name.lower(),
                is_active=True
            )
            brand.save()
    
    click.echo('✓ Brands created')
    
    # Create sample pages
    pages = [
        {
            'title': 'درباره ما',
            'slug': 'about',
            'page_type': 'about',
            'content': '<p>به فروشگاه ما خوش آمدید...</p>',
            'is_active': True
        },
        {
            'title': 'تماس با ما',
            'slug': 'contact',
            'page_type': 'contact',
            'content': '<p>با ما در تماس باشید...</p>',
            'is_active': True
        },
        {
            'title': 'قوانین و مقررات',
            'slug': 'terms',
            'page_type': 'terms',
            'content': '<p>قوانین استفاده از سایت...</p>',
            'is_active': True
        },
        {
            'title': 'حریم خصوصی',
            'slug': 'privacy',
            'page_type': 'privacy',
            'content': '<p>حریم خصوصی کاربران...</p>',
            'is_active': True
        },
    ]
    
    for page_data in pages:
        existing = Page.query.filter_by(slug=page_data['slug']).first()
        if not existing:
            page = Page(**page_data)
            page.save()
    
    click.echo('✓ Pages created')
    
    # Create sample menus
    menus = [
        {'title': 'صفحه اصلی', 'url': '/', 'position': 'header', 'sort_order': 1},
        {'title': 'درباره ما', 'url': '/about', 'position': 'header', 'sort_order': 2},
        {'title': 'تماس با ما', 'url': '/contact', 'position': 'header', 'sort_order': 3},
    ]
    
    for menu_data in menus:
        existing = Menu.query.filter_by(url=menu_data['url'], position=menu_data['position']).first()
        if not existing:
            menu = Menu(**menu_data)
            menu.save()
    
    click.echo('✓ Menus created')
    
    click.echo('\n✓ All data seeded successfully!')


# Register commands
def register_commands(app):
    """Register CLI commands"""
    
    @app.cli.command('init-db')
    def init_db_command():
        """Initialize the database"""
        init_db()
    
    @app.cli.command('create-admin')
    def create_admin_command():
        """Create admin user"""
        create_admin()
    
    @app.cli.command('seed-data')
    def seed_data_command():
        """Seed initial data"""
        seed_data()
    
    @app.cli.command('reset-db')
    def reset_db_command():
        """Reset the database"""
        if click.confirm('آیا مطمئن هستید؟ تمام داده‌ها حذف خواهند شد.'):
            db.drop_all()
            db.create_all()
            click.echo('✓ Database reset')
            seed_data()
            create_admin()
