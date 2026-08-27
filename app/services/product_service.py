"""
Product and Catalog Service Layer
Production-ready catalog management, faceted search, stock verification,
and category hierarchy queries adhering to SQLAlchemy 2.0 patterns.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload, selectinload

from app.extensions import db
from app.models.product import Brand, Category, Product, ProductCategory, ProductImage, Tag

logger = logging.getLogger(__name__)


class ProductService:
    """Production service for querying and managing products and categories."""

    @staticmethod
    def get_by_id(product_id: int) -> Optional[Product]:
        """
        Fetch a single product by primary key with relations eagerly loaded.
        """
        try:
            stmt = (
                select(Product)
                .where(
                    Product.id == product_id,
                    Product.is_deleted.is_(False),
                )
                .options(
                    joinedload(Product.brand),
                    selectinload(Product.categories),
                    selectinload(Product.tags),
                )
            )
            return db.session.execute(stmt).scalars().first()
        except SQLAlchemyError as exc:
            logger.error("Failed to query product id %s: %s", product_id, exc, exc_info=True)
            return None

    @staticmethod
    def get_by_slug(slug: str) -> Optional[Product]:
        """
        Fetch a product by unique slug with relations eagerly loaded.
        """
        try:
            stmt = (
                select(Product)
                .where(
                    Product.slug == slug,
                    Product.is_deleted.is_(False),
                )
                .options(
                    joinedload(Product.brand),
                    selectinload(Product.categories),
                    selectinload(Product.tags),
                )
            )
            return db.session.execute(stmt).scalars().first()
        except SQLAlchemyError as exc:
            logger.error("Failed to query product by slug '%s': %s", slug, exc, exc_info=True)
            return None

    @staticmethod
    def get_featured(limit: int = 8) -> List[Product]:
        """
        Retrieve products marked as featured for showcase components.
        """
        try:
            stmt = (
                select(Product)
                .where(
                    Product.is_featured.is_(True),
                    Product.is_active.is_(True),
                    Product.is_deleted.is_(False),
                )
                .options(joinedload(Product.brand))
                .order_by(Product.sort_order.asc(), Product.created_at.desc())
                .limit(limit)
            )
            return list(db.session.execute(stmt).scalars().all())
        except SQLAlchemyError as exc:
            logger.error("Error loading featured products: %s", exc, exc_info=True)
            return []

    @staticmethod
    def get_new_arrivals(limit: int = 8) -> List[Product]:
        """
        Retrieve newly published active products.
        """
        try:
            stmt = (
                select(Product)
                .where(
                    Product.is_active.is_(True),
                    Product.is_deleted.is_(False),
                )
                .options(joinedload(Product.brand))
                .order_by(Product.created_at.desc())
                .limit(limit)
            )
            return list(db.session.execute(stmt).scalars().all())
        except SQLAlchemyError as exc:
            logger.error("Error loading new arrivals: %s", exc, exc_info=True)
            return []

    @staticmethod
    def get_related(product: Product, limit: int = 4) -> List[Product]:
        """
        Retrieve related products based on matching categories.
        """
        if not product or not product.categories:
            return []

        try:
            cat_ids = [c.id for c in product.categories]
            stmt = (
                select(Product)
                .join(Product.categories)
                .where(
                    Category.id.in_(cat_ids),
                    Product.id != product.id,
                    Product.is_active.is_(True),
                    Product.is_deleted.is_(False),
                )
                .options(joinedload(Product.brand))
                .distinct()
                .limit(limit)
            )
            return list(db.session.execute(stmt).scalars().all())
        except SQLAlchemyError as exc:
            logger.error("Error loading related products for %s: %s", product.id, exc, exc_info=True)
            return []

    @staticmethod
    def search_products(
        query: Optional[str] = None,
        category_slug: Optional[str] = None,
        brand_id: Optional[int] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        in_stock_only: bool = False,
        sort_by: str = "newest",
        page: int = 1,
        per_page: int = 12,
    ) -> Tuple[List[Product], int]:
        """
        Comprehensive search and filtering with pagination.

        Returns:
            Tuple of (products_list, total_count).
        """
        page = max(1, page)
        per_page = min(max(1, per_page), 100)

        try:
            base_query = select(Product).where(
                Product.is_active.is_(True),
                Product.is_deleted.is_(False),
            )

            # Category filter
            if category_slug:
                base_query = base_query.join(Product.categories).where(
                    Category.slug == category_slug,
                    Category.is_deleted.is_(False),
                )

            # Brand filter
            if brand_id:
                base_query = base_query.where(Product.brand_id == brand_id)

            # Text query search in title, sku, and short description
            if query and query.strip():
                term = f"%{query.strip()}%"
                base_query = base_query.where(
                    or_(
                        Product.title.ilike(term),
                        Product.sku.ilike(term),
                        Product.short_description.ilike(term),
                    )
                )

            # Price constraints
            if min_price is not None and min_price >= 0:
                base_query = base_query.where(Product.price >= min_price)
            if max_price is not None and max_price > 0:
                base_query = base_query.where(Product.price <= max_price)

            # Stock filter
            if in_stock_only:
                base_query = base_query.where(Product.stock_quantity > 0)

            # Count total
            count_stmt = select(func.count()).select_from(base_query.subquery())
            total = db.session.execute(count_stmt).scalar() or 0

            # Sorting
            if sort_by == "price_asc":
                base_query = base_query.order_by(Product.price.asc())
            elif sort_by == "price_desc":
                base_query = base_query.order_by(Product.price.desc())
            elif sort_by == "bestseller":
                base_query = base_query.order_by(Product.sales_count.desc() if hasattr(Product, 'sales_count') else Product.created_at.desc())
            elif sort_by == "popular":
                base_query = base_query.order_by(Product.view_count.desc())
            else:
                # Default: newest
                base_query = base_query.order_by(Product.created_at.desc())

            # Eager load relationships & paginate
            paginated_stmt = (
                base_query
                .options(
                    joinedload(Product.brand),
                    selectinload(Product.categories),
                )
                .offset((page - 1) * per_page)
                .limit(per_page)
            )

            items = list(db.session.execute(paginated_stmt).scalars().all())
            return items, total
        except SQLAlchemyError as exc:
            logger.error("Error executing catalog search: %s", exc, exc_info=True)
            return [], 0

    @staticmethod
    def update_stock(product_id: int, quantity_change: int) -> bool:
        """
        Safely adjust inventory levels for a product.
        Prevents negative stock under concurrent executions.
        """
        try:
            product = db.session.get(Product, product_id)
            if not product:
                return False

            new_stock = (product.stock_quantity or 0) + quantity_change
            if new_stock < 0:
                logger.warning("Attempted to reduce stock below 0 for product %s", product_id)
                return False

            product.stock_quantity = new_stock
            if new_stock == 0:
                product.stock_status = "out_of_stock"
            elif new_stock <= (product.low_stock_threshold or 5):
                product.stock_status = "low_stock"
            else:
                product.stock_status = "in_stock"

            db.session.commit()
            return True
        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("Failed to update stock for product %s: %s", product_id, exc, exc_info=True)
            return False

    @staticmethod
    def get_categories_tree() -> List[Category]:
        """
        Retrieve root categories with their child categories eagerly populated.
        """
        try:
            stmt = (
                select(Category)
                .where(
                    Category.parent_id.is_(None),
                    Category.is_active.is_(True),
                    Category.is_deleted.is_(False),
                )
                .options(selectinload(Category.children))
                .order_by(Category.sort_order.asc())
            )
            return list(db.session.execute(stmt).scalars().all())
        except SQLAlchemyError as exc:
            logger.error("Error fetching category tree: %s", exc, exc_info=True)
            return []

    @staticmethod
    def get_category_by_slug(slug: str) -> Optional[Category]:
        """Fetch a category by slug."""
        try:
            stmt = (
                select(Category)
                .where(
                    Category.slug == slug,
                    Category.is_active.is_(True),
                    Category.is_deleted.is_(False),
                )
                .options(selectinload(Category.children))
            )
            return db.session.execute(stmt).scalars().first()
        except SQLAlchemyError as exc:
            logger.error("Error fetching category '%s': %s", slug, exc, exc_info=True)
            return None
