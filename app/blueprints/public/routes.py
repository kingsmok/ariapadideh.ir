"""
Public Routes - Main Site Pages
"""
from flask import render_template, request, abort, jsonify, current_app
from flask_login import current_user
from sqlalchemy import or_, func
from app.blueprints.public import public_bp
from app.extensions import db, cache
from app.models import (
    Product, Category, Brand, Post, Page, Menu, Slider, 
    SliderItem, Banner, FAQ, Setting, ProductImage, Tag, Wishlist
)
from app.services.seo_service import SEOService
from app.services.cart_service import CartService
from app.utils.helpers import get_pagination_params
from app.utils.decorators import rate_limit


# ==================== HOME PAGE ====================

@public_bp.route('/')
@cache.cached(timeout=300, query_string=True)
def home():
    """Home page with dynamic components"""
    
    # Get home page data
    home_page = Page.query.filter_by(page_type='home', is_active=True, is_deleted=False).first()
    
    # Get active sliders
    sliders = Slider.query.filter_by(position='home', is_active=True, is_deleted=False).first()
    slider_items = []
    if sliders:
        slider_items = SliderItem.query.filter_by(
            slider_id=sliders.id, 
            is_active=True, 
            is_deleted=False
        ).order_by(SliderItem.sort_order).all()
    
    # Get featured products
    featured_products = Product.query.filter_by(
        is_featured=True, 
        is_active=True, 
        is_deleted=False
    ).order_by(Product.sort_order).limit(8).all()
    
    # Get new products
    new_products = Product.query.filter_by(
        is_new=True,
        is_active=True, 
        is_deleted=False
    ).order_by(Product.created_at.desc()).limit(8).all()
    
    # Get categories for mega menu
    categories = Category.query.filter_by(
        parent_id=None,
        is_active=True,
        is_deleted=False
    ).order_by(Category.sort_order).limit(12).all()
    
    # Get banners by position
    banners_top = Banner.query.filter_by(
        position='home_top',
        is_active=True,
        is_deleted=False
    ).order_by(Banner.sort_order).all()
    
    banners_middle = Banner.query.filter_by(
        position='home_middle',
        is_active=True,
        is_deleted=False
    ).order_by(Banner.sort_order).all()
    
    banners_bottom = Banner.query.filter_by(
        position='home_bottom',
        is_active=True,
        is_deleted=False
    ).order_by(Banner.sort_order).all()
    
    # Get latest posts
    latest_posts = Post.query.filter_by(
        status='published',
        is_active=True,
        is_deleted=False,
        show_in_home=True
    ).order_by(Post.published_at.desc()).limit(3).all()
    
    # Get FAQs
    faqs = FAQ.query.filter_by(
        is_active=True,
        is_deleted=False,
        is_featured=True
    ).limit(5).all()
    
    # Get cart items count
    cart_items_count = 0
    if current_user.is_authenticated:
        cart_items_count = CartService.get_user_cart_count(current_user.id)
    else:
        session_cart = CartService.get_session_cart_count(request.sid)
        cart_items_count = session_cart
    
    seo = SEOService.get_seo_data('home')
    
    return render_template('public/home.html',
        page=home_page,
        sliders=slider_items,
        featured_products=featured_products,
        new_products=new_products,
        categories=categories,
        banners_top=banners_top,
        banners_middle=banners_middle,
        banners_bottom=banners_bottom,
        latest_posts=latest_posts,
        faqs=faqs,
        cart_items_count=cart_items_count,
        seo=seo
    )


# ==================== PAGE ROUTES ====================

@public_bp.route('/<slug>')
@cache.cached(timeout=300, query_string=True)
def page(slug):
    """Dynamic page by slug"""
    
    page_obj = Page.query.filter_by(slug=slug, is_active=True, is_deleted=False).first_or_404()
    
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
def categories_list():
    """All categories listing"""
    
    parent_categories = Category.query.filter_by(
        parent_id=None,
        is_active=True,
        is_deleted=False
    ).order_by(Category.sort_order).all()
    
    all_categories = Category.query.filter_by(
        is_active=True,
        is_deleted=False
    ).order_by(Category.sort_order).all()
    
    return render_template('public/categories.html',
        parent_categories=parent_categories,
        all_categories=all_categories
    )


