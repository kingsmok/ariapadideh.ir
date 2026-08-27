"""
Email Tasks — ارسال ایمیل‌های تراکنشی از طریق Celery

ایمیل‌ها کُند و شبکه‌ای‌اند؛ هرگز نباید در چرخهٔ درخواست کاربر بلوکه شوند.
الگوی retry: خطای واقعی ارسال (SMTP/شبکه) باعث backoff-retry می‌شود، ولی
«ایمیل کانفیگ نشده» یا «گیرنده بی‌ایمیل» خطا نیست و بی‌محو رد می‌شود.

توجه: بدنهٔ این تسک‌ها از بیرون request context هم اجرا می‌شود؛ به همین دلیل
همه‌چیز از روی شناسه (``order_id`` و…) و با کوئری تازه در DB ساخته می‌شود.
"""
from __future__ import annotations

import logging
import socket
import smtplib
from typing import Optional

from app.tasks.celery_app import celery

logger = logging.getLogger(__name__)

#: استثناهایی که ارزش تلاش مجدد دارند (خطاهای موقت شبکه/سرور ایمیل)
RETRYABLE = (
    smtplib.SMTPException,
    smtplib.SMTPServerDisconnected,
    smtplib.SMTPConnectError,
    socket.timeout,
    OSError,
)


def _mail_available() -> bool:
    """آیا SMTP در این محیط کانفیگ شده است؟

    ``EmailService.send`` بدون MAIL_server مقدار False برمی‌گرداند که «خطا» نیست؛
    با این helper از صف‌ کردن بلااستفاده و retry بی‌پایان جلوگیری می‌کنیم.
    """
    from flask import current_app
    return bool(current_app.config.get('MAIL_SERVER'))


@celery.task(
    name='flaskpro.mail.send_order_confirmation',
    autoretry_for=RETRYABLE,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3,
)
def send_order_confirmation_email(order_id: int) -> bool:
    """ارسال ایمیل تأیید سفارش (پس از پرداخت موفق).

    Args:
        order_id: شناسهٔ سفارش؛ سفارش حذف‌شده/ناموجود بی‌محو رد می‌شود.
    """
    if not _mail_available():
        logger.info('MAIL_SERVER not configured; skip order confirmation email #%s', order_id)
        return False

    from app.extensions import db
    from app.models import Order
    from app.services.email_service import EmailService

    order: Optional[Order] = db.session.get(Order, order_id)
    if order is None or order.is_deleted:
        logger.warning('Order %s vanished before confirmation email', order_id)
        return False

    ok = EmailService.send_order_confirmation(order)
    if not ok:
        # send() خطای شبکه را می‌بلعد و False می‌دهد؛ با raise فعال‌سازی retry می‌شود
        raise RuntimeError(f'EmailService failed for order {order_id}')
    return True


@celery.task(
    name='flaskpro.mail.send_password_reset',
    autoretry_for=RETRYABLE,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3,
)
def send_password_reset_email(user_id: int, reset_url: str) -> bool:
    """ارسال ایمیل بازیابی رمز عبور.

    توکن در همان لحظهٔ درخواست ساخته و به URL گنجانده شده است؛ تسک فقط حمل
    کنندهٔ ایمیل است و خودش توکن نمی‌سازد.
    """
    if not _mail_available():
        logger.info('MAIL_SERVER not configured; skip password reset email for user #%s', user_id)
        return False

    from app.extensions import db
    from app.models import User
    from app.services.email_service import EmailService

    user: Optional[User] = db.session.get(User, user_id)
    if user is None or not user.email or user.is_deleted:
        logger.warning('Password reset email skipped — user %s missing/email-less', user_id)
        return False

    ok = EmailService.send_password_reset(user, reset_url)
    if not ok:
        raise RuntimeError(f'EmailService failed for password reset user {user_id}')
    return True


@celery.task(
    name='flaskpro.mail.send_contact_reply',
    autoretry_for=RETRYABLE,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3,
)
def send_contact_reply_email(contact_id: int, reply_text: str) -> bool:
    """ارسال پاسخ ادمین به پیام «تماس با ما».

    اگر ``reply_text`` خالی باشد یعنی فقط وضعیت «پاسخ‌داده‌شده» ثبت می‌شود؛
    همان رفتار همگام قبلی — بدون ایمیل، موفق برمی‌گردد.
    """
    if not reply_text:
        return True
    if not _mail_available():
        logger.info('MAIL_SERVER not configured; skip contact reply #%s', contact_id)
        return False

    from app.extensions import db
    from app.models import Contact
    from app.services.email_service import EmailService

    contact: Optional[Contact] = db.session.get(Contact, contact_id)
    if contact is None or not contact.email:
        logger.warning('Contact %s missing/email-less; reply not sent', contact_id)
        return False

    ok = EmailService.send_contact_reply(
        contact_email=contact.email,
        contact_name=contact.name,
        reply_text=reply_text,
        original_subject=contact.subject or 'پیام شما',
    )
    if not ok:
        raise RuntimeError(f'EmailService failed for contact reply {contact_id}')
    return True
