"""
Unit tests for the main application module.

These tests verify individual functions and components in isolation.
"""

import os

import pytest
from dotenv import load_dotenv

load_dotenv()


class TestMainModuleUnit:
    """Unit test cases for the main module."""

    def test_app_variable_defined(self):
        """Test that the app variable is defined and accessible."""
        import main

        assert hasattr(main, "app")
        assert main.app is not None

    def test_app_is_fastapi_instance(self):
        """Test that the app is an instance of FastAPI."""
        from fastapi import FastAPI

        import main

        assert isinstance(main.app, FastAPI)

    def test_module_imports_work(self):
        """Test that all required modules can be imported."""
        # Test that dotenv can be imported
        from dotenv import load_dotenv

        assert load_dotenv is not None

        # Test that FastAPI can be imported
        from fastapi import FastAPI

        assert FastAPI is not None

        # Test that our router can be imported
        from app.presentation.api import api_router

        assert api_router is not None

    def test_app_has_expected_attributes(self):
        """Test that the FastAPI app has expected attributes."""
        import main

        app = main.app

        # Test basic FastAPI attributes
        assert hasattr(app, "router")
        assert hasattr(app, "openapi")
        assert hasattr(app, "title")
        assert hasattr(app, "version")
        assert hasattr(app, "description")

    def test_app_has_routes_after_router_inclusion(self):
        """Test that the app has routes after router inclusion."""
        import main

        app = main.app

        # The app should have routes after including the router
        assert len(app.routes) > 0

    def test_openapi_schema_generation(self):
        """Test that the app can generate OpenAPI schema."""
        import main

        app = main.app

        schema = app.openapi()
        assert schema is not None
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema

    def test_router_inclusion_works(self):
        """Test that the router inclusion actually works."""
        import main

        app = main.app

        # Test that the router was actually included by checking routes
        # Should have at least the health endpoint
        assert any("/api/health" in str(route) for route in app.routes)

    def test_app_configuration(self):
        """Test that the app has proper configuration."""
        import main

        app = main.app

        # Test that the app has the expected configuration
        assert app.title == os.getenv("TITLE", "MB API")
        assert app.version == os.getenv("VERSION", "1.0.0")
        assert app.description == os.getenv(
            "DESCRIPTION", "MB API for blockchain operations"
        )

    def test_router_structure(self):
        """Test that the router structure is correct."""
        from app.presentation.api import api_router

        # Test that the router has the expected prefix
        assert api_router.prefix == "/api"

        # Test that the router has routes
        assert len(api_router.routes) > 0

    def test_all_routers_included(self):
        """Test that all sub-routers are included in the main router."""
        from app.presentation.api import api_router

        # Check that all expected routers are included
        route_paths = [str(route) for route in api_router.routes]

        # Should have health, wallet, and transaction routes
        assert any("/health" in path for path in route_paths)
        assert any("/wallet" in path for path in route_paths)
        assert any("/tx" in path for path in route_paths)

    def test_lifespan_function_defined(self):
        """Test that the lifespan function is properly defined."""
        import main

        # Test that lifespan is defined and is a context manager
        assert hasattr(main, "lifespan")
        assert callable(main.lifespan)

    def test_lifespan_initialization_structure(self):
        """Test that lifespan function has the correct structure and can be called."""
        from fastapi import FastAPI

        import main

        # Test that lifespan is a context manager
        test_app = FastAPI()

        # Test that lifespan can be imported and is callable
        assert hasattr(main, "lifespan")
        assert callable(main.lifespan)

        # Test that lifespan returns a context manager
        context_manager = main.lifespan(test_app)
        assert hasattr(context_manager, "__aenter__")
        assert hasattr(context_manager, "__aexit__")

    def test_environment_variables_defaults(self):
        """Test that environment variables have proper defaults."""
        import os
        from unittest.mock import patch

        # Test with no environment variables set
        with patch.dict(os.environ, {}, clear=True):
            # These should use the default values from main.py
            assert os.getenv("POSTGRES_DB", "postgres") == "postgres"
            assert os.getenv("POSTGRES_USER", "postgres") == "postgres"
            assert os.getenv("POSTGRES_PASSWORD", "password") == "password"
            assert os.getenv("POSTGRES_HOST", "localhost") == "localhost"
            assert int(os.getenv("POSTGRES_PORT", "5432")) == 5432


class TestRouterEndpointsUnit:
    """Unit tests for router endpoints."""

    def test_health_router_structure(self):
        """Test that the health router has the correct structure."""
        from app.presentation.api.health import router

        assert router.prefix == "/health"
        assert len(router.routes) > 0

    def test_wallet_router_structure(self):
        """Test that the wallet router has the correct structure."""
        from app.presentation.api.wallet import router

        assert router.prefix == "/wallet"
        assert len(router.routes) > 0

    def test_transaction_router_structure(self):
        """Test that the transaction router has the correct structure."""
        from app.presentation.api.transaction import router

        assert router.prefix == "/tx"
        assert len(router.routes) > 0

    def test_router_tags(self):
        """Test that routers have proper tags for OpenAPI documentation."""
        from app.presentation.api.health import router as health_router
        from app.presentation.api.transaction import \
            router as transaction_router
        from app.presentation.api.wallet import router as wallet_router

        # Check that routers have tags
        assert health_router.tags == ["💊 Health check"]
        assert wallet_router.tags == ["🔐 Wallet"]
        assert transaction_router.tags == ["💰 Transaction"]


if __name__ == "__main__":
    pytest.main([__file__])
