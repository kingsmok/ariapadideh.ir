"""
Utility Helpers
"""
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import re
import json
from typing import List


def format_price(price: float, currency: str = 'IRR') -> str:
    """Format price with Persian numerals and currency"""
    if currency == 'IRR':
        # Convert to Toman (assuming prices are in Rial)
        price = price / 10
    
    formatted = f"{int(price):,}"
    return f"{formatted} تومان"


def format_price_en(price: float, currency: str = 'IRR') -> str:
    """Format price in English numerals"""
    if currency == 'IRR':
        price = price / 10
    
    formatted = f"{int(price):,}"
    return f"{formatted} Toman"


def time_ago(dt: datetime) -> str:
    """Convert datetime to Persian relative time"""
    if not dt:
        return ''
    
    now = datetime.utcnow()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return 'لحظاتی پیش'
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f'{minutes} دقیقه پیش'
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f'{hours} ساعت پیش'
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f'{days} روز پیش'
    elif seconds < 2592000:
        weeks = int(seconds / 604800)
        return f'{weeks} هفته پیش'
    elif seconds < 31536000:
        months = int(seconds / 2592000)
        return f'{months} ماه پیش'
    else:
        years = int(seconds / 31536000)
        return f'{years} سال پیش'


def time_ago_short(dt: datetime) -> str:
    """Short relative time"""
    if not dt:
        return ''
    
    now = datetime.utcnow()
    diff = now - dt
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return 'الان'
    elif seconds < 3600:
        return f'{int(seconds / 60)} دقیقه'
    elif seconds < 86400:
        return f'{int(seconds / 3600)} ساعت'
    elif seconds < 604800:
        return f'{int(seconds / 86400)} روز'
    elif seconds < 2592000:
        return f'{int(seconds / 604800)} هفته'
    else:
        return dt.strftime('%Y/%m/%d')


def truncate_text(text: str, length: int = 100, suffix: str = '...') -> str:
    """Truncate text to specified length"""
    if not text or len(text) <= length:
        return text
    
    return text[:length].rsplit(' ', 1)[0] + suffix


def slugify(text: str, max_length: int = 255) -> str:
    """Convert text to URL-friendly slug"""
    if not text:
        return ''
    
    # Persian to Latin number mapping
    persian_numbers = '۰۱۲۳۴۵۶۷۸۹'
    latin_numbers = '0123456789'
    
    # Replace Persian numbers with Latin
    for i in range(10):
        text = text.replace(persian_numbers[i], latin_numbers[i])
    
    # Convert to lowercase
    text = text.lower()
    
    # Replace spaces with hyphens
    text = re.sub(r'\s+', '-', text)
    
    # Remove non-alphanumeric characters except hyphens
    text = re.sub(r'[^\w\-]', '', text)
    
    # Remove duplicate hyphens
    text = re.sub(r'-+', '-', text)
    
    # Remove leading/trailing hyphens
    text = text.strip('-')
    
    return text[:max_length]


def get_pagination_params(per_page: int = 20, max_per_page: int = 100):
    """Get pagination parameters from request"""
    from flask import request
    
    page = request.args.get('page', 1, type=int)
    if page < 1:
        page = 1
    
    per_page = request.args.get('per_page', per_page, type=int)
    if per_page < 1 or per_page > max_per_page:
        per_page = max_per_page
    
    return page, per_page


def get_pagination_data(pagination, page_name: str = 'page') -> dict:
    """Generate pagination data for templates"""
    return {
        'has_prev': pagination.has_prev,
        'has_next': pagination.has_next,
        'prev_num': pagination.prev_num,
        'next_num': pagination.next_num,
        'current_page': pagination.page,
        'pages': pagination.pages,
        'total': pagination.total,
        'per_page': pagination.per_page,
        'iter_pages': get_page_range(pagination.pages, pagination.page)
    }


def get_page_range(pages: int, current: int, delta: int = 2) -> list:
    """Generate page range for pagination"""
    left = max(1, current - delta)
    right = min(pages, current + delta)
    
    pages_range = []
    
    if left > 1:
        pages_range.append(1)
        if left > 2:
            pages_range.append('...')
    
    for page in range(left, right + 1):
        pages_range.append(page)
    
    if right < pages:
        if right < pages - 1:
            pages_range.append('...')
        pages_range.append(pages)
    
    return pages_range


def get_cdn_url(path: str) -> str:
    """Get CDN URL for static assets"""
    from flask import current_app
    
    cdn_url = current_app.config.get('CDN_URL', '')
    if cdn_url:
        return f'{cdn_url}{path}'
    return path


