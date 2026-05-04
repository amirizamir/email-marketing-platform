from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import ContactList, User
from app.schemas import ContactListCreate, ContactListOut

router = APIRouter()


@router.post("", response_model=ContactListOut)
async def create_list(
    body: ContactListCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    lst = ContactList(user_id=user.id, name=body.name)
    db.add(lst)
    await db.flush()
    await db.refresh(lst)
    return lst


@router.get("", response_model=list[ContactListOut])
async def list_lists(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    r = await db.execute(select(ContactList).where(ContactList.user_id == user.id))
    return list(r.scalars().all())
