# ساختار فولدرهای پروژه

```
flask_pro/
├── app/
│   ├── __init__.py                 # Flask App Factory
│   ├── config.py                   # Configuration Classes
│   ├── extensions.py               # Flask Extensions
│   │
│   ├── blueprints/                 # Blueprint Modules
│   │   ├── __init__.py
│   │   ├── public/                 # Public Pages
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   ├── forms.py
│   │   │   └── templates/
│   │   │       └── public/
│   │   ├── user/                   # User Panel
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   ├── forms.py
│   │   │   └── templates/
│   │   │       └── user/
│   │   ├── admin/                  # Admin Panel
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   ├── forms.py
│   │   │   ├── decorators.py
│   │   │   └── templates/
│   │   │       └── admin/
│   │   ├── api/                    # REST API
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   ├── serializers.py
│   │   │   └── validators.py
│   │   └── blog/                   # Blog/CMS
│   │       ├── __init__.py
│   │       ├── routes.py
│   │       ├── forms.py
│   │       └── templates/
│   │           └── blog/
│   │
│   ├── models/                    # SQLAlchemy Models
│   │   ├── __init__.py
│   │   ├── base.py               # Base Model
│   │   ├── user.py               # User & Auth
│   │   ├── product.py            # Products
│   │   ├── category.py           # Categories
│   │   ├── order.py              # Orders
│   │   ├── content.py            # Pages, Posts
│   │   ├── menu.py               # Menus
│   │   ├── media.py              # Media Files
│   │   ├── setting.py            # Settings
│   │   ├── seo.py                # SEO Data
│   │   └── notification.py       # Notifications
│   │
│   ├── services/                 # Business Logic
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── product_service.py
│   │   ├── order_service.py
│   │   ├── cart_service.py
│   │   ├── search_service.py
│   │   ├── media_service.py
│   │   ├── seo_service.py
│   │   ├── cache_service.py
│   │   ├── notification_service.py
│   │   ├── export_service.py
│   │   └── telegram_service.py
│   │
│   ├── utils/                     # Utilities
│   │   ├── __init__.py
│   │   ├── decorators.py
│   │   ├── helpers.py
│   │   ├── validators.py
│   │   ├── generators.py
│   │   ├── security.py
│   │   ├── seo.py
│   │   └── responses.py
│   │
│   ├── templates/                 # Jinja2 Templates
│   │   ├── base.html
│   │   ├── macros/
│   │   │   ├── forms.html
│   │   │   ├── cards.html
│   │   │   ├── pagination.html
│   │   │   ├── breadcrumbs.html
│   │   │   ├── seo.html
│   │   │   └── icons.html
│   │   ├── components/
│   │   │   ├── header.html
│   │   │   ├── footer.html
│   │   │   ├── sidebar.html
│   │   │   ├── slider.html
│   │   │   ├── banner.html
│   │   │   └── search.html
│   │   └── errors/
│   │       ├── 404.html
│   │       └── 500.html
│   │
│   ├── static/                   # Static Files
│   │   ├── css/
│   │   │   ├── main.css
│   │   │   ├── admin.css
│   │   │   └── components/
│   │   ├── js/
│   │   │   ├── main.js
│   │   │   ├── admin.js
│   │   │   └── components/
│   │   ├── images/
│   │   ├── fonts/
│   │   └── uploads/              # User Uploads
│   │
│   └── errors/                   # Error Handlers
│       ├── __init__.py
│       └── handlers.py
│
├── migrations/                    # Alembic Migrations
│   ├── versions/
│   └── env.py
│
├── tests/                        # Unit Tests
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_models/
│   ├── test_services/
│   └── test_routes/
│
├── celery/                       # Celery Tasks
│   ├── __init__.py
│   ├── celery_app.py
│   └── tasks/
│
├── docker/                       # Docker Files
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── nginx/
│       └── default.conf
│
├── docs/                         # Documentation
│
├── .env                          # Environment Variables
├── .env.example
├── .gitignore
├── requirements.txt
├── requirements-dev.txt
├── requirements-prod.txt
├── run.py                        # Application Runner
├── manage.py                     # Management Commands
└── README.md
```

## ساختار دیتابیس - مدل‌ها

```
┌────────────────────────────────────────────────────────────────────────┐
│                           MODEL RELATIONSHIPS                          │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  User (1)─────(N) Address                                               │
│    │                                                                      │
│    ├──(N) Order                                                         │
│    ├──(N) OrderItem                                                     │
│    ├──(N) CartItem                                                      │
│    ├──(N) Wishlist                                                      │
│    ├──(N) Comparison                                                    │
│    ├──(N) Resume                                                        │
│    ├──(N) Contact                                                       │
│    ├──(N) Comment                                                       │
│    ├──(N) Notification                                                  │
│    └──(1) Role ──(N) Permission                                         │
│                                                                         │
│  Category (1)────(N) Product                                            │
│    │                                                                      │
│    ├──(1) Parent ──(N) Child (Self-referential)                         │
│    ├──(N) CategoryMeta                                                   │
│    └──(N) Product                                                       │
│                                                                         │
│  Product (1)────(N) ProductMeta                                        │
│    │            ──(N) ProductImage                                      │
│    │            ──(N) OrderItem                                          │
│    │            ──(N) CartItem                                          │
│    │            ──(N) Wishlist                                          │
│    │            ──(N) Comparison                                        │
│    │            ──(N) Comment                                           │
│    ├──(1) Brand                                                         │
│    └──(N) Category                                                      │
│                                                                         │
│  Page (1)─────(N) Component                                             │
│                                                                         │
│  Post (1)─────(N) PostTag ──(N) Tag                                    │
│    │            ──(N) Comment                                           │
│    └──(1) Category                                                       │
│                                                                         │
│  Menu (1)─────(N) Child (Self-referential)                            │
│                                                                         │
│  Slider (1)────(N) SliderItem                                          │
│                                                                         │
│  Setting (N) Grouped by 'group' column                                 │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```
