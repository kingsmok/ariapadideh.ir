"""
Base Model - Abstract Base Class for all models
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import inspect, event
from sqlalchemy.orm import declared_attr
from flask_sqlalchemy.query import Query as FlaskQuery
from app.extensions import db


class BaseModel(db.Model):
    """Abstract base model with common fields and methods"""
    
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Soft delete
    deleted_at = db.Column(db.DateTime, nullable=True, index=True)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    
    @classmethod
    def find_by_id(cls, id: int):
        """Find record by ID"""
        return cls.query.filter_by(id=id, is_deleted=False).first()
    
    @classmethod
    def find_by_ids(cls, ids: List[int]):
        """Find records by IDs"""
        return cls.query.filter(cls.id.in_(ids), cls.is_deleted == False).all()
    
    @classmethod
    def get_all(cls):
        """Get all non-deleted records"""
        return cls.query.filter_by(is_deleted=False).all()
    
    @classmethod
    def get_paginated(cls, page: int = 1, per_page: int = 20, **filters):
        """Get paginated results"""
        query = cls.query.filter_by(is_deleted=False, **filters)
        return query.paginate(page=page, per_page=per_page, error_out=False)
    
    def save(self) -> 'BaseModel':
        """Save record to database"""
        db.session.add(self)
        db.session.commit()
        return self
    
    def delete(self, hard: bool = False) -> bool:
        """Soft delete record"""
        if hard:
            db.session.delete(self)
        else:
            self.is_deleted = True
            self.deleted_at = datetime.utcnow()
        db.session.commit()
        return True
    
    def restore(self) -> 'BaseModel':
        """Restore soft-deleted record"""
        self.is_deleted = False
        self.deleted_at = None
        db.session.commit()
        return self
    
    def to_dict(self, exclude: List[str] = None) -> Dict[str, Any]:
        """Convert model to dictionary"""
        exclude = exclude or []
        result = {}
        
        for column in self.__table__.columns:
            if column.name not in exclude:
                value = getattr(self, column.name)
                if isinstance(value, datetime):
                    value = value.isoformat()
                result[column.name] = value
        
        return result
    
    @classmethod
    def get_columns(cls):
        """Get list of column names"""
        return [c.name for c in cls.__table__.columns]
    
    @classmethod
    def searchable_columns(cls):
        """Define which columns are searchable - override in subclasses"""
        return []
    
    def __repr__(self):
        return f'<{self.__class__.__name__} {self.id}>'


class TimestampMixin:
    """Mixin for timestamp tracking"""
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow,
        nullable=False
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality"""
    
    deleted_at = db.Column(db.DateTime, nullable=True, index=True)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)


class SlugMixin:
    """Mixin for slug generation"""
    
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)
    
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()


class MetaMixin:
    """Mixin for SEO meta fields"""
    
    meta_title = db.Column(db.String(255), nullable=True)
    meta_description = db.Column(db.Text, nullable=True)
    meta_keywords = db.Column(db.Text, nullable=True)
    meta_image = db.Column(db.String(500), nullable=True)
    canonical_url = db.Column(db.String(500), nullable=True)
    robots = db.Column(db.String(255), default='index, follow')


class SortOrderMixin:
    """Mixin for sorting"""
    
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    
    @classmethod
    def ordered(cls):
        """Get records ordered by sort_order"""
        return cls.query.filter_by(is_deleted=False).order_by(cls.sort_order.asc())


class ActiveMixin:
    """Mixin for active/inactive status"""
    
    is_active = db.Column(db.Boolean, default=True, nullable=False)


# Custom Query class with soft delete support and Flask-SQLAlchemy methods
class SoftDeleteQuery(FlaskQuery):
    """Query class that filters out soft-deleted records"""
    
    def __init__(self, *args, **kwargs):
        self._with_deleted = kwargs.pop('_with_deleted', False)
        super().__init__(*args, **kwargs)
        if not self._with_deleted:
            self._criterion = False


# Apply soft delete query to base model
BaseModel.query_class = SoftDeleteQuery
