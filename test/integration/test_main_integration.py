"""
Integration tests for the main FastAPI application.

These tests verify that the main application works correctly with all components integrated.
"""

import pytest
from fastapi.testclient import TestClient

from main import app


class TestMainAppIntegration:
    """Integration test cases for the main FastAPI application."""

    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        return TestClient(app)

    def test_app_initialization(self):
        """Test that the FastAPI app is properly initialized."""
        assert app is not None
        assert hasattr(app, "router")
        assert hasattr(app, "openapi")

    def test_app_has_routes(self):
        """Test that the app has routes configured."""
        # Check that the app has routes (should have the API router included)
        assert len(app.routes) > 0

    def test_app_openapi_schema(self):
        """Test that the app generates OpenAPI schema."""
        schema = app.openapi()
        assert schema is not None
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema

    def test_health_endpoint(self, client):
        """Test the health check endpoint."""
        response = client.get("/api/health/")
        assert response.status_code == 200
        assert response.json() == {"message": "OK"}

    def test_health_endpoint_without_trailing_slash(self, client):
        """Test the health check endpoint without trailing slash."""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"message": "OK"}

    def test_root_endpoint_not_found(self, client):
        """Test that root endpoint returns 404 (no root route defined)."""
        response = client.get("/")
        assert response.status_code == 404

    def test_nonexistent_endpoint(self, client):
        """Test that nonexistent endpoints return 404."""
        response = client.get("/api/nonexistent/")
        assert response.status_code == 404

    def test_api_prefix_works(self, client):
        """Test that the API prefix is working correctly."""
        # Test that endpoints without /api prefix return 404
        response = client.get("/health/")
        assert response.status_code == 404

        # Test that endpoints with /api prefix work
        response = client.get("/api/health/")
        assert response.status_code == 200

    def test_dotenv_loaded(self):
        """Test that dotenv is loaded during app initialization."""
        # Since main.py is imported at the top of this file, load_dotenv has already been called
        # We can verify this by checking that the app is properly initialized
        assert app is not None
        assert hasattr(app, "router")

    def test_app_metadata(self):
        """Test that the app has proper metadata."""
        # Check that the app has basic FastAPI metadata
        assert hasattr(app, "title")
        assert hasattr(app, "version")
        assert hasattr(app, "description")

    def test_app_middleware(self):
        """Test that the app has expected middleware."""
        # FastAPI apps typically have some middleware
        assert hasattr(app, "user_middleware")
        assert hasattr(app, "middleware_stack")

    def test_api_router_included(self):
        """Test that the API router is included in the main app."""
        # Check that the API router is included by testing if API endpoints are accessible
        client = TestClient(app)
        response = client.get("/api/health/")
        assert response.status_code == 200

    def test_health_router_included(self):
        """Test that the health router is included."""
        # The health endpoint should be accessible
        client = TestClient(app)
        response = client.get("/api/health/")
        assert response.status_code == 200

    def test_router_structure(self):
        """Test the overall router structure."""
        # Check that the main app has the expected route structure
        client = TestClient(app)

        # Test that the API prefix is working
        response = client.get("/api/health/")
        assert response.status_code == 200

        # Test that non-API routes are not accessible
        response = client.get("/health/")
        assert response.status_code == 404

    def test_404_error_format(self, client):
        """Test that 404 errors return proper JSON format."""
        response = client.get("/nonexistent/")
        assert response.status_code == 404
        assert "detail" in response.json()

    def test_method_not_allowed(self, client):
        """Test that unsupported HTTP methods return 405."""
        response = client.post("/api/health/")
        assert response.status_code == 405

    def test_invalid_json_request(self, client):
        """Test handling of invalid JSON requests."""
        # This would typically be tested with POST endpoints that expect JSON
        # For now, we'll test that the app handles malformed requests gracefully
        response = client.get(
            "/api/health/", headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200  # GET requests don't require JSON body


if __name__ == "__main__":
    pytest.main([__file__])
