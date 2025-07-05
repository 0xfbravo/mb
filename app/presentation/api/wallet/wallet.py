from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.domain.wallet.models import Wallet, WalletsPagination
from app.utils.di import DependencyInjection, get_dependency_injection

# Tags
wallet_tag = "🔐 Wallet"

router = APIRouter(prefix="/wallet", tags=[wallet_tag])


@router.post("/", tags=[wallet_tag])
async def create_wallet(
    request: Request,
    di: Annotated[DependencyInjection, Depends(get_dependency_injection)],
    number_of_wallets: Annotated[
        int, Query(ge=1, le=1000, description="Number of wallets to create")
    ] = 1,
) -> list[Wallet]:
    """
    This endpoint is responsible for creating multiple wallets,
    returning the address, private keys and public keys.
    """
    try:
        di.ensure_database_initialized()
        di.logger.info("Creating wallet")
        return await di.wallet_uc.create(number_of_wallets)
    except RuntimeError as e:
        di.logger.error(f"Database not initialized: {e}")
        raise HTTPException(status_code=503, detail="Database not available")
    except Exception as e:
        di.logger.error(f"Error creating wallet: {e}")
        raise HTTPException(status_code=500, detail="Unable to create wallet")


@router.get("/", tags=[wallet_tag])
async def get_wallets(
    request: Request,
    di: Annotated[DependencyInjection, Depends(get_dependency_injection)],
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    limit: Annotated[
        int, Query(ge=1, le=1000, description="Number of items to return in a page")
    ] = 10,
) -> WalletsPagination:
    """
    Get all wallets with pagination.

    - **page**: Page number (for pagination)
    - **limit**: Number of items to return (max 1000)
    """
    try:
        di.ensure_database_initialized()
        di.logger.info(f"Getting wallets with pagination: page={page}, limit={limit}")

        if page < 1:
            raise HTTPException(
                status_code=400, detail="Page number must be greater than 0"
            )

        if limit < 1 or limit > 1000:
            raise HTTPException(
                status_code=400, detail="Limit must be between 1 and 1000"
            )

        return await di.wallet_uc.get_all(page=page, limit=limit)
    except RuntimeError as e:
        di.logger.error(f"Database not initialized: {e}")
        raise HTTPException(status_code=503, detail="Database not available")
    except HTTPException:
        # Re-raise HTTP exceptions as they are already properly formatted
        raise
    except Exception as e:
        di.logger.error(f"Error getting wallets: {e}")
        raise HTTPException(status_code=500, detail="Unable to get wallets")


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
        di.ensure_database_initialized()
        di.logger.info("Getting wallet")
        return await di.wallet_uc.get_by_address(address)
    except RuntimeError as e:
        di.logger.error(f"Database not initialized: {e}")
        raise HTTPException(status_code=503, detail="Database not available")
    except Exception as e:
        di.logger.error(f"Error getting wallet: {e}")
        raise HTTPException(status_code=404, detail="Wallet not found")
