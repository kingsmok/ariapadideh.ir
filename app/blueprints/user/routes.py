"""
User Routes - User Panel
"""
from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import or_, desc
from werkzeug.datastructures import MultiDict

from app.blueprints.user import user_bp
from app.extensions import db
from app.models import (
    User, Address, Order, OrderItem, CartItem, Wishlist, Comparison,
    Resume, Contact, Notification, Product
)
from app.services.cart_service import CartService
from app.utils.decorators import active_required


# ==================== DASHBOARD ====================

@user_bp.route('/')
@user_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    
    # Get user stats
    stats = {
        'orders_count': Order.query.filter_by(user_id=current_user.id).count(),
        'wishlist_count': Wishlist.query.filter_by(user_id=current_user.id).count(),
        'compare_count': Comparison.query.filter_by(user_id=current_user.id).count(),
        'cart_count': CartItem.query.filter_by(user_id=current_user.id).count()
    }
    
    # Recent orders
    recent_orders = Order.query.filter_by(
        user_id=current_user.id
    ).order_by(Order.created_at.desc()).limit(5).all()
    
    # Unread notifications
    unread_notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()
    
    return render_template('user/dashboard.html',
        stats=stats,
        recent_orders=recent_orders,
        unread_notifications=unread_notifications
    )


# ==================== AUTH ====================

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('حساب کاربری شما غیرفعال است.', 'warning')
                return render_template('user/auth/login.html')
            
            from flask_login import login_user
            login_user(user, remember=remember)
            
            user.update_last_login()
            
            # Merge guest cart with user cart
            if request.sid:
                CartService.merge_carts(request.sid, user.id)
            
            next_page = request.args.get('next')
            flash(f'خوش آمدید {user.full_name}!', 'success')
            return redirect(next_page or url_for('user.dashboard'))
        
        flash('ایمیل یا رمز عبور اشتباه است.', 'error')
    
    return render_template('user/auth/login.html')


