"""
User and Authentication Service Layer
Production-ready services encapsulating all business logic for authentication,
user profile lifecycle, OTP verification, addresses, and customer relations.
Strictly adheres to SQLAlchemy 2.0 standards, type annotations, and secure input sanitization.
"""
from __future__ import annotations

import logging
import re
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import bleach
from flask import current_app
from sqlalchemy import func, or_, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload, selectinload

from app.constants import (
    EMAIL_PATTERN,
    Limits,
    PHONE_LANDLINE_IR,
    PHONE_PATTERN_IR,
)
from app.extensions import db
from app.models.order import CartItem, Comparison, Order, Wishlist
from app.models.product import Product
from app.models.user import Address, Role, User
from app.services.cart_service import CartService
from app.services.sms_service import SmsService

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication and Security operations service."""

    OTP_EXPIRY_MINUTES = 3
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15

    @classmethod
    def authenticate(
        cls,
        identifier: str,
        password: str,
    ) -> Tuple[bool, Optional[User], str]:
        """
        Authenticate a user by email or phone number.

        Applies account lockout protection against brute-force attacks and
        resets failed attempts upon successful authentication.

        Returns:
            Tuple of (is_successful, user_instance, error_or_success_message).
        """
        clean_id = (identifier or "").strip().lower()
        if not clean_id or not password:
            return False, None, "لطفاً ایمیل/شماره موبایل و رمز عبور را وارد کنید."

        try:
            stmt = (
                select(User)
                .where(
                    or_(User.email == clean_id, User.phone == clean_id),
                    User.is_deleted.is_(False),
                )
                .options(joinedload(User.role))
            )
            user = db.session.execute(stmt).scalars().first()

            if not user:
                # Avoid username enumeration by returning a generic error
                return False, None, "ایمیل یا رمز عبور اشتباه است."

            if user.is_locked():
                return False, None, "حساب شما به‌دلیل تلاش‌های ناموفق مکرر قفل شده است. لطفاً بعداً تلاش کنید."

            if not user.check_password(password):
                user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
                if user.failed_login_attempts >= cls.MAX_FAILED_ATTEMPTS:
                    user.lock_account(minutes=cls.LOCKOUT_DURATION_MINUTES)
                    msg = f"به‌دلیل {cls.MAX_FAILED_ATTEMPTS} تلاش ناموفق، حساب شما به‌مدت {cls.LOCKOUT_DURATION_MINUTES} دقیقه قفل شد."
                else:
                    rem = cls.MAX_FAILED_ATTEMPTS - user.failed_login_attempts
                    msg = f"ایمیل یا رمز عبور اشتباه است. {rem} تلاش دیگر باقی مانده است."
                db.session.commit()
                return False, None, msg

            if not user.is_active:
                return False, None, "حساب کاربری شما غیرفعال است. لطفاً با پشتیبانی تماس بگیرید."

            # Successful login state cleanup
            user.failed_login_attempts = 0
            user.locked_until = None
            user.update_last_login()
            db.session.commit()

            return True, user, f"خوش آمدید {user.full_name}!"
        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Database error during authentication: %s", exc, exc_info=True)
            return False, None, "خطای پایگاه داده در فرایند ورود. لطفاً مجدداً تلاش کنید."

    @classmethod
    def register_user(
        cls,
        email: str,
        phone: str,
        first_name: str,
        last_name: str,
        password: str,
        confirm_password: str,
    ) -> Tuple[bool, Optional[User], List[str]]:
        """
        Validate and register a new standard user in the system.

        Performs strict input validation, uniqueness checks, and assigns the default 'user' role.
        """
        errors: List[str] = []
        clean_email = (email or "").strip().lower()
        clean_phone = (phone or "").strip()
        clean_first_name = bleach.clean((first_name or "").strip())
        clean_last_name = bleach.clean((last_name or "").strip())

        # Validations
        if not clean_email or not re.match(EMAIL_PATTERN, clean_email):
            errors.append("فرمت ایمیل نامعتبر است.")

        if not clean_phone or not re.match(PHONE_PATTERN_IR, clean_phone):
            errors.append("شماره موبایل باید با ۰۹ شروع شده و ۱۱ رقم باشد.")

        if len(clean_first_name) < Limits.NAME_MIN or len(clean_first_name) > Limits.NAME_MAX:
            errors.append(f"نام باید بین {Limits.NAME_MIN} تا {Limits.NAME_MAX} کاراکتر باشد.")

        if clean_last_name and (len(clean_last_name) < Limits.NAME_MIN or len(clean_last_name) > Limits.NAME_MAX):
            errors.append(f"نام خانوادگی باید بین {Limits.NAME_MIN} تا {Limits.NAME_MAX} کاراکتر باشد.")

        if len(password or "") < Limits.PASSWORD_MIN:
            errors.append(f"رمز عبور باید حداقل {Limits.PASSWORD_MIN} کاراکتر باشد.")

        if password != confirm_password:
            errors.append("رمز عبور با تکرار آن همخوانی ندارد.")

        if errors:
            return False, None, errors

        try:
            # Check unique email
            email_exists = db.session.execute(
                select(User.id).where(User.email == clean_email, User.is_deleted.is_(False))
            ).scalar()
            if email_exists:
                return False, None, ["این ایمیل قبلاً ثبت شده است."]

            # Check unique phone
            phone_exists = db.session.execute(
                select(User.id).where(User.phone == clean_phone, User.is_deleted.is_(False))
            ).scalar()
            if phone_exists:
                return False, None, ["این شماره موبایل قبلاً ثبت شده است."]

            # Get user role
            user_role = Role.get_user_role()

            new_user = User(
                email=clean_email,
                phone=clean_phone,
                first_name=clean_first_name,
                last_name=clean_last_name,
                role_id=user_role.id if user_role else None,
                is_active=True,
                is_verified=False,
            )
            new_user.set_password(password)

            db.session.add(new_user)
            db.session.commit()
            logger.info("Successfully registered new user id=%s (%s)", new_user.id, clean_email)
            return True, new_user, []
        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Failed to register user: %s", exc, exc_info=True)
            return False, None, ["خطا در ارتباط با دیتابیس در هنگام ثبت‌نام."]

    @classmethod
    def request_otp(cls, phone: str) -> Tuple[bool, str]:
        """
        Generate and dispatch a temporary SMS OTP code to the provided phone number.

        Uses the configured SmsService driver with rate limiting support.
        """
        clean_phone = (phone or "").strip()
        if not clean_phone or not re.match(PHONE_PATTERN_IR, clean_phone):
            return False, "شماره موبایل نامعتبر است."

        code = str(secrets.randbelow(90000) + 10000)  # 5-digit cryptographic OTP

        try:
            # Find or instantiate user meta / verification token
            stmt = select(User).where(User.phone == clean_phone, User.is_deleted.is_(False))
            user = db.session.execute(stmt).scalars().first()

            if user:
                user.verification_token = code
                user.reset_token_expires = datetime.utcnow() + timedelta(minutes=cls.OTP_EXPIRY_MINUTES)
                db.session.commit()
            else:
                # Storing temporary OTP for non-registered phone in user meta or session
                # If user doesn't exist yet, we can create an unverified placeholder or handle via cache
                user_role = Role.get_user_role()
                user = User(
                    phone=clean_phone,
                    password_hash=secrets.token_urlsafe(16),
                    first_name="کاربر",
                    last_name="جدید",
                    role_id=user_role.id if user_role else None,
                    is_active=True,
                    is_verified=False,
                    verification_token=code,
                    reset_token_expires=datetime.utcnow() + timedelta(minutes=cls.OTP_EXPIRY_MINUTES),
                )
                db.session.add(user)
                db.session.commit()

            # Send OTP via SMS Service
            sent, detail = SmsService.send_otp(clean_phone, code, minutes=cls.OTP_EXPIRY_MINUTES)
            if not sent:
                logger.warning("Failed to send OTP to %s: %s", clean_phone, detail)
                return False, "خطا در ارسال پیامک کد تأیید. لطفاً مجدداً تلاش کنید."

            return True, f"کد تأیید به شماره {clean_phone} پیامک شد."
        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Database failure while creating OTP for %s: %s", clean_phone, exc, exc_info=True)
            return False, "خطا در پردازش درخواست ورود با پیامک."

    @classmethod
    def verify_otp(cls, phone: str, code: str) -> Tuple[bool, Optional[User], str]:
        """
        Verify the submitted OTP against the registered phone number.
        """
        clean_phone = (phone or "").strip()
        clean_code = (code or "").strip()

        if not clean_phone or not clean_code:
            return False, None, "لطفاً شماره تماس و کد ارسال شده را وارد کنید."

        try:
            stmt = select(User).where(User.phone == clean_phone, User.is_deleted.is_(False))
            user = db.session.execute(stmt).scalars().first()

            if not user or not user.verification_token:
                return False, None, "کد تأیید یافت نشد یا منقضی شده است."

            if user.reset_token_expires and user.reset_token_expires < datetime.utcnow():
                user.verification_token = None
                user.reset_token_expires = None
                db.session.commit()
                return False, None, "کد تأیید منقضی شده است. لطفاً کد جدید درخواست کنید."

            if user.verification_token != clean_code:
                return False, None, "کد تأیید وارد شده صحیح نمی‌باشد."

            # Code is valid
            user.verification_token = None
            user.reset_token_expires = None
            user.is_verified = True
            user.phone_verified_at = datetime.utcnow()
            user.update_last_login()
            db.session.commit()

            return True, user, "ورود با موفقیت انجام شد."
        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Error during OTP verification for %s: %s", clean_phone, exc, exc_info=True)
            return False, None, "خطا در تأیید کد یکبار مصرف."


class UserService:
    """Business operations for user profile, address book, and account management."""

    @staticmethod
    def get_by_id(user_id: int) -> Optional[User]:
        """Retrieve a non-deleted user by primary key with role eagerly loaded."""
        try:
            stmt = (
                select(User)
                .where(User.id == user_id, User.is_deleted.is_(False))
                .options(joinedload(User.role))
            )
            return db.session.execute(stmt).scalars().first()
        except SQLAlchemyError as exc:
            logger.error("Failed to query user by id %s: %s", user_id, exc, exc_info=True)
            return None

    @staticmethod
    def get_dashboard_stats(user_id: int) -> Dict[str, int]:
        """
        Gather dashboard counters for a user using efficient aggregate queries.
        """
        stats = {
            "orders_count": 0,
            "wishlist_count": 0,
            "compare_count": 0,
            "cart_count": 0,
            "unread_notifications": 0,
        }
        try:
            # Orders count
            orders_stmt = select(func.count(Order.id)).where(Order.user_id == user_id)
            stats["orders_count"] = db.session.execute(orders_stmt).scalar() or 0

            # Wishlist count
            wish_stmt = select(func.count(Wishlist.id)).where(Wishlist.user_id == user_id)
            stats["wishlist_count"] = db.session.execute(wish_stmt).scalar() or 0

            # Comparison count
            comp_stmt = select(func.count(Comparison.id)).where(Comparison.user_id == user_id)
            stats["compare_count"] = db.session.execute(comp_stmt).scalar() or 0

            # Cart items count
            cart_stmt = select(func.coalesce(func.sum(CartItem.quantity), 0)).where(
                CartItem.user_id == user_id, CartItem.is_deleted.is_(False)
            )
            stats["cart_count"] = int(db.session.execute(cart_stmt).scalar() or 0)
        except SQLAlchemyError as exc:
            logger.error("Error gathering dashboard stats for user %s: %s", user_id, exc, exc_info=True)

        return stats

    @staticmethod
    def update_profile(
        user: User,
        first_name: str,
        last_name: str,
        national_code: Optional[str] = None,
    ) -> Tuple[bool, List[str]]:
        """
        Update basic profile information with input sanitization.
        """
        errors: List[str] = []
        clean_first = bleach.clean((first_name or "").strip())
        clean_last = bleach.clean((last_name or "").strip())
        clean_nc = (national_code or "").strip()

        if len(clean_first) < Limits.NAME_MIN or len(clean_first) > Limits.NAME_MAX:
            errors.append(f"نام باید بین {Limits.NAME_MIN} تا {Limits.NAME_MAX} نویسه باشد.")

        if clean_last and (len(clean_last) < Limits.NAME_MIN or len(clean_last) > Limits.NAME_MAX):
            errors.append(f"نام خانوادگی باید بین {Limits.NAME_MIN} تا {Limits.NAME_MAX} نویسه باشد.")

        if clean_nc and not re.match(r"^\d{10}$", clean_nc):
            errors.append("کد ملی باید یک عدد ۱۰ رقمی معتبر باشد.")

        if errors:
            return False, errors

        try:
            user.first_name = clean_first
            user.last_name = clean_last
            if clean_nc:
                user.national_code = clean_nc
            db.session.commit()
            return True, []
        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Failed to update profile for user %s: %s", user.id, exc, exc_info=True)
            return False, ["خطا در ذخیره‌سازی اطلاعات پروفایل."]

    @staticmethod
    def change_password(
        user: User,
        current_password: str,
        new_password: str,
        confirm_password: str,
    ) -> Tuple[bool, str]:
        """
        Safely update user's password verifying old credentials first.
        """
        if not user.check_password(current_password):
            return False, "رمز عبور فعلی نادرست است."

        if len(new_password or "") < Limits.PASSWORD_MIN:
            return False, f"رمز عبور جدید باید حداقل {Limits.PASSWORD_MIN} کاراکتر باشد."

        if new_password != confirm_password:
            return False, "رمز عبور جدید با تکرار آن تطابق ندارد."

        try:
            user.set_password(new_password)
            db.session.commit()
            return True, "رمز عبور با موفقیت به‌روزرسانی شد."
        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Password update error for user %s: %s", user.id, exc, exc_info=True)
            return False, "خطا در تغییر رمز عبور. لطفاً مجدداً امتحان کنید."

    # ==================== ADDRESS MANAGEMENT ====================

    @staticmethod
    def get_user_addresses(user_id: int) -> List[Address]:
        """Retrieve all active addresses for a user ordered by default first."""
        try:
            stmt = (
                select(Address)
                .where(
                    Address.user_id == user_id,
                    Address.is_deleted.is_(False),
                    Address.is_active.is_(True),
                )
                .order_by(Address.is_default.desc(), Address.created_at.desc())
            )
            return list(db.session.execute(stmt).scalars().all())
        except SQLAlchemyError as exc:
            logger.error("Failed loading addresses for user %s: %s", user_id, exc, exc_info=True)
            return []

    @staticmethod
    def save_address(
        user_id: int,
        data: Dict[str, Any],
        address_id: Optional[int] = None,
    ) -> Tuple[bool, Optional[Address], List[str]]:
        """
        Create or update a customer address with validation.
        """
        errors: List[str] = []
        title = bleach.clean((data.get("title") or "").strip())
        recipient_name = bleach.clean((data.get("recipient_name") or "").strip())
        recipient_phone = (data.get("recipient_phone") or "").strip()
        province = bleach.clean((data.get("province") or "").strip())
        city = bleach.clean((data.get("city") or "").strip())
        address_text = bleach.clean((data.get("address") or "").strip())
        postal_code = (data.get("postal_code") or "").strip()
        is_default = bool(data.get("is_default"))

        if not title:
            errors.append("عنوان آدرس (مانند منزل یا محل کار) الزامی است.")
        if not province or not city:
            errors.append("انتخاب استان و شهر الزامی است.")
        if not address_text or len(address_text) < 10:
            errors.append("نشانی پستی باید حداقل ۱۰ نویسه باشد.")
        if recipient_phone and not re.match(PHONE_PATTERN_IR, recipient_phone):
            errors.append("شماره تماس تحویل‌گیرنده نامعتبر است.")
        if postal_code and not re.match(r"^\d{10}$", postal_code):
            errors.append("کد پستی باید ۱۰ رقم باشد.")

        if errors:
            return False, None, errors

        try:
            # Handle default address flag
            if is_default:
                db.session.execute(
                    update(Address)
                    .where(Address.user_id == user_id)
                    .values(is_default=False)
                )

            if address_id:
                stmt = select(Address).where(
                    Address.id == address_id,
                    Address.user_id == user_id,
                    Address.is_deleted.is_(False),
                )
                addr = db.session.execute(stmt).scalars().first()
                if not addr:
                    return False, None, ["آدرس مورد نظر یافت نشد."]
            else:
                addr = Address(user_id=user_id)
                db.session.add(addr)

            addr.title = title
            addr.recipient_name = recipient_name
            addr.recipient_phone = recipient_phone
            addr.province = province
            addr.city = city
            addr.address = address_text
            addr.postal_code = postal_code
            addr.is_default = is_default

            db.session.commit()
            return True, addr, []
        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Failed saving address for user %s: %s", user_id, exc, exc_info=True)
            return False, None, ["خطا در ثبت اطلاعات آدرس."]

    @staticmethod
    def delete_address(address_id: int, user_id: int) -> bool:
        """Soft-delete an address belonging to a user."""
        try:
            stmt = select(Address).where(
                Address.id == address_id,
                Address.user_id == user_id,
                Address.is_deleted.is_(False),
            )
            addr = db.session.execute(stmt).scalars().first()
            if addr:
                addr.is_deleted = True
                db.session.commit()
                return True
            return False
        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Failed deleting address %s: %s", address_id, exc, exc_info=True)
            return False

    @staticmethod
    def set_default_address(address_id: int, user_id: int) -> bool:
        """Set a selected address as the primary/default shipping address."""
        try:
            db.session.execute(
                update(Address)
                .where(Address.user_id == user_id)
                .values(is_default=False)
            )
            stmt = select(Address).where(
                Address.id == address_id,
                Address.user_id == user_id,
                Address.is_deleted.is_(False),
            )
            addr = db.session.execute(stmt).scalars().first()
            if addr:
                addr.is_default = True
                db.session.commit()
                return True
            return False
        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Failed to set default address %s: %s", address_id, exc, exc_info=True)
            return False

    # ==================== WISHLIST & COMPARISON ====================

    @staticmethod
    def toggle_wishlist(user_id: int, product_id: int) -> Tuple[bool, str, bool]:
        """
        Toggle product in user's wishlist.
        Returns (success: bool, message: str, is_now_in_wishlist: bool).
        """
        try:
            product = db.session.get(Product, product_id)
            if not product or product.is_deleted:
                return False, "محصول یافت نشد.", False

            stmt = select(Wishlist).where(
                Wishlist.user_id == user_id,
                Wishlist.product_id == product_id,
            )
            item = db.session.execute(stmt).scalars().first()

            if item:
                db.session.delete(item)
                db.session.commit()
                return True, "محصول از لیست علاقه‌مندی‌ها حذف شد.", False
            else:
                new_item = Wishlist(user_id=user_id, product_id=product_id)
                db.session.add(new_item)
                db.session.commit()
                return True, "محصول به لیست علاقه‌مندی‌ها اضافه شد.", True
        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Failed toggling wishlist for user %s, product %s: %s", user_id, product_id, exc, exc_info=True)
            return False, "خطا در پردازش لیست علاقه‌مندی‌ها.", False

    @staticmethod
    def toggle_comparison(user_id: int, product_id: int) -> Tuple[bool, str, bool]:
        """
        Add or remove product from comparison list (max 4 products).
        """
        try:
            product = db.session.get(Product, product_id)
            if not product or product.is_deleted:
                return False, "محصول مورد نظر معتبر نیست.", False

            stmt = select(Comparison).where(
                Comparison.user_id == user_id,
                Comparison.product_id == product_id,
            )
            existing = db.session.execute(stmt).scalars().first()

            if existing:
                db.session.delete(existing)
                db.session.commit()
                return True, "محصول از لیست مقایسه حذف شد.", False

            count_stmt = select(func.count(Comparison.id)).where(Comparison.user_id == user_id)
            current_count = db.session.execute(count_stmt).scalar() or 0
            if current_count >= 4:
                return False, "حداکثر می‌توانید ۴ کالا را همزمان مقایسه کنید.", False

            new_comp = Comparison(user_id=user_id, product_id=product_id)
            db.session.add(new_comp)
            db.session.commit()
            return True, "محصول به لیست مقایسه اضافه شد.", True
        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Failed toggling comparison for user %s, product %s: %s", user_id, product_id, exc, exc_info=True)
            return False, "خطا در پردازش لیست مقایسه.", False
