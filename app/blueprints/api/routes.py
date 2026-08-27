"""
API Routes - Production-grade REST API Endpoints
Adheres strictly to SQLAlchemy 2.0 select() constructs and layered service calls.
"""
from __future__ import annotations

import logging
import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

from flask import Response, current_app, jsonify, request
from flask_login import current_user
from sqlalchemy import func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from app.blueprints.api import api_bp
from app.extensions import db
from app.models.content import Post
from app.models.order import CartItem, Comparison, Order, Wishlist
from app.models.product import Brand, Category, Product, Tag
from app.services.cart_service import CartService
from app.services.product_service import ProductService
from app.services.user_service import UserService

logger = logging.getLogger(__name__)


# ==================== AUTH MIDDLEWARE ====================

def require_auth(f: Callable) -> Callable:
    """Decorator to require user authentication on protected API routes."""
    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Response:
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated


# ==================== PRODUCTS API ====================

@api_bp.route('/products/filter', methods=['GET'])
def filter_products() -> Response:
    """
    AJAX filtered product listing with sorting and pagination.
    """
    per_page = min(request.args.get('per_page', 12, type=int), 48)
    page = max(request.args.get('page', 1, type=int), 1)

    stmt = select(Product).where(Product.is_active.is_(True), Product.is_deleted.is_(False))

    category_slug = (request.args.get('category') or '').strip()
    if category_slug:
        cat_stmt = select(Category).where(Category.slug == category_slug, Category.is_deleted.is_(False))
        cat = db.session.execute(cat_stmt).scalars().first()
        if not cat:
            return jsonify({'success': True, 'items': [], 'total': 0, 'pages': 0, 'page': page})
        stmt = stmt.where(Product.categories.any(Category.id == cat.id))

    brands = request.args.getlist('brand', type=int)
    if brands:
        stmt = stmt.where(Product.brand_id.in_(brands))

    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    if min_price is not None and min_price >= 0:
        stmt = stmt.where(Product.price >= min_price)
    if max_price is not None and max_price > 0:
        stmt = stmt.where(Product.price <= max_price)

    in_stock = request.args.get('in_stock', type=int)
    if in_stock:
        stmt = stmt.where(Product.stock_quantity > 0)

    on_sale = request.args.get('on_sale', type=int)
    if on_sale:
        stmt = stmt.where(Product.old_price.isnot(None), Product.old_price > Product.price)

    q = (request.args.get('q') or '').strip()
    if q:
        term = f'%{q}%'
        stmt = stmt.where(
            or_(
                Product.title.ilike(term),
                Product.short_description.ilike(term),
                Product.sku.ilike(term),
            )
        )

    # Sorting
    sort = request.args.get('sort', 'newest')
    if sort == 'cheapest':
        stmt = stmt.order_by(Product.price.asc())
    elif sort == 'expensive':
        stmt = stmt.order_by(Product.price.desc())
    elif sort == 'popular':
        stmt = stmt.order_by(Product.view_count.desc())
    elif sort == 'discount':
        stmt = stmt.order_by((Product.old_price - Product.price).desc().nullslast())
    else:
        stmt = stmt.order_by(Product.created_at.desc())

    pagination = db.paginate(stmt, page=page, per_page=per_page, error_out=False)

    items = []
    for p in pagination.items:
        items.append({
            'id': p.id,
            'title': p.title,
            'slug': p.slug,
            'price': p.price,
            'current_price': p.current_price,
            'old_price': p.old_price,
            'is_in_stock': p.is_in_stock,
            'main_image_url': p.main_image_url,
            'short_description': p.short_description,
            'url': f'/product/{p.slug}',
        })

    return jsonify({
        'success': True,
        'items': items,
        'total': pagination.total,
        'pages': pagination.pages,
        'page': pagination.page,
    })


