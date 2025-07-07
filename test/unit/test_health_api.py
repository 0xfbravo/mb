"""
Unit tests for health API endpoints.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.presentation.api.health import health


class TestHealth:
    @pytest.mark.asyncio
    async def test_health_success(self, mock_dependency_injection):
        mock_di = mock_dependency_injection
        mock_di.is_database_initialized = MagicMock(return_value=True)
        mock_di.db_manager.get_pool_stats = AsyncMock(return_value={"pool_size": 5})
        result = await health(di=mock_di)
        assert result["message"] == "Healthy"
        assert result["database"]["status"] == "healthy"
        assert result["database"]["pool_stats"] == {"pool_size": 5}

    @pytest.mark.asyncio
    async def test_health_db_not_initialized(self, mock_dependency_injection):
        mock_di = mock_dependency_injection
        mock_di.is_database_initialized = MagicMock(return_value=False)
        with pytest.raises(HTTPException) as exc_info:
            await health(di=mock_di)
        assert exc_info.value.status_code == 503
        assert exc_info.value.detail == "Database not initialized"

    @pytest.mark.asyncio
    async def test_health_pool_stats_error(self, mock_dependency_injection):
        mock_di = mock_dependency_injection
        mock_di.is_database_initialized = MagicMock(return_value=True)
        mock_di.db_manager.get_pool_stats = AsyncMock(
            side_effect=Exception("Pool error")
        )
        mock_di.logger.error = MagicMock()
        with pytest.raises(HTTPException) as exc_info:
            await health(di=mock_di)
        assert exc_info.value.status_code == 503
        assert exc_info.value.detail == "Database connection error"
        mock_di.logger.error.assert_called_once()
