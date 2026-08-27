"""
Public Routes - Main Site Pages
"""
from datetime import datetime
from flask import render_template, request, abort, jsonify, current_app, redirect, url_for, flash, session
from flask_login import current_user
from sqlalchemy import or_, func, select, desc
from app.blueprints.public import public_bp
from app.extensions import db, cache
from app.models import (
    Product, Category, Brand, Post, Page, Menu, Slider,
    SliderItem, Banner, FAQ, Setting, ProductImage, Tag, Wishlist, Comparison, Address
)
from app.services.seo_service import SEOService
from app.services.cart_service import CartService
from app.utils.helpers import get_pagination_params
from app.utils.decorators import rate_limit


# ==================== HOME PAGE ====================

@public_bp.route('/')
@cache.cached(timeout=300, query_string=True)
def home() -> str:
    """Home page with dynamic components."""
    from app.models.agency import ServiceCatalog, PortfolioCaseStudies
    from app.services.home_builder_service import get_sections
    from app.models import Story, TeamMember, PricingPlan
    from app.services.product_service import ProductService

    home_sections = get_sections()

    # Home page
    home_stmt = select(Page).where(Page.page_type == 'home', Page.is_active.is_(True), Page.is_deleted.is_(False))
    home_page = db.session.execute(home_stmt).scalars().first()

    # Active slider
    slider_stmt = select(Slider).where(Slider.position == 'home', Slider.is_active.is_(True), Slider.is_deleted.is_(False))
    sliders = db.session.execute(slider_stmt).scalars().first()
    slider_items = []
    if sliders:
        items_stmt = select(SliderItem).where(
            SliderItem.slider_id == sliders.id,
            SliderItem.is_active.is_(True),
            SliderItem.is_deleted.is_(False)
        ).order_by(SliderItem.sort_order.asc())
        slider_items = list(db.session.execute(items_stmt).scalars().all())

    # B2B Services and Portfolio
    serv_stmt = select(ServiceCatalog).where(
        ServiceCatalog.is_active.is_(True),
        ServiceCatalog.is_deleted.is_(False)
    ).order_by(ServiceCatalog.sort_order.asc())
    active_services = list(db.session.execute(serv_stmt).scalars().all())

    port_stmt = select(PortfolioCaseStudies).where(
        PortfolioCaseStudies.is_featured.is_(True),
        PortfolioCaseStudies.is_active.is_(True),
        PortfolioCaseStudies.is_deleted.is_(False)
    ).order_by(PortfolioCaseStudies.sort_order.asc()).limit(6)
    featured_portfolio = list(db.session.execute(port_stmt).scalars().all())

    # Products from ProductService
    featured_products = ProductService.get_featured(limit=8)
    new_products = ProductService.get_new_arrivals(limit=8)
    categories = ProductService.get_categories_tree()[:12]

    # Banners by position
    def get_banners_for_pos(position_name: str) -> list:
        stmt = select(Banner).where(
            Banner.position == position_name,
            Banner.is_active.is_(True),
            Banner.is_deleted.is_(False)
        ).order_by(Banner.sort_order.asc())
        return list(db.session.execute(stmt).scalars().all())

    banners_top = get_banners_for_pos('home_top')
    banners_middle = get_banners_for_pos('home_middle')
    banners_bottom = get_banners_for_pos('home_bottom')

    # Latest posts
    post_stmt = select(Post).where(
        Post.status == 'published',
        Post.is_active.is_(True),
        Post.is_deleted.is_(False),
        Post.show_in_home.is_(True)
    ).order_by(Post.published_at.desc()).limit(3)
    latest_posts = list(db.session.execute(post_stmt).scalars().all())

    # FAQs
    faq_stmt = select(FAQ).where(
        FAQ.is_active.is_(True),
        FAQ.is_deleted.is_(False),
        FAQ.is_featured.is_(True)
    ).limit(5)
    faqs = list(db.session.execute(faq_stmt).scalars().all())

    # Cart items count
    user_id = current_user.id if current_user.is_authenticated else None
    cart_items_count = CartService.get_cart_count(user_id=user_id)

    # Stories
    story_stmt = select(Story).where(
        Story.is_active.is_(True),
        Story.is_deleted.is_(False)
    ).order_by(Story.sort_order.asc()).limit(12)
    stories = [s for s in db.session.execute(story_stmt).scalars().all() if s.is_live]

    # Team + pricing
    team_stmt = select(TeamMember).where(
        TeamMember.is_active.is_(True),
        TeamMember.is_deleted.is_(False)
    ).order_by(TeamMember.sort_order.asc()).limit(8)
    team_members = list(db.session.execute(team_stmt).scalars().all())

    pricing_stmt = select(PricingPlan).where(
        PricingPlan.is_active.is_(True),
        PricingPlan.is_deleted.is_(False)
    ).order_by(PricingPlan.sort_order.asc()).limit(4)
    pricing_plans = list(db.session.execute(pricing_stmt).scalars().all())

    seo = SEOService.get_seo_data('home')

    return render_template('public/home.html',
        page=home_page,
        sliders=slider_items,
        active_services=active_services,
        featured_portfolio=featured_portfolio,
        featured_products=featured_products,
        new_products=new_products,
        categories=categories,
        banners_top=banners_top,
        banners_middle=banners_middle,
        banners_bottom=banners_bottom,
        latest_posts=latest_posts,
        faqs=faqs,
        cart_items_count=cart_items_count,
        stories=stories,
        team_members=team_members,
        pricing_plans=pricing_plans,
        home_sections=home_sections,
        en_url='/en/',
        seo=seo
    )


# ==================== PAGE ROUTES ====================