@api_bp.route('/products', methods=['GET'])
def get_products() -> Response:
    """Get paginated products list with filters."""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)

    stmt = select(Product).where(Product.is_active.is_(True), Product.is_deleted.is_(False))

    category_id = request.args.get('category', type=int)
    if category_id:
        stmt = stmt.where(Product.categories.any(Category.id == category_id))

    brand_id = request.args.get('brand', type=int)
    if brand_id:
        stmt = stmt.where(Product.brand_id == brand_id)

    min_price = request.args.get('min_price', type=float)
    if min_price is not None:
        stmt = stmt.where(Product.price >= min_price)

    max_price = request.args.get('max_price', type=float)
    if max_price is not None:
        stmt = stmt.where(Product.price <= max_price)

    in_stock = request.args.get('in_stock', type=bool)
    if in_stock:
        stmt = stmt.where(Product.stock_quantity > 0)

    featured = request.args.get('featured', type=bool)
    if featured:
        stmt = stmt.where(Product.is_featured.is_(True))

    search = (request.args.get('search') or '').strip()
    if search:
        stmt = stmt.where(or_(
            Product.title.ilike(f'%{search}%'),
            Product.short_description.ilike(f'%{search}%')
        ))

    sort = request.args.get('sort', 'newest')
    sort_options = {
        'newest': Product.created_at.desc(),
        'oldest': Product.created_at.asc(),
        'price_asc': Product.price.asc(),
        'price_desc': Product.price.desc(),
        'popular': Product.view_count.desc(),
    }
    stmt = stmt.order_by(sort_options.get(sort, Product.created_at.desc()))

    pagination = db.paginate(stmt, page=page, per_page=per_page, error_out=False)

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
def get_product(product_id: int) -> Response:
    """Retrieve full details for a single product."""
    product = ProductService.get_by_id(product_id)
    if not product or product.is_deleted:
        return jsonify({'error': 'Product not found'}), 404

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
def get_categories() -> Response:
    """Get category list."""
    parent_only = request.args.get('parent_only', False, type=bool)

    stmt = select(Category).where(Category.is_active.is_(True), Category.is_deleted.is_(False))
    if parent_only:
        stmt = stmt.where(Category.parent_id.is_(None))

    stmt = stmt.order_by(Category.sort_order.asc())
    categories = list(db.session.execute(stmt).scalars().all())

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
def get_category_products(slug: str) -> Response:
    """Get products by category slug."""
    cat_stmt = select(Category).where(Category.slug == slug, Category.is_active.is_(True), Category.is_deleted.is_(False))
    category = db.session.execute(cat_stmt).scalars().first()
    if not category:
        return jsonify({'error': 'Category not found'}), 404

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)

    stmt = select(Product).where(
        Product.categories.any(Category.id == category.id),
        Product.is_active.is_(True),
        Product.is_deleted.is_(False)
    ).order_by(Product.created_at.desc())

    pagination = db.paginate(stmt, page=page, per_page=per_page, error_out=False)

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
def get_posts() -> Response:
    """Get published blog posts list."""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 50)
    category_id = request.args.get('category', type=int)

    stmt = select(Post).where(
        Post.status == 'published',
        Post.is_active.is_(True),
        Post.is_deleted.is_(False)
    )

    if category_id:
        stmt = stmt.where(Post.category_id == category_id)

    stmt = stmt.order_by(Post.published_at.desc())
    pagination = db.paginate(stmt, page=page, per_page=per_page, error_out=False)

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
def get_post(slug: str) -> Response:
    """Get single post details."""
    stmt = select(Post).where(Post.slug == slug, Post.status == 'published', Post.is_active.is_(True), Post.is_deleted.is_(False))
    post = db.session.execute(stmt).scalars().first()
    if not post:
        return jsonify({'error': 'Post not found'}), 404

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
def get_cart() -> Response:
    """Get current user's shopping cart."""
    items = CartService.get_user_cart(current_user.id)
    cart_items = []
    total: float = 0.0

    for item in items:
        product = item.product
        if product and not product.is_deleted and product.is_active:
            item_total = float(product.current_price) * item.quantity
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
def add_to_cart() -> Response:
    """Add item to authenticated user's cart."""
    data = request.get_json() or {}
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1))

    if not product_id:
        return jsonify({'success': False, 'message': 'شناسه کالا نامعتبر است'}), 400

    product = ProductService.get_by_id(int(product_id))
    if not product or product.is_deleted:
        return jsonify({'success': False, 'message': 'محصول یافت نشد'}), 404

    if not product.is_in_stock:
        return jsonify({'success': False, 'message': 'محصول موجود نیست'}), 400

    success = CartService.add_to_user_cart(current_user.id, product.id, quantity)
    count = CartService.get_user_cart_count(current_user.id)

    return jsonify({
        'success': success,
        'message': 'محصول به سبد اضافه شد' if success else 'خطا در افزودن به سبد',
        'cart_count': count
    })


