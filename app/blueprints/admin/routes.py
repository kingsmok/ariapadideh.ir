"""
Admin Routes - CMS Management
"""
from flask import (
    render_template, request, redirect, url_for, 
    flash, jsonify, current_app, abort
)
from flask_login import login_required, current_user
from sqlalchemy import or_, desc
from werkzeug.datastructures import CombinedMultiDict
from werkzeug.utils import secure_filename

from app.blueprints.admin import admin_bp
from app.blueprints.admin.decorators import admin_required
from app.blueprints.admin.forms import (
    LoginForm, UserForm, RoleForm, ProductForm, CategoryForm,
    PageForm, PostForm, MenuForm, SliderForm, BannerForm,
    SettingForm, MediaForm, ContactReplyForm
)
from app.extensions import db, cache
from app.models import (
    User, Role, Product, ProductImage, Category, Brand, Tag,
    Order, OrderItem, CartItem, Wishlist, Comparison,
    Page, PageComponent, Post, Comment,
    Menu, Slider, SliderItem, Banner, Media, Setting,
    Contact, FAQ, Resume, Log, Notification,
    ServiceCatalog, PortfolioCaseStudies, ConsultationLeads
)
from app.services.media_service import MediaService
from app.services.notification_service import NotificationService
from app.utils.helpers import (
    save_file, delete_file, resize_image, 
    get_pagination_data, slugify, unique_slug
)


# ==================== DASHBOARD ====================

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard"""
    
    # Stats
    stats = {
        'total_users': User.query.filter_by(is_deleted=False).count(),
        'total_products': Product.query.filter_by(is_deleted=False).count(),
        'total_orders': Order.query.count(),
        'pending_orders': Order.query.filter_by(status='pending').count(),
        'total_posts': Post.query.filter_by(is_deleted=False).count(),
        'unread_contacts': Contact.query.filter_by(is_read=False).count(),
        'new_resumes': Resume.query.filter_by(status='new').count(),
    }
    
    # Recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    
    # Recent contacts
    recent_contacts = Contact.query.filter_by(is_read=False).order_by(
        Contact.created_at.desc()
    ).limit(5).all()
    
    # Sales chart data (last 7 days)
    from datetime import datetime, timedelta
    days = 7
    sales_data = []
    for i in range(days):
        date = datetime.utcnow() - timedelta(days=i)
        date_start = date.replace(hour=0, minute=0, second=0)
        date_end = date.replace(hour=23, minute=59, second=59)
        
        day_total = db.session.query(db.func.sum(Order.total_amount)).filter(
            Order.created_at >= date_start,
            Order.created_at <= date_end,
            Order.payment_status == 'paid'
        ).scalar() or 0
        
        sales_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'label': date.strftime('%A')[:3],
            'total': float(day_total)
        })
    
    sales_data.reverse()
    
    return render_template('admin/dashboard.html',
        stats=stats,
        recent_orders=recent_orders,
        recent_contacts=recent_contacts,
        sales_data=sales_data
    )


# ==================== AUTH ====================

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login"""
    
    if current_user.is_authenticated and current_user.is_admin():
        return redirect(url_for('admin.dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data):
            if not user.is_active_user():
                flash('حساب کاربری شما غیرفعال است.', 'error')
                return render_template('admin/auth/login.html', form=form)
            
            from flask_login import login_user
            login_user(user, remember=form.remember.data)
            
            user.update_last_login()
            
            # Log action
            Log.log_action('admin_login', user_id=user.id, request=request)
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin.dashboard'))
        
        flash('ایمیل یا رمز عبور اشتباه است.', 'error')
    
    return render_template('admin/auth/login.html', form=form)


@admin_bp.route('/logout')
@login_required
def logout():
    """Admin logout"""
    
    Log.log_action('admin_logout', user_id=current_user.id, request=request)
    
    from flask_login import logout_user
    logout_user()
    
    flash('با موفقیت خارج شدید.', 'success')
    return redirect(url_for('admin.login'))


# ==================== USERS MANAGEMENT ====================

@admin_bp.route('/users')
@admin_bp.route('/users/<int:page>')
@login_required
@admin_required
def users(page=1):
    """Users list"""
    
    per_page = current_app.config.get('ADMIN_ITEMS_PER_PAGE', 50)
    
    # Filters
    search = request.args.get('search', '')
    role_filter = request.args.get('role', '')
    status_filter = request.args.get('status', '')
    
    query = User.query.filter_by(is_deleted=False)
    
    if search:
        query = query.filter(or_(
            User.email.ilike(f'%{search}%'),
            User.phone.ilike(f'%{search}%'),
            User.first_name.ilike(f'%{search}%'),
            User.last_name.ilike(f'%{search}%')
        ))
    
    if role_filter:
        query = query.filter_by(role_id=role_filter)
    
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)
    elif status_filter == 'unverified':
        query = query.filter_by(is_verified=False)
    
    users_list = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    roles = Role.query.filter_by(is_deleted=False).all()
    
    return render_template('admin/users/list.html',
        users=users_list,
        roles=roles
    )


@admin_bp.route('/users/create', methods=['GET', 'POST'])
@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def user_edit(user_id=None):
    """Create or edit user"""
    
    user = None
    if user_id:
        user = User.query.get_or_404(user_id)
    
    form = UserForm(obj=user)
    
    if form.validate_on_submit():
        if user:
            # Update existing user
            form.populate_obj(user)
            if form.password.data:
                user.set_password(form.password.data)
            user.save()
            Log.log_action('user_updated', user_id=current_user.id, 
                          entity_type='User', entity_id=user.id, request=request)
            flash('کاربر با موفقیت ویرایش شد.', 'success')
        else:
            # Create new user
            user = User()
            form.populate_obj(user)
            user.set_password(form.password.data)
            user.role_id = form.role_id.data or Role.get_user_role().id
            user.save()
            Log.log_action('user_created', user_id=current_user.id,
                          entity_type='User', entity_id=user.id, request=request)
            flash('کاربر با موفقیت ایجاد شد.', 'success')
        
        return redirect(url_for('admin.users'))
    
    roles = Role.query.filter_by(is_deleted=False).all()
    
    return render_template('admin/users/edit.html',
        form=form,
        user=user,
        roles=roles
    )


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def user_delete(user_id):
    """Delete user (soft delete)"""
    
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('شما نمی‌توانید حساب خود را حذف کنید.', 'error')
        return redirect(url_for('admin.users'))
    
    user.delete()
    Log.log_action('user_deleted', user_id=current_user.id,
                  entity_type='User', entity_id=user_id, request=request)
    
    flash('کاربر با موفقیت حذف شد.', 'success')
    return redirect(url_for('admin.users'))


# ==================== PRODUCTS MANAGEMENT ====================

@admin_bp.route('/products')
@admin_bp.route('/products/<int:page>')
@login_required
@admin_required
def products(page=1):
    """Products list"""
    
    per_page = current_app.config.get('ADMIN_ITEMS_PER_PAGE', 50)
    
    search = request.args.get('search', '')
    category_filter = request.args.get('category', type=int)
    status_filter = request.args.get('status', '')
    
    query = Product.query.filter_by(is_deleted=False)
    
    if search:
        query = query.filter(or_(
            Product.title.ilike(f'%{search}%'),
            Product.sku.ilike(f'%{search}%')
        ))
    
    if category_filter:
        query = query.filter(Product.categories.any(id=category_filter))
    
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)
    elif status_filter == 'out_of_stock':
        query = query.filter(Product.stock_quantity == 0)
    elif status_filter == 'featured':
        query = query.filter_by(is_featured=True)
    
    products_list = query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    categories = Category.query.filter_by(is_deleted=False).all()
    
    return render_template('admin/products/list.html',
        products=products_list,
        categories=categories
    )


