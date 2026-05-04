from app.config import get_settings
from app.services.redis_client import get_sync_redis

_settings = get_settings()


def notify_email_workers() -> None:
    """Wake workers without storing per-job queue entries (DB remains source of truth)."""
    try:
        r = get_sync_redis()
        r.lpush(_settings.email_campaign_queue, "tick")
    except Exception:
        pass
