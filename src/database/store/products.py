"""
Product store operations.

Handles Product, ProductVariant, ProductListing, and PriceSnapshot CRUD.
All find_or_create functions are idempotent and race-condition safe.
"""
from typing import Optional, List
from datetime import datetime
import logging

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.database.models import (
    Product,
    ProductVariant,
    ProductListing,
    PriceSnapshot,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

def find_or_create_product(
    db: Session,
    name: str,
    brand: Optional[str] = None,
    category: Optional[str] = None,
    model_number: Optional[str] = None,
    description: Optional[str] = None,
) -> Product:
    """Find a product by name+brand or create one (ACID).

    Matching is case-insensitive on name + brand to avoid duplicates.
    """
    query = db.query(Product).filter(Product.name.ilike(name))
    if brand:
        query = query.filter(Product.brand.ilike(brand))

    product = query.first()
    if product:
        # Enrich existing product with any new metadata
        changed = False
        if category and not product.category:
            product.category = category
            changed = True
        if model_number and not product.model_number:
            product.model_number = model_number
            changed = True
        if description and not product.description:
            product.description = description
            changed = True
        if changed:
            db.commit()
            db.refresh(product)
        return product

    try:
        product = Product(
            name=name,
            brand=brand,
            category=category,
            model_number=model_number,
            description=description,
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        logger.info(
            "Created product id=%s: %s (%s)", product.id, name, brand or "unknown brand"
        )
        return product
    except IntegrityError:
        db.rollback()
        return db.query(Product).filter(Product.name.ilike(name)).first()


def get_product_by_id(db: Session, product_id: int) -> Optional[Product]:
    """Look up a product by primary key."""
    return db.query(Product).filter(Product.id == product_id).first()


# ---------------------------------------------------------------------------
# Product Variants
# ---------------------------------------------------------------------------

def find_or_create_variant(
    db: Session,
    product_id: int,
    variant_name: Optional[str] = None,
    sku: Optional[str] = None,
    attributes: Optional[dict] = None,
) -> ProductVariant:
    """Find a variant by product_id + variant_name or create one (ACID).

    If variant_name is None, this is a "default" variant (products
    that don't have meaningful configurations).
    """
    query = db.query(ProductVariant).filter(
        ProductVariant.product_id == product_id,
    )
    if variant_name:
        query = query.filter(ProductVariant.variant_name.ilike(variant_name))
    else:
        query = query.filter(ProductVariant.variant_name.is_(None))

    variant = query.first()
    if variant:
        # Enrich with new attributes
        if attributes and variant.attributes != attributes:
            merged = {**(variant.attributes or {}), **attributes}
            variant.attributes = merged
            db.commit()
            db.refresh(variant)
        return variant

    try:
        variant = ProductVariant(
            product_id=product_id,
            variant_name=variant_name,
            sku=sku,
            attributes=attributes or {},
        )
        db.add(variant)
        db.commit()
        db.refresh(variant)
        logger.info(
            "Created variant id=%s for product %s: %s",
            variant.id,
            product_id,
            variant_name or "(default)",
        )
        return variant
    except IntegrityError:
        db.rollback()
        return query.first()


# ---------------------------------------------------------------------------
# Product Listings
# ---------------------------------------------------------------------------

def find_or_create_listing(
    db: Session,
    variant_id: int,
    retailer: str,
    source_url: str,
    current_price: Optional[float] = None,
    currency: str = "USD",
    rating: Optional[float] = None,
    rating_count: Optional[int] = None,
    availability: Optional[str] = None,
) -> ProductListing:
    """Find a listing by source_url or create one (ACID).

    If the listing exists, update its current_price and metadata.
    """
    listing = (
        db.query(ProductListing)
        .filter(ProductListing.source_url == source_url)
        .first()
    )

    if listing:
        listing.current_price = current_price or listing.current_price
        listing.currency = currency
        listing.rating = rating if rating is not None else listing.rating
        listing.rating_count = rating_count if rating_count is not None else listing.rating_count
        listing.availability = availability or listing.availability
        listing.last_checked_at = datetime.utcnow()
        db.commit()
        db.refresh(listing)
        return listing

    try:
        listing = ProductListing(
            variant_id=variant_id,
            retailer=retailer,
            source_url=source_url,
            current_price=current_price,
            currency=currency,
            rating=rating,
            rating_count=rating_count,
            availability=availability,
            last_checked_at=datetime.utcnow(),
        )
        db.add(listing)
        db.commit()
        db.refresh(listing)
        logger.info(
            "Created listing id=%s: %s on %s @ %s %s",
            listing.id, source_url, retailer, current_price, currency,
        )
        return listing
    except IntegrityError:
        db.rollback()
        return (
            db.query(ProductListing)
            .filter(ProductListing.source_url == source_url)
            .first()
        )


def get_listings_for_variant(
    db: Session, variant_id: int
) -> List[ProductListing]:
    """Get all retailer listings for a product variant, cheapest first."""
    return (
        db.query(ProductListing)
        .filter(ProductListing.variant_id == variant_id)
        .order_by(ProductListing.current_price.asc())
        .all()
    )


# ---------------------------------------------------------------------------
# Price Snapshots
# ---------------------------------------------------------------------------

def create_price_snapshot(
    db: Session,
    listing_id: int,
    price: float,
    currency: str = "USD",
) -> PriceSnapshot:
    """Record an immutable price data point (ACID)."""
    snapshot = PriceSnapshot(
        listing_id=listing_id,
        price=price,
        currency=currency,
    )
    try:
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        logger.info(
            "Recorded snapshot id=%s for listing %s: %s %s",
            snapshot.id, listing_id, price, currency,
        )
        return snapshot
    except Exception:
        db.rollback()
        logger.exception("Failed to record snapshot for listing %s", listing_id)
        raise


def get_snapshots_for_listing(
    db: Session, listing_id: int, limit: int = 100
) -> List[PriceSnapshot]:
    """Retrieve price snapshots for a listing, ordered chronologically."""
    return (
        db.query(PriceSnapshot)
        .filter(PriceSnapshot.listing_id == listing_id)
        .order_by(PriceSnapshot.captured_at.asc())
        .limit(limit)
        .all()
    )


# ---------------------------------------------------------------------------
# Convenience: persist a full agent response
# ---------------------------------------------------------------------------

def persist_agent_response(
    db: Session,
    product_data: dict,
    variant_data: Optional[dict] = None,
    listings_data: Optional[list] = None,
) -> ProductVariant:
    """Persist a complete agent response into the product hierarchy.

    Accepts the structured JSON from the OpenClaw price-check skill and
    creates/updates Product → ProductVariant → ProductListing → PriceSnapshot
    in a single transaction.

    Returns the ProductVariant for use in reply formatting.
    """
    # 1. Product
    product = find_or_create_product(
        db,
        name=product_data.get("name", "Unknown Product"),
        brand=product_data.get("brand"),
        category=product_data.get("category"),
        model_number=product_data.get("model_number"),
    )

    # 2. Variant
    v = variant_data or {}
    variant = find_or_create_variant(
        db,
        product_id=product.id,
        variant_name=v.get("variant_name"),
        sku=v.get("sku"),
        attributes=v.get("attributes", {}),
    )

    # 3. Listings + snapshots
    for ld in (listings_data or []):
        listing = find_or_create_listing(
            db,
            variant_id=variant.id,
            retailer=ld.get("retailer", "unknown"),
            source_url=ld.get("source_url", ""),
            current_price=ld.get("price"),
            currency=ld.get("currency", "USD"),
            rating=ld.get("rating"),
            rating_count=ld.get("rating_count"),
            availability=ld.get("availability"),
        )

        if ld.get("price") is not None:
            create_price_snapshot(
                db,
                listing_id=listing.id,
                price=ld["price"],
                currency=ld.get("currency", "USD"),
            )

    return variant
