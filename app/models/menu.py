"""
Menu, Slider, Banner, Media, Settings, and Notification Models
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum, JSON, Float
from sqlalchemy.orm import relationship

from app.extensions import db
from app.models.base import BaseModel, TimestampMixin, SoftDeleteMixin, ActiveMixin, SortOrderMixin


class Menu(BaseModel, TimestampMixin, SoftDeleteMixin, ActiveMixin, SortOrderMixin):
    """Navigation Menu Model"""
    
    __tablename__ = 'menus'
    
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)
    url = db.Column(db.String(500), nullable=True)
    
    # Icon
    icon = db.Column(db.String(255), nullable=True)  # FontAwesome or custom
    icon_type = db.Column(String(50), default='fa')  # 'fa', 'custom', 'image'
    icon_image = db.Column(String(500), nullable=True)
    
    # Hierarchy
    parent_id = db.Column(Integer, ForeignKey('menus.id'), nullable=True, index=True)
    
    # Display
    position = db.Column(
        Enum('header', 'footer', 'sidebar', 'mobile', 'topbar', name='menu_position'),
        default='header',
        nullable=False,
        index=True
    )
    
    # Mega menu
    is_mega_menu = db.Column(Boolean, default=False)
    mega_menu_config = db.Column(JSON, nullable=True)
    
    # Link behavior
    target = db.Column(
        Enum('_self', '_blank', '_parent', '_top', name='link_target'),
        default='_self',
        nullable=False
    )
    no_follow = db.Column(Boolean, default=False)
    
    # Badge
    badge_text = db.Column(String(100), nullable=True)
    badge_color = db.Column(String(7), nullable=True)  # Hex color
    
    # Visibility
    show_logged_in = db.Column(Boolean, default=True)  # Show for logged in users
    show_guest = db.Column(Boolean, default=True)  # Show for guests
    
    # Relationships
    parent = relationship('Menu', remote_side='Menu.id', back_populates='children')
    children = relationship('Menu', back_populates='parent', lazy='dynamic',
                           order_by='Menu.sort_order')
    
    @property
    def full_url(self) -> str:
        """Get full URL with site URL prefix"""
        if self.url and not self.url.startswith(('http://', 'https://', '/')):
            return f'/{self.url}'
        return self.url or '#'
    
    @property
    def has_children(self) -> bool:
        """Check if menu has children"""
        return self.children.filter_by(is_deleted=False, is_active=True).count() > 0
    
    def get_children_ordered(self) -> List['Menu']:
        """Get ordered children (فعال و حذف‌نشده، به ترتیب sort_order)"""
        return self.children.filter_by(is_deleted=False, is_active=True).order_by(Menu.sort_order).all()
    
    @classmethod
    def get_menu_by_position(cls, position: str) -> List['Menu']:
        """Get top-level menu items by position"""
        return cls.query.filter_by(
            position=position,
            parent_id=None,
            is_deleted=False,
            is_active=True
        ).order_by(cls.sort_order).all()
    
    def __repr__(self):
        return f'<Menu {self.title}>'


class Slider(BaseModel, TimestampMixin, SoftDeleteMixin, ActiveMixin, SortOrderMixin):
    """Slider Model"""
    
    __tablename__ = 'sliders'
    
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)
    
    # Display
    position = db.Column(String(100), default='home')  # home, category, product, etc.
    
    # Settings
    autoplay = db.Column(Boolean, default=True)
    autoplay_interval = db.Column(Integer, default=5000)  # milliseconds
    arrows = db.Column(Boolean, default=True)
    dots = db.Column(Boolean, default=True)
    loop = db.Column(Boolean, default=True)
    height = db.Column(Integer, default=500)  # pixels
    
    # Items
    items = relationship('SliderItem', back_populates='slider', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Slider {self.title}>'


class SliderItem(BaseModel, TimestampMixin, SoftDeleteMixin, ActiveMixin, SortOrderMixin):
    """Slider Item Model"""
    
    __tablename__ = 'slider_items'
    
    slider_id = db.Column(Integer, ForeignKey('sliders.id'), nullable=False, index=True)
    
    # Content
    title = db.Column(db.String(500), nullable=True)
    subtitle = db.Column(db.String(1000), nullable=True)
    description = db.Column(Text, nullable=True)
    
    # Media
    image = db.Column(db.String(500), nullable=False)
    mobile_image = db.Column(db.String(500), nullable=True)
    video_url = db.Column(String(500), nullable=True)
    
    # Link
    url = db.Column(String(500), nullable=True)
    link_text = db.Column(String(100), nullable=True)
    target = db.Column(String(20), default='_self')
    
    # Styling
    text_alignment = db.Column(
        Enum('left', 'center', 'right', name='text_alignment'),
        default='right'
    )
    text_color = db.Column(String(7), nullable=True)
    overlay_color = db.Column(String(7), nullable=True)
    overlay_opacity = db.Column(Float, default=0.3)
    
    # Animation
    animation_in = db.Column(String(50), default='fadeIn')
    animation_delay = db.Column(Integer, default=0)
    
    # Scheduling
    start_date = db.Column(DateTime, nullable=True)
    end_date = db.Column(DateTime, nullable=True)
    
    # Relationships
    slider = relationship('Slider', back_populates='items')
    
    @property
    def is_active_now(self) -> bool:
        """Check if item is currently active based on dates"""
        now = datetime.utcnow()
        if self.start_date and self.start_date > now:
            return False
        if self.end_date and self.end_date < now:
            return False
        return True
    
    def __repr__(self):
        return f'<SliderItem {self.title or self.id}>'


class Banner(BaseModel, TimestampMixin, SoftDeleteMixin, ActiveMixin, SortOrderMixin):
    """Banner Model"""
    
    __tablename__ = 'banners'
    
    title = db.Column(db.String(255), nullable=False)
    
    # Media
    image = db.Column(db.String(500), nullable=False)
    mobile_image = db.Column(String(500), nullable=True)
    
    # Link
    url = db.Column(String(500), nullable=True)
    target = db.Column(String(20), default='_self')
    no_follow = db.Column(Boolean, default=False)
    
    # Display
    position = db.Column(String(100), nullable=False, index=True)  # sidebar, between_products, etc.
    size = db.Column(
        Enum('small', 'medium', 'large', 'wide', 'tall', name='banner_size'),
        default='medium'
    )
    
    # Background
    background_color = db.Column(String(7), nullable=True)
    text_color = db.Column(String(7), nullable=True)
    
    # Text overlay
    overlay_text = db.Column(Text, nullable=True)
    overlay_title = db.Column(String(255), nullable=True)
    overlay_subtitle = db.Column(String(255), nullable=True)
    overlay_position = db.Column(String(20), default='right')
    
    # Scheduling
    start_date = db.Column(DateTime, nullable=True)
    end_date = db.Column(DateTime, nullable=True)
    
    # Click tracking
    click_count = db.Column(Integer, default=0)
    impression_count = db.Column(Integer, default=0)
    
    def record_click(self) -> None:
        """Record banner click"""
        self.click_count += 1
        db.session.commit()
    
    def record_impression(self) -> None:
        """Record banner impression"""
        self.impression_count += 1
        db.session.commit()
    
    @property
    def is_active_now(self) -> bool:
        """Check if banner is currently active"""
        if not self.is_active:
            return False
        now = datetime.utcnow()
        if self.start_date and self.start_date > now:
            return False
        if self.end_date and self.end_date < now:
            return False
        return True
    
    def __repr__(self):
        return f'<Banner {self.title}>'


class Media(BaseModel, TimestampMixin):
    """Media Library Model"""
    
    __tablename__ = 'media'
    
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=True)
    
    # Path
    path = db.Column(db.String(1000), nullable=False)
    url = db.Column(db.String(1000), nullable=False)
    
    # Type
    mime_type = db.Column(db.String(100), nullable=False)
    file_type = db.Column(
        Enum('image', 'video', 'audio', 'document', 'archive', 'other', name='file_type'),
        default='other'
    )
    
    # Dimensions
    width = db.Column(Integer, nullable=True)
    height = db.Column(Integer, nullable=True)
    
    # Size
    file_size = db.Column(Integer, nullable=False)  # bytes
    
    # Processed versions
    thumbnail_url = db.Column(String(1000), nullable=True)
    medium_url = db.Column(String(1000), nullable=True)
    large_url = db.Column(String(1000), nullable=True)
    
    # Metadata
    alt = db.Column(String(255), nullable=True)
    title = db.Column(String(255), nullable=True)
    caption = db.Column(Text, nullable=True)
    description = db.Column(Text, nullable=True)
    
    # SEO
    alt_text = db.Column(String(255), nullable=True)
    
    # Organization
    folder = db.Column(String(255), nullable=True, index=True)
    tags = db.Column(String(500), nullable=True)  # Comma-separated tags
    
    # User
    uploaded_by = db.Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Usage tracking
    usage_count = db.Column(Integer, default=0)
    
    @property
    def size_formatted(self) -> str:
        """Get human-readable file size"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f'{size:.1f} {unit}'
            size /= 1024
        return f'{size:.1f} TB'
    
    @property
    def is_image(self) -> bool:
        """Check if file is an image"""
        return self.file_type == 'image'
    
    def __repr__(self):
        return f'<Media {self.filename}>'


