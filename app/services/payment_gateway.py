"""
Payment Gateway Service — driver pattern.

درگاه‌های پشتیبانی‌شده (بر اساس مستندات رسمی هر سرویس):
- MockGateway      : درگاه آزمایشی داخلی (توسعه/دمو)
- ZarinpalGateway  : زرین‌پال — PG v4 (payment.zarinpal.com/pg/v4)
- IDPayGateway     : آی‌دی‌پی — وب‌سرویس v1.1 (api.idpay.ir/v1.1)
- DigiPayGateway   : دیجی‌پی — درگاه پرداخت یکپارچه UPG (mydigipay.com)
- SnappPayGateway  : اسنپ‌پی — خرید اقساطی (payment.snapppay.ir)
- SepahGateway     : بانک سپه — الگوی استاندارد شاپرک (سپهر)

کلیدهای هر درگاه از تنظیمات پنل مدیریت (گروه payment) خوانده می‌شود و در
غیاب آن از متغیرهای محیطی (.env) استفاده می‌شود.
"""
import base64
import time
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple

import requests as _requests
from flask import current_app, request

from app.models import Order, PaymentTransaction
from app.constants import PaymentGateway, TransactionStatus

# مهلت پیش‌فرض تماس با سرویس‌های خارجی (ثانیه)
HTTP_TIMEOUT = (5, 20)


# ==================== Helpers ====================

def payment_setting(setting_key: str, config_key: str = '', default: Any = '') -> Any:
    """
    خواندن پیکربندی درگاه: اول تنظیمات پنل مدیریت (جدول settings، گروه payment)،
    بعد متغیر محیطی از کانفیگ فلاسک، بعد مقدار پیش‌فرض.
    """
    try:
        from app.models import Setting
        value = Setting.get_value('payment', setting_key, None)
        if value not in (None, ''):
            return value
    except Exception:
        pass
    if config_key and current_app.config.get(config_key):
        return current_app.config[config_key]
    return default


def amount_in_rial(order: Order) -> int:
    """
    مبالغ فروشگاه ممکن است به تومان ذخیره شوند؛ همه درگاه‌های ایرانی ریالی هستند.
    PAYMENT_CURRENCY_UNIT = toman (پیش‌فرض) → مبلغ × ۱۰
    """
    unit = current_app.config.get('PAYMENT_CURRENCY_UNIT', 'toman')
    amount = int(round(float(order.total_amount or 0)))
    if str(unit).lower() in ('toman', 't', 'تومان'):
        amount *= 10
    return amount


def _json(resp) -> Tuple[bool, Any]:
    """پاسخ HTTP را امن به JSON تبدیل می‌کند."""
    try:
        return True, resp.json()
    except ValueError:
        return False, {}


def _callback_payload() -> Dict[str, Any]:
    """داده کال‌بک — درگاه‌هایی که POST می‌کنند (IDPay/DigiPay/SnappPay/Sepah) و GET."""
    data: Dict[str, Any] = {}
    try:
        data.update(request.form.to_dict())
    except RuntimeError:
        pass
    data.update(request.args.to_dict())
    return data


# ==================== Core objects ====================

class PaymentResult:
    """Result of a payment operation."""

    def __init__(
        self,
        success: bool,
        transaction_id: str = '',
        redirect_url: str = '',
        error_message: str = '',
        error_code: str = '',
        raw_response: Optional[Dict] = None,
        # برای درگاه‌هایی که کاربر باید با POST فرم به آن‌ها هدایت شود (شاپرک/سپه)
        redirect_method: str = 'redirect',   # 'redirect' | 'form'
        form_url: str = '',
        form_fields: Optional[Dict[str, str]] = None,
    ):
        self.success = success
        self.transaction_id = transaction_id
        self.redirect_url = redirect_url
        self.error_message = error_message
        self.error_code = error_code
        self.raw_response = raw_response or {}
        self.redirect_method = redirect_method
        self.form_url = form_url
        self.form_fields = form_fields or {}

    def to_dict(self) -> Dict:
        return {
            'success': self.success,
            'transaction_id': self.transaction_id,
            'redirect_url': self.redirect_url,
            'error_message': self.error_message,
            'error_code': self.error_code,
            'redirect_method': self.redirect_method,
        }


class PaymentGatewayInterface(ABC):
    """Abstract interface for payment gateways."""

    gateway_name: str = 'abstract'
    # آیا کلیدهای لازم تنظیم شده؟ (برای نمایش/مخفی‌شدن در صفحه پرداخت)
    required_settings: tuple = ()

    def is_configured(self) -> bool:
        if not self.required_settings:
            return True
        return all(
            str(payment_setting(key, cfg, '') or '').strip()
            for key, cfg in self.required_settings
        )

    @abstractmethod
    def create_payment(self, order: Order, callback_url: str) -> PaymentResult:
        """Initiate a payment and return redirect URL."""
        raise NotImplementedError

    @abstractmethod
    def verify_payment(
        self,
        transaction: PaymentTransaction,
        callback_data: Dict[str, Any],
    ) -> PaymentResult:
        """Verify a payment after callback from gateway."""
        raise NotImplementedError


# ==================== Mock (توسعه) ====================