@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if password != confirm_password:
            flash('رمز عبور و تکرار آن مطابقت ندارد.', 'error')
            return render_template('user/auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('این ایمیل قبلاً ثبت شده است.', 'error')
            return render_template('user/auth/register.html')
        
        # Create user
        from app.models import Role
        user = User(
            email=email,
            phone=phone,
            role_id=Role.get_user_role().id
        )
        user.set_password(password)
        user.save()
        
        flash('ثبت‌نام با موفقیت انجام شد. لطفاً وارد شوید.', 'success')
        return redirect(url_for('user.login'))
    
    return render_template('user/auth/register.html')


@user_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    
    from flask_login import logout_user
    logout_user()
    
    flash('با موفقیت خارج شدید.', 'success')
    return redirect(url_for('public.home'))


@user_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password"""
    
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            token = user.generate_reset_token()
            # TODO: Send email with reset link
            flash(f'لینک بازیابی رمز عبور به ایمیل شما ارسال شد.', 'success')
        else:
            flash('کاربری با این ایمیل یافت نشد.', 'warning')
    
    return render_template('user/auth/forgot_password.html')


# ==================== PROFILE ====================

@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile"""
    
    if request.method == 'POST':
        current_user.first_name = request.form.get('first_name')
        current_user.last_name = request.form.get('last_name')
        current_user.phone = request.form.get('phone')
        current_user.save()
        
        flash('پروفایل بروزرسانی شد.', 'success')
        return redirect(url_for('user.profile'))
    
    return render_template('user/profile.html')


@user_bp.route('/profile/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password"""
    
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_user.check_password(current_password):
            flash('رمز فعلی اشتباه است.', 'error')
            return redirect(url_for('user.change_password'))
        
        if new_password != confirm_password:
            flash('رمز جدید و تکرار آن مطابقت ندارد.', 'error')
            return redirect(url_for('user.change_password'))
        
        current_user.set_password(new_password)
        current_user.save()
        
        flash('رمز عبور با موفقیت تغییر کرد.', 'success')
        return redirect(url_for('user.profile'))
    
    return render_template('user/profile/change_password.html')


# ==================== ADDRESSES ====================

@user_bp.route('/addresses')
@login_required
def addresses():
    """User addresses"""
    
    addresses_list = Address.query.filter_by(
        user_id=current_user.id,
        is_deleted=False
    ).order_by(Address.is_default.desc(), Address.created_at.desc()).all()
    
    return render_template('user/addresses.html', addresses=addresses_list)


@user_bp.route('/addresses/create', methods=['GET', 'POST'])
@user_bp.route('/addresses/<int:address_id>/edit', methods=['GET', 'POST'])
@login_required
def address_edit(address_id=None):
    """Create or edit address"""
    
    address = None
    if address_id:
        address = Address.query.filter_by(
            id=address_id,
            user_id=current_user.id
        ).first_or_404()
    
    if request.method == 'POST':
        title = request.form.get('title')
        recipient_name = request.form.get('recipient_name')
        recipient_phone = request.form.get('recipient_phone')
        province = request.form.get('province')
        city = request.form.get('city')
        address_text = request.form.get('address')
        postal_code = request.form.get('postal_code')
        is_default = request.form.get('is_default') == '1'
        
        if address:
            address.title = title
            address.recipient_name = recipient_name
            address.recipient_phone = recipient_phone
            address.province = province
            address.city = city
            address.address = address_text
            address.postal_code = postal_code
            if is_default:
                address.set_as_default()
        else:
            address = Address(
                user_id=current_user.id,
                title=title,
                recipient_name=recipient_name,
                recipient_phone=recipient_phone,
                province=province,
                city=city,
                address=address_text,
                postal_code=postal_code,
                is_default=is_default
            )
            if is_default:
                address.is_default = True
            db.session.add(address)
        
        db.session.commit()
        
        flash('آدرس ذخیره شد.', 'success')
        return redirect(url_for('user.addresses'))
    
    return render_template('user/address_edit.html', address=address)


@user_bp.route('/addresses/<int:address_id>/delete', methods=['POST'])
@login_required
def address_delete(address_id):
    """Delete address"""
    
    address = Address.query.filter_by(
        id=address_id,
        user_id=current_user.id
    ).first_or_404()
    
    address.delete()
    
    flash('آدرس حذف شد.', 'success')
    return redirect(url_for('user.addresses'))


@user_bp.route('/addresses/<int:address_id>/set-default', methods=['POST'])
@login_required
def address_set_default(address_id):
    """Set address as default"""
    
    address = Address.query.filter_by(
        id=address_id,
        user_id=current_user.id
    ).first_or_404()
    
    address.set_as_default()
    
    flash('آدرس پیش‌فرض تغییر کرد.', 'success')
    return redirect(url_for('user.addresses'))


# ==================== ORDERS ====================

@user_bp.route('/orders')
@login_required
def orders():
    """User orders"""
    
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('ITEMS_PER_PAGE', 10)
    status = request.args.get('status', '')
    
    query = Order.query.filter_by(user_id=current_user.id)
    
    if status:
        query = query.filter_by(status=status)
    
    orders_list = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('user/orders.html', orders=orders_list)


@user_bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    """Order detail"""
    
    order = Order.query.filter_by(
        id=order_id,
        user_id=current_user.id
    ).first_or_404()
    
    return render_template('user/order_detail.html', order=order)


@user_bp.route('/orders/<int:order_id>/cancel', methods=['GET', 'POST'])
@login_required
def order_cancel(order_id):
    """Cancel order"""
    
    order = Order.query.filter_by(
        id=order_id,
        user_id=current_user.id
    ).first_or_404()
    
    if not order.can_cancel:
        flash('امکان لغو این سفارش وجود ندارد.', 'error')
        return redirect(url_for('user.order_detail', order_id=order_id))
    
    if request.method == 'POST':
        reason = request.form.get('reason', '')
        order.cancel(reason)
        
        flash('سفارش با موفقیت لغو شد.', 'success')
        return redirect(url_for('user.orders'))
    
    return render_template('user/order_cancel.html', order=order)


# ==================== WISHLIST ====================

@user_bp.route('/wishlist')
@login_required
def wishlist():
    """User wishlist"""
    
    wishlist_items = Wishlist.query.filter_by(
        user_id=current_user.id
    ).order_by(Wishlist.created_at.desc()).all()
    
    return render_template('user/wishlist.html', wishlist_items=wishlist_items)


@user_bp.route('/wishlist/add/<int:product_id>', methods=['POST'])
@login_required
def wishlist_add(product_id):
    """Add to wishlist"""
    
    product = Product.query.get_or_404(product_id)
    
    existing = Wishlist.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()
    
    if existing:
        return jsonify({'success': False, 'message': 'این محصول قبلاً به علاقه‌مندی‌ها اضافه شده'})
    
    wishlist = Wishlist(
        user_id=current_user.id,
        product_id=product_id
    )
    db.session.add(wishlist)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'محصول به علاقه‌مندی‌ها اضافه شد'})


@user_bp.route('/wishlist/remove/<int:product_id>', methods=['POST'])
@login_required
def wishlist_remove(product_id):
    """Remove from wishlist"""
    
    wishlist = Wishlist.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()
    
    if wishlist:
        wishlist.delete()
    
    return jsonify({'success': True, 'message': 'محصول از علاقه‌مندی‌ها حذف شد'})


