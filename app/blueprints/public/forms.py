"""
Public Forms
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional


class ContactForm(FlaskForm):
    """Contact form"""
    
    name = StringField('نام و نام خانوادگی', validators=[
        DataRequired(message='نام الزامی است'),
        Length(min=3, max=100)
    ])
    
    email = StringField('ایمیل', validators=[
        DataRequired(message='ایمیل الزامی است'),
        Email(message='ایمیل نامعتبر است')
    ])
    
    phone = StringField('شماره تلفن', validators=[
        Optional()
    ])
    
    subject = StringField('موضوع', validators=[
        DataRequired(message='موضوع الزامی است'),
        Length(max=255)
    ])
    
    message = TextAreaField('پیام', validators=[
        DataRequired(message='پیام الزامی است'),
        Length(min=10, max=2000)
    ])
    
    submit = SubmitField('ارسال پیام')


class NewsletterForm(FlaskForm):
    """Newsletter subscription form"""
    
    email = StringField('ایمیل', validators=[
        DataRequired(message='ایمیل الزامی است'),
        Email(message='ایمیل نامعتبر است')
    ])
    
    submit = SubmitField('عضویت')


class SearchForm(FlaskForm):
    """Search form"""
    
    q = StringField('جستجو', validators=[
        DataRequired(message='عبارت جستجو الزامی است')
    ])
    
    submit = SubmitField('جستجو')
