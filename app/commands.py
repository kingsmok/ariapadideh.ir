"""
Flask CLI Commands - Aria Padideh Software & Web Agency
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
    
    admin = User.query.filter_by(email='admin@example.com').first()
    if not admin:
        admin = User(
            email='admin@example.com',
            first_name='مدیر',
            last_name='ارشد رهسا دیو',
            role_id=admin_role.id,
            is_active=True,
            is_verified=True
        )
    else:
        admin.role_id = admin_role.id
        admin.is_active = True
        admin.is_verified = True

    admin.set_password('admin123')
    admin.save()
    
    click.echo(f'✓ Admin user created: admin@example.com / admin123')


def seed_data():
    """Seed initial data for Aria Padideh Software & Web Agency"""
    from app.models import Category, Product, Brand, Page, Menu, Setting, FAQ
    from app.services.setting_service import SettingService
    
    click.echo('Seeding initial data for Aria Padideh...')
    
    # Create default settings
    SettingService.init_default_settings()
    click.echo('✓ Settings initialized')
    
    # Create software & web categories
    categories = [
        {'title': 'طراحی وب‌سایت', 'slug': 'web-design', 'is_menu': True, 'icon': 'fa fa-laptop-code', 'description': 'طراحی وب‌سایت‌های فروشگاهی، شرکتی و پورتال‌های اختصاصی'},
        {'title': 'ربات‌های هوشمند', 'slug': 'smart-bots', 'is_menu': True, 'icon': 'fa fa-robot', 'description': 'ساخت ربات تلگرام، ایتا، بله و سیستم‌های مبتنی بر هوش مصنوعی'},
        {'title': 'نرم‌افزار و اتوماسیون', 'slug': 'software-automation', 'is_menu': True, 'icon': 'fa fa-code', 'description': 'نرم‌افزارهای حسابداری، اتوماسیون اداری و مدیریت مشتریان CRM'},
        {'title': 'برنامه‌نویسی و اسکریپت', 'slug': 'programming-scripts', 'is_menu': True, 'icon': 'fa fa-terminal', 'description': 'اسکریپت‌های پایتون، اتصال به API و افزونه‌های سفارشی'},
    ]
    
    cat_objects = {}
    for cat_data in categories:
        cat = Category.query.filter_by(slug=cat_data['slug']).first()
        if not cat:
            cat = Category(**cat_data)
            cat.save()
        cat_objects[cat_data['slug']] = cat
    
    click.echo('✓ Software & Web Categories created')
    
    # Create tech brands
    brands = ['پایتون (Python)', 'فریم‌ورک فلاسک (Flask)', 'هوش مصنوعی (AI)', 'توسعه وب (Web Stack)']
    brand_objects = []
    for brand_name in brands:
        slug = brand_name.split()[0].lower()
        brand = Brand.query.filter_by(name=brand_name).first()
        if not brand:
            brand = Brand(name=brand_name, slug=slug, is_active=True)
            brand.save()
        brand_objects.append(brand)
    
    click.echo('✓ Tech Stack Brands created')
    
    # Create sample products/packages
    products = [
        {
            'sku': 'WEB-SHOP-01',
            'title': 'پکیج جامع طراحی سایت فروشگاهی (فلاسک پرو)',
            'slug': 'flask-pro-ecommerce-package',
            'price': 15800000,
            'old_price': 18500000,
            'stock_quantity': 100,
            'short_description': 'سیستم کامل فروشگاهی تحت وب با فریم‌ورک پایتون فلاسک، پنل مدیریت پیشرفته، اتصال به درگاه بانکی و سورس‌کد کامل.',
            'description': 'پکیج وب‌سایت فروشگاهی طراحی شده توسط رهسا دیو با بهینه‌سازی کامل سئو، پنل مدیریت اختصاصی، سیستم تخفیف‌دهی، گزارش‌گیری مالی و ۱ سال پشتیبانی رایگان.',
            'is_featured': True,
            'is_new': True,
            'show_in_home': True,
            'category_slug': 'web-design'
        },
        {
            'sku': 'BOT-TELE-01',
            'title': 'ربات هوشمند مدیریت گروه و کانال (تلگرام / ایتا)',
            'slug': 'telegram-eitaa-smart-bot',
            'price': 3500000,
            'old_price': 4200000,
            'stock_quantity': 100,
            'short_description': 'ربات چندمنظوره با قابلیت ضداسپم، ثبت سفارش خودکار، پاسخگویی هوشمند و اتصال به دیتابیس وب‌سایت.',
            'description': 'این ربات نرم‌افزاری قابلیت اتصال همزمان به تلگرام و ایتا را داشته و فرآیند پشتیبانی و ثبت سفارش شما را ۱۰۰٪ اتوماتیک می‌کند.',
            'is_featured': True,
            'is_new': True,
            'show_in_home': True,
            'category_slug': 'smart-bots'
        },
        {
            'sku': 'SOFT-CRM-01',
            'title': 'نرم‌افزار حسابداری و مدیریت مشتریان (CRM) ابری',
            'slug': 'cloud-crm-accounting-software',
            'price': 8200000,
            'old_price': 9800000,
            'stock_quantity': 100,
            'short_description': 'اتوماسیون مالی، پیگیری سرنخ‌های فروش، صدور پیش‌فاکتور خودکار و مدیریت فایل‌های مشتریان.',
            'description': 'نرم‌افزار جامع مدیریت ارتباط با مشتریان (CRM) با قابلیت دسترسی تحت وب و موبایل، داشبورد تحلیل نموداری فروش و ارسال پیامک خودکار.',
            'is_featured': True,
            'is_new': False,
            'show_in_home': True,
            'category_slug': 'software-automation'
        },
        {
            'sku': 'SCRP-GATE-01',
            'title': 'اسکریپت درگاه پرداخت چندمنظوره و فاکتورساز آنلاین',
            'slug': 'multi-gateway-invoice-script',
            'price': 2400000,
            'old_price': 3000000,
            'stock_quantity': 100,
            'short_description': 'اتصال به کلیه درگاه‌های مستقیم بانکی و واسط، صدور فاکتور رسمی PDF با شناسه یکتا.',
            'description': 'اسکریپت امنیتی جهت دریافت آنلاین مبالغ، تایید هویت خریدار و تسویه حساب سریع با قابلیت نصب روی کلیه هاست‌های داخلی.',
            'is_featured': True,
            'is_new': False,
            'show_in_home': True,
            'category_slug': 'programming-scripts'
        },
        {
            'sku': 'BOT-AI-02',
            'title': 'ربات تحلیل‌گر بازار و الگوتریدر هوش مصنوعی',
            'slug': 'ai-market-trader-bot',
            'price': 12000000,
            'old_price': 14500000,
            'stock_quantity': 100,
            'short_description': 'تحلیل خودکار نمودارهای قیمتی، سیگنال‌دهی بر اساس استراتژی‌های فنی و ارسال هشدار خودکار.',
            'description': 'سیستم الگوریتمی تحلیل بازار توسعه یافته با پایتون و الگوریتم‌های یادگیری ماشین جهت تحلیل لحظه‌ای شاخص‌ها.',
            'is_featured': True,
            'is_new': True,
            'show_in_home': True,
            'category_slug': 'smart-bots'
        },
        {
            'sku': 'WEB-CORP-02',
            'title': 'پکیج وب‌سایت شرکتی و پورتال سازمانی اختصاصی',
            'slug': 'corporate-portal-website-package',
            'price': 9500000,
            'old_price': 11000000,
            'stock_quantity': 100,
            'short_description': 'طراحی شیک و مدرن، چندزبانه، بخش معرفی خدمات، نمونه‌کارها، فرم رزومه و کاتالوگ آنلاین.',
            'description': 'راهکار وب‌سایت شرکتی رهسا دیو با سرعت بارگذاری زیر ۱ ثانیه، سازگاری کامل با شبکه ملی اطلاعات و امنیت تضمین‌شده.',
            'is_featured': True,
            'is_new': False,
            'show_in_home': True,
            'category_slug': 'web-design'
        }
    ]
    
    for prod_data in products:
        cat_slug = prod_data.pop('category_slug')
        existing_prod = Product.query.filter_by(slug=prod_data['slug']).first()
        if not existing_prod:
            prod = Product(**prod_data)
            if cat_slug in cat_objects:
                prod.categories.append(cat_objects[cat_slug])
            prod.brand = brand_objects[0]
            prod.save()
    
    click.echo('✓ Software Packages & Products created')
    
    # Create sample pages
    pages = [
        {
            'title': 'درباره رهسا دیو',
            'slug': 'about',
            'page_type': 'about',
            'content': '<h3>درباره مجموعه رهسا دیو</h3><p>مجموعه مهندسی رهسا دیو با هدف ارائه راهکارهای نوین در حوزه طراحی وب‌سایت‌های پیشرفته، توسعه نرم‌افزارهای سفارشی و ساخت ربات‌های هوشمند فعالیت خود را آغاز نموده است.</p>',
            'is_active': True
        },
        {
            'title': 'تماس با ما و مشاوره',
            'slug': 'contact',
            'page_type': 'contact',
            'content': '<p>جهت دریافت مشاوره رایگان و برآورد زمان و هزینه پروژه‌های خود با کارشناسان آریا پدیده در تماس باشید.</p>',
            'is_active': True
        },
        {
            'title': 'قوانین و ضمانت پروژه‌ها',
            'slug': 'terms',
            'page_type': 'terms',
            'content': '<p>کلیه پروژه‌های تحویلی آریا پدیده دارای ۱ سال پشتیبانی رایگان، سورس‌کد کامل و ضمانت عدم وجود باگ می‌باشند.</p>',
            'is_active': True
        },
        {
            'title': 'حریم خصوصی و امنیت اطلاعات',
            'slug': 'privacy',
            'page_type': 'privacy',
            'content': '<p>حفاظت از اطلاعات، دیتابیس و سورس‌کدهای سفارشی مشتریان اولویت اصلی شرکت آریا پدیده است.</p>',
            'is_active': True
        },
    ]
    
    for page_data in pages:
        existing = Page.query.filter_by(slug=page_data['slug']).first()
        if not existing:
            page = Page(**page_data)
            page.save()
    
    click.echo('✓ Company Pages created')
    
    # Create FAQs
    faqs = [
        {
            'question': 'آیا سورس‌کد کامل نرم‌افزار یا وب‌سایت به خریدار تحویل داده می‌شود؟',
            'answer': 'بله! در آریا پدیده تمامی پروژه‌ها و پکیج‌ها با سورس‌کد کامل، بدون هیچ‌گونه قفل یا محدودیت در اختیار خریدار قرار می‌گیرند.',
            'is_featured': True,
            'is_active': True,
            'sort_order': 1
        },
        {
            'question': 'شرایط پشتیبانی پروژه‌ها و نرم‌افزارها به چه صورت است؟',
            'answer': 'کلیه خدمات و پکیج‌ها دارای ۱۲ ماه پشتیبانی رایگان شامل رفع هرگونه باگ احتمالی، بروزرسانی‌های امنیتی و راهنمایی فنی می‌باشند.',
            'is_featured': True,
            'is_active': True,
            'sort_order': 2
        },
        {
            'question': 'آیا امکان سفارش ربات اختصاصی بر روی پیام‌رسان‌های ایرانی ایتا و بله وجود دارد؟',
            'answer': 'بله! تیم فنی آریا پدیده انواع ربات‌های هوشمند را علاوه بر تلگرام، بر روی پیام‌رسان‌های بومی نظیر ایتا و بله پیاده‌سازی می‌نماید.',
            'is_featured': True,
            'is_active': True,
            'sort_order': 3
        }
    ]
    
    for faq_data in faqs:
        existing = FAQ.query.filter_by(question=faq_data['question']).first()
        if not existing:
            faq = FAQ(**faq_data)
            faq.save()
            
    click.echo('✓ FAQs created')
    
    # Create sample menus
    menus = [
        {'title': 'صفحه اصلی', 'slug': 'home-menu', 'url': '/', 'position': 'header', 'sort_order': 1},
        {'title': 'درباره ما', 'slug': 'about-menu', 'url': '/about', 'position': 'header', 'sort_order': 2},
        {'title': 'تماس با ما', 'slug': 'contact-menu', 'url': '/contact', 'position': 'header', 'sort_order': 3},
    ]
    
    for menu_data in menus:
        existing = Menu.query.filter_by(url=menu_data['url'], position=menu_data['position']).first()
        if not existing:
            menu = Menu(**menu_data)
            menu.save()
    
    click.echo('✓ Navigation Menus created')
    click.echo('\n✓ All data seeded successfully for Aria Padideh!')


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
