"""
تحقیق بازار قالب‌های شرکتی وردپرس (مارکت راست‌چین)
====================================================

منبع: https://www.rtl-theme.com/category/wp-themes/business-wordpress/
تاریخ برداشت: ۱۴۰۵/۰۶/۰۲ (۲۰۲۶-۰۸-۲۴)

دسته «قالب شرکتی وردپرس» راست‌چین شامل ۱۸ قالب است که در چهار صفحهٔ
جزئیات (ستیا، آرنیکا، نادر، کرافتو) به‌صورت عمیق و بقیه از روی اطلاعات
صفحهٔ دسته‌بندی (فروش، رضایت، درجه پشتیبانی، قیمت، حوزه فعالیت) تحلیل شده‌اند.

این داده فقط برای مرجع داخلی (صفحهٔ پنل مدیریت) است و
هیچ‌گونه محتوایی از راست‌چین کپی نشده است.
"""

RESEARCH_META = {
    "title": "تحلیل بازار قالب‌های شرکتی وردپرس",
    "source_name": "راست‌چین (RTL-Theme)",
    "source_url": "https://www.rtl-theme.com/category/wp-themes/business-wordpress/",
    "collected_at": "۲۰۲۶-۰۸-۲۴",
    "collected_at_fa": "۱۴۰۵/۰۶/۰۲",
    "deep_dived": ["ستیا (Setiya)", "آرنیکا (Arnika)", "نادر (Nader)", "کرافتو (Crafto)"],
    "note": (
        "۴ قالب به‌صورت عمیق (صفحه محصول کامل) و بقیه از روی کارت اطلاعات "
        "صفحهٔ دسته‌بندی تحلیل شده‌اند. قیمت‌ها تومان و مربوط به زمان برداشت است."
    ),
}

