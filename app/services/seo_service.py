"""
SEO Service
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from flask import request, current_app
from sqlalchemy import or_

from app.extensions import db
from app.models import Product, Category, Post, Page, Setting


class SEOService:
    """SEO Operations Service"""
    
    @staticmethod
    def get_site_name() -> str:
        """Get site name from settings"""
        return Setting.get_value('general', 'site_name', 'فلاسک پرو')
    
    @staticmethod
    def get_site_url() -> str:
        """Get site URL"""
        return Setting.get_value('general', 'site_url', request.url_root.rstrip('/'))
    
    @staticmethod
    def get_default_seo() -> Dict[str, str]:
        """Get default SEO data"""
        return {
            'title': SEOService.get_site_name(),
            'description': Setting.get_value('seo', 'default_description', ''),
            'keywords': Setting.get_value('seo', 'default_keywords', ''),
            'og_image': Setting.get_value('seo', 'og_image', ''),
            'robots': 'index, follow'
        }
    
    @staticmethod
    def get_page_seo(page: Page) -> Dict[str, Any]:
        """Get SEO data for a page"""
        seo = {
            'title': page.meta_title or page.title,
            'description': page.meta_description or '',
            'keywords': page.meta_keywords or '',
            'og_image': page.meta_image or '',
            'canonical': page.canonical_url or f'{SEOService.get_site_url()}/{page.slug}',
            'robots': page.robots or 'index, follow'
        }
        
        seo['full_title'] = f"{seo['title']} | {SEOService.get_site_name()}"
        seo['og_type'] = 'website'
        seo['og_url'] = seo['canonical']
        seo['og_site_name'] = SEOService.get_site_name()
        
        return seo
    
    @staticmethod
    def get_product_seo(product: Product) -> Dict[str, Any]:
        """Get SEO data for a product"""
        seo = {
            'title': product.meta_title or product.title,
            'description': product.meta_description or product.short_description or '',
            'keywords': '',
            'og_image': product.main_image_url,
            'canonical': f'{SEOService.get_site_url()}/product/{product.slug}',
            'robots': 'index, follow'
        }
        
        seo['full_title'] = f"{seo['title']} | {SEOService.get_site_name()}"
        seo['og_type'] = 'product'
        seo['og_url'] = seo['canonical']
        
        # Product specific OG
        if product.brand:
            seo['og_brand'] = product.brand.name
        
        if product.is_in_stock:
            seo['og_availability'] = 'https://schema.org/InStock'
        else:
            seo['og_availability'] = 'https://schema.org/OutOfStock'
        
        seo['og_price'] = product.current_price
        seo['og_currency'] = 'IRR'
        
        # Schema.org data
        seo['schema'] = product.get_schema_data()
        
        return seo
    
    @staticmethod
    def get_category_seo(category: Category) -> Dict[str, Any]:
        """Get SEO data for a category"""
        seo = {
            'title': category.meta_title or category.title,
            'description': category.meta_description or category.description or '',
            'keywords': '',
            'og_image': category.image or '',
            'canonical': f'{SEOService.get_site_url()}/category/{category.slug}',
            'robots': 'index, follow'
        }
        
        seo['full_title'] = f"{seo['title']} | {SEOService.get_site_name()}"
        seo['og_type'] = 'website'
        seo['og_url'] = seo['canonical']
        
        return seo
    
    @staticmethod
    def get_post_seo(post: Post) -> Dict[str, Any]:
        """Get SEO data for a blog post"""
        seo = {
            'title': post.meta_title or post.title,
            'description': post.meta_description or post.excerpt or '',
            'keywords': ', '.join([t.name for t in post.tags]) if post.tags else '',
            'og_image': post.featured_image or '',
            'canonical': f'{SEOService.get_site_url()}/blog/{post.slug}',
            'robots': 'index, follow'
        }

        seo['full_title'] = f"{seo['title']} | {SEOService.get_site_name()}"
        seo['og_type'] = 'article'
        seo['og_url'] = seo['canonical']

        if post.author:
            seo['og_author'] = post.author.full_name

        if post.published_at:
            seo['article_published_time'] = post.published_at.isoformat()
            seo['article_modified_time'] = post.updated_at.isoformat()

        if post.category:
            seo['article_section'] = post.category.title

        # Tags as article:tag
        if post.tags:
            seo['og_tags'] = [t.name for t in post.tags]

        # Schema.org data
        seo['schema'] = post.get_schema_data()

        return seo
    
    @staticmethod
    def get_seo_data(page_type: str) -> Dict[str, Any]:
        """Get SEO data by page type"""
        if page_type == 'home':
            return {
                'title': Setting.get_value('seo', 'home_title', SEOService.get_site_name()),
                'description': Setting.get_value('seo', 'home_description', ''),
                'full_title': Setting.get_value('seo', 'home_title', SEOService.get_site_name()),
                'og_type': 'website'
            }
        
        return SEOService.get_default_seo()
    
    @staticmethod
    def generate_breadcrumbs(items: List[Dict[str, str]]) -> str:
        """Generate breadcrumb HTML"""
        html = '<nav aria-label="breadcrumb"><ol class="breadcrumb">'
        html += f'<li class="breadcrumb-item"><a href="{SEOService.get_site_url()}">صفحه اصلی</a></li>'
        
        for i, item in enumerate(items):
            if i == len(items) - 1:
                html += f'<li class="breadcrumb-item active" aria-current="page">{item["title"]}</li>'
            else:
                html += f'<li class="breadcrumb-item"><a href="{item["url"]}">{item["title"]}</a></li>'
        
        html += '</ol></nav>'
        return html
    
    @staticmethod
    def generate_sitemap() -> str:
        """Generate XML sitemap with image:image extension."""
        site_url = SEOService.get_site_url()

        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        # Note: image namespace enables Google Image sitemap ingestion
        xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        xml += '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'

        # Static pages
        static_pages = [
            {'loc': site_url, 'priority': '1.0', 'changefreq': 'daily'},
            {'loc': f'{site_url}/about', 'priority': '0.8', 'changefreq': 'monthly'},
            {'loc': f'{site_url}/contact', 'priority': '0.8', 'changefreq': 'monthly'},
            {'loc': f'{site_url}/faq', 'priority': '0.7', 'changefreq': 'monthly'},
            {'loc': f'{site_url}/blog', 'priority': '0.9', 'changefreq': 'daily'},
            {'loc': f'{site_url}/categories', 'priority': '0.7', 'changefreq': 'weekly'},
            {'loc': f'{site_url}/terms', 'priority': '0.5', 'changefreq': 'yearly'},
            {'loc': f'{site_url}/privacy', 'priority': '0.5', 'changefreq': 'yearly'},
        ]

        for page in static_pages:
            xml += '<url>\n'
            xml += f'  <loc>{page["loc"]}</loc>\n'
            xml += f'  <changefreq>{page["changefreq"]}</changefreq>\n'
            xml += f'  <priority>{page["priority"]}</priority>\n'
            xml += '</url>\n'

        # Products (with image:image)
        products = Product.query.filter_by(is_active=True, is_deleted=False).limit(1000).all()
        for product in products:
            xml += '<url>\n'
            xml += f'  <loc>{site_url}/product/{product.slug}</loc>\n'
            xml += '  <changefreq>weekly</changefreq>\n'
            xml += '  <priority>0.8</priority>\n'
            if product.updated_at:
                xml += f'  <lastmod>{product.updated_at.strftime("%Y-%m-%d")}</lastmod>\n'
            # Image extension — helps Google Image Search index product images
            if product.main_image_url:
                xml += '  <image:image>\n'
                xml += f'    <image:loc>{product.main_image_url}</image:loc>\n'
                xml += f'    <image:title>{product.title}</image:title>\n'
                xml += '  </image:image>\n'
            xml += '</url>\n'

        # Categories
        categories = Category.query.filter_by(is_active=True, is_deleted=False).all()
        for category in categories:
            xml += '<url>\n'
            xml += f'  <loc>{site_url}/category/{category.slug}</loc>\n'
            xml += '  <changefreq>daily</changefreq>\n'
            xml += '  <priority>0.7</priority>\n'
            if category.updated_at:
                xml += f'  <lastmod>{category.updated_at.strftime("%Y-%m-%d")}</lastmod>\n'
            xml += '</url>\n'

        # Posts
        posts = Post.query.filter_by(status='published', is_active=True, is_deleted=False).limit(500).all()
        for post in posts:
            xml += '<url>\n'
            xml += f'  <loc>{site_url}/blog/{post.slug}</loc>\n'
            xml += '  <changefreq>weekly</changefreq>\n'
            xml += '  <priority>0.6</priority>\n'
            lastmod = post.updated_at or post.published_at
            if lastmod:
                xml += f'  <lastmod>{lastmod.strftime("%Y-%m-%d")}</lastmod>\n'
            # Article image
            if post.featured_image:
                xml += '  <image:image>\n'
                xml += f'    <image:loc>{post.featured_image}</image:loc>\n'
                xml += f'    <image:title>{post.title}</image:title>\n'
                xml += '  </image:image>\n'
            xml += '</url>\n'

        xml += '</urlset>'

        return xml
    
    @staticmethod
    def generate_json_ld(schema_type: str, data: Dict) -> str:
        """Generate JSON-LD script tag"""
        import json
        
        json_ld = {
            '@context': 'https://schema.org',
            **data
        }
        
        return f'<script type="application/ld+json">{json.dumps(json_ld, ensure_ascii=False)}</script>'
    
    @staticmethod
    def generate_og_tags(seo: Dict[str, Any]) -> str:
        """Generate Open Graph meta tags"""
        tags = []
        
        tags.append(f'<meta property="og:title" content="{seo.get("full_title", seo.get("title", ""))}">')
        
        if seo.get('description'):
            tags.append(f'<meta property="og:description" content="{seo["description"]}">')
        
        if seo.get('og_image'):
            tags.append(f'<meta property="og:image" content="{seo["og_image"]}">')
        
        tags.append(f'<meta property="og:url" content="{seo.get("canonical", request.url)}">')
        tags.append(f'<meta property="og:type" content="{seo.get("og_type", "website")}">')
        tags.append(f'<meta property="og:site_name" content="{SEOService.get_site_name()}">')
        
        if seo.get('og_price'):
            tags.append(f'<meta property="product:price:amount" content="{seo["og_price"]}">')
            tags.append(f'<meta property="product:price:currency" content="{seo.get("og_currency", "IRR")}">')
        
        return '\n'.join(tags)
    
    @staticmethod
    def generate_twitter_cards(seo: Dict[str, Any]) -> str:
        """Generate Twitter Card meta tags"""
        tags = []
        
        tags.append('<meta name="twitter:card" content="summary_large_image">')
        tags.append(f'<meta name="twitter:title" content="{seo.get("full_title", seo.get("title", ""))}">')
        
        if seo.get('description'):
            tags.append(f'<meta name="twitter:description" content="{seo["description"]}">')
        
        if seo.get('og_image'):
            tags.append(f'<meta name="twitter:image" content="{seo["og_image"]}">')
        
        return '\n'.join(tags)
