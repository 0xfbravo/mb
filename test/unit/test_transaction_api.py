"""
Unit tests for transaction API endpoints.
"""

import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.presentation.api.transaction import (
    validate_transaction,
    create_tx,
    get_transactions,
)
from app.domain.tx_models import CreateTx, Transaction, TransactionValidation, TransactionsPagination
from app.domain.errors import (
    EmptyAddressError, EmptyTransactionIdError, InsufficientBalanceError, InvalidAmountError,
    InvalidNetworkError, InvalidPaginationError, InvalidTxAssetError, InvalidWalletPrivateKeyError,
    SameAddressError, WalletNotFoundError
)
from eth_typing import HexAddress
from ens.utils import HexStr
from app.domain.models import Pagination


class TestValidateTransaction:
    @pytest.mark.asyncio
    async def test_validate_transaction_success(self, mock_dependency_injection):
        mock_di = mock_dependency_injection
        mock_di.tx_uc.validate_transaction = AsyncMock(return_value=TransactionValidation(
            is_valid=True,
            transaction_hash="0xabc",
            transfers=[],
            validation_message="ok",
            network="ethereum"
        ))
        tx_hash = "0xabc"
        result = await validate_transaction(tx_hash=tx_hash, di=mock_di)
        assert result.is_valid is True
        mock_di.logger.info.assert_called_once_with(f"Validating transaction: {tx_hash}")

    @pytest.mark.asyncio
    async def test_validate_transaction_empty_address(self, mock_dependency_injection):
        mock_di = mock_dependency_injection
        mock_di.tx_uc.validate_transaction = AsyncMock(side_effect=EmptyAddressError("Empty address"))
        tx_hash = "0xabc"
        with pytest.raises(HTTPException) as exc_info:
            await validate_transaction(tx_hash=tx_hash, di=mock_di)
        assert exc_info.value.status_code == 400
        assert "Empty address" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_validate_transaction_db_not_initialized(self, mock_dependency_injection):
        mock_di = mock_dependency_injection
        mock_di.tx_uc.validate_transaction = AsyncMock(side_effect=RuntimeError("Database not initialized"))
        tx_hash = "0xabc"
        with pytest.raises(HTTPException) as exc_info:
            await validate_transaction(tx_hash=tx_hash, di=mock_di)
        assert exc_info.value.status_code == 503
        assert exc_info.value.detail == "Database not initialized"

    @pytest.mark.asyncio
    async def test_validate_transaction_general_error(self, mock_dependency_injection):
        mock_di = mock_dependency_injection
        mock_di.tx_uc.validate_transaction = AsyncMock(side_effect=Exception("General error"))
        tx_hash = "0xabc"
        with pytest.raises(HTTPException) as exc_info:
            await validate_transaction(tx_hash=tx_hash, di=mock_di)
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Unexpected error"
        mock_di.logger.error.assert_called_once()


