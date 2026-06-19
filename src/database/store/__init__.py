"""
Data store package.

Re-exports all store functions so existing imports continue to work:
    from src.database import store
    store.get_or_create_user(db, ...)
"""
from src.database.store.users import (
    get_or_create_user,
    get_user_by_identifier,
    get_user_by_id,
)
from src.database.store.products import (
    find_or_create_product,
    find_or_create_variant,
    find_or_create_listing,
    get_product_by_id,
    get_listings_for_variant,
    create_price_snapshot,
    get_snapshots_for_listing,
    persist_agent_response,
)
from src.database.store.tracking import (
    create_tracking_job,
    get_active_tracking_jobs,
    get_user_tracking_jobs,
    mark_job_completed,
    cancel_tracking_job,
    extend_tracking_job,
)
from src.database.store.reports import (
    create_report,
    get_report_by_token,
    get_expired_reports,
)
from src.database.store.conversations import (
    log_conversation,
    get_recent_conversation,
)

__all__ = [
    # Users
    "get_or_create_user",
    "get_user_by_identifier",
    "get_user_by_id",
    # Products
    "find_or_create_product",
    "find_or_create_variant",
    "find_or_create_listing",
    "get_product_by_id",
    "get_listings_for_variant",
    "create_price_snapshot",
    "get_snapshots_for_listing",
    "persist_agent_response",
    # Tracking
    "create_tracking_job",
    "get_active_tracking_jobs",
    "get_user_tracking_jobs",
    "mark_job_completed",
    "cancel_tracking_job",
    "extend_tracking_job",
    # Reports
    "create_report",
    "get_report_by_token",
    "get_expired_reports",
    # Conversations
    "log_conversation",
    "get_recent_conversation",
]
