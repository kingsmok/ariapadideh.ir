"""
Email Service — sends transactional emails via SMTP.
Replaces the placeholder return-True stubs in NotificationService.
"""
import smtplib
import socket
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate
from typing import List, Optional
from flask import current_app, render_template_string

from app.models import Order, User


class EmailError(Exception):
    """Raised when email sending fails."""
    pass


class EmailService:
    """Sends emails through configured SMTP server."""

    @classmethod
    def send(
        cls,
        to: str | List[str],
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        reply_to: Optional[str] = None,
    ) -> bool:
        """
        Send an email.

        Args:
            to: Recipient email(s) — string or list.
            subject: Email subject.
            html_body: HTML content.
            text_body: Plain text fallback. Auto-generated if not provided.
            cc, bcc: Optional CC/BCC lists.
            reply_to: Optional reply-to address.

        Returns:
            True if sent, False otherwise (logs error but doesn't raise).
        """
        if not current_app.config.get('MAIL_SERVER'):
            current_app.logger.info(
                f'Email not sent (no MAIL_SERVER configured): to={to} subject={subject}'
            )
            return False

        # Normalize recipients
        if isinstance(to, str):
            to = [to]
        if not to:
            return False

        # Build message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = formataddr((
            current_app.config.get('MAIL_DEFAULT_SENDER_NAME', 'رهسا دیو'),
            current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@rahsadev.ir')
        ))
        msg['To'] = ', '.join(to)
        msg['Date'] = formatdate(localtime=True)

        if cc:
            msg['Cc'] = ', '.join(cc)
        if reply_to:
            msg['Reply-To'] = reply_to

        # Attach text + html (text first as fallback)
        if not text_body:
            # Simple HTML to text
            import re
            text_body = re.sub(r'<[^>]+>', '', html_body)
            text_body = re.sub(r'\s+', ' ', text_body).strip()

        part1 = MIMEText(text_body, 'plain', 'utf-8')
        part2 = MIMEText(html_body, 'html', 'utf-8')
        msg.attach(part1)
        msg.attach(part2)

        # Send
        try:
            all_recipients = to + (cc or []) + (bcc or [])

            with smtplib.SMTP(
                current_app.config['MAIL_SERVER'],
                current_app.config.get('MAIL_PORT', 587),
                timeout=10,
            ) as server:
                server.ehlo()

                if current_app.config.get('MAIL_USE_TLS', True):
                    server.starttls()
                    server.ehlo()

                username = current_app.config.get('MAIL_USERNAME')
                password = current_app.config.get('MAIL_PASSWORD')
                if username and password:
                    server.login(username, password)

                server.sendmail(msg['From'], all_recipients, msg.as_string())

            current_app.logger.info(f'Email sent to {to}: {subject}')
            return True

        except (smtplib.SMTPException, socket.timeout, OSError) as e:
            current_app.logger.error(f'Email send failed: {e}')
            return False

    # ==================== High-level templates ====================

    @classmethod
    def send_order_confirmation(cls, order: Order) -> bool:
        """Send order confirmation email to customer."""
        if not order.user or not order.user.email:
            return False

        subject = f'تأیید سفارش {order.order_number} - رهسا دیو'
        html = render_template_string(_ORDER_CONFIRMATION_TEMPLATE, order=order)
        return cls.send(order.user.email, subject, html)

    @classmethod
    def send_order_status_update(cls, order: Order) -> bool:
        """Notify customer that their order status changed."""
        if not order.user or not order.user.email:
            return False

        subject = f'بروزرسانی سفارش {order.order_number} - رهسا دیو'
        html = render_template_string(
            _ORDER_STATUS_TEMPLATE,
            order=order,
            status_fa=order.status_fa,
        )
        return cls.send(order.user.email, subject, html)

    @classmethod
    def send_password_reset(cls, user: User, reset_url: str) -> bool:
        """Send password reset link."""
        if not user.email:
            return False

        subject = 'بازیابی رمز عبور - رهسا دیو'
        html = render_template_string(_PASSWORD_RESET_TEMPLATE, user=user, reset_url=reset_url)
        return cls.send(user.email, subject, html)

    @classmethod
    def send_welcome(cls, user: User) -> bool:
        """Send welcome email to new user."""
        if not user.email:
            return False

        subject = 'به رهسا دیو خوش آمدید! 🎉'
        html = render_template_string(_WELCOME_TEMPLATE, user=user)
        return cls.send(user.email, subject, html)

    @classmethod
    def send_contact_reply(cls, contact_email: str, contact_name: str, reply_text: str, original_subject: str) -> bool:
        """Send reply to a contact form submission."""
        if not contact_email:
            return False

        subject = f'پاسخ به: {original_subject}'
        html = render_template_string(
            _CONTACT_REPLY_TEMPLATE,
            contact_name=contact_name,
            reply_text=reply_text,
        )
        return cls.send(contact_email, subject, html)


# ==================== Email templates (inline, can be moved to .html) ====================

