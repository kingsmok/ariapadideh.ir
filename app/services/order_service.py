"""
Order Management Service Layer
Encapsulates business operations for order querying, state transitions,
cancellation with inventory restoration, and invoice summaries.
Adheres strictly to SQLAlchemy 2.0 standards.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import desc, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload, selectinload

from app.constants import OrderStatus, PaymentStatus
from app.extensions import db
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.services.product_service import ProductService

logger = logging.getLogger(__name__)


class OrderService:
    """Production service for handling order lifecycle and fulfillment."""

    @staticmethod
    def get_by_id(order_id: int) -> Optional[Order]:
        """
        Fetch an order by primary key with items, products, and shipping address eagerly loaded.
        """
        try:
            stmt = (
                select(Order)
                .where(Order.id == order_id)
                .options(
                    joinedload(Order.shipping_address),
                    joinedload(Order.user),
                )
            )
            return db.session.execute(stmt).scalars().first()
        except SQLAlchemyError as exc:
            logger.error("Failed to query order id %s: %s", order_id, exc, exc_info=True)
            return None

    @staticmethod
    def get_by_number(order_number: str) -> Optional[Order]:
        """
        Fetch an order by public tracking order number.
        """
        try:
            stmt = (
                select(Order)
                .where(Order.order_number == order_number)
                .options(
                    joinedload(Order.shipping_address),
                    joinedload(Order.user),
                )
            )
            return db.session.execute(stmt).scalars().first()
        except SQLAlchemyError as exc:
            logger.error("Failed to query order number '%s': %s", order_number, exc, exc_info=True)
            return None

    @staticmethod
    def get_user_orders(
        user_id: int,
        page: int = 1,
        per_page: int = 10,
    ) -> Tuple[List[Order], int]:
        """
        Retrieve paginated orders belonging to a specific customer.
        """
        page = max(1, page)
        try:
            base_stmt = select(Order).where(Order.user_id == user_id)

            count_stmt = select(func.count()).select_from(base_stmt.subquery())
            total = db.session.execute(count_stmt).scalar() or 0

            orders_stmt = (
                base_stmt
                .options(
                    joinedload(Order.shipping_address),
                )
                .order_by(Order.created_at.desc())
                .offset((page - 1) * per_page)
                .limit(per_page)
            )
            items = list(db.session.execute(orders_stmt).scalars().all())
            return items, total
        except SQLAlchemyError as exc:
            logger.error("Error loading orders for user %s: %s", user_id, exc, exc_info=True)
            return [], 0

    @staticmethod
    def update_order_status(
        order_id: int,
        new_status: str,
        admin_note: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Transition an order to a new fulfillment status.
        """
        valid_statuses = {s.value for s in OrderStatus}
        if new_status not in valid_statuses:
            return False, f"وضعیت '{new_status}' نامعتبر است."

        try:
            order = OrderService.get_by_id(order_id)
            if not order:
                return False, "سفارش مورد نظر یافت نشد."

            order.status = new_status
            if admin_note:
                order.admin_note = (order.admin_note or "") + f"\n[{new_status}]: {admin_note}"

            db.session.commit()
            logger.info("Order %s status updated to '%s'", order_id, new_status)
            return True, f"وضعیت سفارش به '{order.status_fa}' تغییر یافت."
        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Failed to update status for order %s: %s", order_id, exc, exc_info=True)
            return False, "خطا در تغییر وضعیت سفارش."

    @staticmethod
    def cancel_order(
        order_id: int,
        user_id: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Cancel an order and return reserved items to stock.
        """
        try:
            order = OrderService.get_by_id(order_id)
            if not order:
                return False, "سفارش مورد نظر یافت نشد."

            # Authorization check if initiated by user
            if user_id is not None and order.user_id != user_id:
                return False, "شما دسترسی لازم برای لغو این سفارش را ندارید."

            if not order.can_cancel:
                return False, f"سفارش در وضعیت '{order.status_fa}' قابل لغو نمی‌باشد."

            # Restore product inventory
            for item in order.items:
                if item.product_id and item.quantity > 0:
                    ProductService.update_stock(item.product_id, item.quantity)

            order.status = OrderStatus.CANCELLED.value
            if reason:
                order.cancel_reason = reason

            db.session.commit()
            logger.info("Order %s successfully cancelled with inventory restored", order_id)
            return True, "سفارش با موفقیت لغو شد و موجودی انبار به‌روزرسانی گردید."
        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Failed cancelling order %s: %s", order_id, exc, exc_info=True)
            return False, "خطا در فرایند لغو سفارش."
