"""
Flask CLI Commands - Aria Padideh Software & Web Agency
"""
import click
from flask.cli import with_appcontext
from app.extensions import db


def init_db():
    """Initialize database and create tables"""
    db.create_all()
    _ensure_schema_upgrades()
    click.echo('✓ Database tables created')


def _ensure_schema_upgrades():
    """
    ارتقاهای کوچک و idempotent برای دیتابیس‌های موجود.

    create_all فقط جدول‌های تازه می‌سازد؛ ستون‌های جدیدِ مدل‌ها را به
    جدول‌های قدیمی اضافه نمی‌کند. اینجا ستون‌های اضافه‌شده در نسخه‌های
    جدید را با ALTER امن اضافه می‌کنیم (اگر نباشند).
    """
    from sqlalchemy import inspect, text

    try:
        inspector = inspect(db.engine)
        # نسخهٔ چندزبانه — ستون‌های انگلیسی مقالات
        if 'posts' in inspector.get_table_names():
            cols = {c['name'] for c in inspector.get_columns('posts')}
            for col in ('title_en', 'excerpt_en', 'content_en'):
                if col not in cols:
                    db.session.execute(text(f'ALTER TABLE posts ADD COLUMN {col} TEXT'))
                    click.echo(f'  + posts.{col} added (multilingual upgrade)')

        # نسخهٔ درگاه‌های پرداخت — ردیف‌های تنظیمات payment فقط در صورت نبود
        from app.services.setting_service import SettingService
        SettingService.ensure_payment_settings()

        db.session.commit()
    except Exception as exc:  # noqa: BLE001 — ارتقا نباید بوت را متوقف کند
        click.echo(f'  ! schema upgrade skipped: {exc}')
        try:
            db.session.rollback()
        except Exception:
            pass


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


