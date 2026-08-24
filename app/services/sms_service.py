"""
SMS Service — ارسال پیامک برای OTP (الگوی قالب نادر: ۷ اپراتور)

درایورها با متغیر محیطی SMS_DRIVER انتخاب می‌شوند:
  - console      : کد فقط در لاگ چاپ می‌شود (پیش‌فرض توسعه — بدون نیاز به اکانت)
  - kavenegar    : نیازمند KAVENEGAR_API_KEY
  - mellipayamak : نیازمند MELLIPAYAMAK_USERNAME و MELLIPAYAMAK_PASSWORD
  - smsir        : نیازمند SMSIR_API_KEY
هر درایور فقط requests (یا urllib) استفاده می‌کند تا وابستگی سبک بماند.
"""
import logging
import os

import requests

logger = logging.getLogger(__name__)

TEMPLATE_OTP = 'کد ورود شما به {site}: {code}\nاعتبار: {minutes} دقیقه'


class SmsService:
    """ارسال پیامک با درایور قابل‌تعویض"""

    @staticmethod
    def driver() -> str:
        return os.getenv('SMS_DRIVER', 'console').lower()

    @staticmethod
    def is_configured() -> bool:
        driver = SmsService.driver()
        if driver == 'console':
            return True
        if driver == 'kavenegar':
            return bool(os.getenv('KAVENEGAR_API_KEY'))
        if driver == 'mellipayamak':
            return bool(os.getenv('MELLIPAYAMAK_USERNAME') and os.getenv('MELLIPAYAMAK_PASSWORD'))
        if driver == 'smsir':
            return bool(os.getenv('SMSIR_API_KEY'))
        return False

    @staticmethod
    def send(phone: str, message: str) -> tuple:
        """ارسال پیامک — خروجی: (ok: bool, detail: str)"""
        driver = SmsService.driver()
        try:
            if driver == 'kavenegar':
                return SmsService._send_kavenegar(phone, message)
            if driver == 'mellipayamak':
                return SmsService._send_mellipayamak(phone, message)
            if driver == 'smsir':
                return SmsService._send_smsir(phone, message)
            return SmsService._send_console(phone, message)
        except Exception as exc:  # noqa: BLE001 — لاگ و ادامه
            logger.error('SMS send failed (%s): %s', driver, exc)
            return False, str(exc)

    # ------------------------------------------------------------------ OTP

    @staticmethod
    def send_otp(phone: str, code: str, minutes: int = 3) -> tuple:
        from flask import current_app
        site = 'سایت'
        try:
            from app.services.setting_service import SettingService
            site = SettingService.get_setting('general', 'site_name', 'سایت') or 'سایت'
        except Exception:  # noqa: BLE001
            pass
        text = TEMPLATE_OTP.format(site=site, code=code, minutes=minutes)
        ok, detail = SmsService.send(phone, text)
        # در حالت توسعه کد را در لاگ نگه می‌داریم تا بدون پنل پیامکی هم قابل تست باشد
        logger.info('OTP for %s => %s (driver=%s)', phone, code if not ok else '***', SmsService.driver())
        return ok, detail

    # ------------------------------------------------------------- drivers

    @staticmethod
    def _send_console(phone: str, message: str) -> tuple:
        logger.warning('[SMS:console] to=%s message=%r', phone, message)
        print(f'\n[SMS:console] → {phone}\n{message}\n')
        return True, 'console'

    @staticmethod
    def _send_kavenegar(phone: str, message: str) -> tuple:
        api_key = os.getenv('KAVENEGAR_API_KEY')
        sender = os.getenv('KAVENEGAR_SENDER', '')
        url = f'https://api.kavenegar.com/v1/{api_key}/sms/send.json'
        resp = requests.post(url, data={'receptor': phone, 'message': message, 'sender': sender}, timeout=10)
        data = resp.json()
        ok = resp.status_code == 200 and data.get('return', {}).get('status') == 200
        return ok, str(data.get('return', {}).get('message', ''))

    @staticmethod
    def _send_mellipayamak(phone: str, message: str) -> tuple:
        from requests.auth import HTTPBasicAuth
        username = os.getenv('MELLIPAYAMAK_USERNAME')
        password = os.getenv('MELLIPAYAMAK_PASSWORD')
        line = os.getenv('MELLIPAYAMAK_LINE', '')
        url = 'https://rest.payamak-panel.com/api/SendSMS/SendSMS'
        resp = requests.post(url, json={'username': username, 'password': password,
                                        'to': phone, 'from': line, 'text': message}, timeout=10)
        ok = resp.status_code == 200
        return ok, resp.text[:200]

    @staticmethod
    def _send_smsir(phone: str, message: str) -> tuple:
        api_key = os.getenv('SMSIR_API_KEY')
        url = 'https://api.sms.ir/v1/send/bulk'
        resp = requests.post(url, headers={'x-api-key': api_key},
                             json={'lineNumber': os.getenv('SMSIR_LINE', ''),
                                   'messageText': message, 'mobiles': [phone]}, timeout=10)
        return resp.status_code == 200, resp.text[:200]