class MockGateway(PaymentGatewayInterface):
    """
    In-process mock gateway.

    For development & demo. Simulates a redirect flow:
    - create_payment returns a /payment/mock/<order_number> URL
    - that URL shows a page that lets the user 'Pay' or 'Cancel'
    - on Pay, the transaction is marked SUCCESS
    """
    gateway_name = PaymentGateway.MOCK.value

    def create_payment(self, order: Order, callback_url: str) -> PaymentResult:
        """Return a URL that simulates the gateway payment page."""
        reference = f'MOCK-{uuid.uuid4().hex[:12].upper()}'
        return PaymentResult(
            success=True,
            transaction_id=reference,
            redirect_url=f'/payment/mock/{order.order_number}?ref={reference}&callback={callback_url}',
        )

    def verify_payment(
        self,
        transaction: PaymentTransaction,
        callback_data: Dict[str, Any],
    ) -> PaymentResult:
        """Simulate verification. Status comes from callback_data['status']."""
        status = callback_data.get('status', 'success')
        reference = callback_data.get('ref', transaction.reference_id)

        if status == 'success':
            return PaymentResult(
                success=True,
                transaction_id=reference,
                raw_response={'status': 'success', 'ref': reference},
            )
        return PaymentResult(
            success=False,
            error_message='پرداخت توسط کاربر لغو شد.',
            error_code='cancelled',
        )


# ==================== ZarinPal (PG v4) ====================

class ZarinpalGateway(PaymentGatewayInterface):
    """
    زرین‌پال — مستندات رسمی PG v4:
      request:  POST https://payment.zarinpal.com/pg/v4/payment/request.json
      startpay: GET  https://payment.zarinpal.com/pg/StartPay/{authority}
      verify:   POST https://payment.zarinpal.com/pg/v4/payment/verify.json
      sandbox:  sandbox.zarinpal.com
    کال‌بک: GET ?Authority=...&Status=OK|NOK
    """
    gateway_name = PaymentGateway.ZARINPAL.value
    required_settings = (
        ('zarinpal_merchant_id', 'ZARINPAL_MERCHANT_ID'),
    )

    HOST = 'payment.zarinpal.com'
    SANDBOX_HOST = 'sandbox.zarinpal.com'

    # کدهای خطای رایج زرین‌پال
    ERROR_MAP = {
        -9: 'خطای اعتبارسنجی اطلاعات ارسالی',
        -10: 'ای‌پی‌آی یا ترمینال درگاه فعال نیست',
        -11: 'مرچنت آیدی نامعتبر است',
        -12: 'تلاش بیش از حد در بازه زمانی کوتاه',
        -15: 'مبلغ تراکنش خارج از محدوده مجاز است',
        -16: 'سطح درگاه پذیرندگی برای این پرداخت کافی نیست',
        -30: 'اجازه استفاده از این سرویس را ندارید',
        -31: 'حساب بانکی مرتبط با درگاه یافت نشد',
        -33: 'مبلغ تراکنش با مبلغ پرداخت‌شده مطابقت ندارد',
        -34: 'سقف تقسیم تراکنش برای این حساب پر شده',
        -40: 'پارامترهای اضافی غیرمجاز',
        -50: 'مبلغ پرداخت‌شده با مبلغ درخواستی برابر نیست',
        -51: 'پرداخت ناموفق',
        -52: 'خطای غیرمنتظره — با پشتیبانی تماس بگیرید',
        -53: 'پرداخت متعلق به این مرچنت نیست',
        -54: 'کد نا‌معتبر',
        101: 'تراکنش قبلاً وریفای شده است',
    }

    def _urls(self) -> Dict[str, str]:
        sandbox = str(payment_setting(
            'zarinpal_sandbox', 'ZARINPAL_SANDBOX', False
        )).lower() in ('1', 'true', 'yes', 'on')
        host = self.SANDBOX_HOST if sandbox else self.HOST
        return {
            'request': f'https://{host}/pg/v4/payment/request.json',
            'verify': f'https://{host}/pg/v4/payment/verify.json',
            'start': f'https://{host}/pg/StartPay/',
        }

    def create_payment(self, order: Order, callback_url: str) -> PaymentResult:
        merchant_id = str(payment_setting(
            'zarinpal_merchant_id', 'ZARINPAL_MERCHANT_ID', ''
        )).strip()
        if not merchant_id:
            return PaymentResult(
                success=False,
                error_message='درگاه زرین‌پال پیکربندی نشده است (مرچنت آیدی وجود ندارد).',
                error_code='config_missing',
            )
        if len(merchant_id) != 36:
            return PaymentResult(
                success=False,
                error_message='مرچنت آیدی زرین‌پال باید ۳۶ کاراکتر (UUID) باشد.',
                error_code='config_invalid',
            )

        metadata = {}
        if order.recipient_phone:
            metadata['mobile'] = order.recipient_phone
        elif order.user and order.user.phone:
            metadata['mobile'] = order.user.phone
        if order.user and order.user.email:
            metadata['email'] = order.user.email

        payload = {
            'merchant_id': merchant_id,
            'amount': amount_in_rial(order),          # ریال
            'callback_url': callback_url,
            'description': f'پرداخت سفارش {order.order_number}',
            'metadata': metadata,
        }
        try:
            resp = _requests.post(
                self._urls()['request'], json=payload, timeout=HTTP_TIMEOUT
            )
        except _requests.RequestException as e:
            return PaymentResult(
                success=False,
                error_message=f'عدم دسترسی به زرین‌پال: {e}',
                error_code='network_error',
            )

        ok, data = _json(resp)
        body = (data.get('data') or {}) if ok else {}
        errors = (data.get('errors') or {}) if ok else {}
        code = body.get('code')

        if code == 100 and body.get('authority'):
            authority = str(body['authority'])
            return PaymentResult(
                success=True,
                transaction_id=authority,
                redirect_url=self._urls()['start'] + authority,
                raw_response={'code': code, 'authority': authority},
            )

        # خطا — کد در errors یا data.code
        err_code = errors.get('code', code)
        err_msg = errors.get('message') or self.ERROR_MAP.get(err_code, 'خطای ناشناخته زرین‌پال')
        return PaymentResult(
            success=False,
            error_message=f'زرین‌پال: {err_msg} (کد {err_code})',
            error_code=f'zarinpal_{err_code}',
            raw_response=data,
        )

    def verify_payment(
        self,
        transaction: PaymentTransaction,
        callback_data: Dict[str, Any],
    ) -> PaymentResult:
        # کاربر از درگاه برگشته — Status=OK یعنی پرداخت انجام شده، باید وریفای کرد
        authority = (
            callback_data.get('Authority')
            or callback_data.get('authority')
            or transaction.reference_id
        )
        status = str(
            callback_data.get('Status') or callback_data.get('status') or ''
        ).upper()

        if not authority:
            return PaymentResult(
                success=False, error_message='شناسه پرداخت زرین‌پال یافت نشد.',
                error_code='missing_authority',
            )
        if status == 'NOK' or (status and status != 'OK'):
            return PaymentResult(
                success=False,
                error_message='پرداخت در زرین‌پال ناموفق بود یا توسط کاربر لغو شد.',
                error_code='cancelled',
            )

        merchant_id = str(payment_setting(
            'zarinpal_merchant_id', 'ZARINPAL_MERCHANT_ID', ''
        )).strip()
        payload = {
            'merchant_id': merchant_id,
            'amount': int(round(float(transaction.amount or 0))) * (
                10 if str(current_app.config.get('PAYMENT_CURRENCY_UNIT', 'toman')).lower()
                in ('toman', 't', 'تومان') else 1
            ),
            'authority': str(authority),
        }
        try:
            resp = _requests.post(
                self._urls()['verify'], json=payload, timeout=HTTP_TIMEOUT
            )
        except _requests.RequestException as e:
            return PaymentResult(
                success=False,
                error_message=f'عدم دسترسی به زرین‌پال هنگام تأیید: {e}',
                error_code='network_error',
            )

        ok, data = _json(resp)
        body = (data.get('data') or {}) if ok else {}
        errors = (data.get('errors') or {}) if ok else {}
        code = body.get('code')

        if code in (100, 101):  # 100=موفق، 101=قبلاً وریفای شده
            ref_id = str(body.get('ref_id') or authority)
            return PaymentResult(
                success=True,
                transaction_id=authority,
                raw_response={
                    'code': code, 'ref_id': ref_id,
                    'card_pan': body.get('card_pan'),
                    'card_kind': body.get('card_kind'),
                    'fee_type': body.get('fee_type'),
                    'code_description': self.ERROR_MAP.get(code, 'موفق'),
                },
            )

        err_code = errors.get('code', code)
        err_msg = errors.get('message') or self.ERROR_MAP.get(err_code, 'تأیید پرداخت ناموفق')
        return PaymentResult(
            success=False,
            error_message=f'زرین‌پال: {err_msg} (کد {err_code})',
            error_code=f'zarinpal_{err_code}',
            raw_response=data,
        )


