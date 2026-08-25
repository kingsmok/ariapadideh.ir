"""
تست جامع درگاه‌های پرداخت — زرین‌پال، آی‌دی‌پی، دیجی‌پی، اسنپ‌پی، بانک سپه (شاپرک) و Mock.

تمام تماس‌های HTTP با monkeypatch شبیه‌سازی می‌شوند؛ تست‌ها شامل:
- ساخت پرداخت (create_payment) هر درگاه با پاسخ واقعی‌نما
- تأیید (verify_payment) موفق/ناموفق/لغو
- جریان کامل checkout → callback برای زرین‌پال و سپه (هدایت فرمی)
"""
import json
import sys
import os
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db  # noqa: E402
from app.models import User, Product, Category, Order, PaymentTransaction, Setting  # noqa: E402
from app.constants import TransactionStatus, OrderStatus, PaymentStatus  # noqa: E402
from app.services import payment_gateway as pg  # noqa: E402


# ==================== Fixtures ====================

@pytest.fixture()
def app(tmp_path):
    """اپ تست با SQLite در حافظه."""
    os.environ['DATABASE_URL'] = 'sqlite://'
    os.environ['CACHE_TYPE'] = 'SimpleCache'
    os.environ['SESSION_TYPE'] = 'filesystem'
    os.environ['ENABLED_PAYMENT_GATEWAYS'] = 'mock,zarinpal,idpay,digipay,snapppay,sepah'
    os.environ['PAYMENT_CURRENCY_UNIT'] = 'toman'
    app = create_app('testing')
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SQLALCHEMY_DATABASE_URI='sqlite://',
        CACHE_TYPE='SimpleCache',
        ENABLED_PAYMENT_GATEWAYS=['mock', 'zarinpal', 'idpay', 'digipay', 'snapppay', 'sepah'],
        PAYMENT_CURRENCY_UNIT='toman',
        SERVER_NAME='localhost',
    )
    with app.app_context():
        db.create_all()
        _seed_minimal()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def _seed_minimal():
    """کاربر خریدار + محصول فعال."""
    buyer = User(email='buyer@example.com', first_name='خریدار', last_name='تست',
                 phone='09121112233', is_active=True, is_verified=True)
    buyer.set_password('Passw0rd!')
    db.session.add(buyer)
    cat = Category(title='تست', slug='test-cat')
    db.session.add(cat)
    db.session.flush()
    product = Product(
        title='محصول تست', slug='test-product', price=100000,
        stock_quantity=10, stock_status='in_stock', is_active=True,
    )
    product.categories.append(cat)
    db.session.add(product)
    db.session.commit()


def _set_setting(group, key, value, stype='string'):
    Setting.query.filter_by(group=group, key=key).delete()
    db.session.add(Setting(group=group, key=key, value=value, type=stype, is_public=False))
    db.session.commit()


def _make_order(app):
    """ساخت یک سفارش پرداخت‌نشده با تراکنش pending."""
    product = Product.query.first()
    buyer = User.query.filter_by(email='buyer@example.com').first()
    order = Order(
        order_number='ORD-TEST-0001', user_id=buyer.id, status='pending',
        subtotal=100000, total_amount=100000, payment_method='online',
        payment_status='unpaid', recipient_name='خریدار تست',
        recipient_phone='09121112233', province='تهران', city='تهران',
        postal_code='1234567890', address='خیابان تست',
    )
    db.session.add(order)
    db.session.flush()
    txn = PaymentTransaction(
        order_id=order.id, amount=100000, payment_method='online',
        gateway='mock', status='pending',
    )
    db.session.add(txn)
    db.session.commit()
    return order, txn


def _mock_response(json_data=None, status_code=200, text=''):
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text or (json.dumps(json_data) if json_data is not None else '')
    resp.json.return_value = json_data if json_data is not None else {}
    return resp


# ==================== ZarinPal ====================