def save_file(file, folder: str, allowed_extensions: set = None) -> str:
    """Save uploaded file and return path"""
    from flask import current_app
    from werkzeug.utils import secure_filename
    import os
    import uuid
    
    if allowed_extensions is None:
        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', set())
    
    if not file or file.filename == '':
        return None
    
    if '.' not in file.filename:
        return None
    
    ext = file.filename.rsplit('.', 1)[1].lower()
    if ext not in allowed_extensions:
        return None
    
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], folder, filename)
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    file.save(filepath)
    
    return f'/static/uploads/{folder}/{filename}'


def delete_file(filepath: str) -> bool:
    """Delete a file"""
    from flask import current_app
    import os
    
    if not filepath:
        return False
    
    # Handle both absolute and relative paths
    if filepath.startswith('/'):
        full_path = current_app.config['BASE_DIR'] / 'app' / filepath.lstrip('/')
    else:
        full_path = current_app.config['BASE_DIR'] / filepath
    
    if os.path.exists(full_path):
        os.remove(full_path)
        return True
    
    return False


def resize_image(image_path: str, width: int, height: int, output_path: str = None):
    """Resize an image"""
    from PIL import Image
    import os
    
    if not os.path.exists(image_path):
        return None
    
    with Image.open(image_path) as img:
        # Convert RGBA to RGB if necessary
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        resized = img.resize((width, height), Image.Resampling.LANCZOS)
        
        if output_path is None:
            output_path = image_path
        
        resized.save(output_path, 'JPEG', quality=85, optimize=True)
    
    return output_path


def sanitize_html(html: str, allowed_tags: list = None) -> str:
    """Sanitize HTML content"""
    import bleach
    
    if allowed_tags is None:
        allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                       'ul', 'ol', 'li', 'a', 'img', 'blockquote', 'code', 'pre']
    
    return bleach.clean(
        html,
        tags=allowed_tags,
        attributes={'a': ['href', 'title', 'target'], 'img': ['src', 'alt', 'title']},
        strip=True
    )


def generate_hash(text: str, algorithm: str = 'sha256') -> str:
    """Generate hash of text"""
    if algorithm == 'md5':
        return hashlib.md5(text.encode()).hexdigest()
    elif algorithm == 'sha1':
        return hashlib.sha1(text.encode()).hexdigest()
    else:
        return hashlib.sha256(text.encode()).hexdigest()


def is_valid_email(email: str) -> bool:
    """Validate email address"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_phone(phone: str) -> bool:
    """Validate Iranian phone number"""
    pattern = r'^09[0-9]{9}$'
    return bool(re.match(pattern, phone))


def is_valid_national_code(code: str) -> bool:
    """Validate Iranian national code"""
    if not code or len(code) != 10:
        return False
    
    if not code.isdigit():
        return False
    
    return True


def parse_json(value: str, default=None):
    """Parse JSON string safely"""
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default


def rate_limit_key():
    """Generate rate limit key for current request"""
    from flask import request
    from flask_login import current_user
    
    if current_user.is_authenticated:
        return f'rate_limit:{current_user.id}'
    
    return f'rate_limit:{request.remote_addr}'


def cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate cache key"""
    parts = [prefix]
    
    for arg in args:
        parts.append(str(arg))
    
    for key, value in sorted(kwargs.items()):
        parts.append(f'{key}:{value}')
    
    return ':'.join(parts)


def get_client_ip() -> str:
    """Get client IP address"""
    from flask import request
    
    if request.environ.get('HTTP_X_FORWARDED_FOR'):
        return request.environ['HTTP_X_FORWARDED_FOR'].split(',')[0]
    return request.environ.get('REMOTE_ADDR')


def is_ajax_request() -> bool:
    """Check if request is AJAX"""
    from flask import request
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


# ==================== Persian number conversion ====================

PERSIAN_DIGITS = '۰۱۲۳۴۵۶۷۸۹'
ARABIC_DIGITS = '٠١٢٣٤٥٦٧٨٩'
PERSIAN_TO_EN_TABLE = str.maketrans(PERSIAN_DIGITS + ARABIC_DIGITS, '0123456789' * 2)
EN_TO_PERSIAN_TABLE = str.maketrans('0123456789', PERSIAN_DIGITS)


def to_persian_digits(text: str) -> str:
    """Convert English/Arabic digits to Persian digits (۰۱۲۳...)."""
    if not text:
        return text
    return str(text).translate(EN_TO_PERSIAN_TABLE)


