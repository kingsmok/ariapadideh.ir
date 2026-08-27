"""
B2B Agency Models for Rahsa Dev (rahsadev.ir)
File: app/models/agency.py
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from app.extensions import db
from app.models.base import BaseModel, TimestampMixin, SoftDeleteMixin, ActiveMixin, SortOrderMixin


class ServiceCatalog(BaseModel, TimestampMixin, SoftDeleteMixin, ActiveMixin, SortOrderMixin):
    """Core B2B Agency Service Offerings"""
    __tablename__ = 'service_catalog'

    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)
    icon_svg = db.Column(db.Text, nullable=True)
    short_desc = db.Column(db.Text, nullable=False)
    full_desc = db.Column(db.Text, nullable=True)
    features_json = db.Column(db.JSON, nullable=True, default=[])
    tech_stack_json = db.Column(db.JSON, nullable=True, default=[])
    starting_price_toman = db.Column(db.BigInteger, nullable=True)

    portfolio_items = relationship('PortfolioCaseStudies', back_populates='service', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'icon_svg': self.icon_svg or '🎨',
            'short_desc': self.short_desc,
            'features': self.features_json or [],
            'tech_stack': self.tech_stack_json or [],
            'starting_price': f'{int(self.starting_price_toman):,} تومان' if self.starting_price_toman else 'استعلام قیمت'
        }


class PortfolioCaseStudies(BaseModel, TimestampMixin, SoftDeleteMixin, ActiveMixin, SortOrderMixin):
    """B2B Proof of Work & Case Studies with Measurable ROI Metrics"""
    __tablename__ = 'portfolio_casestudies'

    client_name = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service_catalog.id'), nullable=True, index=True)
    thumbnail_url = db.Column(db.String(500), nullable=False)
    challenge_desc = db.Column(db.Text, nullable=False)
    solution_json = db.Column(db.JSON, nullable=True, default=[])
    results_roi_json = db.Column(db.JSON, nullable=True, default={
        'performance_gain': '+250%',
        'seo_traffic': '+180%',
        'load_time': '0.8s'
    })
    live_url = db.Column(db.String(500), nullable=True)
    is_featured = db.Column(db.Boolean, default=True)

    service = relationship('ServiceCatalog', back_populates='portfolio_items')

    def to_dict(self):
        return {
            'id': self.id,
            'client_name': self.client_name,
            'title': self.title,
            'slug': self.slug,
            'service_name': self.service.title if self.service else 'پروژه سفارشی',
            'thumbnail_url': self.thumbnail_url,
            'challenge_desc': self.challenge_desc,
            'solution': self.solution_json or [],
            'results_roi': self.results_roi_json or {},
            'live_url': self.live_url or '#'
        }


class ConsultationLeads(BaseModel, TimestampMixin):
    """Sales CRM for Incoming B2B Inquiries & Project Proposals"""
    __tablename__ = 'consultation_leads'

    client_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50), nullable=False, index=True)
    email = db.Column(db.String(255), nullable=True)
    service_requested = db.Column(db.String(255), nullable=False)
    budget_range = db.Column(db.String(100), nullable=True)
    project_description = db.Column(db.Text, nullable=False)
    status = db.Column(
        Enum('new', 'contacted', 'proposal_sent', 'closed_won', 'closed_lost', name='lead_status_enum'),
        default='new',
        nullable=False,
        index=True
    )
    ip_address = db.Column(db.String(45), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'client_name': self.client_name,
            'phone': self.phone,
            'service_requested': self.service_requested,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ''
        }
