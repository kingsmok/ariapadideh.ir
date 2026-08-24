"""
Setting Service
"""
from typing import Dict, Any, Optional
from flask import current_app
import json

from app.extensions import db
from app.models import Setting


class SettingService:
    """Site Settings Operations"""
    
    @staticmethod
    def get_public_settings() -> Dict[str, Any]:
        """Get all public settings as dictionary"""
        
        settings = Setting.query.filter_by(is_public=True).all()
        
        result = {}
        for setting in settings:
            value = SettingService.format_setting_value(setting)
            result[f"{setting.group}_{setting.key}"] = value
            
            # Also create a nested structure
            if setting.group not in result:
                result[setting.group] = {}
            result[setting.group][setting.key] = value
        
        # Add defaults if not set
        result.setdefault('general', {})
        result.setdefault('contact', {})
        result.setdefault('social', {})
        result.setdefault('appearance', {})
        
        return result
    
    @staticmethod
    def get_setting(group: str, key: str, default: Any = None) -> Any:
        """Get a specific setting value"""
        
        value = Setting.get_value(group, key, default)
        
        if value and isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        
        return value
    
    @staticmethod
    def set_setting(group: str, key: str, value: Any, 
                   setting_type: str = 'string', is_public: bool = False,
                   label: str = None, description: str = None) -> Setting:
        """Set a setting value"""
        
        return Setting.set_value(group, key, value, setting_type)
    
    @staticmethod
    def get_group_settings(group: str) -> Dict[str, Any]:
        """Get all settings in a group"""
        
        return Setting.get_group(group)
    
    @staticmethod
    def format_setting_value(setting: Setting) -> Any:
        """Format setting value based on type"""
        
        if setting.value is None:
            return None
        
        if setting.type == 'boolean':
            return setting.value in ('true', '1', 'yes', 'on')
        
        if setting.type == 'integer':
            try:
                return int(setting.value)
            except (ValueError, TypeError):
                return setting.value
        
        if setting.type == 'float':
            try:
                return float(setting.value)
            except (ValueError, TypeError):
                return setting.value
        
        if setting.type == 'json':
            try:
                return json.loads(setting.value)
            except (json.JSONDecodeError, TypeError):
                return setting.value
        
        return setting.value
    
    @staticmethod
    def init_default_settings() -> None:
        """Initialize default settings if not exist"""
        
        # General settings
        default_general = {
            'site_name': ('رهسا دیو', 'string', True, 'نام سایت', 'نام شرکت'),
            'site_url': ('https://rahsadev.ir', 'string', True, 'آدرس سایت', 'آدرس رسمی'),
            'tagline': ('راهکارهای جامع توسعه نرم‌افزار، طراحی وب‌سایت و ربات‌های هوشمند', 'string', True, 'تگ‌لاین', 'شعار شرکت'),
            'copyright': ('تمامی حقوق محفوظ و متعلق به رهسا دیو می‌باشد.', 'string', True, 'کپی‌رایت', ''),
        }
        
        # Contact settings
        default_contact = {
            'email': ('info@rahsadev.ir', 'string', True, 'ایمیل تماس', ''),
            'phone': ('071-37271621', 'string', True, 'تلفن', ''),
            'mobile': ('021-88991234', 'string', True, 'موبایل', ''),
            'address': ('شیراز، بلوار دلاوران / تهران، ناحیه نوآوری شریف', 'text', True, 'آدرس', ''),
            'working_hours': ('شنبه تا پنجشنبه: ۹ صبح تا ۱۸ عصر', 'string', True, 'ساعات کاری', ''),
            # نقشهٔ OpenStreetMap در صفحهٔ تماس (الگوی قالب آرنیکا — بدون تحریم و API)
            # مقدار: bbox یا iframe کامل از openstreetmap.org/export/embed.html
            'osm_map_embed': (
                'https://www.openstreetmap.org/export/embed.html?bbox=51.30%2C35.62%2C51.48%2C35.76&layer=mapnik',
                'text', True, 'نقشهٔ OSM (embed)', 'لینک embed نقشهٔ openstreetmap برای صفحهٔ تماس'
            ),
            'osm_map_enabled': ('true', 'boolean', True, 'نمایش نقشه در تماس', ''),
        }
        
        # Social settings
        default_social = {
            'instagram': ('https://instagram.com/rahsadev', 'string', True, 'اینستاگرام', ''),
            'telegram': ('https://t.me/rahsadev', 'string', True, 'تلگرام', ''),
            'whatsapp': ('https://wa.me/989121234567', 'string', True, 'واتساپ', ''),
            'twitter': ('', 'string', True, 'توییتر', ''),
            'facebook': ('', 'string', True, 'فیسبوک', ''),
            'linkedin': ('https://linkedin.com/company/rahsadev', 'string', True, 'لینکدین', ''),
        }
        
        # SEO settings
        default_seo = {
            'default_title': ('رهسا دیو | طراحی وب‌سایت، نرم‌افزار و ربات هوشمند', 'string', True, 'عنوان پیش‌فرض', ''),
            'default_description': ('مرکز تخصصی طراحی وب‌سایت‌های فروشگاهی و شرکتی، برنامه نویسی پایتون، اتوماسیون اداری و ربات تلگرام/ایتا', 'text', True, 'توضیحات پیش‌فرض', ''),
            'default_keywords': ('طراحی وب‌سایت, برنامه‌نویسی, ربات تلگرام, ربات ایتا, نرم‌افزار حسابداری, اسکریپت فروشگاهی', 'string', True, 'کلمات کلیدی پیش‌فرض', ''),
            'og_image': ('', 'string', True, 'تصویر پیش‌فرض OG', ''),
        }
        
        # Appearance settings
        default_appearance = {
            'primary_color': ('#2563eb', 'color', True, 'رنگ اصلی', ''),
            'secondary_color': ('#1e293b', 'color', True, 'رنگ ثانویه', ''),
            'logo': ('', 'string', True, 'لوگو', ''),
            'favicon': ('', 'string', True, 'فاویکون', ''),
            'dark_mode': ('false', 'boolean', True, 'حالت تاریک', ''),
            # --- قابلیت‌های جدید (تحلیل بازار قالب‌های شرکتی راست‌چین) ---
            'accent_color': ('#fbb03b', 'color', True, 'رنگ تأکید (طلایی برند)',
                             'رنگ دکمه‌ها و تأکیدها — از پنل قابل تغییر مثل قالب‌های راست‌چین'),
            'allow_theme_switch': ('true', 'boolean', True, 'دکمهٔ تم تیره/روشن',
                                   'کاربر بتواند بین تم تیره و روشن سوییچ کند (الگوی قالب نادر/کرافتو)'),
            'body_font': ('Vazirmatn', 'string', True, 'فونت متن',
                          'Vazirmatn / IRANSans / Shabnam / YekanBakh — مثل انتخاب فونت در قالب‌ها'),
            'heading_font': ('Vazirmatn', 'string', True, 'فونت تیترها', ''),
            'preloader_enabled': ('false', 'boolean', True, 'پیش‌بارگر (Preloader)',
                                  'نمایش صفحهٔ بارگذاری اولیه'),
            'preloader_style': ('spinner', 'string', True, 'طرح پیش‌بارگر', 'spinner / pulse / bar'),
        }

        # Features settings (خبرنامه / استوری / OTP)
        default_features = {
            'stories_enabled': ('true', 'boolean', True, 'نوار استوری صفحهٔ اصلی',
                                'استوری‌ساز اینستاگرامی (الگوی قالب نادر)'),
            'newsletter_enabled': ('true', 'boolean', True, 'فرم خبرنامه در فوتر', ''),
            'otp_login_enabled': ('true', 'boolean', True, 'ورود با موبایل (OTP)',
                                  'ورود/عضویت پیامکی — نیازمند تنظیم SMS_DRIVER در .env'),
        }

        all_defaults = {
            'general': default_general,
            'contact': default_contact,
            'social': default_social,
            'seo': default_seo,
            'appearance': default_appearance,
            'features': default_features,
        }
        
        for group, settings in all_defaults.items():
            for key, (value, stype, is_public, label, desc) in settings.items():
                setting = Setting.query.filter_by(group=group, key=key).first()
                if not setting:
                    setting = Setting(
                        group=group,
                        key=key,
                        value=value,
                        type=stype,
                        is_public=is_public,
                        label=label,
                        description=desc
                    )
                    db.session.add(setting)
                else:
                    setting.value = value
                    setting.is_public = is_public
        
        db.session.commit()
    
    @staticmethod
    def clear_cache() -> None:
        """Clear settings cache"""
        from app.extensions import cache
        cache.delete('site_settings')