class TestZarinpal:

    def test_create_payment_success(self, app):
        _set_setting('payment', 'zarinpal_merchant_id', 'a8aaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee')  # 36 chars
        order, _ = _make_order(app)
        gateway = pg.ZarinpalGateway()
        with patch.object(pg._requests, 'post',
                         return_value=_mock_response({'data': {'code': 100, 'authority': 'A0001'}})):
            result = gateway.create_payment(order, 'https://cb')
        assert result.success
        assert result.transaction_id == 'A0001'
        assert '/pg/StartPay/A0001' in result.redirect_url

    def test_create_payment_missing_merchant(self, app):
        order, _ = _make_order(app)
        result = pg.ZarinpalGateway().create_payment(order, 'https://cb')
        assert not result.success
        assert result.error_code == 'config_missing'

    def test_create_payment_error_code(self, app):
        _set_setting('payment', 'zarinpal_merchant_id', 'm' * 36)
        order, _ = _make_order(app)
        gateway = pg.ZarinpalGateway()
        with patch.object(pg._requests, 'post',
                         return_value=_mock_response({'data': {'code': -50}, 'errors': {'code': -50}})):
            result = gateway.create_payment(order, 'https://cb')
        assert not result.success
        assert '-50' in result.error_code

    def test_verify_success(self, app):
        _set_setting('payment', 'zarinpal_merchant_id', 'm' * 36)
        order, txn = _make_order(app)
        txn.gateway = 'zarinpal'
        txn.reference_id = 'A0001'
        gateway = pg.ZarinpalGateway()
        with patch.object(pg._requests, 'post',
                         return_value=_mock_response({'data': {'code': 100, 'ref_id': 12345}})):
            result = gateway.verify_payment(txn, {'Authority': 'A0001', 'Status': 'OK'})
        assert result.success
        assert result.raw_response['ref_id'] == '12345'

    def test_verify_already_verified_101(self, app):
        _set_setting('payment', 'zarinpal_merchant_id', 'm' * 36)
        order, txn = _make_order(app)
        with patch.object(pg._requests, 'post',
                         return_value=_mock_response({'data': {'code': 101}})):
            result = pg.ZarinpalGateway().verify_payment(txn, {'Authority': 'A1', 'Status': 'OK'})
        assert result.success

    def test_verify_user_cancelled(self, app):
        _set_setting('payment', 'zarinpal_merchant_id', 'm' * 36)
        order, txn = _make_order(app)
        result = pg.ZarinpalGateway().verify_payment(txn, {'Authority': 'A1', 'Status': 'NOK'})
        assert not result.success
        assert result.error_code == 'cancelled'

    def test_amount_toman_converted_to_rial(self, app):
        _set_setting('payment', 'zarinpal_merchant_id', 'm' * 36)
        order, _ = _make_order(app)
        gateway = pg.ZarinpalGateway()
        captured = {}

        def fake_post(url, json=None, timeout=None):
            captured.update(json or {})
            return _mock_response({'data': {'code': 100, 'authority': 'X'}})

        with patch.object(pg._requests, 'post', side_effect=fake_post):
            gateway.create_payment(order, 'https://cb')
        assert captured['amount'] == 1000000  # 100,000 toman × 10


# ==================== IDPay ====================

