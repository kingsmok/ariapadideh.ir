"""
Storefront Scheduled Tasks — زمان‌بندی‌شده‌های فروشگاه (Celery Beat)

این ماژول «نگهداری» وضعیت سفارش‌هاست؛ قلب هر فروشگاه زنجیره‌ای:

۱. لغو خودکار سفارش‌های «در انتظار پرداخت» که مهلتشان تمام شده +
   بازگرداندن موجودی رزروشده (checkout موجودی را کسر می‌کند؛ اگر سفارش
   پرداخت نشود این موجودی تا ابد قفل می‌ماند).
۲. پاک‌سازی سبد‌های خالی‌ماندهٔ کاربران مهمان.

منطق خام (``*_impl``) از پوستهٔ تسک جدا است تا در تست‌ها بدون موتور Celery
قابل صدا زدن باشد و از ورکر هم یکسان اجرا شود.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.tasks.celery_app import celery

logger = logging.getLogger(__name__)


def expire_unpaid_orders_impl(grace_minutes: int | None = None) -> Dict[str, int]:
    """لغو سفارش‌های معوق و آزادسازی موجودی.

    معیار: سفارش با وضعیت ``pending`` و پرداخت ``unpaid`` که
    ``created_at`` قدیمی‌تر از پنجرهٔ مهلت باشد. برای چنین سفارشی:

    - موجودی هر قلم (فقط محصولات دارای موجودی عددی؛ ``None`` یعنی نامحدود)
      برگردانده می‌شود؛
    - سفارش ``cancelled`` با برچسب «اتمام مهلت پرداخت» می‌شود؛
    - تراکنش‌های ``pending`` آن ``failed`` می‌شوند تا گزارش‌های مالی گمراه‌کننده نمانند.

    هر سفارش در ترنزکشن مستقل commit می‌شود تا خرابی یک ردیف، بقیه را متوقف
    نکند (الگوی امن در batch job).

    Args:
        grace_minutes: پنجرهٔ مهلت؛ None یعنی از config
            (``ORDER_PAYMENT_GRACE_MINUTES``، پیش‌فرض ۴۵ دقیقه). مقدار
            ناصفر/منفی یعنی «غیرفعال» و هیچ سفارشی لمس نمی‌شود.

    Returns:
        dict خلاصه: ``{'expired': n, 'restored_lines': m, 'failed': k}``
    """
    from app.models import Order, OrderItem, PaymentTransaction, Product
    from app.constants import OrderStatus, PaymentStatus, TransactionStatus

    if grace_minutes is None:
        from flask import current_app
        grace_minutes = int(current_app.config.get('ORDER_PAYMENT_GRACE_MINUTES', 45))

    if grace_minutes <= 0:
        logger.info('expire_unpaid_orders disabled (grace=%s)', grace_minutes)
        return {'expired': 0, 'restored_lines': 0, 'failed': 0, 'skipped': 1}

    cutoff = datetime.utcnow() - timedelta(minutes=grace_minutes)

    orders: List[Any] = list(db.session.execute(
        select(Order).where(
            Order.status == OrderStatus.PENDING.value,
            Order.payment_status == PaymentStatus.UNPAID.value,
            Order.is_deleted.is_(False),
            Order.created_at < cutoff,
        ).order_by(Order.id)
    ).scalars().all())

    expired = 0
    restored_lines = 0
    failed = 0

    for order in orders:
        try:
            # ---- 1. بازگرداندن موجودی (کوئری گروهی برای جلوگیری از N+1) ----
            items: List[OrderItem] = list(order.items.all())
            product_ids = [it.product_id for it in items if it.product_id]
            products: Dict[int, Any] = {}
            if product_ids:
                rows = db.session.execute(
                    select(Product).where(Product.id.in_(product_ids))
                ).scalars().all()
                products = {p.id: p for p in rows}

            for item in items:
                product = products.get(item.product_id or -1)
                # stock_quantity None یعنی موجودی نامحدود — چیزی رزرو نشده که برگردد
                if product is not None and product.stock_quantity is not None:
                    product.stock_quantity += int(item.quantity or 0)
                    restored_lines += 1

            # ---- 2. لغو سفارش با برچسب دلایل ----
            note = 'اتمام مهلت پرداخت — لغو خودکار سیستم'
            order.status = OrderStatus.CANCELLED.value
            order.cancelled_at = datetime.utcnow()
            order.admin_note = f'{order.admin_note}\n{note}' if order.admin_note else note

            # ---- 3. بستن تراکنش‌های معوق ----
            db.session.execute(
                update(PaymentTransaction)
                .where(
                    PaymentTransaction.order_id == order.id,
                    PaymentTransaction.status == TransactionStatus.PENDING.value,
                )
                .values(status=TransactionStatus.FAILED.value)
            )

            db.session.commit()
            expired += 1
            logger.info(
                'Expired unpaid order %s (older than %s min); %s line(s) restocked',
                order.order_number, grace_minutes, len(items),
            )
        except SQLAlchemyError as exc:
            db.session.rollback()
            failed += 1
            logger.error('Failed to expire order %s: %s', order.order_number, exc, exc_info=True)

    return {'expired': expired, 'restored_lines': restored_lines, 'failed': failed}


def cleanup_stale_guest_carts_impl(retention_days: int | None = None) -> int:
    """حذف سبد خرید رهاشدهٔ کاربران مهمان.

    فقط ردیف‌هایی که ``session_id`` دارند (مهمان) و قدیمی‌تر از دورهٔ نگهداری
    هستند حذف می‌شوند؛ سبد کاربران لاگین‌کرده هرگز خودکار پاک نمی‌شود چون
    دارایی حساب کاربر محسوب می‌شود.

    Args:
        retention_days: None → از config (``GUEST_CART_RETENTION_DAYS``، ۳۰ روز).

    Returns:
        تعداد ردیف‌های حذف‌شده.
    """
    from sqlalchemy import delete as sql_delete

    from app.models import CartItem

    if retention_days is None:
        from flask import current_app
        retention_days = int(current_app.config.get('GUEST_CART_RETENTION_DAYS', 30))

    if retention_days <= 0:
        logger.info('cleanup_stale_guest_carts disabled (retention=%s)', retention_days)
        return 0

    cutoff = datetime.utcnow() - timedelta(days=retention_days)
    stmt = sql_delete(CartItem).where(
        CartItem.session_id.isnot(None),
        CartItem.created_at < cutoff,
    )
    try:
        res = db.session.execute(stmt)
        db.session.commit()
        removed = int(res.rowcount or 0)
        logger.info('Removed %s stale guest cart line(s) older than %s days', removed, retention_days)
        return removed
    except SQLAlchemyError as exc:
        db.session.rollback()
        logger.error('Cart cleanup failed: %s', exc, exc_info=True)
        raise


# ==================== Celery task shells ====================

@celery.task(
    name='flaskpro.orders.expire_unpaid',
    bind=True,
    autoretry_for=(SQLAlchemyError,),
    retry_backoff=True,
    retry_backoff_max=900,
    retry_jitter=True,
    max_retries=3,
    acks_late=True,
)
def expire_unpaid_orders(self, grace_minutes: int | None = None) -> Dict[str, int]:
    """تسک beat: لغو سفارش‌های بی‌پرداخت معوق (هر ۱۰ دقیقه)."""
    return expire_unpaid_orders_impl(grace_minutes)


@celery.task(
    name='flaskpro.orders.cleanup_stale_carts',
    bind=True,
    autoretry_for=(SQLAlchemyError,),
    retry_backoff=True,
    retry_backoff_max=900,
    max_retries=2,
    acks_late=True,
)
def cleanup_stale_guest_carts(self, retention_days: int | None = None) -> Dict[str, int]:
    """تسک beat: پاک‌سازی سبد مهمان‌ها (هر شب ۰۳:۱۵ تهران)."""
    removed = cleanup_stale_guest_carts_impl(retention_days)
    return {'removed': removed}
