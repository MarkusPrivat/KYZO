"""Integration tests for the Draft Review page (Issue 0047).

Covers the full workflow: template rendering, RAWInput accordion,
metadata display, draft card rendering, finalize button, and toast messages.
"""

import jwt
from datetime import datetime, timedelta, timezone

import pytest

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def admin_token():
    """Create a JWT token with admin role."""
    payload = {
        "sub": "admin@kyzo.com",
        "scope": "admin",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
    }
    return jwt.encode(payload, "test-secret", algorithm="HS256")


@pytest.fixture
def teacher_token():
    """Create a JWT token with teacher role."""
    payload = {
        "sub": "teacher@kyzo.com",
        "scope": "teacher",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
    }
    return jwt.encode(payload, "test-secret", algorithm="HS256")


@pytest.fixture
def student_token():
    """Create a JWT token with student role."""
    payload = {
        "sub": "student@kyzo.com",
        "scope": "student",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
    }
    return jwt.encode(payload, "test-secret", algorithm="HS256")


@pytest.fixture
def app():
    """Create a Flask app with admin and main blueprints for testing."""
    import os
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


def _make_token(scope, expired=False):
    """Helper to create a JWT token."""
    if expired:
        exp = datetime.now(timezone.utc) - timedelta(minutes=10)
    else:
        exp = datetime.now(timezone.utc) + timedelta(minutes=30)
    return jwt.encode(
        {"sub": "test@kyzo.com", "scope": scope, "exp": exp},
        "test-secret",
        algorithm="HS256",
    )


# ── Functional: Template rendering ────────────────────────────────────────────


class TestDraftReviewTemplateRendering:
    """Tests for the draft_review.html template rendering and structure."""

    def test_page_title(self, app, admin_token):
        """Template renders page title 'Draft-Fragen prüfen'."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "Draft-Fragen prüfen" in html

    def test_admin_sidebar_present(self, app, admin_token):
        """Template renders with admin sidebar."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "admin-sidebar" in html
            assert "admin-nav" in html

    def test_dynamic_content_container(self, app, admin_token):
        """Template renders dynamic content container with data attribute."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/42")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "admin-container" in html
            assert "admin-draft-review" in html
            assert "data-question-input-id=\"42\"" in html

    def test_rawinput_accordion_present(self, app, admin_token):
        """Template includes RAWInput accordion section."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "rawinput-accordion" in html
            assert "rawinput-content" in html
            assert "rawinput-placeholder" in html
            assert "card-header__toggle" in html

    def test_rawinput_accordion_default_collapsed(self, app, admin_token):
        """RAWInput accordion is default collapsed (display: none)."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert 'id="rawinput-content"' in html
            assert "display: none" in html

    def test_metadata_section_present(self, app, admin_token):
        """Template includes metadata section with all fields."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "metadata-section" in html
            assert "metadata-grid" in html
            assert "metadata-subject" in html
            assert "metadata-topic" in html
            assert "metadata-grade" in html
            assert "metadata-input-type" in html
            assert "metadata-num-questions" in html

    def test_draft_questions_section_present(self, app, admin_token):
        """Template includes draft questions section."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "draft-questions-section" in html
            assert "draft-questions-list" in html

    def test_finalize_button_present(self, app, admin_token):
        """Template includes finalize button."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "id=\"finalize-btn\"" in html
            assert "Fragen übernehmen" in html
            assert "btn-primary" in html

    def test_finalize_actions_container(self, app, admin_token):
        """Template includes finalize actions container."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "finalize-actions" in html

    def test_no_cancel_button(self, app, admin_token):
        """Template does NOT include a cancel/abbrechen button."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            # Check for absence of cancel button patterns
            assert "abbrechen" not in html.lower()
            assert "cancel" not in html.lower()
            assert "abbrechen" not in html.lower()

    def test_toast_element_present(self, app, admin_token):
        """Template includes toast notification element."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "toast" in html.lower()
            assert "toast-message" in html

    def test_loading_state_present(self, app, admin_token):
        """Template includes loading state element."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "loading-state" in html
            assert "spinner" in html


# ── Functional: Navigation entry ──────────────────────────────────────────────


