"""
Order and Cart Models
"""
from datetime import datetime, timedelta
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
import uuid

from app.extensions import db
from app.models.base import BaseModel, TimestampMixin, SoftDeleteMixin


class Order(BaseModel, TimestampMixin):
    """Order Model"""
    
    __tablename__ = 'orders'
    
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    user_id = db.Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    
    # Status
    status = db.Column(
        Enum('pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded', 
             name='order_status'),
        default='pending',
        nullable=False,
        index=True
    )
    
    # Pricing
    subtotal = db.Column(Float, default=0, nullable=False)
    discount_amount = db.Column(Float, default=0)
    discount_code = db.Column(db.String(50), nullable=True)
    shipping_amount = db.Column(Float, default=0)
    tax_amount = db.Column(Float, default=0)
    total_amount = db.Column(Float, default=0, nullable=False)
    
    # Payment
    payment_method = db.Column(
        Enum('cash', 'card', 'online', 'wallet', name='payment_method'),
        default='cash',
        nullable=False
    )
    payment_status = db.Column(
        Enum('unpaid', 'paid', 'failed', 'refunded', name='payment_status'),
        default='unpaid',
        nullable=False,
        index=True
    )
    payment_reference = db.Column(db.String(255), nullable=True)
    payment_date = db.Column(DateTime, nullable=True)
    
    # Shipping
    shipping_address_id = db.Column(Integer, ForeignKey('addresses.id'), nullable=True)
    
    # Shipping info (copy from address)
    recipient_name = db.Column(db.String(100), nullable=True)
    recipient_phone = db.Column(db.String(20), nullable=True)
    province = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    postal_code = db.Column(db.String(10), nullable=True)
    address = db.Column(db.Text, nullable=True)
    
    shipping_method = db.Column(db.String(100), nullable=True)
    tracking_code = db.Column(db.String(100), nullable=True, index=True)
    tracking_url = db.Column(db.String(500), nullable=True)
    
    # Notes
    customer_note = db.Column(db.Text, nullable=True)
    admin_note = db.Column(db.Text, nullable=True)
    
    # Timestamps
    confirmed_at = db.Column(DateTime, nullable=True)
    shipped_at = db.Column(DateTime, nullable=True)
    delivered_at = db.Column(DateTime, nullable=True)
    cancelled_at = db.Column(DateTime, nullable=True)
    
    # Extra data
    extra_data = db.Column(JSON, nullable=True)
    
    # Relationships
    user = relationship('User', back_populates='orders')
    items = relationship('OrderItem', back_populates='order', lazy='dynamic', cascade='all, delete-orphan')
    shipping_address = relationship('Address', back_populates='orders')
    transactions = relationship('PaymentTransaction', back_populates='order', lazy='dynamic')
    
    @classmethod
    def generate_order_number(cls) -> str:
        """Generate unique order number"""
        date_str = datetime.utcnow().strftime('%Y%m%d')
        random_str = uuid.uuid4().hex[:6].upper()
        return f'ORD-{date_str}-{random_str}'
    
    def calculate_totals(self) -> None:
        """Recalculate order totals"""
        self.subtotal = sum(item.total for item in self.items)
        self.total_amount = self.subtotal + self.shipping_amount + self.tax_amount - self.discount_amount
    
    def add_item(self, product, quantity: int = 1, unit_price: float = None) -> 'OrderItem':
        """Add item to order"""
        if unit_price is None:
            unit_price = product.current_price
        
        # Check if item already exists
        existing_item = self.items.filter_by(product_id=product.id).first()
        if existing_item:
            existing_item.quantity += quantity
            existing_item.save()
            return existing_item
        
        item = OrderItem(
            order_id=self.id,
            product_id=product.id,
            quantity=quantity,
            unit_price=unit_price,
            product_snapshot={
                'title': product.title,
                'sku': product.sku,
                'image': product.main_image_url,
            }
        )
        item.save()
        self.calculate_totals()
        return item
    
    def remove_item(self, item_id: int) -> bool:
        """Remove item from order"""
        item = self.items.filter_by(id=item_id).first()
        if item:
            item.delete()
            self.calculate_totals()
            return True
        return False
    
    def update_status(self, new_status: str) -> None:
        """Update order status with timestamp"""
        self.status = new_status
        
        status_timestamps = {
            'confirmed': 'confirmed_at',
            'shipped': 'shipped_at',
            'delivered': 'delivered_at',
            'cancelled': 'cancelled_at'
        }
        
        if new_status in status_timestamps:
            setattr(self, status_timestamps[new_status], datetime.utcnow())
        
        db.session.commit()
    
    def confirm(self) -> None:
        """Confirm order"""
        self.update_status('confirmed')
    
    def cancel(self, reason: str = None) -> None:
        """Cancel order"""
        self.status = 'cancelled'
        self.cancelled_at = datetime.utcnow()
        if reason:
            self.admin_note = f"دلیل لغو: {reason}"
        db.session.commit()
    
    def mark_paid(self, reference: str = None) -> None:
        """Mark order as paid"""
        self.payment_status = 'paid'
        self.payment_reference = reference
        self.payment_date = datetime.utcnow()
        db.session.commit()
    
    @property
    def status_fa(self) -> str:
        """Get Persian status text"""
        status_map = {
            'pending': 'در انتظار پرداخت',
            'confirmed': 'تأیید شده',
            'processing': 'در حال آماده‌سازی',
            'shipped': 'ارسال شده',
            'delivered': 'تحویل داده شده',
            'cancelled': 'لغو شده',
            'refunded': 'بازگردانده شده'
        }
        return status_map.get(self.status, self.status)
    
    @property
    def payment_status_fa(self) -> str:
        """Get Persian payment status text"""
        status_map = {
            'unpaid': 'پرداخت نشده',
            'paid': 'پرداخت شده',
            'failed': 'ناموفق',
            'refunded': 'بازگردانده شده'
        }
        return status_map.get(self.payment_status, self.payment_status)
    
    @property
    def can_cancel(self) -> bool:
        """Check if order can be cancelled"""
        return self.status in ['pending', 'confirmed']
    
    @property
    def can_return(self) -> bool:
        """Check if order can be returned"""
        return self.status == 'delivered' and \
               (datetime.utcnow() - self.delivered_at).days <= 7
    
    def __repr__(self):
        return f'<Order {self.order_number}>'


