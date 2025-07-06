from fastapi import APIRouter

from app.presentation.api.health import health_router
from app.presentation.api.transaction import transaction_router
from app.presentation.api.wallet import wallet_router

api_router = APIRouter(prefix="/api")
api_router.include_router(wallet_router)
api_router.include_router(transaction_router)
api_router.include_router(health_router)
