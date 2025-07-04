"""
Unit tests for the main application module.

These tests verify individual functions and components in isolation.
"""

from unittest.mock import MagicMock, patch

import pytest


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

    def test_router_import_successful(self):
        """Test that the router import is successful."""
        import main

        # This test verifies that the import doesn't raise an exception
        assert True

    def test_module_imports_work(self):
        """Test that all required modules can be imported."""
        # Test that dotenv can be imported
        from dotenv import load_dotenv

        assert load_dotenv is not None

        # Test that FastAPI can be imported
        from fastapi import FastAPI

        assert FastAPI is not None

        # Test that our router can be imported
        from app.presentation.api import router

        assert router is not None

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
        assert app.title == "FastAPI"
        assert app.version == "0.1.0"
        assert app.description is not None

    def test_router_structure(self):
        """Test that the router structure is correct."""
        from app.presentation.api import router

        # Test that the router has the expected prefix
        assert router.prefix == "/api"

        # Test that the router has routes
        assert len(router.routes) > 0


if __name__ == "__main__":
    pytest.main([__file__])
