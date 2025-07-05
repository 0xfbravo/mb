"""
Integration tests for the main FastAPI application.

These tests verify that the main application works correctly with all components integrated.
"""

import asyncio
import os
import pytest
import pytest_asyncio
from dotenv import load_dotenv
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport, Response

from app import DependencyInjection, router, setup_loguru

load_dotenv()


class TestMainAppIntegration:
    """Integration test cases for the main FastAPI application."""

    @pytest.fixture(scope="session")
    def test_app(self):
        """Create a test FastAPI app with TEST database configuration."""
        setup_loguru()
        app = FastAPI()
        app.include_router(router)
        return app

    @pytest_asyncio.fixture
    async def di_session(self):
        """Initialize the DI for each test function."""
        db_name = os.getenv("POSTGRES_DB")
        db_user = os.getenv("POSTGRES_USER")
        db_password = os.getenv("POSTGRES_PASSWORD")
        db_host = os.getenv("POSTGRES_HOST")
        db_port = os.getenv("POSTGRES_PORT")

        if not all([db_name, db_user, db_password, db_host, db_port]):
            raise ValueError("Missing environment variables for database configuration")

        di = DependencyInjection()
        try:
            await di.initialize(
                db_name=str(db_name),
                db_user=str(db_user),
                db_password=str(db_password),
                db_host=str(db_host),
                db_port=int(str(db_port)),
            )
            di.logger.info("DI initialized successfully with TEST database.")
        except Exception as e:
            di.logger.error(f"Error during DI startup: {e}")
            raise e

        yield di

        try:
            await di.shutdown()
            di.logger.info("DI shutdown successfully after test.")
        except Exception as e:
            di.logger.error(f"Error during DI shutdown: {e}")

    @pytest_asyncio.fixture
    async def client(self, test_app: FastAPI, di_session):
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    def test_app_initialization(self, test_app):
        """Test that the FastAPI app is properly initialized."""
        assert test_app is not None
        assert hasattr(test_app, "router")
        assert hasattr(test_app, "openapi")

    def test_app_openapi_schema(self, test_app):
        """Test that the OpenAPI schema is properly generated."""
        schema = test_app.openapi()
        assert schema and "openapi" in schema and "info" in schema and "paths" in schema

    @pytest.mark.asyncio
    async def test_database_connection_health(self, di_session):
        """Test that the database connection is working."""
        pool_stats = await di_session.db_manager.get_pool_stats()
        assert pool_stats

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """Test the health endpoint functionality."""
        response = await client.get("/api/health/")
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            assert response.json().get("message") == "Healthy"

    @pytest.mark.asyncio
    async def test_api_routing_structure(self, client):
        """Test that API routing is working correctly."""
        # Test that non-API routes return 404
        assert (await client.get("/health/")).status_code == 404
        assert (await client.get("/")).status_code == 404
        
        # Test that API routes are accessible
        response = await client.get("/api/health/")
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_error_handling(self, client):
        """Test error handling for various scenarios."""
        # Test 404 for nonexistent endpoints
        response = await client.get("/api/nonexistent/")
        assert response.status_code == 404
        assert "detail" in response.json()

        # Test 405 for wrong HTTP method
        response = await client.post("/api/health/")
        assert response.status_code == 405

    @pytest.mark.asyncio
    async def test_endpoint_accessibility(self, client):
        """Test that all main endpoints are accessible."""
        # Test health endpoint
        response = await client.get("/api/health/")
        assert response.status_code in [200, 500]

        # Test wallet endpoint
        response = await client.get("/api/wallet/")
        assert response.status_code in [200, 400, 405]

        # Test transaction endpoint
        response = await client.get("/api/tx/")
        assert response.status_code in [200, 400, 405]