@public_bp.route('/<slug>')
@cache.cached(timeout=300, query_string=True)
def page(slug: str) -> str:
    """Dynamic page by slug."""
    stmt = select(Page).where(Page.slug == slug, Page.is_active.is_(True), Page.is_deleted.is_(False))
    page_obj = db.session.execute(stmt).scalars().first()
    if not page_obj:
        abort(404)

    # Get page components
    components = page_obj.components.filter_by(
        is_active=True,
        is_deleted=False
    ).order_by(page_obj.components.property.mapper.class_.sort_order).all()

    seo = SEOService.get_page_seo(page_obj)

    return render_template(f'public/pages/{page_obj.template or "default"}.html',
        page=page_obj,
        components=components,
        seo=seo
    )


# ==================== CATEGORY ROUTES ====================

@public_bp.route('/categories/')
def categories_list() -> str:
    """All categories listing."""
    parent_stmt = select(Category).where(
        Category.parent_id.is_(None),
        Category.is_active.is_(True),
        Category.is_deleted.is_(False)
    ).order_by(Category.sort_order.asc())
    parent_categories = list(db.session.execute(parent_stmt).scalars().all())

    all_stmt = select(Category).where(
        Category.is_active.is_(True),
        Category.is_deleted.is_(False)
    ).order_by(Category.sort_order.asc())
    all_categories = list(db.session.execute(all_stmt).scalars().all())

    return render_template('public/categories.html', en_url='/en/products',
        parent_categories=parent_categories,
        all_categories=all_categories
    )


@public_bp.route('/category/<slug>')
@public_bp.route('/category/<slug>/<int:page>')
@cache.cached(timeout=300, query_string=True)
def category(slug: str, page: int = 1) -> str:
    """Category page with products."""
    cat_stmt = select(Category).where(Category.slug == slug, Category.is_active.is_(True), Category.is_deleted.is_(False))
    category_obj = db.session.execute(cat_stmt).scalars().first()
    if not category_obj:
        abort(404)

    per_page = current_app.config.get('ITEMS_PER_PAGE', 20)

    # Build query with SQLAlchemy 2.0 select()
    stmt = (
        select(Product)
        .where(
            Product.categories.any(Category.id == category_obj.id),
            Product.is_active.is_(True),
            Product.is_deleted.is_(False),
        )
    )

    # Filters
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    brand_ids = request.args.getlist('brand', type=int)
    in_stock = request.args.get('in_stock', type=int)
    sort = request.args.get('sort', 'newest')

    if min_price:
        stmt = stmt.where(Product.price >= min_price)
    if max_price:
        stmt = stmt.where(Product.price <= max_price)
    if brand_ids:
        stmt = stmt.where(Product.brand_id.in_(brand_ids))
    if in_stock:
        stmt = stmt.where(Product.stock_quantity > 0)

    # Sorting
    sort_options = {
        'newest': Product.created_at.desc(),
        'price_asc': Product.price.asc(),
        'price_desc': Product.price.desc(),
        'popular': Product.view_count.desc(),
        'rating': Product.created_at.desc()
    }
    stmt = stmt.order_by(sort_options.get(sort, Product.created_at.desc()))

    # Paginate with modern db.paginate
    products = db.paginate(stmt, page=page, per_page=per_page, error_out=False)

    # Get child categories
    child_categories = category_obj.children.filter_by(
        is_active=True,
        is_deleted=False
    ).order_by(Category.sort_order).all() if category_obj.show_children else []

    # Get brands in this category
    brand_ids_in_category = [p.brand_id for p in category_obj.products if p.brand_id]
    brands = []
    if brand_ids_in_category:
        b_stmt = select(Brand).where(Brand.id.in_(brand_ids_in_category), Brand.is_active.is_(True))
        brands = list(db.session.execute(b_stmt).scalars().all())

    seo = SEOService.get_category_seo(category_obj)

    return render_template('public/category.html',
        category=category_obj,
        products=products,
        child_categories=child_categories,
        brands=brands,
        seo=seo
    )


# ==================== PRODUCT ROUTES ====================

@public_bp.route('/product/<slug>')
def product(slug: str) -> str:
    """Product detail page."""
    prod_stmt = select(Product).where(Product.slug == slug, Product.is_active.is_(True), Product.is_deleted.is_(False))
    product_obj = db.session.execute(prod_stmt).scalars().first()
    if not product_obj:
        abort(404)

    # Increment views
    product_obj.increment_views()

    # Get images
    images = product_obj.images.filter_by(is_deleted=False).order_by(ProductImage.sort_order).all()

    # Get specifications
    specifications = product_obj.get_specifications_dict()

    # Get related products
    related_products = product_obj.get_related_products(limit=4)

    # Get comments
    comments = product_obj.comments.filter_by(
        is_approved=True,
        is_deleted=False
    ).order_by(db.desc('created_at')).limit(10).all()

    # Check if in wishlist
    in_wishlist = False
    if current_user.is_authenticated:
        wish_stmt = select(Wishlist.id).where(
            Wishlist.user_id == current_user.id,
            Wishlist.product_id == product_obj.id
        )
        in_wishlist = db.session.execute(wish_stmt).scalar() is not None

    # Get breadcrumb categories
    breadcrumb_categories = product_obj.categories[0].breadcrumbs if product_obj.categories else []

    # Get related posts
    related_posts = []
    if product_obj.categories:
        cat_ids = [c.id for c in product_obj.categories]
        if cat_ids:
            rp_stmt = select(Post).where(
                Post.is_active.is_(True),
                Post.is_deleted.is_(False),
                Post.status == 'published',
                Post.category_id.in_(cat_ids),
            ).order_by(Post.published_at.desc()).limit(3)
            related_posts = list(db.session.execute(rp_stmt).scalars().all())

    seo = SEOService.get_product_seo(product_obj)

    # Video gallery
    from app.models.features import ProductVideo
    pv_stmt = select(ProductVideo).where(
        ProductVideo.product_id == product_obj.id,
        ProductVideo.is_active.is_(True),
        ProductVideo.is_deleted.is_(False)
    ).order_by(ProductVideo.sort_order.asc())
    product_videos = list(db.session.execute(pv_stmt).scalars().all())

    return render_template('public/product.html',
        product=product_obj,
        images=images,
        specifications=specifications,
        related_products=related_products,
        related_posts=related_posts,
        comments=comments,
        in_wishlist=in_wishlist,
        breadcrumb_categories=breadcrumb_categories,
        product_videos=product_videos,
        seo=seo
    )