class TestIDPay:

    def test_create_payment_success(self, app):
        _set_setting('payment', 'idpay_api_key', 'test-key')
        order, _ = _make_order(app)
        gateway = pg.IDPayGateway()
        with patch.object(pg._requests, 'post',
                         return_value=_mock_response({'id': 'pid1', 'link': 'https://idpay.ir/p/x'})):
            result = gateway.create_payment(order, 'https://cb')
        assert result.success
        assert result.redirect_url == 'https://idpay.ir/p/x'

    def test_create_payment_unauthorized(self, app):
        _set_setting('payment', 'idpay_api_key', 'bad')
        order, _ = _make_order(app)
        gateway = pg.IDPayGateway()
        with patch.object(pg._requests, 'post', return_value=_mock_response(status_code=401)):
            result = gateway.create_payment(order, 'https://cb')
        assert not result.success
        assert result.error_code == 'unauthorized'

    def test_verify_success(self, app):
        _set_setting('payment', 'idpay_api_key', 'k')
        order, txn = _make_order(app)
        txn.gateway = 'idpay'
        txn.reference_id = 'pid1'
        gateway = pg.IDPayGateway()
        with patch.object(pg._requests, 'post',
                         return_value=_mock_response({'status': 100, 'track_id': 555, 'id': 'pid1'})):
            result = gateway.verify_payment(txn, {'id': 'pid1', 'order_id': order.order_number, 'status': '1'})
        assert result.success
        assert result.raw_response['track_id'] == 555

    def test_verify_cancelled(self, app):
        _set_setting('payment', 'idpay_api_key', 'k')
        order, txn = _make_order(app)
        result = pg.IDPayGateway().verify_payment(txn, {'id': 'p', 'status': '2'})
        assert not result.success
        assert result.error_code == 'cancelled'


# ==================== DigiPay ====================

class TestDigiPay:

    def _oauth_ok(self, url, **kwargs):
        if url.endswith('/oauth/token'):
            return _mock_response({'access_token': 'tok1', 'expires_in': 3000})
        raise AssertionError(f'unexpected url {url}')

    def test_create_payment_success(self, app):
        for k in ('client_id', 'client_secret', 'username', 'password'):
            _set_setting('payment', f'digipay_{k}', f'v-{k}')
        order, _ = _make_order(app)
        gateway = pg.DigiPayGateway()
        gateway._token_cache.clear()

        responses = [
            _mock_response({'access_token': 'tok1', 'expires_in': 3000}),       # oauth
            _mock_response({'result': {'status': 0, 'message': 'ok'}, 'ticket': 't1',
                            'redirectUrl': 'https://uatweb.mydigipay.info/web-pay/tgs/t1'}),
        ]
        with patch.object(pg._requests, 'post', side_effect=responses):
            result = gateway.create_payment(order, 'https://cb')
        assert result.success
        assert 'web-pay' in result.redirect_url

    def test_missing_config(self, app):
        order, _ = _make_order(app)
        result = pg.DigiPayGateway().create_payment(order, 'https://cb')
        assert not result.success
        assert result.error_code == 'config_or_auth_failed'

    def test_verify_success_checks_amount(self, app):
        for k in ('client_id', 'client_secret', 'username', 'password'):
            _set_setting('payment', f'digipay_{k}', 'x')
        order, txn = _make_order(app)
        gateway = pg.DigiPayGateway()
        gateway._token_cache.clear()
        responses = [
            _mock_response({'access_token': 'tok2', 'expires_in': 3000}),
            _mock_response({'result': {'status': 0}, 'trackingCode': 'TC1', 'type': 11}),
        ]
        cb = {'result': 'SUCCESS', 'trackingCode': 'TC1', 'providerId': order.order_number,
              'amount': 1000000, 'type': 11}
        with patch.object(pg._requests, 'post', side_effect=responses):
            result = gateway.verify_payment(txn, cb)
        assert result.success
        assert result.raw_response['trackingCode'] == 'TC1'

    def test_verify_amount_mismatch(self, app):
        order, txn = _make_order(app)
        cb = {'result': 'SUCCESS', 'trackingCode': 'T', 'providerId': order.order_number,
              'amount': 1, 'type': 11}
        result = pg.DigiPayGateway().verify_payment(txn, cb)
        assert not result.success
        assert result.error_code == 'amount_mismatch'

    def test_verify_failure_result(self, app):
        order, txn = _make_order(app)
        result = pg.DigiPayGateway().verify_payment(txn, {'result': 'FAILURE'})
        assert not result.success


# ==================== SnappPay ====================