@admin_bp.route('/products/create', methods=['GET', 'POST'])
@admin_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def product_edit(product_id=None):
    """Create or edit product"""
    
    product = None
    if product_id:
        product = Product.query.get_or_404(product_id)
    
    form = ProductForm(obj=product)
    
    if form.validate_on_submit():
        if product:
            old_values = product.to_dict()
        
        product = product or Product()
        # Populate all scalar/simple fields, but skip relationship-backed and
        # file-upload fields — those are assigned from real model objects / saved
        # files below to avoid assigning raw ints/None to relationships or wiping
        # stored file paths.
        _skip = {'categories', 'tags', 'images', 'featured_image', 'csrf_token', 'submit'}
        for field in form:
            if field.name in _skip:
                continue
            if hasattr(product, field.name):
                setattr(product, field.name, field.data)

        # Ensure a slug exists (Product.slug is NOT NULL & unique)
        if not getattr(product, 'slug', None):
            product.slug = unique_slug(Product, product.title or 'product', exclude_id=product.id)

        # Handle categories
        if form.categories.data:
            product.categories = Category.query.filter(
                Category.id.in_(form.categories.data)
            ).all()
        
        # Handle featured image
        if form.featured_image.data:
            filename = MediaService.save_product_image(
                form.featured_image.data, 
                product.id or 0
            )
            product.featured_image = f'/static/uploads/products/{filename}'
        
        product.save()
        
        # Handle additional images
        if form.images.data:
            for img in form.images.data:
                if img:
                    filename = MediaService.save_product_image(img, product.id)
                    image = ProductImage(
                        product_id=product.id,
                        url=f'/static/uploads/products/{filename}'
                    )
                    db.session.add(image)
            db.session.commit()
        
        # Log
        Log.log_action(
            'product_updated' if product_id else 'product_created',
            user_id=current_user.id,
            entity_type='Product',
            entity_id=product.id,
            old_values=old_values if product_id else None,
            new_values=product.to_dict(),
            request=request
        )
        
        flash('محصول با موفقیت ذخیره شد.', 'success')
        return redirect(url_for('admin.products'))
    
    categories = Category.query.filter_by(is_deleted=False).all()
    brands = Brand.query.filter_by(is_deleted=False).all()
    tags = Tag.query.filter_by(is_deleted=False).all()
    
    return render_template('admin/products/edit.html',
        form=form,
        product=product,
        categories=categories,
        brands=brands,
        tags=tags
    )


