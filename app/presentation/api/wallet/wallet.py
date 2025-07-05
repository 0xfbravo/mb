from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.domain.wallet.models import Wallet
from app.utils.di import DependencyInjection, get_dependency_injection

# Tags
wallet_tag = "🔐 Wallet"

router = APIRouter(prefix="/wallet", tags=[wallet_tag])


@router.post("/", tags=[wallet_tag])
async def create_wallet(
    request: Request,
    di: Annotated[DependencyInjection, Depends(get_dependency_injection)],
) -> Wallet:
    """
    This endpoint is responsible for creating multiple wallets,
    returning the address, private keys and public keys.
    """
    di.logger.info("Creating wallet")
    try:
        return await di.wallet_uc.create()
    except Exception as e:
        di.logger.error(f"Error creating wallet: {e}")
        raise HTTPException(status_code=400, detail="Unable to create wallet")

@router.get("/", tags=[wallet_tag])
async def get_wallets(
    request: Request,
    di: Annotated[DependencyInjection, Depends(get_dependency_injection)],
) -> list[Wallet]:
    """
    Get all wallets.
    """
    di.logger.info("Getting wallets")
    try:
        return await di.wallet_uc.get_all()
    except Exception as e:
        di.logger.error(f"Error getting wallets: {e}")
        raise HTTPException(status_code=400, detail="Unable to get wallets")

@router.get("/{address}", tags=[wallet_tag])
async def get_wallet(
    request: Request,
    address: str,
    di: Annotated[DependencyInjection, Depends(get_dependency_injection)],
) -> Wallet:
    """
    Get wallet information by address.
    """
    try:
        di.logger.info("Getting wallet")
        return await di.wallet_uc.get_by_address(address)
    except Exception as e:
        di.logger.error(f"Error getting wallet: {e}")
        raise HTTPException(status_code=404, detail="Wallet not found")