class Setting(BaseModel, TimestampMixin):
    """Site Settings Model"""
    
    __tablename__ = 'settings'
    
    group = db.Column(db.String(100), nullable=False, index=True)
    key = db.Column(db.String(255), nullable=False, index=True)
    value = db.Column(Text, nullable=True)
    
    # Type for formatting
    type = db.Column(
        Enum('string', 'text', 'boolean', 'integer', 'float', 'json', 'select', 'color', 'image', name='setting_type'),
        default='string'
    )
    
    # Options for select type
    options = db.Column(JSON, nullable=True)
    
    # Display
    label = db.Column(db.String(255), nullable=True)
    description = db.Column(Text, nullable=True)
    
    # Access
    is_public = db.Column(Boolean, default=False)  # Visible in public API
    is_system = db.Column(Boolean, default=False)  # Cannot be deleted
    
    # Validation
    validation_rules = db.Column(JSON, nullable=True)
    
    # Order
    sort_order = db.Column(Integer, default=0)
    
    __table_args__ = (
        db.UniqueConstraint('group', 'key', name='unique_setting'),
    )
    
    @classmethod
    def get_value(cls, group: str, key: str, default=None):
        """Get setting value"""
        setting = cls.query.filter_by(group=group, key=key).first()
        if setting:
            if setting.type == 'boolean':
                return setting.value in ('true', '1', 'yes', 'on')
            if setting.type == 'json':
                import json
                try:
                    return json.loads(setting.value) if setting.value else None
                except:
                    return None
            return setting.value
        return default
    
    @classmethod
    def set_value(cls, group: str, key: str, value, type: str = 'string') -> 'Setting':
        """Set setting value"""
        setting = cls.query.filter_by(group=group, key=key).first()
        if not setting:
            setting = cls(group=group, key=key)
            db.session.add(setting)
        
        if isinstance(value, (dict, list)):
            import json
            value = json.dumps(value)
            type = 'json'
        
        setting.value = str(value) if value is not None else None
        setting.type = type
        db.session.commit()
        return setting
    
    @classmethod
    def get_group(cls, group: str) -> dict:
        """Get all settings in a group"""
        settings = cls.query.filter_by(group=group).order_by(cls.sort_order).all()
        return {s.key: s.value for s in settings}
    
    def __repr__(self):
        return f'<Setting {self.group}.{self.key}>'


