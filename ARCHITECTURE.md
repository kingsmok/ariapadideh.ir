# معماری پروژه Flask Pro

## 1. Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Mobile  │  │   Web    │  │   API    │  │ Telegram │  │  Admin   │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
└───────┼─────────────┼─────────────┼─────────────┼─────────────┼────────┘
        │             │             │             │             │
        └─────────────┴─────────────┴──────┬──────┴─────────────┘
                                          │
┌─────────────────────────────────────────┼────────────────────────────────┐
│                                    LOAD BALANCER                         │
│                              (Nginx / Traefik)                          │
└─────────────────────────────────────────┼────────────────────────────────┘
                                          │
┌─────────────────────────────────────────┼────────────────────────────────┐
│                               WSGI SERVER                                │
│                          (Gunicorn / uWSGI)                             │
└─────────────────────────────────────────┼────────────────────────────────┘
                                          │
┌─────────────────────────────────────────┼────────────────────────────────┐
│                                  FLASK APP                               │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                        BLUEPRINTS                                    │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │ │
│  │  │  public  │ │  user    │ │  admin   │ │   api    │ │  blog    │   │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘   │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                      CORE SERVICES                                   │ │
│  │  Auth │ Cache │ SEO │ Media │ Search │ Notification │ Logging      │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────┼────────────────────────────────┘
                                          │
┌───────────────────┬─────────────────────┼─────────────────────┬─────────┐
│     REDIS         │    POSTGRESQL       │      S3/MinIO       │ CELERY │
│   (Cache/Queue)   │    (Main DB)         │    (Media Files)    │ (Jobs) │
└───────────────────┴─────────────────────┴─────────────────────┴─────────┘
```

## 2. Clean Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                   │
│  Templates (Jinja2) │ Forms (WTForms) │ Views │ Assets  │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER                     │
│  Use Cases │ Services │ DTOs │ Validators │ Mappers    │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                     DOMAIN LAYER                         │
│  Models │ Entities │ Value Objects │ Enums │ Interfaces │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                 INFRASTRUCTURE LAYER                     │
│  Repositories │ External APIs │ File Storage │ Cache    │
└─────────────────────────────────────────────────────────┘
```

## 3. Database Schema Overview

### ERD (Entity Relationship Diagram)

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     users       │     │     roles       │     │    permissions │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id (PK)         │     │ id (PK)         │     │ id (PK)         │
│ email           │     │ name            │     │ name            │
│ password_hash   │     │ slug            │     │ slug            │
│ phone           │     │ permissions     │     │ description     │
│ first_name      │     │ created_at      │     │ created_at      │
│ last_name       │     └────────┬────────┘     └────────┬────────┘
│ avatar          │              │                       │
│ role_id (FK)────┼──────────────┼───────────────────────┘
│ is_active       │
│ is_verified     │     ┌─────────────────┐     ┌─────────────────┐
│ last_login      │     │   user_meta     │     │   addresses     │
│ created_at      │     ├─────────────────┤     ├─────────────────┤
│ updated_at      │     │ id (PK)         │     │ id (PK)         │
└────────┬────────┘     │ user_id (FK)────┼────▶│ user_id (FK)────┤
         │              │ meta_key        │     │ title           │
         │              │ meta_value      │     │ province        │
         │              └─────────────────┘     │ city            │
         │                                     │ address         │
┌────────┴────────┐                            │ postal_code     │
│     orders      │                            │ phone           │
├─────────────────┤                            │ is_default      │
│ id (PK)         │     ┌─────────────────┐     │ created_at      │
│ order_number    │     │  order_items    │     └─────────────────┘
│ user_id (FK)────┤     ├─────────────────┤
│ status          │     │ id (PK)         │
│ total_amount    │     │ order_id (FK)───┼──────▶
│ discount_amount │     │ product_id(FK)──┼────┐
│ shipping_amount │     │ quantity        │     │
│ payment_method  │     │ unit_price      │     │
│ payment_status  │     │ discount        │     │
│ shipping_address│     └─────────────────┘     │
│ tracking_code   │                             │
│ created_at      │     ┌─────────────────┐     │
│ updated_at      │     │   products      │     │
└─────────────────┘     ├─────────────────┤     │
                        │ id (PK)         │     │
