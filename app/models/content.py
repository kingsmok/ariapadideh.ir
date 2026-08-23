"""
Content Management Models (Pages, Posts, Comments)
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship, Mapped

from app.extensions import db
from app.models.base import BaseModel, TimestampMixin, SoftDeleteMixin, ActiveMixin, SortOrderMixin, MetaMixin


# Association table for posts and tags
class PostTag(db.Model):
    """Association table for post-tag relationship"""
    __tablename__ = 'post_tags'
    post_id = Column(Integer, ForeignKey('posts.id'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('tags.id'), primary_key=True)


class Page(BaseModel, TimestampMixin, SoftDeleteMixin, ActiveMixin, SortOrderMixin, MetaMixin):
    """CMS Page Model"""
    
    __tablename__ = 'pages'
    
    title = db.Column(db.String(500), nullable=False)
    slug = db.Column(db.String(500), unique=True, nullable=False, index=True)
    content = db.Column(db.Text, nullable=True)
    
    # Page type for custom rendering
    page_type = db.Column(
        Enum('default', 'home', 'about', 'contact', 'faq', 'terms', 'privacy', 'landing', name='page_type'),
        default='default',
        nullable=False
    )
    
    # Template
    template = db.Column(db.String(100), nullable=True)
    
    # Display
    show_in_menu = db.Column(db.Boolean, default=False)
    show_in_footer = db.Column(db.Boolean, default=False)
    show_breadcrumb = db.Column(db.Boolean, default=True)
    show_sidebar = db.Column(db.Boolean, default=False)
    
    # Components (dynamic sections)
    components = relationship('PageComponent', back_populates='page', lazy='dynamic', cascade='all, delete-orphan')
    
    # Parent page for nesting
    parent_id = db.Column(Integer, ForeignKey('pages.id'), nullable=True, index=True)
    parent = relationship('Page', remote_side='Page.id', back_populates='children')
    children = relationship('Page', back_populates='parent', lazy='dynamic')
    
    def __repr__(self):
        return f'<Page {self.title}>'


class PageComponent(BaseModel, TimestampMixin, SoftDeleteMixin, ActiveMixin, SortOrderMixin):
    """Dynamic Page Component Model"""
    
    __tablename__ = 'page_components'
    
    page_id = db.Column(Integer, ForeignKey('pages.id'), nullable=False, index=True)
    
    # Component type
    component_type = db.Column(
        Enum(
            'hero', 'slider', 'banner', 'banners_grid', 'products_grid', 'products_carousel',
            'categories_grid', 'features', 'faq', 'testimonials', 'team', 'gallery',
            'cta', 'newsletter', 'brands', 'posts_grid', 'html', 'spacer', 'divider',
            name='component_type'
        ),
        nullable=False
    )
    
    # Content
    title = db.Column(db.String(500), nullable=True)
    subtitle = db.Column(db.String(1000), nullable=True)
    content = db.Column(Text, nullable=True)
    
    # Configuration (JSON for flexible settings)
    config = db.Column(JSON, nullable=True)
    
    # Image/media
    image = db.Column(db.String(500), nullable=True)
    images = db.Column(JSON, nullable=True)  # Array of image URLs
    
    # Link
    link = db.Column(db.String(500), nullable=True)
    link_text = db.Column(db.String(255), nullable=True)
    
    # Display
    position = db.Column(String(50), nullable=True)  # 'main', 'sidebar', 'footer', 'header'
    cols_count = db.Column(Integer, default=3)  # Bootstrap grid cols
    full_width = db.Column(Boolean, default=False)
    background_color = db.Column(String(7), nullable=True)  # Hex color
    background_image = db.Column(String(500), nullable=True)
    
    # Relationships
    page = relationship('Page', back_populates='components')
    
    def get_config(self, key, default=None):
        """Get config value"""
        if not self.config:
            return default
        return self.config.get(key, default)
    
    def __repr__(self):
        return f'<PageComponent {self.component_type}:{self.id}>'


class Post(BaseModel, TimestampMixin, SoftDeleteMixin, ActiveMixin, SortOrderMixin, MetaMixin):
    """Blog Post Model"""
    
    __tablename__ = 'posts'
    
    title = db.Column(db.String(500), nullable=False)
    slug = db.Column(db.String(500), unique=True, nullable=False, index=True)
    excerpt = db.Column(db.String(1000), nullable=True)
    content = db.Column(Text, nullable=True)
    
    # Featured image
    featured_image = db.Column(db.String(500), nullable=True)
    featured_video = db.Column(db.String(500), nullable=True)
    
    # Author
    author_id = db.Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    
    # Category
    category_id = db.Column(Integer, ForeignKey('categories.id'), nullable=True, index=True)
    
    # Relations
    tags: Mapped[List["Tag"]] = db.relationship(
        'Tag', secondary='post_tags', back_populates='posts', lazy='select'
    )
    
    # Publishing
    status = db.Column(
        Enum('draft', 'published', 'scheduled', 'archived', name='post_status'),
        default='draft',
        nullable=False,
        index=True
    )
    published_at = db.Column(DateTime, nullable=True)
    scheduled_at = db.Column(DateTime, nullable=True)
    
    # Stats
    views = db.Column(Integer, default=0, nullable=False)
    likes = db.Column(Integer, default=0, nullable=False)
    shares = db.Column(Integer, default=0, nullable=False)
    
    # Display
    is_featured = db.Column(Boolean, default=False)
    show_in_home = db.Column(Boolean, default=False)
    allow_comments = db.Column(Boolean, default=True)
    
    # Schema
    schema_type = db.Column(String(50), default='Article')
    
    # Relationships
    author = relationship('User', foreign_keys=[author_id])
    category = relationship('Category', foreign_keys=[category_id])
    comments = relationship('Comment', back_populates='post', lazy='dynamic', cascade='all, delete-orphan')
    
    def publish(self) -> None:
        """Publish the post"""
        self.status = 'published'
        self.published_at = datetime.utcnow()
        db.session.commit()
    
    def archive(self) -> None:
        """Archive the post"""
        self.status = 'archived'
        db.session.commit()
    
    def increment_views(self) -> None:
        """Increment view count"""
        self.views += 1
        db.session.commit()
    
    def get_related_posts(self, limit: int = 5) -> List['Post']:
        """Get related posts by tags and category"""
        from app.models.content import Post
        
        tag_ids = [tag.id for tag in self.tags]
        related = Post.query.filter(
            Post.id != self.id,
            Post.status == 'published',
            Post.is_deleted == False
        )
        
        if tag_ids:
            related = related.join(post_tags).filter(post_tags.c.tag_id.in_(tag_ids))
        elif self.category_id:
            related = related.filter(Post.category_id == self.category_id)
        
        return related.distinct().limit(limit).all()
    
    def get_schema_data(self) -> dict:
        """Generate Schema.org data"""
        schema = {
            '@context': 'https://schema.org',
            '@type': self.schema_type,
            'headline': self.title,
            'description': self.excerpt or (self.content[:200] if self.content else ''),
            'image': self.featured_image,
            'datePublished': self.published_at.isoformat() if self.published_at else None,
            'dateModified': self.updated_at.isoformat(),
            'author': {
                '@type': 'Person',
                'name': self.author.full_name if self.author else 'نویسنده'
            },
        }
        
        if self.category:
            schema['articleSection'] = self.category.title
        
        return schema
    
    def __repr__(self):
        return f'<Post {self.title}>'


class Comment(BaseModel, TimestampMixin, SoftDeleteMixin, ActiveMixin):
    """Comment Model"""
    
    __tablename__ = 'comments'
    
    # Polymorphic relations
    user_id = db.Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    
    # Commentable types
    commentable_type = db.Column(
        Enum('product', 'post', name='commentable_type'),
        nullable=False,
        index=True
    )
    commentable_id = db.Column(Integer, nullable=False, index=True)
    
    # Content
    content = db.Column(Text, nullable=False)
    
    # Status
    is_approved = db.Column(Boolean, default=False, nullable=False, index=True)
    is_spam = db.Column(Boolean, default=False)
    
    # Parent for nested comments
    parent_id = db.Column(Integer, ForeignKey('comments.id'), nullable=True, index=True)
    
    # Info (for guest comments)
    guest_name = db.Column(String(255), nullable=True)
    guest_email = db.Column(String(255), nullable=True)
    
    # Moderation
    approved_by = db.Column(Integer, ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(DateTime, nullable=True)
    
    # IP for spam prevention
    ip_address = db.Column(String(45), nullable=True)
    user_agent = db.Column(String(500), nullable=True)
    
    # Relationships
    user = relationship('User', foreign_keys=[user_id], back_populates='comments')
    parent = relationship('Comment', remote_side='Comment.id', back_populates='replies')
    replies = relationship('Comment', back_populates='parent', lazy='dynamic')
    product = relationship('Product', back_populates='comments')
    post = relationship('Post', back_populates='comments')
    
    @property
    def display_name(self) -> str:
        """Get display name"""
        if self.user:
            return self.user.full_name
        return self.guest_name or 'مهمان'
    
    @property
    def is_reply(self) -> bool:
        """Check if comment is a reply"""
        return self.parent_id is not None
    
    def approve(self, approved_by_user_id: int = None) -> None:
        """Approve comment"""
        self.is_approved = True
        self.approved_by = approved_by_user_id
        self.approved_at = datetime.utcnow()
        db.session.commit()
    
    def mark_spam(self) -> None:
        """Mark as spam"""
        self.is_spam = True
        self.is_approved = False
        db.session.commit()
    
    def __repr__(self):
        return f'<Comment {self.id}>'
