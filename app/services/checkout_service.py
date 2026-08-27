"""
Checkout Service — handles the entire order creation flow.
This is the missing piece: previously cart had no way to become an Order.
"""
from typing import Optional, List, Dict, Any, Tuple
from decimal import Decimal
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models import (
    Order, OrderItem, CartItem, Product, User, Address,
    PaymentTransaction, Setting
)
from app.services.cart_service import CartService
from app.services.notification_service import NotificationService
from app.constants import OrderStatus, PaymentStatus, PaymentMethod, TransactionStatus


class CheckoutError(Exception):
    """Custom exception for checkout failures."""
    def __init__(self, message: str, code: str = 'checkout_error', status: int = 400):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status


class CheckoutService:
    """Handles order creation, validation, and post-order cleanup."""

    SHIPPING_COST = 0       # Free shipping (could be dynamic later)
    TAX_PERCENT = 0         # 0% (Iran's e-commerce tax)

    @classmethod
    def create_order_from_cart(
        cls,
        user: Optional[User],
        cart_items: List,
        shipping_address: Dict[str, str],
        payment_method: str = PaymentMethod.ONLINE.value,
        customer_note: str = '',
        discount_code: str = '',
    ) -> Order:
        """
        Create an order from the current cart.

        Args:
            user: Current user (None for guest checkout).
            cart_items: List of CartItem (or dict for guest) objects.
            shipping_address: Dict with keys: recipient_name, recipient_phone,
                province, city, address, postal_code.
            payment_method: One of PaymentMethod values.
            customer_note: Optional customer message.
            discount_code: Optional coupon code (not yet implemented).

        Returns:
            Created Order instance.

        Raises:
            CheckoutError: If validation fails or DB error.
        """
        # ---- 1. Validate inputs ----
        if not cart_items:
            raise CheckoutError('سبد خرید شما خالی است.', code='empty_cart', status=400)

        if not shipping_address or not shipping_address.get('recipient_name'):
            raise CheckoutError('اطلاعات گیرنده ناقص است.', code='invalid_address', status=400)

        cls._validate_address(shipping_address)

        if payment_method not in [m.value for m in PaymentMethod]:
            raise CheckoutError('روش پرداخت نامعتبر است.', code='invalid_payment', status=400)

        # ---- 2. Validate products and stock ----
        validated_items = []
        for item in cart_items:
            # CartItem (کاربر لاگین‌کرده) یا dict سبد مهمان
            if hasattr(item, 'product'):
                product, quantity = item.product, item.quantity
            else:
                product = item.get('product') or Product.query.get(item.get('product_id'))
                quantity = item.get('quantity', 1)

            if not product or product.is_deleted or not product.is_active:
                raise CheckoutError(
                    f'محصول «{product.title if product else "نامشخص"}» دیگر موجود نیست.',
                    code='product_unavailable', status=409
                )

            if product.stock_quantity is not None and product.stock_quantity < quantity:
                raise CheckoutError(
                    f'موجودی محصول «{product.title}» کافی نیست. فقط {product.stock_quantity} عدد موجود است.',
                    code='insufficient_stock', status=409
                )

            validated_items.append({'product': product, 'quantity': quantity})

        # ---- 3. Calculate totals ----
        subtotal = sum(
            float(item['product'].current_price) * item['quantity']
            for item in validated_items
        )
        discount_amount = cls._apply_discount(discount_code, subtotal) if discount_code else 0
        tax_amount = (subtotal - discount_amount) * (cls.TAX_PERCENT / 100)
        total_amount = subtotal + cls.SHIPPING_COST + tax_amount - discount_amount

        # ---- 4. Create Order ----
        try:
            order = Order(
                order_number=Order.generate_order_number(),
                user_id=user.id if user else None,
                status=OrderStatus.PENDING.value,
                payment_method=payment_method,
                payment_status=PaymentStatus.UNPAID.value,
                subtotal=subtotal,
                discount_amount=discount_amount,
                discount_code=discount_code or None,
                shipping_amount=cls.SHIPPING_COST,
                tax_amount=tax_amount,
                total_amount=total_amount,
                recipient_name=shipping_address.get('recipient_name'),
                recipient_phone=shipping_address.get('recipient_phone'),
                province=shipping_address.get('province'),
                city=shipping_address.get('city'),
                postal_code=shipping_address.get('postal_code'),
                address=shipping_address.get('address'),
                customer_note=customer_note or None,
            )
            db.session.add(order)
            db.session.flush()  # Get order.id before adding items

            # ---- 5. Add items to order ----
            for item in validated_items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item['product'].id,
                    quantity=item['quantity'],
                    unit_price=float(item['product'].current_price),
                    product_snapshot={
                        'title': item['product'].title,
                        'sku': item['product'].sku,
                        'image': item['product'].main_image_url,
                        'slug': item['product'].slug,
                    }
                )
                db.session.add(order_item)

            # ---- 6. Decrement stock ----
            for item in validated_items:
                product = item['product']
                if product.stock_quantity is not None:
                    product.stock_quantity -= item['quantity']
                    product.save()

            # ---- 7. Create initial transaction record ----
            transaction = PaymentTransaction(
                order_id=order.id,
                amount=total_amount,
                payment_method=payment_method,
                status=TransactionStatus.PENDING.value,
            )
            db.session.add(transaction)

            db.session.commit()

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f'Order creation DB error: {e}')
            raise CheckoutError(
                'خطا در ثبت سفارش. لطفاً مجدداً تلاش کنید.',
                code='db_error', status=500
            )

        # ---- 8. Notify (post-commit) ----
        # اعلان داخلی ادمین‌ها همین‌جا نوشته می‌شود (محلی و سریع)؛
        # اما تماس شبکه‌ای با تلگرام به صف Celery می‌رود تا در صورت کُندی/قطعی
        # تلگرام، ثبت سفارش کاربر با خطا یا تأخیر مواجه نشود.
        try:
            NotificationService.notify_admins(
                title='سفارش جدید',
                message=f'سفارش {order.order_number} به مبلغ {int(order.total_amount):,} تومان ثبت شد.',
                type='order',
                data={'order_id': order.id}
            )
            from app.tasks import enqueue
            from app.tasks.notify_tasks import telegram_order_new_task
            enqueue(telegram_order_new_task, order.id)
        except Exception as e:
            # Don't fail the order if notification fails
            current_app.logger.warning(f'Order notification failed: {e}')

        return order

    @classmethod
    def clear_user_cart(cls, user: User) -> None:
        """Clear the cart after successful order."""
        try:
            if user:
                CartItem.query.filter_by(user_id=user.id).delete()
            db.session.commit()
        except SQLAlchemyError as e:
            current_app.logger.error(f'Cart cleanup error: {e}')
            db.session.rollback()

    @classmethod
    def _validate_address(cls, address: Dict[str, str]) -> None:
        """Validate shipping address fields."""
        required_fields = ['recipient_name', 'recipient_phone', 'province', 'city', 'address']
        for field in required_fields:
            if not address.get(field, '').strip():
                raise CheckoutError(
                    f'فیلد «{cls._field_label_fa(field)}» الزامی است.',
                    code='missing_field', status=400
                )

        # Phone validation
        phone = address.get('recipient_phone', '').strip()
        import re
        from app.constants import PHONE_PATTERN_IR, PHONE_LANDLINE_IR
        if not (re.match(PHONE_PATTERN_IR, phone) or re.match(PHONE_LANDLINE_IR, phone)):
            raise CheckoutError(
                'شماره تلفن نامعتبر است.',
                code='invalid_phone', status=400
            )

    @staticmethod
    def _field_label_fa(field: str) -> str:
        labels = {
            'recipient_name': 'نام گیرنده',
            'recipient_phone': 'تلفن گیرنده',
            'province': 'استان',
            'city': 'شهر',
            'address': 'آدرس',
            'postal_code': 'کد پستی',
        }
        return labels.get(field, field)

    @classmethod
    def _apply_discount(cls, code: str, subtotal: float) -> float:
        """Apply discount code. Returns discount amount. (Stub for now.)"""
        # TODO: implement discount code lookup
        # For now, return 0
        return 0.0

    @classmethod
    def cancel_order(cls, order: Order, reason: str = '', user: Optional[User] = None) -> bool:
        """Cancel an order and restore stock."""
        if not order.can_cancel:
            raise CheckoutError('امکان لغو این سفارش وجود ندارد.', code='cannot_cancel', status=400)

        if user and order.user_id and order.user_id != user.id and not user.is_admin():
            raise CheckoutError('دسترسی غیرمجاز.', code='unauthorized', status=403)

        try:
            # Restore stock
            for item in order.items:
                if item.product and item.product.stock_quantity is not None:
                    item.product.stock_quantity += item.quantity
                    item.product.save()

            order.cancel(reason)
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f'Order cancel error: {e}')
            raise CheckoutError('خطا در لغو سفارش.', code='db_error', status=500)