class TestSnappPay:

    def test_create_payment_success(self, app):
        for k in ('client_id', 'client_secret', 'username', 'password'):
            _set_setting('payment', f'snapppay_{k}', 's')
        order, _ = _make_order(app)
        gateway = pg.SnappPayGateway()
        gateway._token_cache.clear()
        responses = [
            _mock_response({'access_token': 'st', 'expires_in': 3000}),
            _mock_response({'paymentToken': 'PT1', 'paymentPageUrl': 'https://sandbox.snappymarket.ir/pay/PT1'}),
        ]
        with patch.object(pg._requests, 'post', side_effect=responses):
            result = gateway.create_payment(order, 'https://cb')
        assert result.success
        assert result.transaction_id == 'PT1'

    def test_verify_success_with_settle(self, app):
        for k in ('client_id', 'client_secret', 'username', 'password'):
            _set_setting('payment', f'snapppay_{k}', 's')
        order, txn = _make_order(app)
        gateway = pg.SnappPayGateway()
        gateway._token_cache.clear()
        responses = [
            _mock_response({'access_token': 'st2', 'expires_in': 3000}),   # oauth
            _mock_response({'status': 'DONE', 'paymentToken': 'PT1'}),     # verify
            _mock_response({'status': 'SETTLED'}),                          # settle
        ]
        with patch.object(pg._requests, 'post', side_effect=responses):
            result = gateway.verify_payment(txn, {'status': 'SUCCESSFUL', 'paymentToken': 'PT1'})
        assert result.success

    def test_verify_cancelled(self, app):
        order, txn = _make_order(app)
        result = pg.SnappPayGateway().verify_payment(txn, {'status': 'CANCELLED', 'paymentToken': 'x'})
        assert not result.success
        assert result.error_code == 'cancelled'


# ==================== بانک سپه (شاپرک) ====================

class TestSepah:

    def test_create_payment_form_redirect(self, app):
        _set_setting('payment', 'sepah_terminal_id', '123456')
        order, _ = _make_order(app)
        gateway = pg.SepahGateway()
        with patch.object(pg._requests, 'post',
                         return_value=_mock_response({'Status': '0', 'Accesstoken': 'ATK1'})):
            result = gateway.create_payment(order, 'https://cb')
        assert result.success
        assert result.redirect_method == 'form'
        assert result.form_url == 'https://sepehr.shaparak.ir:8080'
        assert result.form_fields['token'] == 'ATK1'
        assert result.form_fields['TerminalID'] == '123456'
        assert result.form_fields['getMethod'] == '1'

    def test_create_payment_bad_status(self, app):
        _set_setting('payment', 'sepah_terminal_id', '123456')
        order, _ = _make_order(app)
        with patch.object(pg._requests, 'post',
                         return_value=_mock_response({'Status': '-1', 'Description': 'bad'})):
            result = pg.SepahGateway().create_payment(order, 'https://cb')
        assert not result.success
        assert 'sepah_token' in result.error_code

    def test_verify_success(self, app):
        _set_setting('payment', 'sepah_terminal_id', '123456')
        order, txn = _make_order(app)
        txn.gateway = 'sepah'
        cb = {'State': 'OK', 'ResNum': order.order_number, 'RefNum': 'RF123', 'TraceNo': '99'}
        gateway = pg.SepahGateway()
        with patch.object(pg._requests, 'post',
                         return_value=_mock_response({'Status': '0', 'Amount': 1000000, 'RefNum': 'RF123'})):
            result = gateway.verify_payment(txn, cb)
        assert result.success
        assert result.raw_response['RefNum'] == 'RF123'

    def test_verify_user_cancel(self, app):
        _set_setting('payment', 'sepah_terminal_id', '123456')
        order, txn = _make_order(app)
        result = pg.SepahGateway().verify_payment(
            txn, {'State': 'Canceled By User'})
        assert not result.success
        assert result.error_code == 'cancelled'

    def test_verify_invoice_mismatch(self, app):
        _set_setting('payment', 'sepah_terminal_id', '123456')
        order, txn = _make_order(app)
        result = pg.SepahGateway().verify_payment(
            txn, {'State': 'OK', 'ResNum': 'OTHER-ORDER', 'RefNum': 'R'})
        assert not result.success
        assert result.error_code == 'invoice_mismatch'