class Notification(BaseModel, TimestampMixin):
    """Notification Model"""
    
    __tablename__ = 'notifications'
    
    user_id = db.Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    
    # Type
    type = db.Column(
        Enum('info', 'success', 'warning', 'error', 'order', 'message', 'system', name='notification_type'),
        default='info'
    )
    
    # Content
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(Text, nullable=True)
    
    # Action
    action_url = db.Column(String(500), nullable=True)
    action_text = db.Column(String(100), nullable=True)
    
    # Data
    data = db.Column(JSON, nullable=True)
    
    # Status
    is_read = db.Column(Boolean, default=False, nullable=False, index=True)
    read_at = db.Column(DateTime, nullable=True)
    
    # Delivery
    delivered = db.Column(Boolean, default=False)
    delivered_at = db.Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship('User', back_populates='notifications')
    
    def mark_read(self) -> None:
        """Mark notification as read"""
        self.is_read = True
        self.read_at = datetime.utcnow()
        db.session.commit()
    
    @classmethod
    def send_to_user(cls, user_id: int, title: str, message: str, type: str = 'info', data: dict = None) -> 'Notification':
        """Create and send notification to user"""
        notification = cls(
            user_id=user_id,
            title=title,
            message=message,
            type=type,
            data=data
        )
        notification.save()
        return notification
    
    @classmethod
    def send_bulk(cls, user_ids: List[int], title: str, message: str, type: str = 'info') -> List['Notification']:
        """Send notification to multiple users"""
        notifications = []
        for user_id in user_ids:
            notification = cls(
                user_id=user_id,
                title=title,
                message=message,
                type=type
            )
            notifications.append(notification)
        db.session.bulk_save_objects(notifications)
        db.session.commit()
        return notifications
    
    def __repr__(self):
        return f'<Notification {self.title}>'


class Resume(BaseModel, TimestampMixin, SoftDeleteMixin):
    """Job Resume Model"""
    
    __tablename__ = 'resumes'
    
    user_id = db.Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    
    # Personal info
    full_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    
    # Job
    job_position = db.Column(String(255), nullable=True)
    job_category = db.Column(String(255), nullable=True)
    
    # Files
    file_path = db.Column(db.String(500), nullable=True)
    cover_letter = db.Column(Text, nullable=True)
    
    # Portfolio
    portfolio_url = db.Column(String(500), nullable=True)
    linkedin_url = db.Column(String(500), nullable=True)
    github_url = db.Column(String(500), nullable=True)
    
    # Status
    status = db.Column(
        Enum('new', 'reviewed', 'interview', 'rejected', 'accepted', name='resume_status'),
        default='new',
        nullable=False,
        index=True
    )
    
    # Admin review
    reviewed_by = db.Column(Integer, ForeignKey('users.id'), nullable=True)
    reviewed_at = db.Column(DateTime, nullable=True)
    review_notes = db.Column(Text, nullable=True)
    
    # Info
    ip_address = db.Column(String(45), nullable=True)
    
    # Relationships
    user = relationship('User', foreign_keys=[user_id], back_populates='resumes')
    
    def update_status(self, status: str, reviewed_by: int = None, notes: str = None) -> None:
        """Update resume status"""
        self.status = status
        if reviewed_by:
            self.reviewed_by = reviewed_by
            self.reviewed_at = datetime.utcnow()
        if notes:
            self.review_notes = notes
        db.session.commit()
    
    def __repr__(self):
        return f'<Resume {self.full_name}>'


