"""
AI Content Service — تولید پیش‌نویس محتوا با هوش مصنوعی (الگوی قالب کرافتو)

با هر سرویس سازگار با OpenAI Chat Completions کار می‌کند (OpenAI، OpenRouter،
Groq، doubleo و سرویس‌های ایرانی سازگار). کافی است در .env تنظیم شود:

    AI_API_BASE=https://api.openai.com/v1
    AI_API_KEY=sk-...
    AI_MODEL=gpt-4o-mini

اگر تنظیم نشده باشد، سرویس به‌صورت شفاف «غیرفعال» گزارش می‌شود
(خطایی در رابط کاربری نمی‌بینید — فقط پیام راهنما).
"""
import logging
import os

import requests

logger = logging.getLogger(__name__)

PRESETS = {
    'product_desc': {
        'label': 'توضیح محصول',
        'system': 'تو یک کپی‌رایتر حرفه‌ای فروشگاه آنلاین فارسی‌زبان هستی.',
        'instruction': (
            'برای محصول «{topic}» یک توضیح فروشی بنویس:\n'
            '- بند اول: معرفی جذاب ۲ جمله‌ای\n'
            '- ۴ تا ۶ ویژگی کلیدی به‌صورت لیست با خط تیره\n'
            '- بند آخر: دعوت به خرید\n'
            'فقط HTML ساده (<p> و <ul><li>) خروجی بده، فارسی روان، بدون اغراق.'
        ),
    },
    'post_intro': {
        'label': 'مقدمه مقاله',
        'system': 'تو یک ویراستار حرفه‌ای وبلاگ فارسی‌زبان هستی.',
        'instruction': (
            'برای مقاله‌ای با موضوع «{topic}» یک مقدمه ۳ جمله‌ای بنویس که خواننده را '
            'به ادامهٔ خواندن ترغیب کند. فقط متن، بدون عنوان.'
        ),
    },
    'seo_meta': {
        'label': 'توضیحات متا (سئو)',
        'system': 'تو یک متخصص سئوی فارسی هستی.',
        'instruction': (
            'برای صفحهٔ «{topic}» یک meta description حداکثر ۱۵۵ کاراکتری بنویس؛ '
            'فقط خود جمله، بدون توضیح اضافه.'
        ),
    },
    'faq': {
        'label': 'سوال متداول',
        'system': 'تو پشتیبان ارتباط با مشتری فارسی‌زبان هستی.',
        'instruction': (
            'برای «{topic}» یک سوال متداول احتمالی مشتری + پاسخ کوتاه (حداکثر ۳ جمله) بنویس. '
            'قالب: سوال؟ | پاسخ'
        ),
    },
}


class AiService:
    """تولید محتوای کمکی با مدل زبانی"""

    @staticmethod
    def is_configured() -> bool:
        return bool(os.getenv('AI_API_KEY'))

    @staticmethod
    def config_info() -> dict:
        return {
            'configured': AiService.is_configured(),
            'base': os.getenv('AI_API_BASE', 'https://api.openai.com/v1'),
            'model': os.getenv('AI_MODEL', 'gpt-4o-mini'),
        }

    @staticmethod
    def presets() -> dict:
        return {key: p['label'] for key, p in PRESETS.items()}

    @staticmethod
    def generate(preset: str, topic: str, extra: str = '') -> str:
        """تولید متن — در صورت خطا استثنا با پیام فارسی پرتاب می‌شود"""
        if not AiService.is_configured():
            raise RuntimeError(
                'سرویس هوش مصنوعی فعال نیست. برای فعال‌سازی، AI_API_KEY را در .env تنظیم کنید '
                '(سازگار با OpenAI/OpenRouter/Groq).'
            )

        preset = PRESETS.get(preset)
        if not preset:
            raise ValueError('پیش‌فرض نامعتبر است')

        prompt = preset['instruction'].format(topic=topic[:500])
        if extra:
            prompt += f'\n\nنکات تکمیلی: {extra[:500]}'

        base = os.getenv('AI_API_BASE', 'https://api.openai.com/v1').rstrip('/')
        model = os.getenv('AI_MODEL', 'gpt-4o-mini')

        try:
            resp = requests.post(
                f'{base}/chat/completions',
                headers={'Authorization': f'Bearer {os.getenv("AI_API_KEY")}'},
                json={
                    'model': model,
                    'messages': [
                        {'role': 'system', 'content': preset['system']},
                        {'role': 'user', 'content': prompt},
                    ],
                    'temperature': 0.7,
                },
                timeout=60,
            )
        except requests.RequestException as exc:
            logger.error('AI request failed: %s', exc)
            raise RuntimeError('ارتباط با سرویس هوش مصنوعی برقرار نشد') from exc

        if resp.status_code != 200:
            raise RuntimeError(f'خطای سرویس AI ({resp.status_code}): {resp.text[:200]}')

        content = resp.json().get('choices', [{}])[0].get('message', {}).get('content', '')
        if not content:
            raise RuntimeError('پاسخی از مدل دریافت نشد')
        return content.strip()