# ==================== IDPay (v1.1) ====================

class IDPayGateway(PaymentGatewayInterface):
    """
    آی‌دی‌پی — مستندات رسمی وب‌سرویس v1.1:
      create:  POST https://api.idpay.ir/v1.1/payment   (X-API-KEY, X-SANDBOX)
      paypage: GET  {link}
      verify:  POST https://api.idpay.ir/v1.1/payment/verify
    کال‌بک: POST یا GET (تنظیم پنل) با id / order_id / status
    """
    gateway_name = PaymentGateway.IDPAY.value
    required_settings = (
        ('idpay_api_key', 'IDPAY_API_KEY'),
    )

    BASE = 'https://api.idpay.ir/v1.1'

    def _headers(self) -> Dict[str, str]:
        sandbox = str(payment_setting(
            'idpay_sandbox', 'IDPAY_SANDBOX', False
        )).lower() in ('1', 'true', 'yes', 'on')
        headers = {
            'X-API-KEY': str(payment_setting('idpay_api_key', 'IDPAY_API_KEY', '')).strip(),
            'Content-Type': 'application/json',
        }
        if sandbox:
            headers['X-SANDBOX'] = '1'
        return headers

    def create_payment(self, order: Order, callback_url: str) -> PaymentResult:
        if not str(payment_setting('idpay_api_key', 'IDPAY_API_KEY', '')).strip():
            return PaymentResult(
                success=False,
                error_message='درگاه آی‌دی‌پی پیکربندی نشده است (کلید API وجود ندارد).',
                error_code='config_missing',
            )

        payload = {
            'order_id': order.order_number,
            'amount': amount_in_rial(order),          # ریال
            'callback': callback_url,
            'desc': f'پرداخت سفارش {order.order_number}',
        }
        if order.recipient_phone:
            payload['phone'] = order.recipient_phone
        if order.user and order.user.email:
            payload['mail'] = order.user.email

        try:
            resp = _requests.post(
                f'{self.BASE}/payment', json=payload,
                headers=self._headers(), timeout=HTTP_TIMEOUT,
            )
        except _requests.RequestException as e:
            return PaymentResult(
                success=False, error_message=f'عدم دسترسی به آی‌دی‌پی: {e}',
                error_code='network_error',
            )

        if resp.status_code == 401:
            return PaymentResult(
                success=False,
                error_message='کلید API آی‌دی‌پی نامعتبر است (۴۰۱).',
                error_code='unauthorized', raw_response={'http': resp.status_code},
            )

        ok, data = _json(resp)
        if ok and data.get('id') and data.get('link'):
            return PaymentResult(
                success=True,
                transaction_id=str(data['id']),
                redirect_url=str(data['link']),
                raw_response=data,
            )
        if ok and data.get('error_message'):
            return PaymentResult(
                success=False,
                error_message=f"آی‌دی‌پی: {data.get('error_message')}",
                error_code=f"idpay_{data.get('error_code', 'error')}",
                raw_response=data,
            )
        return PaymentResult(
            success=False,
            error_message=f'پاسخ نامعتبر آی‌دی‌پی (HTTP {resp.status_code}).',
            error_code='invalid_response',
            raw_response={'body': resp.text[:500]},
        )

    def verify_payment(
        self,
        transaction: PaymentTransaction,
        callback_data: Dict[str, Any],
    ) -> PaymentResult:
        payment_id = (
            callback_data.get('id') or transaction.reference_id
        )
        order_id = callback_data.get('order_id') or (
            transaction.order.order_number if transaction.order else ''
        )
        status = callback_data.get('status')

        if not payment_id:
            return PaymentResult(
                success=False, error_message='شناسه پرداخت آی‌دی‌پی یافت نشد.',
                error_code='missing_id',
            )
        # status=1 → پرداخت انجام شده (باید وریفای شود)؛ 2→لغو؛ 3→ناموفق؛ …
        if str(status) == '2':
            return PaymentResult(
                success=False, error_message='پرداخت توسط کاربر لغو شد.',
                error_code='cancelled',
            )

        try:
            resp = _requests.post(
                f'{self.BASE}/payment/verify',
                json={'id': str(payment_id), 'order_id': str(order_id)},
                headers=self._headers(), timeout=HTTP_TIMEOUT,
            )
        except _requests.RequestException as e:
            return PaymentResult(
                success=False, error_message=f'عدم دسترسی به آی‌دی‌پی هنگام تأیید: {e}',
                error_code='network_error',
            )

        ok, data = _json(resp)
        v_status = data.get('status') if ok else None
        # 100 = وریفای موفق، 101 = قبلاً وریفای شده
        if v_status in (100, 101):
            return PaymentResult(
                success=True,
                transaction_id=str(data.get('id', payment_id)),
                raw_response=data,   # شامل track_id, amount, card_no, date
            )
        if str(v_status) in ('1',):
            return PaymentResult(
                success=False,
                error_message='پرداخت انجام شده اما تأیید نهایی نشد — با پشتیبانی تماس بگیرید.',
                error_code='verify_pending', raw_response=data,
            )
        return PaymentResult(
            success=False,
            error_message=f"تأیید پرداخت آی‌دی‌پی ناموفق بود (status={v_status}).",
            error_code=f'idpay_status_{v_status}',
            raw_response=data,
        )