# ==================== WISHLIST API ====================

@api_bp.route('/wishlist', methods=['GET'])
@require_auth
def get_wishlist() -> Response:
    """Get authenticated user's wishlist."""
    stmt = (
        select(Wishlist)
        .where(Wishlist.user_id == current_user.id)
        .options(selectinload(Wishlist.product))
    )
    items = list(db.session.execute(stmt).scalars().all())

    return jsonify({
        'items': [
            {
                'id': item.id,
                'product_id': item.product_id,
                'product': item.product.to_dict() if item.product else None,
                'created_at': item.created_at.isoformat()
            } for item in items if item.product and not item.product.is_deleted
        ],
        'count': len(items)
    })


@api_bp.route('/wishlist/toggle', methods=['POST'])
@require_auth
def toggle_wishlist() -> Response:
    """Toggle wishlist item."""
    data = request.get_json() or {}
    product_id = data.get('product_id')
    if not product_id:
        return jsonify({'success': False, 'message': 'شناسه کالا الزامی است'}), 400

    success, message, in_wishlist = UserService.toggle_wishlist(current_user.id, int(product_id))

    count_stmt = select(func.count(Wishlist.id)).where(Wishlist.user_id == current_user.id)
    count = db.session.execute(count_stmt).scalar() or 0

    return jsonify({
        'success': success,
        'message': message,
        'in_wishlist': in_wishlist,
        'count': count
    })


# ==================== SEARCH API ====================

@api_bp.route('/search', methods=['GET'])
def api_search() -> Response:
    """Multi-entity search endpoint."""
    query = (request.args.get('q') or '').strip()
    type_filter = request.args.get('type', 'all')
    per_page = min(request.args.get('per_page', 20, type=int), 50)

    if len(query) < 2:
        return jsonify({'error': 'Query too short'}), 400

    search_pattern = f'%{query}%'
    results: Dict[str, List[Any]] = {'products': [], 'posts': []}

    if type_filter in ['all', 'products']:
        prod_stmt = select(Product).where(
            Product.is_active.is_(True),
            Product.is_deleted.is_(False),
            or_(
                Product.title.ilike(search_pattern),
                Product.short_description.ilike(search_pattern),
                Product.sku.ilike(search_pattern),
            )
        ).limit(per_page)
        products = list(db.session.execute(prod_stmt).scalars().all())
        results['products'] = [p.to_dict() for p in products]

    if type_filter in ['all', 'posts']:
        post_stmt = select(Post).where(
            Post.status == 'published',
            Post.is_active.is_(True),
            Post.is_deleted.is_(False),
            or_(
                Post.title.ilike(search_pattern),
                Post.excerpt.ilike(search_pattern),
            )
        ).limit(per_page)
        posts = list(db.session.execute(post_stmt).scalars().all())
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
def products_feed() -> Response:
    """Products JSON feed."""
    stmt = select(Product).where(
        Product.is_active.is_(True),
        Product.is_deleted.is_(False)
    ).limit(1000)
    products = list(db.session.execute(stmt).scalars().all())

    return jsonify({
        'generated_at': time.time(),
        'products': [p.to_dict() for p in products]
    })


# ==================== HEALTH CHECK ====================

@api_bp.route('/health', methods=['GET'])
def health_check() -> Response:
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time()
    })