# ==================== COMPARISONS ====================

@user_bp.route('/comparisons')
@login_required
def comparisons():
    """User comparisons"""
    
    comparisons_list = Comparison.query.filter_by(
        user_id=current_user.id
    ).all()
    
    products = [c.product for c in comparisons_list if c.product]
    
    return render_template('user/comparisons.html', products=products)


# ==================== NOTIFICATIONS ====================

@user_bp.route('/notifications')
@login_required
def notifications():
    """User notifications"""
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    notifications_list = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('user/notifications.html', notifications=notifications_list)


@user_bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def notification_read(notification_id):
    """Mark notification as read"""
    
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id
    ).first_or_404()
    
    notification.mark_read()
    
    if notification.action_url:
        return redirect(notification.action_url)
    
    return redirect(url_for('user.notifications'))


@user_bp.route('/notifications/read-all', methods=['POST'])
@login_required
def notifications_read_all():
    """Mark all notifications as read"""
    
    Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).update({'is_read': True})
    db.session.commit()
    
    flash('همه اعلان‌ها خوانده شد.', 'success')
    return redirect(url_for('user.notifications'))


# ==================== RESUME ====================

@user_bp.route('/resumes', methods=['GET', 'POST'])
@login_required
def resumes():
    """User submitted resumes"""
    
    resumes_list = Resume.query.filter_by(
        user_id=current_user.id,
        is_deleted=False
    ).order_by(Resume.created_at.desc()).all()
    
    return render_template('user/resumes.html', resumes=resumes_list)


# ==================== API: CART ====================

@user_bp.route('/api/cart/add', methods=['POST'])
def api_cart_add():
    """Add item to cart API"""
    
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    if current_user.is_authenticated:
        success = CartService.add_to_user_cart(current_user.id, product_id, quantity)
        cart_count = CartService.get_user_cart_count(current_user.id)
    else:
        success = CartService.add_to_session_cart(product_id, quantity)
        cart_count = CartService.get_session_cart_count(request.sid)
    
    return jsonify({
        'success': success,
        'cart_count': cart_count,
        'message': 'محصول به سبد خرید اضافه شد' if success else 'خطا در افزودن به سبد'
    })


@user_bp.route('/api/cart/update', methods=['POST'])
@login_required
def api_cart_update():
    """Update cart item API"""
    
    data = request.get_json()
    item_id = data.get('item_id')
    quantity = data.get('quantity', 1)
    
    success = CartService.update_user_cart_item(item_id, quantity)
    
    return jsonify({
        'success': success,
        'message': 'سبد خرید بروزرسانی شد' if success else 'خطا در بروزرسانی'
    })


@user_bp.route('/api/cart/remove', methods=['POST'])
@login_required
def api_cart_remove():
    """Remove cart item API"""
    
    data = request.get_json()
    item_id = data.get('item_id')
    
    success = CartService.remove_from_user_cart(item_id)
    
    return jsonify({
        'success': success,
        'message': 'محصول از سبد حذف شد' if success else 'خطا در حذف'
    })


# ==================== API: WISHLIST ====================

@user_bp.route('/api/wishlist/toggle', methods=['POST'])
@login_required
def api_wishlist_toggle():
    """Toggle wishlist API"""
    
    data = request.get_json()
    product_id = data.get('product_id')
    
    existing = Wishlist.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()
    
    if existing:
        existing.delete()
        message = 'محصول از علاقه‌مندی‌ها حذف شد'
    else:
        wishlist = Wishlist(user_id=current_user.id, product_id=product_id)
        db.session.add(wishlist)
        db.session.commit()
        message = 'محصول به علاقه‌مندی‌ها اضافه شد'
    
    return jsonify({
        'success': True,
        'message': message,
        'in_wishlist': existing is None
    })


# ==================== API: COMPARE ====================

@user_bp.route('/api/compare/add', methods=['POST'])
@login_required
def api_compare_add():
    """Add to compare API"""
    
    data = request.get_json()
    product_id = data.get('product_id')
    
    existing = Comparison.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()
    
    if existing:
        return jsonify({
            'success': False,
            'message': 'این محصول در لیست مقایسه وجود دارد'
        })
    
    # Check max 4 products
    current_count = Comparison.query.filter_by(user_id=current_user.id).count()
    if current_count >= 4:
        return jsonify({
            'success': False,
            'message': 'حداکثر ۴ محصول می‌توانید مقایسه کنید'
        })
    
    comparison = Comparison(user_id=current_user.id, product_id=product_id)
    db.session.add(comparison)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'محصول به لیست مقایسه اضافه شد',
        'count': current_count + 1
    })
