# Flask Pro - Professional Flask CMS

یک وب‌سایت حرفه‌ای و کامل با Flask برای راه‌اندازی فروشگاه، سایت شرکتی یا پرتال محتوا.

## ✨ ویژگی‌ها

- **پنل مدیریت کامل**: مدیریت محصولات، سفارشات، کاربران، صفحات، منوها، مقالات و...
- **فروشگاه آنلاین**: سبد خرید، مقایسه، علاقه‌مندی، پیگیری سفارش، سواچ متغیر (رنگ/تصویر) روی صفحه و کارت محصول، گالری ویدئو (آپارات/یوتیوب)، فیلتر ایجکسی محصولات، فاکتور و لیبل چاپی
- **سیستم محتوا**: وبلاگ با پنل مدیریت کامل + پیش‌نویس AI، صفحات CMS، سوالات متداول
- **صفحه‌سازی بصری**: صفحه‌ساز خانه با درگ‌انددراپ (ترتیب/نمایش/عنوان ۸ بخش) + منوساز هدر/فوتر داینامیک با مگامنو دوستونه
- **قابلیت‌های شرکتی حرفه‌ای**: تیم ما با نوار مهارت، جداول تعرفه، استوری‌ساز اینستاگرامی، نقشهٔ تعاملی Leaflet با پین قابل کلیک در تماس، خبرنامه با ارسال گروهی و خروجی CSV
- **پشتیبانی و کاربر**: سیستم تیکت پشتیبانی ردوبدل با پیوست فایل، ورود/عضویت با موبایل (OTP پیامکی)، پنل کاربری با اطلاعیه‌ها
- **شخصی‌سازی ظاهر**: تم تیره/روشن با سوییچ، انتخاب رنگ تأکید و فونت از پنل، پری‌لودر چندطرح
- **هوش مصنوعی**: پیش‌نویس خودکار توضیحات محصول و مقالات (سازگار با OpenAI/OpenRouter/Groq)
- **SEO کامل**: Meta tags، Open Graph، JSON-LD، Sitemap
- **امنیت**: CSRF، XSS Protection، Rate Limiting، Password Hashing، ضد بمباران پیامکی
- **performance**: Caching، Lazy Loading، Database Indexing
- **ریسپانسیو**: طراحی Mobile-First با RTL Support
- **یکپارچه‌سازی**: تلگرام، فید قیمت (ترب، ایمالز)، پنل‌های پیامکی ایرانی
- **دموی آماده**: `flask seed-demo corporate|shop` — درون‌ریزی یک‌کلیک (الگوی قالب‌های راست‌چین)

> 📊 تحلیل کامل بازار قالب‌های شرکتی راست‌چین (۱۸ قالب) و تطبیق قابلیت‌ها: `THEME_RESEARCH.md` و صفحهٔ «تحلیل بازار قالب‌ها» در پنل مدیریت.

## 🚀 نصب و راه‌اندازی

### پیش‌نیازها

- Python 3.11+
- Redis (اختیاری)
- PostgreSQL (اختیاری، SQLite برای توسعه)

### مراحل

```bash
# 1. کلون پروژه
git clone https://github.com/your-repo/flask-pro.git
cd flask-pro

# 2. ساخت محیط مجازی
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate   # Windows

# 3. نصب وابستگی‌ها
pip install -r requirements.txt

# 4. تنظیم متغیرهای محیطی
cp .env.example .env
# ویرایش .env و تنظیم SECRET_KEY و سایر مقادیر

# 5. راه‌اندازی دیتابیس
flask init-db
flask create-admin
flask seed-data

# 6. اجرای سرور
python run.py
```

### دستورات CLI

```bash
flask init-db        # ایجاد جداول دیتابیس
flask create-admin    # ساخت کاربر ادمین
flask seed-data      # درج داده‌های اولیه
flask reset-db       # بازنشانی دیتابیس
```

## 📁 ساختار پروژه

