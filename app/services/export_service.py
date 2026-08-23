"""
Export Service - Generate Feeds for Price Aggregators
"""
from typing import List, Dict, Any
from datetime import datetime
from flask import current_app
from sqlalchemy import or_

from app.models import Product, Category


class ExportService:
    """Data Export Service for Price Aggregators"""
    
    @staticmethod
    def generate_torob_feed() -> str:
        """Generate XML feed for Torob"""
        
        site_url = current_app.config.get('SITE_URL', 'https://example.com')
        
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += '<products>\n'
        
        products = Product.query.filter(
            Product.is_active == True,
            Product.is_deleted == False,
            Product.stock_quantity > 0
        ).all()
        
        for product in products:
            xml += '  <product>\n'
            xml += f'    <id>{product.id}</id>\n'
            xml += f'    <name><![CDATA[{product.title}]]></name>\n'
            xml += f'    <url>{site_url}/product/{product.slug}</url>\n'
            xml += f'    <image>{product.main_image_url}</image>\n'
            xml += f'    <price>{int(product.current_price)}</price>\n'
            
            if product.old_price and product.old_price > product.current_price:
                xml += f'    <old_price>{int(product.old_price)}</old_price>\n'
            
            xml += f'    <availability>1</availability>\n'
            xml += f'    <category><![CDATA[{"|".join(product.category_names)}]]></category>\n'
            
            if product.brand:
                xml += f'    <brand><![CDATA[{product.brand.name}]]></brand>\n'
            
            xml += f'    <description><![CDATA[{product.short_description or ""}]]></description>\n'
            xml += f'    <sku>{product.sku or product.id}</sku>\n'
            
            xml += '  </product>\n'
        
        xml += '</products>'
        
        return xml
    
    @staticmethod
    def generate_emalls_feed() -> str:
        """Generate XML feed for Emalls"""
        
        site_url = current_app.config.get('SITE_URL', 'https://example.com')
        
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += '<catalog>\n'
        xml += '  <products>\n'
        
        products = Product.query.filter(
            Product.is_active == True,
            Product.is_deleted == False,
            Product.stock_quantity > 0
        ).all()
        
        for product in products:
            xml += '    <product>\n'
            xml += f'      <product_id>{product.id}</product_id>\n'
            xml += f'      <title><![CDATA[{product.title}]]></title>\n'
            xml += f'      <link>{site_url}/product/{product.slug}</link>\n'
            xml += f'      <image_link>{product.main_image_url}</image_link>\n'
            xml += f'      <price>{int(product.current_price)}</price>\n'
            
            if product.old_price:
                xml += f'      <sale_price>{int(product.old_price)}</sale_price>\n'
            
            xml += f'      <availability>in stock</availability>\n'
            xml += f'      <condition>new</condition>\n'
            
            if product.brand:
                xml += f'      <brand><![CDATA[{product.brand.name}]]></brand>\n'
            
            xml += f'      <description><![CDATA[{product.short_description or product.description or ""}]]></description>\n'
            
            if product.categories:
                xml += f'      <google_product_category><![CDATA[{product.categories[0].title}]]></google_product_category>\n'
            
            xml += '    </product>\n'
        
        xml += '  </products>\n'
        xml += '</catalog>'
        
        return xml
    
    @staticmethod
    def generate_json_feed() -> Dict[str, Any]:
        """Generate JSON feed for products"""
        
        products = Product.query.filter(
            Product.is_active == True,
            Product.is_deleted == False
        ).all()
        
        data = []
        for product in products:
            item = {
                'id': product.id,
                'title': product.title,
                'slug': product.slug,
                'price': product.current_price,
                'old_price': product.old_price,
                'in_stock': product.is_in_stock,
                'stock_quantity': product.stock_quantity,
                'image': product.main_image_url,
                'images': product.all_images,
                'categories': product.category_names,
                'brand': product.brand.name if product.brand else None,
                'sku': product.sku,
                'description': product.short_description,
                'specifications': product.get_specifications_dict(),
                'updated_at': product.updated_at.isoformat() if product.updated_at else None
            }
            data.append(item)
        
        return {
            'generated_at': datetime.utcnow().isoformat(),
            'count': len(data),
            'products': data
        }
    
    @staticmethod
    def generate_google_feed() -> str:
        """Generate XML feed for Google Merchant"""
        
        site_url = current_app.config.get('SITE_URL', 'https://example.com')
        
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += '<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0">\n'
        xml += '  <channel>\n'
        xml += f'    <title>{current_app.config.get("SITE_NAME", "فروشگاه")}</title>\n'
        xml += f'    <link>{site_url}</link>\n'
        xml += '    <description>محصولات فروشگاه</description>\n'
        
        products = Product.query.filter(
            Product.is_active == True,
            Product.is_deleted == False
        ).all()
        
        for product in products:
            xml += '    <item>\n'
            xml += f'      <g:id>{product.id}</g:id>\n'
            xml += f'      <g:title><![CDATA[{product.title}]]></g:title>\n'
            xml += f'      <g:link>{site_url}/product/{product.slug}</g:link>\n'
            xml += f'      <g:image_link>{product.main_image_url}</g:image_link>\n'
            xml += f'      <g:price>{int(product.current_price)} IRR</g:price>\n'
            
            if product.old_price:
                xml += f'      <g:sale_price>{int(product.old_price)} IRR</g:sale_price>\n'
            
            availability = 'in_stock' if product.is_in_stock else 'out_of_stock'
            xml += f'      <g:availability>{availability}</g:availability>\n'
            
            xml += '      <g:condition>new</g:condition>\n'
            
            if product.brand:
                xml += f'      <g:brand><![CDATA[{product.brand.name}]]></g:brand>\n'
            
            xml += f'      <g:description><![CDATA[{product.short_description or ""}]]></g:description>\n'
            
            if product.gtin:
                xml += f'      <g:gtin>{product.gtin}</g:gtin>\n'
            
            if product.mpn:
                xml += f'      <g:mpn>{product.mpn}</g:mpn>\n'
            
            xml += '    </item>\n'
        
        xml += '  </channel>\n'
        xml += '</rss>'
        
        return xml
    
    @staticmethod
    def generate_csv_feed() -> str:
        """Generate CSV feed for products"""
        
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'ID', 'Title', 'Slug', 'Price', 'Old Price', 'In Stock', 
            'Stock Qty', 'Image', 'Brand', 'Categories', 'SKU', 'Description'
        ])
        
        products = Product.query.filter(
            Product.is_active == True,
            Product.is_deleted == False
        ).all()
        
        for product in products:
            writer.writerow([
                product.id,
                product.title,
                product.slug,
                product.current_price,
                product.old_price,
                'Yes' if product.is_in_stock else 'No',
                product.stock_quantity,
                product.main_image_url,
                product.brand.name if product.brand else '',
                '|'.join(product.category_names),
                product.sku or '',
                (product.short_description or '')[:500]
            ])
        
        return output.getvalue()
