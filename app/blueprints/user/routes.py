"""
User Blueprint Routes
Presentation layer for user portal, account lifecycle, order history,
address management, customer support tickets, and AJAX endpoints.
Routes strictly handle HTTP parsing, calling Service layers, and rendering responses.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from flask import (
    Response,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.blueprints.user import user_bp
from app.extensions import db
from app.models.features import OtpCode, Ticket, TicketMessage
from app.models.menu import Notification, Resume
from app.models.order import Comparison, Order, Wishlist
from app.models.product import Product
from app.models.user import Address, User
from app.services.cart_service import CartService
from app.services.notification_service import NotificationService
from app.services.order_service import OrderService
from app.services.ticket_file_service import attachment_path, save_ticket_attachment
from app.services.user_service import AuthService, UserService
from app.utils.decorators import rate_limit

logger = logging.getLogger(__name__)


# ==================== DASHBOARD ====================

@user_bp.route('/')
@user_bp.route('/dashboard')
@login_required
def dashboard() -> str:
    """User dashboard view displaying summary statistics and recent orders."""
    stats = UserService.get_dashboard_stats(current_user.id)
    recent_orders, _ = OrderService.get_user_orders(current_user.id, page=1, per_page=5)

    # Unread notifications count
    unread_stmt = select(Notification).where(
        Notification.user_id == current_user.id,
        Notification.is_read.is_(False),
    )
    unread_notifications = len(db.session.execute(unread_stmt).scalars().all())

    return render_template(
        'user/dashboard.html',
        stats=stats,
        recent_orders=recent_orders,
        unread_notifications=unread_notifications,
    )


# ==================== AUTHENTICATION ====================

@user_bp.route('/login', methods=['GET', 'POST'])
@rate_limit(limit=10, period=900, key_func=lambda: f'login:{request.remote_addr}')
def login() -> Response | str:
    """User login endpoint delegating credential checks to AuthService."""
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))

    if request.method == 'POST':
        identifier = (request.form.get('email') or '').strip()
        password = request.form.get('password') or ''
        remember = bool(request.form.get('remember'))

        success, user, message = AuthService.authenticate(identifier, password)

        if not success or not user:
            flash(message, 'error')
            return render_template('user/auth/login.html')

        login_user(user, remember=remember)

        # Merge session cart into persistent user cart
        try:
            CartService.merge_carts(CartService.get_session_id(), user.id)
        except Exception as exc:
            logger.warning("Failed to merge guest cart on login: %s", exc)

        flash(message, 'success')

        next_page = request.args.get('next', '')
        if next_page and next_page.startswith('/') and not next_page.startswith('//'):
            return redirect(next_page)
        return redirect(url_for('user.dashboard'))

    return render_template('user/auth/login.html')


@user_bp.route('/register', methods=['GET', 'POST'])
@rate_limit(limit=5, period=3600, key_func=lambda: f'register:{request.remote_addr}')
def register() -> Response | str:
    """User registration view validating credentials via AuthService."""
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))

    if request.method == 'POST':
        email = (request.form.get('email') or '').strip()
        phone = (request.form.get('phone') or '').strip()
        first_name = (request.form.get('first_name') or '').strip()
        last_name = (request.form.get('last_name') or '').strip()
        password = request.form.get('password') or ''
        confirm_password = request.form.get('confirm_password') or ''

        success, user, errors = AuthService.register_user(
            email=email,
            phone=phone,
            first_name=first_name,
            last_name=last_name,
            password=password,
            confirm_password=confirm_password,
        )

        if not success or not user:
            for error in errors:
                flash(error, 'error')
            return render_template('user/auth/register.html')

        login_user(user)

        # Merge guest cart
        try:
            CartService.merge_carts(CartService.get_session_id(), user.id)
        except Exception as exc:
            logger.warning("Failed merging cart during registration: %s", exc)

        flash(f'ثبت‌نام با موفقیت انجام شد. خوش آمدید {user.full_name}!', 'success')
        return redirect(url_for('user.dashboard'))

    return render_template('user/auth/register.html')


@user_bp.route('/logout')
@login_required
def logout() -> Response:
    """Clear user session and log out."""
    logout_user()
    flash('با موفقیت خارج شدید.', 'success')
    return redirect(url_for('public.home'))


@user_bp.route('/forgot-password', methods=['GET', 'POST'])
@rate_limit(limit=3, period=3600, key_func=lambda: f'forgot:{request.remote_addr}')
def forgot_password() -> Response | str:
    """Request a password reset link."""
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))

    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        if not email:
            flash('لطفاً ایمیل خود را وارد کنید.', 'error')
            return render_template('user/auth/forgot_password.html')

        stmt = select(User).where(User.email == email, User.is_deleted.is_(False))
        user = db.session.execute(stmt).scalars().first()

        if user:
            try:
                token = user.generate_reset_token()
                reset_url = url_for('user.reset_password', token=token, _external=True)
                NotificationService.send_password_reset(user, reset_url)
            except Exception as exc:
                logger.error("Failed dispatching password reset email: %s", exc, exc_info=True)
                flash('خطا در ارسال ایمیل بازیابی. لطفاً بعداً تلاش فرمایید.', 'error')
                return render_template('user/auth/forgot_password.html')

        flash('در صورت صحت ایمیل، پیوند بازیابی برای شما ارسال گردید.', 'success')
        return redirect(url_for('user.login'))

    return render_template('user/auth/forgot_password.html')


@user_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token: str) -> Response | str:
    """Reset password using cryptographic URL token."""
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))

    stmt = select(User).where(User.reset_token == token, User.is_deleted.is_(False))
    user = db.session.execute(stmt).scalars().first()

    if not user or not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
        flash('پیوند بازیابی رمز عبور نامعتبر یا منقضی شده است.', 'error')
        return redirect(url_for('user.forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not new_password or len(new_password) < 8:
            flash('رمز عبور باید حداقل ۸ کاراکتر باشد.', 'error')
            return render_template('user/auth/reset_password.html', token=token, valid=True)

        if new_password != confirm_password:
            flash('رمز عبور جدید با تکرار آن تطابق ندارد.', 'error')
            return render_template('user/auth/reset_password.html', token=token, valid=True)

        try:
            user.set_password(new_password)
            user.reset_token = None
            user.reset_token_expires = None
            user.unlock_account()
            db.session.commit()
            flash('رمز عبور با موفقیت تغییر کرد. اکنون می‌توانید وارد شوید.', 'success')
            return redirect(url_for('user.login'))
        except Exception as exc:
            db.session.rollback()
            logger.error("Failed committing password reset: %s", exc, exc_info=True)
            flash('خطا در ثبت رمز عبور جدید.', 'error')

    return render_template('user/auth/reset_password.html', token=token, valid=True)


@user_bp.route('/otp-login', methods=['GET', 'POST'])
@rate_limit(limit=12, period=900, key_func=lambda: f'otp:{request.remote_addr}')
def otp_login() -> Response | str:
    """Mobile phone SMS OTP login and rapid registration flow."""
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))

    step = request.form.get('step', 'request')

    if request.method == 'POST' and step == 'request':
        phone = OtpCode.normalize_phone(request.form.get('phone', ''))
        if not OtpCode.is_valid_phone(phone):
            flash('شماره موبایل معتبر نیست (مثال: 09123456789).', 'error')
            return render_template('user/auth/otp_login.html', step='request', phone=phone)

        try:
            otp = OtpCode.issue(phone, purpose='login', ip=request.remote_addr)
            from app.services.sms_service import SmsService
            sent, detail = SmsService.send_otp(phone, otp._plain_code, OtpCode.TTL_MINUTES)
            dev_code = otp._plain_code if (SmsService.driver() == 'console' and current_app.debug) else None

            if not sent:
                flash('ارسال پیامک ناموفق بود؛ لطفاً بعداً تلاش فرمایید.', 'error')
                return render_template('user/auth/otp_login.html', step='request', phone=phone)

            session['otp_phone'] = phone
            flash('کد تأیید به شماره همراه شما ارسال شد.', 'success')
            return render_template('user/auth/otp_login.html', step='verify', phone=phone, dev_code=dev_code)
        except ValueError as exc:
            flash(str(exc), 'warning')
            return render_template('user/auth/otp_login.html', step='request', phone=phone)

    if request.method == 'POST' and step == 'verify':
        phone = OtpCode.normalize_phone(request.form.get('phone', '') or session.get('otp_phone', ''))
        code = (request.form.get('code') or '').strip()

        otp = OtpCode.latest_for(phone, purpose='login')
        if not otp or not otp.verify(code):
            flash('کد وارد شده صحیح نیست یا منقضی شده است.', 'error')
            return render_template('user/auth/otp_login.html', step='verify', phone=phone)

        stmt = select(User).where(User.phone == phone, User.is_deleted.is_(False))
        user = db.session.execute(stmt).scalars().first()

        created = False
        if not user:
            from app.models.user import Role
            user_role = Role.get_user_role()
            user = User(
                phone=phone,
                username=f'u{phone[1:]}',
                first_name='کاربر',
                last_name='گرامی',
                role_id=user_role.id if user_role else None,
                is_active=True,
                is_verified=True,
                phone_verified_at=datetime.utcnow(),
            )
            user.set_password(code)
            db.session.add(user)
            db.session.commit()
            created = True
        else:
            if not user.phone_verified_at:
                user.phone_verified_at = datetime.utcnow()
            if not user.is_active:
                flash('حساب کاربری شما غیرفعال است.', 'warning')
                return render_template('user/auth/otp_login.html', step='request')

        login_user(user, remember=True)
        user.update_last_login()
        session.pop('otp_phone', None)

        try:
            CartService.merge_carts(CartService.get_session_id(), user.id)
        except Exception as exc:
            logger.warning("Cart merge failed during OTP login: %s", exc)

        flash(('حساب شما با موفقیت ساخته شد؛ ' if created else '') + f'خوش آمدید {user.full_name}!', 'success')
        return redirect(url_for('user.dashboard'))

    return render_template('user/auth/otp_login.html', step='request')


# ==================== PROFILE & CREDENTIALS ====================

@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile() -> Response | str:
    """User profile edit."""
    if request.method == 'POST':
        first_name = request.form.get('first_name') or ''
        last_name = request.form.get('last_name') or ''
        national_code = request.form.get('national_code')

        success, errors = UserService.update_profile(
            user=current_user,
            first_name=first_name,
            last_name=last_name,
            national_code=national_code,
        )

        if not success:
            for err in errors:
                flash(err, 'error')
        else:
            flash('اطلاعات کاربری با موفقیت به‌روزرسانی شد.', 'success')
        return redirect(url_for('user.profile'))

    return render_template('user/profile.html')


@user_bp.route('/profile/change-password', methods=['GET', 'POST'])
@login_required
@rate_limit(limit=5, period=3600, key_func=lambda: f'change_pw:{current_user.id}')
def change_password() -> Response | str:
    """Change user password enforcing current password verification."""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        success, message = UserService.change_password(
            user=current_user,
            current_password=current_password,
            new_password=new_password,
            confirm_password=confirm_password,
        )

        if not success:
            flash(message, 'error')
            return render_template('user/profile/change_password.html')

        flash(message, 'success')
        return redirect(url_for('user.profile'))

    return render_template('user/profile/change_password.html')


# ==================== ADDRESS BOOK ====================

@user_bp.route('/addresses')
@login_required
def addresses() -> str:
    """List customer shipping addresses."""
    addresses_list = UserService.get_user_addresses(current_user.id)
    return render_template('user/addresses.html', addresses=addresses_list)


@user_bp.route('/addresses/create', methods=['GET', 'POST'])
@user_bp.route('/addresses/<int:address_id>/edit', methods=['GET', 'POST'])
@login_required
def address_edit(address_id: Optional[int] = None) -> Response | str:
    """Create or update an address."""
    address = None
    if address_id:
        stmt = select(Address).where(
            Address.id == address_id,
            Address.user_id == current_user.id,
            Address.is_deleted.is_(False),
        )
        address = db.session.execute(stmt).scalars().first()
        if not address:
            abort(404)

    if request.method == 'POST':
        form_data = {
            'title': request.form.get('title'),
            'recipient_name': request.form.get('recipient_name'),
            'recipient_phone': request.form.get('recipient_phone'),
            'province': request.form.get('province'),
            'city': request.form.get('city'),
            'address': request.form.get('address'),
            'postal_code': request.form.get('postal_code'),
            'is_default': request.form.get('is_default') == '1',
        }

        success, _, errors = UserService.save_address(
            user_id=current_user.id,
            data=form_data,
            address_id=address_id,
        )

        if not success:
            for err in errors:
                flash(err, 'error')
            return render_template('user/address_edit.html', address=address)

        flash('آدرس با موفقیت ذخیره شد.', 'success')
        return redirect(url_for('user.addresses'))

    return render_template('user/address_edit.html', address=address)


@user_bp.route('/addresses/<int:address_id>/delete', methods=['POST'])
@login_required
def address_delete(address_id: int) -> Response:
    """Soft-delete an address."""
    if UserService.delete_address(address_id, current_user.id):
        flash('آدرس مورد نظر حذف گردید.', 'success')
    else:
        flash('خطا در حذف آدرس.', 'error')
    return redirect(url_for('user.addresses'))


@user_bp.route('/addresses/<int:address_id>/set-default', methods=['POST'])
@login_required
def address_set_default(address_id: int) -> Response:
    """Set address as default."""
    if UserService.set_default_address(address_id, current_user.id):
        flash('آدرس پیش‌فرض با موفقیت تغییر یافت.', 'success')
    else:
        flash('خطا در تنظیم آدرس پیش‌فرض.', 'error')
    return redirect(url_for('user.addresses'))


# ==================== ORDERS ====================

@user_bp.route('/orders')
@login_required
def orders() -> str:
    """User order history."""
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('ITEMS_PER_PAGE', 10)
    orders_list, total = OrderService.get_user_orders(current_user.id, page=page, per_page=per_page)

    return render_template('user/orders.html', orders=orders_list, total_orders=total)


@user_bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id: int) -> str:
    """Detailed view of an order."""
    order = OrderService.get_by_id(order_id)
    if not order or order.user_id != current_user.id:
        abort(404)

    return render_template('user/order_detail.html', order=order)


@user_bp.route('/orders/<int:order_id>/cancel', methods=['GET', 'POST'])
@login_required
def order_cancel(order_id: int) -> Response | str:
    """Cancel order and restore product stock."""
    order = OrderService.get_by_id(order_id)
    if not order or order.user_id != current_user.id:
        abort(404)

    if not order.can_cancel():
        flash('امکان لغو این سفارش در وضعیت فعلی وجود ندارد.', 'error')
        return redirect(url_for('user.order_detail', order_id=order_id))

    if request.method == 'POST':
        reason = request.form.get('reason', '')
        success, message = OrderService.cancel_order(order_id, user_id=current_user.id, reason=reason)
        if success:
            flash(message, 'success')
            return redirect(url_for('user.orders'))
        flash(message, 'error')

    return render_template('user/order_cancel.html', order=order)


# ==================== WISHLIST & COMPARISON ====================

@user_bp.route('/wishlist')
@login_required
def wishlist() -> str:
    """User wishlist view."""
    stmt = (
        select(Wishlist)
        .where(Wishlist.user_id == current_user.id)
        .options(selectinload(Wishlist.product))
    )
    wishlist_items = list(db.session.execute(stmt).scalars().all())
    return render_template('user/wishlist.html', wishlist_items=wishlist_items)


@user_bp.route('/wishlist/add/<int:product_id>', methods=['POST'])
@login_required
def wishlist_add(product_id: int) -> Response:
    """Add product to wishlist."""
    success, message, _ = UserService.toggle_wishlist(current_user.id, product_id)
    flash(message, 'success' if success else 'error')
    return redirect(request.referrer or url_for('user.wishlist'))


@user_bp.route('/wishlist/remove/<int:product_id>', methods=['POST'])
@login_required
def wishlist_remove(product_id: int) -> Response:
    """Remove product from wishlist."""
    success, message, _ = UserService.toggle_wishlist(current_user.id, product_id)
    flash(message, 'success' if success else 'error')
    return redirect(url_for('user.wishlist'))


@user_bp.route('/comparisons')
@login_required
def comparisons() -> str:
    """Products comparison view."""
    stmt = (
        select(Comparison)
        .where(Comparison.user_id == current_user.id)
        .options(selectinload(Comparison.product))
    )
    comps = list(db.session.execute(stmt).scalars().all())
    products = [c.product for c in comps if c.product and not c.product.is_deleted]
    return render_template('user/comparisons.html', products=products)


# ==================== NOTIFICATIONS ====================

@user_bp.route('/notifications')
@login_required
def notifications() -> str:
    """User notifications list."""
    stmt = (
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
    )
    notifications_list = list(db.session.execute(stmt).scalars().all())
    return render_template('user/notifications.html', notifications=notifications_list)


@user_bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def notification_read(notification_id: int) -> Response:
    """Mark a notification as read."""
    stmt = select(Notification).where(
        Notification.id == notification_id,
        Notification.user_id == current_user.id,
    )
    notif = db.session.execute(stmt).scalars().first()
    if notif:
        notif.is_read = True
        db.session.commit()
    return jsonify({'success': True})


@user_bp.route('/notifications/read-all', methods=['POST'])
@login_required
def notification_read_all() -> Response:
    """Mark all user notifications as read."""
    stmt = select(Notification).where(
        Notification.user_id == current_user.id,
        Notification.is_read.is_(False),
    )
    notifs = db.session.execute(stmt).scalars().all()
    for n in notifs:
        n.is_read = True
    db.session.commit()
    flash('همه اعلان‌ها به عنوان خوانده شده علامت‌گذاری شدند.', 'success')
    return redirect(url_for('user.notifications'))


# ==================== RESUMES ====================

@user_bp.route('/resumes', methods=['GET', 'POST'])
@login_required
def resumes() -> str:
    """Submitted job application resumes."""
    stmt = (
        select(Resume)
        .where(Resume.user_id == current_user.id, Resume.is_deleted.is_(False))
        .order_by(Resume.created_at.desc())
    )
    resumes_list = list(db.session.execute(stmt).scalars().all())
    return render_template('user/resumes.html', resumes=resumes_list)


# ==================== API ENDPOINTS ====================

@user_bp.route('/api/cart/add', methods=['POST'])
def api_cart_add() -> Response:
    """Asynchronous add to cart."""
    data = request.get_json() or {}
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1))

    if not product_id:
        return jsonify({'success': False, 'message': 'شناسه کالا نامعتبر است.'}), 400

    user_id = current_user.id if current_user.is_authenticated else None
    success = CartService.add_to_cart(product_id=product_id, quantity=quantity, user_id=user_id)
    cart_count = CartService.get_cart_count(user_id=user_id)

    return jsonify({
        'success': success,
        'cart_count': cart_count,
        'message': 'محصول به سبد خرید اضافه شد.' if success else 'خطا در افزودن کالا به سبد.',
    })


@user_bp.route('/api/cart/update', methods=['POST'])
def api_cart_update() -> Response:
    """Asynchronous cart quantity update."""
    data = request.get_json() or {}
    item_id = data.get('item_id')
    quantity = int(data.get('quantity', 1))

    if not item_id:
        return jsonify({'success': False, 'message': 'شناسه آیتم نامعتبر است.'}), 400

    user_id = current_user.id if current_user.is_authenticated else None
    success = CartService.update_cart_item(item_id=item_id, quantity=quantity, user_id=user_id)

    return jsonify({
        'success': success,
        'message': 'سبد خرید بروزرسانی شد.' if success else 'خطا در بروزرسانی سبد خرید.',
    })


@user_bp.route('/api/cart/remove', methods=['POST'])
def api_cart_remove() -> Response:
    """Asynchronous cart item removal."""
    data = request.get_json() or {}
    item_id = data.get('item_id')

    if not item_id:
        return jsonify({'success': False, 'message': 'شناسه آیتم نامعتبر است.'}), 400

    user_id = current_user.id if current_user.is_authenticated else None
    success = CartService.remove_from_cart(item_id=item_id, user_id=user_id)

    return jsonify({
        'success': success,
        'message': 'محصول از سبد حذف شد.' if success else 'خطا در حذف آیتم.',
    })


@user_bp.route('/api/wishlist/toggle', methods=['POST'])
@login_required
def api_wishlist_toggle() -> Response:
    """Toggle wishlist item asynchronously."""
    data = request.get_json() or {}
    product_id = data.get('product_id')
    if not product_id:
        return jsonify({'success': False, 'message': 'شناسه محصول الزامی است.'}), 400

    success, message, in_wishlist = UserService.toggle_wishlist(current_user.id, int(product_id))
    return jsonify({
        'success': success,
        'message': message,
        'in_wishlist': in_wishlist,
    })


@user_bp.route('/api/compare/add', methods=['POST'])
@login_required
def api_compare_add() -> Response:
    """Add product to comparison asynchronously."""
    data = request.get_json() or {}
    product_id = data.get('product_id')
    if not product_id:
        return jsonify({'success': False, 'message': 'شناسه محصول الزامی است.'}), 400

    success, message, in_comp = UserService.toggle_comparison(current_user.id, int(product_id))
    stats = UserService.get_dashboard_stats(current_user.id)
    return jsonify({
        'success': success,
        'message': message,
        'count': stats['compare_count'],
    })


# ==================== SUPPORT TICKETS ====================

@user_bp.route('/tickets')
@login_required
def tickets() -> str:
    """User support ticket list."""
    status = request.args.get('status', '')
    stmt = select(Ticket).where(
        Ticket.user_id == current_user.id,
        Ticket.is_deleted.is_(False),
    )
    if status:
        stmt = stmt.where(Ticket.status == status)

    stmt = stmt.order_by(Ticket.last_reply_at.desc())
    tickets_list = list(db.session.execute(stmt).scalars().all())

    return render_template('user/tickets/list.html', tickets=tickets_list, current_status=status)


@user_bp.route('/tickets/new', methods=['GET', 'POST'])
@login_required
@rate_limit(limit=10, period=3600, key_func=lambda: f'ticket_new:{current_user.id}')
def ticket_new() -> Response | str:
    """Create a new support ticket."""
    if request.method == 'POST':
        subject = (request.form.get('subject') or '').strip()
        message = (request.form.get('message') or '').strip()

        if len(subject) < 5 or len(message) < 10:
            flash('موضوع حداقل ۵ و متن حداقل ۱۰ کاراکتر باشد.', 'error')
            return render_template('user/tickets/new.html', form_data=request.form)

        ticket = Ticket(
            user_id=current_user.id,
            ticket_number=Ticket.generate_number(),
            subject=subject,
            department=request.form.get('department', 'general'),
            priority=request.form.get('priority', 'medium'),
        )
        ticket.save()

        attachment = None
        if 'attachment' in request.files:
            attachment, err = save_ticket_attachment(request.files['attachment'])
            if err:
                flash(f'تیکت ثبت شد اما خطا در پیوست: {err}', 'error')

        ticket.add_message(message, user_id=current_user.id, is_admin=False, attachment=attachment)

        NotificationService.notify_admins(
            title='تیکت پشتیبانی جدید',
            message=f'{current_user.full_name}: {subject}',
            type='message',
            data={'ticket_id': ticket.id},
        )

        flash('تیکت شما با موفقیت ثبت شد.', 'success')
        return redirect(url_for('user.ticket_detail', ticket_id=ticket.id))

    return render_template('user/tickets/new.html', form_data={})


@user_bp.route('/tickets/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def ticket_detail(ticket_id: int) -> Response | str:
    """View ticket discussion and post messages."""
    stmt = (
        select(Ticket)
        .where(Ticket.id == ticket_id)
    )
    ticket = db.session.execute(stmt).scalars().first()

    if not ticket or ticket.user_id != current_user.id:
        abort(404)

    if request.method == 'POST':
        action = request.form.get('action', 'reply')
        if action == 'reply' and ticket.status != 'closed':
            message = (request.form.get('message') or '').strip()
            attachment = None
            if 'attachment' in request.files:
                attachment, err = save_ticket_attachment(request.files['attachment'])
                if err:
                    flash(err, 'error')

            if message or attachment:
                ticket.add_message(message or '(پیوست)', user_id=current_user.id, is_admin=False, attachment=attachment)
                flash('پیام شما ثبت گردید.', 'success')
        elif action == 'close':
            ticket.close(by_user_id=current_user.id)
            flash('تیکت با موفقیت بسته شد.', 'success')
        elif action == 'reopen':
            ticket.reopen()
            flash('تیکت مجدداً بازگشایی شد.', 'success')

        return redirect(url_for('user.ticket_detail', ticket_id=ticket.id))

    return render_template('user/tickets/detail.html', ticket=ticket)


@user_bp.route('/tickets/message/<int:message_id>/attachment')
@login_required
def ticket_attachment_download(message_id: int) -> Response:
    """Download ticket attachment."""
    stmt = select(TicketMessage).where(TicketMessage.id == message_id)
    msg = db.session.execute(stmt).scalars().first()
    if not msg or not msg.ticket:
        abort(404)

    is_owner = msg.ticket.user_id == current_user.id
    try:
        is_admin = current_user.is_admin()
    except Exception:
        is_admin = False

    if not (is_owner or is_admin):
        abort(404)

    path = attachment_path(msg.attachment or '')
    if not path:
        abort(404)

    ext = path.rsplit('.', 1)[-1] if '.' in path else ''
    name = f'ticket-{msg.ticket.id}-msg-{msg.id}.{ext}' if ext else f'ticket-{msg.ticket.id}-msg-{msg.id}'
    return send_file(path, as_attachment=True, download_name=name)
