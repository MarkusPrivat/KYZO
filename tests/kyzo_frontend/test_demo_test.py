"""Integration tests for the Demo Test route (Issue 048).

Covers: template rendering, test_id handling, API_URL injection, and route accessibility.
"""

import os

import pytest


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def app():
    """Create a Flask app with admin and main blueprints for testing."""
    from flask import Flask

    template_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "apps",
        "kyzo_frontend",
        "templates",
    )
    app = Flask(__name__, template_folder=template_dir)
    app.config["SECRET_KEY"] = "test-secret"
    app.config["API_URL"] = "http://localhost:8000/api/v1"
    app.config["AUTH_SECRET_KEY"] = "test-secret"

    from apps.kyzo_frontend.routes.admin import admin_bp
    from apps.kyzo_frontend.routes.main import main_bp

    app.register_blueprint(admin_bp)
    app.register_blueprint(main_bp)

    return app


# ── Functional: Template rendering ────────────────────────────────────────────


class TestDemoTestTemplateRendering:
    """Tests for the demo_test.html template rendering and structure."""

    def test_route_renders_with_valid_test_id(self, app):
        """Route /demo-test?test_id=1 renders with status 200."""
        with app.test_client() as client:
            resp = client.get("/demo-test?test_id=1")
            assert resp.status_code == 200

    def test_route_renders_with_different_test_id(self, app):
        """Route /demo-test works with different valid test IDs."""
        with app.test_client() as client:
            resp = client.get("/demo-test?test_id=42")
            assert resp.status_code == 200

    def test_route_renders_without_test_id(self, app):
        """Route /demo-test without test_id renders without error."""
        with app.test_client() as client:
            resp = client.get("/demo-test")
            assert resp.status_code == 200

    def test_route_extends_base_template(self, app):
        """Template extends base.html (verified by rendered nav structure)."""
        with app.test_client() as client:
            resp = client.get("/demo-test?test_id=1")
            html = resp.data.decode()
            assert 'class="nav"' in html

    def test_route_includes_footer(self, app):
        """Template includes footer (extends base.html)."""
        with app.test_client() as client:
            resp = client.get("/demo-test?test_id=1")
            html = resp.data.decode()
            assert "footer" in html.lower()


# ── Functional: test_id handling ──────────────────────────────────────────────


class TestDemoTestIdHandling:
    """Tests for test_id query parameter handling."""

    def test_valid_test_id_passed_to_template(self, app):
        """Valid test_id is present in rendered HTML."""
        with app.test_client() as client:
            resp = client.get("/demo-test?test_id=123")
            html = resp.data.decode()
            assert "123" in html

    def test_missing_test_id_is_none(self, app):
        """Missing test_id renders without error (treated as None)."""
        with app.test_client() as client:
            resp = client.get("/demo-test")
            assert resp.status_code == 200

    def test_empty_test_id_treated_as_none(self, app):
        """Empty string test_id renders without error."""
        with app.test_client() as client:
            resp = client.get("/demo-test?test_id=")
            assert resp.status_code == 200


# ── Technical: API_URL injection ──────────────────────────────────────────────


class TestDemoTestApiUrlInjection:
    """Tests for API_URL JS constant injection."""

    def test_api_url_js_constant_present(self, app):
        """Template sets const API_URL JS variable."""
        with app.test_client() as client:
            resp = client.get("/demo-test?test_id=1")
            html = resp.data.decode()
            assert "const API_URL" in html

    def test_api_url_value_from_config(self, app):
        """API_URL value matches Flask config."""
        with app.test_client() as client:
            resp = client.get("/demo-test?test_id=1")
            html = resp.data.decode()
            assert "http://localhost:8000/api/v1" in html


# ── Deep Interface: Route registration ────────────────────────────────────────


class TestDemoTestRouteRegistration:
    """Tests for route being registered on main_bp."""

    def test_route_accessible_at_demo_test(self, app):
        """GET /demo-test returns 200 (route is registered)."""
        with app.test_client() as client:
            resp = client.get("/demo-test?test_id=1")
            assert resp.status_code == 200

    def test_route_not_accessible_via_post(self, app):
        """POST /demo-test returns method not allowed (GET only)."""
        with app.test_client() as client:
            resp = client.post("/demo-test?test_id=1")
            assert resp.status_code == 405