# ---------------------------------------------------------------------------
# ۱۸ قالب دستهٔ «قالب شرکتی وردپرس»
# ---------------------------------------------------------------------------
# category: corporate | multipurpose | specialized
# origin: iranian | international
THEMES = [
    {
        "slug": "nader",
        "title": "قالب شخصی و شرکتی نادر",
        "en_title": "Nader",
        "origin": "iranian",
        "category": "multipurpose",
        "category_label": "شرکتی / شخصی / فروشگاهی",
        "sales": 2131,
        "satisfaction": 86,
        "support": "A+",
        "price_toman": 1_465_000,
        "discount_percent": 0,
        "url": "https://www.rtl-theme.com/nader-wordpress-theme/",
        "thumbnail": "https://media.rtlcdn.com/2026/08/a70562788a1041886119b139233c27bc79d6a98189169c-590x300.jpg",
        "demos": "۱۸ دموی دوزبانه + بسته نصبی",
        "builder": "المنتور + ۱۳۶ ویجت اختصاصی",
        "design_style": "چندسبکه؛ شرکتی، شخصی و فروشگاهی با پنل تنظیمات پیشرفته و رنگ‌بندی نامحدود",
        "highlights": [
            "ورود و عضویت پیامکی (OTP) با AJAX و پشتیبانی از ۷ پنل پیامکی (ملی‌پیامک، کاوه‌نگار، sms.ir و…)",
            "استوری‌ساز اختصاصی شبیه اینستاگرام (عکس/ویدئو، دسته‌بندی، زمان‌بندی نمایش)",
            "سیستم تیکت پشتیبانی اختصاصی با پیوست فایل + اخبار و اطلاعیهٔ پنل کاربری با تاریخ شمسی",
            "مگامنوی ۵ استایل، هدر/فوتر اختصاصی برای هر صفحه، منوی چسبان موبایل اپ‌مانند",
            "فروشگاهی: ۶ طرح کارت محصول، فیلتر ایجکسی سئو-محور، Variation Swatches چهارگانه، رهگیری سفارش، سبد و پرداخت مشابه دیجی‌کالا",
            "۵ فونت پریمیوم ایرانی با لایسنس (ایران‌سنس، ایران‌یکان، دانا، امکان، مربع)",
            "امنیت چندلایه (خاموش‌کردن XML-RPC/REST-API، پنهان‌سازی نسخه) + گزارش فعالیت ادمین به تلگرام و بله",
            "گالری پروژه با ۶ طرح و فیلتر، ۱۰ طرح Preloader، تم تیره/روشن، بردکرامب و جستجوی ایجکسی کش‌شده",
        ],
        "specs": {
            "دمو": "۱۸ عدد (همگی دوزبانه)",
            "ویجت‌ها": "۱۳۶+ ویجت اختصاصی المنتور",
            "چندزبانه": "WPML و Polylang (آمادهٔ دوزبانه)",
            "فروشگاه": "ووکامرس (عمیق) + فاکتورساز و لیبل‌ساز",
            "فونت": "۵ فونت پریمیوم ایرانی",
            "نسخه": "9.10.0",
        },
    },
    {
        "slug": "setiya",
        "title": "قالب شرکتی ستیا",
        "en_title": "Setiya",
        "origin": "iranian",
        "category": "corporate",
        "category_label": "شرکتی",
        "sales": 68,
        "satisfaction": 66,
        "support": None,
        "price_toman": 948_000,
        "discount_percent": 0,
        "url": "https://www.rtl-theme.com/setiya-wordpress-theme/",
        "thumbnail": "https://media.rtlcdn.com/2025/02/7ea2d92502ea128cc8663750d12e4ea4c1ea327493d29a-590x300.jpg",
        "demos": "۳ صفحه اصلی + صفحات داخلی",
        "builder": "المنتور + ۳۰+ المان اختصاصی",
        "design_style": "مدرن و مینیمال بر پایهٔ Bootstrap 5؛ مناسب استارتاپ، آژانس، نمونه‌کار و وبلاگ",
        "highlights": [
            "۳ صفحه اصلی متفاوت + صفحات خدمات، پروژه‌ها، تیم، فروشگاه و وبلاگ",
            "پنل تنظیمات Redux با رنگ‌بندی نامحدود و انتخاب جداگانهٔ فونت متن و تیتر",
            "۴ طرح Preloader از پیش طراحی‌شده و قابل مدیریت",
            "حساب کاربری کاربران + اطلاعیه‌ها در پنل کاربری (نسخهٔ 3.1 به بعد)",
            "سازگار با Contact Form 7 و Polylang (دوزبانه)",
            "بدون ووکامرس → تمرکز روی سرعت و سبکی (تصمیم آگاهانهٔ طراح)",
        ],
        "specs": {
            "فریمورک": "Bootstrap 5.x + فونت‌آیکون",
            "پنل تنظیمات": "Redux",
            "دمو": "۳ صفحه اصلی",
            "چندزبانه": "Polylang",
            "فروشگاه": "ندارد (فوکوس سرعت)",
            "سازگاری": "PHP 7.4 / WordPress 5.8–6.7",
        },
    },
    {
        "slug": "arnika",
        "title": "قالب شرکتی آرنیکا",
        "en_title": "Arnika",
        "origin": "iranian",
        "category": "corporate",
        "category_label": "شرکتی",
        "sales": 161,
        "satisfaction": 60,
        "support": "A+",
        "price_toman": 1_548_000,
        "discount_percent": 0,
        "url": "https://www.rtl-theme.com/arnika-wordpress-theme/",
        "thumbnail": "https://media.rtlcdn.com/2022/12/6d55d62c10923d04b0a1661b99b9ddbd77eb7454678431-590x300.jpg",
        "demos": "۶ دمو (+ دموی جدید در هر بروزرسانی)",
        "builder": "المنتور + سفارشی‌سازی زنده",
        "design_style": "مدرن با سلیقهٔ ایرانی؛ اسلایدرها و کاروسل‌ها متناسب با سلیقهٔ مخاطب فارسی‌زبان",
        "highlights": [
            "سربرگ‌ساز و پاورقی‌ساز حرفه‌ای در سفارشی‌سازی قالب",
            "فونت‌های رایگان ایرانی: ایران‌یکان، پرستو، استعداد، شبنم و…",
            "اعضای تیم با سبک‌های متعدد + نوار مهارت خطی و دایره‌ای",
            "گالری تصاویر و نمونه‌کارهای حرفه‌ای + صفحهٔ اختصاصی خدمات و درباره ما",
            "نقشهٔ OpenStreetMap در تماس (بدون مشکل تحریم و بدون نیاز به API)",
            "جداول قیمت و لیست تعرفه + فرم تماس داخل المنتور بدون افزونه",
            "قابل تبدیل به چپ‌چین و دوزبانه با Polylang / WPML",
        ],
        "specs": {
            "دمو": "۶ صفحهٔ خانه (+ دموهای جدید در آپدیت‌ها)",
            "چندزبانه": "Polylang و WPML",
            "نقشه": "OpenStreetMap",
            "فونت": "ایران‌یکان، پرستو، استعداد، شبنم…",
            "سازگاری": "PHP 7.4 – 8.2 / ووکامرس استاندارد",
            "نسخه": "1.4.2",
        },
    },
    {
        "slug": "crafto",
        "title": "کرافتو، قالب چندمنظوره با پشتیبانی هوش مصنوعی",
        "en_title": "Crafto",
        "origin": "international",
        "category": "multipurpose",
        "category_label": "چندمنظوره (+AI)",
        "sales": 130,
        "satisfaction": 86,
        "support": "A+",
        "price_toman": 1_348_000,
        "discount_percent": 0,
        "url": "https://www.rtl-theme.com/crafto-wordpress-theme/",
        "thumbnail": "https://media.rtlcdn.com/2025/12/97987708f049728717b760b38758ad7bcf376506c995c2-590x300.jpg",
        "demos": "۴۸ دمو + ۵۰۰ صفحه آماده + ۱۴۵۰ الگو",
        "builder": "المنتور + ۱۰۰+ ابزارک اختصاصی (درگ‌انددراپ)",
        "design_style": "خلاقانه و خیره‌کننده؛ وکالت، مشاورهٔ مالی، کلینیک، سالن زیبایی و کسب‌وکارهای عمومی",
        "highlights": [
            "ادغام با هوش مصنوعی: تولید مقاله (عنوان/محتوا/برچسب)، تولید تصویر، تولید محتوای سئو + ربات چت یکپارچه",
            "۴۸ دمو، ۵۰۰+ صفحهٔ آماده و ۱۴۵۰+ الگوی المنتور",
            "بهینه‌سازی Core Web Vitals: Critical CSS، مینی‌فای، لیزی‌لود، پیش‌بارگذاری هوشمند (prefetch صفحهٔ بعد)",
            "سازندهٔ هدر، فوتر، پست تکی، پاپ‌آپ، آرشیو و ۴۰۴ با المنتور + بخش/ستون چسبنده",
            "بیش از ۱۰۰ فونت فارسی + استایل جهانی المنتور (رنگ/تایپوگرافی/چیدمان)",
            "سازگار با ووکامرس، RankMath/Yoast، WPML/Polylang، GiveWP، LearnPress، MailChimp و افزونه‌های کش",
        ],
        "specs": {
            "دمو": "۴۸ دمو / ۵۰۰+ صفحه / ۱۴۵۰+ الگو",
            "ویجت‌ها": "۱۰۰+ ابزارک اختصاصی",
            "هوش مصنوعی": "متن + تصویر + چت‌بات",
            "فونت": "۱۰۰+ فونت فارسی",
            "عملکرد": "PHP 8، Critical CSS، کاهش ۵۰٪ کوئری‌ها",
            "نسخه": "2.1",
        },
    },
    {
        "slug": "xtra",
        "title": "قالب اکسترا، پرفروش‌ترین قالب چندمنظوره",
        "en_title": "Xtra",
        "origin": "international",
        "category": "multipurpose",
        "category_label": "چندمنظوره / ووکامرس",
        "sales": 31_691,
        "satisfaction": 90,
        "support": "A+",
        "price_toman": 2_047_000,
        "discount_percent": 0,
        "url": "https://www.rtl-theme.com/xtra-corporate-woocommerce-theme/",
        "thumbnail": None,
        "demos": "دموهای متعدد (شرکتی + معماری مینیمال + فروشگاهی)",
        "builder": "المنتور / WPBakery",
        "design_style": "چندمنظورهٔ استودیویی؛ از شرکتی تا فروشگاهی و معماری مینیمال",
        "highlights": [
            "پرفروش‌ترین قالب دسته با ۳۱,۶۹۱ فروش",
            "پوشش وسیع دموها: شرکتی، فروشگاهی، معماری و دکوراسیون مینیمال",
            "گران‌ترین قالب دسته (۲,۰۴۷,۰۰۰ تومان) با رضایت ۹۰٪",
        ],
        "specs": {
            "فروش": "۳۱,۶۹۱ (رکورد دسته)",
            "رضایت": "۹۰٪ + پشتیبانی A+",
            "قیمت": "گران‌ترین قالب دسته",
        },
    },
    {
        "slug": "betheme",
        "title": "قالب بی تم، قالب چندمنظوره و فروشگاهی",
        "en_title": "Betheme",
        "origin": "international",
        "category": "multipurpose",
        "category_label": "چندمنظوره / فروشگاهی",
        "sales": 7_308,
        "satisfaction": 80,
        "support": "A+",
        "price_toman": 740_850,
        "discount_percent": 45,
        "url": "https://www.rtl-theme.com/betheme/",
        "thumbnail": "https://media.rtlcdn.com/2026/06/4a94f9c8014d6e4987c6e61007319920002bd8c77163fa-590x300.jpg",
        "demos": "صدها وب‌سایت آماده",
        "builder": "بیلدر اختصاصی Muffin + المنتور",
        "design_style": "چندمنظورهٔ کلاسیک با کتابخانهٔ عظیم وب‌سایت‌های آماده",
        "highlights": [
            "۷,۳۰۸ فروش؛ دومین قالب پرفروش این دسته",
            "کتابخانهٔ عظیم دموهای آمادهٔ شرکتی و فروشگاهی",
            "با تخفیف ۴۵٪ مقرون‌به‌صرفه‌ترین گزینهٔ بین قالب‌های پرفروش",
        ],
        "specs": {
            "فروش": "۷,۳۰۸",
            "رضایت": "۸۰٪ + پشتیبانی A+",
            "تخفیف": "۴۵٪ (۷۴۰,۸۵۰ تومان)",
        },
    },
    {
        "slug": "divi",
        "title": "قالب Divi، کاملترین نسخهٔ قالب دیوی",
        "en_title": "Divi",
        "origin": "international",
        "category": "multipurpose",
        "category_label": "چندمنظوره",
        "sales": 3_350,
        "satisfaction": 86,
        "support": "A+",
        "price_toman": 1_675_000,
        "discount_percent": 0,
        "url": "https://www.rtl-theme.com/divi-multi-purpose-wordpress-theme/",
        "thumbnail": "https://media.rtlcdn.com/2026/07/b091f725836301034747b9785217f3515919b2d8c8aa4a-590x300.jpg",
        "demos": "صدها layout pack آماده",
        "builder": "Divi Builder (صفحه‌ساز بصری نقطه‌وکلیک)",
        "design_style": "چندمنظوره با صفحه‌ساز بصری سراسری (Theme Builder برای هدر/فوتر/آرشیوها)",
        "highlights": [
            "صفحه‌ساز بصری Divi Builder با ویرایش نقطه‌وکلیک روی خود صفحه",
            "Theme Builder برای طراحی سراسری هدر، فوتر، صفحهٔ محصول و آرشیوها",
            "۳,۳۵۰ فروش و شبکهٔ گستردهٔ آموزش و افزونه‌های جانبی",
        ],
        "specs": {
            "فروش": "۳,۳۵۰",
            "رضایت": "۸۶٪ + پشتیبانی A+",
            "بیلدر": "Divi Builder",
        },
    },
    {
        "slug": "phlox",
        "title": "قالب Phlox Pro، چندمنظورهٔ فلوکس",
        "en_title": "Phlox Pro",
        "origin": "international",
        "category": "multipurpose",
        "category_label": "چندمنظوره",
        "sales": 4_641,
        "satisfaction": 84,
        "support": "A+",
        "price_toman": 1_985_000,
        "discount_percent": 0,
        "url": "https://www.rtl-theme.com/phlox-corporate-wordpress-theme/",
        "thumbnail": "https://media.rtlcdn.com/2026/07/d79761214440e2b6e62b5048432aa0f1d7200173792165-590x300.jpg",
        "demos": "دموهای متعدد شرکتی/فروشگاهی",
        "builder": "المنتور",
        "design_style": "چندمنظورهٔ مدرن با دموهای متنوع کسب‌وکاری",
        "highlights": [
            "۴,۶۴۱ فروش؛ جزو پرفروش‌های دسته",
            "پشتیبانی کامل از المنتور و دموهای متنوع",
            "نزدیک‌ترین رقیب قیمتیمت به اکسترا (۱,۹۸۵,۰۰۰ تومان)",
        ],
        "specs": {
            "فروش": "۴,۶۴۱",
            "رضایت": "۸۴٪ + پشتیبانی A+",
            "قیمت": "۱,۹۸۵,۰۰۰ تومان",
        },
    },
    {
        "slug": "essentials",
        "title": "قالب Essentials، اسنشیالز + ۴۳ دمو",
        "en_title": "Essentials",
        "origin": "international",
        "category": "multipurpose",
        "category_label": "چندمنظوره",
        "sales": 1_618,
        "satisfaction": 48,
        "support": "B+",
        "price_toman": 1_748_000,
        "discount_percent": 0,
        "url": "https://www.rtl-theme.com/essentials-wordpress-theme/",
        "thumbnail": "https://media.rtlcdn.com/2023/05/9402b2b8db4d26a796464560b0083763096b96c5511c88-590x300.jpg",
        "demos": "۴۳+ دمو",
        "builder": "المنتور",
        "design_style": "چندمنظورهٔ مدرن و پرامکانات",
        "highlights": [
            "۴۳ دموی آمادهٔ متنوع",
            "۱,۶۱۸ فروش ولی رضایت ۴۸٪ و پشتیبانی B+ (پایین‌ترین کیفیت پشتیبانی این دسته)",
            "نمونه‌ای از اهمیت «رضایت کاربر» بیش از تعداد امکانات",
        ],
        "specs": {
            "فروش": "۱,۶۱۸",
            "رضایت": "۴۸٪ (پایین‌ترین دسته)",
            "پشتیبانی": "B+",
        },
    },
    {
        "slug": "ave",
        "title": "قالب ایو، پوستهٔ چندمنظورهٔ Ave",
        "en_title": "Ave",
        "origin": "international",
        "category": "multipurpose",
        "category_label": "چندمنظوره",
        "sales": 1_182,
        "satisfaction": 98,
        "support": "A+",
        "price_toman": 1_289_000,
        "discount_percent": 0,
        "url": "https://www.rtl-theme.com/ave-multiporpose-wordpress-theme/",
        "thumbnail": None,
        "demos": "دموهای متعدد (از جمله مؤسسهٔ دیجیتال خلاقانه)",
        "builder": "المنتور",
        "design_style": "خلاقانه و مدرن؛ دموهای آژانس دیجیتال و مؤسسات خلاق",
        "highlights": [
            "بالاترین رضایت کاربران کل دسته: ۹۸٪",
            "دموهای خلاقانه مناسب آژانس‌ها و مؤسسات دیجیتال",
            "نسبت قیمت به رضایت عالی (۱,۲۸۹,۰۰۰ تومان)",
        ],
        "specs": {
            "فروش": "۱,۱۸۲",
            "رضایت": "۹۸٪ (بالاترین دسته)",
            "پشتیبانی": "A+",
        },
    },
    {
        "slug": "ewebot",
        "title": "قالب Ewebot، قالب شرکتی ایوبات",
        "en_title": "Ewebot",
        "origin": "international",
        "category": "corporate",
        "category_label": "شرکتی (IT/سئو)",
        "sales": 602,
        "satisfaction": 90,
        "support": "A+",
        "price_toman": 1_248_000,
        "discount_percent": 0,
        "url": "https://www.rtl-theme.com/ewebot-corporate-wordpress-theme/",
        "thumbnail": "https://media.rtlcdn.com/2024/02/d59f942f86047263d041f7f71af198838c4893ad7178a2-590x300.jpg",
        "demos": "دموهای چندگانهٔ خدمات IT",
        "builder": "المنتور",
        "design_style": "تخصصی خدمات IT، سئو و دیجیتال مارکتینگ",
        "highlights": [
            "محبوب‌ترین قالب شرکتی خارجی این دسته (۶۰۲ فروش) با رضایت ۹۰٪",
            "طراحی تخصصی برای آژانس‌های سئو و خدمات وب",
        ],
        "specs": {
            "فروش": "۶۰۲",
            "رضایت": "۹۰٪ + پشتیبانی A+",
            "حوزه": "IT / سئو / دیجیتال مارکتینگ",
        },
    },
    {
        "slug": "creote",
        "title": "قالب شرکتی Creote، کریوت",
        "en_title": "Creote",
        "origin": "international",
        "category": "corporate",
        "category_label": "شرکتی / مشاوره",
        "sales": 832,
        "satisfaction": 84,
        "support": "A+",
        "price_toman": 1_247_000,
        "discount_percent": 0,
        "url": "https://www.rtl-theme.com/creote-wordpress-theme/",
        "thumbnail": "https://media.rtlcdn.com/2023/03/158d30184b2b4b9a783c137f08c5838e6d9a34a67ab92d-590x300.jpg",
        "demos": "دموهای متعدد مشاوره/کسب‌وکار",
        "builder": "المنتور",
        "design_style": "شرکتی کلاسیک-مدرن مناسب مشاورهٔ کسب‌وکار",
        "highlights": [
            "پرفروش‌ترین قالب شرکتی خالص (غیر چندمنظوره) دسته با ۸۳۲ فروش",
            "تمرکز بر صفحات خدمات و مشاورهٔ کسب‌وکار",
        ],
        "specs": {
            "فروش": "۸۳۲",
            "رضایت": "۸۴٪ + پشتیبانی A+",
        },
    },
    {
        "slug": "ramzineh",
        "title": "قالب شرکتی ارز دیجیتال رمزینه",
        "en_title": "Ramzineh",
        "origin": "iranian",
        "category": "specialized",
        "category_label": "تخصصی (کریپتو/بلاک‌چین)",
        "sales": 197,
        "satisfaction": 84,
        "support": "A+",
        "price_toman": 539_200,
        "discount_percent": 60,
        "url": "https://www.rtl-theme.com/ramzineh-wordpress-theme/",
        "thumbnail": "https://media.rtlcdn.com/2026/07/0fd396051144fd6e16381a723c5a4974368715542c754-590x300.jpg",
        "demos": "دموی تخصصی ارز دیجیتال",
        "builder": "المنتور",
        "design_style": "تخصصی حوزهٔ ارز دیجیتال و بلاک‌چین",
        "highlights": [
            "تنها قالب تخصصی کریپتوی این دسته",
            "با تخفیف ۶۰٪ ارزان‌ترین گزینهٔ فعلی دسته (۵۳۹,۲۰۰ تومان)",
        ],
        "specs": {
            "فروش": "۱۹۷",
            "رضایت": "۸۴٪ + پشتیبانی A+",
            "تخفیف": "۶۰٪",
        },
    },
    {
        "slug": "luxina",
        "title": "قالب شرکتی معماری و ساختمانی لوکسینا",
        "en_title": "Luxina",
        "origin": "iranian",
        "category": "specialized",
        "category_label": "تخصصی (معماری/دکوراسیون)",
        "sales": 318,
        "satisfaction": 91,
        "support": "A+",
        "price_toman": 1_448_000,
        "discount_percent": 0,
        "url": "https://www.rtl-theme.com/luxina-wordpress-theme/",
        "thumbnail": "https://media.rtlcdn.com/2025/10/cdfc15e6c5abba5cf646f6bb4d732c136738cd3cd074e3-590x300.jpg",
        "demos": "دموهای معماری و پروژه",
        "builder": "المنتور",
        "design_style": "لوکس و مینیمال؛ گالری‌محور برای معماری و دکوراسیون داخلی",
        "highlights": [
            "رضایت ۹۱٪ — جزو بالاترین‌های قالب‌های ایرانی",
            "طراحی گالری‌محور مناسب نمایش پروژه‌های معماری",
        ],
        "specs": {
            "فروش": "۳۱۸",
            "رضایت": "۹۱٪ + پشتیبانی A+",
            "حوزه": "معماری / ساختمان / دکوراسیون داخلی",
        },
    },
    {
        "slug": "seofy",
        "title": "قالب Seofy، پوستهٔ شرکتی سئوفای",
        "en_title": "Seofy",
        "origin": "international",
        "category": "corporate",
        "category_label": "شرکتی (سئو/آژانس)",
        "sales": 199,
        "satisfaction": 80,
        "support": "A+",
        "price_toman": 1_347_000,
        "discount_percent": 0,
        "url": "https://www.rtl-theme.com/seofy-creative-wordpress-theme/",
        "thumbnail": "https://media.rtlcdn.com/2022/01/61c6041b65bad0dc24e73ad642ffe060502d2b51608fd2-590x300.png",
        "demos": "دموهای آژانس سئو",
        "builder": "WPBakery",
        "design_style": "آژانسی مدرن برای شرکت‌های سئو و تبلیغات",
        "highlights": [
            "طراحی تخصصی آژانس‌های سئو و مارکتینگ",
            "۱۹۹ فروش با رضایت ۸۰٪",
        ],
        "specs": {
            "فروش": "۱۹۹",
            "رضایت": "۸۰٪ + پشتیبانی A+",
        },
    },
    {
        "slug": "vankine",
        "title": "قالب شرکتی Vankine، ونکاین",
        "en_title": "Vankine",
        "origin": "international",
        "category": "corporate",
        "category_label": "شرکتی",
        "sales": 255,
        "satisfaction": 80,
        "support": "A+",
        "price_toman": 1_248_000,
        "discount_percent": 0,
        "url": "https://www.rtl-theme.com/vankine-wordpress-theme/",
        "thumbnail": "https://media.rtlcdn.com/2023/05/8031d32d2a73d981e32852c700892a76c10ef3ec1160f2-590x300.jpg",
        "demos": "دموهای چندگانه",
        "builder": "المنتور",
        "design_style": "شرکتی مدرن عمومی",
        "highlights": [
            "قالب شرکتی عمومی با رضایت ۸۰٪",
            "۲۵۵ فروش",
        ],
        "specs": {
            "فروش": "۲۵۵",
            "رضایت": "۸۰٪ + پشتیبانی A+",
        },
    },
    {
        "slug": "arvin",
        "title": "قالب وردپرس شرکتی و فروشگاهی آروین",
        "en_title": "Arvin",
        "origin": "iranian",
        "category": "multipurpose",
        "category_label": "شرکتی / فروشگاهی",
        "sales": 27,
        "satisfaction": 100,
        "support": None,
        "price_toman": 1_448_000,
        "discount_percent": 0,
        "url": "https://www.rtl-theme.com/arvin-wordpress-theme/",
        "thumbnail": "https://media.rtlcdn.com/2026/08/8a935b476dd8365a68a1a789fb6f96fccf62d9e5863617-590x300.jpg",
        "demos": "دموهای شرکتی + فروشگاهی",
        "builder": "المنتور",
        "design_style": "جدیدترین قالب ایرانی دسته (۱۴۰۵)؛ شرکتی + فروشگاهی",
        "highlights": [
            "تازه‌منتشرشده (تابستان ۱۴۰۵) با رضایت ۱۰۰٪ از ۲۷ خریدار",
            "ترکیب سایت شرکتی + فروشگاه در یک قالب ایرانی",
        ],
        "specs": {
            "فروش": "۲۷ (جدید)",
            "رضایت": "۱۰۰٪",
            "حوزه": "شرکتی + فروشگاهی",
        },
    },
    {
        "slug": "quick",
        "title": "کوییک، قالب شرکتی وردپرس",
        "en_title": "Quick",
        "origin": "iranian",
        "category": "corporate",
        "category_label": "شرکتی",
        "sales": 18,
        "satisfaction": 50,
        "support": "A+",
        "price_toman": 1_150_000,
        "discount_percent": 0,
        "url": "https://www.rtl-theme.com/quick-wordpress-theme/",
        "thumbnail": "https://media.rtlcdn.com/2026/07/196db257249082a826338397d988d618ac68339bd5007a-590x300.jpg",
        "demos": "دموی شرکتی",
        "builder": "المنتور",
        "design_style": "شرکتی ساده و سریع (نام: Quick)",
        "highlights": [
            "ارزان‌ترین قیمت پایهٔ دسته بین قالب‌های بدون تخفیف (۱,۱۵۰,۰۰۰ تومان)",
            "تازه‌منتشرشده؛ ۱۸ فروش اولیه",
        ],
        "specs": {
            "فروش": "۱۸ (جدید)",
            "رضایت": "۵۰٪",
            "قیمت پایه": "ارزان‌ترین بدون تخفیف",
        },
    },
]

