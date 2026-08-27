"""
سرویس منوهای ناوبری — هدر/فوتر داینامیک (الگوی Header/Footer Builder قالب‌های راست‌چین)

منوهای دیتابیسی (جدول menus) را به ساختار قابل رندر برای قالب تبدیل می‌کند.
اگر منویی در دیتابیس نباشد، قالب به نسخهٔ پیش‌فرض (هاردکد) برمی‌گردد —
یعنی بدون هیچ تنظیمی سایت مثل قبل کار می‌کند (graceful degradation).

کش: ۵ دقیقه — کلیدهای menu_header / menu_footer (همان کلیدهایی که
admin routes پاک می‌کنند).
"""
from typing import Any, Dict, List, Optional

from app.extensions import cache
from app.models.menu import Menu

POSITIONS = ('header', 'footer')
_CACHE_KEY = {'header': 'menu_header', 'footer': 'menu_footer'}
_CACHE_TTL = 300  # seconds


def _build_item(m: Menu) -> Dict[str, Any]:
    """تبدیل یک ردیف Menu به دیکشنری قابل رندر (با فرزندان)."""
    children: List[Dict[str, Any]] = []
    try:
        for c in m.get_children_ordered():
            children.append(_build_item(c))
    except Exception:
        children = []

    return {
        'id': m.id,
        'title': m.title,
        'url': m.full_url,
        'icon': m.icon,
        'target': m.target or '_self',
        'no_follow': bool(m.no_follow),
        'badge_text': m.badge_text,
        'badge_color': m.badge_color,
        'is_mega': bool(m.is_mega_menu),
        'show_logged_in': m.show_logged_in if m.show_logged_in is not None else True,
        'show_guest': m.show_guest if m.show_guest is not None else True,
        'children': children,
    }


def _visible(item: Dict[str, Any], is_authenticated: bool) -> bool:
    """فیلتر نمایش بر اساس وضعیت ورود کاربر."""
    if is_authenticated:
        return item['show_logged_in']
    return item['show_guest']


def get_nav(position: str = 'header', is_authenticated: bool = False) -> List[Dict[str, Any]]:
    """
    گرفتن منوی یک موقعیت (header/footer) به‌صورت کش‌شده.
    خروجی: لیست آیتم‌های سطح-۱ (با فرزندان تودرتو) فیلترشده بر اساس ورود کاربر.
    """
    if position not in _CACHE_KEY:
        return []

    items: Optional[List[Dict[str, Any]]] = None
    try:
        items = cache.get(_CACHE_KEY[position])
    except Exception:
        items = None

    if items is None:
        try:
            rows = Menu.get_menu_by_position(position)
            items = [_build_item(m) for m in rows]
        except Exception:
            items = []
        try:
            cache.set(_CACHE_KEY[position], items, timeout=_CACHE_TTL)
        except Exception:
            pass

    # فیلتر دیداری بعد از کش (به‌ازای هر درخواست)
    result = []
    for it in items:
        if not _visible(it, is_authenticated):
            continue
        it_copy = dict(it)
        it_copy['children'] = [
            c for c in it['children'] if _visible(c, is_authenticated)
        ]
        result.append(it_copy)
    return result


def clear_cache(position: Optional[str] = None) -> None:
    """پاکسازی کش منو (بعد از هر تغییر در پنل)."""
    keys = [_CACHE_KEY[position]] if position in _CACHE_KEY else list(_CACHE_KEY.values())
    for k in keys:
        try:
            cache.delete(k)
        except Exception:
            pass