def seed_demo(preset: str = 'corporate'):
    """دموی آمادهٔ قابلیت‌های جدید — الگوی بستهٔ نصبی قالب‌های راست‌چین"""
    from app.models import (
        TeamMember, PricingPlan, Story, Setting, Product, ProductVideo
    )
    from app.services.setting_service import SettingService

    click.echo(f'Seeding demo preset: {preset} ...')

    # 1) تنظیمات جدید (نقشه/ظاهر/قابلیت‌ها)
    SettingService.init_default_settings()
    click.echo('✓ Settings (features + appearance + OSM map) initialized')

    # 2) تیم ما + نوار مهارت
    if TeamMember.query.filter_by(is_deleted=False).count() == 0:
        members = [
            {'full_name': 'امیر رهنما', 'role_title': 'مدیرعامل و معمار ارشد نرم‌افزار',
             'bio': '۱۵ سال تجربهٔ معماری سیستم‌های سازمانی و مقیاس‌پذیر.',
             'skills': [{'name': 'معماری نرم‌افزار', 'level': 96}, {'name': 'Python', 'level': 92}, {'name': 'DevOps', 'level': 80}]},
            {'full_name': 'سارا محمدی', 'role_title': 'مدیر محصول و UI/UX',
             'bio': 'طراحی تجربهٔ کاربری برای بیش از ۵۰ محصول دیجیتال.',
             'skills': [{'name': 'UI/UX', 'level': 94}, {'name': 'Figma', 'level': 90}, {'name': 'Research', 'level': 82}]},
            {'full_name': 'رضا کریمی', 'role_title': 'مدیر فنی تیم توسعه',
             'bio': 'متخصص فلاسک و زیرساخت‌های ابری.',
             'skills': [{'name': 'Flask', 'level': 95}, {'name': 'PostgreSQL', 'level': 88}, {'name': 'Docker', 'level': 85}]},
        ]
        for i, m in enumerate(members):
            TeamMember(**m, sort_order=i).save()
        click.echo(f'✓ {len(members)} team members created')
    else:
        click.echo('• team members exist — skipped')

    # 3) جداول تعرفه
    if PricingPlan.query.filter_by(is_deleted=False).count() == 0:
        plans = [
            {'title': 'وب‌سایت شرکتی استاندارد', 'subtitle': 'برای کسب‌وکارهای در حال رشد',
             'price_toman': 24_900_000, 'period': 'پروژه',
             'features': ['طراحی ریسپانسیو اختصاصی', 'پنل مدیریت کامل', 'سئوی پایه', 'یک سال پشتیبانی'],
             'features_off': ['فروشگاه آنلاین', 'ربات هوشمند'], 'sort_order': 0},
            {'title': 'وب‌سایت + فروشگاه آنلاین', 'subtitle': 'پرفروش‌ترین پکیج',
             'price_toman': 49_900_000, 'old_price_toman': 59_900_000, 'period': 'پروژه',
             'badge_text': 'محبوب‌ترین', 'is_featured': True,
             'features': ['همهٔ امکانات استاندارد', 'فروشگاه کامل و درگاه پرداخت', 'سئوی حرفه‌ای + اسکیما', 'ربات تلگرام فروشگاه', 'دو سال پشتیبانی'],
             'sort_order': 1},
            {'title': 'پلتفرم اختصاصی سازمانی', 'subtitle': 'سیستم‌های سفارشی و مقیاس‌پذیر',
             'price_toman': None, 'period': 'استعلام',
             'features': ['تحلیل و معماری اختصاصی', 'توسعهٔ چابک (Agile)', 'SLA و پشتیبانی ۲۴/۷', 'امنیت سازمانی'],
             'button_text': 'درخواست مشاوره', 'sort_order': 2},
        ]
        for p in plans:
            PricingPlan(**p).save()
        click.echo(f'✓ {len(plans)} pricing plans created')
    else:
        click.echo('• pricing plans exist — skipped')

    # 4) استوری‌ها
    if Story.query.filter_by(is_deleted=False).count() == 0:
        stories = [
            {'title': 'معرفی خدمات', 'group_name': 'معرفی', 'media_type': 'image', 'duration': 5,
             'link': '/categories/'},
            {'title': 'نمونه‌کارهای اخیر', 'group_name': 'نمونه‌کار', 'media_type': 'image', 'duration': 6,
             'link': '/#portfolio'},
            {'title': 'مشاوره رایگان', 'group_name': 'مشاوره', 'media_type': 'image', 'duration': 5,
             'link': '/contact'},
        ]
        for i, s in enumerate(stories):
            Story(**s, sort_order=i).save()
        click.echo(f'✓ {len(stories)} stories created')
    else:
        click.echo('• stories exist — skipped')

    # 5) سواچ + ویدئو روی اولین محصول (فقط پرست شاپ)
    if preset == 'shop':
        product = Product.query.filter_by(is_deleted=False).order_by(Product.id).first()
        if product and not product.variations:
            product.variations = [
                {'name': 'نسخه پایه', 'type': 'label', 'value': '', 'price': 0, 'stock': 10},
                {'name': 'نسخه حرفه‌ای', 'type': 'label', 'value': '', 'price': 9_000_000, 'stock': 5},
                {'name': 'پشتیبانی طلایی', 'type': 'color', 'value': '#fbb03b', 'price': 4_500_000, 'stock': 3},
            ]
            product.save()
            click.echo(f'✓ variation swatches added to "{product.title[:40]}"')
        if product and ProductVideo.query.filter_by(product_id=product.id, is_deleted=False).count() == 0:
            ProductVideo(product_id=product.id, title='دموی محصول', provider='aparat',
                         url='https://www.aparat.com/v/example').save()
            click.echo('✓ demo video added')

    # 6) مقالات نمونهٔ وبلاگ (هر دو پرست — وبلاگ خالی بد است!)
    from app.models import Post, Category as BlogCat, Tag as BlogTag, User
    from app.extensions import db as _db
    from datetime import datetime, timedelta
    if Post.query.filter_by(is_deleted=False).count() == 0:
        cat = BlogCat.query.filter_by(is_deleted=False, is_active=True).order_by(BlogCat.id).first()
        cat_id = cat.id if cat else None
        admin_user = User.query.filter_by(is_active=True).order_by(User.id).first()
        demo_posts = [
            {'title': 'چرا فلاسک برای استارتاپ‌های ایرانی انتخاب هوشمندانه‌ای است؟',
             'slug': 'why-flask-for-iranian-startups',
             'excerpt': 'مقایسهٔ هزینه، سرعت توسعه و مقیاس‌پذیری فلاسک با فریمورک‌های دیگر برای تیم‌های کوچک.',
             'tags': ['فلاسک', 'پایتون', 'استارتاپ'],
             'days_ago': 4, 'featured': True,
             # نسخهٔ انگلیسی — دموی چندزبانه (/en/blog/…)
             'title_en': 'Why Flask Is a Smart Choice for Iranian Startups',
             'excerpt_en': 'Cost, development speed and scalability of Flask compared to other frameworks for small teams.',
             'content_en': (
                 '<p>For early-stage teams, shipping fast and keeping maintenance costs low matter more than '
                 'following hype. Flask lets a two-person team build and deploy a production-grade product in weeks.</p>'
                 '<h2>Why it matters</h2>'
                 '<p>Speed of delivery and low maintenance have become the key criteria when choosing a stack. '
                 'A team that ships v1 faster and cheaper has a better chance of finding its market.</p>'
                 '<h2>Key points</h2>'
                 '<ul><li>Quick start with minimal dependencies</li>'
                 '<li>Low maintenance cost, gradual scaling</li>'
                 '<li>Active community and Persian documentation</li>'
                 '<li>Smooth migration path to a service-oriented architecture later</li></ul>'
                 '<h2>Bottom line</h2>'
                 '<p>Choose technology based on real business needs. Need help deciding? <a href="/en/contact">Talk to us</a>.</p>'
             )},
            {'title': 'راهنمای انتخاب هاست و سرور برای فروشگاه‌های آنلاین',
             'slug': 'hosting-guide-online-shops',
             'excerpt': 'از هاست اشتراکی تا سرور اختصاصی — چطور بستهٔ مناسب کسب‌وکارتان را انتخاب کنید.',
             'tags': ['هاست', 'سرور', 'فروشگاه آنلاین'],
             'days_ago': 11, 'featured': False},
            {'title': 'اتوماسیون با ربات تلگرام: ۵ کاربرد واقعی برای کسب‌وکارها',
             'slug': 'telegram-bot-automation-usecases',
             'excerpt': 'پشتیبانی خودکار، فروش، اطلاع‌رسانی، نظرسنجی و اتوماسیون داخلی با یک ربات.',
             'tags': ['ربات تلگرام', 'اتوماسیون', 'ایتیا'],
             'days_ago': 21, 'featured': False},
        ]
        for i, p in enumerate(demo_posts):
            post = Post(
                title=p['title'], slug=p['slug'], excerpt=p['excerpt'],
                content=(
                    f'<p>{p["excerpt"]}</p>'
                    '<h2>چرا این موضوع مهم است؟</h2>'
                    '<p>در سال‌های اخیر سرعت توسعه و هزینهٔ نگهداری به مهم‌ترین معیارهای انتخاب فناوری تبدیل شده‌اند. '
                    'تیمی که بتواند نسخهٔ اول محصول را سریع‌تر و با هزینهٔ کمتر عرضه کند، شانس بیشتری برای پیدا کردن بازار دارد.</p>'
                    '<h2>نکات کلیدی</h2>'
                    '<ul><li>شروع سریع با حداقل وابستگی</li>'
                    '<li>هزینهٔ پایین نگهداری و مقیاس‌پذیری تدریجی</li>'
                    '<li>جامعهٔ فعال و مستندات فارسی</li>'
                    '<li>امکان مهاجرت تدریجی به معماری سرویس‌محور</li></ul>'
                    '<h2>جمع‌بندی</h2>'
                    '<p>انتخاب فناوری باید بر اساس نیاز واقعی کسب‌وکار باشد نه هیاهوی فناوری‌های روز. '
                    'برای مشاورهٔ رایگان با تیم ما در تماس باشید.</p>'
                ),
                status='published', category_id=cat_id,
                author_id=admin_user.id if admin_user else None,
                published_at=datetime.utcnow() - timedelta(days=p['days_ago']),
                is_active=True, show_in_home=True, is_featured=p['featured'],
                views=(340 - i * 77),
                title_en=p.get('title_en'), excerpt_en=p.get('excerpt_en'),
                content_en=p.get('content_en'),
            )
            _db.session.add(post)
            for name in p['tags']:
                tag = BlogTag.query.filter_by(name=name).first()
                if not tag:
                    tag_counter = (BlogTag.query.count() or 0) + 1
                    tag = BlogTag(name=name, slug=f'demo-tag-{tag_counter}')
                    _db.session.add(tag)
                post.tags.append(tag)
        _db.session.commit()
        click.echo(f'✓ {len(demo_posts)} demo blog posts created')

    # 7) منوی نمونهٔ هدر (مگامنو) + فوتر — نمایش قابلیت منوساز
    from app.models import Menu
    if Menu.query.filter_by(position='header', is_mega_menu=True, is_deleted=False).count() == 0:
        mega = Menu(title='خدمات ما', slug='demo-mega-services', url='/categories',
                    position='header', icon='🧩', is_mega_menu=True,
                    badge_text='جدید', badge_color='#fbb03b', sort_order=1)
        _db.session.add(mega)
        _db.session.flush()
        for t, u, ic in [('طراحی وب‌سایت', '/category/web-design', '💻'),
                         ('ربات‌های هوشمند', '/category/smart-bots', '🤖'),
                         ('نرم‌افزار و اتوماسیون', '/category/software-automation', '⚙️'),
                         ('برنامه‌نویسی و اسکریپت', '/category/programming-scripts', '📝')]:
            _db.session.add(Menu(title=t, url=u, slug=f'demo-sub-{u.split("/")[-1]}',
                                 position='header', icon=ic, parent_id=mega.id, sort_order=0))
        _db.session.commit()
        click.echo('✓ demo header mega-menu created')
    if Menu.query.filter_by(position='footer', is_deleted=False).count() == 0:
        for j, (t, u) in enumerate([('درباره ما', '/about'), ('تماس با ما', '/contact'), ('سوالات متداول', '/faq')]):
            _db.session.add(Menu(title=t, url=u, slug=f'demo-footer-{j}', position='footer', sort_order=j))
        _db.session.commit()
        click.echo('✓ demo footer menu created')

    click.echo(f'\n✓ Demo "{preset}" ready → /admin/team, /admin/pricing, /admin/stories, /admin/posts, صفحهٔ اصلی')


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
    
    @app.cli.command('seed-demo')
    @click.argument('preset', default='corporate', type=click.Choice(['corporate', 'shop']))
    def seed_demo_command(preset):
        """دموی آماده — درون‌ریزی یک‌کلیک (الگوی قالب‌های راست‌چین)

        team/pricing/stories/سواچ/ویدئو/نقشه را نمونه‌سازی می‌کند.
        idempotent است و دادهٔ تکراری نمی‌سازد.
        """
        seed_demo(preset)
    
    @app.cli.command('reset-db')
    def reset_db_command():
        """Reset the database"""
        if click.confirm('آیا مطمئن هستید؟ تمام داده‌ها حذف خواهند شد.'):
            db.drop_all()
            db.create_all()
            click.echo('✓ Database reset')
            seed_data()
            create_admin()
