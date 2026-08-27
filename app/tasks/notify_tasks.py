"""
Notification Tasks — کانال‌های بیرونی (تلگرام) و اعلان داخلی ادمین‌ها

هرچه شبکه‌ای است (تلگرام و…) باید از request path بیرون برود. این تسک‌ها با
autoretry + exponential backoff اجرا می‌شوند تا نوسان شبکهٔ داخلی/خارجی و
rate-limit تلگرام، ثبت سفارش کاربر را خراب نکند.
"""
from __future__ import annotations

import logging
import socket
from typing import Any, Dict, Optional

from app.tasks.celery_app import celery

logger = logging.getLogger(__name__)

RETRYABLE = (OSError, socket.timeout, ConnectionError, TimeoutError)


def _telegram_available() -> bool:
    """آیا ربات تلگرام در این محیط کانفیگ شده است؟"""
    from flask import current_app
    return bool(
        current_app.config.get('TELEGRAM_BOT_TOKEN')
        and current_app.config.get('TELEGRAM_ADMIN_CHAT_ID')
    )


@celery.task(
    name='flaskpro.notify.telegram_send',
    autoretry_for=RETRYABLE,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3,
)
def telegram_send_task(message: str, chat_id: Optional[str] = None) -> bool:
    """ارسال یک پیام خام به ربات تلگرام (استفادهٔ عمومی/ادمین)."""
    if not _telegram_available():
        return False
    from app.services.notification_service import NotificationService

    ok = NotificationService.notify_telegram(message, chat_id=chat_id)
    if not ok:
        raise RuntimeError('Telegram sendMessage returned non-200')
    return True


@celery.task(
    name='flaskpro.notify.telegram_order_new',
    autoretry_for=RETRYABLE,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3,
)
def telegram_order_new_task(order_id: int) -> bool:
    """اطلاع‌رسانی سفارش تازه به ادمین‌ها در تلگرام (سفارش را از DB تازه می‌خواند)."""
    if not _telegram_available():
        return False

    from app.extensions import db
    from app.models import Order
    from app.services.notification_service import NotificationService

    order: Optional[Order] = db.session.get(Order, order_id)
    if order is None or order.is_deleted:
        logger.warning('Order %s vanished before telegram notify', order_id)
        return False

    ok = NotificationService.notify_telegram_order_new(order)
    if not ok:
        raise RuntimeError(f'Telegram notify failed for order {order_id}')
    return True


@celery.task(
    name='flaskpro.notify.telegram_contact_new',
    autoretry_for=RETRYABLE,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3,
)
def telegram_contact_task(contact_id: int) -> bool:
    """اطلاع‌رسانی پیام جدید «تماس با ما» به ادمین‌ها در تلگرام."""
    if not _telegram_available():
        return False

    from app.extensions import db
    from app.models import Contact
    from app.services.notification_service import NotificationService

    contact: Optional[Contact] = db.session.get(Contact, contact_id)
    if contact is None:
        logger.warning('Contact %s vanished before telegram notify', contact_id)
        return False

    ok = NotificationService.notify_telegram_contact(contact)
    if not ok:
        raise RuntimeError(f'Telegram notify failed for contact {contact_id}')
    return True


@celery.task(name='flaskpro.notify.admins_inapp')
def admins_notification_task(
    title: str,
    message: str,
    notif_type: str = 'info',
    data: Optional[Dict[str, Any]] = None,
) -> int:
    """درج اعلان داخلی برای همهٔ ادمین‌ها (write به جدول notifications).

    این کار محلی و سریع است؛ تسک فقط برای بیرون بردن نوشتن از مسیر request
    ساخته شده و retry شبکه‌ای لازم ندارد.
    """
    from app.services.notification_service import NotificationService

    notifications = NotificationService.notify_admins(
        title=title, message=message, type=notif_type, data=data
    )
    return len(notifications)
