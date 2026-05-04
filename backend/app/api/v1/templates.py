from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import EmailTemplate, User
from app.schemas import TemplateCreate, TemplateOut, TemplateUpdate

router = APIRouter()


@router.post("", response_model=TemplateOut)
async def create_template(
    body: TemplateCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    t = EmailTemplate(
        user_id=user.id,
        name=body.name,
        subject=body.subject,
        html_content=body.html_content,
        version=1,
    )
    db.add(t)
    await db.flush()
    await db.refresh(t)
    return t


@router.get("", response_model=list[TemplateOut])
async def list_templates(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    r = await db.execute(select(EmailTemplate).where(EmailTemplate.user_id == user.id))
    return list(r.scalars().all())


@router.get("/{template_id}", response_model=TemplateOut)
async def get_template(
    template_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    t = await db.get(EmailTemplate, template_id)
    if not t or t.user_id != user.id:
        raise HTTPException(status_code=404, detail="Template not found")
    return t


@router.put("/{template_id}", response_model=TemplateOut)
async def update_template(
    template_id: int,
    body: TemplateUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    t = await db.get(EmailTemplate, template_id)
    if not t or t.user_id != user.id:
        raise HTTPException(status_code=404, detail="Template not found")
    if body.name is not None:
        t.name = body.name
    if body.subject is not None:
        t.subject = body.subject
    if body.html_content is not None:
        t.html_content = body.html_content
    t.version = t.version + 1
    await db.flush()
    await db.refresh(t)
    return t