# ==================== DigiPay (UPG) ====================

class DigiPayGateway(PaymentGatewayInterface):
    """
    دیجی‌پی — مستندات رسمی درگاه پرداخت یکپارچه (UPG):
      oauth:   POST {base}/oauth/token   (Basic client_id:client_secret + grant_type=password)
      ticket:  POST {base}/tickets/business?type=11   (Agent: WEB, Digipay-Version)
      redirect: redirectUrl از پاسخ تیکت (کیف پول/اعتباری/IPG انتخاب کاربر)
      verify:  POST {base}/purchases/verify?tracingCode={code}&type={type}
    کال‌بک: POST {amount, providerId, trackingCode, result: SUCCESS|FAILURE, type}
    """
    gateway_name = PaymentGateway.DIGIPAY.value
    required_settings = (
        ('digipay_client_id', 'DIGIPAY_CLIENT_ID'),
        ('digipay_client_secret', 'DIGIPAY_CLIENT_SECRET'),
        ('digipay_username', 'DIGIPAY_USERNAME'),
        ('digipay_password', 'DIGIPAY_PASSWORD'),
    )

    LIVE_BASE = 'https://api.mydigipay.com/digipay/api'
    SANDBOX_BASE = 'https://uat.mydigipay.info/digipay/api'

    # کش توکن در حافظه فرآیند
    _token_cache: Dict[str, Tuple[str, float]] = {}

    def _base(self) -> str:
        sandbox = str(payment_setting(
            'digipay_sandbox', 'DIGIPAY_SANDBOX', False
        )).lower() in ('1', 'true', 'yes', 'on')
        return self.SANDBOX_BASE if sandbox else self.LIVE_BASE

    def _get_token(self) -> Optional[str]:
        client_id = str(payment_setting('digipay_client_id', 'DIGIPAY_CLIENT_ID', '')).strip()
        client_secret = str(payment_setting('digipay_client_secret', 'DIGIPAY_CLIENT_SECRET', '')).strip()
        username = str(payment_setting('digipay_username', 'DIGIPAY_USERNAME', '')).strip()
        password = str(payment_setting('digipay_password', 'DIGIPAY_PASSWORD', '')).strip()
        if not all([client_id, client_secret, username, password]):
            return None

        cached = self._token_cache.get(self._base())
        if cached and cached[1] > time.time() + 60:
            return cached[0]

        basic = base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode()
        try:
            resp = _requests.post(
                f'{self._base()}/oauth/token',
                headers={'Authorization': f'Basic {basic}'},
                data={
                    'grant_type': 'password',
                    'username': username,
                    'password': password,
                },
                timeout=HTTP_TIMEOUT,
            )
        except _requests.RequestException:
            return None
        if resp.status_code != 200:
            return None
        ok, data = _json(resp)
        token = data.get('access_token') if ok else None
        if token:
            expires = int(data.get('expires_in', 3000) or 3000)
            self._token_cache[self._base()] = (token, time.time() + expires)
            return token
        return None

    def create_payment(self, order: Order, callback_url: str) -> PaymentResult:
        token = self._get_token()
        if not token:
            return PaymentResult(
                success=False,
                error_message='درگاه دیجی‌پی پیکربندی نشده یا احراز هویت ناموفق بود.',
                error_code='config_or_auth_failed',
            )

        phone = order.recipient_phone or (order.user.phone if order.user else '') or ''
        payload = {
            'cellNumber': phone,
            'amount': amount_in_rial(order),          # ریال
            'providerId': order.order_number,         # شناسه یکتای سفارش نزد پذیرنده
            'callbackUrl': callback_url,
        }
        headers = {
            'Authorization': f'Bearer {token}',
            'Agent': 'WEB',
            'Digipay-Version': '2022-02-02',
            'Content-Type': 'application/json; charset=UTF-8',
        }
        try:
            resp = _requests.post(
                f'{self._base()}/tickets/business?type=11',
                json=payload, headers=headers, timeout=HTTP_TIMEOUT,
            )
        except _requests.RequestException as e:
            return PaymentResult(
                success=False, error_message=f'عدم دسترسی به دیجی‌پی: {e}',
                error_code='network_error',
            )

        ok, data = _json(resp)
        result = (data.get('result') or {}) if ok else {}
        if resp.status_code == 200 and result.get('status') == 0 and data.get('redirectUrl'):
            ticket = str(data.get('ticket', ''))
            return PaymentResult(
                success=True,
                transaction_id=ticket,
                redirect_url=str(data['redirectUrl']),
                raw_response=data,
            )
        return PaymentResult(
            success=False,
            error_message=f"دیجی‌پی: {result.get('message') or f'خطای HTTP {resp.status_code}'}",
            error_code=f'digipay_{result.get("status", resp.status_code)}',
            raw_response={'http': resp.status_code, 'body': resp.text[:500]},
        )

    def verify_payment(
        self,
        transaction: PaymentTransaction,
        callback_data: Dict[str, Any],
    ) -> PaymentResult:
        # دیجی‌پی نتیجه را POST می‌کند: result / trackingCode / providerId / amount / type
        result = str(callback_data.get('result', '')).upper()
        tracking_code = str(callback_data.get('trackingCode', '') or '')
        provider_id = str(callback_data.get('providerId', '') or '')
        ticket_type = str(callback_data.get('type', '') or '')
        amount = callback_data.get('amount')

        if result == 'FAILURE':
            return PaymentResult(
                success=False, error_message='پرداخت در دیجی‌پی ناموفق بود.',
                error_code='failed', raw_response=callback_data,
            )
        if result != 'SUCCESS':
            return PaymentResult(
                success=False,
                error_message='پاسخ نامعتبر از دیجی‌پی.',
                error_code='invalid_response', raw_response=callback_data,
            )

        # تطبیق سفارش (توصیه رسمی مستندات: قبل از verify مقدار amount و providerId را چک کنید)
        order = transaction.order
        if provider_id and order and provider_id != order.order_number:
            return PaymentResult(
                success=False,
                error_message='شناسه پرداخت دیجی‌پی با سفارش مطابقت ندارد.',
                error_code='provider_mismatch', raw_response=callback_data,
            )
        if amount and order:
            try:
                expected = amount_in_rial(order)
                if int(amount) != expected:
                    return PaymentResult(
                        success=False,
                        error_message='مبلغ پرداخت‌شده با مبلغ سفارش مطابقت ندارد.',
                        error_code='amount_mismatch', raw_response=callback_data,
                    )
            except (ValueError, TypeError):
                pass

        token = self._get_token()
        if not token:
            return PaymentResult(
                success=False,
                error_message='احراز هویت دیجی‌پی هنگام تأیید ناموفق بود.',
                error_code='config_or_auth_failed',
            )
        try:
            resp = _requests.post(
                f'{self._base()}/purchases/verify'
                f'?tracingCode={tracking_code}&type={ticket_type}',
                json={
                    'trackingCode': tracking_code,
                    'providerId': provider_id or (order.order_number if order else ''),
                },
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json; charset=UTF-8',
                },
                timeout=HTTP_TIMEOUT,
            )
        except _requests.RequestException as e:
            return PaymentResult(
                success=False, error_message=f'عدم دسترسی به دیجی‌پی هنگام تأیید: {e}',
                error_code='network_error',
            )

        ok, data = _json(resp)
        body_result = (data.get('result') or {}) if ok else {}
        if resp.status_code == 200 and body_result.get('status') == 0:
            return PaymentResult(
                success=True,
                transaction_id=str(tracking_code),
                raw_response=data,   # شامل trackingCode, amount, type, orderId
            )
        return PaymentResult(
            success=False,
            error_message=f"دیجی‌پی: تأیید پرداخت ناموفق — {body_result.get('message') or resp.status_code}",
            error_code=f'digipay_{body_result.get("status", resp.status_code)}',
            raw_response={'http': resp.status_code, 'body': resp.text[:500]},
        )