# ---------------------------------------------------------------------------
# روندهای طراحی و ویژگی‌های مشترک (تحلیل تجمیعی)
# ---------------------------------------------------------------------------
DESIGN_TRENDS = [
    {
        "title": "صفحه‌ساز بصری + ویجت‌های اختصاصی",
        "icon": "🧩",
        "description": (
            "تقریباً همهٔ قالب‌ها با المنتور ساخته شده‌اند و مزیت رقابتی‌شان «ویجت اختصاصی» است: "
            "ستیا ۳۰+، آرنیکا سفارشی‌سازی زنده، کرافتو ۱۰۰+ و نادر ۱۳۶ ویجت. دیوی بیلدر اختصاصی خودش را دارد."
        ),
    },
    {
        "title": "چنددمویی بودن + درون‌ریزی با یک کلیک",
        "icon": "🎭",
        "description": (
            "از ۳ دمو (ستیا) تا ۴۸ دمو و ۱۴۵۰ الگو (کرافتو). همه با «بسته نصبی آسان» عرضه می‌شوند تا "
            "کاربر بدون دانش فنی سایت را مثل دمو راه بیندازد."
        ),
    },
    {
        "title": "فونت فارسی به‌عنوان ویژگی فروش",
        "icon": "🔤",
        "description": (
            "انتخاب فونت متن و تیتر از پنل: آرنیکا (ایران‌یکان، پرستو، استعداد، شبنم)، نادر (۵ فونت پریمیوم "
            "با لایسنس)، کرافتو (۱۰۰+ فونت فارسی)."
        ),
    },
    {
        "title": "سرعت و Core Web Vitals",
        "icon": "⚡",
        "description": (
            "Critical CSS، مینی‌فای JS/CSS، لیزی‌لود، پیش‌بارگذاری هوشمند صفحهٔ بعد، کاهش ۵۰٪ کوئری دیتابیس، "
            "غیرفعال‌سازی ماژول‌های بلااستفاده — رضایت و سئو را مستقیم بالا می‌برد."
        ),
    },
    {
        "title": "تم تیره/روشن + رنگ‌بندی نامحدود",
        "icon": "🎨",
        "description": (
            "پنل تنظیمات (Redux یا Customizer) با انتخاب رنگ نامحدود، تم تیره/روشن و Preloaderهای طرح‌دار "
            "(۴ طرح در ستیا، ۱۰ طرح در نادر)."
        ),
    },
    {
        "title": "هدرساز / فوترساز / مگامنو",
        "icon": "🧱",
        "description": (
            "کرافتو: سازندهٔ هدر، فوتر، پست تکی، پاپ‌آپ، آرشیو و ۴۰۴. نادر: هدر/فوتر اختصاصی هر صفحه + "
            "مگامنوی ۵ استایل. دیوی: Theme Builder سراسری."
        ),
    },
    {
        "title": "اعتمادسازهای شرکتی",
        "icon": "🤝",
        "description": (
            "بخش تیم با نوار مهارت خطی/دایره‌ای، نمونه‌کار فیلتردار، جداول قیمت و تعرفه، نظرات مشتریان، "
            "لوگوی بردها و شمارندهٔ آمار — ساختار ثابت همهٔ دموهای شرکتی."
        ),
    },
    {
        "title": "تعامل پیشرفته با کاربر",
        "icon": "💬",
        "description": (
            "ورود/عضویت پیامکی OTP با ۷ اپراتور (نادر)، تیکت پشتیبانی با پیوست فایل، استوری‌ساز اینستاگرامی، "
            "اطلاعیه‌های پنل کاربری با تاریخ شمسی و گزارش لحظه‌ای به تلگرام/بله."
        ),
    },
    {
        "title": "فروشگاه حرفه‌ای روی سایت شرکتی",
        "icon": "🛒",
        "description": (
            "ترکیب شرکتی+ووکامرس در نادر، آروین و بی‌تم: کارت محصول چندطرح، فیلتر ایجکسی سئو-محور، "
            "Variation Swatches (رنگ/تصویر/دکمه)، مقایسه، علاقه‌مندی و سبد خرید مشابه دیجی‌کالا."
        ),
    },
    {
        "title": "هوش مصنوعی؛ موج جدید ۱۴۰۴ به بعد",
        "icon": "🤖",
        "description": (
            "کرافتو: تولید مقاله، تصویر و محتوای سئو با AI + چت‌بات یکپارچه. روند صعودی بازار قالب ایرانی "
            "به سمت ابزارهای مولد است."
        ),
    },
    {
        "title": "دوزبانه و آمادهٔ صادرات دیجیتال",
        "icon": "🌍",
        "description": (
            "پشتیبانی ذاتی Polylang/WPML؛ نادر هر ۱۸ دمو را به‌صورت پیش‌فرض دوزبانه ارائه می‌دهد و "
            "آرنیکا به‌سادگی چپ‌چین (LTR) می‌شود."
        ),
    },
    {
        "title": "نقشه بدون تحریم",
        "icon": "🗺️",
        "description": (
            "استفاده از OpenStreetMap به‌جای Google Maps در صفحهٔ تماس (آرنیکا) برای رفع مشکل API و تحریم — "
            "الگوی استاندارد قالب‌های ایرانی."
        ),
    },
]