class Contact(BaseModel, TimestampMixin, SoftDeleteMixin):
    """Contact Form Submission Model"""
    
    __tablename__ = 'contacts'
    
    user_id = db.Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    
    # Contact info
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    
    # Subject
    subject = db.Column(db.String(500), nullable=True)
    
    # Content
    message = db.Column(Text, nullable=False)
    
    # Response
    is_read = db.Column(Boolean, default=False, index=True)
    read_by = db.Column(Integer, ForeignKey('users.id'), nullable=True)
    read_at = db.Column(DateTime, nullable=True)
    
    # Reply
    replied = db.Column(Boolean, default=False)
    reply_content = db.Column(Text, nullable=True)
    replied_by = db.Column(Integer, ForeignKey('users.id'), nullable=True)
    replied_at = db.Column(DateTime, nullable=True)
    
    # Tracking
    ip_address = db.Column(String(45), nullable=True)
    user_agent = db.Column(String(500), nullable=True)
    
    # Relationships
    user = relationship('User', foreign_keys=[user_id], back_populates='contacts')
    
    def mark_read(self, read_by_user_id: int = None) -> None:
        """Mark contact as read"""
        self.is_read = True
        self.read_by = read_by_user_id
        self.read_at = datetime.utcnow()
        db.session.commit()
    
    def reply(self, content: str, replied_by_user_id: int) -> None:
        """Reply to contact"""
        self.reply_content = content
        self.replied = True
        self.replied_by = replied_by_user_id
        self.replied_at = datetime.utcnow()
        db.session.commit()
    
    def __repr__(self):
        return f'<Contact {self.name}: {self.subject}>'


class FAQ(BaseModel, TimestampMixin, SoftDeleteMixin, ActiveMixin, SortOrderMixin):
    """FAQ Model"""
    
    __tablename__ = 'faqs'
    
    question = db.Column(db.String(1000), nullable=False)
    answer = db.Column(Text, nullable=False)
    
    # Category
    category = db.Column(db.String(255), nullable=True)
    
    # SEO
    meta_title = db.Column(db.String(255), nullable=True)
    meta_description = db.Column(db.Text, nullable=True)
    
    # Display
    is_featured = db.Column(Boolean, default=False)
    
    # Schema (for FAQPage)
    schema_data = db.Column(JSON, nullable=True)
    
    @property
    def get_schema_data(self) -> dict:
        """Get FAQPage schema data"""
        return {
            '@context': 'https://schema.org',
            '@type': 'FAQPage',
            'mainEntity': [{
                '@type': 'Question',
                'name': self.question,
                'acceptedAnswer': {
                    '@type': 'Answer',
                    'text': self.answer
                }
            }]
        }
    
    def __repr__(self):
        return f'<FAQ {self.question[:50]}>'


class Log(BaseModel, TimestampMixin):
    """Audit Log Model"""
    
    __tablename__ = 'logs'
    
    # Action
    action = db.Column(String(100), nullable=False, index=True)
    
    # Who
    user_id = db.Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    user_ip = db.Column(String(45), nullable=True)
    user_agent = db.Column(String(500), nullable=True)
    
    # What
    entity_type = db.Column(String(100), nullable=True)
    entity_id = db.Column(Integer, nullable=True)
    
    # Details
    old_values = db.Column(JSON, nullable=True)
    new_values = db.Column(JSON, nullable=True)
    description = db.Column(Text, nullable=True)
    
    # Relationships
    user = relationship('User')
    
    @classmethod
    def log_action(cls, action: str, user_id: int = None, entity_type: str = None, 
                  entity_id: int = None, old_values: dict = None, new_values: dict = None,
                  description: str = None, request=None) -> 'Log':
        """Create audit log entry"""
        log = cls(
            action=action,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values,
            description=description
        )
        
        if request:
            log.user_ip = request.remote_addr
            log.user_agent = request.user_agent.string[:500] if request.user_agent else None
        
        db.session.add(log)
        db.session.commit()
        return log
    
    def __repr__(self):
        return f'<Log {self.action}:{self.entity_type}:{self.entity_id}>'
