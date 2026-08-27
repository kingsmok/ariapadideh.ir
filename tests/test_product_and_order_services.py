"""
Tests for ProductService and OrderService business layers.
"""
import pytest
from app import create_app
from app.extensions import db
from app.models.product import Product, Category
from app.models.order import Order, OrderItem
from app.models.user import User, Role
from app.services.product_service import ProductService
from app.services.order_service import OrderService
from app.constants import OrderStatus


@pytest.fixture
def app_ctx():
    """Create testing application context."""
    test_app = create_app('testing')
    with test_app.app_context():
        db.create_all()
        Role.get_admin_role()
        Role.get_user_role()
        yield test_app
        db.session.remove()
        db.drop_all()


def test_product_service_catalog_and_stock(app_ctx):
    """Test product creation, querying, searching, and inventory adjustment."""
    cat = Category(title="لپ تاپ", slug="laptops", is_active=True)
    db.session.add(cat)
    db.session.commit()

    prod = Product(
        title="لپ تاپ ایسوس ZenBook",
        slug="asus-zenbook",
        price=50000000,
        stock_quantity=10,
        is_active=True,
    )
    prod.categories.append(cat)
    db.session.add(prod)
    db.session.commit()

    # Query by ID and Slug
    found_by_id = ProductService.get_by_id(prod.id)
    assert found_by_id is not None
    assert found_by_id.slug == "asus-zenbook"

    found_by_slug = ProductService.get_by_slug("asus-zenbook")
    assert found_by_slug is not None
    assert found_by_slug.id == prod.id

    # Search
    items, total = ProductService.search_products(query="ایسوس", category_slug="laptops")
    assert total == 1
    assert len(items) == 1
    assert items[0].id == prod.id

    # Stock update
    stock_ok = ProductService.update_stock(prod.id, -3)
    assert stock_ok is True
    refreshed = db.session.get(Product, prod.id)
    assert refreshed.stock_quantity == 7


def test_order_service_lifecycle_and_cancellation(app_ctx):
    """Test order status updates and cancellation with inventory restoration."""
    prod = Product(
        title="گوشی سامسونگ گلکسی",
        slug="samsung-galaxy",
        price=30000000,
        stock_quantity=5,
        is_active=True,
    )
    db.session.add(prod)
    db.session.commit()

    order = Order(
        order_number="ORD-TEST-1001",
        total_amount=30000000,
        status=OrderStatus.PENDING.value,
    )
    db.session.add(order)
    db.session.commit()

    order_item = OrderItem(
        order_id=order.id,
        product_id=prod.id,
        quantity=2,
        unit_price=30000000,
    )
    db.session.add(order_item)
    db.session.commit()

    # Update order status
    ok, msg = OrderService.update_order_status(order.id, OrderStatus.CONFIRMED.value, admin_note="تأیید فاکتور")
    assert ok is True

    # Cancel order and restore stock
    cancel_ok, cancel_msg = OrderService.cancel_order(order.id, reason="عدم نیاز مشتری")
    assert cancel_ok is True

    # Check inventory returned: 5 + 2 = 7
    refreshed_prod = db.session.get(Product, prod.id)
    assert refreshed_prod.stock_quantity == 7

    # Check order status is now cancelled
    refreshed_order = db.session.get(Order, order.id)
    assert refreshed_order.status == OrderStatus.CANCELLED.value
