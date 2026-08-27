"""
Cart Service Module
Production-ready shopping cart business logic supporting both session (guest)
and database-backed (authenticated user) carts with SQLAlchemy 2.0 syntax.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from uuid import uuid4

from flask import session
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models.order import CartItem
from app.models.product import Product

logger = logging.getLogger(__name__)


class CartService:
    """Production-grade Shopping Cart Operations for Flask Pro."""

    @staticmethod
    def get_session_id() -> str:
        """Retrieve or generate an isolated guest cart session identifier."""
        if 'cart_session_id' not in session:
            session['cart_session_id'] = str(uuid4())
            session.modified = True
        return str(session['cart_session_id'])

    # ==================== SESSION CART (Guest Users) ====================

    @staticmethod
    def get_session_cart(session_id: str) -> List[Dict[str, Any]]:
        """
        Fetch active cart items stored in the guest session.

        Eagerly loads active and non-deleted products in a single bulk query
        to prevent N+1 database roundtrips.
        """
        cart_data: Dict[str, int] = session.get('cart', {})
        if not cart_data:
            return []

        try:
            product_ids = [int(pid) for pid in cart_data.keys() if str(pid).isdigit()]
            if not product_ids:
                return []

            stmt = (
                select(Product)
                .where(
                    Product.id.in_(product_ids),
                    Product.is_deleted.is_(False),
                    Product.is_active.is_(True),
                )
                .options(selectinload(Product.categories))
            )
            products = db.session.execute(stmt).scalars().all()
            product_map = {product.id: product for product in products}

            items: List[Dict[str, Any]] = []
            for pid in product_ids:
                if pid in product_map:
                    qty = int(cart_data.get(str(pid), 1))
                    if qty > 0:
                        items.append({
                            'product': product_map[pid],
                            'quantity': qty,
                        })

            return items
        except Exception as exc:
            logger.error("Failed to load session cart: %s", exc, exc_info=True)
            return []

    @staticmethod
    def get_session_cart_count(session_id: str) -> int:
        """Calculate the total quantity of items currently stored in the session cart."""
        cart_data: Dict[str, int] = session.get('cart', {})
        return sum(int(qty) for qty in cart_data.values() if isinstance(qty, (int, str)) and int(qty) > 0)

    @staticmethod
    def get_session_cart_total(session_id: str) -> float:
        """Calculate the monetary total of all valid items in the guest session cart."""
        items = CartService.get_session_cart(session_id)
        return sum(item['product'].current_price * item['quantity'] for item in items)

    @staticmethod
    def add_to_session_cart(product_id: int, quantity: int = 1) -> bool:
        """
        Add a product or increment its quantity inside the guest session cart.

        Ensures product exists and is active before mutating session state.
        """
        if quantity <= 0:
            return False

        try:
            product = db.session.get(Product, product_id)
            if not product or product.is_deleted or not product.is_active:
                logger.warning("Attempted to add non-existent or inactive product %s to guest cart", product_id)
                return False

            cart_data: Dict[str, int] = session.get('cart', {})
            pid_str = str(product_id)
            current_qty = cart_data.get(pid_str, 0)
            cart_data[pid_str] = current_qty + quantity

            session['cart'] = cart_data
            session.modified = True
            return True
        except Exception as exc:
            logger.error("Error adding product %s to guest cart: %s", product_id, exc, exc_info=True)
            return False

    @staticmethod
    def update_session_cart_item(product_id: int, quantity: int) -> bool:
        """Update the quantity of a specific product in the guest session cart."""
        cart_data: Dict[str, int] = session.get('cart', {})
        pid_str = str(product_id)

        if quantity <= 0:
            cart_data.pop(pid_str, None)
        else:
            cart_data[pid_str] = quantity

        session['cart'] = cart_data
        session.modified = True
        return True

    @staticmethod
    def remove_from_session_cart(product_id: int) -> bool:
        """Remove a product entirely from the guest session cart."""
        cart_data: Dict[str, int] = session.get('cart', {})
        pid_str = str(product_id)

        if pid_str in cart_data:
            del cart_data[pid_str]
            session['cart'] = cart_data
            session.modified = True
            return True
        return False

    @staticmethod
    def clear_session_cart() -> None:
        """Flush the entire session cart structure."""
        session.pop('cart', None)
        session.modified = True

    # ==================== USER CART (Authenticated Users) ====================

    @staticmethod
    def get_user_cart(user_id: int) -> List[CartItem]:
        """
        Fetch all persisted cart items for a registered user.

        Uses selectinload to eagerly load related Product entities and avoid N+1 queries.
        """
        try:
            stmt = (
                select(CartItem)
                .where(CartItem.user_id == user_id, CartItem.is_deleted.is_(False))
                .options(
                    selectinload(CartItem.product).selectinload(Product.categories),
                )
                .order_by(CartItem.created_at.desc())
            )
            return list(db.session.execute(stmt).scalars().all())
        except SQLAlchemyError as exc:
            logger.error("Database error while fetching cart for user %s: %s", user_id, exc, exc_info=True)
            return []

    @staticmethod
    def get_user_cart_count(user_id: int) -> int:
        """Query the aggregated quantity count for an authenticated user's cart."""
        try:
            stmt = (
                select(func.coalesce(func.sum(CartItem.quantity), 0))
                .where(CartItem.user_id == user_id, CartItem.is_deleted.is_(False))
            )
            result = db.session.execute(stmt).scalar()
            return int(result or 0)
        except SQLAlchemyError as exc:
            logger.error("Database error while counting cart for user %s: %s", user_id, exc, exc_info=True)
            return 0

    @staticmethod
    def get_user_cart_total(user_id: int) -> float:
        """Calculate the total monetary sum of an authenticated user's cart items."""
        items = CartService.get_user_cart(user_id)
        total: float = 0.0
        for item in items:
            if item.product and not item.product.is_deleted and item.product.is_active:
                total += float(item.product.current_price) * item.quantity
        return total

    @staticmethod
    def add_to_user_cart(user_id: int, product_id: int, quantity: int = 1) -> bool:
        """
        Add a product to the user's database cart or increment quantity if present.

        Safely handles transactions and rollbacks on concurrency or database errors.
        """
        if quantity <= 0:
            return False

        try:
            product = db.session.get(Product, product_id)
            if not product or product.is_deleted or not product.is_active:
                logger.warning("User %s attempted to add invalid product %s", user_id, product_id)
                return False

            stmt = select(CartItem).where(
                CartItem.user_id == user_id,
                CartItem.product_id == product_id,
                CartItem.is_deleted.is_(False),
            )
            existing = db.session.execute(stmt).scalars().first()

            if existing:
                existing.quantity += quantity
            else:
                new_item = CartItem(
                    user_id=user_id,
                    product_id=product_id,
                    quantity=quantity,
                )
                db.session.add(new_item)

            db.session.commit()
            return True
        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Failed adding product %s to cart for user %s: %s", product_id, user_id, exc, exc_info=True)
            return False

    @staticmethod
    def update_user_cart_item(item_id: int, quantity: int) -> bool:
        """Update the quantity of a persisted user cart item or soft-delete if <= 0."""
        try:
            item = db.session.get(CartItem, item_id)
            if not item or item.is_deleted:
                return False

            if quantity <= 0:
                item.is_deleted = True
            else:
                item.quantity = quantity

            db.session.commit()
            return True
        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Failed updating cart item %s: %s", item_id, exc, exc_info=True)
            return False

    @staticmethod
    def remove_from_user_cart(item_id: int) -> bool:
        """Soft-delete an item from the user's cart."""
        try:
            item = db.session.get(CartItem, item_id)
            if item and not item.is_deleted:
                item.is_deleted = True
                db.session.commit()
                return True
            return False
        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Failed removing cart item %s: %s", item_id, exc, exc_info=True)
            return False

    @staticmethod
    def clear_user_cart(user_id: int) -> bool:
        """Mark all active cart items of a user as deleted."""
        try:
            stmt = select(CartItem).where(
                CartItem.user_id == user_id,
                CartItem.is_deleted.is_(False),
            )
            items = db.session.execute(stmt).scalars().all()
            for item in items:
                item.is_deleted = True
            db.session.commit()
            return True
        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Failed clearing cart for user %s: %s", user_id, exc, exc_info=True)
            return False

    # ==================== UNIFIED METHODS ====================

    @staticmethod
    def get_cart(user_id: Optional[int] = None) -> List[Any]:
        """Unified access to cart items regardless of authentication state."""
        if user_id:
            return CartService.get_user_cart(user_id)
        return CartService.get_session_cart(CartService.get_session_id())

    @staticmethod
    def get_cart_count(user_id: Optional[int] = None) -> int:
        """Unified count of items in cart."""
        if user_id:
            return CartService.get_user_cart_count(user_id)
        return CartService.get_session_cart_count(CartService.get_session_id())

    @staticmethod
    def get_cart_total(user_id: Optional[int] = None) -> float:
        """Unified total cost of cart items."""
        if user_id:
            return CartService.get_user_cart_total(user_id)
        return CartService.get_session_cart_total(CartService.get_session_id())

    @staticmethod
    def add_to_cart(product_id: int, quantity: int = 1, user_id: Optional[int] = None) -> bool:
        """Unified add-to-cart operation."""
        if user_id:
            return CartService.add_to_user_cart(user_id, product_id, quantity)
        return CartService.add_to_session_cart(product_id, quantity)

    @staticmethod
    def update_cart_item(item_id: int, quantity: int, user_id: Optional[int] = None) -> bool:
        """Unified cart item update."""
        if user_id:
            return CartService.update_user_cart_item(item_id, quantity)
        return CartService.update_session_cart_item(item_id, quantity)

    @staticmethod
    def remove_from_cart(item_id: int, user_id: Optional[int] = None) -> bool:
        """Unified item removal."""
        if user_id:
            return CartService.remove_from_user_cart(item_id)
        return CartService.remove_from_session_cart(item_id)

    @staticmethod
    def clear_cart(user_id: Optional[int] = None) -> None:
        """Unified cart cleanup."""
        if user_id:
            CartService.clear_user_cart(user_id)
        else:
            CartService.clear_session_cart()

    @staticmethod
    def merge_carts(guest_session_id: str, user_id: int) -> None:
        """
        Merge an existing guest session cart into an authenticated user's cart.

        Called immediately following successful user login or registration.
        """
        guest_items = CartService.get_session_cart(guest_session_id)
        for item in guest_items:
            product = item.get('product')
            quantity = item.get('quantity', 1)
            if product and hasattr(product, 'id'):
                CartService.add_to_user_cart(user_id, product.id, quantity)

        CartService.clear_session_cart()