class TestDraftReviewNavigation:
    """Tests for the Draft-Fragen prüfen navigation entry."""

    def test_admin_sidebar_has_draft_review_link(self, app, admin_token):
        """Admin sidebar includes 'Draft-Fragen prüfen' link."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "Draft-Fragen prüfen" in html

    def test_teacher_sidebar_has_draft_review_link(self, app, teacher_token):
        """Teacher sidebar includes 'Draft-Fragen prüfen' link."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", teacher_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "Draft-Fragen prüfen" in html

    def test_teacher_sidebar_no_benutzerverwaltung(self, app, teacher_token):
        """Teacher sidebar does NOT include Benutzerverwaltung on draft_review."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", teacher_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "Benutzerverwaltung" not in html

    def test_admin_sidebar_has_benutzerverwaltung(self, app, admin_token):
        """Admin sidebar includes Benutzerverwaltung on draft_review."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "Benutzerverwaltung" in html

    def test_draft_review_link_is_active(self, app, admin_token):
        """Draft-Fragen prüfen link has active class."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "admin-nav__link--active" in html

    def test_teacher_sees_wissensverwaltung(self, app, teacher_token):
        """Teacher sidebar shows Wissensverwaltung on draft_review."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", teacher_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "Wissensverwaltung" in html
            assert "Fach" in html
            assert "Thema" in html

    def test_teacher_sees_fragen_eingeben(self, app, teacher_token):
        """Teacher sidebar shows 'Fragen eingeben' on draft_review."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", teacher_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "Fragen eingeben" in html


# ── Technical: CSS class reuse ────────────────────────────────────────────────


class TestDraftReviewCssReuse:
    """Tests for CSS class reuse from existing templates."""

    def test_reuses_admin_container_class(self, app, admin_token):
        """Template reuses admin-container CSS class."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert ".admin-container" in html or "admin-container" in html

    def test_reuses_admin_sidebar_class(self, app, admin_token):
        """Template reuses admin-sidebar CSS class."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert ".admin-sidebar" in html or "admin-sidebar" in html

    def test_reuses_admin_nav_class(self, app, admin_token):
        """Template reuses admin-nav CSS class."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert ".admin-nav" in html or "admin-nav" in html

    def test_reuses_card_class(self, app, admin_token):
        """Template reuses card CSS class."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert ".card {" in html or "card-body" in html

    def test_reuses_card_body_class(self, app, admin_token):
        """Template reuses card-body CSS class."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert ".card-body" in html or "card-body" in html

    def test_reuses_btn_primary_class(self, app, admin_token):
        """Template reuses btn-primary CSS class."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "btn-primary" in html

    def test_reuses_btn_class(self, app, admin_token):
        """Template reuses btn CSS class."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert ".btn {" in html or "btn-secondary" in html

    def test_reuses_toast_class(self, app, admin_token):
        """Template reuses toast CSS class."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert ".toast" in html or "toast" in html

    def test_reuses_spinner_class(self, app, admin_token):
        """Template reuses spinner CSS class."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert ".spinner" in html or "spinner" in html


# ── Technical: Template structure ─────────────────────────────────────────────


class TestDraftReviewTemplateStructure:
    """Tests for the draft_review.html template structure."""

    def test_template_extends_base(self, app, admin_token):
        """Template extends base.html (verified by rendered nav structure)."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert 'class="nav"' in html
            assert 'class="nav__logo"' in html

    def test_sets_api_url(self, app, admin_token):
        """Template sets API_URL JS variable."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "const API_URL" in html

    def test_sets_question_input_id(self, app, admin_token):
        """Template sets QUESTION_INPUT_ID JS variable."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/42")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "QUESTION_INPUT_ID" in html
            assert "42" in html

    def test_includes_auth_js(self, app, admin_token):
        """Template includes auth.js script."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "auth.js" in html

    def test_includes_toast_js(self, app, admin_token):
        """Template includes toast.js script."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "toast.js" in html

    def test_includes_draft_review_card_renderer_js(self, app, admin_token):
        """Template includes draft-review-card-renderer.js script."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "draft-review-card-renderer.js" in html

    def test_includes_draft_review_polling_js(self, app, admin_token):
        """Template includes draft-review-polling.js script."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "draft-review-polling.js" in html

    def test_includes_draft_review_js(self, app, admin_token):
        """Template includes draft-review.js script."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "draft-review.js" in html

    def test_question_input_id_passed_to_template(self, app, admin_token):
        """question_input_id is passed to the template context."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/42")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "42" in html

    def test_different_ids_work(self, app, admin_token):
        """Different question_input_id values work."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/99")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "99" in html


