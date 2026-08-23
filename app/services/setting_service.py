"""
Setting Service
"""
from typing import Dict, Any, Optional
from flask import current_app
import json

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
            'site_name': ('فلاسک پرو', 'string', True, 'نام سایت', 'نام سایت شما'),
            'site_url': ('https://example.com', 'string', True, 'آدرس سایت', 'آدرس اصلی سایت'),
            'tagline': ('بهترین فروشگاه آنلاین', 'string', True, 'تگ‌لاین', 'جمله کوتاه تبلیغاتی'),
            'copyright': ('تمامی حقوق محفوظ است', 'string', True, 'کپی‌رایت', ''),
        }
        
        # Contact settings
        default_contact = {
            'email': ('info@example.com', 'string', True, 'ایمیل تماس', ''),
            'phone': ('021-12345678', 'string', True, 'تلفن', ''),
            'mobile': ('0912-1234567', 'string', True, 'موبایل', ''),
            'address': ('تهران، خیابان ولیعصر', 'text', True, 'آدرس', ''),
            'working_hours': ('شنبه تا پنجشنبه: ۹ صبح تا ۶ عصر', 'string', True, 'ساعات کاری', ''),
        }
        
        # Social settings
        default_social = {
            'instagram': ('https://instagram.com/', 'string', True, 'اینستاگرام', ''),
            'telegram': ('https://t.me/', 'string', True, 'تلگرام', ''),
            'whatsapp': ('', 'string', True, 'واتساپ', ''),
            'twitter': ('', 'string', True, 'توییتر', ''),
            'facebook': ('', 'string', True, 'فیسبوک', ''),
            'linkedin': ('', 'string', True, 'لینکدین', ''),
        }
        
        # SEO settings
        default_seo = {
            'default_title': ('فلاسک پرو', 'string', True, 'عنوان پیش‌فرض', ''),
            'default_description': ('فروشگاه آنلاین فلاسک پرو', 'text', True, 'توضیحات پیش‌فرض', ''),
            'default_keywords': ('فروشگاه, آنلاین, خرید', 'string', True, 'کلمات کلیدی پیش‌فرض', ''),
            'og_image': ('', 'string', True, 'تصویر پیش‌فرض OG', ''),
        }
        
        # Appearance settings
        default_appearance = {
            'primary_color': ('#007bff', 'color', True, 'رنگ اصلی', ''),
            'secondary_color': ('#6c757d', 'color', True, 'رنگ ثانویه', ''),
            'logo': ('', 'string', True, 'لوگو', ''),
            'favicon': ('', 'string', True, 'فاویکون', ''),
            'dark_mode': ('false', 'boolean', True, 'حالت تاریک', ''),
        }
        
        all_defaults = {
            'general': default_general,
            'contact': default_contact,
            'social': default_social,
            'seo': default_seo,
            'appearance': default_appearance,
        }
        
        for group, settings in all_defaults.items():
            for key, (value, stype, is_public, label, desc) in settings.items():
                existing = Setting.query.filter_by(group=group, key=key).first()
                if not existing:
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
        
        db.session.commit()
    
    @staticmethod
    def clear_cache() -> None:
        """Clear settings cache"""
        from app.extensions import cache
        cache.delete('site_settings')