# ==================== SnappPay (اقساطی) ====================

class SnappPayGateway(PaymentGatewayInterface):
    """
    اسنپ‌پی — سرویس خرید اقساطی (BNPL):
      oauth:   POST {base}/api/online/v1/oauth/token (Basic + grant_type=password)
      token:   POST {base}/api/online/payment/v1/token → paymentPageUrl
      verify:  POST {base}/api/online/payment/v1/verify  {paymentToken}
      settle:  POST {base}/api/online/payment/v1/settle  (بعد از تأیید)
    کال‌بک: POST {status, paymentToken, ...}
    مستندات کامل فقط در قالب PDF محرمانه به پذیرنده ارسال می‌شود؛
    مسیرها/فیلدها بر اساس پکیج‌های رسمی community قابل تنظیم از پنل است.
    """
    gateway_name = PaymentGateway.SNAPPPAY.value
    required_settings = (
        ('snapppay_client_id', 'SNAPPPAY_CLIENT_ID'),
        ('snapppay_client_secret', 'SNAPPPAY_CLIENT_SECRET'),
        ('snapppay_username', 'SNAPPPAY_USERNAME'),
        ('snapppay_password', 'SNAPPPAY_PASSWORD'),
    )

    LIVE_BASE = 'https://payment.snapppay.ir'
    SANDBOX_BASE = 'https://sandbox.snappymarket.ir'

    _token_cache: Dict[str, Tuple[str, float]] = {}

    def _base(self) -> str:
        sandbox = str(payment_setting(
            'snapppay_sandbox', 'SNAPPPAY_SANDBOX', False
        )).lower() in ('1', 'true', 'yes', 'on')
        return self.SANDBOX_BASE if sandbox else self.LIVE_BASE

    def _get_token(self) -> Optional[str]:
        client_id = str(payment_setting('snapppay_client_id', 'SNAPPPAY_CLIENT_ID', '')).strip()
        client_secret = str(payment_setting('snapppay_client_secret', 'SNAPPPAY_CLIENT_SECRET', '')).strip()
        username = str(payment_setting('snapppay_username', 'SNAPPPAY_USERNAME', '')).strip()
        password = str(payment_setting('snapppay_password', 'SNAPPPAY_PASSWORD', '')).strip()
        if not all([client_id, client_secret, username, password]):
            return None

        cached = self._token_cache.get(self._base())
        if cached and cached[1] > time.time() + 60:
            return cached[0]

        basic = base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode()
        try:
            resp = _requests.post(
                f'{self._base()}/api/online/v1/oauth/token',
                headers={'Authorization': f'Basic {basic}'},
                data={
                    'grant_type': 'password',
                    'username': username,
                    'password': password,
                },
                timeout=HTTP_TIMEOUT,
            )
        except _requests.RequestException:
            return None
        if resp.status_code not in (200, 201):
            return None
        ok, data = _json(resp)
        token = (data.get('access_token') or data.get('token')) if ok else None
        if token:
            expires = int(data.get('expires_in', 3000) or 3000)
            self._token_cache[self._base()] = (token, time.time() + expires)
            return token
        return None

    def create_payment(self, order: Order, callback_url: str) -> PaymentResult:
        token = self._get_token()
        if not token:
            return PaymentResult(
                success=False,
                error_message='درگاه اسنپ‌پی پیکربندی نشده یا احراز هویت ناموفق بود.',
                error_code='config_or_auth_failed',
            )

        phone = order.recipient_phone or (order.user.phone if order.user else '') or ''
        address = '، '.join(
            str(x or '') for x in (order.province, order.city, order.address)
        ).strip('، ')

        payload = {
            'amount': amount_in_rial(order),          # ریال
            'telephone': phone,
            'postalAddress': address or 'بدون آدرس',
            'invoiceNumber': order.order_number,
            'returnUrl': callback_url,
        }
        if order.user and order.user.email:
            payload['email'] = order.user.email

        try:
            resp = _requests.post(
                f'{self._base()}/api/online/payment/v1/token',
                json=payload,
                headers={'Authorization': f'Bearer {token}'},
                timeout=HTTP_TIMEOUT,
            )
        except _requests.RequestException as e:
            return PaymentResult(
                success=False, error_message=f'عدم دسترسی به اسنپ‌پی: {e}',
                error_code='network_error',
            )

        ok, data = _json(resp)
        if resp.status_code in (200, 201) and data.get('paymentToken'):
            return PaymentResult(
                success=True,
                transaction_id=str(data['paymentToken']),
                redirect_url=str(data.get('paymentPageUrl', '')),
                raw_response=data,
            )
        return PaymentResult(
            success=False,
            error_message=f"اسنپ‌پی: {data.get('message') or f'خطای HTTP {resp.status_code}'}",
            error_code=f'snapppay_{resp.status_code}',
            raw_response={'http': resp.status_code, 'body': resp.text[:500]},
        )

    def verify_payment(
        self,
        transaction: PaymentTransaction,
        callback_data: Dict[str, Any],
    ) -> PaymentResult:
        status = str(callback_data.get('status', '')).upper()
        payment_token = str(
            callback_data.get('paymentToken') or transaction.reference_id or ''
        )

        if status in ('CANCELLED', 'CANCELED', 'FAILED', 'REJECTED'):
            return PaymentResult(
                success=False, error_message='پرداخت اسنپ‌پی لغو یا ناموفق بود.',
                error_code='cancelled', raw_response=callback_data,
            )
        if not payment_token:
            return PaymentResult(
                success=False, error_message='توکن پرداخت اسنپ‌پی یافت نشد.',
                error_code='missing_token',
            )

        token = self._get_token()
        if not token:
            return PaymentResult(
                success=False,
                error_message='احراز هویت اسنپ‌پی هنگام تأیید ناموفق بود.',
                error_code='config_or_auth_failed',
            )
        try:
            resp = _requests.post(
                f'{self._base()}/api/online/payment/v1/verify',
                json={'paymentToken': payment_token},
                headers={'Authorization': f'Bearer {token}'},
                timeout=HTTP_TIMEOUT,
            )
        except _requests.RequestException as e:
            return PaymentResult(
                success=False, error_message=f'عدم دسترسی به اسنپ‌پی هنگام تأیید: {e}',
                error_code='network_error',
            )

        ok, data = _json(resp)
        v_status = str((data.get('status') or '') if ok else '').upper()
        if resp.status_code == 200 and v_status in ('DONE', 'SUCCESSFUL', 'SUCCESS', 'OK', 'VERIFIED'):
            # تسویه نهایی (settle) — بهترین تلاش؛ نتیجه‌اش جریان را نمی‌شکند
            try:
                _requests.post(
                    f'{self._base()}/api/online/payment/v1/settle',
                    json={'paymentToken': payment_token},
                    headers={'Authorization': f'Bearer {token}'},
                    timeout=HTTP_TIMEOUT,
                )
            except _requests.RequestException:
                pass
            return PaymentResult(
                success=True,
                transaction_id=payment_token,
                raw_response=data,
            )
        return PaymentResult(
            success=False,
            error_message=f"اسنپ‌پی: تأیید پرداخت ناموفق (status={v_status or resp.status_code}).",
            error_code=f'snapppay_{v_status or resp.status_code}',
            raw_response={'http': resp.status_code, 'body': resp.text[:500]},
        )


