"""
Payment Gateway Service — driver pattern.

Defines a base interface and provides:
- MockGateway: for development, no external account needed.
- ZarinpalGateway / IDPayGateway: stubs ready to be filled in.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from decimal import Decimal
from flask import current_app, url_for
import uuid

from app.models import Order, PaymentTransaction
from app.constants import PaymentGateway, TransactionStatus
from app.extensions import db


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
    ):
        self.success = success
        self.transaction_id = transaction_id
        self.redirect_url = redirect_url
        self.error_message = error_message
        self.error_code = error_code
        self.raw_response = raw_response or {}

    def to_dict(self) -> Dict:
        return {
            'success': self.success,
            'transaction_id': self.transaction_id,
            'redirect_url': self.redirect_url,
            'error_message': self.error_message,
            'error_code': self.error_code,
        }


class PaymentGatewayInterface(ABC):
    """Abstract interface for payment gateways."""

    gateway_name: str = 'abstract'

    @abstractmethod
    def create_payment(
        self,
        order: Order,
        callback_url: str,
    ) -> PaymentResult:
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


class MockGateway(PaymentGatewayInterface):
    """
    In-process mock gateway.

    For development & demo. Simulates a redirect flow:
    - create_payment returns a /payment/mock/<order_number> URL
    - that URL shows a page that lets the user 'Pay' or 'Cancel'
    - on Pay, the transaction is marked SUCCESS
    """
    gateway_name = 'mock'

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


class ZarinpalGateway(PaymentGatewayInterface):
    """
    Zarinpal gateway stub.

    To activate:
    1. Set ZARINPAL_MERCHANT_ID in config
    2. pip install requests
    3. Replace the `requests.post(...)` calls below
    """
    gateway_name = PaymentGateway.ZARINPAL.value

    SANDBOX_REQUEST_URL = 'https://sandbox.zarinpal.com/pg/services/Webgate/wsdl'
    REQUEST_URL = 'https://api.zarinpal.com/pg/v4/payment/request.json'
    VERIFY_URL = 'https://api.zarinpal.com/pg/v4/payment/verify.json'
    START_URL = 'https://www.zarinpal.com/pg/StartPay/'
    SANDBOX_START_URL = 'https://sandbox.zarinpal.com/pg/StartPay/'

    def create_payment(self, order: Order, callback_url: str) -> PaymentResult:
        merchant_id = current_app.config.get('ZARINPAL_MERCHANT_ID')
        if not merchant_id:
            return PaymentResult(
                success=False,
                error_message='درگاه زرین‌پال پیکربندی نشده است.',
                error_code='config_missing',
            )

        # TODO: implement real Zarinpal call
        # import requests
        # resp = requests.post(self.REQUEST_URL, json={...})
        # data = resp.json()
        # if data['data']['code'] == 100:
        #     return PaymentResult(success=True, transaction_id=str(data['data']['authority']),
        #                          redirect_url=self.START_URL + str(data['data']['authority']))
        return PaymentResult(
            success=False,
            error_message='درگاه زرین‌پال هنوز فعال نشده است. (پیاده‌سازی ناقص)',
            error_code='not_implemented',
        )

    def verify_payment(
        self,
        transaction: PaymentTransaction,
        callback_data: Dict[str, Any],
    ) -> PaymentResult:
        # TODO: implement real verification
        return PaymentResult(
            success=False,
            error_message='تأیید پرداخت زرین‌پال هنوز پیاده‌سازی نشده است.',
            error_code='not_implemented',
        )


class IDPayGateway(PaymentGatewayInterface):
    """IDPay gateway stub. Same structure as Zarinpal."""
    gateway_name = PaymentGateway.IDPAY.value
    REQUEST_URL = 'https://api.idpay.ir/v1.1/payment'
    VERIFY_URL = 'https://api.idpay.ir/v1.1/payment/verify'

    def create_payment(self, order: Order, callback_url: str) -> PaymentResult:
        return PaymentResult(
            success=False,
            error_message='درگاه آی‌دی‌پی هنوز فعال نشده است.',
            error_code='not_implemented',
        )

    def verify_payment(
        self,
        transaction: PaymentTransaction,
        callback_data: Dict[str, Any],
    ) -> PaymentResult:
        return PaymentResult(
            success=False,
            error_message='تأیید پرداخت آی‌دی‌پی هنوز پیاده‌سازی نشده است.',
            error_code='not_implemented',
        )


# ==================== Gateway factory ====================

_GATEWAYS: Dict[str, type] = {
    PaymentGateway.MANUAL.value: MockGateway,
    PaymentGateway.ZARINPAL.value: ZarinpalGateway,
    PaymentGateway.IDPAY.value: IDPayGateway,
    PaymentGateway.NEXTPAY.value: MockGateway,  # placeholder
}


def get_gateway(name: str) -> PaymentGatewayInterface:
    """
    Get a payment gateway instance by name.

    Falls back to MockGateway if name is unknown.
    """
    cls = _GATEWAYS.get(name, MockGateway)
    return cls()


def list_available_gateways() -> list:
    """List all configured gateway names."""
    enabled = current_app.config.get('ENABLED_PAYMENT_GATEWAYS', None)
    if enabled is None:
        # Default: only mock
        return [PaymentGateway.MANUAL.value]
    if isinstance(enabled, str):
        return [g.strip() for g in enabled.split(',') if g.strip()]
    return list(enabled)