# ---------------------------------------------------------------------------
# جدول امکانات قالب‌ها ↔ وضعیت همین CMS (تحلیل شکاف)
# ---------------------------------------------------------------------------
# status: have | partial | missing
FEATURE_MATRIX = [
    # --- محتوا و صفحات ---
    {"group": "محتوا و صفحات", "feature": "صفحه‌ساز کامپوننتی (hero، اسلایدر، تیم، FAQ، نظرات، گالری، CTA، خبرنامه…)", "in_themes": "✅ همهٔ قالب‌ها (المنتور)", "status": "have", "status_label": "موجود", "note": "مدل PageComponent با ~۲۰ نوع کامپوننت", "suggestion": "افزودن پیش‌نمایش زنده و مرتب‌سازی درگ‌انددراپ در پنل"},
    {"group": "محتوا و صفحات", "feature": "صفحه‌ساز بصری درگ‌انددراپ کامل (سطح المنتور)", "in_themes": "✅ ۱۶ از ۱۸ قالب", "status": "partial", "status_label": "ناقص", "note": "کامپوننت‌ها (PageComponent ~۲۰ نوع) + سواچ/فیلتر/استوری اضافه شد؛ ویرایشگر drag&drop کامل نیست", "suggestion": "گام بعدی: ویرایشگر بصری صفحات در پنل مدیریت"},
    {"group": "محتوا و صفحات", "feature": "دموهای آمادهٔ چندگانه + درون‌ریزی با یک کلیک", "in_themes": "✅ ۳ تا ۴۸ دمو در هر قالب", "status": "have", "status_label": "موجود", "note": "دستور `flask seed-demo corporate|shop` — بستهٔ نصبی تیم/تعرفه/استوری/سواچ/ویدئو/نقشه", "suggestion": "ساخت چیدمان‌های بیشتر (آژانسی/شخصی)"},
    {"group": "محتوا و صفحات", "feature": "سازندهٔ هدر/فوتر + مگامنو", "in_themes": "✅ نادر، کرافتو، دیوی، آرنیکا", "status": "partial", "status_label": "ناقص", "note": "مگامنو در مدل منو موجود (is_mega_menu + config)؛ هدرساز بصری نیست", "suggestion": "فرم پیکربندی بصری مگامنو و چند طرح هدر/فوتر قابل انتخاب"},
    {"group": "محتوا و صفحات", "feature": "وبلاگ + نظرات", "in_themes": "✅ همه", "status": "have", "status_label": "موجود", "note": "بلاوپرینت blog + Comment", "suggestion": "چیدمان‌های چندگانهٔ بلاگ (گرید/لیست/ماسونری)"},
    {"group": "محتوا و صفحات", "feature": "نمونه‌کارها (پورتفولیو) با فیلتر", "in_themes": "✅ آرنیکا (گالری)، نادر (۶ طرح + فیلتر ایجکسی)", "status": "have", "status_label": "موجود", "note": "مدل PortfolioCaseStudies موجود است", "suggestion": "فیلتر ایجکسی دسته‌بندی + چند طرح کارت"},
    {"group": "محتوا و صفحات", "feature": "صفحهٔ تیم + نوار مهارت خطی/دایره‌ای", "in_themes": "✅ آرنیکا، ستیا، نادر", "status": "have", "status_label": "موجود", "note": "مدل TeamMember با CRUD کامل + بخش تیم در خانه/درباره ما + نوار مهارت", "suggestion": "نمایش دایره‌ای مهارت‌ها"},
    {"group": "محتوا و صفحات", "feature": "جدول قیمت / تعرفهٔ خدمات", "in_themes": "✅ آرنیکا (جداول تعرفه)", "status": "have", "status_label": "موجود", "note": "مدل PricingPlan + CRUD + بخش تعرفه در صفحهٔ اصلی با طرح ویژه", "suggestion": "کامپوننت صفحه (PageComponent) مستقل"},
    {"group": "محتوا و صفحات", "feature": "اسلایدر و بنر", "in_themes": "✅ همه (اسلایدر قوی از معیارهای انتخاب)", "status": "have", "status_label": "موجود", "note": "Slider/SliderItem + Banner", "suggestion": "افزودن انیمیشن‌ها و اسلایدر ویدئویی/فول‌اسکرین"},
    # --- فروشگاه ---
    {"group": "فروشگاه", "feature": "فروشگاه کامل (سبد، سفارش، پرداخت)", "in_themes": "✅ نادر، آروین، بی‌تم، فلوکس، اکسترا", "status": "have", "status_label": "موجود", "note": "Order/CartItem/...", "suggestion": "درگاه‌های بیشتر + پرداخت اقساطی (اسنپ‌پی)"},
    {"group": "فروشگاه", "feature": "مقایسه و علاقه‌مندی (Wishlist)", "in_themes": "✅ نادر (هر دو ایجکسی)", "status": "have", "status_label": "موجود", "note": "مدل‌های Comparison + Wishlist", "suggestion": "—"},
    {"group": "فروشگاه", "feature": "فیلتر ایجکسی محصولات (سئو-محور)", "in_themes": "✅ نادر، کرافتو", "status": "have", "status_label": "موجود", "note": "API /api/products/filter + نوار فیلتر قیمت/موجودی/تخفیف/مرتب‌سازی + تاریخچهٔ URL", "suggestion": "فیلتر برند و ویژگی‌های داینامیک"},
    {"group": "فروشگاه", "feature": "Variation Swatches (رنگ/تصویر/دکمه)", "in_themes": "✅ نادر (۴ نوع)", "status": "have", "status_label": "موجود", "note": "سواچ رنگ/تصویر/دکمه روی صفحه محصول + ورود متغیر به سبد خرید + فیلتر از API", "suggestion": "سواچ روی کارت محصول در لیست‌ها"},
    {"group": "فروشگاه", "feature": "گالری ویدئو محصول (آپارات/یوتیوب)", "in_themes": "✅ نادر (نامحدود + آپارات)", "status": "have", "status_label": "موجود", "note": "مدل ProductVideo + تبدیل خودکار embed آپارات/یوتیوب + مودال پخش", "suggestion": "آپلود مستقیم ویدئو"},
    {"group": "فروشگاه", "feature": "رهگیری سفارش توسط مشتری", "in_themes": "✅ نادر (ایجکسی)", "status": "have", "status_label": "موجود", "note": "tracking_code روی Order + صفحه پیگیری", "suggestion": "نمایش مرحله‌به‌مرحلهٔ وضعیت (progress bar)"},
    {"group": "فروشگاه", "feature": "فاکتور و لیبل چاپی سفارش", "in_themes": "✅ نادر (فاکتورساز/لیبل‌ساز)", "status": "have", "status_label": "موجود", "note": "صفحات /admin/orders/<id>/invoice و /label با استایل چاپ A4 و 10×15", "suggestion": "ارسال خودکار فاکتور با ایمیل"},
    # --- کاربر و تعامل ---
    {"group": "کاربر و تعامل", "feature": "حساب کاربری + پنل کاربر", "in_themes": "✅ نادر، ستیا", "status": "have", "status_label": "موجود", "note": "blueprint user + Notification", "suggestion": "داشبورد کاربر قابل شخصی‌سازی"},
    {"group": "کاربر و تعامل", "feature": "ورود/عضویت با موبایل (OTP پیامکی)", "in_themes": "✅ نادر (۷ اپراتور پیامکی)", "status": "have", "status_label": "موجود", "note": "/user/otp-login با ۴ درایور پیامکی (kavenegar/mellipayamak/smsir/console) + ضد بمباران", "suggestion": "تنظیم SMS_DRIVER در .env برای فعال‌سازی ارسال واقعی"},
    {"group": "کاربر و تعامل", "feature": "سیستم تیکت پشتیبانی", "in_themes": "✅ نادر (اختصاصی + پیوست فایل)", "status": "have", "status_label": "موجود", "note": "تیکت ردوبدل + دپارتمان/اولویت/وضعیت + اطلاع‌رسانی (user + admin)", "suggestion": "پیوست فایل در پیام‌ها"},
    {"group": "کاربر و تعامل", "feature": "اطلاعیه/اخبار پنل کاربری (تاریخ شمسی)", "in_themes": "✅ نادر، ستیا", "status": "have", "status_label": "موجود", "note": "مدل Notification موجود", "suggestion": "نمایش تاریخ شمسی و اعلان خوانده‌نشده در هدر"},
    {"group": "کاربر و تعامل", "feature": "فرم تماس / درخواست مشاوره", "in_themes": "✅ همه (Contact Form 7)", "status": "have", "status_label": "موجود", "note": "Contact + ConsultationLeads", "suggestion": "فرم‌ساز عمومی (مثل فرم تماس 7)"},
    {"group": "کاربر و تعامل", "feature": "نقشه در صفحهٔ تماس (OpenStreetMap)", "in_themes": "✅ آرنیکا (بدون تحریم)", "status": "have", "status_label": "موجود", "note": "iframe نقشهٔ OSM قابل تنظیم از پنل (گروه تماس) — بدون تحریم و API", "suggestion": "نقشهٔ تعاملی با Pin سفارشی"},
    {"group": "کاربر و تعامل", "feature": "استوری‌ساز (نوار استوری اینستاگرامی)", "in_themes": "✅ نادر (عکس/ویدئو/دسته‌بندی)", "status": "have", "status_label": "موجود", "note": "نوار استوری + ویوئر تمام‌صفحه با تایمر، ویدئو، ثبت بازدید و CTA", "suggestion": "استوری از پست‌ها/محصولات به‌صورت خودکار"},
    {"group": "کاربر و تعامل", "feature": "خبرنامه", "in_themes": "✅ کرافتو (MailChimp)", "status": "have", "status_label": "موجود", "note": "فرم عضویت در فوتر + مدل Subscriber + خروجی CSV در پنل", "suggestion": "ارسال گروهی ایمیل خبرنامه"},
    # --- ظاهر و شخصی‌سازی ---
    {"group": "ظاهر و شخصی‌سازی", "feature": "تم تیره/روشن قابل سوییچ", "in_themes": "✅ نادر، کرافتو", "status": "have", "status_label": "موجود", "note": "توکن‌های CSS تم روشن + دکمهٔ سوییچ شناور + ذخیره در localStorage", "suggestion": "تم روشن پیش‌فرض برای برخی صفحات"},
    {"group": "ظاهر و شخصی‌سازی", "feature": "انتخاب فونت/رنگ از پنل (رنگ نامحدود)", "in_themes": "✅ همه (Redux/Customizer)", "status": "have", "status_label": "موجود", "note": "تنظیمات ظاهر: رنگ تأکید + فونت متن/تیتر — تزریق CSS خودکار", "suggestion": "پیش‌نمایش زنده هنگام انتخاب"},
    {"group": "ظاهر و شخصی‌سازی", "feature": "Preloaderهای چندطرح", "in_themes": "✅ ستیا (۴ طرح)، نادر (۱۰ طرح)", "status": "have", "status_label": "موجود", "note": "۳ طرح (spinner/pulse/bar) + فعال‌سازی و انتخاب طرح از تنظیمات", "suggestion": "—"},
    {"group": "ظاهر و شخصی‌سازی", "feature": "جستجوی ایجکسی", "in_themes": "✅ نادر (کش نتایج + انتخاب پست‌تایپ)", "status": "have", "status_label": "موجود", "note": "API /api/search موجود", "suggestion": "کش نتایج + جستجو در صفحات و نمونه‌کارها هم"},
    {"group": "ظاهر و شخصی‌سازی", "feature": "چندزبانه (فارسی/انگلیسی)", "in_themes": "✅ همه (Polylang/WPML)", "status": "missing", "status_label": "ندارد", "note": "زیرساخت Babel هست ولی محتوا تک‌زبانه است", "suggestion": "فیلد ترجمه روی محتوا + URL پوشه‌ای /en/"},
    # --- عملکرد و عملیات ---
    {"group": "عملکرد و عملیات", "feature": "سئو (متا، OG، JSON-LD، sitemap)", "in_themes": "✅ همه + سازگاری RankMath/Yoast", "status": "have", "status_label": "موجود", "note": "سرویس SEO + Person/Product schema", "suggestion": "ریچ‌اسنیپت نظرات و قیمت"},
    {"group": "عملکرد و عملیات", "feature": "سرعت (کش، لیزی‌لود، فشرده‌سازی)", "in_themes": "✅ همه؛ کرافتو: Critical CSS + Prefetch", "status": "have", "status_label": "موجود", "note": "Flask-Caching + Compress + لیزی‌لود", "suggestion": "Critical CSS و preload فونت‌ها"},
    {"group": "عملکرد و عملیات", "feature": "امنیت (CSRF، Rate limit، لاگ)", "in_themes": "✅ نادر (امنیت چندلایه)", "status": "have", "status_label": "موجود", "note": "CSRF + rate limiting + Log", "suggestion": "۲FA برای پنل مدیریت"},
    {"group": "عملکرد و عملیات", "feature": "گزارش لحظه‌ای به تلگرام", "in_themes": "✅ نادر (تلگرام و بله با پروکسی)", "status": "have", "status_label": "موجود", "note": "سرویس تلگرام پیاده شده", "suggestion": "افزودن ایتا/بله"},
    {"group": "عملکرد و عملیات", "feature": "تولید محتوا با هوش مصنوعی", "in_themes": "✅ کرافتو (متن/تصویر/چت‌بات)", "status": "partial", "status_label": "زیرساخت آماده", "note": "سرویس AI سازگار با OpenAI/OpenRouter/Groq + دکمهٔ «پیش‌نویس با AI» در فرم محصول", "suggestion": "تنظیم AI_API_KEY در .env برای فعال‌سازی؛ افزودن به فرم مقاله"},
]

