from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.domain.errors import AssetNotFoundError, InvalidNetworkError
from app.utils.di import DependencyInjection, get_dependency_injection

# Tags
assets_tag = "🪙 Assets"

router = APIRouter(prefix="/assets", tags=[assets_tag])


@router.post("/", tags=[assets_tag])
async def get_all_assets(
    request: Request,
    di: Annotated[DependencyInjection, Depends(get_dependency_injection)],
) -> list[str]:
    """
    This endpoint is responsible for getting all assets.
    Returns:
        The list of all assets.
    """
    try:
        di.logger.info("Getting all assets")
        return di.assets_uc.get_all_assets()
    except RuntimeError as e:
        di.logger.error(f"Database not initialized: {e}")
        raise HTTPException(status_code=503, detail="Database not available")
    except Exception as e:
        di.logger.error(f"Error getting all assets: {e}")
        raise HTTPException(status_code=500, detail="Unable to get all assets")


@router.get("/native", tags=[assets_tag])
async def get_native_asset(
    request: Request,
    di: Annotated[DependencyInjection, Depends(get_dependency_injection)],
) -> str:
    """
    This endpoint is responsible for getting the native asset
    for the current network.
    Returns:
        The native asset.
    """
    try:
        di.logger.info("Getting native asset")
        return di.assets_uc.get_native_asset()
    except Exception as e:
        di.logger.error(f"Error getting native asset: {e}")
        raise HTTPException(status_code=500, detail="Unable to get native asset")


@router.get("/{asset}", tags=[assets_tag])
async def get_asset(
    request: Request,
    asset: str,
    di: Annotated[DependencyInjection, Depends(get_dependency_injection)],
) -> dict:
    """
    This endpoint is responsible for getting an asset configuration.
    Args:
        asset: The asset to get the configuration of.
    Returns:
        The configuration of the asset.
    """
    try:
        di.logger.info(f"Getting asset: {asset}")
        return di.assets_uc.get_asset(asset)
    except (AssetNotFoundError, InvalidNetworkError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        di.logger.error(f"Error getting asset: {e}")
        raise HTTPException(status_code=500, detail="Unable to get asset")
