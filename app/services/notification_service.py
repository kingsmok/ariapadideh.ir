"""
Notification Service
"""
from typing import Optional, List, Dict, Any
from flask import current_app
import requests
import json

from app.extensions import db
from app.models import Notification, User, Order, Contact


class NotificationService:
    """Notification Operations"""
    
    @staticmethod
    def send_to_user(user_id: int, title: str, message: str, 
                    type: str = 'info', data: dict = None) -> Notification:
        """Send notification to specific user"""
        
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=type,
            data=data
        )
        notification.save()
        
        return notification
    
    @staticmethod
    def notify_admins(title: str, message: str, type: str = 'info', 
                     data: dict = None) -> List[Notification]:
        """Send notification to all admin users"""
        
        admins = User.query.join(User.role).filter(
            User.is_deleted == False,
            User.is_active == True,
            User.role.has(slug='admin')
        ).all()
        
        notifications = []
        for admin in admins:
            notif = NotificationService.send_to_user(
                admin.id, title, message, type, data
            )
            notifications.append(notif)
        
        return notifications
    
    @staticmethod
    def notify_telegram(message: str, chat_id: str = None) -> bool:
        """Send notification via Telegram bot"""
        
        bot_token = current_app.config.get('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            return False
        
        if not chat_id:
            chat_id = current_app.config.get('TELEGRAM_ADMIN_CHAT_ID')
        
        if not chat_id:
            return False
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        try:
            response = requests.post(url, data=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            current_app.logger.error(f"Telegram notification error: {e}")
            return False
    
    @staticmethod
    def notify_telegram_order_new(order: Order) -> bool:
        """Send new order notification to Telegram"""
        
        message = f"""🛒 <b>سفارش جدید</b>

📋 شماره: {order.order_number}
💰 مبلغ: {order.total_amount:,.0f} تومان
📦 وضعیت: {order.status_fa}
👤 مشتری: {order.recipient_name or order.user.full_name if order.user else 'مهمان'}
📱 تلفن: {order.recipient_phone or (order.user.phone if order.user else '-')}

🔗 لینک: {current_app.config.get('SITE_URL', '')}/admin/orders/{order.id}
"""
        
        return NotificationService.notify_telegram(message)
    
    @staticmethod
    def notify_telegram_order_update(order: Order) -> bool:
        """Send order status update to Telegram"""
        
        message = f"""📦 <b>بروزرسانی سفارش</b>

📋 شماره: {order.order_number}
🔄 وضعیت جدید: {order.status_fa}
👤 مشتری: {order.recipient_name or order.user.full_name if order.user else 'مهمان'}
"""
        
        return NotificationService.notify_telegram(message)
    
    @staticmethod
    def notify_telegram_contact(contact: Contact) -> bool:
        """Send new contact message to Telegram"""
        
        message = f"""📩 <b>پیام جدید</b>

👤 نام: {contact.name}
📧 ایمیل: {contact.email}
📱 تلفن: {contact.phone or '-'}
📝 موضوع: {contact.subject or '-'}
💬 پیام: {contact.message[:500]}

🔗 لینک: {current_app.config.get('SITE_URL', '')}/admin/contacts/{contact.id}
"""
        
        return NotificationService.notify_telegram(message)
    
    @staticmethod
    def notify_telegram_resume(resume) -> bool:
        """Send new resume notification to Telegram"""
        
        message = f"""📄 <b>رزومه جدید</b>

👤 نام: {resume.full_name}
📧 ایمیل: {resume.email}
📱 تلفن: {resume.phone}
💼 سمت: {resume.job_position or '-'}
🏢 بخش: {resume.job_category or '-'}

🔗 لینک: {current_app.config.get('SITE_URL', '')}/admin/resumes/{resume.id}
"""
        
        return NotificationService.notify_telegram(message)
    
    @staticmethod
    def send_contact_reply(contact: Contact, reply_text: str = '') -> bool:
        """Send reply to contact via email"""
        from app.services.email_service import EmailService

        if not contact.email:
            return False

        # If reply_text not provided, just mark as replied
        if not reply_text:
            return True

        return EmailService.send_contact_reply(
            contact_email=contact.email,
            contact_name=contact.name,
            reply_text=reply_text,
            original_subject=contact.subject or 'پیام شما',
        )

    @staticmethod
    def send_order_confirmation(order: Order) -> bool:
        """Send order confirmation email to customer"""
        from app.services.email_service import EmailService

        # Always create in-app notification
        if order.user:
            NotificationService.send_to_user(
                user_id=order.user_id,
                title='تأیید سفارش',
                message=f'سفارش شما با شماره {order.order_number} ثبت شد.',
                type='order',
                data={'order_id': order.id}
            )

        # Send actual email
        return EmailService.send_order_confirmation(order)

    @staticmethod
    def send_password_reset(user: User, reset_url: str = None) -> bool:
        """Send password reset email"""
        from app.services.email_service import EmailService
        from flask import url_for

        if reset_url is None:
            # Generate URL if not provided
            token = user.generate_reset_token()
            reset_url = url_for('user.reset_password', token=token, _external=True)

        # Send email
        email_sent = EmailService.send_password_reset(user, reset_url)

        # Also create in-app notification
        NotificationService.send_to_user(
            user_id=user.id,
            title='بازیابی رمز عبور',
            message='لینک بازیابی رمز عبور به ایمیل شما ارسال شد.',
            type='warning',
            data={'action': 'password_reset'}
        )

        return email_sent