# ==================== Mock + Factory ====================

class TestMockAndFactory:

    def test_mock_gateway(self, app):
        order, _ = _make_order(app)
        result = pg.MockGateway().create_payment(order, 'https://cb')
        assert result.success
        assert '/payment/mock/' in result.redirect_url

    def test_unknown_gateway_falls_back_to_mock(self):
        assert isinstance(pg.get_gateway('nope'), pg.MockGateway)

    def test_list_available_filters_unconfigured(self, app):
        _set_setting('payment', 'zarinpal_merchant_id', 'm' * 36)
        _set_setting('payment', 'sepah_terminal_id', 'T1')
        gateways = pg.list_available_gateways()
        ids = [g['id'] for g in gateways]
        assert 'mock' in ids
        assert 'zarinpal' in ids
        assert 'sepah' in ids
        assert 'digipay' not in ids      # بدون کلید → نمایش داده نمی‌شود
        assert all('label' in g and 'description' in g for g in gateways)

    def test_is_configured(self, app):
        assert not pg.ZarinpalGateway().is_configured()
        _set_setting('payment', 'zarinpal_merchant_id', 'm' * 36)
        assert pg.ZarinpalGateway().is_configured()


# ==================== Full flow (checkout → callback) ====================

class TestFullFlow:

    def _login(self, client):
        assert client.post('/user/login', data={
            'email': 'buyer@example.com', 'password': 'Passw0rd!'
        }, follow_redirects=True)

    def _checkout_online(self, client, gateway):
        product = Product.query.first()
        resp = client.post('/cart', data={'product_id': product.id, 'quantity': 1},
                           follow_redirects=True)
        assert resp.status_code == 200
        return client.post('/checkout', data={
            'recipient_name': 'خریدار تست',
            'recipient_phone': '09121112233',
            'province': 'تهران', 'city': 'تهران',
            'postal_code': '1234567890', 'address': 'خیابان تست',
            'payment_method': 'online', 'gateway': gateway,
        })

    def test_zarinpal_full_flow(self, app, client):
        self._login(client)
        _set_setting('payment', 'zarinpal_merchant_id', 'm' * 36)

        def fake_post(url, json=None, data=None, headers=None, timeout=None):
            if 'request.json' in url:
                return _mock_response({'data': {'code': 100, 'authority': 'AFLOW'}})
            if 'verify.json' in url:
                return _mock_response({'data': {'code': 100, 'ref_id': 777001}})
            raise AssertionError(url)

        with patch.object(pg._requests, 'post', side_effect=fake_post):
            resp = self._checkout_online(client, 'zarinpal')
            assert resp.status_code == 302
            assert 'StartPay/AFLOW' in resp.headers['Location']

            order = Order.query.filter_by(order_number=resp.headers['Location']).first() or \
                Order.query.order_by(Order.id.desc()).first()
            txn = order.transactions.first()
            assert txn.gateway == 'zarinpal'
            assert txn.reference_id == 'AFLOW'
            assert txn.status == 'pending'

            # کاربر از درگاه برمی‌گردد: /payment/callback/<order>?Authority=AFLOW&Status=OK
            resp = client.get(f'/payment/callback/{order.order_number}',
                              query_string={'Authority': 'AFLOW', 'Status': 'OK'})
            assert resp.status_code == 302

            order = Order.query.get(order.id)
            txn = order.transactions.first()
            assert txn.status == TransactionStatus.SUCCESS.value
            assert txn.tracking_code == '777001'
            assert txn.paid_at is not None
            assert order.payment_status == PaymentStatus.PAID.value
            assert order.status == OrderStatus.CONFIRMED.value

    def test_zarinpal_cancel_flow(self, app, client):
        self._login(client)
        _set_setting('payment', 'zarinpal_merchant_id', 'm' * 36)

        def fake_post(url, **kw):
            if 'request.json' in url:
                return _mock_response({'data': {'code': 100, 'authority': 'ACANCEL'}})
            raise AssertionError(url)

        with patch.object(pg._requests, 'post', side_effect=fake_post):
            resp = self._checkout_online(client, 'zarinpal')
            order = Order.query.order_by(Order.id.desc()).first()
            resp = client.get(f'/payment/callback/{order.order_number}',
                              query_string={'Authority': 'ACANCEL', 'Status': 'NOK'},
                              follow_redirects=True)
            assert resp.status_code == 200
            txn = order.transactions.first()
            assert txn.status == TransactionStatus.CANCELLED.value
            assert order.payment_status == PaymentStatus.FAILED.value

    def test_sepah_form_redirect_flow(self, app, client):
        self._login(client)
        _set_setting('payment', 'sepah_terminal_id', 'T-001')

        def fake_post(url, json=None, data=None, headers=None, timeout=None):
            if 'GetToken' in url:
                return _mock_response({'Status': '0', 'Accesstoken': 'SEPEHR-TOK'})
            if 'Verify' in url:
                return _mock_response({'Status': '0', 'Amount': 1000000, 'RefNum': 'RF-9'})
            raise AssertionError(url)

        with patch.object(pg._requests, 'post', side_effect=fake_post):
            resp = self._checkout_online(client, 'sepah')
            assert resp.status_code == 302
            assert '/payment/redirect/' in resp.headers['Location']

            order = Order.query.order_by(Order.id.desc()).first()
            txn = order.transactions.first()
            assert txn.gateway == 'sepah'
            assert txn.reference_id == 'SEPEHR-TOK'

            # صفحه واسط فرم را رندر می‌کند
            resp = client.get(f'/payment/redirect/{order.order_number}')
            assert resp.status_code == 200
            assert b'SEPEHR-TOK' in resp.data
            assert b'sepehr.shaparak.ir' in resp.data

            # درگاه (شاپرک) کاربر را با POST برمی‌گرداند
            resp = client.post(f'/payment/callback/{order.order_number}', data={
                'State': 'OK', 'ResNum': order.order_number,
                'RefNum': 'RF-9', 'TraceNo': '10',
            }, follow_redirects=True)
            assert resp.status_code == 200

            order = Order.query.get(order.id)
            txn = order.transactions.first()
            assert txn.status == TransactionStatus.SUCCESS.value
            assert txn.tracking_code == 'RF-9'
            assert order.payment_status == PaymentStatus.PAID.value

    def test_retry_payment_route(self, app, client):
        self._login(client)
        with patch.object(pg._requests, 'post',
                         return_value=_mock_response({'data': {'code': 100, 'authority': 'ARETRY'}})):
            _set_setting('payment', 'zarinpal_merchant_id', 'm' * 36)
            self._checkout_online(client, 'zarinpal')
            order = Order.query.order_by(Order.id.desc()).first()
            client.get(f'/payment/callback/{order.order_number}',
                       query_string={'Authority': 'ARETRY', 'Status': 'NOK'})
            resp = client.get(f'/order/{order.order_number}/pay')
            assert resp.status_code == 302
            assert 'StartPay' in resp.headers['Location']

    def test_product_add_to_cart_button(self, client):
        """دکمهٔ خرید صفحه محصول → POST /cart → افزودن به سبد."""
        product = Product.query.first()
        resp = client.post('/cart', data={'product_id': product.id, 'quantity': 2},
                           follow_redirects=True)
        assert resp.status_code == 200
        assert 'سبد خرید'.encode() in resp.data or 'cart'.encode() in resp.data

    def test_card_payment_page_renders(self, app, client):
        """صفحهٔ کارت‌به‌کارت نباید 500 بدهد (باگ Setting.get سابق)."""
        self._login(client)
        order, _ = _make_order(app)
        resp = client.get(f'/order/{order.order_number}/card-payment')
        assert resp.status_code == 200
