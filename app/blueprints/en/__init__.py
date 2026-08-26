"""
English Blueprint — نسخهٔ انگلیسی سایت زیر /en/

الگوی چندزبانهٔ قالب‌های راست‌چین: URL پوشه‌ای (/en/) + کروم انگلیسی
(LTR) برای صفحات اصلی. محتوای دیتابیسی (محصولات) با عنوان اصلی
نمایش داده می‌شود؛ مقالات اگر نسخهٔ انگلیسی داشته باشند همان نمایش
داده می‌شود وگرنه نسخهٔ فارسی با نکتهٔ «original version».
"""
from flask import Blueprint, g

en_bp = Blueprint('en', __name__, url_prefix='/en')


@en_bp.before_request
def _set_lang():
    g.lang = 'en'


from app.blueprints.en import routes  # noqa: E402,F401
