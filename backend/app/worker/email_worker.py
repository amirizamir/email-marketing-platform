"""
Email worker: atomic claim after rate wait; Redis spacing per sender; PostgreSQL source of truth.
"""
from __future__ import annotations

import logging
import random
import signal
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.database_sync import SessionLocal
from app.models import Campaign, CampaignStatus
from app.models.email_job import EmailJob, EmailJobStatus
from app.services.email_sender import send_smtp_sync
from app.services.redis_client import get_sync_redis

logger = logging.getLogger(__name__)
settings = get_settings()

STOP = False


def _handle_sig(*_):
    global STOP
    STOP = True


def activate_scheduled_campaigns(db: Session) -> None:
    db.execute(
        text(
            """
            UPDATE campaigns
            SET status = 'running'
            WHERE status = 'scheduled' AND scheduled_at IS NOT NULL AND scheduled_at <= NOW()
            """
        )
    )


def find_next_job_ids(db: Session) -> tuple[int, int, int] | None:
    r = db.execute(
        text(
            """
            SELECT ej.id, ej.campaign_id, c.sender_id
            FROM email_jobs ej
            INNER JOIN campaigns c ON c.id = ej.campaign_id
            WHERE ej.status = 'pending'
              AND c.status = 'running'
              AND ej.attempts < 3
              AND (ej.scheduled_at IS NULL OR ej.scheduled_at <= NOW())
            ORDER BY ej.id
            LIMIT 1
            """
        )
    )
    row = r.first()
    if not row:
        return None
    return (int(row[0]), int(row[1]), int(row[2]))


def sync_campaign_stats(db: Session, campaign_id: int) -> None:
    db.execute(
        text(
            """
            UPDATE campaigns AS c
            SET
              sent_count = s.sent,
              failed_count = s.failed,
              total_recipients = s.tot
            FROM (
              SELECT
                campaign_id,
                COUNT(*) FILTER (WHERE status = 'sent') AS sent,
                COUNT(*) FILTER (WHERE status = 'failed') AS failed,
                COUNT(*) AS tot
              FROM email_jobs
              WHERE campaign_id = :cid
              GROUP BY campaign_id
            ) AS s
            WHERE c.id = :cid AND c.id = s.campaign_id
            """
        ),
        {"cid": campaign_id},
    )


def wait_rate_limit(r, sender_id: int) -> None:
    key = f"sender:next_ts:{sender_id}"
    while not STOP:
        raw = r.get(key)
        now = time.time()
        if raw is None:
            return
        try:
            nxt = float(raw)
        except ValueError:
            return
        if now >= nxt:
            return
        time.sleep(min(1.0, max(0.0, nxt - now) + 0.01))


def mark_rate_after_attempt(r, sender_id: int) -> None:
    delay = 10.0 + random.uniform(0.0, 3.0)
    r.set(f"sender:next_ts:{sender_id}", str(time.time() + delay))


def load_job(db: Session, job_id: int) -> EmailJob | None:
    from sqlalchemy import select

    return (
        db.execute(
            select(EmailJob)
            .where(EmailJob.id == job_id)
            .options(
                joinedload(EmailJob.campaign).joinedload(Campaign.template),
                joinedload(EmailJob.campaign).joinedload(Campaign.sender),
            )
        )
        .unique()
        .scalar_one_or_none()
    )


def claim_job(db: Session, job_id: int) -> bool:
    """Increment attempts for one eligible pending job. Returns False if no row updated."""
    res = db.execute(
        text(
            """
            UPDATE email_jobs AS ej
            SET attempts = ej.attempts + 1
            FROM campaigns c
            WHERE ej.id = :jid
              AND ej.campaign_id = c.id
              AND ej.status = 'pending'
              AND c.status = 'running'
              AND ej.attempts < 3
              AND (ej.scheduled_at IS NULL OR ej.scheduled_at <= NOW())
            RETURNING ej.id
            """
        ),
        {"jid": job_id},
    )
    return res.first() is not None


def run_loop() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    signal.signal(signal.SIGINT, _handle_sig)
    signal.signal(signal.SIGTERM, _handle_sig)

    r = get_sync_redis()
    logger.info("Email worker started (queue: %s)", settings.email_campaign_queue)

    while not STOP:
        d0 = SessionLocal()
        try:
            activate_scheduled_campaigns(d0)
            d0.commit()
        except Exception:
            d0.rollback()
        finally:
            d0.close()

        try:
            r.brpop(settings.email_campaign_queue, timeout=5)
        except Exception:
            time.sleep(1)

        d1 = SessionLocal()
        try:
            meta = find_next_job_ids(d1)
        finally:
            d1.close()

        if not meta:
            time.sleep(2)
            continue

        job_id, _campaign_id, sender_id = meta
        lock = r.lock(f"sender:{sender_id}:mail", timeout=300, blocking_timeout=60)
        if not lock.acquire(blocking=True):
            time.sleep(0.2)
            continue

        did_attempt = False
        try:
            wait_rate_limit(r, sender_id)

            db = SessionLocal()
            try:
                if not claim_job(db, job_id):
                    db.rollback()
                else:
                    db.commit()
                    job = load_job(db, job_id)
                    if job is None:
                        pass
                    else:
                        did_attempt = True
                        try:
                            send_smtp_sync(
                                job.campaign.sender,
                                job.campaign.template,
                                job.email,
                                variables={"email": job.email},
                            )
                        except Exception as e:
                            logger.exception("SMTP failed job=%s", job_id)
                            err = str(e)[:4000]
                            job.last_error = err
                            if job.attempts >= 3:
                                job.status = EmailJobStatus.failed
                            else:
                                job.status = EmailJobStatus.pending
                                job.scheduled_at = datetime.now(timezone.utc) + timedelta(
                                    seconds=10.0 * (2 ** (job.attempts - 1))
                                )
                            sync_campaign_stats(db, job.campaign_id)
                            db.commit()
                        else:
                            job.status = EmailJobStatus.sent
                            job.sent_at = datetime.now(timezone.utc)
                            job.last_error = None
                            job.scheduled_at = None
                            sync_campaign_stats(db, job.campaign_id)
                            pend_left = db.execute(
                                text(
                                    "SELECT COUNT(*) FROM email_jobs WHERE campaign_id = :c AND status = 'pending'"
                                ),
                                {"c": job.campaign_id},
                            ).scalar_one()
                            if pend_left == 0:
                                c = db.get(Campaign, job.campaign_id)
                                if c and c.status == CampaignStatus.running:
                                    c.status = CampaignStatus.completed
                            db.commit()
            except Exception:
                db.rollback()
                logger.exception("job processing")
            finally:
                db.close()
        finally:
            try:
                lock.release()
            except Exception:
                pass
            if did_attempt:
                mark_rate_after_attempt(r, sender_id)

    logger.info("Email worker stopped")


if __name__ == "__main__":
    run_loop()