class TestCreateTx:
    @pytest.mark.asyncio
    async def test_create_tx_success(self, mock_dependency_injection):
        mock_di = mock_dependency_injection
        tx = CreateTx(
            from_address=HexAddress(HexStr("0x1234567890123456789012345678901234567890")),
            to_address=HexAddress(HexStr("0x1234567890123456789012345678901234567890")),
            asset="ETH",
            amount=1.0
        )
        mock_di.tx_uc.create = AsyncMock(return_value=Transaction(id=uuid4(), tx_hash="0xabc"))
        result = await create_tx(tx=tx, di=mock_di)
        assert result.tx_hash == "0xabc"
        mock_di.logger.info.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("error,code", [
        (SameAddressError("0x1234567890123456789012345678901234567890"), 400),
        (EmptyAddressError("empty address"), 400),
        (InsufficientBalanceError("0x1234567890123456789012345678901234567890", 0.0, 1.0), 400),
        (InvalidNetworkError("ethereum"), 400),
        (InvalidWalletPrivateKeyError("bad key"), 400),
        (WalletNotFoundError("0x1234567890123456789012345678901234567890"), 400),
        (RuntimeError("db not initialized"), 503),
    ])
    async def test_create_tx_errors(self, mock_dependency_injection, error, code):
        mock_di = mock_dependency_injection
        tx = CreateTx(
            from_address=HexAddress(HexStr("0x1234567890123456789012345678901234567890")),
            to_address=HexAddress(HexStr("0x1234567890123456789012345678901234567890")),
            asset="ETH",
            amount=1.0
        )
        mock_di.tx_uc.create = AsyncMock(side_effect=error)
        with pytest.raises(HTTPException) as exc_info:
            await create_tx(tx=tx, di=mock_di)
        assert exc_info.value.status_code == code

    @pytest.mark.asyncio
    async def test_create_tx_general_error(self, mock_dependency_injection):
        mock_di = mock_dependency_injection
        tx = CreateTx(
            from_address=HexAddress(HexStr("0x1234567890123456789012345678901234567890")),
            to_address=HexAddress(HexStr("0x1234567890123456789012345678901234567890")),
            asset="ETH",
            amount=1.0
        )
        mock_di.tx_uc.create = AsyncMock(side_effect=Exception("General error"))
        with pytest.raises(HTTPException) as exc_info:
            await create_tx(tx=tx, di=mock_di)
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Unexpected error"


class TestGetTransactions:
    @pytest.mark.asyncio
    async def test_get_transactions_by_id(self, mock_dependency_injection):
        mock_di = mock_dependency_injection
        mock_di.tx_uc.get_by_id = AsyncMock(return_value=Transaction(id=uuid4(), tx_hash="0xabc"))
        result = await get_transactions(di=mock_di, transaction_id=uuid4())
        assert isinstance(result, Transaction)
        mock_di.tx_uc.get_by_id.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_transactions_by_tx_hash(self, mock_dependency_injection):
        mock_di = mock_dependency_injection
        mock_di.tx_uc.get_by_tx_hash = AsyncMock(return_value=Transaction(id=uuid4(), tx_hash="0xabc"))
        result = await get_transactions(di=mock_di, tx_hash="0xabc")
        assert isinstance(result, Transaction)
        mock_di.tx_uc.get_by_tx_hash.assert_called_once_with("0xabc")

    @pytest.mark.asyncio
    async def test_get_transactions_by_wallet_address(self, mock_dependency_injection):
        mock_di = mock_dependency_injection
        mock_di.tx_uc.get_txs = AsyncMock(return_value=[Transaction(id=uuid4(), tx_hash="0xabc")])
        result = await get_transactions(di=mock_di, wallet_address="0x123")
        assert isinstance(result, list)
        mock_di.tx_uc.get_txs.assert_called_once_with("0x123")

    @pytest.mark.asyncio
    async def test_get_transactions_pagination(self, mock_dependency_injection):
        mock_di = mock_dependency_injection
        mock_di.tx_uc.get_all = AsyncMock(return_value=TransactionsPagination(
            transactions=[],
            pagination=Pagination(total=0, page=1)
        ))
        result = await get_transactions(di=mock_di, page=1, limit=10)
        assert hasattr(result, 'transactions')
        mock_di.tx_uc.get_all.assert_called_once_with(page=1, limit=10)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("error,code", [
        (InvalidPaginationError("bad pagination"), 400),
        (EmptyAddressError("from"), 400),
        (EmptyTransactionIdError(), 400),
        (RuntimeError("db not initialized"), 503),
    ])
    async def test_get_transactions_errors(self, mock_dependency_injection, error, code):
        mock_di = mock_dependency_injection
        mock_di.tx_uc.get_all = AsyncMock(side_effect=error)
        with pytest.raises(HTTPException) as exc_info:
            await get_transactions(di=mock_di, page=1, limit=10)
        assert exc_info.value.status_code == code 