# ==================== بانک سپه (الگوی شاپرک) ====================

class SepahGateway(PaymentGatewayInterface):
    """
    بانک سپه — درگاه مستقل IPG ندارد و پذیرندگی‌اش از طریق شرکت‌های PSP
    همکار (وب‌سرویس‌های شاپرک) صادر می‌شود. این درایور با «الگوی استاندارد
    شاپرک (سپهر)» پیاده شده که روان‌ترین مسیر پذیرندگی سپه است:

      gettoken: POST {api_base}/V1/PeymentApi/GetToken
                form {terminalID, Amount(ریال), callbackURL, invoiceID, CellNumber}
                → JSON {Status: '0', Accesstoken}
      pay:      POST فرم به {pay_base} با {TerminalID, token, getMethod:1}
      callback: POST {State:'OK', ResNum(=invoiceID), RefNum, TraceNo, ...}
      verify:   POST {api_base}/V1/PeymentApi/Verify {terminalID, refnum}

    آدرس‌ها از پنل قابل تغییرند (برای PSP دیگری که قرارداد سپه را گرفته).
    """
    gateway_name = PaymentGateway.SEPASH.value
    required_settings = (
        ('sepah_terminal_id', 'SEPASH_TERMINAL_ID'),
    )

    DEFAULT_API_BASE = 'https://sepehr.shaparak.ir:8081'
    DEFAULT_PAY_BASE = 'https://sepehr.shaparak.ir:8080'

    def _api_base(self) -> str:
        return str(payment_setting('sepah_api_base', 'SEPASH_API_BASE', self.DEFAULT_API_BASE)).rstrip('/')

    def _pay_base(self) -> str:
        return str(payment_setting('sepah_pay_base', 'SEPASH_PAY_BASE', self.DEFAULT_PAY_BASE)).rstrip('/')

    def _terminal_id(self) -> str:
        return str(payment_setting('sepah_terminal_id', 'SEPASH_TERMINAL_ID', '')).strip()

    def create_payment(self, order: Order, callback_url: str) -> PaymentResult:
        terminal_id = self._terminal_id()
        if not terminal_id:
            return PaymentResult(
                success=False,
                error_message='درگاه بانک سپه پیکربندی نشده است (شماره پایانه وجود ندارد).',
                error_code='config_missing',
            )

        rial = amount_in_rial(order)
        if rial < 1000:  # حداقل مبلغ تراکنش شاپرک
            return PaymentResult(
                success=False,
                error_message='مبلغ تراکنش کمتر از حداقل مجاز درگاه (۱٬۰۰۰ ریال) است.',
                error_code='amount_too_low',
            )

        phone = order.recipient_phone or (order.user.phone if order.user else '') or ''
        payload = {
            'terminalID': terminal_id,
            'Amount': rial,
            'callbackURL': callback_url,
            'invoiceID': order.order_number,
        }
        if phone:
            payload['CellNumber'] = phone

        try:
            resp = _requests.post(
                f'{self._api_base()}/V1/PeymentApi/GetToken',
                data=payload, timeout=HTTP_TIMEOUT,
            )
        except _requests.RequestException as e:
            return PaymentResult(
                success=False, error_message=f'عدم دسترسی به درگاه سپه: {e}',
                error_code='network_error',
            )

        ok, data = _json(resp)
        if not ok:
            # برخی استقرارها به‌جای JSON، متن ساده برمی‌گردانند
            text = resp.text.strip()
            if text.startswith('{'):
                import json as _jsonlib
                try:
                    data = _jsonlib.loads(text)
                except ValueError:
                    data = {}

        status = str(data.get('Status', data.get('status', '')))
        access_token = data.get('Accesstoken') or data.get('accessToken')

        if status == '0' and access_token:
            # شاپرک نیاز به هدایت کاربر با POST فرم دارد (نه ریدایرکت ساده)
            return PaymentResult(
                success=True,
                transaction_id=str(access_token),
                redirect_url=self._pay_base(),
                redirect_method='form',
                form_url=self._pay_base(),
                form_fields={
                    'TerminalID': terminal_id,
                    'token': str(access_token),
                    'getMethod': '1',
                },
                raw_response={'Status': status, 'invoiceID': order.order_number},
            )
        return PaymentResult(
            success=False,
            error_message=f'درگاه سپه: صدور توکن ناموفق بود (Status={status or resp.status_code}).',
            error_code=f'sepah_token_{status or resp.status_code}',
            raw_response={'http': resp.status_code, 'body': resp.text[:500]},
        )

    def verify_payment(
        self,
        transaction: PaymentTransaction,
        callback_data: Dict[str, Any],
    ) -> PaymentResult:
        # کال‌بک شاپرک: State / ResNum / RefNum / TraceNo
        state = str(callback_data.get('State', callback_data.get('state', ''))).upper()
        ref_num = str(callback_data.get('RefNum') or callback_data.get('refnum') or '')
        res_num = str(callback_data.get('ResNum') or callback_data.get('resnum') or '')
        trace_no = str(callback_data.get('TraceNo') or callback_data.get('traceno') or '')

        if not ref_num:
            if 'CANCEL' in state:
                return PaymentResult(
                    success=False, error_message='پرداخت توسط کاربر لغو شد.',
                    error_code='cancelled', raw_response=callback_data,
                )
            if state and state != 'OK':
                return PaymentResult(
                    success=False,
                    error_message=f'پرداخت درگاه سپه ناموفق بود (State={state}).',
                    error_code=f'sepah_state_{state}',
                    raw_response=callback_data,
                )
            return PaymentResult(
                success=False, error_message='شماره پیگیری (RefNum) از درگاه سپه دریافت نشد.',
                error_code='missing_refnum', raw_response=callback_data,
            )
        if state and state != 'OK':
            # رشته State استاندارد: OK / Canceled By User / ...
            if 'CANCEL' in state:
                return PaymentResult(
                    success=False, error_message='پرداخت توسط کاربر لغو شد.',
                    error_code='cancelled', raw_response=callback_data,
                )
            return PaymentResult(
                success=False,
                error_message=f'پرداخت درگاه سپه ناموفق بود (State={state}).',
                error_code=f'sepah_state_{state}',
                raw_response=callback_data,
            )

        # تطبیق سفارش
        order = transaction.order
        if res_num and order and res_num != order.order_number:
            return PaymentResult(
                success=False,
                error_message='شناسه فاکتور درگاه سپه با سفارش مطابقت ندارد.',
                error_code='invoice_mismatch', raw_response=callback_data,
            )

        try:
            resp = _requests.post(
                f'{self._api_base()}/V1/PeymentApi/Verify',
                json={'terminalID': self._terminal_id(), 'refnum': ref_num},
                timeout=HTTP_TIMEOUT,
            )
        except _requests.RequestException as e:
            return PaymentResult(
                success=False, error_message=f'عدم دسترسی به درگاه سپه هنگام تأیید: {e}',
                error_code='network_error',
            )

        ok, data = _json(resp)
        v_status = str(data.get('Status', data.get('status', '')))
        # Status=0 و/یا Success برابر true/1 یعنی تأیید شده
        success_flag = str(data.get('Success', '')).lower() in ('1', 'true', 'yes')
        verified_amount = data.get('Amount') or data.get('amount')

        if v_status == '0' or success_flag:
            # بررسی مبلغ (اگر درگاه برگرداند)
            try:
                if verified_amount and order:
                    if int(verified_amount) != amount_in_rial(order):
                        return PaymentResult(
                            success=False,
                            error_message='مبلغ تأییدشده درگاه سپه با مبلغ سفارش مطابقت ندارد.',
                            error_code='amount_mismatch', raw_response=data,
                        )
            except (ValueError, TypeError):
                pass
            return PaymentResult(
                success=True,
                transaction_id=ref_num,
                raw_response={'RefNum': ref_num, 'TraceNo': trace_no,
                              'Status': v_status, 'Amount': verified_amount},
            )
        return PaymentResult(
            success=False,
            error_message=f'درگاه سپه: تأیید تراکنش ناموفق بود (Status={v_status or resp.status_code}).',
            error_code=f'sepah_verify_{v_status or resp.status_code}',
            raw_response={'http': resp.status_code, 'body': resp.text[:500]},
        )


