"""
Feature Models — قابلیت‌های الهام‌گرفته از تحلیل بازار قالب‌های شرکتی راست‌چین
(app/data/theme_research.md)
  - TeamMember  : تیم ما + نوار مهارت (الگوی آرنیکا/ستیا)
  - PricingPlan : جداول قیمت و تعرفه (الگوی آرنیکا)
  - Story       : استوری‌ساز اینستاگرامی (الگوی نادر)
  - Subscriber  : خبرنامه (الگوی کرافتو/MailChimp)
  - Ticket/TicketMessage : سیستم تیکت پشتیبانی (الگوی نادر)
  - OtpCode     : ورود/عضویت پیامکی OTP (الگوی نادر — ۷ اپراتور)
  - ProductVideo: گالری ویدئو محصول + آپارات (الگوی نادر)
Variation Swatches از ستون JSON موجود «Product.variations» استفاده می‌کند.
"""
from datetime import datetime, timedelta

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum, JSON, BigInteger

from app.extensions import db
from app.models.base import (
    BaseModel, TimestampMixin, SoftDeleteMixin, ActiveMixin, SortOrderMixin
)


class TeamMember(BaseModel, TimestampMixin, SoftDeleteMixin, ActiveMixin, SortOrderMixin):
    """عضو تیم با نوار مهارت خطی/دایره‌ای"""

    __tablename__ = 'team_members'

    full_name = db.Column(db.String(255), nullable=False)
    role_title = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    avatar = db.Column(db.String(500), nullable=True)

    # [{name: 'Python', level: 92}, ...] — level: 0..100
    skills = db.Column(JSON, nullable=True)
    # {instagram: '...', linkedin: '...', telegram: '...', email: '...'}
    socials = db.Column(JSON, nullable=True)

    def skill_list(self):
        return self.skills or []

    def __repr__(self):
        return f'<TeamMember {self.full_name}>'


class PricingPlan(BaseModel, TimestampMixin, SoftDeleteMixin, ActiveMixin, SortOrderMixin):
    """جدول قیمت/تعرفهٔ خدمات"""

    __tablename__ = 'pricing_plans'

    title = db.Column(db.String(255), nullable=False)
    subtitle = db.Column(db.String(500), nullable=True)
    price_toman = db.Column(BigInteger, nullable=True)          # None → «استعلام قیمت»
    old_price_toman = db.Column(BigInteger, nullable=True)
    period = db.Column(db.String(100), default='پروژه')          # پروژه / ماهانه / سالانه

    # ['ویژگی ۱', 'ویژگی ۲', ...]
    features = db.Column(JSON, nullable=True)
    # ['ویژگی غیرفعال', ...] — با ✕ نمایش داده می‌شود
    features_off = db.Column(JSON, nullable=True)

    badge_text = db.Column(db.String(100), nullable=True)        # «محبوب‌ترین»
    is_featured = db.Column(db.Boolean, default=False)           # هایلایت ویژه
    button_text = db.Column(db.String(100), default='سفارش')
    button_url = db.Column(db.String(500), nullable=True)

    def feature_list(self):
        return self.features or []

    def feature_off_list(self):
        return self.features_off or []

    def __repr__(self):
        return f'<PricingPlan {self.title}>'


class Story(BaseModel, TimestampMixin, SoftDeleteMixin, ActiveMixin, SortOrderMixin):
    """استوری اینستاگرامی — گروه‌بندی‌شده با نوار نمایش در بالای صفحهٔ اصلی"""

    __tablename__ = 'stories'

    title = db.Column(db.String(255), nullable=False)
    group_name = db.Column(db.String(100), default='عمومی', index=True)

    media_type = db.Column(Enum('image', 'video', name='story_media_type'), default='image')
    image = db.Column(db.String(500), nullable=True)             # کاور/تصویر استوری
    video_url = db.Column(db.String(500), nullable=True)         # mp4 یا embed

    link = db.Column(db.String(500), nullable=True)              # لینک CTA
    link_text = db.Column(db.String(100), default='مشاهده')

    duration = db.Column(Integer, default=5)                     # ثانیه نمایش خودکار
    views = db.Column(Integer, default=0)

    start_at = db.Column(DateTime, nullable=True)                # زمان‌بندی نمایش
    expires_at = db.Column(DateTime, nullable=True)

    @property
    def is_live(self) -> bool:
        now = datetime.utcnow()
        if self.start_at and self.start_at > now:
            return False
        if self.expires_at and self.expires_at < now:
            return False
        return True

    def __repr__(self):
        return f'<Story {self.title}>'


