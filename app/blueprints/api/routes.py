"""
API Routes - REST API Endpoints
"""
from flask import request, jsonify, current_app
from flask_login import current_user
from sqlalchemy import or_, func
from app.blueprints.api import api_bp
from app.extensions import db
from app.models import Product, Category, Post, Order, CartItem, Wishlist, Comparison
from app.utils.decorators import rate_limit
import time


# ==================== AUTH MIDDLEWARE ====================

def require_auth(f):
    """Decorator to require authentication"""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated


# ==================== PRODUCTS API ====================

@api_bp.route('/products', methods=['GET'])
def get_products():
    """Get products list"""
    
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    
    # Filters
    category_id = request.args.get('category', type=int)
    brand_id = request.args.get('brand', type=int)
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    in_stock = request.args.get('in_stock', type=bool)
    featured = request.args.get('featured', type=bool)
    search = request.args.get('search', '')
    sort = request.args.get('sort', 'newest')
    
    query = Product.query.filter_by(is_active=True, is_deleted=False)
    
    if category_id:
        query = query.filter(Product.categories.any(id=category_id))
    
    if brand_id:
        query = query.filter_by(brand_id=brand_id)
    
    if min_price:
        query = query.filter(Product.price >= min_price)
    
    if max_price:
        query = query.filter(Product.price <= max_price)
    
    if in_stock:
        query = query.filter(Product.stock_quantity > 0)
    
    if featured:
        query = query.filter_by(is_featured=True)
    
    if search:
        query = query.filter(or_(
            Product.title.ilike(f'%{search}%'),
            Product.short_description.ilike(f'%{search}%')
        ))
    
    # Sorting
    sort_options = {
        'newest': Product.created_at.desc(),
        'oldest': Product.created_at.asc(),
        'price_asc': Product.price.asc(),
        'price_desc': Product.price.desc(),
        'popular': Product.view_count.desc(),
        'rating': Product.rating_avg.desc()
    }
    query = query.order_by(sort_options.get(sort, Product.created_at.desc()))
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'data': [p.to_dict() for p in pagination.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    })


@api_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get single product"""
    
    product = Product.query.get_or_404(product_id)
    
    # Increment views
    product.increment_views()
    
    data = product.to_dict()
    data['specifications'] = product.get_specifications_dict()
    data['images'] = product.all_images
    data['related_products'] = [
        p.to_dict() for p in product.get_related_products(4)
    ]
    
    return jsonify(data)


# ==================== CATEGORIES API ====================

@api_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get categories list"""
    
    parent_only = request.args.get('parent_only', False, type=bool)
    
    if parent_only:
        categories = Category.query.filter_by(
            parent_id=None,
            is_active=True,
            is_deleted=False
        ).all()
    else:
        categories = Category.query.filter_by(
            is_active=True,
            is_deleted=False
        ).all()
    
    return jsonify({
        'data': [
            {
                'id': c.id,
                'title': c.title,
                'slug': c.slug,
                'parent_id': c.parent_id,
                'image': c.image,
                'product_count': c.product_count
            } for c in categories
        ]
    })


@api_bp.route('/categories/<slug>/products', methods=['GET'])
def get_category_products(slug):
    """Get products by category slug"""
    
    category = Category.query.filter_by(slug=slug, is_active=True).first_or_404()
    
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    
    query = category.products.filter(
        Product.is_active == True,
        Product.is_deleted == False
    )
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'category': {
            'id': category.id,
            'title': category.title,
            'slug': category.slug,
            'description': category.description
        },
        'data': [p.to_dict() for p in pagination.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    })


# ==================== POSTS API ====================

@api_bp.route('/posts', methods=['GET'])
def get_posts():
    """Get posts list"""
    
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 50)
    category_id = request.args.get('category', type=int)
    
    query = Post.query.filter_by(
        status='published',
        is_active=True,
        is_deleted=False
    )
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    pagination = query.order_by(Post.published_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'data': [
            {
                'id': p.id,
                'title': p.title,
                'slug': p.slug,
                'excerpt': p.excerpt,
                'featured_image': p.featured_image,
                'published_at': p.published_at.isoformat() if p.published_at else None,
                'author': p.author.full_name if p.author else None,
                'category': p.category.title if p.category else None
            } for p in pagination.items
        ],
        'pagination': {
            'page': page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    })


@api_bp.route('/posts/<slug>', methods=['GET'])
def get_post(slug):
    """Get single post"""
    
    post = Post.query.filter_by(slug=slug, status='published', is_active=True).first_or_404()
    
    post.increment_views()
    
    return jsonify({
        'id': post.id,
        'title': post.title,
        'slug': post.slug,
        'content': post.content,
        'excerpt': post.excerpt,
        'featured_image': post.featured_image,
        'published_at': post.published_at.isoformat() if post.published_at else None,
        'author': {
            'name': post.author.full_name if post.author else 'نویسنده',
            'avatar': post.author.avatar if post.author else None
        },
        'category': {
            'title': post.category.title,
            'slug': post.category.slug
        } if post.category else None,
        'tags': [t.name for t in post.tags],
        'views': post.views,
        'related_posts': [
            {
                'id': p.id,
                'title': p.title,
                'slug': p.slug,
                'featured_image': p.featured_image
            } for p in post.get_related_posts(3)
        ]
    })