# ---------------------------------------------------------------------------
# خدمات و ضمانت‌های مارکت راست‌چین (الگوی فروش)
# ---------------------------------------------------------------------------
MARKETPLACE_NOTES = [
    "ضمانت بازگشت وجه ۶ ماهه برای همهٔ محصولات",
    "۶ ماه پشتیبانی رایگان + درجه‌بندی پشتیبانی (A+، B+ و…)",
    "بروزرسانی خودکار و مادام‌العمر (لایسنس مادام‌العمر)",
    "بستهٔ نصب آسان + فایل راهنما + آموزش ویدیویی",
    "خرید اقساطی با اسنپ‌پی (۴ قسط بدون کارمزد)",
    "اشتراک Pro با تخفیف ۳۰۰ تا ۶۰۰ هزار تومانی روی قالب‌ها",
    "هدیهٔ تتر (همتاپی) برای سبد خرید بالای ۱ میلیون تومان",
    "نمایش شفاف فروش، درصد رضایت و درجهٔ پشتیبانی هر قالب",
]

# معیارهای انتخاب قالب شرکتی (از خود صفحهٔ دسته‌بندی)
SELECTION_CRITERIA = [
    {"title": "واکنش‌گرایی کامل", "description": "نمایش درست در همهٔ دستگاه‌ها و سایزها"},
    {"title": "سازگاری با صفحه‌ساز", "description": "المنتور یا ویژوال‌کامپوزر برای سفارشی‌سازی بدون کد"},
    {"title": "سازگاری با افزونه‌ها", "description": "رنک‌مث (سئو)، WP Rocket (سرعت) و…"},
    {"title": "سرعت بالا", "description": "کاربر منتظر سایت کند نمی‌ماند؛ سرعت روی سئو اثر مستقیم دارد"},
    {"title": "صفحات آماده", "description": "درباره ما، تماس، خدمات، وبلاگ، قیمت و نمونه‌کار از پیش موجود"},
    {"title": "کاملاً فارسی و سئوفرندلی", "description": "RTL بومی، فونت فارسی و ساختار سئوی استاندارد"},
]