# ==================== BLOG ROUTES ====================

@public_bp.route('/blog/')
@public_bp.route('/blog/<int:page>')
@cache.cached(timeout=300, query_string=True)
def blog(page: int = 1) -> str:
    """Blog listing page."""
    per_page = current_app.config.get('ITEMS_PER_PAGE', 12)

    post_stmt = select(Post).where(
        Post.status == 'published',
        Post.is_active.is_(True),
        Post.is_deleted.is_(False)
    ).order_by(Post.published_at.desc())
    posts = db.paginate(post_stmt, page=page, per_page=per_page, error_out=False)

    cat_stmt = select(Category).where(
        Category.is_active.is_(True),
        Category.is_deleted.is_(False)
    ).order_by(Category.title.asc())
    categories = list(db.session.execute(cat_stmt).scalars().all())

    pop_stmt = select(Post).where(
        Post.status == 'published',
        Post.is_active.is_(True),
        Post.is_deleted.is_(False)
    ).order_by(Post.views.desc()).limit(5)
    popular_posts = list(db.session.execute(pop_stmt).scalars().all())

    return render_template('public/blog.html', en_url='/en/blog',
        posts=posts,
        categories=categories,
        popular_posts=popular_posts
    )


@public_bp.route('/blog/<slug>')
@cache.cached(timeout=300, query_string=True)
def post(slug: str) -> str:
    """Blog post detail page."""
    post_stmt = select(Post).where(Post.slug == slug, Post.status == 'published', Post.is_active.is_(True), Post.is_deleted.is_(False))
    post_obj = db.session.execute(post_stmt).scalars().first()
    if not post_obj:
        abort(404)

    # Increment views
    post_obj.increment_views()

    # Get related posts
    related_posts = post_obj.get_related_posts(limit=3)

    # Get related products
    related_products = []
    if post_obj.category_id:
        from app.models.product import ProductCategory
        pc_stmt = select(ProductCategory.product_id).where(ProductCategory.category_id == post_obj.category_id).limit(4)
        product_ids = list(db.session.execute(pc_stmt).scalars().all())
        if product_ids:
            prod_stmt = select(Product).where(
                Product.id.in_(product_ids),
                Product.is_active.is_(True),
                Product.is_deleted.is_(False),
            ).limit(4)
            related_products = list(db.session.execute(prod_stmt).scalars().all())

    # Get comments
    comments = post_obj.comments.filter_by(
        is_approved=True,
        is_deleted=False
    ).order_by(db.desc('created_at')).all()

    # Previous and next posts
    prev_stmt = select(Post).where(
        Post.id < post_obj.id,
        Post.status == 'published',
        Post.is_deleted.is_(False)
    ).order_by(Post.id.desc()).limit(1)
    prev_post = db.session.execute(prev_stmt).scalars().first()

    next_stmt = select(Post).where(
        Post.id > post_obj.id,
        Post.status == 'published',
        Post.is_deleted.is_(False)
    ).order_by(Post.id.asc()).limit(1)
    next_post = db.session.execute(next_stmt).scalars().first()

    seo = SEOService.get_post_seo(post_obj)

    return render_template('public/post.html',
        post=post_obj,
        related_posts=related_posts,
        related_products=related_products,
        comments=comments,
        prev_post=prev_post,
        next_post=next_post,
        seo=seo
    )


@public_bp.route('/blog/category/<slug>')
@public_bp.route('/blog/category/<slug>/<int:page>')
def blog_category(slug: str, page: int = 1) -> str:
    """Blog posts by category."""
    cat_stmt = select(Category).where(Category.slug == slug, Category.is_active.is_(True), Category.is_deleted.is_(False))
    category_obj = db.session.execute(cat_stmt).scalars().first()
    if not category_obj:
        abort(404)

    per_page = current_app.config.get('ITEMS_PER_PAGE', 12)
    post_stmt = select(Post).where(
        Post.category_id == category_obj.id,
        Post.status == 'published',
        Post.is_active.is_(True),
        Post.is_deleted.is_(False)
    ).order_by(Post.published_at.desc())

    posts = db.paginate(post_stmt, page=page, per_page=per_page, error_out=False)

    return render_template('public/blog_category.html',
        category=category_obj,
        posts=posts
    )


# ==================== SEARCH ====================

@public_bp.route('/search')
@cache.cached(timeout=60, query_string=True)
def search() -> str:
    """Search page across products and articles."""
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    search_type = request.args.get('type', 'all')

    per_page = current_app.config.get('ITEMS_PER_PAGE', 20)

    products = None
    posts = None
    total_results = 0

    if query and len(query) >= 2:
        search_pattern = f'%{query}%'

        if search_type in ['all', 'products']:
            prod_stmt = select(Product).where(
                Product.is_active.is_(True),
                Product.is_deleted.is_(False),
                or_(
                    Product.title.ilike(search_pattern),
                    Product.short_description.ilike(search_pattern),
                    Product.sku.ilike(search_pattern)
                )
            ).order_by(Product.view_count.desc())
            products = db.paginate(prod_stmt, page=page, per_page=per_page, error_out=False)
            total_results += products.total

        if search_type in ['all', 'posts']:
            post_stmt = select(Post).where(
                Post.is_active.is_(True),
                Post.is_deleted.is_(False),
                Post.status == 'published',
                or_(
                    Post.title.ilike(search_pattern),
                    Post.excerpt.ilike(search_pattern)
                )
            ).order_by(Post.views.desc())
            posts = db.paginate(post_stmt, page=page, per_page=per_page, error_out=False)
            total_results += posts.total

    return render_template('public/search.html',
        query=query,
        products=products,
        posts=posts,
        total_results=total_results,
        search_type=search_type
    )
    
    return render_template('public/search.html',
        query=query,
        products=products,
        posts=posts,
        total_results=total_results,
        search_type=search_type
    )


