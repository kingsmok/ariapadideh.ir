# Flask Pro - Professional Flask CMS

یک وب‌سایت حرفه‌ای و کامل با Flask برای راه‌اندازی فروشگاه، سایت شرکتی یا پرتال محتوا.

## ✨ ویژگی‌ها

- **پنل مدیریت کامل**: مدیریت محصولات، سفارشات، کاربران، صفحات، منوها، مقالات و...
- **فروشگاه آنلاین**: سبد خرید، مقایسه، علاقه‌مندی، پیگیری سفارش، سواچ متغیر (رنگ/تصویر) روی صفحه و کارت محصول، گالری ویدئو (آپارات/یوتیوب)، فیلتر ایجکسی محصولات، فاکتور و لیبل چاپی
- **سیستم محتوا**: وبلاگ با پنل مدیریت کامل + پیش‌نویس AI، صفحات CMS، سوالات متداول
- **صفحه‌سازی بصری**: صفحه‌ساز خانه با درگ‌انددراپ (ترتیب/نمایش/عنوان ۸ بخش) + منوساز هدر/فوتر داینامیک با مگامنو دوستونه
- **چندزبانه (فارسی/انگلیسی)**: نسخهٔ کامل انگلیسی زیر `/en/` (خانه/درباره/تماس/محصولات/وبلاگ/مقاله/سوالات) با سوییچر زبان، LTR، hreflang و sitemap دوزبانه + فیلدهای ترجمهٔ انگلیسی مقالات در پنل با fallback فارسی
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

# 5. راه‌اندازی دیتابیس (دو مسیر)
flask db upgrade     # مسیر استاندارد: Alembic migrations (تولید/استیج)
flask init-db        # مسیر توسعه: create_all سریع روی SQLite
flask create-admin
flask seed-data

# 6. اجرای سرور
python run.py

# 7. (اختیاری) تسک‌های پس‌زمینه — با Redis در دسترس
celery -A worker.celery worker -l INFO --queues=default,mail,notifications
celery -A worker.celery beat   -l INFO
```

### دستورات CLI

```bash
flask db upgrade     # اعمال مهاجرت‌های Alembic
flask db migrate -m "..."   # ساخت مهاجرت جدید از تغییر مدل‌ها
flask init-db        # ایجاد جداول دیتابیس (فقط توسعه)
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
│   ├── tasks/               # Celery Tasks (ایمیل، تلگرام، jobهای زمان‌دار)
│   │   ├── celery_app.py    # کارخانهٔ Celery + enqueue (fallback همگام)
│   │   ├── mail_tasks.py    # ایمیل‌های تراکنشی با retry
│   │   ├── notify_tasks.py  # تلگرام + اعلان ادمین‌ها
│   │   └── order_tasks.py   # لغو خودکار سفارش بی‌پرداخت، پاک‌سازی سبد مهمان
│   ├── templates/           # Jinja2 Templates
│   │   ├── components/      # Header, Footer, etc.
│   │   ├── macros/          # Reusable Components
│   │   └── errors/          # Error Pages
│   └── static/              # CSS, JS, Images
├── migrations/              # Alembic Migrations
├── docker/                  # entrypoint کانتینر
├── tests/                   # Unit Tests
├── .env                     # Environment Variables
├── requirements.txt         # Python Packages
├── worker.py                # ورودی Celery (worker/beat)
├── gunicorn.conf.py         # تنظیمات Gunicorn (از env خوانده می‌شود)
├── Dockerfile               # ایمیج production
├── docker-compose.yml       # Stack کامل: Postgres + Redis + Web + Worker + Beat
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
| `CELERY_ENABLED` | فعال‌سازی صف تسک‌ها (در production پیش‌فرض true) | false |
| `CELERY_BROKER_URL` | آدرس broker | redis://localhost:6379/0 |
| `ORDER_PAYMENT_GRACE_MINUTES` | مهلت پرداخت؛ بعد از آن لغو خودکار + آزادسازی موجودی | 45 |
| `GUEST_CART_RETENTION_DAYS` | نگهداری سبد رهاشدهٔ مهمان‌ها (روز) | 30 |
| `SESSION_REDIS_DB` | دیتابیس Redis برای سشن سمت‌سرور | 2 |
| `VALID_API_KEYS` | کلیدهای `X-API-Key` برای نقاط محافظت‌شدهٔ API | خالی (API خاموش) |

