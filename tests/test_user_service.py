"""
Tests for AuthService and UserService business layer.
"""
import pytest
from app import create_app
from app.extensions import db
from app.models.user import User, Role, Address
from app.models.product import Product
from app.services.user_service import AuthService, UserService


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


def test_user_registration_and_authentication(app_ctx):
    """Test user registration validation and subsequent login."""
    # Register user
    success, user, errors = AuthService.register_user(
        email="customer@example.com",
        phone="09123456789",
        first_name="علیرضا",
        last_name="احمدی",
        password="SecurePassword123!",
        confirm_password="SecurePassword123!",
    )
    assert success is True
    assert user is not None
    assert user.email == "customer@example.com"
    assert len(errors) == 0

    # Successful authentication
    auth_ok, auth_user, msg = AuthService.authenticate("customer@example.com", "SecurePassword123!")
    assert auth_ok is True
    assert auth_user.id == user.id

    # Authenticate via phone
    phone_ok, phone_user, _ = AuthService.authenticate("09123456789", "SecurePassword123!")
    assert phone_ok is True
    assert phone_user.id == user.id

    # Bad password
    bad_ok, _, err_msg = AuthService.authenticate("customer@example.com", "WrongPassword")
    assert bad_ok is False
    assert "اشتباه" in err_msg


def test_failed_login_lockout(app_ctx):
    """Verify account locks after 5 consecutive failed attempts."""
    # Create user
    AuthService.register_user(
        email="locked@example.com",
        phone="09129876543",
        first_name="تست",
        last_name="لاک",
        password="Password123!",
        confirm_password="Password123!",
    )

    # 5 failed attempts
    for _ in range(5):
        AuthService.authenticate("locked@example.com", "WrongPassword")

    # 6th attempt should be blocked due to lockout
    locked_ok, _, lock_msg = AuthService.authenticate("locked@example.com", "Password123!")
    assert locked_ok is False
    assert "قفل" in lock_msg


def test_user_address_crud(app_ctx):
    """Test adding, editing, and deleting customer shipping addresses."""
    _, user, _ = AuthService.register_user(
        email="addr@example.com",
        phone="09121112233",
        first_name="سارا",
        last_name="کریمی",
        password="Password123!",
        confirm_password="Password123!",
    )

    address_data = {
        "title": "منزل",
        "recipient_name": "سارا کریمی",
        "recipient_phone": "09121112233",
        "province": "تهران",
        "city": "تهران",
        "address": "خیابان ولیعصر، نرسیده به میدان ونک، پلاک ۱۲",
        "postal_code": "1234567890",
        "is_default": True,
    }

    # Create address
    ok, addr, errs = UserService.save_address(user.id, address_data)
    assert ok is True
    assert addr is not None
    assert addr.title == "منزل"
    assert addr.is_default is True

    # Retrieve addresses
    addresses = UserService.get_user_addresses(user.id)
    assert len(addresses) == 1

    # Delete address
    del_ok = UserService.delete_address(addr.id, user.id)
    assert del_ok is True
    assert len(UserService.get_user_addresses(user.id)) == 0


def test_user_profile_and_password_change(app_ctx):
    """Test updating user profile details and password changes."""
    _, user, _ = AuthService.register_user(
        email="profile@example.com",
        phone="09123334455",
        first_name="محمد",
        last_name="رضایی",
        password="OldPassword123!",
        confirm_password="OldPassword123!",
    )

    # Update profile
    prof_ok, errs = UserService.update_profile(user, first_name="محمدرضا", last_name="رضایی اصل")
    assert prof_ok is True
    assert user.first_name == "محمدرضا"

    # Change password
    pw_ok, pw_msg = UserService.change_password(user, "OldPassword123!", "NewPassword123!", "NewPassword123!")
    assert pw_ok is True

    # Verify old password no longer works
    old_auth, _, _ = AuthService.authenticate("profile@example.com", "OldPassword123!")
    assert old_auth is False

    # Verify new password works
    new_auth, _, _ = AuthService.authenticate("profile@example.com", "NewPassword123!")
    assert new_auth is True
