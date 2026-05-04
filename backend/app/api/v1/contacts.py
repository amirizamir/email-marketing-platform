from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Contact, ContactList, User
from app.schemas import ContactOut, ContactsUploadResult
from app.services.csv_import import parse_emails_csv

router = APIRouter()


class ContactsDeleteBody(BaseModel):
    ids: list[int] = Field(default_factory=list)


@router.post("/upload", response_model=ContactsUploadResult)
async def upload_contacts(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(...),
    list_id: int = Form(...),
):
    lst = await db.get(ContactList, list_id)
    if not lst or lst.user_id != user.id:
        raise HTTPException(status_code=404, detail="List not found")

    raw = await file.read()
    emails, skipped_invalid = parse_emails_csv(raw)

    from sqlalchemy.dialects.postgresql import insert as pg_insert

    CHUNK = 5000
    imported = 0
    for i in range(0, len(emails), CHUNK):
        chunk = emails[i : i + CHUNK]
        rows = [{"user_id": user.id, "list_id": list_id, "email": e} for e in chunk]
        stmt = pg_insert(Contact).values(rows).on_conflict_do_nothing(constraint="uq_contact_list_email")
        res = await db.execute(stmt)
        imported += res.rowcount or 0

    skipped_duplicate = max(0, len(emails) - imported)
    return ContactsUploadResult(
        imported=imported,
        skipped_invalid=skipped_invalid,
        skipped_duplicate=skipped_duplicate,
    )


@router.get("", response_model=list[ContactOut])
async def list_contacts(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    list_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
):
    q = select(Contact).where(Contact.user_id == user.id)
    if list_id is not None:
        lst = await db.get(ContactList, list_id)
        if not lst or lst.user_id != user.id:
            raise HTTPException(status_code=404, detail="List not found")
        q = q.where(Contact.list_id == list_id)
    q = q.order_by(Contact.id).offset(skip).limit(min(limit, 500))
    r = await db.execute(q)
    return list(r.scalars().all())


@router.delete("")
async def delete_contacts(
    body: ContactsDeleteBody,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    if not body.ids:
        return {"deleted": 0}
    r = await db.execute(
        delete(Contact).where(Contact.user_id == user.id, Contact.id.in_(body.ids))
    )
    return {"deleted": r.rowcount or 0}
