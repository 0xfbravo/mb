"""
Integration tests for health API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.presentation.api.routes import api_router


class TestHealthAPIIntegration:
    """Integration tests for health API endpoints."""

    @pytest.fixture
    def mock_di(self):
        """Create a mock dependency injection container."""
        di = MagicMock()
        di.logger = MagicMock()
        di.db_manager = MagicMock()
        return di

    @pytest.fixture
    def client(self, mock_di):
        """Create a test client with mocked dependencies."""
        from fastapi import FastAPI
        from app.utils.di import get_dependency_injection
        
        app = FastAPI()
        app.include_router(api_router)
        
        # Mock the dependency injection
        app.dependency_overrides[get_dependency_injection] = lambda: mock_di
        
        return TestClient(app)

    def test_health_success(self, client, mock_di):
        """Test successful health check."""
        # Arrange
        mock_di.is_database_initialized = MagicMock(return_value=True)
        mock_di.db_manager.get_pool_stats = AsyncMock(return_value={
            "pool_size": 5,
            "checked_in": 3,
            "checked_out": 2,
            "overflow": 0,
            "checkedout_overflows": 0,
            "returned_overflows": 0,
        })
        
        # Act
        response = client.get("/api/health/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Healthy"
        assert data["database"]["status"] == "healthy"
        assert data["database"]["pool_stats"]["pool_size"] == 5
        assert data["database"]["pool_stats"]["checked_in"] == 3

    def test_health_db_not_initialized(self, client, mock_di):
        """Test health check when database is not initialized."""
        # Arrange
        mock_di.is_database_initialized = MagicMock(return_value=False)
        
        # Act
        response = client.get("/api/health/")
        
        # Assert
        assert response.status_code == 503
        assert response.json()["detail"] == "Database not initialized"

    def test_health_pool_stats_error(self, client, mock_di):
        """Test health check when pool stats retrieval fails."""
        # Arrange
        mock_di.is_database_initialized = MagicMock(return_value=True)
        mock_di.db_manager.get_pool_stats = AsyncMock(side_effect=Exception("Pool error"))
        
        # Act
        response = client.get("/api/health/")
        
        # Assert
        assert response.status_code == 503
        assert response.json()["detail"] == "Database connection error"
        mock_di.logger.error.assert_called_once()

    def test_health_empty_pool_stats(self, client, mock_di):
        """Test health check with empty pool stats."""
        # Arrange
        mock_di.is_database_initialized = MagicMock(return_value=True)
        mock_di.db_manager.get_pool_stats = AsyncMock(return_value={})
        
        # Act
        response = client.get("/api/health/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Healthy"
        assert data["database"]["status"] == "healthy"
        assert data["database"]["pool_stats"] == {}

    def test_health_partial_pool_stats(self, client, mock_di):
        """Test health check with partial pool stats."""
        # Arrange
        mock_di.is_database_initialized = MagicMock(return_value=True)
        mock_di.db_manager.get_pool_stats = AsyncMock(return_value={
            "pool_size": 10,
            "checked_in": 5,
        })
        
        # Act
        response = client.get("/api/health/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Healthy"
        assert data["database"]["status"] == "healthy"
        assert data["database"]["pool_stats"]["pool_size"] == 10
        assert data["database"]["pool_stats"]["checked_in"] == 5 