class Subscriber(BaseModel, TimestampMixin):
    """مشترک خبرنامه"""

    __tablename__ = 'subscribers'

    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    source = db.Column(db.String(100), default='footer')         # footer / popup / ...
    ip_address = db.Column(db.String(45), nullable=True)
    unsubscribed_at = db.Column(DateTime, nullable=True)

    @property
    def is_active_subscriber(self) -> bool:
        return self.unsubscribed_at is None

    def unsubscribe(self):
        self.unsubscribed_at = datetime.utcnow()
        db.session.commit()

    def __repr__(self):
        return f'<Subscriber {self.email}>'


class Ticket(BaseModel, TimestampMixin, SoftDeleteMixin):
    """تیکت پشتیبانی (ردوبدل پیام با پیوست)"""

    __tablename__ = 'tickets'

    user_id = db.Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    ticket_number = db.Column(db.String(20), unique=True, nullable=False, index=True)

    subject = db.Column(db.String(500), nullable=False)
    department = db.Column(
        Enum('general', 'order', 'technical', 'billing', 'feedback', name='ticket_department'),
        default='general'
    )
    priority = db.Column(
        Enum('low', 'medium', 'high', name='ticket_priority'),
        default='medium'
    )
    status = db.Column(
        Enum('open', 'answered', 'user_reply', 'closed', name='ticket_status'),
        default='open', index=True
    )

    last_reply_at = db.Column(DateTime, default=datetime.utcnow)
    closed_at = db.Column(DateTime, nullable=True)
    closed_by = db.Column(Integer, ForeignKey('users.id'), nullable=True)

    messages = db.relationship(
        'TicketMessage', back_populates='ticket', lazy='dynamic',
        cascade='all, delete-orphan', order_by='TicketMessage.created_at'
    )
    user = db.relationship('User', foreign_keys=[user_id])

    DEPARTMENT_LABELS = {
        'general': 'عمومی',
        'order': 'سفارش',
        'technical': 'فنی',
        'billing': 'مالی',
        'feedback': 'انتقاد/پیشنهاد',
    }
    PRIORITY_LABELS = {'low': 'کم', 'medium': 'متوسط', 'high': 'فوری'}
    STATUS_LABELS = {
        'open': 'باز', 'answered': 'پاسخ داده‌شده',
        'user_reply': 'پاسخ کاربر', 'closed': 'بسته',
    }

    @property
    def status_label(self):
        return self.STATUS_LABELS.get(self.status, self.status)

    @property
    def priority_label(self):
        return self.PRIORITY_LABELS.get(self.priority, self.priority)

    @property
    def department_label(self):
        return self.DEPARTMENT_LABELS.get(self.department, self.department)

    @property
    def last_message(self):
        return self.messages.order_by(TicketMessage.created_at.desc()).first()

    @classmethod
    def generate_number(cls) -> str:
        """شمارهٔ یکتا مثل TK-14050602-4821"""
        now = datetime.utcnow()
        seq = db.session.query(cls.id).count() + 1
        return f"TK-{now.strftime('%y%m%d')}-{(now.microsecond // 100):04d}{seq % 10}"

    def add_message(self, message: str, user_id: int = None, is_admin: bool = False,
                    attachment: str = None) -> 'TicketMessage':
        msg = TicketMessage(
            ticket_id=self.id,
            user_id=user_id,
            message=message,
            is_admin_reply=is_admin,
            attachment=attachment,
        )
        db.session.add(msg)
        self.last_reply_at = datetime.utcnow()
        if is_admin:
            self.status = 'answered'
        else:
            self.status = 'user_reply'
        db.session.commit()
        return msg

    def close(self, by_user_id: int = None):
        self.status = 'closed'
        self.closed_at = datetime.utcnow()
        self.closed_by = by_user_id
        db.session.commit()

    def reopen(self):
        self.status = 'open'
        self.closed_at = None
        db.session.commit()

    def __repr__(self):
        return f'<Ticket {self.ticket_number}>'


class TicketMessage(BaseModel, TimestampMixin):
    """پیام داخل تیکت"""

    __tablename__ = 'ticket_messages'

    ticket_id = db.Column(Integer, ForeignKey('tickets.id'), nullable=False, index=True)
    user_id = db.Column(Integer, ForeignKey('users.id'), nullable=True)
    message = db.Column(Text, nullable=False)
    attachment = db.Column(db.String(500), nullable=True)
    is_admin_reply = db.Column(Boolean, default=False)

    ticket = db.relationship('Ticket', back_populates='messages')
    author = db.relationship('User')

    def __repr__(self):
        return f'<TicketMessage {self.id}>'