> **سلول ایمنی:** اگر Redis/Celery در دسترس نباشد، `CELERY_ENABLED` خاموش می‌ماند و
> تمام تسک‌ها (ایمیل، تلگرام) **همگام در همین پروسه** اجرا می‌شوند — هیچ قابلیت‌ای
> از کار نمی‌افتد، فقط synchronous است.

### تسک‌های پس‌زمینه (Celery)

| تسک | زمان‌بندی | کارکرد |
|------|-----------|--------|
| `flaskpro.orders.expire_unpaid` | هر ۱۰ دقیقه (beat) | لغو سفارش‌های «در انتظار پرداخت»ِ معوق + بازگرداندن موجودی رزروشده + بستن تراکنش‌های معلق |
| `flaskpro.orders.cleanup_stale_carts` | هر شب ۰۳:۱۵ | حذف سبد رهاشدهٔ کاربران مهمان |
| `flaskpro.mail.*` | رویدادمحور | ایمیل تأیید سفارش / بازیابی رمز / پاسخ تماس با ما (با retry+backoff) |
| `flaskpro.notify.*` | رویدادمحور | اطلاع‌رسانی تلگرام و اعلان ادمین‌ها |

اجرا: `celery -A worker.celery worker -l INFO --queues=default,mail,notifications` و `celery -A worker.celery beat -l INFO` (دقیقاً یک beat).

### سلامت سرویس

`GET /healthz` (و `/api/v1/health`) وابستگی‌ها را پروب می‌کند:
`200 healthy` / `200 degraded` (Redis صف یا worker مشکل دارد ولی سرویس با fallback کار می‌کند) /
`503 down` (دیتابیس از دسترس خارج است — LB باید نود را از روت خارج کند).

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
- **Rate Limiting**: با Redis (fallback درون‌حافظه‌ای در نبود Redis)
- **Password Hashing**: bcrypt/PBKDF2
- **Secure Cookies**: HttpOnly, Secure, SameSite
- **Server-side Sessions**: ذخیره روی Redis + کوکی امضاشدهٔ بی‌محتوا (با `SESSION_TYPE=redis`)
- **API Auth**: هدر `X-API-Key` با مقایسهٔ زمان-ثابت و fail-closed (بدون کلید کانفیگ‌شده، نقاط API روی 503 می‌روند)
- **RBAC**: Role-Based Access Control

## 🚢 استقرار

### Docker (Stack کامل)

`docker-compose.yml` پنج سرویس را بالا می‌آورد: **db** (PostgreSQL 16)، **redis**،
**web** (Gunicorn — همان کانتینر `flask db upgrade` را قبل از سرویس‌دهی اجرا می‌کند)،
**worker** (Celery با سه صف) و **beat** (زمان‌بند).

```bash
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
docker compose up -d --build
docker compose exec web flask create-admin   # اولین ادمین
```

اپ روی `http://localhost:8000`؛ healthcheck کانتینرها از `/healthz` است.
برای overrides کلید سرویس‌ها (درگاه، پیامک، ایمیل) متغیرهای `.env` را ست کنید —
compose همان‌ها را پاس می‌دهد.

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

## 💳 درگاه‌های پرداخت

فروشگاه با ۶ درگاه آماده است: **زرین‌پال، آی‌دی‌پی، دیجی‌پی، اسنپ‌پی (اقساطی)، بانک سپه (الگوی شاپرک)** و درگاه آزمایشی (بدون نیاز به هیچ کلیدی).

- فعال‌سازی: `.env` → `ENABLED_PAYMENT_GATEWAYS=mock,zarinpal,sepah,…` یا پنل مدیریت → تنظیمات → پرداخت
- کلید هر درگاه از پنل مدیریت وارد می‌شود (بر `.env` اولویت دارد) و درگاه بدون کلید به‌صورت خودکار از صفحه پرداخت حذف می‌شود.
- راهنمای کامل API هر درگاه + جریان کال‌بک: [`docs/PAYMENTS.md`](docs/PAYMENTS.md)
- تست: `.venv/bin/python -m pytest tests/test_payment_gateways.py -q`
