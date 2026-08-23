"""
Application Constants
Centralized constants to avoid magic strings throughout the codebase.
"""
from enum import Enum


# ==================== Order Status ====================
class OrderStatus(str, Enum):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    PROCESSING = 'processing'
    SHIPPED = 'shipped'
    DELIVERED = 'delivered'
    CANCELLED = 'cancelled'
    REFUNDED = 'refunded'

    @property
    def label_fa(self) -> str:
        return {
            'pending': 'در انتظار پرداخت',
            'confirmed': 'تأیید شده',
            'processing': 'در حال آماده‌سازی',
            'shipped': 'ارسال شده',
            'delivered': 'تحویل داده شده',
            'cancelled': 'لغو شده',
            'refunded': 'بازگردانده شده',
        }.get(self.value, self.value)


# ==================== Payment Status ====================
class PaymentStatus(str, Enum):
    UNPAID = 'unpaid'
    PAID = 'paid'
    FAILED = 'failed'
    REFUNDED = 'refunded'

    @property
    def label_fa(self) -> str:
        return {
            'unpaid': 'پرداخت نشده',
            'paid': 'پرداخت شده',
            'failed': 'ناموفق',
            'refunded': 'بازگردانده شده',
        }.get(self.value, self.value)


# ==================== Payment Methods ====================
class PaymentMethod(str, Enum):
    CASH = 'cash'             # پرداخت در محل
    CARD = 'card'             # کارت به کارت
    ONLINE = 'online'         # درگاه آنلاین
    WALLET = 'wallet'         # کیف پول


# ==================== Payment Gateways ====================
class PaymentGateway(str, Enum):
    ZARINPAL = 'zarinpal'
    IDPAY = 'idpay'
    NEXTPAY = 'nextpay'
    MANUAL = 'manual'         # پرداخت دستی/کارت به کارت


# ==================== Transaction Status ====================
class TransactionStatus(str, Enum):
    PENDING = 'pending'
    SUCCESS = 'success'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    REFUNDED = 'refunded'


# ==================== Lead Status (B2B) ====================
class LeadStatus(str, Enum):
    NEW = 'new'
    CONTACTED = 'contacted'
    PROPOSAL_SENT = 'proposal_sent'
    CLOSED_WON = 'closed_won'
    CLOSED_LOST = 'closed_lost'


# ==================== Resume Status ====================
class ResumeStatus(str, Enum):
    NEW = 'new'
    REVIEWING = 'reviewing'
    SHORTLISTED = 'shortlisted'
    REJECTED = 'rejected'
    HIRED = 'hired'


# ==================== Notification Types ====================
class NotificationType(str, Enum):
    INFO = 'info'
    SUCCESS = 'success'
    WARNING = 'warning'
    DANGER = 'danger'
    ORDER = 'order'
    MESSAGE = 'message'
    SYSTEM = 'system'


# ==================== User Roles ====================
class RoleSlug(str, Enum):
    ADMIN = 'admin'
    USER = 'user'
    EDITOR = 'editor'
    SUPPORT = 'support'


# ==================== Slider Positions ====================
class SliderPosition(str, Enum):
    HOME = 'home'
    PRODUCT = 'product'
    CATEGORY = 'category'
    SIDEBAR = 'sidebar'


# ==================== Banner Positions ====================
class BannerPosition(str, Enum):
    HOME_TOP = 'home_top'
    HOME_MIDDLE = 'home_middle'
    HOME_BOTTOM = 'home_bottom'
    SIDEBAR = 'sidebar'
    BETWEEN_PRODUCTS = 'between_products'
    CATEGORY_TOP = 'category_top'


# ==================== Menu Positions ====================
class MenuPosition(str, Enum):
    HEADER = 'header'
    FOOTER = 'footer'
    MOBILE = 'mobile'
    SIDEBAR = 'sidebar'


# ==================== Page Types ====================
class PageType(str, Enum):
    HOME = 'home'
    ABOUT = 'about'
    CONTACT = 'contact'
    TERMS = 'terms'
    PRIVACY = 'privacy'
    FAQ = 'faq'
    DEFAULT = 'default'


# ==================== Post Status ====================
class PostStatus(str, Enum):
    DRAFT = 'draft'
    PUBLISHED = 'published'
    ARCHIVED = 'archived'


# ==================== Cache Keys ====================
class CacheKey(str, Enum):
    SITE_SETTINGS = 'site_settings'
    MENU_HEADER = 'menu_header'
    MENU_FOOTER = 'menu_footer'
    PRODUCT_DETAIL = 'product_detail'
    CATEGORY_TREE = 'category_tree'
    POPULAR_PRODUCTS = 'popular_products'
    HOME_PAGE = 'home_page'


# ==================== Cache Timeouts (seconds) ====================
class CacheTimeout:
    SHORT = 60           # 1 min - dynamic data
    MEDIUM = 300         # 5 min - product list, blog list
    LONG = 3600          # 1 hour - settings, menus
    VERY_LONG = 86400    # 1 day - static pages


# ==================== Pagination ====================
class Pagination:
    DEFAULT_PER_PAGE = 20
    ADMIN_PER_PAGE = 50
    API_PER_PAGE = 50
    MAX_PER_PAGE = 100


# ==================== Validation Limits ====================
class Limits:
    NAME_MIN = 2
    NAME_MAX = 100
    EMAIL_MAX = 255
    PASSWORD_MIN = 8
    PASSWORD_MAX = 128
    PHONE_LENGTH = 11        # Iranian mobile: 09xxxxxxxxx
    NATIONAL_CODE_LENGTH = 10
    POSTAL_CODE_LENGTH = 10
    TITLE_MAX = 255
    DESCRIPTION_MAX = 2000
    SEARCH_MIN_LENGTH = 2
    SEARCH_MAX_LENGTH = 100
    COMMENT_MAX = 1000
    REVIEW_MAX = 2000


# ==================== Iranian Phone Patterns ====================
PHONE_PATTERN_IR = r'^09[0-9]{9}$'
PHONE_LANDLINE_IR = r'^0[0-9]{10}$'  # like 021xxxxxxxx
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
NATIONAL_CODE_PATTERN = r'^[0-9]{10}$'
POSTAL_CODE_PATTERN = r'^[0-9]{10}$'


# ==================== File Upload ====================
class FileUpload:
    MAX_IMAGE_SIZE = 5 * 1024 * 1024       # 5 MB
    MAX_DOCUMENT_SIZE = 20 * 1024 * 1024   # 20 MB
    ALLOWED_IMAGE_EXTS = {'jpg', 'jpeg', 'png', 'webp', 'gif'}
    ALLOWED_DOCUMENT_EXTS = {'pdf', 'doc', 'docx', 'txt'}

    ALLOWED_IMAGE_MIMES = {
        'image/jpeg', 'image/jpg', 'image/png',
        'image/webp', 'image/gif'
    }
    ALLOWED_DOCUMENT_MIMES = {
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain'
    }


# ==================== Rate Limiting ====================
class RateLimits:
    CONTACT_FORM = '5 per hour'
    LOGIN = '10 per 15 minutes'
    REGISTER = '3 per hour'
    PASSWORD_RESET = '3 per hour'
    SEARCH = '60 per minute'
    API_DEFAULT = '100 per hour'
    API_HEAVY = '20 per minute'
