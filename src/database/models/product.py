"""
Product hierarchy models.

    Product → ProductVariant → ProductListing → PriceSnapshot

ProductVariant uses JSONB `attributes` for category-specific fields
(storage for phones, RAM for laptops, fabric for sofas).
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime

from src.database.session import Base


class Product(Base):
    """Canonical product entity (e.g. 'iPhone 16 Pro')."""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    brand = Column(String, nullable=True, index=True)
    category = Column(String, nullable=True, index=True)
    model_number = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    variants = relationship("ProductVariant", back_populates="product")


class ProductVariant(Base):
    """Specific SKU/configuration (e.g. '256GB, Space Black').

    The `attributes` JSONB column stores category-specific fields:
        - Phones:    {"storage": "256GB", "color": "Space Black"}
        - Laptops:   {"ram": "36GB", "storage": "1TB SSD", "cpu": "M4 Max"}
        - Furniture: {"seats": "3", "fabric": "Tibbleby beige"}
    """

    __tablename__ = "product_variants"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    variant_name = Column(String, nullable=True)
    sku = Column(String, nullable=True)
    attributes = Column(JSONB, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship("Product", back_populates="variants")
    listings = relationship("ProductListing", back_populates="variant")
    tracking_jobs = relationship("TrackingJob", back_populates="variant")


class ProductListing(Base):
    """A variant sold on a specific retailer (e.g. iPhone 16 Pro 256GB on Amazon)."""

    __tablename__ = "product_listings"

    id = Column(Integer, primary_key=True, index=True)
    variant_id = Column(
        Integer, ForeignKey("product_variants.id"), nullable=False, index=True
    )
    retailer = Column(String, nullable=False, index=True)
    source_url = Column(String, nullable=False, unique=True, index=True)
    current_price = Column(Float, nullable=True)
    currency = Column(String, default="USD")
    rating = Column(Float, nullable=True)
    rating_count = Column(Integer, nullable=True)
    availability = Column(String, nullable=True)  # in_stock, out_of_stock, preorder
    last_checked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    variant = relationship("ProductVariant", back_populates="listings")
    snapshots = relationship("PriceSnapshot", back_populates="listing")


class PriceSnapshot(Base):
    """Immutable price data point captured at a point in time."""

    __tablename__ = "price_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(
        Integer, ForeignKey("product_listings.id"), nullable=False, index=True
    )
    price = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    captured_at = Column(DateTime, default=datetime.utcnow)

    listing = relationship("ProductListing", back_populates="snapshots")