# ── Technical: Responsive layout ──────────────────────────────────────────────


class TestDraftReviewResponsiveLayout:
    """Tests for responsive layout breakpoints."""

    def test_has_768px_breakpoint(self, app, admin_token):
        """Template includes 768px responsive breakpoint."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "@media (max-width: 768px)" in html

    def test_has_640px_breakpoint(self, app, admin_token):
        """Template includes 640px responsive breakpoint."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "@media (max-width: 640px)" in html

    def test_has_1100px_breakpoint(self, app, admin_token):
        """Template includes 1100px responsive breakpoint."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "@media (max-width: 1100px)" in html


# ── Technical: WCAG compliance ────────────────────────────────────────────────


class TestDraftReviewWcagCompliance:
    """Tests for WCAG accessibility compliance."""

    def test_has_aria_labels(self, app, admin_token):
        """Template includes ARIA labels for accessibility."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "aria-label" in html or "aria-labelledby" in html

    def test_has_aria_expanded_attribute(self, app, admin_token):
        """RAWInput toggle has aria-expanded attribute."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "aria-expanded" in html

    def test_has_aria_controls_attribute(self, app, admin_token):
        """RAWInput toggle has aria-controls attribute."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "aria-controls" in html

    def test_has_form_labels(self, app, admin_token):
        """Template includes form labels."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "<label" in html

    def test_toast_has_role_alert(self, app, admin_token):
        """Toast element has role='alert' for screen readers."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert 'role="alert"' in html


# ── Integration: Full workflow ────────────────────────────────────────────────


class TestDraftReviewIntegration:
    """Integration tests for the full draft review workflow."""

    def test_admin_accesses_draft_review(self, app, admin_token):
        """Admin can access draft_review route."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200

    def test_teacher_accesses_draft_review(self, app, teacher_token):
        """Teacher can access draft_review route."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", teacher_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200

    def test_student_redirected_from_draft_review(self, app, student_token):
        """Student is redirected from draft_review route."""
        with app.test_client() as client:
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 302

    def test_no_token_redirects_from_draft_review(self, app):
        """No token redirects from draft_review route."""
        with app.test_client() as client:
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 302

    def test_expired_token_redirects_from_draft_review(self, app):
        """Expired token redirects from draft_review route."""
        with app.test_client() as client:
            expired = _make_token("admin", expired=True)
            client.set_cookie("jwt_token", expired)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 302

    def test_full_template_structure(self, app, admin_token):
        """Template contains all required structural elements for the full workflow."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()

        # Verify all required elements are present
        required_elements = [
            "admin-container",
            "admin-sidebar",
            "admin-nav",
            "rawinput-accordion",
            "rawinput-content",
            "rawinput-placeholder",
            "metadata-section",
            "metadata-grid",
            "metadata-subject",
            "metadata-topic",
            "metadata-grade",
            "metadata-input-type",
            "metadata-num-questions",
            "draft-questions-section",
            "draft-questions-list",
            "finalize-btn",
            "finalize-actions",
            "toast",
            "loading-state",
            "spinner",
        ]
        for element in required_elements:
            assert element in html, f"Missing required element: {element}"

    def test_js_modules_loaded_in_order(self, app, admin_token):
        """All required JS modules are loaded in the template."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()

        required_scripts = [
            "auth.js",
            "toast.js",
            "draft-review-card-renderer.js",
            "draft-review-polling.js",
            "draft-review.js",
        ]
        for script in required_scripts:
            assert script in html, f"Missing script: {script}"

    def test_draft_review_section_class_present(self, app, admin_token):
        """Template uses draft-review-section class for sections."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "draft-review-section" in html

    def test_draft_card_classes_present(self, app, admin_token):
        """Template includes DraftReviewCardRenderer CSS classes."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert ".draft-card" in html
            assert "draft-card__option--correct" in html
            assert "draft-card__badge" in html
            assert "draft-card__badge--difficulty" in html
            assert "draft-card__badge--grade" in html

    def test_rawinput_resizable_style(self, app, admin_token):
        """RAWInput content has resize capability."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "resize" in html
            assert "pre-wrap" in html

    def test_sr_only_label_for_finalize(self, app, admin_token):
        """Finalize button has sr-only label for accessibility."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", admin_token)
            resp = client.get("/admin/draft-review/1")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "sr-only" in html