# ==================== CART & CHECKOUT ====================

@public_bp.route('/cart', methods=['GET', 'POST'])
def cart():
    """Shopping cart page — POST = add product to cart (فرم دکمهٔ خرید صفحه محصول)"""

    if request.method == 'POST':
        product_id = request.form.get('product_id', type=int)
        quantity = request.form.get('quantity', 1, type=int) or 1
        quantity = max(1, min(quantity, 99))

        if not product_id:
            flash('محصول مشخص نیست.', 'error')
            return redirect(url_for('public.cart'))

        added = CartService.add_to_cart(
            product_id, quantity,
            current_user.id if current_user.is_authenticated else None,
        )
        if added:
            flash('محصول به سبد خرید اضافه شد.', 'success')
        else:
            flash('این محصول در دسترس نیست یا موجود نیست.', 'error')
        return redirect(url_for('public.cart'))

    cart_items = []
    cart_total = 0

    if current_user.is_authenticated:
        cart_items = CartService.get_user_cart(current_user.id)
        cart_total = CartService.get_user_cart_total(current_user.id)
    else:
        cart_items = CartService.get_session_cart(CartService.get_session_id())
        cart_total = CartService.get_session_cart_total(CartService.get_session_id())

    return render_template('public/cart.html',
        cart_items=cart_items,
        cart_total=cart_total
    )


@public_bp.route('/compare')
def compare() -> str:
    """Product comparison page."""
    if not current_user.is_authenticated:
        return render_template('public/compare.html', products=[])

    comp_stmt = select(Comparison).where(Comparison.user_id == current_user.id)
    comparisons = list(db.session.execute(comp_stmt).scalars().all())
    products = [c.product for c in comparisons if c.product and not c.product.is_deleted]

    return render_template('public/compare.html', products=products)


# ==================== CHECKOUT ====================

@public_bp.route('/checkout', methods=['GET', 'POST'])
@rate_limit(limit=10, period=600, key_func=lambda: f'checkout:{request.remote_addr}')
def checkout():
    """
    Checkout — convert cart to order, choose payment method, redirect to gateway.

    GET: show checkout form
    POST: validate address, create order, redirect to payment
    """
    from app.services.checkout_service import CheckoutService, CheckoutError
    from app.services.payment_gateway import list_available_gateways
    from app.constants import PaymentMethod

    # ---- 1. Get cart ----
    if current_user.is_authenticated:
        cart_items = CartService.get_user_cart(current_user.id)
    else:
        # Guest checkout: allow, but collect email
        cart_items = CartService.get_session_cart(CartService.get_session_id())

    if not cart_items:
        flash('سبد خرید شما خالی است.', 'warning')
        return redirect(url_for('public.cart'))

    def _item_total(item) -> float:
        # CartItem (کاربر) یا dict سبد مهمان {product, quantity}
        if hasattr(item, 'total'):
            return item.total
        product = item.get('product')
        return float(product.current_price or 0) * item.get('quantity', 1) if product else 0.0

    cart_total = sum(_item_total(item) for item in cart_items)

    # ---- 2. Get default address for logged-in users ----
    default_address = None
    if current_user.is_authenticated:
        addr_stmt = select(Address).where(
            Address.user_id == current_user.id,
            Address.is_default.is_(True),
            Address.is_deleted.is_(False)
        )
        default_address = db.session.execute(addr_stmt).scalars().first()

    if request.method == 'POST':
        # ---- 3. Build shipping address from form ----
        shipping_address = {
            'recipient_name': (request.form.get('recipient_name') or '').strip(),
            'recipient_phone': (request.form.get('recipient_phone') or '').strip(),
            'province': (request.form.get('province') or '').strip(),
            'city': (request.form.get('city') or '').strip(),
            'postal_code': (request.form.get('postal_code') or '').strip(),
            'address': (request.form.get('address') or '').strip(),
        }

        payment_method = request.form.get('payment_method', PaymentMethod.ONLINE.value)
        customer_note = (request.form.get('customer_note') or '').strip()
        discount_code = (request.form.get('discount_code') or '').strip()

        # ---- 4. Create order ----
        try:
            order = CheckoutService.create_order_from_cart(
                user=current_user if current_user.is_authenticated else None,
                cart_items=cart_items,
                shipping_address=shipping_address,
                payment_method=payment_method,
                customer_note=customer_note,
                discount_code=discount_code,
            )
        except CheckoutError as e:
            flash(e.message, 'error')
            return render_template(
                'public/checkout.html',
                cart_items=cart_items,
                cart_total=cart_total,
                default_address=default_address,
                payment_gateways=list_available_gateways(),
                form_data=shipping_address,
            )

        # ---- 5. Handle payment method ----
        if payment_method == PaymentMethod.CASH.value:
            # Cash on delivery: clear cart, go to confirmation
            CheckoutService.clear_user_cart(current_user if current_user.is_authenticated else None)
            flash(f'سفارش {order.order_number} با موفقیت ثبت شد. پرداخت در محل انجام خواهد شد.', 'success')
            return redirect(url_for('public.order_success', order_number=order.order_number))

        if payment_method == PaymentMethod.CARD.value:
            # Bank card: clear cart, show instructions, go to confirmation
            CheckoutService.clear_user_cart(current_user if current_user.is_authenticated else None)
            flash(f'سفارش {order.order_number} ثبت شد. لطفاً طبق راهنما پرداخت کنید.', 'info')
            return redirect(url_for('public.order_card_payment', order_number=order.order_number))

        # Online payment: redirect to the selected gateway
        from app.services.payment_gateway import get_gateway
        available = list_available_gateways()
        gateway_name = (request.form.get('gateway') or '').strip()
        if gateway_name:
            # انتخاب صریح کاربر — اگر در دسترس نبود، به درگاه دیگری سقوط نکن
            if gateway_name not in [g['id'] for g in available]:
                flash('درگاه پرداخت انتخابی در دسترس نیست. سفارش ثبت شد؛ از صفحه سفارش دوباره تلاش کنید.', 'error')
                return redirect(url_for('public.order_success', order_number=order.order_number))
        else:
            gateway_name = available[0]['id'] if available else 'mock'

        gateway = get_gateway(gateway_name)
        callback_url = url_for('public.payment_callback', order_number=order.order_number, _external=True)
        result = gateway.create_payment(order, callback_url)

        if not result.success:
            # Gateway unavailable: show order, but mark transaction failed
            current_app.logger.error(f'Gateway error: {result.error_message}')
            flash(f'خطا در اتصال به درگاه پرداخت: {result.error_message}', 'error')
            return redirect(url_for('public.order_success', order_number=order.order_number))

        # Update transaction with gateway reference
        from app.models import PaymentTransaction
        from app.constants import TransactionStatus
        transaction = order.transactions.first()
        if transaction:
            transaction.reference_id = result.transaction_id
            transaction.gateway = gateway.gateway_name
            transaction.status = TransactionStatus.PENDING.value
            transaction.gateway_response = result.raw_response or None
            transaction.save()

        # درگاه‌های شاپرک (سپه) کاربر را با POST فرم می‌گیرند نه ریدایرکت ساده
        if result.redirect_method == 'form' and result.form_url:
            session[f'pay_form_{order.order_number}'] = {
                'url': result.form_url,
                'fields': result.form_fields or {},
            }
            return redirect(url_for('public.payment_redirect', order_number=order.order_number))

        return redirect(result.redirect_url)

    # ---- GET: show checkout form ----
    return render_template(
        'public/checkout.html',
        cart_items=cart_items,
        cart_total=cart_total,
        default_address=default_address,
        payment_gateways=list_available_gateways(),
    )


