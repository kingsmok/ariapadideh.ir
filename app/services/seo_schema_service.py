"""
SEO Schema Service — generates JSON-LD structured data.

This service is the central place for all Schema.org markup. It produces
validated JSON-LD that Google can consume for rich results.

Why a separate service? Because:
  1. Base.html needs global schemas (Organization, WebSite) that apply
     to every page. We can't put them in SEOService which is called
     per-route.
  2. Per-page schemas (Product, Article, FAQPage, BreadcrumbList)
     belong next to the data they describe.
  3. The output is always valid JSON-LD with @context set to
     https://schema.org — Google Search Central requires this.
"""
import json
from typing import Optional, List, Dict, Any
from flask import current_app, url_for, request
from sqlalchemy import desc

from app.extensions import db
from app.models import (
    Product, Category, Post, Page, Brand, Tag,
    Setting
)
from app.utils.helpers import slugify


# ==================== Helpers ====================

def _site_url() -> str:
    """Get absolute site URL — never trust request.url_root alone."""
    return Setting.get_value('general', 'site_url', request.url_root.rstrip('/'))


def _site_name() -> str:
    return Setting.get_value('general', 'site_name', 'رهسا دیو')


def _logo_url() -> str:
    """Return absolute URL of the site logo, or empty string."""
    logo = Setting.get_value('general', 'logo', '')
    if not logo:
        return ''
    if logo.startswith('http'):
        return logo
    return f"{_site_url()}{logo if logo.startswith('/') else '/' + logo}"


def _social_links() -> List[str]:
    """Return sameAs URLs from settings (social profiles for E-E-A-T)."""
    links = []
    for key in ('social_telegram', 'social_instagram', 'social_linkedin',
                'social_twitter', 'social_github', 'social_youtube'):
        val = Setting.get_value('social', key.replace('social_', ''), '')
        if val and val.strip():
            url = val.strip()
            if not url.startswith('http'):
                url = 'https://' + url
            links.append(url)
    return links


def _dump(payload: Dict[str, Any]) -> str:
    """Serialize JSON-LD safely. ensure_ascii=False so Persian is preserved."""
    return json.dumps(payload, ensure_ascii=False, separators=(',', ':'))


def _script(payload: Dict[str, Any]) -> str:
    """Wrap a JSON-LD payload in a <script> tag."""
    return f'<script type="application/ld+json">{_dump(payload)}</script>'


# ==================== Global schemas (inject on every page) ====================

def get_organization_schema() -> str:
    """
    Organization + LocalBusiness schema — one of the most important
    pieces of E-E-A-T markup. Without it Google cannot build a
    Knowledge Panel, and the site will not appear in local searches
    for «توسعه نرم‌افزار شیراز» etc.

    Two @types are merged into one @id to avoid the "duplicate
    organization" warnings in Search Console.
    """
    site_url = _site_url()
    site_name = _site_name()
    logo = _logo_url()

    org_id = f"{site_url}/#organization"
    local_id = f"{site_url}/#localbusiness"

    # Description from settings, with a sensible default
    description = Setting.get_value(
        'seo', 'organization_description',
        'رهسا دیو — آتلیه تخصصی توسعه نرم‌افزار سازمانی، طراحی وب و ربات‌های هوشمند'
    )

    # Build telephone list
    phones = []
    for key in ('phone_primary', 'phone_secondary'):
        val = Setting.get_value('contact', key, '')
        if val and val.strip():
            phones.append(val.strip())

    # Address
    province = Setting.get_value('contact', 'province', 'فارس')
    city = Setting.get_value('contact', 'city', 'شیراز')
    street = Setting.get_value('contact', 'address', '')
    postal = Setting.get_value('contact', 'postal_code', '')

    address = {
        '@type': 'PostalAddress',
        'addressCountry': 'IR',
        'addressRegion': province,
        'addressLocality': city,
    }
    if street:
        address['streetAddress'] = street
    if postal:
        address['postalCode'] = postal

    # Geo coordinates (optional but valuable for local SEO)
    geo = {}
    lat = Setting.get_value('contact', 'latitude', '')
    lng = Setting.get_value('contact', 'longitude', '')
    if lat and lng:
        try:
            geo = {
                '@type': 'GeoCoordinates',
                'latitude': float(lat),
                'longitude': float(lng),
            }
        except (ValueError, TypeError):
            geo = {}

    # Founding date (optional)
    founding_date = Setting.get_value('general', 'founding_date', '')

    # Organization block
    organization = {
        '@context': 'https://schema.org',
        '@type': 'Organization',
        '@id': org_id,
        'name': site_name,
        'alternateName': Setting.get_value('seo', 'alternate_name', 'RahsaDev'),
        'url': site_url,
        'description': description,
        'inLanguage': 'fa-IR',
    }

    if logo:
        organization['logo'] = {
            '@type': 'ImageObject',
            'url': logo,
        }
    else:
        # Fallback to favicon if no logo set
        organization['logo'] = f"{site_url}/static/favicon.ico"

    if phones:
        organization['telephone'] = phones if len(phones) > 1 else phones[0]

    email = Setting.get_value('contact', 'email', '')
    if email:
        organization['email'] = email

    same_as = _social_links()
    if same_as:
        organization['sameAs'] = same_as

    if founding_date:
        organization['foundingDate'] = founding_date

    # LocalBusiness block (extends Organization)
    local_business = {
        '@type': ['LocalBusiness', 'Organization'],
        '@id': local_id,
        'parentOrganization': {'@id': org_id},
        'name': site_name,
        'url': site_url,
        'description': description,
        'address': address,
    }
    if phones:
        local_business['telephone'] = phones[0]
    if email:
        local_business['email'] = email
    if geo:
        local_business['geo'] = geo
    if same_as:
        local_business['sameAs'] = same_as

    # Price range (helps Google understand the business tier)
    price_range = Setting.get_value('general', 'price_range', '$$')
    if price_range:
        local_business['priceRange'] = price_range

    # Opening hours
    opening_hours = Setting.get_value('contact', 'opening_hours', '')
    if opening_hours:
        local_business['openingHours'] = [opening_hours]

    return _script(organization) + _script(local_business)


