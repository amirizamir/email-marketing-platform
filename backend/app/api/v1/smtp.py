from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import SMTPAccount, User
from app.schemas import SMTPAccountCreate, SMTPAccountOut, SMTPTestExisting, SMTPTestRequest
from app.services.encryption import encrypt_secret
from app.services.email_sender import test_smtp_connection, test_smtp_raw

router = APIRouter()


@router.post("", response_model=SMTPAccountOut)
async def create_smtp(
    body: SMTPAccountCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    acc = SMTPAccount(
        user_id=user.id,
        name=body.name,
        smtp_host=body.smtp_host,
        smtp_port=body.smtp_port,
        username=body.username,
        password_encrypted=encrypt_secret(body.password),
        from_email=body.from_email,
        from_name=body.from_name,
        use_tls=body.use_tls,
    )
    db.add(acc)
    await db.flush()
    await db.refresh(acc)
    return acc


@router.get("", response_model=list[SMTPAccountOut])
async def list_smtp(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    r = await db.execute(select(SMTPAccount).where(SMTPAccount.user_id == user.id))
    return list(r.scalars().all())


@router.post("/test")
async def test_smtp_new(
    body: SMTPTestRequest,
    user: Annotated[User, Depends(get_current_user)],
):
    _ = user
    try:
        test_smtp_raw(body.smtp_host, body.smtp_port, body.username, body.password, body.use_tls)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"ok": True}


@router.post("/test-existing")
async def test_smtp_saved(
    body: SMTPTestExisting,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    acc = await db.get(SMTPAccount, body.smtp_id)
    if not acc or acc.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SMTP account not found")
    try:
        test_smtp_connection(acc)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"ok": True}