```
flask-pro/
├── app/
│   ├── __init__.py          # App Factory
│   ├── config.py            # Configuration
│   ├── extensions.py        # Flask Extensions
│   ├── models/              # Database Models
│   ├── blueprints/          # Route Blueprints
│   │   ├── public/          # صفحات عمومی
│   │   ├── admin/           # پنل مدیریت
│   │   ├── user/            # پنل کاربری
│   │   ├── api/             # REST API
│   │   └── blog/            # وبلاگ
│   ├── services/             # Business Logic
│   ├── templates/           # Jinja2 Templates
│   │   ├── components/      # Header, Footer, etc.
│   │   ├── macros/          # Reusable Components
│   │   └── errors/          # Error Pages
│   └── static/              # CSS, JS, Images
├── migrations/              # Alembic Migrations
├── tests/                   # Unit Tests
├── .env                     # Environment Variables
├── requirements.txt         # Python Packages
└── run.py                   # Application Entry Point
```

## 🔧 تنظیمات

### متغیرهای محیطی

| متغیر | توضیحات | مقدار پیش‌فرض |
|--------|---------|---------------|
| `SECRET_KEY` | کلید امنیتی | - |
| `DATABASE_URL` | آدرس دیتابیس | SQLite |
| `REDIS_HOST` | آدرس Redis | localhost |
| `SITE_NAME` | نام سایت | فلاسک پرو |
| `SITE_URL` | آدرس سایت | http://localhost:5000 |

## 📱 صفحات اصلی

- `/` - صفحه اصلی
- `/category/<slug>` - صفحه دسته‌بندی
- `/product/<slug>` - صفحه محصول
- `/blog` - صفحه وبلاگ
- `/blog/<slug>` - صفحه مقاله
- `/search` - صفحه جستجو
- `/cart` - سبد خرید
- `/about` - درباره ما
- `/contact` - تماس با ما
- `/faq` - سوالات متداول

## 🔐 پنل مدیریت

مسیر: `/admin`

| صفحه | توضیحات |
|------|---------|
| `/admin/dashboard` | داشبورد |
| `/admin/products` | مدیریت محصولات |
| `/admin/categories` | مدیریت دسته‌بندی‌ها |
| `/admin/orders` | مدیریت سفارشات |
| `/admin/users` | مدیریت کاربران |
| `/admin/pages` | مدیریت صفحات |
| `/admin/menus` | مدیریت منوها |
| `/admin/sliders` | مدیریت اسلایدرها |
| `/admin/banners` | مدیریت بنرها |
| `/admin/settings` | تنظیمات سایت |
| `/admin/media` | کتابخانه رسانه |
| `/admin/contacts` | پیام‌های تماس |
| `/admin/resumes` | رزومه‌های دریافتی |

## 📡 REST API

مسیر: `/api/v1`

### محصولات
```
GET /api/v1/products
GET /api/v1/products/<id>
GET /api/v1/products?category=electronics&sort=price_asc
```

### دسته‌بندی‌ها
```
GET /api/v1/categories
GET /api/v1/categories/<slug>/products
```

### وبلاگ
```
GET /api/v1/posts
GET /api/v1/posts/<slug>
```

### سبد خرید
```
GET /api/v1/cart (requires auth)
POST /api/v1/cart/add (requires auth)
```

## 🔒 امنیت

- **CSRF Protection**: تمام فرم‌ها با Flask-WTF
- **XSS Protection**: Sanitization با Bleach
- **SQL Injection**: جلوگیری با SQLAlchemy ORM
- **Rate Limiting**: با Redis
- **Password Hashing**: PBKDF2/SHA256
- **Secure Cookies**: HttpOnly, Secure, SameSite
- **RBAC**: Role-Based Access Control

## 🚢 استقرار

### Docker

```bash
docker-compose up -d
```

### Gunicorn + Nginx

```bash
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app('production')"
```

## 📈 توسعه

### تست

```bash
pytest tests/
pytest --cov=app tests/
```

### افزودن Blueprint جدید

```python
# app/blueprints/new_module/__init__.py
from flask import Blueprint
new_bp = Blueprint('new', __name__)
from app.blueprints.new_module import routes

# app/__init__.py
def register_blueprints(app):
    ...
    from app.blueprints.new_module import new_bp
    app.register_blueprint(new_bp, url_prefix='/new')
```

## 📄 لایسنس

MIT License

## 🤝 مشارکت

درخواست‌های Pull را خوش‌آمد می‌دانیم!

---

ساخته شده با ❤️ و Flask
