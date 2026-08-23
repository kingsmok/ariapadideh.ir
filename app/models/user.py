"""
User and Authentication Models
"""
from datetime import datetime
from typing import Optional, List
import hashlib
import secrets
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db
from app.models.base import BaseModel, TimestampMixin, SoftDeleteMixin, ActiveMixin


class Role(BaseModel, TimestampMixin, SoftDeleteMixin, ActiveMixin):
    """User Role Model"""
    
    __tablename__ = 'roles'
    
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    permissions = db.Column(db.Text, nullable=True)  # JSON string of permissions
    
    # Relationships
    users = relationship('User', back_populates='role', lazy='dynamic')
    permissions_rel = relationship('Permission', back_populates='role', lazy='dynamic')
    
    def has_permission(self, permission: str) -> bool:
        """Check if role has a specific permission"""
        if not self.permissions:
            return False
        permissions_list = self.permissions.split(',')
        return permission in permissions_list or 'all' in permissions_list
    
    @classmethod
    def get_admin_role(cls):
        """Get or create admin role"""
        admin_role = cls.query.filter_by(slug='admin').first()
        if not admin_role:
            admin_role = cls(
                name='مدیر کل',
                slug='admin',
                description='دسترسی کامل به سیستم',
                permissions='all'
            )
            admin_role.save()
        return admin_role
    
    @classmethod
    def get_user_role(cls):
        """Get or create user role"""
        user_role = cls.query.filter_by(slug='user').first()
        if not user_role:
            user_role = cls(
                name='کاربر',
                slug='user',
                description='دسترسی کاربر عادی',
                permissions='read'
            )
            user_role.save()
        return user_role
    
    def __repr__(self):
        return f'<Role {self.name}>'


class Permission(BaseModel, TimestampMixin):
    """Permission Model"""
    
    __tablename__ = 'permissions'
    
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    group = db.Column(db.String(100), nullable=True)
    
    # Relationships
    role_id = db.Column(db.Integer, ForeignKey('roles.id'), nullable=True)
    role = relationship('Role', back_populates='permissions_rel')
    
    def __repr__(self):
        return f'<Permission {self.name}>'


