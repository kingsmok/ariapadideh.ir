"""
Admin Forms
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import (
    StringField, TextAreaField, SelectField, BooleanField,
    IntegerField, FloatField, PasswordField, SubmitField,
    HiddenField, DateField, DateTimeField, FormField, FieldList,
    SelectMultipleField
)
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo, NumberRange,
    Optional, Regexp, URL
)
from wtforms_sqlalchemy.fields import QuerySelectField

from app.extensions import db
from app.models import Role, Category, Brand, Tag


# ==================== AUTH FORMS ====================

class LoginForm(FlaskForm):
    """Admin login form"""
    
    email = StringField('ایمیل', validators=[
        DataRequired(message='ایمیل الزامی است'),
        Email(message='ایمیل نامعتبر است')
    ])
    
    password = PasswordField('رمز عبور', validators=[
        DataRequired(message='رمز عبور الزامی است')
    ])
    
    remember = BooleanField('مرا به خاطر بسپار')
    
    submit = SubmitField('ورود به پنل مدیریت')


# ==================== USER FORMS ====================

class UserForm(FlaskForm):
    """User create/edit form"""
    
    email = StringField('ایمیل', validators=[
        Email(message='ایمیل نامعتبر است')
    ])
    
    phone = StringField('شماره تلفن', validators=[
        Optional(),
        Regexp(r'^09[0-9]{9}$', message='شماره تلفن نامعتبر است')
    ])
    
    first_name = StringField('نام', validators=[
        Optional(),
        Length(max=100)
    ])
    
    last_name = StringField('نام خانوادگی', validators=[
        Optional(),
        Length(max=100)
    ])
    
    password = PasswordField('رمز عبور', validators=[
        Optional(),
        Length(min=8, message='رمز عبور باید حداقل ۸ کاراکتر باشد')
    ])
    
    role_id = SelectField('نقش', coerce=int, validate_choice=False, validators=[Optional()])
    
    is_active = BooleanField('فعال')
    is_verified = BooleanField('تأیید شده')
    
    submit = SubmitField('ذخیره')


class RoleForm(FlaskForm):
    """Role create/edit form"""
    
    name = StringField('نام نقش', validators=[
        DataRequired(message='نام نقش الزامی است'),
        Length(max=100)
    ])
    
    slug = StringField('شناسه', validators=[
        DataRequired(message='شناسه الزامی است'),
        Length(max=100),
        Regexp(r'^[a-z0-9_]+$', message='شناسه باید فقط شامل حروف کوچک، اعداد و underscore باشد')
    ])
    
    description = TextAreaField('توضیحات')
    
    permissions = TextAreaField('دسترسی‌ها', description='دسترسی‌ها را با کاما جدا کنید')
    
    submit = SubmitField('ذخیره')


# ==================== PRODUCT FORMS ====================

class ProductForm(FlaskForm):
    """Product create/edit form"""
    
    title = StringField('عنوان محصول', validators=[
        DataRequired(message='عنوان الزامی است'),
        Length(max=500)
    ])
    
    slug = StringField('نامک (Slug)', validators=[
        Optional(),
        Length(max=500)
    ])
    
    sku = StringField('کد محصول (SKU)', validators=[
        Optional(),
        Length(max=100)
    ])
    
    short_description = TextAreaField('توضیح کوتاه', validators=[
        Optional(),
        Length(max=1000)
    ])
    
    description = TextAreaField('توضیحات کامل')
    
    price = FloatField('قیمت', validators=[
        DataRequired(message='قیمت الزامی است'),
        NumberRange(min=0)
    ])
    
    old_price = FloatField('قیمت قبلی', validators=[
        Optional(),
        NumberRange(min=0)
    ])
    
    discount_percent = FloatField('درصد تخفیف', validators=[
        Optional(),
        NumberRange(min=0, max=100)
    ])
    
    stock_quantity = IntegerField('تعداد موجودی', validators=[
        DataRequired(),
        NumberRange(min=0)
    ])
    
    stock_status = SelectField('وضعیت موجودی', default='in_stock', choices=[
        ('in_stock', 'موجود'),
        ('out_of_stock', 'ناموجود'),
        ('limited', 'محدود'),
        ('preorder', 'پیش‌سفارش')
    ])
    
    brand_id = SelectField('برند', coerce=int, validate_choice=False, validators=[Optional()])
    
    categories = SelectMultipleField('دسته‌بندی‌ها', coerce=int, validate_choice=False)
    
    tags = SelectMultipleField('برچسب‌ها', coerce=int, validate_choice=False)
    
    featured_image = FileField('تصویر اصلی', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'فقط تصاویر مجاز هستند')
    ])
    
    images = FileField('تصاویر اضافی', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'فقط تصاویر مجاز هستند')
    ], render_kw={'multiple': True})
    
    specifications = TextAreaField('مشخصات فنی (JSON)', description='مشخصات را به فرمت JSON وارد کنید')
    
    is_active = BooleanField('فعال')
    is_featured = BooleanField('ویژه')
    is_new = BooleanField('جدید')
    show_in_home = BooleanField('نمایش در صفحه اصلی')
    
    meta_title = StringField('Meta Title', validators=[Length(max=255)])
    meta_description = TextAreaField('Meta Description', validators=[Length(max=500)])
    
    submit = SubmitField('ذخیره')


# ==================== CATEGORY FORMS ====================

class CategoryForm(FlaskForm):
    """Category create/edit form"""
    
    title = StringField('عنوان', validators=[
        DataRequired(message='عنوان الزامی است'),
        Length(max=255)
    ])
    
    slug = StringField('نامک (Slug)', validators=[
        Optional(),
        Length(max=255)
    ])
    
    description = TextAreaField('توضیحات')
    
    parent_id = SelectField('دسته‌بندی والد', coerce=int, validate_choice=False, validators=[Optional()])
    
    icon = StringField('آیکون', description='نام کلاس FontAwesome یا SVG')
    
    image = FileField('تصویر', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'webp', 'svg'], 'فقط تصاویر مجاز هستند')
    ])
    
    banner = FileField('بنر', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'فقط تصاویر مجاز هستند')
    ])
    
    color = StringField('رنگ', description='کد هگزادسیمال (مثال: #FF5733)')
    
    sort_order = IntegerField('ترتیب نمایش', default=0, validators=[Optional(), NumberRange(min=0)])
    
    is_active = BooleanField('فعال')
    is_menu = BooleanField('نمایش در منو')
    is_mega_menu = BooleanField('مگامنو')
    show_in_home = BooleanField('نمایش در صفحه اصلی')
    show_children = BooleanField('نمایش زیرشاخه‌ها')
    
    meta_title = StringField('Meta Title', validators=[Length(max=255)])
    meta_description = TextAreaField('Meta Description', validators=[Length(max=500)])
    
    submit = SubmitField('ذخیره')


# ==================== PAGE FORMS ====================

class PageForm(FlaskForm):
    """Page create/edit form"""
    
    title = StringField('عنوان', validators=[
        DataRequired(message='عنوان الزامی است'),
        Length(max=500)
    ])
    
    slug = StringField('نامک (Slug)', validators=[
        Optional(),
        Length(max=500)
    ])
    
    content = TextAreaField('محتوا')
    
    page_type = SelectField('نوع صفحه', default='default', choices=[
        ('default', 'پیش‌فرض'),
        ('home', 'صفحه اصلی'),
        ('about', 'درباره ما'),
        ('contact', 'تماس با ما'),
        ('faq', 'سوالات متداول'),
        ('terms', 'قوانین'),
        ('privacy', 'حریم خصوصی'),
        ('landing', 'صفحه فرود')
    ])
    
    template = SelectField('قالب', default='default', choices=[
        ('default', 'پیش‌فرض'),
        ('fullwidth', 'تمام عرض'),
        ('sidebar', 'سایدبار'),
        ('landing', 'صفحه فرود'),
        ('blank', 'خالی')
    ])
    
    show_in_menu = BooleanField('نمایش در منو')
    show_in_footer = BooleanField('نمایش در فوتر')
    show_breadcrumb = BooleanField('نمایش مسیر')
    show_sidebar = BooleanField('نمایش سایدبار')
    
    sort_order = IntegerField('ترتیب نمایش', default=0, validators=[Optional(), NumberRange(min=0)])
    
    is_active = BooleanField('فعال')
    
    meta_title = StringField('Meta Title', validators=[Length(max=255)])
    meta_description = TextAreaField('Meta Description', validators=[Length(max=500)])
    meta_keywords = StringField('Meta Keywords', validators=[Length(max=500)])
    
    canonical_url = StringField('Canonical URL', validators=[Optional(), URL()])
    robots = StringField('Robots', default='index, follow')
    
    submit = SubmitField('ذخیره')


# ==================== POST FORMS ====================

class PostForm(FlaskForm):
    """Post create/edit form"""
    
    title = StringField('عنوان', validators=[
        DataRequired(message='عنوان الزامی است'),
        Length(max=500)
    ])
    
    slug = StringField('نامک (Slug)', validators=[
        Optional(),
        Length(max=500)
    ])
    
    excerpt = TextAreaField('خلاصه', validators=[
        Optional(),
        Length(max=1000)
    ])
    
    content = TextAreaField('محتوا')
    
    featured_image = FileField('تصویر شاخص', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'فقط تصاویر مجاز هستند')
    ])
    
    category_id = SelectField('دسته‌بندی', coerce=int, validate_choice=False, validators=[Optional()])
    
    tags = StringField('برچسب‌ها', description='برچسب‌ها را با کاما جدا کنید')
    
    status = SelectField('وضعیت', default='draft', choices=[
        ('draft', 'پیش‌نویس'),
        ('published', 'منتشر شده'),
        ('scheduled', 'زمان‌بندی شده'),
        ('archived', 'آرشیو شده')
    ])
    
    published_at = DateTimeField('تاریخ انتشار', format='%Y-%m-%d %H:%M', validators=[Optional()])
    
    is_featured = BooleanField('مقاله ویژه')
    show_in_home = BooleanField('نمایش در صفحه اصلی')
    allow_comments = BooleanField('اجازه نظرات')
    
    meta_title = StringField('Meta Title', validators=[Length(max=255)])
    meta_description = TextAreaField('Meta Description', validators=[Length(max=500)])
    meta_keywords = StringField('Meta Keywords', validators=[Length(max=500)])
    
    submit = SubmitField('ذخیره')


# ==================== MENU FORMS ====================

class MenuForm(FlaskForm):
    """Menu create/edit form"""
    
    title = StringField('عنوان', validators=[
        DataRequired(message='عنوان الزامی است'),
        Length(max=255)
    ])
    
    url = StringField('لینک', validators=[
        Optional(),
        Length(max=500)
    ])
    
    icon = StringField('آیکون', description='کلاس FontAwesome (مثال: fa fa-home)')
    
    position = SelectField('موقعیت', default='header', choices=[
        ('header', 'هدر'),
        ('footer', 'فوتر'),
        ('mobile', 'موبایل'),
        ('sidebar', 'سایدبار')
    ])
    
    parent_id = SelectField('منوی والد', coerce=int, validate_choice=False, validators=[Optional()])
    
    target = SelectField('باز شدن لینک', default='_self', choices=[
        ('_self', 'در همان تب'),
        ('_blank', 'در تب جدید')
    ])
    
    no_follow = BooleanField('nofollow')
    
    badge_text = StringField('متن بج', validators=[Length(max=100)])
    badge_color = StringField('رنگ بج')
    
    is_mega_menu = BooleanField('مگامنو')
    
    is_active = BooleanField('فعال')
    show_logged_in = BooleanField('نمایش برای کاربران')
    show_guest = BooleanField('نمایش برای مهمانان')
    
    sort_order = IntegerField('ترتیب', default=0, validators=[Optional(), NumberRange(min=0)])
    
    submit = SubmitField('ذخیره')


# ==================== SLIDER/BANNER FORMS ====================

class SliderForm(FlaskForm):
    """Slider form"""
    
    title = StringField('عنوان', validators=[
        DataRequired(message='عنوان الزامی است')
    ])
    
    position = StringField('موقعیت')
    
    autoplay = BooleanField('حرکت خودکار')
    arrows = BooleanField('نمایش فلش‌ها')
    dots = BooleanField('نمایش نقاط')
    
    submit = SubmitField('ذخیره')


class BannerForm(FlaskForm):
    """Banner form"""
    
    title = StringField('عنوان', validators=[
        DataRequired(message='عنوان الزامی است')
    ])
    
    image = FileField('تصویر', validators=[
        FileRequired(message='تصویر الزامی است'),
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'فقط تصاویر مجاز هستند')
    ])
    
    url = StringField('لینک', validators=[Optional()])
    
    position = SelectField('موقعیت', default='home_top', choices=[
        ('home_top', 'بالای صفحه اصلی'),
        ('home_middle', 'میانه صفحه اصلی'),
        ('home_bottom', 'پایین صفحه اصلی'),
        ('sidebar', 'سایدبار')
    ])
    
    size = SelectField('اندازه', default='medium', choices=[
        ('small', 'کوچک'),
        ('medium', 'متوسط'),
        ('large', 'بزرگ'),
        ('wide', 'عریض')
    ])
    
    sort_order = IntegerField('ترتیب', default=0, validators=[Optional(), NumberRange(min=0)])
    
    start_date = DateTimeField('تاریخ شروع', format='%Y-%m-%d %H:%M', validators=[Optional()])
    end_date = DateTimeField('تاریخ پایان', format='%Y-%m-%d %H:%M', validators=[Optional()])
    
    is_active = BooleanField('فعال')
    
    submit = SubmitField('ذخیره')


# ==================== SETTINGS FORMS ====================

class SettingForm(FlaskForm):
    """Setting form"""
    
    value = StringField('مقدار')
    label = StringField('عنوان')
    description = TextAreaField('توضیحات')
    
    submit = SubmitField('ذخیره')


# ==================== MEDIA FORMS ====================

class MediaForm(FlaskForm):
    """Media upload form"""
    
    file = FileField('فایل', validators=[
        FileRequired(message='فایل الزامی است')
    ])
    
    folder = StringField('پوشه')
    alt = StringField('Alt')
    title = StringField('عنوان')
    
    submit = SubmitField('آپلود')


# ==================== CONTACT REPLY FORM ====================

class ContactReplyForm(FlaskForm):
    """Contact reply form"""
    
    reply_content = TextAreaField('پاسخ', validators=[
        DataRequired(message='پاسخ الزامی است')
    ])
    
    send_email = BooleanField('ارسال به ایمیل کاربر')
    
    submit = SubmitField('ارسال پاسخ')


# ==================== HELPER FUNCTIONS ====================

def populate_roles():
    """Populate role choices"""
    roles = Role.query.filter_by(is_deleted=False).all()
    return [(r.id, r.name) for r in roles]


def populate_categories():
    """Populate category choices"""
    categories = Category.query.filter_by(is_deleted=False, parent_id=None).all()
    return [(0, 'بدون دسته‌بندی')] + [(c.id, c.title) for c in categories]


def populate_brands():
    """Populate brand choices"""
    brands = Brand.query.filter_by(is_deleted=False).all()
    return [(0, 'بدون برند')] + [(b.id, b.name) for b in brands]


def populate_tags():
    """Populate tag choices"""
    tags = Tag.query.filter_by(is_deleted=False).all()
    return [(t.id, t.name) for t in tags]


def init_form_choices():
    """Initialize form choices after database setup"""
    pass  # This will be called after database initialization
