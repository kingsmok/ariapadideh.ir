# 🔍 Backend Audit Report — Rahsa Dev (رهسا دیو)

> تاریخ بررسی: ۲۰۲۶-۰۸-۲۳
> بررسی‌کننده: Tech Lead Review
> دامنه: ۳۷ فایل Python، ۵۲۵۴ خط کد، ۱۴۳ روت

---

## 🚨 باگ‌های بحرانی (P0) — بلااستفاده یا ناقص

### ۱. `forgot_password` و `change_password` کار نمی‌کنند
- **فایل**: `app/blueprints/user/routes.py:130-140`, `routes.py:165-185`
- **مشکل**: `forgot_password` token می‌سازد ولی ایمیل نمی‌فرستد (فقط flash می‌کند). `change_password` و `forgot_password` اصلاً token را verify نمی‌کنند.
- **ریسک**: کاربران رمز عبور خود را از دست می‌دهند، قابلیت بازیابی عملاً وجود ندارد.

### ۲. `send_password_reset` و `send_contact_reply` placeholder هستند
- **فایل**: `app/services/notification_service.py:170-180`
- **مشکل**: متدها فقط `return True` می‌کنند، هیچ ایمیلی واقعی ارسال نمی‌شود. TODOها رها شده.
- **ریسک**: کاربران هیچ‌گاه ایمیل بازیابی/تأیید سفارش دریافت نمی‌کنند.

### ۳. `PaymentTransaction` و `checkout` وجود ندارند
- **فایل**: `app/blueprints/public/routes.py:cart()`
- **مشکل**: `cart` فقط نمایش می‌دهد، ولی **checkout، payment gateway، و Order ساختن اصلاً پیاده‌سازی نشده**! `cart.html` دکمه "تکمیل خرید" دارد ولی به `user.checkout` redirect می‌کند که route ندارد.
- **ریسک**: ۱۰۰٪ خراب — کاربر نمی‌تواند خرید کند.

### ۴. `api_required` validation ندارد
- **فایل**: `app/utils/decorators.py:117-130`
- **مشکل**: متد فقط بررسی می‌کند header موجود باشد، validation نمی‌کند. کامنت هم صریحاً گفته "For now, we'll skip validation".
- **ریسک**: هر کسی با هر کلیدی می‌تواند API را صدا بزند.

### ۵. `User.is_active_user()` استفاده می‌شود ولی تعریف نشده در `decorators.py` admin
- **فایل**: `app/blueprints/admin/routes.py:113`
- **مشکل**: `if not user.is_active_user():` — این متد در مدل هست، ولی در `__init__.py` admin route تعریف نشده. احتمال کرش.

### ۶. `Log.log_action` در routes به‌صورت global صدا زده می‌شود ولی `Log` در imports نیست
- **فایل**: `app/blueprints/admin/routes.py:14-23`
- **مشکل**: `Log` در import list است ولی متد `Log.log_action` static نیست و signature اشتباه دارد (در مدل چک کنید).
- **ریسک**: هر admin action کرش می‌کند.

### ۷. `services/__init__.py` خالی است
- **فایل**: `app/services/__init__.py`
- **مشکل**: هیچ `__all__` یا import مرکزی. import ها پراکنده‌اند.

---

## ⚠️ باگ‌های منطقی (P1) — کار می‌کند ولی ناقص

### ۸. N+1 Query در `home()`
- **فایل**: `app/blueprints/public/routes.py:30-100`
- **مشکل**: ۱۰ کوئری جداگانه (sliders, services, portfolio, products, categories, banners×3, posts, faqs). بهینه نیست.
- **ریسک**: صفحه اصلی کند load می‌شود.

### ۹. `category` route از `is_in_stock` استفاده می‌کند ولی این property در product تعریف نشده
- **فایل**: `app/blueprints/public/routes.py:175` و `app/services/cart_service.py:67`
- **ریسک**: AttributeError هنگام افزودن به سبد.

### ۱۰. Cache `query_string=True` باعث cache miss بی‌نهایت می‌شود
- **فایل**: `app/blueprints/public/routes.py:38, 154, 285, 332, 388`
- **مشکل**: `@cache.cached(timeout=300, query_string=True)` یعنی به ازای هر `?utm_source=...` یک entry جدید. Cache بی‌نهایت بزرگ می‌شود.
- **ریسک**: memory leak در Flask-Caching.

### ۱۱. `get_pagination_params` و `get_pagination_data` duplicate هستند
- **فایل**: `app/utils/helpers.py:117-160`
- **مشکل**: `get_pagination_data` تعریف شده ولی در هیچ جا استفاده نمی‌شود. routes از `paginate()` مستقیم استفاده می‌کنند.

