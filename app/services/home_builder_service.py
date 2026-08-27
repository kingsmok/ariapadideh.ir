"""
صفحه‌ساز خانه (Home Section Builder) — الگوی Visual Page Builder قالب‌های راست‌چین

ترتیب/نمایش/عنوان بخش‌های صفحهٔ اول در تنظیمات (گروه appearance، کلید
home_sections) به‌صورت JSON ذخیره می‌شود:
    [{"key":"hero","title":"...","enabled":true}, …]

اگر تنظیمی نباشد، ترتیب پیش‌فرض قالب استفاده می‌شود — یعنی بدون هیچ
تنظیمی صفحهٔ اول دقیقاً مثل قبل رندر می‌شود (graceful degradation).
"""
import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

SETTING_GROUP = 'appearance'
SETTING_KEY = 'home_sections'

# کلیدهای مجاز — هر کلید خارج از این لیست نادیده گرفته می‌شود
SECTION_KEYS = (
    'hero',       # هدر اصلی
    'stories',    # نوار استوری
    'services',   # خدمات (بنتو گرید)
    'quote',      # فرم درخواست مشاوره
    'featured',   # محصولات ویژه
    'team',       # تیم ما
    'pricing',    # جداول تعرفه
    'faq',        # سوالات متداول
)

DEFAULT_SECTIONS: List[Dict[str, Any]] = [
    {'key': 'hero', 'title': '', 'enabled': True},
    {'key': 'stories', 'title': '', 'enabled': True},
    {'key': 'services', 'title': '', 'enabled': True},
    {'key': 'quote', 'title': '', 'enabled': True},
    {'key': 'featured', 'title': '', 'enabled': True},
    {'key': 'team', 'title': '', 'enabled': True},
    {'key': 'pricing', 'title': '', 'enabled': True},
    {'key': 'faq', 'title': '', 'enabled': True},
]

SECTION_LABELS = {
    'hero': 'هدر اصلی (Hero)',
    'stories': 'نوار استوری اینستاگرامی',
    'services': 'بخش خدمات',
    'quote': 'فرم درخواست مشاوره',
    'featured': 'محصولات ویژه',
    'team': 'تیم ما',
    'pricing': 'جداول تعرفه',
    'faq': 'سوالات متداول',
}


def get_sections() -> List[Dict[str, Any]]:
    """خواندن ترتیب بخش‌ها از تنظیمات؛ در نبود تنظیم، پیش‌فرض."""
    sections: List[Dict[str, Any]] = []
    try:
        from app.services.setting_service import SettingService
        raw = SettingService.get_setting(SETTING_GROUP, SETTING_KEY)
        if raw:
            sections = _normalize(raw)
    except Exception as exc:  # هر خطای دیتابیس/کش → پیش‌فرض
        logger.warning('home_builder: fallback to defaults (%s)', exc)

    if not sections:
        sections = [dict(s) for s in DEFAULT_SECTIONS]

    # هر بخش پیش‌فرضِ جاافتاده به انتهای لیست اضافه می‌شود
    present = {s['key'] for s in sections}
    for d in DEFAULT_SECTIONS:
        if d['key'] not in present:
            sections.append(dict(d))
    return sections


def save_sections(sections: List[Dict[str, Any]]) -> None:
    """ذخیرهٔ ترتیب بخش‌ها (نرمال‌شده) در تنظیمات + پاکسازی کش تنظیمات."""
    from app.services.setting_service import SettingService
    SettingService.set_setting(SETTING_GROUP, SETTING_KEY, _normalize(sections) or DEFAULT_SECTIONS)
    try:
        SettingService.clear_cache()
    except Exception:
        pass


def _normalize(raw: Any) -> List[Dict[str, Any]]:
    """تبدیل ورودی (JSON string یا لیست) به لیست تمیز از بخش‌های مجاز."""
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (ValueError, TypeError):
            return []
    if not isinstance(raw, list):
        return []

    result: List[Dict[str, Any]] = []
    seen = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        key = str(item.get('key', ''))
        if key not in SECTION_KEYS or key in seen:
            continue
        seen.add(key)
        title = str(item.get('title') or '').strip()[:120]
        enabled = item.get('enabled')
        result.append({
            'key': key,
            'title': title,
            'enabled': True if enabled in (True, 'true', 'on', '1', 1) else False,
        })
    return result