@public_bp.route('/order/<order_number>/success')
def order_success(order_number: str) -> str:
    """Order confirmation page (after successful payment or COD)."""
    from app.services.order_service import OrderService

    order = OrderService.get_by_number(order_number)
    if not order:
        abort(404)

    # Authorization: only order owner or admin
    if order.user_id and current_user.is_authenticated and order.user_id != current_user.id and not current_user.is_admin():
        abort(404)

    return render_template('public/order_success.html', order=order)


@public_bp.route('/order/<order_number>/card-payment')
def order_card_payment(order_number: str) -> str:
    """Show bank card payment instructions."""
    from app.services.order_service import OrderService

    order = OrderService.get_by_number(order_number)
    if not order:
        abort(404)

    if order.user_id and current_user.is_authenticated and order.user_id != current_user.id and not current_user.is_admin():
        abort(404)

    # Get bank card info from settings
    from app.models import Setting
    card_number = Setting.get_value('payment', 'bank_card_number', '') or 'شماره کارت را از تنظیمات پنل وارد کنید'
    card_holder = Setting.get_value('payment', 'bank_card_holder', '') or ''
    site_name = Setting.get_value('general', 'site_name', 'فروشگاه')

    return render_template(
        'public/order_card_payment.html',
        order=order,
        card_number=card_number,
        card_holder=card_holder,
        site_name=site_name,
    )


@public_bp.route('/payment/mock/<order_number>', methods=['GET', 'POST'])
def payment_mock(order_number: str):
    """Mock payment page — simulates a gateway for development."""
    from app.models import PaymentTransaction
    from app.services.order_service import OrderService
    from app.services.checkout_service import CheckoutService
    from app.services.payment_gateway import get_gateway
    from app.constants import TransactionStatus, PaymentStatus, OrderStatus

    order = OrderService.get_by_number(order_number)
    if not order:
        abort(404)

    txn_stmt = select(PaymentTransaction).where(PaymentTransaction.order_id == order.id)
    transaction = db.session.execute(txn_stmt).scalars().first()
    if not transaction:
        abort(404)

    if request.method == 'POST':
        action = request.form.get('action', 'pay')
        ref = request.args.get('ref', transaction.reference_id)

        gateway = get_gateway('mock')
        if action == 'pay':
            result = gateway.verify_payment(transaction, {'status': 'success', 'ref': ref})
        else:
            result = gateway.verify_payment(transaction, {'status': 'cancelled', 'ref': ref})

        if result.success:
            transaction.status = TransactionStatus.SUCCESS.value
            transaction.paid_at = datetime.utcnow()
            transaction.gateway_response = result.raw_response
            transaction.save()

            order.mark_paid(reference=ref)
            order.status = OrderStatus.CONFIRMED.value
            order.confirmed_at = datetime.utcnow()
            order.save()

            CheckoutService.clear_user_cart(current_user if current_user.is_authenticated else None)

            # Send confirmation email
            try:
                from app.services.notification_service import NotificationService
                NotificationService.send_order_confirmation(order)
            except Exception as e:
                current_app.logger.warning(f'Order confirmation email failed: {e}')

            return redirect(url_for('public.order_success', order_number=order.order_number))
        else:
            transaction.status = TransactionStatus.CANCELLED.value
            transaction.save()
            order.payment_status = PaymentStatus.FAILED.value
            order.save()
            flash('پرداخت لغو شد. می‌توانید مجدداً تلاش کنید.', 'warning')
            return redirect(url_for('public.order_success', order_number=order.order_number))

    return render_template(
        'public/payment_mock.html',
        order=order,
        transaction=transaction,
    )