### ۱۲. `Wishlist` و `Comparison` add/remove تکراری
- **فایل**: `app/blueprints/user/routes.py:380-440`
- **مشکل**: هم route `wishlist_add` و هم API `api_wishlist_toggle` وجود دارد. ولی UI دکمه‌ای برای آن‌ها ندارد.

### ۱۳. `MediaService.save_*` هیچ‌کدام validation MIME type ندارند
- **فایل**: `app/services/media_service.py:158-260`
- **مشکل**: فقط extension چک می‌شود. امکان upload فایل malicious با rename.

### ۱۴. `Order.calculate_totals()` استفاده نمی‌شود
- **فایل**: `app/models/order.py`
- **مشکل**: متد تعریف شده ولی route یا service آن را صدا نمی‌زند. total_amount همیشه 0.

### ۱۵. `MediaService.process_image` فقط thumbnail می‌سازد ولی اصل را optimize نمی‌کند
- **فایل**: `app/services/media_service.py:124-152`
- **مشکل**: `img.save(str(filepath), 'WEBP', quality=85)` بعد از ساخت thumbnail، ولی اگر فرمت اصلی webp نباشد، فایل اصلی format اشتباه ذخیره می‌شود.

### ۱۶. `delete` در BaseModel commit می‌کند ولی خطا نمی‌دهد اگر commit شکست بخورد
- **فایل**: `app/models/base.py:63-70`

### ۱۷. `BaseModel.save()` exception handling ندارد
- **فایل**: `app/models/base.py:53-57`
- **ریسک**: اگر db down باشد، request crash می‌کند نه 500 graceful.

### ۱۸. Forms `ContactForm` validation فارسی ندارد
- **فایل**: `app/blueprints/public/forms.py` (احتمالی)
- **ریسک**: شماره تلفن فارسی قبول نمی‌کند.

### ۱۹. `Contact` model `ip_address` ذخیره می‌شود ولی rate limit نمی‌شود
- **فایل**: `app/blueprints/public/routes.py:contact()`
- **ریسک**: spam بدون rate limit.

### ۲۰. SEO service `page_type='home'` hard-coded
- **فایل**: `app/services/seo_service.py:145`
- **مشکل**: home_title در settings ذخیره می‌شود ولی schema_org داده نمی‌شود.

### ۲۱. `app/__init__.py` تمام context processors در هر request اجرا می‌شوند
- **فایل**: `app/__init__.py:register_context_processors`
- **مشکل**: `SettingService.get_public_settings()` در هر request کوئری می‌زند.
- **ریسک**: performance hit.

### ۲۲. `inject_globals` در هر request query می‌زند
- **فایل**: `app/__init__.py:register_context_processors`
- **ریسک**: overhead.

### ۲۳. `current_year` با `__import__` غیراصولی
- **فایل**: `app/__init__.py:172`
- **مشکل**: `__import__('datetime').datetime.now().year` — باید `from datetime import datetime` و `datetime.now().year`.

### ۲۴. Blog post `featured_image` fallback به `no-image.png` ولی این فایل وجود ندارد
- **فایل**: چندین تمپلیت
- **ریسک**: 404 روی تصویر.

### ۲۵. `MediaService.delete` thumbnail path را اشتباه محاسبه می‌کند
- **فایل**: `app/services/media_service.py:262-280`
- **مشکل**: `current_app.config['BASE_DIR'] / 'app' / 'static' / media.thumbnail_url.lstrip('/')` — اگر URL با `/static/` شروع شود، double-slash می‌شود.

### ۲۶. Forms `ProductForm` و `CategoryForm` validation ندارند
- **فایل**: `app/blueprints/admin/forms.py`
- **ریسک**: ادمین می‌تواند قیمت منفی وارد کند.

### ۲۷. `Product.stock_quantity` کاهش نمی‌یابد بعد از خرید
- **مشکل**: در `Order.calculate_totals` stock check نمی‌شود.

### ۲۸. `User.update_last_login` failed_login_attempts را reset نمی‌کند
- **فایل**: `app/models/user.py:update_last_login`
- **ریسک**: brute force detection ندارد.

### ۲۹. Session secret key ضعیف در dev
- **فایل**: `app/config.py:Config.SECRET_KEY`
- **مشکل**: default `'dev-secret-key-change-in-production'` اگر env var تنظیم نشود.

### ۳۰. CSRF روی API endpoint های POST اعمال نمی‌شود
- **فایل**: `app/blueprints/user/routes.py:api_*`
- **ریسک**: CSRF attack.

---

## 🟡 امکانات ناقص (P2) — وعده داده شده ولی پیاده نشده

### ۳۱. Checkout & Payment Gateway
- **نبود**: route، template، service
- **نیاز**: `POST /checkout`, `GET /checkout/success`, payment gateway integration (Zarinpal, IDPay)