┌─────────────────┐     │ sku             │     │
│    comments     │     │ title           │     │
├─────────────────┤     │ slug            │◀────┘
│ id (PK)         │     │ description     │
│ user_id (FK)────┼────▶│ short_desc      │
│ entity_type     │     │ price           │
│ entity_id       │     │ old_price       │
│ content         │     │ discount_percent│
│ rating          │     │ stock_quantity  │
│ is_approved     │     │ category_id(FK)─┼────┐
│ parent_id (FK)──┼──┐  │ brand_id (FK)──┼───┐│
│ created_at      │  │  │ images         │   ││
└─────────────────┘  │  │ is_active      │   ││
                     │  │ is_featured    │   ││
                     │  │ meta           │   ││
                     │  │ created_at     │   ││
                     │  │ updated_at     │   ││
                     │  └────────────────┘   ││
                     │                        ││
┌─────────────────┐ │  ┌─────────────────┐    ││
│   categories    │ │  │    brands       │    ││
├─────────────────┤ │  ├─────────────────┤    ││
│ id (PK)         │ │  │ id (PK)         │    ││
│ parent_id (FK)──┼─┼──│ name            │    ││
│ title           │ │  │ slug            │    ││
│ slug            │◀┼───┤ logo           │    ││
│ description     │ │  │ is_active      │    ││
│ icon            │ │  │ created_at     │    ││
│ image           │ │  └─────────────────┘    ││
│ banner          │ │                        ││
│ is_active       │ │  ┌─────────────────┐    ││
│ is_menu         │ │  │  category_meta  │    ││
│ sort_order      │ │  ├─────────────────┤    ││
│ meta_title      │ │  │ id (PK)         │    ││
│ meta_desc       │ │  │ category_id(FK)─│────┘│
│ created_at      │ │  │ meta_key        │      │
└─────────────────┘ │  │ meta_value      │      │
                    │  └─────────────────┘      │
┌─────────────────┐ │                            │
│     pages       │ │  ┌─────────────────┐       │
├─────────────────┤ │  │   product_meta  │       │
│ id (PK)         │ │  ├─────────────────┤       │
│ title           │ │  │ id (PK)         │       │
│ slug            │◀┼──│ product_id(FK)──│───────┘
│ content         │ │  │ meta_key        │
│ template        │ │  │ meta_value      │
│ is_active       │ │  └─────────────────┘
│ sort_order      │ │
│ page_type       │ │  ┌─────────────────┐
│ meta_title      │ │  │   wishlists     │
│ meta_desc       │ │  ├─────────────────┤
│ meta_image      │ │  │ id (PK)         │
│ canonical_url   │ │  │ user_id (FK)────┼───────▶
│ robots          │ │  │ product_id(FK)──│──┐
│ created_at      │ │  │ created_at      │  │
│ updated_at      │ │  └─────────────────┘  │
└─────────────────┘ │                       │
                    │  ┌─────────────────┐  │
┌─────────────────┐ │  │   comparisons   │  │
│   components    │ │  ├─────────────────┤  │
├─────────────────┤ │  │ id (PK)         │  │
│ id (PK)         │ │  │ user_id (FK)────┼──┐│
│ component_type  │ │  │ product_id(FK)──┼──┼─┤
│ title           │ │  │ created_at      │  ││
│ content         │ │  └─────────────────┘  ││
│ config          │ │                       ││
│ is_active       │ │  ┌─────────────────┐  ││
│ sort_order      │ │  │  cart_items     │  ││
│ position        │ │  ├─────────────────┤  ││
│ page_id (FK)────┼─┘  │ id (PK)         │  ││
└─────────────────┘     │ user_id (FK)────┼──┘│
                        │ session_id      │    │
