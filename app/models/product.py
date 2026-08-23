"""
Product and Category Models
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Enum, JSON, and_
from sqlalchemy.orm import relationship, Mapped, foreign
import re

from app.extensions import db
from app.models.base import BaseModel, TimestampMixin, SoftDeleteMixin, ActiveMixin, SortOrderMixin, MetaMixin


# Association table for products and categories
class ProductCategory(db.Model):
    """Association table for product-category relationship"""
    __tablename__ = 'product_categories'
    product_id = Column(Integer, ForeignKey('products.id'), primary_key=True)
    category_id = Column(Integer, ForeignKey('categories.id'), primary_key=True)


# Association table for products and tags
class ProductTag(db.Model):
    """Association table for product-tag relationship"""
    __tablename__ = 'product_tags'
    product_id = Column(Integer, ForeignKey('products.id'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('tags.id'), primary_key=True)


class Category(BaseModel, TimestampMixin, SoftDeleteMixin, ActiveMixin, SortOrderMixin, MetaMixin):
    """Category Model"""
    
    __tablename__ = 'categories'
    
    parent_id = db.Column(Integer, ForeignKey('categories.id'), nullable=True, index=True)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    
    # Visual
    icon = db.Column(db.String(255), nullable=True)  # Icon class or SVG
    image = db.Column(db.String(500), nullable=True)
    banner = db.Column(db.String(500), nullable=True)
    color = db.Column(db.String(7), nullable=True)  # Hex color
    
    # Display options
    is_menu = db.Column(db.Boolean, default=False)  # Show in main menu
    is_mega_menu = db.Column(db.Boolean, default=False)  # Show as mega menu
    show_in_home = db.Column(db.Boolean, default=False)  # Show products in home
    show_children = db.Column(db.Boolean, default=True)  # Show child categories
    
    # Counts (cached)
    product_count = db.Column(Integer, default=0)
    
    # Relationships
    parent = relationship('Category', remote_side='Category.id', back_populates='children')
    children = relationship('Category', back_populates='parent', lazy='dynamic',
                           order_by='Category.sort_order')
    products: Mapped[List["Product"]] = db.relationship(
        'Product', secondary='product_categories', back_populates='categories', lazy='select'
    )
    meta_rel = relationship('CategoryMeta', back_populates='category', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def full_path(self) -> str:
        """Get full category path"""
        path = [self.title]
        parent = self.parent
        while parent:
            path.insert(0, parent.title)
            parent = parent.parent
        return ' > '.join(path)
    
    @property
    def breadcrumbs(self) -> List['Category']:
        """Get breadcrumb path"""
        crumbs = []
        parent = self.parent
        while parent:
            crumbs.insert(0, parent)
            parent = parent.parent
        crumbs.append(self)
        return crumbs
    
    def get_ancestors(self) -> List['Category']:
        """Get all ancestor categories"""
        ancestors = []
        parent = self.parent
        while parent:
            ancestors.insert(0, parent)
            parent = parent.parent
        return ancestors
    
    def get_children_tree(self) -> dict:
        """Get nested children tree"""
        return {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'children': [child.get_children_tree() for child in self.children.filter_by(is_deleted=False, is_active=True).all()]
        }
    
    def update_product_count(self) -> None:
        """Update cached product count"""
        self.product_count = self.products.filter_by(is_deleted=False, is_active=True).count()
        db.session.commit()
    
    def __repr__(self):
        return f'<Category {self.title}>'


class CategoryMeta(BaseModel, TimestampMixin):
    """Category Meta Model"""
    
    __tablename__ = 'category_meta'
    
    category_id = db.Column(Integer, ForeignKey('categories.id'), nullable=False, index=True)
    meta_key = db.Column(db.String(255), nullable=False)
    meta_value = db.Column(db.Text, nullable=True)
    
    # Relationships
    category = relationship('Category', back_populates='meta_rel')
    
    __table_args__ = (
        db.UniqueConstraint('category_id', 'meta_key', name='unique_category_meta'),
    )
    
    def __repr__(self):
        return f'<CategoryMeta {self.category_id}:{self.meta_key}>'


class Brand(BaseModel, TimestampMixin, SoftDeleteMixin, ActiveMixin):
    """Brand Model"""
    
    __tablename__ = 'brands'
    
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    
    logo = db.Column(db.String(500), nullable=True)
    banner = db.Column(db.String(500), nullable=True)
    
    # Contact
    website = db.Column(db.String(500), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    
    # Meta
    meta_title = db.Column(db.String(255), nullable=True)
    meta_description = db.Column(db.Text, nullable=True)
    
    # Display
    is_featured = db.Column(db.Boolean, default=False)
    sort_order = db.Column(Integer, default=0)
    
    # Relationships
    products = relationship('Product', back_populates='brand')
    
    def __repr__(self):
        return f'<Brand {self.name}>'


class Product(BaseModel, TimestampMixin, SoftDeleteMixin, ActiveMixin, SortOrderMixin, MetaMixin):
    """Product Model"""
    
    __tablename__ = 'products'
    
    sku = db.Column(db.String(100), unique=True, nullable=True, index=True)
    title = db.Column(db.String(500), nullable=False)
    slug = db.Column(db.String(500), unique=True, nullable=False, index=True)
    
    short_description = db.Column(db.String(1000), nullable=True)
    description = db.Column(db.Text, nullable=True)
    
    # Pricing
    price = db.Column(db.Float, nullable=False, default=0)
    old_price = db.Column(db.Float, nullable=True)
    cost = db.Column(db.Float, nullable=True)  # Cost price for profit calculation
    
    # Discount
    discount_percent = db.Column(db.Float, nullable=True)
    discount_amount = db.Column(db.Float, nullable=True)
    discount_start = db.Column(db.DateTime, nullable=True)
    discount_end = db.Column(db.DateTime, nullable=True)
    
    # Stock
    stock_quantity = db.Column(Integer, default=0)
    stock_status = db.Column(db.String(50), default='in_stock')  # in_stock, out_of_stock, limited, preorder
    low_stock_threshold = db.Column(Integer, default=5)
    
    # Relations
    brand_id = db.Column(Integer, ForeignKey('brands.id'), nullable=True, index=True)
    categories: Mapped[List["Category"]] = db.relationship(
        'Category', secondary='product_categories', back_populates='products', lazy='select'
    )
    tags: Mapped[List["Tag"]] = db.relationship(
        'Tag', secondary='product_tags', back_populates='products', lazy='select'
    )
    
    # Media
    featured_image = db.Column(db.String(500), nullable=True)
    images = relationship('ProductImage', back_populates='product', lazy='dynamic', cascade='all, delete-orphan')
    
    # Attributes (JSON)
    attributes = db.Column(JSON, nullable=True)  # Dynamic attributes
    specifications = db.Column(JSON, nullable=True)  # Technical specs
    variations = db.Column(JSON, nullable=True)  # Product variations
    
    # Display
    is_featured = db.Column(db.Boolean, default=False)
    is_bestseller = db.Column(db.Boolean, default=False)
    is_new = db.Column(db.Boolean, default=False)
    show_in_home = db.Column(db.Boolean, default=False)
    
    # SEO
    schema_data = db.Column(JSON, nullable=True)  # Custom schema.org data
    
    # Stats (cached)
    view_count = db.Column(Integer, default=0)
    sale_count = db.Column(Integer, default=0)
    rating_avg = db.Column(Float, default=0)
    review_count = db.Column(Integer, default=0)
    
    # Relationships
    brand = relationship('Brand', back_populates='products')
    items = relationship('OrderItem', back_populates='product', lazy='dynamic')
    cart_items = relationship('CartItem', back_populates='product', lazy='dynamic')
    wishlisted_by = relationship('Wishlist', back_populates='product', lazy='dynamic')
    compared_by = relationship('Comparison', back_populates='product', lazy='dynamic')
    comments = relationship('Comment', primaryjoin="and_(Comment.commentable_type=='product', foreign(Comment.commentable_id)==Product.id)", back_populates='product', lazy='dynamic', overlaps="comments")
    meta_rel = relationship('ProductMeta', back_populates='product', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def current_price(self) -> float:
        """Get current active price"""
        if self.is_discount_active:
            return self.price - (self.discount_amount or (self.price * self.discount_percent / 100))
        return self.price
    
    @property
    def is_discount_active(self) -> bool:
        """Check if discount is currently active"""
        if not self.discount_percent and not self.discount_amount:
            return False
        now = datetime.utcnow()
        if self.discount_start and self.discount_start > now:
            return False
        if self.discount_end and self.discount_end < now:
            return False
        return True
    
    @property
    def discount_price(self) -> Optional[float]:
        """Get discounted price if active"""
        if self.is_discount_active:
            return self.current_price
        return None
    
    @property
    def is_in_stock(self) -> bool:
        """Check if product is in stock"""
        return self.stock_status != 'out_of_stock' and self.stock_quantity > 0
    
    @property
    def is_low_stock(self) -> bool:
        """Check if product is low on stock"""
        return 0 < self.stock_quantity <= self.low_stock_threshold
    
    @property
    def main_image_url(self) -> str:
        """Get main product image URL"""
        if self.featured_image:
            return self.featured_image
        first_image = self.images.filter_by(is_deleted=False).first()
        return first_image.url if first_image else '/static/images/no-image.png'
    
    @property
    def all_images(self) -> List[str]:
        """Get all product images"""
        images = []
        if self.featured_image:
            images.append(self.featured_image)
        images.extend([img.url for img in self.images.filter_by(is_deleted=False).all()])
        return images
    
    @property
    def category_names(self) -> List[str]:
        """Get category names"""
        return [cat.title for cat in self.categories]
    
    def increment_views(self) -> None:
        """Increment view count"""
        self.view_count += 1
        db.session.commit()

    def get_related_products(self, limit: int = 4) -> List['Product']:
        """Get related products in the same category"""
        if not self.categories:
            return Product.query.filter(Product.id != self.id, Product.is_active == True, Product.is_deleted == False).limit(limit).all()
        cat_id = self.categories[0].id
        return Product.query.filter(
            Product.id != self.id,
            Product.categories.any(id=cat_id),
            Product.is_active == True,
            Product.is_deleted == False
        ).limit(limit).all()
    
    def get_specifications_dict(self) -> dict:
        """Get specifications as dictionary"""
        if not self.specifications:
            return {}
        return self.specifications
    
    def get_price_range(self) -> Optional[tuple]:
        """Get price range for variations"""
        if not self.variations:
            return None
        prices = [v.get('price', self.price) for v in self.variations]
        return (min(prices), max(prices))
    
    def get_schema_data(self) -> dict:
        """Generate Schema.org data"""
        if self.schema_data:
            return self.schema_data
        
        schema = {
            '@context': 'https://schema.org',
            '@type': 'Product',
            'name': self.title,
            'description': self.short_description or self.description[:200] if self.description else '',
            'sku': self.sku,
            'url': f'/products/{self.slug}',
            'image': self.main_image_url,
        }
        
        if self.brand:
            schema['brand'] = {
                '@type': 'Brand',
                'name': self.brand.name
            }
        
        if self.is_in_stock:
            schema['offers'] = {
                '@type': 'Offer',
                'price': self.current_price,
                'priceCurrency': 'IRR',
                'availability': 'https://schema.org/InStock',
                'seller': {'@type': 'Organization', 'name': 'فروشگاه'}
            }
        else:
            schema['offers'] = {
                '@type': 'Offer',
                'price': self.current_price,
                'priceCurrency': 'IRR',
                'availability': 'https://schema.org/OutOfStock',
            }
        
        if self.rating_avg > 0:
            schema['aggregateRating'] = {
                '@type': 'AggregateRating',
                'ratingValue': self.rating_avg,
                'reviewCount': self.review_count
            }
        
        return schema
    
    def __repr__(self):
        return f'<Product {self.title}>'


class ProductImage(BaseModel, TimestampMixin):
    """Product Image Model"""
    
    __tablename__ = 'product_images'
    
    product_id = db.Column(Integer, ForeignKey('products.id'), nullable=False, index=True)
    url = db.Column(db.String(500), nullable=False)
    
    title = db.Column(db.String(255), nullable=True)
    alt = db.Column(db.String(255), nullable=True)
    sort_order = db.Column(Integer, default=0)
    
    # Processed versions
    thumbnail_url = db.Column(db.String(500), nullable=True)
    medium_url = db.Column(db.String(500), nullable=True)
    
    # Metadata
    width = db.Column(Integer, nullable=True)
    height = db.Column(Integer, nullable=True)
    file_size = db.Column(Integer, nullable=True)  # bytes
    
    # Relationships
    product = relationship('Product', back_populates='images')
    
    def __repr__(self):
        return f'<ProductImage {self.id}>'


class ProductMeta(BaseModel, TimestampMixin):
    """Product Meta Model"""
    
    __tablename__ = 'product_meta'
    
    product_id = db.Column(Integer, ForeignKey('products.id'), nullable=False, index=True)
    meta_key = db.Column(db.String(255), nullable=False)
    meta_value = db.Column(db.Text, nullable=True)
    
    # Relationships
    product = relationship('Product', back_populates='meta_rel')
    
    __table_args__ = (
        db.UniqueConstraint('product_id', 'meta_key', name='unique_product_meta'),
    )
    
    def __repr__(self):
        return f'<ProductMeta {self.product_id}:{self.meta_key}>'


class Tag(BaseModel, TimestampMixin, SoftDeleteMixin):
    """Tag Model for products and posts"""
    
    __tablename__ = 'tags'
    
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    
    # Relationships
    products: Mapped[List["Product"]] = db.relationship(
        'Product', secondary='product_tags', back_populates='tags', lazy='select'
    )
    posts: Mapped[List["Post"]] = db.relationship(
        'Post', secondary='post_tags', back_populates='tags', lazy='select'
    )
    
    def __repr__(self):
        return f'<Tag {self.name}>'


# Forward reference for Post
from app.models.content import Post