@public_bp.route('/category/<slug>')
@public_bp.route('/category/<slug>/<int:page>')
@cache.cached(timeout=300, query_string=True)
def category(slug, page=1):
    """Category page with products"""
    
    category_obj = Category.query.filter_by(slug=slug, is_active=True, is_deleted=False).first_or_404()
    
    per_page = current_app.config.get('ITEMS_PER_PAGE', 20)
    
    # Build query
    query = category_obj.products.filter(
        Product.is_active == True,
        Product.is_deleted == False
    )
    
    # Filters
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    brand_ids = request.args.getlist('brand', type=int)
    in_stock = request.args.get('in_stock', type=int)
    sort = request.args.get('sort', 'newest')
    
    if min_price:
        query = query.filter(Product.price >= min_price)
    if max_price:
        query = query.filter(Product.price <= max_price)
    if brand_ids:
        query = query.filter(Product.brand_id.in_(brand_ids))
    if in_stock:
        query = query.filter(Product.stock_quantity > 0)
    
    # Sorting
    sort_options = {
        'newest': Product.created_at.desc(),
        'price_asc': Product.price.asc(),
        'price_desc': Product.price.desc(),
        'popular': Product.view_count.desc(),
        'rating': Product.rating_avg.desc()
    }
    query = query.order_by(sort_options.get(sort, Product.created_at.desc()))
    
    # Paginate
    products = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Get child categories
    child_categories = category_obj.children.filter_by(
        is_active=True,
        is_deleted=False
    ).order_by(Category.sort_order).all() if category_obj.show_children else []
    
    # Get brands in this category
    brand_ids_in_category = [p.brand_id for p in category_obj.products.filter(
        Product.brand_id.isnot(None)
    ).all()]
    brands = Brand.query.filter(Brand.id.in_(brand_ids_in_category)).all() if brand_ids_in_category else []
    
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
def product(slug):
    """Product detail page"""
    
    product_obj = Product.query.filter_by(slug=slug, is_active=True, is_deleted=False).first_or_404()
    
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
        in_wishlist = Wishlist.query.filter_by(
            user_id=current_user.id,
            product_id=product_obj.id
        ).first() is not None
    
    # Get breadcrumb categories
    breadcrumb_categories = product_obj.categories[0].breadcrumbs if product_obj.categories else []
    
    seo = SEOService.get_product_seo(product_obj)
    
    return render_template('public/product.html',
        product=product_obj,
        images=images,
        specifications=specifications,
        related_products=related_products,
        comments=comments,
        in_wishlist=in_wishlist,
        breadcrumb_categories=breadcrumb_categories,
        seo=seo
    )


# ==================== BLOG ROUTES ====================