┌─────────────────┐     │ product_id(FK)──┘    │
│    sliders      │     │ quantity        │    │
├─────────────────┤     │ created_at      │    │
│ id (PK)         │     │ updated_at      │    │
│ title           │     └─────────────────┘    │
│ subtitle        │                            │
│ image           │     ┌─────────────────┐    │
│ link            │     │   resumes       │    │
│ button_text     │     ├─────────────────┤    │
│ is_active       │     │ id (PK)         │    │
│ sort_order      │     │ user_id (FK)────┼────┘
│ position        │     │ full_name       │
│ start_date      │     │ email           │
│ end_date        │     │ phone           │
│ created_at      │     │ job_position    │
└─────────────────┘     │ file_path       │
                        │ cover_letter    │
┌─────────────────┐     │ status          │
│     menus       │     │ created_at      │
├─────────────────┤     │ updated_at      │
│ id (PK)         │     └─────────────────┘
│ title           │
│ slug            │     ┌─────────────────┐
│ url             │     │    contacts     │
│ icon            │     ├─────────────────┤
│ parent_id (FK)──┼──┐  │ id (PK)         │
│ sort_order      │  │  │ user_id (FK)────┼──────▶
│ is_active       │  │  │ name            │
│ is_mega_menu    │  │  │ email           │
│ mega_menu_config│  │  │ phone           │
│ position        │  │  │ subject         │
│ created_at      │  │  │ message         │
└─────────────────┘  │  │ ip_address      │
                     │  │ is_read         │
┌─────────────────┐  │  │ read_at         │
│     banners     │  │  │ created_at      │
├─────────────────┤  │  └─────────────────┘
│ id (PK)         │  │
│ title           │  │  ┌─────────────────┐
│ image           │  │  │     posts       │
│ link            │  │  ├─────────────────┤
│ position        │  │  │ id (PK)         │
│ size            │  │  │ title           │
│ is_active       │  │  │ slug            │◀──┐
│ sort_order      │  │  │ content         │   │
│ start_date      │  │  │ excerpt         │   │
│ end_date        │  │  │ featured_image  │   │
│ created_at      │  │  │ author_id (FK)─│──┐│
└─────────────────┘  │  │ category_id(FK)│──┼┐│
                     │  │ tags           │  ││
┌─────────────────┐  │  │ status         │  ││
│    settings     │  │  │ views          │  ││
├─────────────────┤  │  │ is_featured    │  ││
│ id (PK)         │  │  │ meta_title     │  ││
│ group           │  │  │ meta_desc      │  ││
│ key             │  │  │ meta_image     │  ││
│ value           │  │  │ canonical_url  │  ││
│ type            │  │  │ robots         │  ││
│ is_public       │  │  │ created_at     │  ││
│ description     │  │  │ updated_at     │  ││
│ updated_at      │  │  └────────────────┘  ││
└─────────────────┘  │                      ││
                    │  ┌─────────────────┐  ││
┌─────────────────┐  │  │    tags        │  ││
│   notifications │  │  ├─────────────────┤  ││
├─────────────────┤  │  │ id (PK)         │  ││
│ id (PK)         │  │  │ name            │  ││
│ user_id (FK)────┼──┘  │ slug            │◀─┼┘│
│ type            │     │ created_at      │   │
│ title           │     └─────────────────┘   │
│ message         │                          │
│ data            │     ┌─────────────────┐  │
│ is_read         │     │   post_tags     │  │
│ read_at         │     ├─────────────────┤  │
│ created_at      │     │ post_id (FK)    │◀─┘
└─────────────────┘     │ tag_id (FK)      │
                        └─────────────────┘
```

## 4. Component Hierarchy

```
Page Structure:
├── Header
│   ├── Top Bar (Settings)
│   ├── Logo
│   ├── Search Bar
│   ├── Mega Menu (Dynamic)
│   └── User Actions
├── Main Content
│   ├── Hero Section
│   ├── Components (CMS-driven)
│   │   ├── Slider
│   │   ├── Banner Grid
│   │   ├── Product Cards
│   │   ├── Category Grid
│   │   ├── Features
│   │   ├── FAQ
│   │   └── Custom HTML
│   └── Page-specific content
├── Sidebar (optional)
└── Footer
    ├── Footer Columns (Dynamic)
    ├── Footer Links
    ├── Social Links
    └── Copyright
