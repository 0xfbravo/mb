from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.domain.errors import (EmptyAddressError, EmptyTransactionIdError,
                               InsufficientBalanceError, InvalidAmountError,
                               InvalidNetworkError, InvalidPaginationError,
                               InvalidTxAssetError,
                               InvalidWalletPrivateKeyError, SameAddressError,
                               WalletNotFoundError)
from app.domain.tx_models import (CreateTx, Transaction,
                                  TransactionsPagination,
                                  TransactionValidation)
from app.utils.di import DependencyInjection, get_dependency_injection

# Tags
transaction_tag = "💰 Transaction"

router = APIRouter(prefix="/tx", tags=[transaction_tag])


@router.post("/validate", tags=[transaction_tag])
async def validate_transaction(
    tx_hash: str, di: Annotated[DependencyInjection, Depends(get_dependency_injection)]
) -> TransactionValidation:
    """
    Validate a transaction hash to determine if it's safe for credit generation.

    This endpoint:
    1. Fetches the transaction from the blockchain
    2. Identifies if it's an ETH or ERC-20 transfer
    3. Validates if the destination address is one of our generated addresses
    4. Returns validation results and transfer details
    5. Stores valid transactions in the database

    Args:
        tx_hash: The transaction hash to validate

    Returns:
        TransactionValidation object with validation results and transfer details
    """
    try:
        di.logger.info(f"Validating transaction: {tx_hash}")
        return await di.tx_uc.validate_transaction(tx_hash)
    except EmptyAddressError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Database not initialized")
    except Exception as e:
        di.logger.error(f"Unexpected error validating transaction: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error")


@router.post("/", tags=[transaction_tag])
async def create_tx(
    tx: CreateTx, di: Annotated[DependencyInjection, Depends(get_dependency_injection)]
) -> Transaction:
    """
    Create a new transaction.
    """
    try:
        di.logger.info(f"Creating transaction: {tx}")
        return await di.tx_uc.create(tx)
    except (
        InvalidTxAssetError,
        InvalidAmountError,
        SameAddressError,
        EmptyAddressError,
        InsufficientBalanceError,
        InvalidNetworkError,
        InvalidWalletPrivateKeyError,
        WalletNotFoundError,
    ) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Database not initialized")
    except Exception:
        raise HTTPException(status_code=500, detail="Unexpected error")


@router.get("/", tags=[transaction_tag])
async def get_transactions(
    di: Annotated[DependencyInjection, Depends(get_dependency_injection)],
    transaction_id: Annotated[
        Optional[UUID], Query(description="Transaction ID to search by")
    ] = None,
    tx_hash: Annotated[
        Optional[str], Query(description="Transaction hash to search by")
    ] = None,
    wallet_address: Annotated[
        Optional[str], Query(description="Wallet address to get transactions for")
    ] = None,
    page: Annotated[
        int,
        Query(
            ge=1,
            description="Page number (only used when no specific filters are provided)",
        ),
    ] = 1,
    limit: Annotated[
        int, Query(ge=1, le=1000, description="Number of items to return in a page")
    ] = 10,
) -> Transaction | TransactionsPagination:
    """
    Get transactions with flexible query parameters.

    - Use `transaction_id` to get a specific transaction by ID
    - Use `tx_hash` to get a specific transaction by hash
    - Use `wallet_address` to get all transactions for a wallet
    - Use `page` and `limit` to get paginated transactions

    The `page` and `limit` parameters are required for
    wallet_address or no specific filters.

    Only one filter should be used at a time. If multiple filters are provided,
    the priority order is: transaction_id > tx_hash > wallet_address > pagination.
    """
    try:
        di.logger.info("Getting transactions with filters")
        if transaction_id:
            return await di.tx_uc.get_by_id(transaction_id)
        elif tx_hash:
            return await di.tx_uc.get_by_tx_hash(tx_hash)
        elif wallet_address:
            return await di.tx_uc.get_txs(wallet_address)
        else:
            return await di.tx_uc.get_all(page=page, limit=limit)
    except (InvalidPaginationError, EmptyAddressError, EmptyTransactionIdError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Database not initialized")
    except Exception:
        raise HTTPException(status_code=500, detail="Unexpected error")
