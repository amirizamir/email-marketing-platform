from fastapi import APIRouter

from app.api.v1 import auth, campaigns, contacts, lists, smtp, templates

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(smtp.router, prefix="/smtp", tags=["smtp"])
api_router.include_router(lists.router, prefix="/lists", tags=["lists"])
api_router.include_router(contacts.router, prefix="/contacts", tags=["contacts"])
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])
api_router.include_router(campaigns.router, prefix="/campaigns", tags=["campaigns"])
