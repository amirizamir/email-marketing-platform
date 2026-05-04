from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import (
    Campaign,
    CampaignStatus,
    ContactList,
    EmailJob,
    EmailJobStatus,
    EmailTemplate,
    SMTPAccount,
    User,
)
from app.schemas import (
    CampaignCreate,
    CampaignOut,
    CampaignSchedule,
    CampaignStats,
    CampaignUpdate,
)
from app.services.campaign_ops import build_jobs_for_campaign, maybe_complete_campaign, recompute_campaign_totals
from app.services.queue_notify import notify_email_workers

router = APIRouter()


def _require_owned_campaign(c: Campaign | None, user: User) -> Campaign:
    if not c or c.user_id != user.id:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return c


@router.post("", response_model=CampaignOut)
async def create_campaign(
    body: CampaignCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    for mid, model in [(body.template_id, EmailTemplate), (body.sender_id, SMTPAccount), (body.list_id, ContactList)]:
        obj = await db.get(model, mid)
        if not obj or obj.user_id != user.id:
            raise HTTPException(status_code=400, detail=f"Invalid reference {mid}")

    camp = Campaign(
        user_id=user.id,
        name=body.name,
        template_id=body.template_id,
        sender_id=body.sender_id,
        list_id=body.list_id,
        status=CampaignStatus.draft,
    )
    db.add(camp)
    await db.flush()
    await db.refresh(camp)
    return camp


@router.get("", response_model=list[CampaignOut])
async def list_campaigns(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    r = await db.execute(select(Campaign).where(Campaign.user_id == user.id).order_by(Campaign.id.desc()))
    return list(r.scalars().all())


@router.get("/{campaign_id}", response_model=CampaignOut)
async def get_campaign(
    campaign_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    c = await db.get(Campaign, campaign_id)
    return _require_owned_campaign(c, user)


@router.put("/{campaign_id}", response_model=CampaignOut)
async def update_campaign(
    campaign_id: int,
    body: CampaignUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    c = await db.get(Campaign, campaign_id)
    c = _require_owned_campaign(c, user)
    if body.name is not None:
        c.name = body.name
    await db.flush()
    await db.refresh(c)
    return c


@router.post("/{campaign_id}/start", response_model=CampaignOut)
async def start_campaign(
    campaign_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    c = await db.get(Campaign, campaign_id)
    c = _require_owned_campaign(c, user)
    if c.status not in (CampaignStatus.draft, CampaignStatus.paused, CampaignStatus.scheduled):
        raise HTTPException(status_code=400, detail="Campaign cannot be started from this state")

    await build_jobs_for_campaign(db, c)
    c.status = CampaignStatus.running
    c.scheduled_at = None
    await db.flush()
    await recompute_campaign_totals(db, c.id)
    notify_email_workers()
    await db.refresh(c)
    return c


@router.post("/{campaign_id}/pause", response_model=CampaignOut)
async def pause_campaign(
    campaign_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    c = await db.get(Campaign, campaign_id)
    c = _require_owned_campaign(c, user)
    if c.status != CampaignStatus.running:
        raise HTTPException(status_code=400, detail="Campaign is not running")
    c.status = CampaignStatus.paused
    await db.flush()
    await db.refresh(c)
    return c


@router.post("/{campaign_id}/resume", response_model=CampaignOut)
async def resume_campaign(
    campaign_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    c = await db.get(Campaign, campaign_id)
    c = _require_owned_campaign(c, user)
    if c.status != CampaignStatus.paused:
        raise HTTPException(status_code=400, detail="Campaign is not paused")
    c.status = CampaignStatus.running
    await db.flush()
    notify_email_workers()
    await db.refresh(c)
    return c


@router.post("/{campaign_id}/schedule", response_model=CampaignOut)
async def schedule_campaign(
    campaign_id: int,
    body: CampaignSchedule,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    c = await db.get(Campaign, campaign_id)
    c = _require_owned_campaign(c, user)
    if c.status not in (CampaignStatus.draft,):
        raise HTTPException(status_code=400, detail="Only draft campaigns can be scheduled")

    when = body.scheduled_at
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)

    await build_jobs_for_campaign(db, c)
    c.status = CampaignStatus.scheduled
    c.scheduled_at = when
    await db.flush()
    await recompute_campaign_totals(db, c.id)
    await db.refresh(c)
    return c


@router.get("/{campaign_id}/stats", response_model=CampaignStats)
async def campaign_stats(
    campaign_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    c = await db.get(Campaign, campaign_id)
    _require_owned_campaign(c, user)
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
    return CampaignStats(sent=int(row["sent"]), failed=int(row["failed"]), pending=int(row["pending"]))


@router.post("/{campaign_id}/retry-failed", response_model=CampaignOut)
async def retry_failed(
    campaign_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Reset failed jobs to pending for another attempt cycle (attempts reset to 0)."""
    c = await db.get(Campaign, campaign_id)
    c = _require_owned_campaign(c, user)
    now = datetime.now(timezone.utc)
    await db.execute(
        text(
            """
            UPDATE email_jobs
            SET status = 'pending', attempts = 0, last_error = NULL,
                scheduled_at = :now
            WHERE campaign_id = :cid AND status = 'failed'
            """
        ),
        {"cid": campaign_id, "now": now},
    )
    await recompute_campaign_totals(db, campaign_id)
    if c.status in (CampaignStatus.completed, CampaignStatus.paused, CampaignStatus.draft):
        c.status = CampaignStatus.running
    await db.flush()
    notify_email_workers()
    await db.refresh(c)
    return c