@admin_bp.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
@admin_required
def product_delete(product_id):
    """Delete product"""
    
    product = Product.query.get_or_404(product_id)
    product.delete()
    
    Log.log_action('product_deleted', user_id=current_user.id,
                  entity_type='Product', entity_id=product_id, request=request)
    
    flash('محصول با موفقیت حذف شد.', 'success')
    return redirect(url_for('admin.products'))


# ==================== CATEGORIES MANAGEMENT ====================

@admin_bp.route('/categories')
@login_required
@admin_required
def categories():
    """Categories list"""
    
    categories_list = Category.query.filter_by(
        is_deleted=False,
        parent_id=None
    ).order_by(Category.sort_order).all()
    
    return render_template('admin/categories/list.html',
        categories=categories_list
    )


@admin_bp.route('/categories/create', methods=['GET', 'POST'])
@admin_bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def category_edit(category_id=None):
    """Create or edit category"""
    
    category = None
    if category_id:
        category = Category.query.get_or_404(category_id)
    
    form = CategoryForm(obj=category)
    
    if form.validate_on_submit():
        category = category or Category()
        form.populate_obj(category)
        # Category.slug is NOT NULL & unique — auto-generate if left blank
        if not getattr(category, 'slug', None):
            category.slug = unique_slug(Category, category.title or 'category', exclude_id=category.id)

        # Handle image upload
        if form.image.data:
            filename = MediaService.save_category_image(form.image.data)
            category.image = f'/static/uploads/categories/{filename}'
        
        if form.banner.data:
            filename = MediaService.save_category_banner(form.banner.data)
            category.banner = f'/static/uploads/categories/{filename}'
        
        category.save()
        
        Log.log_action(
            'category_updated' if category_id else 'category_created',
            user_id=current_user.id,
            entity_type='Category',
            entity_id=category.id,
            request=request
        )
        
        flash('دسته‌بندی با موفقیت ذخیره شد.', 'success')
        return redirect(url_for('admin.categories'))
    
    parent_categories = Category.query.filter_by(
        is_deleted=False,
        parent_id=None
    ).all()
    
    if category:
        parent_categories = [c for c in parent_categories if c.id != category.id]
    
    return render_template('admin/categories/edit.html',
        form=form,
        category=category,
        parent_categories=parent_categories
    )


@admin_bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@login_required
@admin_required
def category_delete(category_id):
    """Delete category"""
    
    category = Category.query.get_or_404(category_id)
    
    # Check if has children or products
    has_children = category.children.filter_by(is_deleted=False).count() > 0
    has_products = category.products.count() > 0
    
    if has_children:
        flash('ابتدا زیرشاخه‌ها را حذف کنید.', 'error')
        return redirect(url_for('admin.categories'))
    
    if has_products:
        flash('این دسته‌بندی دارای محصول است و نمی‌تواند حذف شود.', 'error')
        return redirect(url_for('admin.categories'))
    
    category.delete()
    
    Log.log_action('category_deleted', user_id=current_user.id,
                  entity_type='Category', entity_id=category_id, request=request)
    
    flash('دسته‌بندی با موفقیت حذف شد.', 'success')
    return redirect(url_for('admin.categories'))


# ==================== PAGES MANAGEMENT ====================

@admin_bp.route('/pages')
@login_required
@admin_required
def pages():
    """Pages list"""
    
    pages_list = Page.query.filter_by(is_deleted=False).order_by(
        Page.sort_order
    ).all()
    
    return render_template('admin/pages/list.html', pages=pages_list)