@public_bp.route('/blog/')
@public_bp.route('/blog/<int:page>')
@cache.cached(timeout=300, query_string=True)
def blog(page=1):
    """Blog listing page"""
    
    per_page = current_app.config.get('ITEMS_PER_PAGE', 12)
    
    # Get posts
    posts = Post.query.filter_by(
        status='published',
        is_active=True,
        is_deleted=False
    ).order_by(Post.published_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get categories
    categories = Category.query.filter_by(
        is_active=True,
        is_deleted=False
    ).order_by(Category.title).all()
    
    # Get popular posts
    popular_posts = Post.query.filter_by(
        status='published',
        is_active=True,
        is_deleted=False
    ).order_by(Post.views.desc()).limit(5).all()
    
    return render_template('public/blog.html',
        posts=posts,
        categories=categories,
        popular_posts=popular_posts
    )


@public_bp.route('/blog/<slug>')
@cache.cached(timeout=300, query_string=True)
def post(slug):
    """Blog post detail page"""
    
    post_obj = Post.query.filter_by(slug=slug, status='published', is_active=True, is_deleted=False).first_or_404()
    
    # Increment views
    post_obj.increment_views()
    
    # Get related posts
    related_posts = post_obj.get_related_posts(limit=3)
    
    # Get comments
    comments = post_obj.comments.filter_by(
        is_approved=True,
        is_deleted=False
    ).order_by(db.desc('created_at')).all()
    
    # Previous and next posts
    prev_post = Post.query.filter(
        Post.id < post_obj.id,
        Post.status == 'published',
        Post.is_deleted == False
    ).order_by(Post.id.desc()).first()
    
    next_post = Post.query.filter(
        Post.id > post_obj.id,
        Post.status == 'published',
        Post.is_deleted == False
    ).order_by(Post.id.asc()).first()
    
    seo = SEOService.get_post_seo(post_obj)
    
    return render_template('public/post.html',
        post=post_obj,
        related_posts=related_posts,
        comments=comments,
        prev_post=prev_post,
        next_post=next_post,
        seo=seo
    )


@public_bp.route('/blog/category/<slug>')
@public_bp.route('/blog/category/<slug>/<int:page>')
def blog_category(slug, page=1):
    """Blog posts by category"""
    
    category_obj = Category.query.filter_by(slug=slug, is_active=True, is_deleted=False).first_or_404()
    
    per_page = current_app.config.get('ITEMS_PER_PAGE', 12)
    
    posts = Post.query.filter_by(
        category_id=category_obj.id,
        status='published',
        is_active=True,
        is_deleted=False
    ).order_by(Post.published_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('public/blog_category.html',
        category=category_obj,
        posts=posts
    )


# ==================== SEARCH ====================

@public_bp.route('/search')
@cache.cached(timeout=60, query_string=True)
def search():
    """Search page"""
    
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    search_type = request.args.get('type', 'all')  # all, products, posts
    
    per_page = current_app.config.get('ITEMS_PER_PAGE', 20)
    
    products = None
    posts = None
    total_results = 0
    
    if query and len(query) >= 2:
        search_pattern = f'%{query}%'
        
        if search_type in ['all', 'products']:
            products = Product.query.filter(
                Product.is_active == True,
                Product.is_deleted == False,
                or_(
                    Product.title.ilike(search_pattern),
                    Product.short_description.ilike(search_pattern),
                    Product.sku.ilike(search_pattern)
                )
            ).order_by(Product.view_count.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            total_results += products.total
        
        if search_type in ['all', 'posts']:
            posts = Post.query.filter(
                Post.is_active == True,
                Post.is_deleted == False,
                Post.status == 'published',
                or_(
                    Post.title.ilike(search_pattern),
                    Post.excerpt.ilike(search_pattern)
                )
            ).order_by(Post.views.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            total_results += posts.total
    
    return render_template('public/search.html',
        query=query,
        products=products,
        posts=posts,
        total_results=total_results,
        search_type=search_type
    )


# ==================== CART & CHECKOUT ====================

@public_bp.route('/cart')
def cart():
    """Shopping cart page"""
    
    cart_items = []
    cart_total = 0
    
    if current_user.is_authenticated:
        cart_items = CartService.get_user_cart(current_user.id)
        cart_total = CartService.get_user_cart_total(current_user.id)
    else:
        cart_items = CartService.get_session_cart(request.sid)
        cart_total = CartService.get_session_cart_total(request.sid)
    
    return render_template('public/cart.html',
        cart_items=cart_items,
        cart_total=cart_total
    )


@public_bp.route('/compare')
def compare():
    """Product comparison page"""
    
    if not current_user.is_authenticated:
        return render_template('public/compare.html', products=[])
    
    comparisons = Comparison.query.filter_by(user_id=current_user.id).all()
    products = [c.product for c in comparisons if c.product]
    
    return render_template('public/compare.html', products=products)


# ==================== STATIC PAGES ====================

@public_bp.route('/about')
def about():
    """About us page"""
    
    page = Page.query.filter_by(page_type='about', is_active=True, is_deleted=False).first_or_404()
    
    return render_template('public/page.html', page=page)


@public_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact us page"""
    
    from app.blueprints.public.forms import ContactForm
    from app.services.notification_service import NotificationService
    
    form = ContactForm()
    
    if form.validate_on_submit():
        from app.models import Contact, Address
        
        contact_obj = Contact(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            subject=form.subject.data,
            message=form.message.data,
            ip_address=request.remote_addr
        )
        contact_obj.save()
        
        # Notify admins
        NotificationService.notify_admins(
            title='پیام جدید تماس با ما',
            message=f'{form.name.data} - {form.subject.data}',
            type='message',
            data={'contact_id': contact_obj.id}
        )
        
        return render_template('public/contact.html', 
            form=ContactForm(), 
            success=True)
    
    page = Page.query.filter_by(page_type='contact', is_active=True, is_deleted=False).first()
    
    return render_template('public/contact.html', 
        form=form, 
        page=page,
        success=False)


@public_bp.route('/faq')
@cache.cached(timeout=300)
def faq():
    """FAQ page"""
    
    faqs = FAQ.query.filter_by(
        is_active=True,
        is_deleted=False
    ).order_by(FAQ.sort_order).all()
    
    # Group by category
    faq_categories = {}
    for faq in faqs:
        cat = faq.category or 'عمومی'
        if cat not in faq_categories:
            faq_categories[cat] = []
        faq_categories[cat].append(faq)
    
    return render_template('public/faq.html', faqs=faqs, faq_categories=faq_categories)


@public_bp.route('/terms')
def terms():
    """Terms and conditions page"""
    
    page = Page.query.filter_by(page_type='terms', is_active=True, is_deleted=False).first_or_404()
    return render_template('public/page.html', page=page)


@public_bp.route('/privacy')
def privacy():
    """Privacy policy page"""
    
    page = Page.query.filter_by(page_type='privacy', is_active=True, is_deleted=False).first_or_404()
    return render_template('public/page.html', page=page)


# ==================== SITEMAP & ROBOTS ====================

@public_bp.route('/sitemap.xml')
def sitemap():
    """XML Sitemap"""
    
    from app.services.seo_service import SEOService
    sitemap_xml = SEOService.generate_sitemap()
    
    return sitemap_xml, 200, {'Content-Type': 'application/xml'}


@public_bp.route('/robots.txt')
def robots():
    """Robots.txt file"""
    
    site_url = current_app.config.get('SITE_URL', request.url_root.rstrip('/'))
    
    content = f"""User-agent: *
Allow: /
Disallow: /admin/
Disallow: /user/
Disallow: /api/
Disallow: /cart
Disallow: /checkout
Disallow: /*?*

Sitemap: {site_url}/sitemap.xml"""
    
    return content, 200, {'Content-Type': 'text/plain'}


# ==================== API ENDPOINTS ====================

@public_bp.route('/api/quick-search')
def api_quick_search():
    """Quick search API for autocomplete"""
    
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return jsonify({'results': []})
    
    search_pattern = f'%{query}%'
    
    # Products
    products = Product.query.filter(
        Product.is_active == True,
        Product.is_deleted == False,
        Product.title.ilike(search_pattern)
    ).limit(5).all()
    
    # Categories
    categories = Category.query.filter(
        Category.is_active == True,
        Category.is_deleted == False,
        Category.title.ilike(search_pattern)
    ).limit(3).all()
    
    results = {
        'products': [
            {
                'id': p.id,
                'title': p.title,
                'slug': p.slug,
                'price': p.current_price,
                'image': p.main_image_url,
                'type': 'product'
            } for p in products
        ],
        'categories': [
            {
                'id': c.id,
                'title': c.title,
                'slug': c.slug,
                'type': 'category'
            } for c in categories
        ]
    }
    
    return jsonify(results)


@public_bp.route('/api/price-history/<int:product_id>')
def api_price_history(product_id):
    """Get price history for a product"""
    
    # This would typically come from a price history table
    # For now, return mock data
    return jsonify({'prices': []})


# ==================== PRICE COMPARISON FEEDS ====================

@public_bp.route('/feed/torob.xml')
def feed_torob():
    """Generate Torob-compatible XML feed"""
    
    from app.services.export_service import ExportService
    
    xml = ExportService.generate_torob_feed()
    
    return xml, 200, {'Content-Type': 'application/xml'}


@public_bp.route('/feed/emalls.xml')
def feed_emalls():
    """Generate Emalls-compatible XML feed"""
    
    from app.services.export_service import ExportService
    
    xml = ExportService.generate_emalls_feed()
    
    return xml, 200, {'Content-Type': 'application/xml'}


@public_bp.route('/feed/products.json')
def feed_products():
    """Generate JSON feed for products"""
    
    from app.services.export_service import ExportService
    
    json_data = ExportService.generate_json_feed()
    
    return jsonify(json_data)