def get_website_schema() -> str:
    """
    WebSite schema with SearchAction — enables the Google Sitelinks
    Searchbox. When a user types a query, they see a search bar that
    searches YOUR site directly. This is one of the highest-ROI SEO
    features available.
    """
    site_url = _site_url()
    site_name = _site_name()

    website = {
        '@context': 'https://schema.org',
        '@type': 'WebSite',
        '@id': f"{site_url}/#website",
        'name': site_name,
        'url': site_url,
        'inLanguage': 'fa-IR',
        'publisher': {'@id': f"{site_url}/#organization"},
        'potentialAction': {
            '@type': 'SearchAction',
            'target': {
                '@type': 'EntryPoint',
                'urlTemplate': f"{site_url}/search?q={{search_term_string}}",
            },
            'query-input': 'required name=search_term_string',
        },
    }

    # Optional: alternateName for English search
    alt_name = Setting.get_value('seo', 'alternate_name', '')
    if alt_name:
        website['alternateName'] = alt_name

    return _script(website)


# ==================== Page-specific schemas ====================

def get_breadcrumb_schema(items: List[Dict[str, str]]) -> str:
    """
    BreadcrumbList schema — Google shows breadcrumbs in search results
    instead of raw URLs, which dramatically increases CTR.

    Args:
        items: list of dicts with 'name' and 'url' (absolute URL).
               The last item should be the current page (no link).
    """
    if not items:
        return ''

    schema = {
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        'itemListElement': [
            {
                '@type': 'ListItem',
                'position': i + 1,
                'name': item['name'],
                'item': item['url'],
            }
            for i, item in enumerate(items)
        ],
    }

    return _script(schema)


def get_faq_schema(faqs: List[Any]) -> str:
    """
    FAQPage schema — enables FAQ rich results in Google.
    Each FAQ should have `question` and `answer` (or `q`/`a`) attrs.
    """
    if not faqs:
        return ''

    schema = {
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        'mainEntity': [],
    }

    for faq in faqs:
        # Accept both `question`/`answer` and `q`/`a`
        question = getattr(faq, 'question', None) or getattr(faq, 'q', '')
        answer = getattr(faq, 'answer', None) or getattr(faq, 'a', '')
        if not question or not answer:
            continue

        # If answer is HTML, strip tags for schema (Google disallows HTML in FAQ)
        if '<' in str(answer):
            import re
            answer = re.sub(r'<[^>]+>', ' ', str(answer))
            answer = re.sub(r'\s+', ' ', answer).strip()

        schema['mainEntity'].append({
            '@type': 'Question',
            'name': question,
            'acceptedAnswer': {
                '@type': 'Answer',
                'text': answer,
            },
        })

    if not schema['mainEntity']:
        return ''

    return _script(schema)


def get_product_schema(product: Product) -> str:
    """
    Product schema with Offer, AggregateRating, and Brand.
    The most important schema for e-commerce pages — drives product
    cards in Google Search with price, availability, and rating.
    """
    if not product or product.is_deleted or not product.is_active:
        return ''

    site_url = _site_url()
    product_url = f"{site_url}/product/{product.slug}"

    schema = {
        '@context': 'https://schema.org',
        '@type': 'Product',
        'name': product.title,
        'description': product.short_description or (
            product.description[:160] if product.description else ''
        ),
        'url': product_url,
        'sku': product.sku or '',
        'image': product.main_image_url or '',
    }

    if product.brand:
        schema['brand'] = {
            '@type': 'Brand',
            'name': product.brand.name,
        }

    # Category (helps Google understand vertical)
    if product.categories:
        schema['category'] = product.categories[0].title

    # Offer
    if product.current_price:
        offer = {
            '@type': 'Offer',
            'price': str(int(product.current_price)),
            'priceCurrency': 'IRR',
            'url': product_url,
            'seller': {
                '@type': 'Organization',
                '@id': f"{site_url}/#organization",
                'name': _site_name(),
            },
        }
        if product.is_in_stock:
            offer['availability'] = 'https://schema.org/InStock'
        else:
            offer['availability'] = 'https://schema.org/OutOfStock'

        # Price valid until
        offer['priceValidUntil'] = (
            (product.updated_at.replace(month=12, day=31).strftime('%Y-%m-%d'))
            if product.updated_at else '2099-12-31'
        )
        schema['offers'] = offer

    # Aggregate rating (only if real data exists)
    if product.rating_avg and product.rating_avg > 0 and product.rating_count and product.rating_count > 0:
        schema['aggregateRating'] = {
            '@type': 'AggregateRating',
            'ratingValue': str(product.rating_avg),
            'bestRating': '5',
            'worstRating': '1',
            'ratingCount': str(product.rating_count),
        }

    return _script(schema)


