"""
Cart Service
"""
from typing import List, Optional
from flask import request, session
from sqlalchemy import and_

from app.extensions import db
from app.models import Product, CartItem


class CartService:
    """Shopping Cart Operations"""
    
    @staticmethod
    def get_session_id() -> str:
        """Get or create session ID"""
        if 'cart_session_id' not in session:
            from uuid import uuid4
            session['cart_session_id'] = str(uuid4())
        return session['cart_session_id']
    
    # ==================== SESSION CART (Guest Users) ====================
    
    @staticmethod
    def get_session_cart(session_id: str) -> List[dict]:
        """Get cart items from session"""
        cart_data = session.get('cart', {})
        items = []
        
        for product_id, quantity in cart_data.items():
            product = Product.query.get(int(product_id))
            if product and not product.is_deleted:
                items.append({
                    'product': product,
                    'quantity': quantity
                })
        
        return items
    
    @staticmethod
    def get_session_cart_count(session_id: str) -> int:
        """Get total items count in session cart"""
        cart_data = session.get('cart', {})
        return sum(cart_data.values())
    
    @staticmethod
    def get_session_cart_total(session_id: str) -> float:
        """Get total price of session cart"""
        cart_data = session.get('cart', {})
        total = 0
        
        for product_id, quantity in cart_data.items():
            product = Product.query.get(int(product_id))
            if product and not product.is_deleted:
                total += product.current_price * quantity
        
        return total
    
    @staticmethod
    def add_to_session_cart(product_id: int, quantity: int = 1) -> bool:
        """Add item to session cart"""
        cart_data = session.get('cart', {})
        
        product = Product.query.get(product_id)
        if not product or not product.is_in_stock:
            return False
        
        if product_id in cart_data:
            cart_data[product_id] += quantity
        else:
            cart_data[product_id] = quantity
        
        session['cart'] = cart_data
        session.modified = True
        
        return True
    
    @staticmethod
    def update_session_cart_item(product_id: int, quantity: int) -> bool:
        """Update quantity of session cart item"""
        cart_data = session.get('cart', {})
        
        if quantity <= 0:
            if product_id in cart_data:
                del cart_data[product_id]
        else:
            cart_data[product_id] = quantity
        
        session['cart'] = cart_data
        session.modified = True
        
        return True
    
    @staticmethod
    def remove_from_session_cart(product_id: int) -> bool:
        """Remove item from session cart"""
        cart_data = session.get('cart', {})
        
        if product_id in cart_data:
            del cart_data[product_id]
            session['cart'] = cart_data
            session.modified = True
            return True
        
        return False
    
    @staticmethod
    def clear_session_cart() -> None:
        """Clear entire session cart"""
        session.pop('cart', None)
        session.modified = True
    
    # ==================== USER CART (Logged In Users) ====================
    
    @staticmethod
    def get_user_cart(user_id: int) -> List[CartItem]:
        """Get user's cart items"""
        return CartItem.query.filter_by(user_id=user_id, is_deleted=False).all()
    
    @staticmethod
    def get_user_cart_count(user_id: int) -> int:
        """Get total items count in user's cart"""
        result = db.session.query(db.func.sum(CartItem.quantity)).filter(
            CartItem.user_id == user_id,
            CartItem.is_deleted == False
        ).scalar()
        return result or 0
    
    @staticmethod
    def get_user_cart_total(user_id: int) -> float:
        """Get total price of user's cart"""
        items = CartItem.query.filter_by(user_id=user_id, is_deleted=False).all()
        total = 0
        
        for item in items:
            if item.product and not item.product.is_deleted:
                total += item.product.current_price * item.quantity
        
        return total
    
    @staticmethod
    def add_to_user_cart(user_id: int, product_id: int, quantity: int = 1) -> bool:
        """Add item to user's cart"""
        product = Product.query.get(product_id)
        if not product or not product.is_in_stock:
            return False
        
        # Check if already in cart
        existing = CartItem.query.filter_by(
            user_id=user_id,
            product_id=product_id,
            is_deleted=False
        ).first()
        
        if existing:
            existing.quantity += quantity
            db.session.commit()
        else:
            item = CartItem(
                user_id=user_id,
                product_id=product_id,
                quantity=quantity
            )
            db.session.add(item)
            db.session.commit()
        
        return True
    
    @staticmethod
    def update_user_cart_item(item_id: int, quantity: int) -> bool:
        """Update quantity of user cart item"""
        item = CartItem.query.get(item_id)
        
        if not item:
            return False
        
        if quantity <= 0:
            item.delete()
        else:
            item.quantity = quantity
            db.session.commit()
        
        return True
    
    @staticmethod
    def remove_from_user_cart(item_id: int) -> bool:
        """Remove item from user's cart"""
        item = CartItem.query.get(item_id)
        
        if item:
            item.delete()
            return True
        
        return False
    
    @staticmethod
    def clear_user_cart(user_id: int) -> None:
        """Clear entire user's cart"""
        CartItem.query.filter_by(user_id=user_id).delete()
        db.session.commit()
    
    # ==================== UNIFIED METHODS ====================
    
    @staticmethod
    def get_cart(user_id: Optional[int] = None) -> List:
        """Get cart items for user or guest"""
        if user_id:
            return CartService.get_user_cart(user_id)
        else:
            return CartService.get_session_cart(CartService.get_session_id())
    
    @staticmethod
    def get_cart_count(user_id: Optional[int] = None) -> int:
        """Get cart items count for user or guest"""
        if user_id:
            return CartService.get_user_cart_count(user_id)
        else:
            return CartService.get_session_cart_count(CartService.get_session_id())
    
    @staticmethod
    def get_cart_total(user_id: Optional[int] = None) -> float:
        """Get cart total for user or guest"""
        if user_id:
            return CartService.get_user_cart_total(user_id)
        else:
            return CartService.get_session_cart_total(CartService.get_session_id())
    
    @staticmethod
    def add_to_cart(product_id: int, quantity: int = 1, user_id: Optional[int] = None) -> bool:
        """Add item to cart for user or guest"""
        if user_id:
            return CartService.add_to_user_cart(user_id, product_id, quantity)
        else:
            return CartService.add_to_session_cart(product_id, quantity)
    
    @staticmethod
    def update_cart_item(item_id: int, quantity: int, user_id: Optional[int] = None) -> bool:
        """Update cart item for user or guest"""
        if user_id:
            return CartService.update_user_cart_item(item_id, quantity)
        else:
            # For guest, item_id is product_id
            return CartService.update_session_cart_item(item_id, quantity)
    
    @staticmethod
    def remove_from_cart(item_id: int, user_id: Optional[int] = None) -> bool:
        """Remove item from cart for user or guest"""
        if user_id:
            return CartService.remove_from_user_cart(item_id)
        else:
            return CartService.remove_from_session_cart(item_id)
    
    @staticmethod
    def clear_cart(user_id: Optional[int] = None) -> None:
        """Clear cart for user or guest"""
        if user_id:
            CartService.clear_user_cart(user_id)
        else:
            CartService.clear_session_cart()
    
    @staticmethod
    def merge_carts(guest_session_id: str, user_id: int) -> None:
        """Merge guest cart into user cart after login"""
        guest_cart = CartService.get_session_cart(guest_session_id)
        
        for item in guest_cart:
            CartService.add_to_user_cart(user_id, item['product'].id, item['quantity'])
        
        CartService.clear_session_cart()
