"""Campaign helpers used by API (async) and workers."""

from datetime import datetime, timezone

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Campaign, CampaignStatus, Contact, EmailJob, EmailJobStatus


async def recompute_campaign_totals(db: AsyncSession, campaign_id: int) -> None:
    r = await db.execute(
        text(
            """
            SELECT
              COUNT(*) FILTER (WHERE status = 'sent') AS sent,
              COUNT(*) FILTER (WHERE status = 'failed') AS failed,
              COUNT(*) FILTER (WHERE status = 'pending') AS pending
            FROM email_jobs
            WHERE campaign_id = :cid
            """
        ),
        {"cid": campaign_id},
    )
    row = r.mappings().one()
    sent, failed, pending = int(row["sent"]), int(row["failed"]), int(row["pending"])
    await db.execute(
        text(
            "UPDATE campaigns SET sent_count = :s, failed_count = :f, total_recipients = :t WHERE id = :id"
        ),
        {"s": sent, "f": failed, "t": sent + failed + pending, "id": campaign_id},
    )


async def maybe_complete_campaign(db: AsyncSession, campaign_id: int) -> None:
    r = await db.execute(
        text(
            "SELECT COUNT(*) FROM email_jobs WHERE campaign_id = :cid AND status = 'pending'"
        ),
        {"cid": campaign_id},
    )
    pending = r.scalar_one()
    if pending == 0:
        c = await db.get(Campaign, campaign_id)
        if c and c.status == CampaignStatus.running:
            c.status = CampaignStatus.completed


async def build_jobs_for_campaign(db: AsyncSession, campaign: Campaign) -> int:
    """Create pending EmailJob rows for all contacts in campaign.list_id. Idempotent per email."""
    r = await db.execute(select(Contact.email).where(Contact.list_id == campaign.list_id))
    emails = [row[0] for row in r.all()]
    if not emails:
        campaign.total_recipients = 0
        return 0

    existing = await db.execute(select(EmailJob.email).where(EmailJob.campaign_id == campaign.id))
    have = {e[0] for e in existing.all()}
    to_add = [e for e in emails if e not in have]
    now = datetime.now(timezone.utc)
    chunk = 5000
    for i in range(0, len(to_add), chunk):
        part = to_add[i : i + chunk]
        db.add_all(
            [
                EmailJob(
                    campaign_id=campaign.id,
                    email=e,
                    status=EmailJobStatus.pending,
                    scheduled_at=now,
                )
                for e in part
            ]
        )
        await db.flush()
    await recompute_campaign_totals(db, campaign.id)
    return len(to_add)
