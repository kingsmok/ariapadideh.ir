#!/usr/bin/env python
"""
Celery Entry Point — worker و beat از همین فایل بالا می‌آیند.

    # ورکر (هر سه صف):
    celery -A worker.celery worker -l INFO --queues=default,mail,notifications

    # فقط صف ایمیل روی ماشین جدا:
    celery -A worker.celery worker -l INFO -Q mail

    # زمان‌بند (beat) — فقط یک نمونه در کل کلاستر:
    celery -A worker.celery beat -l INFO

فایل عمداً سبک است: اپ فلاسک ساخته می‌شود (که init_celery را صدا می‌زند)،
ماژول‌های تسک ایمپورت می‌شوند تا در رجیستری ثبت شوند، و نماد ``celery``
در سطح ماژول در اختیار ``-A worker.celery`` قرار می‌گیرد.
"""
import os
import sys

# اطمینان از در دسترس بودن ریشهٔ مخزن برای import برنامه (اجرا از هر مسیری)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app  # noqa: E402

# ماژول‌های تسک — ایمپورت‌شان یعنی «ثبت در رجیستری سلری»
from app.tasks import order_tasks, mail_tasks, notify_tasks  # noqa: E402,F401
from app.tasks.celery_app import celery  # noqa: E402

env = os.getenv('FLASK_ENV', 'development')
flask_app = create_app(env)  # داخلش init_celery(app) اجرا می‌شود

if __name__ == '__main__':
    # تسهیل اجرای مستقیم: `python worker.py worker -l INFO`
    celery.start()
