"""
Celery Application Factory

نمونهٔ Celery به‌صورت lazy به Flask app وصل می‌شود ( الگوی کارخانهٔ برنامه ):

- در پروسهٔ وب: ``create_app`` صدا زدن ``init_celery(app)`` باعث می‌شود
  broker/result-backend از تنظیمات Flask خوانده شوند و تسک‌های eager/inline
  در صورت غیرفعال بودن Celery بدون broker اجرا شوند.
- در ورکر: ``worker.py`` اپ را می‌سازد و همین تابع را صدا می‌زند؛ بدنهٔ هر تسک
  داخل یک ``app_context`` اجرا می‌شود (:class:`ContextTask`) تا ``db`` و
  ``current_app`` در دسترس باشند.

صف‌ها:
    default        → کارهای فروشگاه و زمان‌بندی‌شده (beat)
    mail           → ایمیل‌های تراکنشی
    notifications  → تلگرام/اعلان‌های بیرونی (شبکه‌ای، کند و قابل‌ریتری)
"""
from __future__ import annotations

import logging
from typing import Any, Callable

from celery import Celery
from celery.schedules import crontab
from celery.result import AsyncResult

_log = logging.getLogger(__name__)

#: نام برنامه برای CLI ها (celery -A worker.celery ...)
APP_NAME = 'flask_pro'

#: فلش‌اپلیکیشن جاری در پروسهٔ ورکر (توسط init_celery پر می‌شود).
_flask_app: Any = None


# ==================== Celery instance (config-independent) ====================

celery = Celery(APP_NAME)

celery.conf.update(
    # سریالایزشن — فقط JSON، هیچ pickle‌ای روی broker ردوبدل نمی‌شود (امنیت)
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    # منطقهٔ زمانی برنامه‌ریز — شمسی تهران طبق استاندارد پروژه
    timezone='Asia/Tehran',
    enable_utc=True,
    # رفتار حرفه‌ای ورکر
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_send_task_events=True,
    task_send_sent_event=True,
    # نتیجهٔ تسک‌ها یک روز در backend می‌ماند
    result_expires=60 * 60 * 24,
    broker_transport_options={'visibility_timeout': 3600},
    # محدودیت زمانی پیش‌فرض هر تسک (ثانیه) — در init_celery از config بازنویسی می‌شود
    task_time_limit=300,
    task_soft_time_limit=270,
    # ==================== Queue routing ====================
    task_default_queue='default',
    task_routes={
        'flaskpro.mail.*': {'queue': 'mail'},
        'flaskpro.notify.*': {'queue': 'notifications'},
        'flaskpro.orders.*': {'queue': 'default'},
    },
    # ==================== Beat schedule ====================
    # این زمان‌بندی فقط توسط پروسهٔ `celery beat` مصرف می‌شود.
    beat_schedule={
        'expire-unpaid-orders': {
            'task': 'flaskpro.orders.expire_unpaid',
            'schedule': 600.0,  # هر ۱۰ دقیقه
            'options': {'expires': 540},
        },
        'cleanup-stale-guest-carts': {
            'task': 'flaskpro.orders.cleanup_stale_carts',
            'schedule': crontab(hour=3, minute=15),  # هر شب ۰۳:۱۵ تهران
            'options': {'expires': 3600},
        },
    },
)


# ==================== Flask-context task base ====================

class ContextTask(celery.Task):
    """پایهٔ تسک‌ها: اجرای بدنه داخل app context فلاسک.

    بدون این کلاس، هر تسکی که به ``db`` یا ``current_app`` نیاز دارد در ورکر
    با RuntimeError خارج از context مواجه می‌شد.
    """

    abstract = True

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        if _flask_app is None:
            # ورکر باید از طریق worker.py بالا بیاید؛ در غیر این صورت context نیست.
            raise RuntimeError(
                'Celery task executed without a bound Flask app — '
                'start the worker via `celery -A worker.celery ...` from the repo root.'
            )
        with _flask_app.app_context():
            try:
                return self.run(*args, **kwargs)
            finally:
                # آزاد کردن اتصال‌های session بین دورهای تسک (جلوگیری از استخر نشتی)
                try:
                    from app.extensions import db
                    db.session.remove()
                except Exception:  # pragma: no cover - defensive
                    pass


celery.Task = ContextTask


# ==================== Public helpers ====================

def init_celery(app: Any) -> Celery:
    """اتصال نمونهٔ Celery به کانفیگ یک Flask app مشخص.

    Idempotent است؛ در create_app یک‌بار صدا زده می‌شود و ``worker.py`` نیز
    پس از ساخت اپ همان را صدا می‌زند.

    Args:
        app: نمونهٔ Flask app ساخته‌شده توسط ``create_app``.

    Returns:
        نمونهٔ جهانی Celery.
    """
    global _flask_app
    _flask_app = app

    celery.conf.update(
        broker_url=app.config.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
        result_backend=app.config.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
        timezone=app.config.get('CELERY_TIMEZONE', 'Asia/Tehran'),
        task_time_limit=int(app.config.get('CELERY_TASK_TIME_LIMIT', 300)),
        task_soft_time_limit=int(app.config.get('CELERY_TASK_SOFT_TIME_LIMIT', 270)),
        result_expires=int(app.config.get('CELERY_RESULT_EXPIRES', 60 * 60 * 24)),
    )
    return celery


def get_flask_app() -> Any:
    """برگرداندن Flask app متصل‌شده به ورکر (یا None)."""
    return _flask_app


def celery_enabled() -> bool:
    """آیا صف‌گذاری غیرهمگام در این پروسه فعال است؟

    از ``current_app.config['CELERY_ENABLED']`` می‌خواند؛ خارج از request/app
    context (مثلاً در CLI) مقدار روی ``_flask_app`` ذخیره‌شده را بررسی می‌کند.
    """
    try:
        from flask import current_app
        return bool(current_app.config.get('CELERY_ENABLED', False))
    except RuntimeError:
        if _flask_app is not None:
            return bool(_flask_app.config.get('CELERY_ENABLED', False))
        return False


def enqueue(task: Any, *args: Any, **kwargs: Any) -> Any:
    """اجرای یک تسک — غیرهمگام اگر Celery فعال است، وگرنه همگام و درجا.

    این تنها راه صدا زدن تسک‌ها از لایهٔ سرویس/روت است تا رفتار برنامه به
    در دسترس بودن broker وابسته نماند (fail-safe برای توسعه، تست و قطعی Redis).

    Args:
        task: شیء تسک سلری (تزئین‌شده با ``@celery.task``).
        *args/**kwargs: آرگومان‌های تسک. ترجیحاً فقط شناسه (id) پاس داده شود،
            نه شیء ORM — تسک خودش را با latest data از دیتابیس می‌خواند.

    Returns:
        در حالت همگام: مقدار بازگشتی بدنهٔ تسک.
        در حالت غیرهمگام: ``AsyncResult``.
    """
    if celery_enabled():
        result: AsyncResult = task.delay(*args, **kwargs)
        return result
    # Fallback همگام: بدنهٔ خام تسک بدون موتور retry/serializer اجرا می‌شود.
    run_fn: Callable[..., Any] = getattr(task, 'run', None) or task
    return run_fn(*args, **kwargs)