@public_bp.route('/payment/callback/<order_number>', methods=['GET', 'POST'])
def payment_callback(order_number: str):
    """
    کال‌بک رسمی درگاه‌های پرداخت.
    """
    from app.models import PaymentTransaction
    from app.services.order_service import OrderService
    from app.services.checkout_service import CheckoutService
    from app.services.payment_gateway import get_gateway, _callback_payload
    from app.constants import TransactionStatus, PaymentStatus, OrderStatus

    order = OrderService.get_by_number(order_number)
    if not order:
        abort(404)

    txn_stmt = select(PaymentTransaction).where(PaymentTransaction.order_id == order.id).order_by(PaymentTransaction.id.desc())
    transaction = db.session.execute(txn_stmt).scalars().first()
    if not transaction:
        abort(404)

    # اگر قبلاً تأیید شده، دوباره پردازش نکن (idempotent)
    if transaction.status == TransactionStatus.SUCCESS.value:
        return redirect(url_for('public.order_success', order_number=order_number))

    callback_data = _callback_payload()
    gateway = get_gateway(transaction.gateway or 'mock')
    current_app.logger.info(
        f'Payment callback [{gateway.gateway_name}] order={order_number} data={callback_data}'
    )
    result = gateway.verify_payment(transaction, callback_data)

    if result.success:
        transaction.status = TransactionStatus.SUCCESS.value
        transaction.paid_at = datetime.utcnow()
        transaction.gateway_response = result.raw_response or transaction.gateway_response
        tracking = (
            result.raw_response.get('ref_id')      # زرین‌پال
            or result.raw_response.get('track_id')  # آی‌دی‌پی
            or result.raw_response.get('trackingCode')  # دیجی‌پی
            or result.raw_response.get('RefNum')    # سپه
            or result.transaction_id
        )
        transaction.tracking_code = str(tracking or '')[:255] or None
        transaction.save()

        order.mark_paid(reference=str(tracking or transaction.reference_id or ''))
        order.status = OrderStatus.CONFIRMED.value
        order.confirmed_at = datetime.utcnow()
        order.save()

        CheckoutService.clear_user_cart(current_user if current_user.is_authenticated else None)

        try:
            from app.services.notification_service import NotificationService
            NotificationService.send_order_confirmation(order)
        except Exception as e:
            current_app.logger.warning(f'Order confirmation email failed: {e}')

        flash(f'پرداخت سفارش {order.order_number} با موفقیت تأیید شد.', 'success')
    else:
        cancelled = result.error_code in ('cancelled', 'cancelled_by_user')
        transaction.status = (
            TransactionStatus.CANCELLED.value if cancelled else TransactionStatus.FAILED.value
        )
        transaction.gateway_response = {'callback': callback_data, 'error': result.to_dict()}
        transaction.save()

        order.payment_status = PaymentStatus.FAILED.value
        order.save()

        current_app.logger.warning(
            f'Payment failed [{gateway.gateway_name}] order={order_number}: '
            f'{result.error_code} — {result.error_message}'
        )
        flash(result.error_message or 'پرداخت ناموفق بود. در صورت کسر مبلغ، طی ۷۲ ساعت بازگشت داده می‌شود.', 'error')

    return redirect(url_for('public.order_success', order_number=order_number))


@public_bp.route('/payment/redirect/<order_number>')
def payment_redirect(order_number: str):
    """
    صفحهٔ واسط برای درگاه‌هایی که کاربر باید با POST فرم به آن‌ها هدایت شود
    """
    from app.services.order_service import OrderService

    order = OrderService.get_by_number(order_number)
    if not order:
        abort(404)

    form_data = session.get(f'pay_form_{order_number}')
    if not form_data or not form_data.get('url'):
        flash('نشست پرداخت منقضی شده است. لطفاً دوباره تلاش کنید.', 'warning')
        return redirect(url_for('public.order_pay', order_number=order_number))

    session.pop(f'pay_form_{order_number}', None)
    return render_template(
        'public/payment_redirect.html',
        order=order,
        form_url=form_data['url'],
        form_fields=form_data.get('fields', {}),
    )


@public_bp.route('/order/<order_number>/pay', methods=['GET', 'POST'])
@rate_limit(limit=5, period=3600, key_func=lambda: f'repay:{request.remote_addr}')
def order_pay(order_number: str):
    """پرداخت مجدد سفارش پرداخت‌نشده."""
    from app.models import PaymentTransaction
    from app.services.order_service import OrderService
    from app.services.payment_gateway import get_gateway, list_available_gateways
    from app.constants import TransactionStatus

    order = OrderService.get_by_number(order_number)
    if not order:
        abort(404)

    if order.user_id and current_user.is_authenticated and order.user_id != current_user.id and not current_user.is_admin():
        abort(404)
    if order.payment_status in ('paid',) or order.status in ('delivered', 'cancelled', 'refunded'):
        flash('این سفارش نیاز به پرداخت ندارد.', 'info')
        return redirect(url_for('public.order_success', order_number=order_number))

    available = list_available_gateways()
    gateway_name = request.form.get('gateway') or request.args.get('gateway') or ''
    if gateway_name not in [g['id'] for g in available]:
        txn_stmt = select(PaymentTransaction).where(PaymentTransaction.order_id == order.id).order_by(PaymentTransaction.id.desc())
        last_txn = db.session.execute(txn_stmt).scalars().first()
        prev = last_txn.gateway if last_txn else ''
        gateway_name = prev if prev in [g['id'] for g in available] else (
            available[0]['id'] if available else 'mock'
        )

    gateway = get_gateway(gateway_name)
    callback_url = url_for('public.payment_callback', order_number=order.order_number, _external=True)
    result = gateway.create_payment(order, callback_url)

    if not result.success:
        flash(f'خطا در اتصال به درگاه پرداخت: {result.error_message}', 'error')
        return redirect(url_for('public.order_success', order_number=order_number))

    transaction = order.transactions.order_by(PaymentTransaction.id.desc()).first()
    if transaction:
        transaction.status = TransactionStatus.PENDING.value
        transaction.gateway = gateway.gateway_name
        transaction.reference_id = result.transaction_id
        transaction.gateway_response = result.raw_response or None
        transaction.save()

    if result.redirect_method == 'form' and result.form_url:
        session[f'pay_form_{order.order_number}'] = {
            'url': result.form_url,
            'fields': result.form_fields or {},
        }
        return redirect(url_for('public.payment_redirect', order_number=order.order_number))

    return redirect(result.redirect_url)


