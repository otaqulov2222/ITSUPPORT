from fastapi import APIRouter

from app.api.v1 import audit, auth, conversations, org, tickets

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(org.router)
api_router.include_router(audit.router)
api_router.include_router(conversations.router)
api_router.include_router(tickets.router)
