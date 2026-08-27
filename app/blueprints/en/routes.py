"""
مسیرهای نسخهٔ انگلیسی سایت (/en/...)

صفحات: خانه، درباره، تماس (با فرم)، محصولات، وبلاگ، مقاله، سوالات متداول
"""
from flask import (
    render_template, request, redirect, url_for, flash, current_app,
)
from sqlalchemy import or_

from app.blueprints.en import en_bp
from app.extensions import db
from app.models import (
    Product, Post, Category, FAQ, Page, Contact,
)


def _ctx(mirror):
    """زمینهٔ مشترک: مسیر معادل فارسی برای دکمهٔ تغییر زبان."""
    return {'fa_url': mirror}


@en_bp.route('/')
def home():
    featured = Product.query.filter_by(
        is_active=True, is_deleted=False, is_featured=True,
    ).order_by(Product.sort_order).limit(6).all()
    if not featured:
        featured = Product.query.filter_by(
            is_active=True, is_deleted=False,
        ).order_by(Product.id).limit(6).all()

    posts = Post.query.filter_by(
        status='published', is_active=True, is_deleted=False,
    ).order_by(Post.published_at.desc()).limit(3).all()

    return render_template('en/home.html',
                           featured_products=featured, latest_posts=posts,
                           **_ctx('/'))


@en_bp.route('/about')
def about():
    return render_template('en/about.html', **_ctx('/about'))


@en_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page with working form (stored like the Persian one)."""
    success = False
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        email = (request.form.get('email') or '').strip()
        subject = (request.form.get('subject') or 'Contact (EN)').strip()
        message = (request.form.get('message') or '').strip()

        if len(name) < 2 or '@' not in email or len(message) < 10:
            flash('Please fill in your name, a valid email, and a message of at least 10 characters.', 'error')
        else:
            try:
                Contact(
                    name=name, email=email, subject=subject, message=message,
                    ip_address=request.remote_addr,
                ).save()
                from app.services.notification_service import NotificationService
                NotificationService.notify_admins(
                    title='پیام جدید (EN)', message=f'{name} - {subject}',
                    type='message')
                success = True
            except Exception as exc:
                current_app.logger.error(f'EN contact save error: {exc}')
                flash('Something went wrong. Please try again.', 'error')

    return render_template('en/contact.html', success=success, **_ctx('/contact'))


@en_bp.route('/products')
@en_bp.route('/products/<int:page>')
def products(page=1):
    cats = Category.query.filter_by(
        is_active=True, is_deleted=False).order_by(Category.sort_order).all()

    cat_slug = (request.args.get('category') or '').strip()
    query = Product.query.filter_by(is_active=True, is_deleted=False)
    if cat_slug:
        cat = Category.query.filter_by(slug=cat_slug, is_deleted=False).first()
        if cat:
            query = query.filter(Product.categories.contains(cat))

    pagination = query.order_by(Product.sort_order, Product.id.desc()).paginate(
        page=page, per_page=12, error_out=False)

    return render_template('en/products.html',
                           products=pagination, categories=cats,
                           active_cat=cat_slug, **_ctx('/categories/'))


@en_bp.route('/blog')
@en_bp.route('/blog/<int:page>')
def blog(page=1):
    pagination = Post.query.filter_by(
        status='published', is_active=True, is_deleted=False,
    ).order_by(Post.published_at.desc()).paginate(
        page=page, per_page=10, error_out=False)

    return render_template('en/blog.html', posts=pagination, **_ctx('/blog/'))


@en_bp.route('/blog/<slug>')
def post(slug):
    post_obj = Post.query.filter_by(
        slug=slug, status='published', is_active=True, is_deleted=False,
    ).first_or_404()

    post_obj.increment_views()
    related = post_obj.get_related_posts(limit=3)

    has_en = bool(post_obj.title_en and post_obj.content_en)

    return render_template('en/post.html',
                           post=post_obj, related_posts=related,
                           has_english=has_en, **_ctx(f'/blog/{slug}'))


@en_bp.route('/faq')
def faq():
    faqs = FAQ.query.filter_by(
        is_active=True, is_deleted=False,
    ).order_by(FAQ.sort_order).limit(20).all()
    return render_template('en/faq.html', faqs=faqs, **_ctx('/faq'))
