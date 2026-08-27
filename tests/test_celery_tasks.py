"""
Tests for the Celery task layer (app/tasks), the enqueue fallback,
scheduled storefront jobs and the api_required hardening.

These tests run entirely without Redis: TestingConfig forces
``CELERY_ENABLED = False`` so ``enqueue`` executes task bodies inline,
and the scheduled-job tests call the ``*_impl`` functions directly.
"""
from datetime import datetime, timedelta

import pytest
from flask import jsonify

from app import create_app
from app.extensions import db
from app.constants import OrderStatus, PaymentStatus, TransactionStatus
from app.models import (
    CartItem, Order, OrderItem, PaymentTransaction, Product,
)
from app.tasks import celery, enqueue
from app.tasks.order_tasks import expire_unpaid_orders_impl, cleanup_stale_guest_carts_impl


# ==================== fixtures ====================

@pytest.fixture
def app_ctx():
    """Create a testing application context with a clean schema."""
    test_app = create_app('testing')
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


def _make_pending_order(stock: int = 10, qty: int = 2, age_minutes: int = 120):
    """Persist a Product + unpaid pending Order (2 stock lines) + pending txn.

    Returns (product, order, transaction) with created_at back-dated so the
    expiration job can observe window semantics.
    """
    product = Product(
        title=f'محصول تستی {datetime.utcnow().timestamp()}',
        slug=f'test-product-{datetime.utcnow().strftime("%H%M%S%f")}',
        price=100000,
        stock_quantity=stock,
        is_active=True,
    )
    db.session.add(product)
    db.session.flush()

    order = Order(
        order_number=Order.generate_order_number(),
        status=OrderStatus.PENDING.value,
        payment_status=PaymentStatus.UNPAID.value,
        subtotal=product.price * qty,
        total_amount=product.price * qty,
        recipient_name='کاربر تست',
        recipient_phone='09120000000',
        created_at=datetime.utcnow() - timedelta(minutes=age_minutes),
    )
    db.session.add(order)
    db.session.flush()

    item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=qty,
        unit_price=product.price,
    )
    db.session.add(item)

    # شبیه‌سازی رفتار واقعی checkout: موجودی در لحظهٔ ثبت سفارش کسر (رزرو) می‌شود
    if product.stock_quantity is not None:
        product.stock_quantity -= qty

    txn = PaymentTransaction(
        order_id=order.id,
        amount=order.total_amount,
        status=TransactionStatus.PENDING.value,
    )
    db.session.add(txn)
    db.session.commit()
    return product, order, txn


# ==================== expire_unpaid_orders ====================

def test_expire_unpaid_orders_cancels_and_restocks(app_ctx):
    """Stale pending+unpaid orders are cancelled, stock restored, txn failed."""
    product, order, txn = _make_pending_order(stock=10, qty=2, age_minutes=120)

    result = expire_unpaid_orders_impl()

    assert result['expired'] == 1
    assert result['restored_lines'] == 1
    assert result['failed'] == 0

    db.session.expire_all()
    order = db.session.get(Order, order.id)
    assert order.status == OrderStatus.CANCELLED.value
    assert order.cancelled_at is not None
    assert 'اتمام مهلت پرداخت' in (order.admin_note or '')

    refreshed_product = db.session.get(Product, product.id)
    # ۱۰ موجودی اولیه → ۸ پس از رزرو checkout → ۱۰ پس از آزادسازی توسط تسک
    assert refreshed_product.stock_quantity == 10

    refreshed_txn = db.session.get(PaymentTransaction, txn.id)
    assert refreshed_txn.status == TransactionStatus.FAILED.value


def test_expire_unpaid_orders_skips_fresh_and_paid(app_ctx):
    """Orders inside the grace window — or already paid — must be untouched."""
    fresh_product, fresh_order, _ = _make_pending_order(stock=5, qty=1, age_minutes=10)

    paid_product, paid_order, _ = _make_pending_order(stock=7, qty=1, age_minutes=120)
    paid_order.payment_status = PaymentStatus.PAID.value
    db.session.commit()

    result = expire_unpaid_orders_impl()
    assert result['expired'] == 0

    db.session.expire_all()
    assert db.session.get(Order, fresh_order.id).status == OrderStatus.PENDING.value
    assert db.session.get(Product, fresh_product.id).stock_quantity == 4  # reserved, not restored
    assert db.session.get(Product, paid_product.id).stock_quantity == 6  # paid, not restored


def test_expire_unpaid_orders_can_be_disabled(app_ctx):
    """grace_minutes <= 0 is an explicit kill-switch (zero rows touched)."""
    _make_pending_order(stock=10, qty=2, age_minutes=120)

    result = expire_unpaid_orders_impl(grace_minutes=0)
    assert result['expired'] == 0
    assert result.get('skipped') == 1


# ==================== cleanup_stale_guest_carts ====================

