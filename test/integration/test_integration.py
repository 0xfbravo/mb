"""
Integration tests for the application.

These tests verify that different components work together correctly.
"""

import pytest
from fastapi.testclient import TestClient

from main import app


class TestIntegration:
    """Integration test cases."""

    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        return TestClient(app)

    def test_health_endpoint_integration(self, client):
        """Test that the health endpoint works in an integrated manner."""
        response = client.get("/api/health/")
        assert response.status_code == 200
        assert response.json() == {"message": "OK"}

    def test_api_structure_integration(self, client):
        """Test that the API structure is properly integrated."""
        # Test that the API prefix is working
        response = client.get("/api/health/")
        assert response.status_code == 200

        # Test that non-API routes are not accessible
        response = client.get("/health/")
        assert response.status_code == 404