def to_english_digits(text: str) -> str:
    """Convert Persian/Arabic digits to English (0-9)."""
    if not text:
        return text
    return str(text).translate(PERSIAN_TO_EN_TABLE)


# ==================== Table of Contents ====================

def extract_toc(html_content: str, min_level: int = 2, max_level: int = 3) -> List[dict]:
    """
    Extract heading tags (h2-h3) from HTML and build a Table of Contents.

    Each item: {'level': int, 'title': str, 'id': str}
    The IDs are derived from the heading text (slugified) so anchors work.
    """
    if not html_content:
        return []

    # Find all h2-h3 with their text
    pattern = re.compile(
        r'<h([' + str(min_level) + '-' + str(max_level) + r'])(\b[^>]*)>(.*?)</h\1>',
        re.DOTALL | re.IGNORECASE,
    )

    used_ids = set()
    toc = []
    for match in pattern.finditer(html_content):
        level = int(match.group(1))
        attrs = match.group(2) or ''
        inner = match.group(3) or ''

        # If an id is already set in HTML, use it
        id_match = re.search(r'\bid\s*=\s*["\']([^"\']+)["\']', attrs)
        if id_match:
            heading_id = id_match.group(1)
        else:
            # Strip HTML tags to get plain text
            text = re.sub(r'<[^>]+>', '', inner)
            text = re.sub(r'\s+', ' ', text).strip()
            heading_id = _slugify_for_anchor(text)
            if not heading_id:
                continue
            # Ensure unique
            base = heading_id
            i = 2
            while heading_id in used_ids:
                heading_id = f"{base}-{i}"
                i += 1

        used_ids.add(heading_id)

        # Clean title
        title = re.sub(r'<[^>]+>', '', inner)
        title = re.sub(r'\s+', ' ', title).strip()
        if not title:
            continue

        toc.append({
            'level': level,
            'title': title,
            'id': heading_id,
        })

    return toc


def _slugify_for_anchor(text: str) -> str:
    """Make a URL-safe anchor id (works with Persian)."""
    if not text:
        return ''
    text = text.strip().lower()
    # Replace Persian/Arabic digits with Latin
    text = text.translate(PERSIAN_TO_EN_TABLE)
    # Replace spaces with hyphens
    text = re.sub(r'\s+', '-', text)
    # Keep Persian letters, Latin letters, digits, hyphens
    text = re.sub(r'[^\w\u0600-\u06FF\-]', '', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def inject_heading_ids(html_content: str, min_level: int = 2, max_level: int = 3) -> str:
    """
    Add id="..." attributes to h2-h3 in HTML so TOC anchors work.

    This mutates the HTML in-place but safely (preserves existing ids).
    """
    if not html_content:
        return html_content

    def repl(match):
        level = match.group(1)
        attrs = match.group(2) or ''
        inner = match.group(3) or ''

        # Don't overwrite an existing id
        if 'id=' in attrs.lower():
            return match.group(0)

        text = re.sub(r'<[^>]+>', '', inner)
        text = re.sub(r'\s+', ' ', text).strip()
        heading_id = _slugify_for_anchor(text)
        if not heading_id:
            return match.group(0)
        return f'<h{level} id="{heading_id}"{attrs}>{inner}</h{level}>'

    pattern = re.compile(
        r'<h([' + str(min_level) + '-' + str(max_level) + r'])(\b[^>]*)>(.*?)</h\1>',
        re.DOTALL | re.IGNORECASE,
    )
    return pattern.sub(repl, html_content)



def unique_slug(model, text, slug_field='slug', exclude_id=None, max_attempts=1000):
    """Generate a guaranteed-unique slug for a SQLAlchemy model.

    Falls back to a short random token when ``text`` produces an empty slug
    (e.g. purely Persian input), so models with a NOT NULL/unique ``slug``
    never raise an IntegrityError on create.
    """
    import secrets
    base = slugify(text)
    if not base:
        table = getattr(model, '__tablename__', 'item') or 'item'
        base = f"{table}-{secrets.token_hex(3)}"

    slug = base
    n = 1
    field = getattr(model, slug_field)
    for _ in range(max_attempts):
        q = model.query.filter(field == slug)
        if exclude_id is not None:
            q = q.filter(model.id != exclude_id)
        if not q.first():
            return slug
        slug = f"{base}-{n}"
        n += 1
    # Extremely unlikely fallback
    return f"{base}-{secrets.token_hex(3)}"