@admin_bp.route('/pages/create', methods=['GET', 'POST'])
@admin_bp.route('/pages/<int:page_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def page_edit(page_id=None):
    """Create or edit page"""
    
    page_obj = None
    if page_id:
        page_obj = Page.query.get_or_404(page_id)
    
    form = PageForm(obj=page_obj)
    
    if form.validate_on_submit():
        page_obj = page_obj or Page()
        form.populate_obj(page_obj)
        # Page.slug is NOT NULL & unique — auto-generate if left blank
        if not getattr(page_obj, 'slug', None):
            page_obj.slug = unique_slug(Page, page_obj.title or 'page', exclude_id=page_obj.id)
        page_obj.save()
        
        Log.log_action(
            'page_updated' if page_id else 'page_created',
            user_id=current_user.id,
            entity_type='Page',
            entity_id=page_obj.id,
            request=request
        )
        
        flash('صفحه با موفقیت ذخیره شد.', 'success')
        return redirect(url_for('admin.pages'))
    
    templates = ['default', 'fullwidth', 'sidebar', 'landing', 'blank']
    
    return render_template('admin/pages/edit.html',
        form=form,
        page=page_obj,
        templates=templates
    )


@admin_bp.route('/pages/<int:page_id>/components')
@login_required
@admin_required
def page_components(page_id):
    """Page components management"""
    
    page_obj = Page.query.get_or_404(page_id)
    
    components = PageComponent.query.filter_by(
        page_id=page_id,
        is_deleted=False
    ).order_by(PageComponent.sort_order).all()
    
    return render_template('admin/pages/components.html',
        page=page_obj,
        components=components
    )


@admin_bp.route('/pages/<int:page_id>/delete', methods=['POST'])
@login_required
@admin_required
def page_delete(page_id):
    """Delete page"""
    
    page_obj = Page.query.get_or_404(page_id)
    page_obj.delete()
    
    flash('صفحه با موفقیت حذف شد.', 'success')
    return redirect(url_for('admin.pages'))


# ==================== MENUS MANAGEMENT ====================

@admin_bp.route('/menus')
@login_required
@admin_required
def menus():
    """Menus list"""
    
    menus_dict = {}
    positions = ['header', 'footer', 'mobile', 'sidebar']
    
    for position in positions:
        menus_dict[position] = Menu.query.filter_by(
            position=position,
            is_deleted=False,
            parent_id=None
        ).order_by(Menu.sort_order).all()
    
    return render_template('admin/menus/list.html', menus=menus_dict)


@admin_bp.route('/menus/create', methods=['GET', 'POST'])
@admin_bp.route('/menus/<int:menu_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def menu_edit(menu_id=None):
    """Create or edit menu item"""
    
    menu = None
    if menu_id:
        menu = Menu.query.get_or_404(menu_id)
    
    form = MenuForm(obj=menu)
    
    if form.validate_on_submit():
        menu = menu or Menu()
        form.populate_obj(menu)
        # Menu model requires a unique slug; auto-generate one if missing.
        if not getattr(menu, 'slug', None):
            menu.slug = unique_slug(Menu, menu.title or 'menu', exclude_id=menu.id)
        menu.save()
        
        # Clear cache
        cache.delete('menu_header')
        cache.delete('menu_footer')
        
        flash('منو با موفقیت ذخیره شد.', 'success')
        return redirect(url_for('admin.menus'))
    
    menus = Menu.query.filter_by(is_deleted=False, parent_id=None).all()
    
    return render_template('admin/menus/edit.html',
        form=form,
        menu=menu,
        menus=menus
    )


@admin_bp.route('/menus/<int:menu_id>/delete', methods=['POST'])
@login_required
@admin_required
def menu_delete(menu_id):
    """Delete menu item"""
    
    menu = Menu.query.get_or_404(menu_id)
    menu.delete()
    
    cache.delete('menu_header')
    cache.delete('menu_footer')
    
    flash('منو با موفقیت حذف شد.', 'success')
    return redirect(url_for('admin.menus'))


# ==================== SLIDERS MANAGEMENT ====================

@admin_bp.route('/sliders')
@login_required
@admin_required
def sliders():
    """Sliders list"""
    
    sliders_list = Slider.query.filter_by(is_deleted=False).all()
    
    return render_template('admin/sliders/list.html', sliders=sliders_list)


@admin_bp.route('/sliders/create', methods=['GET', 'POST'])
@admin_bp.route('/sliders/<int:slider_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def slider_edit(slider_id=None):
    """Create or edit slider"""
    
    slider = None
    if slider_id:
        slider = Slider.query.get_or_404(slider_id)
    
    if request.method == 'POST':
        title = request.form.get('title')
        position = request.form.get('position', 'home')
        autoplay = request.form.get('autoplay', '1') == '1'
        
        if slider:
            slider.title = title
            slider.position = position
            slider.autoplay = autoplay
            slider.save()
        else:
            slider = Slider(
                title=title,
                slug=unique_slug(Slider, title or 'slider'),
                position=position,
                autoplay=autoplay
            )
            slider.save()
        
        flash('اسلایدر با موفقیت ذخیره شد.', 'success')
        return redirect(url_for('admin.slider_items', slider_id=slider.id))
    
    return render_template('admin/sliders/edit.html', slider=slider)


@admin_bp.route('/sliders/<int:slider_id>/items')
@login_required
@admin_required
def slider_items(slider_id):
    """Slider items management"""
    
    slider = Slider.query.get_or_404(slider_id)
    items = SliderItem.query.filter_by(
        slider_id=slider_id,
        is_deleted=False
    ).order_by(SliderItem.sort_order).all()
    
    return render_template('admin/sliders/items.html', slider=slider, items=items)


@admin_bp.route('/sliders/<int:slider_id>/items/create', methods=['GET', 'POST'])
@admin_bp.route('/sliders/<int:slider_id>/items/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def slider_item_edit(slider_id, item_id=None):
    """Create or edit slider item"""
    
    slider = Slider.query.get_or_404(slider_id)
    item = None
    
    if item_id:
        item = SliderItem.query.get_or_404(item_id)
    
    if request.method == 'POST':
        item = item or SliderItem(slider_id=slider_id)
        
        item.title = request.form.get('title')
        item.subtitle = request.form.get('subtitle')
        item.description = request.form.get('description')
        item.url = request.form.get('url')
        item.link_text = request.form.get('link_text')
        item.text_alignment = request.form.get('text_alignment', 'right')
        item.sort_order = request.form.get('sort_order', 0, type=int)
        
        # Image upload
        if request.files.get('image'):
            filename = MediaService.save_slider_image(request.files['image'])
            item.image = f'/static/uploads/sliders/{filename}'
        
        item.save()
        
        flash('آیتم اسلایدر با موفقیت ذخیره شد.', 'success')
        return redirect(url_for('admin.slider_items', slider_id=slider_id))
    
    return render_template('admin/sliders/item_edit.html',
        slider=slider, item=item)


# ==================== BANNERS MANAGEMENT ====================

@admin_bp.route('/banners')
@login_required
@admin_required
def banners():
    """Banners list"""
    
    banners_list = Banner.query.filter_by(is_deleted=False).order_by(
        Banner.position, Banner.sort_order
    ).all()
    
    return render_template('admin/banners/list.html', banners=banners_list)


@admin_bp.route('/banners/create', methods=['GET', 'POST'])
@admin_bp.route('/banners/<int:banner_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def banner_edit(banner_id=None):
    """Create or edit banner"""
    
    banner = None
    if banner_id:
        banner = Banner.query.get_or_404(banner_id)
    
    form = BannerForm(obj=banner)
    
    if form.validate_on_submit():
        banner = banner or Banner()
        form.populate_obj(banner)
        
        if form.image.data:
            filename = MediaService.save_banner_image(form.image.data)
            banner.image = f'/static/uploads/banners/{filename}'
        
        banner.save()
        
        flash('بنر با موفقیت ذخیره شد.', 'success')
        return redirect(url_for('admin.banners'))
    
    positions = [
        ('home_top', 'بالای صفحه اصلی'),
        ('home_middle', 'میانه صفحه اصلی'),
        ('home_bottom', 'پایین صفحه اصلی'),
        ('sidebar', 'سایدبار'),
        ('between_products', 'بین محصولات'),
        ('category_top', 'بالای صفحه دسته‌بندی'),
    ]
    
    return render_template('admin/banners/edit.html',
        form=form,
        banner=banner,
        positions=positions
    )


# ==================== SETTINGS MANAGEMENT ====================

@admin_bp.route('/settings')
@login_required
@admin_required
def settings():
    """Settings page"""
    
    settings_groups = {
        'general': {
            'title': 'تنظیمات عمومی',
            'icon': 'fa-cog',
            'settings': Setting.query.filter_by(group='general').order_by(Setting.sort_order).all()
        },
        'appearance': {
            'title': 'ظاهر',
            'icon': 'fa-palette',
            'settings': Setting.query.filter_by(group='appearance').order_by(Setting.sort_order).all()
        },
        'contact': {
            'title': 'اطلاعات تماس',
            'icon': 'fa-envelope',
            'settings': Setting.query.filter_by(group='contact').order_by(Setting.sort_order).all()
        },
        'social': {
            'title': 'شبکه‌های اجتماعی',
            'icon': 'fa-share-alt',
            'settings': Setting.query.filter_by(group='social').order_by(Setting.sort_order).all()
        },
        'seo': {
            'title': 'سئو',
            'icon': 'fa-search',
            'settings': Setting.query.filter_by(group='seo').order_by(Setting.sort_order).all()
        },
        'email': {
            'title': 'ایمیل',
            'icon': 'fa-mail-bulk',
            'settings': Setting.query.filter_by(group='email').order_by(Setting.sort_order).all()
        },
        'payment': {
            'title': 'پرداخت',
            'icon': 'fa-credit-card',
            'settings': Setting.query.filter_by(group='payment').order_by(Setting.sort_order).all()
        }
    }
    
    return render_template('admin/settings/index.html', settings_groups=settings_groups)


@admin_bp.route('/settings/group/<group>', methods=['GET', 'POST'])
@login_required
@admin_required
def settings_group(group):
    """Edit settings in a group"""
    
    if request.method == 'POST':
        for key, value in request.form.items():
            if key.startswith('setting_'):
                setting_key = key.replace('setting_', '')
                Setting.set_value(group, setting_key, value)
        
        # Clear cache
        cache.clear()
        
        flash('تنظیمات با موفقیت ذخیره شد.', 'success')
        return redirect(url_for('admin.settings_group', group=group))
    
    settings_list = Setting.query.filter_by(group=group).order_by(Setting.sort_order).all()
    
    # Group metadata
    group_meta = {
        'general': 'تنظیمات عمومی سایت',
        'appearance': 'تنظیمات ظاهری و قالب',
        'contact': 'اطلاعات تماس و آدرس',
        'social': 'لینک شبکه‌های اجتماعی',
        'seo': 'تنظیمات سئو و موتور جستجو',
        'email': 'تنظیمات ایمیل',
        'payment': 'تنظیمات درگاه پرداخت',
    }
    
    return render_template('admin/settings/group.html',
        group=group,
        group_title=group_meta.get(group, group),
        settings=settings_list
    )


# ==================== MEDIA LIBRARY ====================

@admin_bp.route('/media')
@admin_bp.route('/media/<int:page>')
@login_required
@admin_required
def media(page=1):
    """Media library"""
    
    per_page = 40
    
    folder = request.args.get('folder', '')
    search = request.args.get('search', '')
    file_type = request.args.get('type', '')
    
    query = Media.query
    
    if folder:
        query = query.filter_by(folder=folder)
    
    if search:
        query = query.filter(or_(
            Media.filename.ilike(f'%{search}%'),
            Media.alt.ilike(f'%{search}%')
        ))
    
    if file_type:
        query = query.filter_by(file_type=file_type)
    
    media_list = query.order_by(Media.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get folders
    folders = db.session.query(Media.folder).filter(
        Media.folder.isnot(None)
    ).distinct().all()
    folders = [f[0] for f in folders if f[0]]
    
    return render_template('admin/media/index.html',
        media=media_list,
        folders=folders,
        current_folder=folder
    )


@admin_bp.route('/media/upload', methods=['POST'])
@login_required
@admin_required
def media_upload():
    """Upload media file"""
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    folder = request.form.get('folder', '')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    result = MediaService.upload(
        file=file,
        folder=folder,
        uploaded_by=current_user.id
    )
    
    if result:
        return jsonify({
            'success': True,
            'media': result.to_dict()
        })
    
    return jsonify({'error': 'Upload failed'}), 500


@admin_bp.route('/media/<int:media_id>/delete', methods=['POST'])
@login_required
@admin_required
def media_delete(media_id):
    """Delete media file"""
    
    media = Media.query.get_or_404(media_id)
    MediaService.delete(media)
    
    return jsonify({'success': True})


# ==================== ORDERS MANAGEMENT ====================

@admin_bp.route('/orders')
@admin_bp.route('/orders/<int:page>')
@login_required
@admin_required
def orders(page=1):
    """Orders list"""
    
    per_page = current_app.config.get('ADMIN_ITEMS_PER_PAGE', 50)
    
    status = request.args.get('status', '')
    search = request.args.get('search', '')
    payment_status = request.args.get('payment', '')
    
    query = Order.query
    
    if status:
        query = query.filter_by(status=status)
    
    if payment_status:
        query = query.filter_by(payment_status=payment_status)
    
    if search:
        query = query.filter(or_(
            Order.order_number.ilike(f'%{search}%'),
            Order.tracking_code.ilike(f'%{search}%')
        ))
    
    orders_list = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/orders/list.html', orders=orders_list)


@admin_bp.route('/orders/<int:order_id>')
@login_required
@admin_required
def order_detail(order_id):
    """Order detail"""
    
    order = Order.query.get_or_404(order_id)
    
    return render_template('admin/orders/detail.html', order=order)


@admin_bp.route('/orders/<int:order_id>/update-status', methods=['POST'])
@login_required
@admin_required
def order_update_status(order_id):
    """Update order status"""
    
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    note = request.form.get('note', '')
    
    order.update_status(new_status)
    if note:
        order.admin_note = note
    
    # Send notification to user
    if order.user:
        NotificationService.send_to_user(
            user_id=order.user_id,
            title='بروزرسانی سفارش',
            message=f'سفارش {order.order_number} به وضعیت «{order.status_fa}» تغییر یافت.',
            type='order',
            data={'order_id': order.id}
        )
    
    # Send Telegram notification
    NotificationService.notify_telegram_order_update(order)
    
    Log.log_action('order_status_updated', user_id=current_user.id,
                  entity_type='Order', entity_id=order.id,
                  new_values={'status': new_status},
                  request=request)
    
    flash('وضعیت سفارش بروزرسانی شد.', 'success')
    return redirect(url_for('admin.order_detail', order_id=order_id))


# ==================== CONTACTS MANAGEMENT ====================

@admin_bp.route('/contacts')
@admin_bp.route('/contacts/<int:page>')
@login_required
@admin_required
def contacts(page=1):
    """Contacts list"""
    
    per_page = 30
    
    is_read = request.args.get('read', '')
    
    query = Contact.query
    
    if is_read == 'read':
        query = query.filter_by(is_read=True)
    elif is_read == 'unread':
        query = query.filter_by(is_read=False)
    
    contacts_list = query.order_by(Contact.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/contacts/list.html', contacts=contacts_list)


@admin_bp.route('/contacts/<int:contact_id>')
@login_required
@admin_required
def contact_detail(contact_id):
    """Contact detail"""
    
    contact = Contact.query.get_or_404(contact_id)
    
    if not contact.is_read:
        contact.mark_read(current_user.id)
    
    return render_template('admin/contacts/detail.html', contact=contact)


@admin_bp.route('/contacts/<int:contact_id>/reply', methods=['POST'])
@login_required
@admin_required
def contact_reply(contact_id):
    """Reply to contact"""
    
    contact = Contact.query.get_or_404(contact_id)
    
    reply_content = request.form.get('reply_content')
    
    if reply_content:
        contact.reply(reply_content, current_user.id)
        
        # Send reply email
        from app.services.notification_service import NotificationService
        NotificationService.send_contact_reply(contact)
        
        flash('پاسخ ارسال شد.', 'success')
    
    return redirect(url_for('admin.contacts'))


# ==================== RESUMES MANAGEMENT ====================

@admin_bp.route('/resumes')
@admin_bp.route('/resumes/<int:page>')
@login_required
@admin_required
def resumes(page=1):
    """Resumes list"""
    
    per_page = 30
    
    status = request.args.get('status', '')
    
    query = Resume.query.filter_by(is_deleted=False)
    
    if status:
        query = query.filter_by(status=status)
    
    resumes_list = query.order_by(Resume.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/resumes/list.html', resumes=resumes_list)


@admin_bp.route('/resumes/<int:resume_id>/update', methods=['POST'])
@login_required
@admin_required
def resume_update(resume_id):
    """Update resume status"""
    
    resume = Resume.query.get_or_404(resume_id)
    
    new_status = request.form.get('status')
    notes = request.form.get('notes', '')
    
    resume.update_status(new_status, current_user.id, notes)
    
    flash('وضعیت رزومه بروزرسانی شد.', 'success')
    return redirect(url_for('admin.resumes'))


# ==================== FAQS MANAGEMENT ====================

@admin_bp.route('/faqs')
@login_required
@admin_required
def faqs():
    """FAQs list"""
    
    faqs_list = FAQ.query.filter_by(is_deleted=False).order_by(
        FAQ.sort_order
    ).all()
    
    return render_template('admin/faqs/list.html', faqs=faqs_list)


@admin_bp.route('/faqs/create', methods=['GET', 'POST'])
@admin_bp.route('/faqs/<int:faq_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def faq_edit(faq_id=None):
    """Create or edit FAQ"""
    
    faq = None
    if faq_id:
        faq = FAQ.query.get_or_404(faq_id)
    
    if request.method == 'POST':
        faq = faq or FAQ()
        faq.question = request.form.get('question')
        faq.answer = request.form.get('answer')
        faq.category = request.form.get('category')
        faq.sort_order = request.form.get('sort_order', 0, type=int)
        faq.is_featured = request.form.get('is_featured') == '1'
        faq.is_active = request.form.get('is_active') == '1'
        faq.save()
        
        flash('سؤال متداول ذخیره شد.', 'success')
        return redirect(url_for('admin.faqs'))
    
    return render_template('admin/faqs/edit.html', faq=faq)


# ==================== COMMENTS MANAGEMENT ====================

@admin_bp.route('/comments')
@admin_bp.route('/comments/<int:page>')
@login_required
@admin_required
def comments(page=1):
    """Comments list"""
    
    per_page = 30
    
    is_approved = request.args.get('approved', '')
    
    query = Comment.query.filter_by(is_deleted=False)
    
    if is_approved == 'approved':
        query = query.filter_by(is_approved=True)
    elif is_approved == 'pending':
        query = query.filter_by(is_approved=False)
    
    comments_list = query.order_by(Comment.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/comments/list.html', comments=comments_list)


@admin_bp.route('/comments/<int:comment_id>/approve', methods=['POST'])
@login_required
@admin_required
def comment_approve(comment_id):
    """Approve comment"""
    
    comment = Comment.query.get_or_404(comment_id)
    comment.approve(current_user.id)
    
    return jsonify({'success': True})


@admin_bp.route('/comments/<int:comment_id>/spam', methods=['POST'])
@login_required
@admin_required
def comment_spam(comment_id):
    """Mark comment as spam"""
    
    comment = Comment.query.get_or_404(comment_id)
    comment.mark_spam()
    
    return jsonify({'success': True})


# ==================== LOGS ====================

@admin_bp.route('/logs')
@admin_bp.route('/logs/<int:page>')
@login_required
@admin_required
def logs(page=1):
    """Activity logs"""
    
    per_page = 50
    
    action = request.args.get('action', '')
    user_id = request.args.get('user', type=int)
    
    query = Log.query
    
    if action:
        query = query.filter_by(action=action)
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    logs_list = query.order_by(Log.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/logs/list.html', logs=logs_list)


# ==================== PROFILE ====================

@admin_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Admin profile"""
    
    if request.method == 'POST':
        user = current_user
        
        if request.form.get('first_name'):
            user.first_name = request.form.get('first_name')
        if request.form.get('last_name'):
            user.last_name = request.form.get('last_name')
        
        if request.form.get('new_password'):
            if user.check_password(request.form.get('current_password')):
                user.set_password(request.form.get('new_password'))
                flash('رمز عبور تغییر کرد.', 'success')
            else:
                flash('رمز عبور فعلی اشتباه است.', 'error')
        
        user.save()
        flash('پروفایل بروزرسانی شد.', 'success')
        
        return redirect(url_for('admin.profile'))
    
    return render_template('admin/profile.html')


# ==================== AGENCY B2B MANAGEMENT ====================

@admin_bp.route('/agency/services')
@login_required
@admin_required
def agency_services():
    """Agency services catalog management"""
    services_list = ServiceCatalog.query.order_by(ServiceCatalog.sort_order).all()
    return render_template('admin/agency/services.html', services=services_list)


@admin_bp.route('/agency/services/create', methods=['GET', 'POST'])
@admin_bp.route('/agency/services/<int:service_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def agency_service_edit(service_id=None):
    """Create or edit agency service"""
    service = ServiceCatalog.query.get_or_404(service_id) if service_id else None

    if request.method == 'POST':
        service = service or ServiceCatalog()
        service.title = request.form.get('title')
        service.slug = request.form.get('slug')
        service.short_desc = request.form.get('short_desc') or request.form.get('summary', '')
        service.full_desc = request.form.get('full_desc') or request.form.get('description', '')
        service.starting_price_toman = request.form.get('starting_price_toman', type=int) or request.form.get('starting_price', type=int)
        service.icon_svg = request.form.get('icon_svg') or request.form.get('icon', '⚡')
        service.sort_order = request.form.get('sort_order', 0, type=int)
        service.is_active = request.form.get('is_active') == '1'
        
        service.save()
        flash('خدمت با موفقیت ذخیره شد.', 'success')
        return redirect(url_for('admin.agency_services'))

    return render_template('admin/agency/service_edit.html', service=service)


@admin_bp.route('/agency/services/<int:service_id>/delete', methods=['POST'])
@login_required
@admin_required
def agency_service_delete(service_id):
    """Delete agency service"""
    service = ServiceCatalog.query.get_or_404(service_id)
    db.session.delete(service)
    db.session.commit()
    flash('خدمت با موفقیت حذف شد.', 'success')
    return redirect(url_for('admin.agency_services'))


@admin_bp.route('/agency/portfolio')
@login_required
@admin_required
def agency_portfolio():
    """Agency portfolio case studies management"""
    portfolio_list = PortfolioCaseStudies.query.order_by(PortfolioCaseStudies.sort_order).all()
    return render_template('admin/agency/portfolio.html', portfolio=portfolio_list)


@admin_bp.route('/agency/portfolio/create', methods=['GET', 'POST'])
@admin_bp.route('/agency/portfolio/<int:portfolio_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def agency_portfolio_edit(portfolio_id=None):
    """Create or edit portfolio case study"""
    item = PortfolioCaseStudies.query.get_or_404(portfolio_id) if portfolio_id else None

    if request.method == 'POST':
        item = item or PortfolioCaseStudies()
        item.title = request.form.get('title')
        item.slug = request.form.get('slug')
        item.client_name = request.form.get('client_name')
        item.challenge_desc = request.form.get('challenge_desc') or request.form.get('challenge', '')
        item.thumbnail_url = request.form.get('thumbnail_url') or request.form.get('featured_image', '/static/images/no-image.png')
        item.live_url = request.form.get('live_url')
        item.sort_order = request.form.get('sort_order', 0, type=int)
        item.is_featured = request.form.get('is_featured') == '1'
        item.is_active = request.form.get('is_active') == '1'

        item.save()
        flash('پروژه نمونه‌کار با موفقیت ذخیره شد.', 'success')
        return redirect(url_for('admin.agency_portfolio'))

    return render_template('admin/agency/portfolio_edit.html', item=item)


@admin_bp.route('/agency/portfolio/<int:portfolio_id>/delete', methods=['POST'])
@login_required
@admin_required
def agency_portfolio_delete(portfolio_id):
    """Delete portfolio case study"""
    item = PortfolioCaseStudies.query.get_or_404(portfolio_id)
    db.session.delete(item)
    db.session.commit()
    flash('نمونه‌کار با موفقیت حذف شد.', 'success')
    return redirect(url_for('admin.agency_portfolio'))


@admin_bp.route('/agency/leads')
@admin_bp.route('/agency/leads/<int:page>')
@login_required
@admin_required
def agency_leads(page=1):
    """Consultation leads CRM list"""
    per_page = 30
    status_filter = request.args.get('status', '')

    query = ConsultationLeads.query
    if status_filter:
        query = query.filter_by(status=status_filter)

    leads_list = query.order_by(ConsultationLeads.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return render_template('admin/agency/leads.html', leads=leads_list)


@admin_bp.route('/agency/leads/<int:lead_id>/status', methods=['POST'])
@login_required
@admin_required
def agency_lead_update_status(lead_id):
    """Update consultation lead status"""
    lead = ConsultationLeads.query.get_or_404(lead_id)
    new_status = request.form.get('status')
    if new_status:
        lead.status = new_status
        lead.save()
        flash('وضعیت لید با موفقیت بروزرسانی شد.', 'success')
    return redirect(url_for('admin.agency_leads'))