class User(BaseModel, TimestampMixin, SoftDeleteMixin, UserMixin):
    """User Model"""
    
    __tablename__ = 'users'
    
    email = db.Column(db.String(255), unique=True, nullable=True, index=True)
    username = db.Column(db.String(100), unique=True, nullable=True, index=True)
    phone = db.Column(db.String(20), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    avatar = db.Column(db.String(500), nullable=True)
    national_code = db.Column(db.String(10), nullable=True)
    
    # Status
    role_id = db.Column(db.Integer, ForeignKey('roles.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_subscribed = db.Column(db.Boolean, default=False, nullable=False)
    
    # Verification
    email_verified_at = db.Column(db.DateTime, nullable=True)
    phone_verified_at = db.Column(db.DateTime, nullable=True)
    verification_token = db.Column(db.String(255), nullable=True)
    reset_token = db.Column(db.String(255), nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)
    
    # Login tracking
    last_login = db.Column(db.DateTime, nullable=True)
    login_count = db.Column(db.Integer, default=0)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    
    # OAuth
    oauth_provider = db.Column(db.String(50), nullable=True)
    oauth_uid = db.Column(db.String(255), nullable=True)
    
    # Relationships
    role = relationship('Role', back_populates='users')
    addresses = relationship('Address', back_populates='user', lazy='dynamic')
    orders = relationship('Order', back_populates='user', lazy='dynamic')
    cart_items = relationship('CartItem', back_populates='user', lazy='dynamic')
    wishlists = relationship('Wishlist', back_populates='user', lazy='dynamic')
    comparisons = relationship('Comparison', back_populates='user', lazy='dynamic')
    resumes = relationship('Resume', foreign_keys='Resume.user_id', back_populates='user', lazy='dynamic')
    contacts = relationship('Contact', foreign_keys='Contact.user_id', back_populates='user', lazy='dynamic')
    notifications = relationship('Notification', back_populates='user', lazy='dynamic')
    comments = relationship('Comment', foreign_keys='Comment.user_id', back_populates='user', lazy='dynamic')
    meta = relationship('UserMeta', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        parts = [self.first_name, self.last_name]
        return ' '.join(p for p in parts if p) or self.username or self.email or f'کاربر {self.id}'
    
    @property
    def display_name(self) -> str:
        """Get display name"""
        return self.full_name
    
    def set_password(self, password: str) -> None:
        """Hash and set password"""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password: str) -> bool:
        """Check password against hash"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def generate_verification_token(self) -> str:
        """Generate email verification token"""
        self.verification_token = secrets.token_urlsafe(32)
        db.session.commit()
        return self.verification_token
    
    def generate_reset_token(self) -> str:
        """Generate password reset token"""
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expires = datetime.utcnow() + timedelta(hours=24)
        db.session.commit()
        return self.reset_token
    
    def update_last_login(self) -> None:
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        self.login_count += 1
        db.session.commit()
    
    def is_locked(self) -> bool:
        """Check if account is locked"""
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False
    
    def lock_account(self, minutes: int = 30) -> None:
        """Lock account for specified minutes"""
        self.locked_until = datetime.utcnow() + timedelta(minutes=minutes)
        db.session.commit()
    
    def unlock_account(self) -> None:
        """Unlock account"""
        self.locked_until = None
        self.failed_login_attempts = 0
        db.session.commit()
    
    def can(self, permission: str) -> bool:
        """Check if user has permission"""
        if not self.role:
            return False
        return self.role.has_permission(permission)
    
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role and self.role.slug == 'admin'
    
    def is_active_user(self) -> bool:
        """Check if user is active and not locked"""
        return self.is_active and not self.is_locked()
    
    def get_meta(self, key: str, default=None):
        """Get user meta value"""
        meta = UserMeta.query.filter_by(user_id=self.id, meta_key=key).first()
        return meta.meta_value if meta else default
    
    def set_meta(self, key: str, value: str) -> None:
        """Set user meta value"""
        meta = UserMeta.query.filter_by(user_id=self.id, meta_key=key).first()
        if meta:
            meta.meta_value = value
        else:
            meta = UserMeta(user_id=self.id, meta_key=key, meta_value=value)
            db.session.add(meta)
        db.session.commit()
    
    def __repr__(self):
        return f'<User {self.email or self.id}>'


class UserMeta(BaseModel, TimestampMixin):
    """User Meta Model for storing additional user data"""
    
    __tablename__ = 'user_meta'
    
    user_id = db.Column(db.Integer, ForeignKey('users.id'), nullable=False, index=True)
    meta_key = db.Column(db.String(255), nullable=False, index=True)
    meta_value = db.Column(db.Text, nullable=True)
    
    # Relationships
    user = relationship('User', back_populates='meta')
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('user_id', 'meta_key', name='unique_user_meta'),
    )
    
    def __repr__(self):
        return f'<UserMeta {self.user_id}:{self.meta_key}>'


class Address(BaseModel, TimestampMixin, SoftDeleteMixin, ActiveMixin):
    """User Address Model"""
    
    __tablename__ = 'addresses'
    
    user_id = db.Column(db.Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    title = db.Column(db.String(100), nullable=False)  # مثلاً: خانه، محل کار
    recipient_name = db.Column(db.String(100), nullable=True)
    recipient_phone = db.Column(db.String(20), nullable=True)
    
    province = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    district = db.Column(db.String(100), nullable=True)
    postal_code = db.Column(db.String(10), nullable=True)
    address = db.Column(db.Text, nullable=False)
    
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    delivery_instructions = db.Column(db.Text, nullable=True)
    
    # Relationships
    user = relationship('User', back_populates='addresses')
    orders = relationship('Order', back_populates='shipping_address')
    
    @property
    def full_address(self) -> str:
        """Get full address string"""
        parts = [self.address]
        if self.district:
            parts.insert(0, self.district)
        parts.insert(0, f'{self.city}، {self.province}')
        return '، '.join(parts)
    
    def set_as_default(self) -> None:
        """Set this as default address"""
        Address.query.filter_by(user_id=self.user_id).update({'is_default': False})
        self.is_default = True
        db.session.commit()
    
    def __repr__(self):
        return f'<Address {self.title}>'


# Import timedelta for lock_account
from datetime import timedelta