_ORDER_CONFIRMATION_TEMPLATE = """
<div dir="rtl" style="font-family: Tahoma, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background: linear-gradient(135deg, #0a1128, #14213d); padding: 2rem; text-align: center;">
        <h1 style="color: #fbb03b; margin: 0;">رهسا دیو</h1>
    </div>
    <div style="background: #ffffff; padding: 2rem; color: #1f2937;">
        <h2 style="color: #0a1128;">سفارش شما با موفقیت ثبت شد ✓</h2>
        <p>{{ order.user.full_name if order.user else 'کاربر گرامی' }} عزیز،</p>
        <p>سفارش شما با شماره <strong>{{ order.order_number }}</strong> با موفقیت در سیستم ثبت شد.</p>

        <div style="background: #f3f4f6; border-radius: 0.5rem; padding: 1rem; margin: 1.5rem 0;">
            <h3 style="margin-top: 0;">جزئیات سفارش:</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 0.5rem 0;"><strong>مبلغ کل:</strong></td><td>{{ "{:,}".format(order.total_amount|int) }} تومان</td></tr>
                <tr><td style="padding: 0.5rem 0;"><strong>وضعیت:</strong></td><td>{{ order.status_fa }}</td></tr>
                <tr><td style="padding: 0.5rem 0;"><strong>روش پرداخت:</strong></td><td>{{ order.payment_method }}</td></tr>
            </table>
        </div>

        <p>برای پیگیری وضعیت سفارش، به پنل کاربری خود مراجعه کنید.</p>
        <p style="color: #6b7280; font-size: 0.875rem; margin-top: 2rem;">با تشکر،<br>تیم رهسا دیو</p>
    </div>
</div>
"""

_ORDER_STATUS_TEMPLATE = """
<div dir="rtl" style="font-family: Tahoma, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background: #14213d; padding: 1.5rem; text-align: center;">
        <h2 style="color: #fbb03b; margin: 0;">رهسا دیو - بروزرسانی سفارش</h2>
    </div>
    <div style="background: #ffffff; padding: 2rem; color: #1f2937;">
        <p>{{ order.user.full_name }} عزیز،</p>
        <p>سفارش <strong>{{ order.order_number }}</strong> شما به وضعیت <strong style="color: #fbb03b;">«{{ status_fa }}»</strong> تغییر یافت.</p>
        <p>برای مشاهده جزئیات بیشتر، به پنل کاربری خود مراجعه کنید.</p>
    </div>
</div>
"""

_PASSWORD_RESET_TEMPLATE = """
<div dir="rtl" style="font-family: Tahoma, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background: #14213d; padding: 1.5rem; text-align: center;">
        <h2 style="color: #fbb03b; margin: 0;">بازیابی رمز عبور</h2>
    </div>
    <div style="background: #ffffff; padding: 2rem; color: #1f2937;">
        <p>{{ user.full_name }} عزیز،</p>
        <p>برای بازنشانی رمز عبور خود روی دکمه زیر کلیک کنید:</p>
        <div style="text-align: center; margin: 2rem 0;">
            <a href="{{ reset_url }}" style="background: #fbb03b; color: #0a1128; padding: 0.75rem 2rem; text-decoration: none; border-radius: 0.5rem; font-weight: bold; display: inline-block;">
                بازنشانی رمز عبور
            </a>
        </div>
        <p style="color: #6b7280; font-size: 0.875rem;">این لینک تا ۲۴ ساعت معتبر است.</p>
        <p style="color: #6b7280; font-size: 0.875rem;">اگر این درخواست از طرف شما نبوده، این ایمیل را نادیده بگیرید.</p>
    </div>
</div>
"""

_WELCOME_TEMPLATE = """
<div dir="rtl" style="font-family: Tahoma, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background: linear-gradient(135deg, #0a1128, #14213d); padding: 2rem; text-align: center;">
        <h1 style="color: #fbb03b; margin: 0;">به رهسا دیو خوش آمدید! 🎉</h1>
    </div>
    <div style="background: #ffffff; padding: 2rem; color: #1f2937;">
        <p>{{ user.full_name }} عزیز،</p>
        <p>از اینکه به جمع کاربران رهسا دیو پیوستید خوشحالیم.</p>
        <p>می‌توانید از خدمات و محصولات متنوع ما بازدید کرده و در صورت نیاز با ما تماس بگیرید.</p>
        <p style="margin-top: 2rem;">با تشکر،<br><strong>تیم رهسا دیو</strong></p>
    </div>
</div>
"""

_CONTACT_REPLY_TEMPLATE = """
<div dir="rtl" style="font-family: Tahoma, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background: #14213d; padding: 1.5rem; text-align: center;">
        <h2 style="color: #fbb03b; margin: 0;">پاسخ به پیام شما</h2>
    </div>
    <div style="background: #ffffff; padding: 2rem; color: #1f2937;">
        <p>{{ contact_name }} عزیز،</p>
        <p>پاسخ کارشناسان ما به پیام شما:</p>
        <div style="background: #f3f4f6; border-right: 3px solid #fbb03b; padding: 1rem; margin: 1.5rem 0;">
            {{ reply_text }}
        </div>
        <p style="color: #6b7280; font-size: 0.875rem; margin-top: 2rem;">با تشکر،<br>تیم پشتیبانی رهسا دیو</p>
    </div>
</div>
"""