class OtpCode(BaseModel, TimestampMixin):
    """کد یک‌بارمصرف پیامکی — ورود/عضویت با موبایل"""

    __tablename__ = 'otp_codes'

    phone = db.Column(db.String(20), nullable=False, index=True)
    code_hash = db.Column(db.String(255), nullable=False)
    purpose = db.Column(Enum('login', 'register', name='otp_purpose'), default='login')

    expires_at = db.Column(DateTime, nullable=False)
    attempts = db.Column(Integer, default=0)
    used_at = db.Column(DateTime, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)

    TTL_MINUTES = 3
    MAX_ATTEMPTS = 5

    @classmethod
    def normalize_phone(cls, phone: str) -> str:
        phone = ''.join(c for c in (phone or '') if c.isdigit())
        if phone.startswith('0098'):
            phone = '0' + phone[4:]
        elif phone.startswith('98') and len(phone) == 12:
            phone = '0' + phone[2:]
        elif phone.startswith('9') and len(phone) == 10:
            phone = '0' + phone
        return phone

    @classmethod
    def is_valid_phone(cls, phone: str) -> bool:
        return len(phone) == 11 and phone.startswith('09')

    @classmethod
    def issue(cls, phone: str, purpose: str = 'login', ip: str = None) -> 'OtpCode':
        import secrets
        import hashlib

        # حداکثر ۳ کد در ۱۵ دقیقه برای هر شماره (ضد بمباران پیامکی)
        window = datetime.utcnow() - timedelta(minutes=15)
        recent = cls.query.filter(
            cls.phone == phone, cls.created_at >= window
        ).count()
        if recent >= 3:
            raise ValueError('تعداد درخواست کد زیاد است؛ کمی بعد دوباره تلاش کنید.')

        code = f'{secrets.randbelow(1000000):06d}'
        otp = cls(
            phone=phone,
            code_hash=hashlib.sha256(code.encode()).hexdigest(),
            purpose=purpose,
            expires_at=datetime.utcnow() + timedelta(minutes=cls.TTL_MINUTES),
            ip_address=ip,
        )
        db.session.add(otp)
        db.session.commit()
        otp._plain_code = code
        return otp

    def verify(self, code: str) -> bool:
        import hashlib

        if self.used_at or self.expires_at < datetime.utcnow():
            return False
        self.attempts += 1
        db.session.commit()
        if self.attempts > self.MAX_ATTEMPTS:
            return False
        ok = hashlib.sha256((code or '').strip().encode()).hexdigest() == self.code_hash
        if ok:
            self.used_at = datetime.utcnow()
            db.session.commit()
        return ok

    @classmethod
    def latest_for(cls, phone: str, purpose: str = 'login'):
        return cls.query.filter(
            cls.phone == phone,
            cls.purpose == purpose,
            cls.used_at.is_(None),
        ).order_by(cls.created_at.desc()).first()

    def __repr__(self):
        return f'<OtpCode {self.phone}>'


class ProductVideo(BaseModel, TimestampMixin, SoftDeleteMixin, ActiveMixin, SortOrderMixin):
    """گالری ویدئو محصول — آپارات/یوتیوب/فایل"""

    __tablename__ = 'product_videos'

    product_id = db.Column(Integer, ForeignKey('products.id'), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=True)
    provider = db.Column(
        Enum('aparat', 'youtube', 'file', name='video_provider'),
        default='aparat'
    )
    url = db.Column(db.String(500), nullable=False)
    thumbnail = db.Column(db.String(500), nullable=True)

    product = db.relationship('Product', backref='videos')

    def embed_url(self) -> str:
        """تبدیل صفحهٔ ویدئو به embed قابل پخش"""
        url = self.url or ''
        if self.provider == 'file':
            return url
        if self.provider == 'youtube':
            for token in ('watch?v=', 'youtu.be/', 'embed/'):
                if token in url:
                    vid = url.split(token)[-1].split('&')[0].split('?')[0]
                    return f'https://www.youtube.com/embed/{vid}'
            return url
        # aparat
        if '/v/' in url:
            return url
        for token in ('/w/', '/f/'):
            if token in url:
                return url.replace(token, '/v/')
        return url

    def __repr__(self):
        return f'<ProductVideo {self.product_id}:{self.provider}>'
