"""
Background Tasks Package (Celery)

اعلان‌ها، ایمیل‌ها و کارهای زمان‌بندی‌شدهٔ فروشگاه از طریق Celery اجرا می‌شوند.
الایهٔ سرویس (``app/services``) همیشه از طریق :func:`enqueue` تسک را صدا می‌زند:

- اگر ``CELERY_ENABLED`` روشن باشد → تسک روی broker صف می‌شود (غیرهمگام).
- اگر خاموش باشد (توسعهٔ بدون Redis، تست، یا broker قطع) → تابع بدنهٔ تسک
  به‌صورت همگام و در همین پروسه اجرا می‌شود. یعنی هیچ قابلیت از کار نمی‌افتد،
  فقط synchronous اجرا می‌شود.

این ماژول عمداً هیچ تسکی را در سطح ماژول import نمی‌کند تا از چرخهٔ
import (tasks → services → tasks) جلوگیری شود؛ فایل‌های تسک مستقیماً
(مثلاً ``from app.tasks.order_tasks import expire_unpaid_orders``) ایمپورت می‌شوند
و ``worker.py`` هم آن‌ها را برای ثبت در رجیستری وارد می‌کند.
"""
from app.tasks.celery_app import (
    celery,
    init_celery,
    enqueue,
    celery_enabled,
    get_flask_app,
)

__all__ = [
    'celery',
    'init_celery',
    'enqueue',
    'celery_enabled',
    'get_flask_app',
]
