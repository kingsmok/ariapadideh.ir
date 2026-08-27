"""
پیوست تیکت‌ها — ذخیرهٔ امن فایل خارج از مسیر عمومی

فایل‌ها در instance/ticket_attachments/ ذخیره می‌شوند (خارج از static)
و فقط از طریق روت دارای بررسی دسترسی قابل دانلودند.
"""
import os
import uuid
from typing import Optional, Tuple

from flask import current_app
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {
    'png', 'jpg', 'jpeg', 'webp', 'gif',
    'pdf', 'zip', 'rar', '7z',
    'txt', 'doc', 'docx', 'xls', 'xlsx', 'csv',
}
MAX_SIZE_MB = 5


def attachments_dir() -> str:
    """پوشهٔ ذخیرهٔ پیوست‌ها (ایجاد در صورت نبود)."""
    from app.extensions import db  # noqa: F401 — فقط برای اطمینان از ایمپورت‌شدن اپ
    base = current_app.config.get('BASE_DIR') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(str(base), 'instance', 'ticket_attachments')
    os.makedirs(path, exist_ok=True)
    return path


def save_ticket_attachment(file) -> Tuple[Optional[str], Optional[str]]:
    """
    ذخیرهٔ امن پیوست تیکت.

    خروجی: (stored_filename, None) یا (None, error_message)
    stored_filename فقط نام فایل است — مسیر کامل از attachment_path() گرفته شود.
    """
    if file is None or not file.filename:
        return None, None  # فایلی ارسال نشده — خطا نیست

    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        return None, f'فرمت فایل مجاز نیست (فرمت‌های مجاز: {", ".join(sorted(ALLOWED_EXTENSIONS))})'

    # خواندن با سقف حجم
    file.stream.seek(0, os.SEEK_END)
    size = file.stream.tell()
    file.stream.seek(0)
    if size > MAX_SIZE_MB * 1024 * 1024:
        return None, f'حجم فایل بیشتر از {MAX_SIZE_MB} مگابایت است'

    # نام امن + uuid (نام اصلی فقط برای نمایش در دیتابیس ذخیره نمی‌شود)
    _ = secure_filename(file.filename)  # اعتبارسنجی — خروجی استفاده نمی‌شود
    stored = f'{uuid.uuid4().hex}.{ext}'
    file.save(os.path.join(attachments_dir(), stored))
    return stored, None


def attachment_path(stored_filename: str) -> Optional[str]:
    """مسیر کامل فایل پیوست با ضد تروجان مسیر (path traversal)."""
    if not stored_filename:
        return None
    stored_filename = os.path.basename(stored_filename)  # ضد ../
    full = os.path.join(attachments_dir(), stored_filename)
    return full if os.path.isfile(full) else None