class OrderItem(BaseModel, TimestampMixin):
    """Order Item Model"""
    
    __tablename__ = 'order_items'
    
    order_id = db.Column(Integer, ForeignKey('orders.id'), nullable=False, index=True)
    product_id = db.Column(Integer, ForeignKey('products.id'), nullable=True, index=True)
    
    quantity = db.Column(Integer, default=1, nullable=False)
    unit_price = db.Column(Float, nullable=False)
    discount = db.Column(Float, default=0)
    
    # Snapshot of product at time of order
    product_snapshot = db.Column(JSON, nullable=True)
    
    # Relationships
    order = relationship('Order', back_populates='items')
    product = relationship('Product', back_populates='items')
    
    @property
    def total(self) -> float:
        """Get item total"""
        return (self.unit_price * self.quantity) - self.discount
    
    @property
    def title(self) -> str:
        """Get product title from snapshot"""
        if self.product_snapshot:
            return self.product_snapshot.get('title', 'محصول حذف شده')
        if self.product:
            return self.product.title
        return 'محصول'
    
    def __repr__(self):
        return f'<OrderItem {self.id}>'


class CartItem(BaseModel, TimestampMixin):
    """Cart Item Model"""
    
    __tablename__ = 'cart_items'
    
    user_id = db.Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    session_id = db.Column(db.String(255), nullable=True, index=True)  # For non-logged in users
    product_id = db.Column(Integer, ForeignKey('products.id'), nullable=False, index=True)
    
    quantity = db.Column(Integer, default=1, nullable=False)
    variations = db.Column(JSON, nullable=True)  # Selected variations
    
    # Relationships
    user = relationship('User', back_populates='cart_items')
    product = relationship('Product', back_populates='cart_items')
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'product_id', 'session_id', 
                           name='unique_cart_item'),
    )
    
    @property
    def total(self) -> float:
        """Get cart item total"""
        return self.product.current_price * self.quantity
    
    def __repr__(self):
        return f'<CartItem {self.id}>'


class Wishlist(BaseModel, TimestampMixin):
    """Wishlist Model"""
    
    __tablename__ = 'wishlists'
    
    user_id = db.Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    product_id = db.Column(Integer, ForeignKey('products.id'), nullable=False, index=True)
    
    # Relationships
    user = relationship('User', back_populates='wishlists')
    product = relationship('Product', back_populates='wishlisted_by')
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'product_id', name='unique_wishlist_item'),
    )
    
    def __repr__(self):
        return f'<Wishlist {self.id}>'


class Comparison(BaseModel, TimestampMixin):
    """Product Comparison Model"""
    
    __tablename__ = 'comparisons'
    
    user_id = db.Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    product_id = db.Column(Integer, ForeignKey('products.id'), nullable=False, index=True)
    
    # Relationships
    user = relationship('User', back_populates='comparisons')
    product = relationship('Product', back_populates='compared_by')
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'product_id', name='unique_comparison_item'),
    )
    
    def __repr__(self):
        return f'<Comparison {self.id}>'


class PaymentTransaction(BaseModel, TimestampMixin):
    """Payment Transaction Model"""
    
    __tablename__ = 'payment_transactions'
    
    order_id = db.Column(Integer, ForeignKey('orders.id'), nullable=False, index=True)
    
    amount = db.Column(Float, nullable=False)
    payment_method = db.Column(String(50), nullable=True)
    gateway = db.Column(String(50), nullable=True)
    
    reference_id = db.Column(db.String(255), nullable=True, index=True)
    tracking_code = db.Column(db.String(255), nullable=True)
    
    status = db.Column(
        Enum('pending', 'success', 'failed', 'cancelled', 'refunded', name='transaction_status'),
        default='pending',
        nullable=False
    )
    
    gateway_response = db.Column(JSON, nullable=True)
    
    # Timestamps
    paid_at = db.Column(DateTime, nullable=True)
    
    # Relationships
    order = relationship('Order', back_populates='transactions')
    
    def __repr__(self):
        return f'<PaymentTransaction {self.reference_id or self.id}>'