# ==================== Gateway factory ====================

_GATEWAYS: Dict[str, type] = {
    PaymentGateway.MOCK.value: MockGateway,
    PaymentGateway.ZARINPAL.value: ZarinpalGateway,
    PaymentGateway.IDPAY.value: IDPayGateway,
    PaymentGateway.DIGIPAY.value: DigiPayGateway,
    PaymentGateway.SNAPPPAY.value: SnappPayGateway,
    PaymentGateway.SEPASH.value: SepahGateway,
    # سازگاری با داده‌های قدیمی
    PaymentGateway.MANUAL.value: MockGateway,
    PaymentGateway.NEXTPAY.value: MockGateway,
}


def get_gateway(name: str) -> PaymentGatewayInterface:
    """
    Get a payment gateway instance by name.

    Falls back to MockGateway if name is unknown.
    """
    cls = _GATEWAYS.get(name, MockGateway)
    return cls()


def list_available_gateways() -> list:
    """
    درگاه‌های فعال و پیکربندی‌شده برای نمایش در صفحه پرداخت.

    خروجی: لیست دیکشنری {id, label, description, badge} —
    فیلتر بر اساس ENABLED_PAYMENT_GATEWAYS و سپس is_configured().
    mock همیشه در دسترس است (توسعه/دمو).
    """
    from app.constants import GATEWAY_CATALOG

    enabled = current_app.config.get('ENABLED_PAYMENT_GATEWAYS', None)
    if enabled is None:
        enabled = [PaymentGateway.MOCK.value]
    if isinstance(enabled, str):
        enabled = [g.strip() for g in enabled.split(',') if g.strip()]

    result = []
    for name in enabled:
        cls = _GATEWAYS.get(name)
        catalog = GATEWAY_CATALOG.get(name, {})
        if cls is None or not catalog:
            continue
        # mock را بدون بررسی پیکربندی نشان بده؛ بقیه فقط اگر کلید دارند
        if name != PaymentGateway.MOCK.value and not cls().is_configured():
            continue
        result.append({
            'id': name,
            'label': catalog.get('label', name),
            'description': catalog.get('description', ''),
            'badge': catalog.get('badge', name),
        })
    if not result:  # هیچ‌چیز پیکربندی نیست → mock برای جریان تست
        result = [{
            'id': PaymentGateway.MOCK.value,
            'label': GATEWAY_CATALOG[PaymentGateway.MOCK.value]['label'],
            'description': GATEWAY_CATALOG[PaymentGateway.MOCK.value]['description'],
            'badge': 'تست',
        }]
    return result