### ۳۲. Order Management برای کاربر
- **ناقص**: `user/orders.html`, `user/order_detail.html` templates reference شده ولی route‌ها route شده‌اند. test نشده.

### ۳۳. Search autocomplete UI
- **ناقص**: `api_quick_search` route دارد ولی UI در header ندارد.

### ۳۴. Newsletter subscription
- **نبود**: route و UI

### ۳۵. Product reviews/ratings
- **ناقص**: `Product.rating_avg` field دارد ولی review model و route ندارد.

### ۳۶. Discount/Coupon system
- **ناقص**: `Order.discount_code` field دارد ولی service و validation ندارد.

### ۳۷. Email verification flow
- **ناقص**: `verification_token` field دارد ولی verify route و email template ندارد.

### ۳۸. Multi-language (i18n)
- **نبود**: باوجود Babel، فقط fa وجود دارد.

### ۳۹. Two-factor authentication
- **نبود**: باوجود `is_verified` و `verification_token`

### ۴۰. File upload validation (MIME check)
- **ناقص**: فقط extension چک می‌شود.

### ۴۱. Backup/restore
- **نبود**

### ۴۲. Audit log viewer
- **ناقص**: route دارد ولی template ندارد (`admin/logs/list.html`)

### ۴۳. Email queue (Celery)
- **ناقص**: Celery config ولی worker setup نشده.

### ۴۴. Export to PDF
- **نبود**

### ۴۵. Refund flow
- **ناقص**: `Order.status = 'refunded'` ولی route ندارد.

### ۴۶. Address edit
- **ناقص**: `user/address_edit.html` template reference شده ولی template خودش نیست.

### ۴۷. Profile templates
- **ناقص**: `user/profile.html`, `user/change_password.html` reference شده.

### ۴۸. Wishlist/Compare UI
- **ناقص**: route دارد ولی `product.html` دکمه ندارد.

---

## 🟢 بهبودهای کیفی (P3)

### ۴۹. N+1 در `home()` — eager loading نیست
### ۵۰. تست‌های خودکار — pytest config نشده
### ۵۱. Type hints ناقص در routes
### ۵۲. Docstring در routes کم است
### ۵۳. Magic strings ('admin', 'paid' و...) به constants نیاز دارند
### ۵۴. `cache_key_prefix` در همه cache call ها استفاده نمی‌شود
### ۵۵. `app.config['WTF_CSRF_HEADERS']` شامل `X-CSRF-Token` نیست (template ها از `X-CSRFToken` استفاده می‌کنند)
### ۵۶. Jinja auto-reload همیشه فعال در debug — performance
### ۵۷. Logging در routes کم است
### ۵۸. Try/except در `send_*` template calls
### ۵۹. `app.logger.info` در routes init نمی‌شود
### ۶۰. `flask db migrate` workflow مستند نیست

---

## 📊 خلاصه آماری

| دسته | تعداد |
|---|---|
| باگ بحرانی P0 | ۷ |
| باگ منطقی P1 | ۲۳ |
| امکانات ناقص P2 | ۱۸ |
| بهبود کیفی P3 | ۱۲ |
| **جمع** | **۶۰ مورد** |

---

## 🗺️ نقشه راه پیشنهادی (Roadmap)

### فاز ۱ — ثبات (Stability) — ۲ روز
1. P0-3: پیاده‌سازی کامل Checkout + Order creation
2. P0-1, P0-2: پیاده‌سازی واقعی `forgot_password`, `change_password`, `send_password_reset`
3. P0-5, P0-6: بررسی و fix کرش‌های `is_active_user` و `Log.log_action`
4. P1-9: fix `is_in_stock` property
5. P1-14: فراخوانی `calculate_totals` در checkout

### فاز ۲ — امنیت (Security) — ۱.۵ روز
6. P1-19: rate limit روی contact form
7. P1-26: form validation قوی
8. P1-30: CSRF در API
9. P0-4: API key validation واقعی
10. P1-28: brute force lockout

### فاز ۳ — Performance — ۱ روز
11. P1-8, P3-49: eager loading در home, dashboard
12. P1-10: cache query_string → cache key اصلاح شود
13. P1-21, P1-22: cache کردن site_settings
14. P3-56: Jinja auto-reload conditional

### فاز ۴ — ویژگی‌های UX — ۲ روز
15. P2-33: search autocomplete
16. P2-48: wishlist/compare buttons
17. P2-32: order detail templates
18. Loading states + empty states در API responses

### فاز ۵ — Polish — ۱ روز
19. P3-50: تست‌های خودکار
20. P3-51-52: type hints + docstrings
21. P3-53: constants module
22. P2-44: logs template