def test_cleanup_stale_guest_carts(app_ctx):
    """Only old *guest* cart lines are deleted; user carts and fresh rows stay."""
    product = Product(title='کالای سبد', slug='cart-item-1', price=5000,
                      stock_quantity=1, is_active=True)
    db.session.add(product)
    db.session.flush()

    old_guest = CartItem(product_id=product.id, quantity=1, session_id='sess-old',
                         created_at=datetime.utcnow() - timedelta(days=40))
    fresh_guest = CartItem(product_id=product.id, quantity=1, session_id='sess-new',
                           created_at=datetime.utcnow() - timedelta(days=2))
    user_cart = CartItem(product_id=product.id, quantity=3, session_id=None,
                         created_at=datetime.utcnow() - timedelta(days=40))
    db.session.add_all([old_guest, fresh_guest, user_cart])
    db.session.commit()

    # شناسه‌ها را قبل از job نگه می‌داریم: commitِ بعدِ حذف، آبجکت‌های identity-map
    # را expire می‌کند و دسترسی مجدد به ردیفِ حذف‌شده ObjectDeletedError می‌دهد.
    old_id, fresh_id, user_id = old_guest.id, fresh_guest.id, user_cart.id

    removed = cleanup_stale_guest_carts_impl()
    assert removed == 1

    # چک با کوئری (نه session.get) چون ردیفِ bulk-deleted در identity map
    # باقی مانده و get روی آن ObjectDeletedError می‌دهد.
    from sqlalchemy import func, select

    def _exists(row_id: int) -> bool:
        count = db.session.execute(
            select(func.count()).select_from(CartItem).where(CartItem.id == row_id)
        ).scalar_one()
        return count > 0

    assert _exists(old_id) is False
    assert _exists(fresh_id) is True
    assert _exists(user_id) is True


# ==================== enqueue fallback ====================

def test_enqueue_runs_inline_when_celery_disabled(app_ctx):
    """Without Celery, enqueue() must execute the body and return its value."""
    calls = []

    def sample_task(x: int) -> str:
        calls.append(x)
        return f'done-{x}'

    result = enqueue(sample_task, 7)
    assert result == 'done-7'
    assert calls == [7]


def test_enqueue_uses_delay_when_celery_enabled(app_ctx):
    """With Celery enabled, enqueue() must go through .delay (no inline run)."""
    app_ctx.config['CELERY_ENABLED'] = True
    events = []

    class FakeTask:
        def delay(self, *args, **kwargs):
            events.append(('delay', args, kwargs))
            return 'async-result'

    result = enqueue(FakeTask(), 1, 2, key='v')
    assert result == 'async-result'
    assert events == [('delay', (1, 2), {'key': 'v'})]


# ==================== task availability guards (misconfig must not explode) ====================

def test_mail_tasks_skip_silently_without_smtp(app_ctx):
    """No MAIL_SERVER → the email task returns False instead of raising."""
    from app.tasks.mail_tasks import send_order_confirmation_email, send_password_reset_email

    assert send_order_confirmation_email.run(order_id=1) is False
    assert send_password_reset_email.run(user_id=1, reset_url='https://x') is False


def test_telegram_task_skips_without_config(app_ctx):
    """No bot token → telegram task is a no-op, not an exception."""
    from app.tasks.notify_tasks import telegram_order_new_task

    _, order, _ = _make_pending_order()
    assert telegram_order_new_task.run(order.id) is False


# ==================== api_required (VALID_API_KEYS now wired to Config) ====================

@pytest.mark.parametrize('scenario', ['missing-key', 'bad-key', 'good-key', 'no-keys-configured'])
def test_api_required_decorator(app_ctx, scenario):
    """Fail-closed key auth: 401 for missing/invalid keys, 503 when unconfigured, 200 for valid."""
    from app.utils.decorators import api_required

    @api_required
    def protected():
        return jsonify(ok=True)

    app_ctx.add_url_rule('/_test/api-protected', 'api_protected', protected)

    if scenario == 'no-keys-configured':
        app_ctx.config['VALID_API_KEYS'] = []
        resp = app_ctx.test_client().get('/_test/api-protected', headers={'X-API-Key': 'whatever'})
        assert resp.status_code == 503
        return

    app_ctx.config['VALID_API_KEYS'] = ['secret-key-1', 'secret-key-2']
    client = app_ctx.test_client()

    if scenario == 'missing-key':
        resp = client.get('/_test/api-protected')
        assert resp.status_code == 401
    elif scenario == 'bad-key':
        resp = client.get('/_test/api-protected', headers={'X-API-Key': 'nope'})
        assert resp.status_code == 401
    else:  # good-key — via header, plus query-string variant
        resp = client.get('/_test/api-protected', headers={'X-API-Key': 'secret-key-2'})
        assert resp.status_code == 200
        resp = client.get('/_test/api-protected?api_key=secret-key-1')
        assert resp.status_code == 200


# ==================== wiring integrity ====================

def test_task_registry_and_beat_schedule():
    """Names referenced by routing/beat must match registered tasks."""
    registered = set(celery.tasks)
    for expected in (
        'flaskpro.orders.expire_unpaid',
        'flaskpro.orders.cleanup_stale_carts',
        'flaskpro.mail.send_order_confirmation',
        'flaskpro.mail.send_password_reset',
        'flaskpro.mail.send_contact_reply',
        'flaskpro.notify.telegram_send',
        'flaskpro.notify.telegram_order_new',
        'flaskpro.notify.telegram_contact_new',
    ):
        assert expected in registered, f'task {expected} not registered'

    for entry in celery.conf.beat_schedule.values():
        assert entry['task'] in registered, 'beat references an unregistered task'