# ساختار ثابت صفحهٔ اصلی قالب‌های شرکتی (الگوی بخش‌ها)
CORPORATE_PAGE_BLUEPRINT = [
    "اسلایدر اصلی (معرفی خدمات/محصول مهم)",
    "معرفی کوتاه شرکت + دکمهٔ CTA",
    "خدمات (کارت‌های آیکون‌دار)",
    "درباره ما + شمارندهٔ آمار (پروژه‌ها، مشتریان، سال تجربه)",
    "نمونه‌کارها با فیلتر",
    "تیم ما + مهارت‌ها",
    "جداول قیمت/تعرفه",
    "نظرات مشتریان (تستیمونیال)",
    "لوگوی بردها/مشتریان",
    "وبلاگ (آخرین مقالات)",
    "فرم تماس + نقشه",
    "خبرنامه و شبکه‌های اجتماعی در فوتر",
]


def theme_research_summary():
    """محاسبهٔ آمار تجمیعی برای نمایش در بالای صفحه."""
    prices = [t["price_toman"] for t in THEMES]
    best_seller = max(THEMES, key=lambda t: t["sales"])
    top_satisfaction = max(THEMES, key=lambda t: t["satisfaction"])
    most_expensive = max(THEMES, key=lambda t: t["price_toman"])
    cheapest = min(THEMES, key=lambda t: t["price_toman"])
    iranian_count = sum(1 for t in THEMES if t["origin"] == "iranian")
    avg_satisfaction = round(sum(t["satisfaction"] for t in THEMES) / len(THEMES))
    feature_status = {
        "have": sum(1 for f in FEATURE_MATRIX if f["status"] == "have"),
        "partial": sum(1 for f in FEATURE_MATRIX if f["status"] == "partial"),
        "missing": sum(1 for f in FEATURE_MATRIX if f["status"] == "missing"),
    }
    return {
        "total_themes": len(THEMES),
        "iranian_count": iranian_count,
        "international_count": len(THEMES) - iranian_count,
        "avg_price": sum(prices) // len(prices),
        "min_price": min(prices),
        "max_price": max(prices),
        "avg_satisfaction": avg_satisfaction,
        "best_seller": best_seller,
        "top_satisfaction": top_satisfaction,
        "most_expensive": most_expensive,
        "cheapest": cheapest,
        "feature_status": feature_status,
    }