@public_bp.route('/order/<order_number>/cancel', methods=['POST'])
@rate_limit(limit=5, period=3600, key_func=lambda: f'cancel_order:{request.remote_addr}')
def cancel_order(order_number: str):
    """Allow user to cancel their own order."""
    from app.services.order_service import OrderService
    from app.services.checkout_service import CheckoutService, CheckoutError

    order = OrderService.get_by_number(order_number)
    if not order:
        abort(404)

    if order.user_id and current_user.is_authenticated and order.user_id != current_user.id and not current_user.is_admin():
        abort(403)

    reason = request.form.get('reason', '').strip()

    try:
        CheckoutService.cancel_order(order, reason=reason, user=current_user if current_user.is_authenticated else None)
        flash(f'سفارش {order.order_number} لغو شد.', 'success')
    except CheckoutError as e:
        flash(e.message, 'error')

    return redirect(url_for('user.dashboard' if current_user.is_authenticated else 'public.home'))


# ==================== STATIC PAGES ====================

@public_bp.route('/about')
def about() -> str:
    """About us page."""
    from app.models import TeamMember
    page_stmt = select(Page).where(Page.page_type == 'about', Page.is_active.is_(True), Page.is_deleted.is_(False))
    page_obj = db.session.execute(page_stmt).scalars().first()

    tm_stmt = select(TeamMember).where(
        TeamMember.is_active.is_(True), TeamMember.is_deleted.is_(False)
    ).order_by(TeamMember.sort_order.asc())
    team_members = list(db.session.execute(tm_stmt).scalars().all())

    return render_template('public/about.html', en_url='/en/about', page=page_obj, team_members=team_members)


@public_bp.route('/contact', methods=['GET', 'POST'])
@rate_limit(limit=5, period=3600, key_func=lambda: f'contact:{request.remote_addr}')
def contact():
    """Contact us page."""
    from app.blueprints.public.forms import ContactForm
    from app.services.notification_service import NotificationService

    form = ContactForm()

    if form.validate_on_submit():
        from app.models import Contact
        from app.constants import PHONE_PATTERN_IR, PHONE_LANDLINE_IR
        import re

        phone = (form.phone.data or '').strip()
        if phone and not re.match(PHONE_PATTERN_IR, phone) and not re.match(PHONE_LANDLINE_IR, phone):
            flash('شماره تلفن وارد شده نامعتبر است.', 'error')
            page_stmt = select(Page).where(Page.page_type == 'contact', Page.is_active.is_(True), Page.is_deleted.is_(False))
            page = db.session.execute(page_stmt).scalars().first()
            return render_template('public/contact.html', en_url='/en/contact', form=form, page=page, success=False)

        try:
            contact_obj = Contact(
                name=form.name.data,
                email=form.email.data,
                phone=phone or None,
                subject=form.subject.data,
                message=form.message.data,
                ip_address=request.remote_addr,
            )
            contact_obj.save()

            NotificationService.notify_admins(
                title='پیام جدید تماس با ما',
                message=f'{form.name.data} - {form.subject.data}',
                type='message',
                data={'contact_id': contact_obj.id}
            )

            try:
                # ارسال تلگرام بیرون از request path — با Celery صف می‌شود و
                # در حالت غیرفعال به‌صورت همگام اجرا می‌گردد.
                from app.tasks import enqueue
                from app.tasks.notify_tasks import telegram_contact_task
                enqueue(telegram_contact_task, contact_obj.id)
            except Exception as e:
                current_app.logger.warning(f'Telegram notify failed: {e}')

            return render_template('public/contact.html', en_url='/en/contact',
                form=ContactForm(),
                success=True)
        except Exception as e:
            current_app.logger.error(f'Contact save error: {e}')
            flash('خطا در ارسال پیام. لطفاً مجدداً تلاش کنید.', 'error')

    page_stmt = select(Page).where(Page.page_type == 'contact', Page.is_active.is_(True), Page.is_deleted.is_(False))
    page = db.session.execute(page_stmt).scalars().first()

    return render_template('public/contact.html', en_url='/en/contact',
        form=form,
        page=page,
        success=False)


@public_bp.route('/faq')
@cache.cached(timeout=300)
def faq() -> str:
    """FAQ page."""
    faq_stmt = select(FAQ).where(
        FAQ.is_active.is_(True),
        FAQ.is_deleted.is_(False)
    ).order_by(FAQ.sort_order.asc())
    faqs = list(db.session.execute(faq_stmt).scalars().all())

    faq_categories = {}
    for f in faqs:
        cat = f.category or 'عمومی'
        if cat not in faq_categories:
            faq_categories[cat] = []
        faq_categories[cat].append(f)

    return render_template('public/faq.html', faqs=faqs, faq_categories=faq_categories, en_url='/en/faq')


@public_bp.route('/terms')
def terms() -> str:
    """Terms and conditions page."""
    page_stmt = select(Page).where(Page.page_type == 'terms', Page.is_active.is_(True), Page.is_deleted.is_(False))
    page = db.session.execute(page_stmt).scalars().first()
    if not page:
        abort(404)
    return render_template('public/page.html', page=page)