def get_article_schema(post: Post) -> str:
    """
    BlogPosting schema — better than generic Article for blog content.
    Includes author, publisher, dates, image, and article section.
    """
    if not post or post.status != 'published':
        return ''

    site_url = _site_url()
    post_url = f"{site_url}/blog/{post.slug}"

    schema = {
        '@context': 'https://schema.org',
        '@type': 'BlogPosting',
        '@id': f"{post_url}#article",
        'headline': post.title,
        'description': post.excerpt or (post.content[:160] if post.content else ''),
        'url': post_url,
        'inLanguage': 'fa-IR',
        'isFamilyFriendly': True,
    }

    if post.featured_image:
        schema['image'] = {
            '@type': 'ImageObject',
            'url': post.featured_image,
        }

    if post.published_at:
        schema['datePublished'] = post.published_at.isoformat()
    if post.updated_at:
        schema['dateModified'] = post.updated_at.isoformat()

    # Author
    if post.author:
        author_id = f"{site_url}/#person-{post.author.id}"
        schema['author'] = {
            '@type': 'Person',
            '@id': author_id,
            'name': post.author.full_name,
            'url': f"{site_url}/about",
        }
        if post.author.avatar:
            schema['author']['image'] = post.author.avatar

    # Publisher (mandatory for BlogPosting)
    schema['publisher'] = {
        '@type': 'Organization',
        '@id': f"{site_url}/#organization",
        'name': _site_name(),
    }
    logo = _logo_url()
    if logo:
        schema['publisher']['logo'] = {
            '@type': 'ImageObject',
            'url': logo,
        }

    if post.category:
        schema['articleSection'] = post.category.title

    # Keywords
    if post.tags:
        schema['keywords'] = ', '.join([t.name for t in post.tags])

    # Word count (helps Google assess content quality)
    if post.content:
        word_count = len(post.content.split())
        if word_count > 0:
            schema['wordCount'] = str(word_count)

    return _script(schema)


def get_service_schema(category: Category) -> str:
    """
    Service schema — Google Service rich results.
    Each service category (ERP, Web Design, Smart Bots) becomes a
    Service provider entry, which is critical for B2B sites.
    """
    if not category or category.is_deleted or not category.is_active:
        return ''

    site_url = _site_url()
    cat_url = f"{site_url}/category/{category.slug}"

    # Get product count (useful signal)
    product_count = 0
    try:
        product_count = len(category.products) if hasattr(category, 'products') else 0
    except Exception:
        pass

    schema = {
        '@context': 'https://schema.org',
        '@type': 'Service',
        'serviceType': category.title,
        'name': category.title,
        'description': category.description or f'ارائه خدمات {category.title}',
        'url': cat_url,
        'provider': {
            '@type': 'Organization',
            '@id': f"{site_url}/#organization",
            'name': _site_name(),
        },
        'areaServed': {
            '@type': 'Country',
            'name': 'Iran',
        },
        'availableLanguage': ['fa', 'fa-IR', 'en'],
    }

    if category.image:
        schema['image'] = category.image

    if product_count > 0:
        schema['offers'] = {
            '@type': 'AggregateOffer',
            'priceCurrency': 'IRR',
            'offerCount': str(product_count),
        }

    return _script(schema)


def get_person_schema(person_name: str, person_role: str = '',
                      person_image: str = '', person_url: str = '') -> str:
    """
    Person schema — used for team members (E-E-A-T).
    """
    if not person_name:
        return ''

    site_url = _site_url()

    schema = {
        '@context': 'https://schema.org',
        '@type': 'Person',
        'name': person_name,
        'worksFor': {
            '@type': 'Organization',
            '@id': f"{site_url}/#organization",
            'name': _site_name(),
        },
    }

    if person_role:
        schema['jobTitle'] = person_role
    if person_image:
        schema['image'] = person_image
    if person_url:
        schema['url'] = person_url
    else:
        schema['url'] = f"{site_url}/about"

    # Add sameAs from settings if available
    same_as = _social_links()
    if same_as:
        schema['sameAs'] = same_as

    return _script(schema)