```

## 5. Service Architecture

```python
# Dependency Injection Pattern
services/
├── __init__.py
├── container.py          # Service Container
├── auth_service.py       # Authentication
├── user_service.py       # User Management
├── product_service.py    # Product Operations
├── order_service.py      # Order Processing
├── cart_service.py       # Cart Management
├── search_service.py     # Search Engine
├── media_service.py       # Media Processing
├── seo_service.py        # SEO Operations
├── cache_service.py      # Caching Layer
├── notification_service.py # Notifications
├── export_service.py      # Data Export
└── webhook_service.py    # Webhook Handler
```

## 6. Caching Strategy

```
┌─────────────────────────────────────────────────────────┐
│                    CACHE LAYERS                         │
├─────────────────────────────────────────────────────────┤
│ L1: Memory Cache (In-App)    │ 5-60 seconds            │
│ L2: Redis Cache              │ 5-60 minutes            │
│ L3: Database Query Cache      │ Request-scoped          │
└─────────────────────────────────────────────────────────┘

Cache Keys Pattern:
- page:{slug}:data           → Page content
- category:{id}:products     → Category products
- product:{id}:details       → Product details
- menu:{position}:items      → Menu items
- settings:{group}           → Site settings
- user:{id}:profile          → User profile
- search:{query}:results     → Search results
```

## 7. File Upload Flow

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Client  │───▶│  WSGI    │───▶│  Media   │───▶│  S3/CDN  │
│  Upload  │    │  Server  │    │ Service  │    │  Storage │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                                     │
                                     ▼
                              ┌──────────┐
                              │  Redis   │
                              │  Queue   │
                              └──────────┘
                                     │
                                     ▼
                              ┌──────────┐
                              │  Celery  │
                              │  Worker  │
                              └──────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                ▼                ▼
             ┌──────────┐    ┌──────────┐    ┌──────────┐
             │  Resize  │    │ Compress │    │  WebP    │
             │  Images  │    │  Images  │    │ Convert  │
             └──────────┘    └──────────┘    └──────────┘
```

## 8. Security Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    SECURITY MIDDLEWARE                  │
├─────────────────────────────────────────────────────────┤
│ 1. Rate Limiting (Redis-based)                         │
│ 2. CSRF Protection (Flask-WTF)                         │
│ 3. XSS Sanitization (MarkupSafe + Bleach)               │
│ 4. SQL Injection Prevention (SQLAlchemy ORM)            │
│ 5. Password Hashing (Bcrypt/Argon2)                     │
│ 6. Session Security (Secure Cookies + HttpOnly)         │
│ 7. CORS Management                                      │
│ 8. Content Security Policy                             │
│ 9. Subresource Integrity (SRI)                          │
│ 10. Audit Logging                                       │
└─────────────────────────────────────────────────────────┘

Authentication Flow:
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Login   │───▶│ Validate │───▶│  Create  │───▶│  Set     │
│  Request │    │  Creds   │    │  Session │    │  Cookie  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

## 9. SEO Pipeline

```
┌─────────────────────────────────────────────────────────┐
│                    SEO PIPELINE                         │
├─────────────────────────────────────────────────────────┤
│ URL Rewriting → Meta Tags → Schema.org → Sitemap →     │
│ Robots.txt → Canonical → Hreflang → Speed → Mobile     │
└─────────────────────────────────────────────────────────┘

Meta Tags Generated:
- <title>
- <meta name="description">
- <meta name="keywords">
- <meta name="robots">
- <link rel="canonical">
- Open Graph (og:*)
- Twitter Cards
- JSON-LD Structured Data

Structured Data Types:
- Organization
- WebSite
- WebPage
- Product
- Article
- BreadcrumbList
- FAQPage
- LocalBusiness
```

## 10. Integration Points

```
External Services:
├── Price Aggregators (Torob, Emalls)
│   └── XML/JSON Feed Export
├── Telegram Bot
│   ├── Order Notifications
│   ├── Resume Alerts
│   └── Admin Commands
├── SMS Provider
│   └── OTP Verification
├── Email Provider
│   └── Transactional Emails
├── Payment Gateways
│   └── Zarinpal, IDPay, Mellat
├── Analytics
│   └── Google Analytics, Matomo
└── Error Tracking
    └── Sentry
```