@public_bp.route('/privacy')
def privacy() -> str:
    """Privacy policy page."""
    page_stmt = select(Page).where(Page.page_type == 'privacy', Page.is_active.is_(True), Page.is_deleted.is_(False))
    page = db.session.execute(page_stmt).scalars().first()
    if not page:
        abort(404)
    return render_template('public/page.html', page=page)


# ==================== SITEMAP & ROBOTS ====================

@public_bp.route('/sitemap.xml')
def sitemap():
    """XML Sitemap."""
    from app.services.seo_service import SEOService
    sitemap_xml = SEOService.generate_sitemap()
    return sitemap_xml, 200, {'Content-Type': 'application/xml'}


@public_bp.route('/robots.txt')
def robots():
    """Robots.txt file."""
    site_url = current_app.config.get('SITE_URL', request.url_root.rstrip('/'))

    content = f"""User-agent: *
Allow: /
Disallow: /admin/
Disallow: /user/
Disallow: /api/
Disallow: /cart
Disallow: /checkout
Disallow: /order/
Disallow: /payment/
Disallow: /login
Disallow: /register
Disallow: /forgot-password
Disallow: /reset-password
Disallow: /change-password

# AI crawlers
User-agent: GPTBot
Allow: /

User-agent: PerplexityBot
Allow: /

Sitemap: {site_url}/sitemap.xml"""

    return content, 200, {'Content-Type': 'text/plain'}


# ==================== API ENDPOINTS ====================

@public_bp.route('/api/quick-search')
def api_quick_search():
    """Quick search API for autocomplete."""
    query = request.args.get('q', '').strip()

    if not query or len(query) < 2:
        return jsonify({'results': []})

    search_pattern = f'%{query}%'

    prod_stmt = select(Product).where(
        Product.is_active.is_(True),
        Product.is_deleted.is_(False),
        Product.title.ilike(search_pattern)
    ).limit(5)
    products = list(db.session.execute(prod_stmt).scalars().all())

    cat_stmt = select(Category).where(
        Category.is_active.is_(True),
        Category.is_deleted.is_(False),
        Category.title.ilike(search_pattern)
    ).limit(3)
    categories = list(db.session.execute(cat_stmt).scalars().all())

    results_list = []
    for p in products:
        results_list.append({
            'id': p.id,
            'title': p.title,
            'url': f'/product/{p.slug}',
            'price': f'{int(p.current_price):,} تومان' if p.current_price else 'استعلام قیمت',
            'image': p.main_image_url,
            'type': 'product'
        })
    for c in categories:
        results_list.append({
            'id': c.id,
            'title': c.title,
            'url': f'/category/{c.slug}',
            'price': 'دسته‌بندی خدمات',
            'type': 'category'
        })

    return jsonify({'results': results_list})


@public_bp.route('/api/price-history/<int:product_id>')
def api_price_history(product_id: int):
    """Get price history for a product."""
    return jsonify({'prices': []})


# ==================== PRICE COMPARISON FEEDS ====================

@public_bp.route('/feed/torob.xml')
def feed_torob():
    """Generate Torob-compatible XML feed."""
    from app.services.export_service import ExportService
    xml = ExportService.generate_torob_feed()
    return xml, 200, {'Content-Type': 'application/xml'}


@public_bp.route('/feed/emalls.xml')
def feed_emalls():
    """Generate Emalls-compatible XML feed."""
    from app.services.export_service import ExportService
    xml = ExportService.generate_emalls_feed()
    return xml, 200, {'Content-Type': 'application/xml'}


@public_bp.route('/feed/products.json')
def feed_products():
    """Generate JSON feed for products."""
    from app.services.export_service import ExportService
    json_data = ExportService.generate_json_feed()
    return jsonify(json_data)


# ==================== NEWSLETTER ====================

@public_bp.route('/newsletter/subscribe', methods=['POST'])
@rate_limit(limit=5, period=600, key_func=lambda: f'newsletter:{request.remote_addr}')
def newsletter_subscribe():
    """Subscribe email to newsletter (AJAX/form)."""
    from app.models.features import Subscriber
    import re

    email = (request.form.get('email') or (request.get_json(silent=True) or {}).get('email') or '').strip().lower()

    if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'message': 'ایمیل معتبر وارد کنید'}), 400
        flash('ایمیل معتبر وارد کنید.', 'error')
        return redirect(request.referrer or url_for('public.home'))

    sub_stmt = select(Subscriber).where(Subscriber.email == email)
    existing = db.session.execute(sub_stmt).scalars().first()

    if existing:
        existing.unsubscribed_at = None
        existing.save()
        message = 'ایمیل شما قبلاً ثبت شده بود — دوباره فعال شد. سپاس!'
    else:
        Subscriber(email=email, source=request.form.get('source', 'footer'),
                   ip_address=request.remote_addr).save()
        message = 'عضویت شما در خبرنامه ثبت شد. سپاس از همراهی!'

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({'success': True, 'message': message})

    flash(message, 'success')
    return redirect(request.referrer or url_for('public.home'))


# ==================== STORIES ====================

@public_bp.route('/stories/<int:story_id>/view', methods=['POST'])
def story_view(story_id: int):
    """Increment story views (AJAX)."""
    from app.models.features import Story
    story = db.session.get(Story, story_id)
    if not story:
        abort(404)
    story.views = (story.views or 0) + 1
    db.session.commit()
    return jsonify({'success': True, 'views': story.views})


# ==================== INFRA HEALTH ====================

@public_bp.route('/healthz', methods=['GET'])
def healthz():
    """Health endpoint for load-balancers / container orchestration.

    مسیر استاندارد کنار `/` تا healthcheck داکر و LB بدون فرض پیشوند API
    کار کند. منطق بررسی کامل در ``HealthService`` است؛ این روت فقط پروب‌ها را
    صدا زده و وضعیت HTTP را برمی‌گرداند (503 فقط وقتی دیتابیس down باشد).
    """
    from app.services.health_service import HealthService

    body, status = HealthService.snapshot()
    return jsonify(body), status