# ==================== CART API ====================

@api_bp.route('/cart', methods=['GET'])
@require_auth
def get_cart():
    """Get user cart"""
    
    items = CartItem.query.filter_by(
        user_id=current_user.id,
        is_deleted=False
    ).all()
    
    cart_items = []
    total = 0
    
    for item in items:
        product = item.product
        if product:
            item_total = product.current_price * item.quantity
            total += item_total
            cart_items.append({
                'id': item.id,
                'product_id': product.id,
                'title': product.title,
                'slug': product.slug,
                'image': product.main_image_url,
                'price': product.current_price,
                'quantity': item.quantity,
                'total': item_total,
                'in_stock': product.is_in_stock
            })
    
    return jsonify({
        'items': cart_items,
        'total': total,
        'count': len(cart_items)
    })


@api_bp.route('/cart/add', methods=['POST'])
@require_auth
def add_to_cart():
    """Add item to cart"""
    
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    product = Product.query.get(product_id)
    
    if not product:
        return jsonify({'success': False, 'message': 'محصول یافت نشد'}), 404
    
    if not product.is_in_stock:
        return jsonify({'success': False, 'message': 'محصول موجود نیست'}), 400
    
    # Check existing
    existing = CartItem.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()
    
    if existing:
        existing.quantity += quantity
        existing.save()
    else:
        item = CartItem(
            user_id=current_user.id,
            product_id=product_id,
            quantity=quantity
        )
        db.session.add(item)
        db.session.commit()
    
    count = sum(i.quantity for i in CartItem.query.filter_by(user_id=current_user.id).all())
    
    return jsonify({
        'success': True,
        'message': 'محصول به سبد اضافه شد',
        'cart_count': count
    })


# ==================== WISHLIST API ====================

@api_bp.route('/wishlist', methods=['GET'])
@require_auth
def get_wishlist():
    """Get user wishlist"""
    
    items = Wishlist.query.filter_by(
        user_id=current_user.id
    ).all()
    
    return jsonify({
        'items': [
            {
                'id': item.id,
                'product_id': item.product_id,
                'product': item.product.to_dict() if item.product else None,
                'created_at': item.created_at.isoformat()
            } for item in items
        ],
        'count': len(items)
    })


@api_bp.route('/wishlist/toggle', methods=['POST'])
@require_auth
def toggle_wishlist():
    """Toggle wishlist item"""
    
    data = request.get_json()
    product_id = data.get('product_id')
    
    existing = Wishlist.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()
    
    if existing:
        existing.delete()
        in_wishlist = False
        message = 'از علاقه‌مندی‌ها حذف شد'
    else:
        item = Wishlist(user_id=current_user.id, product_id=product_id)
        db.session.add(item)
        db.session.commit()
        in_wishlist = True
        message = 'به علاقه‌مندی‌ها اضافه شد'
    
    count = Wishlist.query.filter_by(user_id=current_user.id).count()
    
    return jsonify({
        'success': True,
        'message': message,
        'in_wishlist': in_wishlist,
        'count': count
    })


# ==================== SEARCH API ====================

@api_bp.route('/search', methods=['GET'])
def api_search():
    """Search API"""
    
    query = request.args.get('q', '').strip()
    type_filter = request.args.get('type', 'all')  # all, products, posts
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)
    
    if len(query) < 2:
        return jsonify({'error': 'Query too short'}), 400
    
    search_pattern = f'%{query}%'
    results = {'products': [], 'posts': []}
    
    if type_filter in ['all', 'products']:
        products = Product.query.filter(
            Product.is_active == True,
            Product.is_deleted == False,
            Product.title.ilike(search_pattern)
        ).limit(per_page).all()
        
        results['products'] = [p.to_dict() for p in products]
    
    if type_filter in ['all', 'posts']:
        posts = Post.query.filter(
            Post.status == 'published',
            Post.is_active == True,
            Post.is_deleted == False,
            Post.title.ilike(search_pattern)
        ).limit(per_page).all()
        
        results['posts'] = [
            {
                'id': p.id,
                'title': p.title,
                'slug': p.slug,
                'excerpt': p.excerpt,
                'featured_image': p.featured_image
            } for p in posts
        ]
    
    return jsonify({
        'query': query,
        'results': results
    })


# ==================== FEEDS API ====================

@api_bp.route('/feeds/products.json', methods=['GET'])
def products_feed():
    """Products JSON feed"""
    
    products = Product.query.filter_by(
        is_active=True,
        is_deleted=False
    ).limit(1000).all()
    
    return jsonify({
        'generated_at': time.time(),
        'products': [p.to_dict() for p in products]
    })


# ==================== HEALTH CHECK ====================

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time()
    })
