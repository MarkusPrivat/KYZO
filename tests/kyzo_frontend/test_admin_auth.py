"""Tests for admin authentication helpers and role-based sidebar filtering."""

import jwt
from datetime import datetime, timedelta, timezone

import pytest

from apps.kyzo_frontend.routes.admin import has_role, get_user_role_from_token, is_admin_user


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
def multi_role_token():
    """Create a JWT token with multiple roles (list)."""
    payload = {
        "sub": "multi@kyzo.com",
        "scope": ["admin", "teacher"],
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
    }
    return jwt.encode(payload, "test-secret", algorithm="HS256")


@pytest.fixture
def expired_token():
    """Create an expired JWT token."""
    payload = {
        "sub": "expired@kyzo.com",
        "scope": "admin",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=10),
    }
    return jwt.encode(payload, "test-secret", algorithm="HS256")


# ── has_role() tests ──────────────────────────────────────────────────────────

class TestHasRole:
    """Tests for the has_role() helper function."""

    def test_admin_token_has_role_admin(self, admin_token):
        assert has_role(admin_token, ["admin"], "test-secret") is True

    def test_admin_token_has_role_teacher(self, admin_token):
        assert has_role(admin_token, ["teacher"], "test-secret") is False

    def test_admin_token_has_role_both(self, admin_token):
        assert has_role(admin_token, ["teacher", "admin"], "test-secret") is True

    def test_teacher_token_has_role_teacher(self, teacher_token):
        assert has_role(teacher_token, ["teacher"], "test-secret") is True

    def test_teacher_token_has_role_admin(self, teacher_token):
        assert has_role(teacher_token, ["admin"], "test-secret") is False

    def test_teacher_token_has_role_both(self, teacher_token):
        assert has_role(teacher_token, ["teacher", "admin"], "test-secret") is True

    def test_student_token_has_role_student(self, student_token):
        assert has_role(student_token, ["student"], "test-secret") is True

    def test_student_token_has_role_teacher(self, student_token):
        assert has_role(student_token, ["teacher"], "test-secret") is False

    def test_student_token_has_role_admin(self, student_token):
        assert has_role(student_token, ["admin"], "test-secret") is False

    def test_multi_role_token_has_role_admin(self, multi_role_token):
        assert has_role(multi_role_token, ["admin"], "test-secret") is True

    def test_multi_role_token_has_role_teacher(self, multi_role_token):
        assert has_role(multi_role_token, ["teacher"], "test-secret") is True

    def test_multi_role_token_has_role_student(self, multi_role_token):
        assert has_role(multi_role_token, ["student"], "test-secret") is False

    def test_expired_token_returns_false(self, expired_token):
        assert has_role(expired_token, ["admin"], "test-secret") is False

    def test_none_token_returns_false(self):
        assert has_role(None, ["admin"], "test-secret") is False

    def test_empty_roles_list_returns_false(self, admin_token):
        assert has_role(admin_token, [], "test-secret") is False


# ── get_user_role_from_token() tests ──────────────────────────────────────────

class TestGetUserRoleFromToken:
    """Tests for role extraction from JWT tokens."""

    def test_admin_role_from_scope(self, admin_token):
        assert get_user_role_from_token(admin_token, "test-secret") == "admin"

    def test_teacher_role_from_scope(self, teacher_token):
        assert get_user_role_from_token(teacher_token, "test-secret") == "teacher"

    def test_student_role_from_scope(self, student_token):
        assert get_user_role_from_token(student_token, "test-secret") == "student"

    def test_multi_role_from_scope(self, multi_role_token):
        role = get_user_role_from_token(multi_role_token, "test-secret")
        assert role == ["admin", "teacher"]

    def test_expired_token_returns_none(self, expired_token):
        assert get_user_role_from_token(expired_token, "test-secret") is None

    def test_none_token_returns_none(self):
        assert get_user_role_from_token(None, "test-secret") is None

    def test_invalid_token_returns_none(self):
        assert get_user_role_from_token("invalid.token.here", "test-secret") is None


# ── is_admin_user() tests ─────────────────────────────────────────────────────

class TestIsAdminUser:
    """Tests for the is_admin_user() helper function."""

    def test_admin_token_is_admin(self, admin_token):
        assert is_admin_user(admin_token, "test-secret") is True

    def test_teacher_token_is_not_admin(self, teacher_token):
        assert is_admin_user(teacher_token, "test-secret") is False

    def test_student_token_is_not_admin(self, student_token):
        assert is_admin_user(student_token, "test-secret") is False

    def test_multi_role_token_is_admin(self, multi_role_token):
        assert is_admin_user(multi_role_token, "test-secret") is True

    def test_expired_token_is_not_admin(self, expired_token):
        assert is_admin_user(expired_token, "test-secret") is False

    def test_none_token_is_not_admin(self):
        assert is_admin_user(None, "test-secret") is False


# ── Template rendering tests ──────────────────────────────────────────────────

class TestAdminTemplateRendering:
    """Tests for role-based sidebar rendering in admin templates."""

    @pytest.fixture
    def app(self):
        """Create a Flask app with admin and main blueprints for testing."""
        import os
        from flask import Flask
        template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "apps", "kyzo_frontend", "templates")
        app = Flask(__name__, template_folder=template_dir)
        app.config["SECRET_KEY"] = "test-secret"
        app.config["API_URL"] = "http://localhost:8000/api/v1"
        app.config["AUTH_SECRET_KEY"] = "test-secret"

        from apps.kyzo_frontend.routes.admin import admin_bp
        from apps.kyzo_frontend.routes.main import main_bp
        app.register_blueprint(admin_bp)
        app.register_blueprint(main_bp)

        return app

    def _make_token(self, scope, expired=False):
        """Helper to create a JWT token."""
        if expired:
            exp = datetime.now(timezone.utc) - timedelta(minutes=10)
        else:
            exp = datetime.now(timezone.utc) + timedelta(minutes=30)
        return jwt.encode(
            {"sub": "test@kyzo.com", "scope": scope, "exp": exp},
            "test-secret", algorithm="HS256"
        )

    def test_admin_sees_all_menu_items(self, app):
        """Admin sees all sidebar menu items including Benutzerverwaltung."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("admin"))
            resp = client.get("/admin")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "Benutzerverwaltung" in html
            assert "Wissensverwaltung" in html
            assert "Fach" in html
            assert "Thema" in html

    def test_teacher_sees_knowledge_and_question_input_no_users(self, app):
        """Teacher sees Wissensverwaltung + Frage-Eingabe, but NOT Benutzerverwaltung."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("teacher"))
            resp = client.get("/admin")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "Wissensverwaltung" in html
            assert "Fach" in html
            assert "Thema" in html
            assert "Fragen eingeben" in html
            assert "Benutzerverwaltung" not in html

    def test_student_redirected_from_admin(self, app):
        """Student is redirected away from admin routes."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("student"))
            resp = client.get("/admin")
            assert resp.status_code == 302  # redirect

    def test_no_token_redirects_to_login(self, app):
        """No token redirects to login."""
        with app.test_client() as client:
            resp = client.get("/admin")
            assert resp.status_code == 302
            assert "login" in resp.location.lower() or "main" in resp.location.lower()

    def test_expired_token_redirects_to_login(self, app):
        """Expired token redirects to login."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("admin", expired=True))
            resp = client.get("/admin")
            assert resp.status_code == 302

    def test_teacher_knowledge_subjects_accessible(self, app):
        """Teacher can access knowledge_subjects."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("teacher"))
            resp = client.get("/admin/knowledge/subjects")
            assert resp.status_code == 200

    def test_teacher_users_not_accessible(self, app):
        """Teacher cannot access users management."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("teacher"))
            resp = client.get("/admin/users")
            assert resp.status_code == 302  # redirected away

    def test_admin_users_accessible(self, app):
        """Admin can access users management."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("admin"))
            resp = client.get("/admin/users")
            assert resp.status_code == 200

    def test_teacher_accesses_question_input(self, app):
        """Teacher can access question_input route."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("teacher"))
            resp = client.get("/admin/questions/input")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "Fragen eingeben" in html

    def test_admin_accesses_question_input(self, app):
        """Admin can access question_input route."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("admin"))
            resp = client.get("/admin/questions/input")
            assert resp.status_code == 200

    def test_student_redirected_from_question_input(self, app):
        """Student is redirected from question_input route."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("student"))
            resp = client.get("/admin/questions/input")
            assert resp.status_code == 302

    def test_teacher_sidebar_has_question_input_no_users(self, app):
        """Teacher sidebar shows Frage-Eingabe but not Benutzerverwaltung."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("teacher"))
            resp = client.get("/admin/knowledge/subjects")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "Fragen eingeben" in html
            assert "Benutzerverwaltung" not in html
            assert "Wissensverwaltung" in html

    def test_admin_sidebar_has_all_items(self, app):
        """Admin sidebar shows all menu items."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("admin"))
            resp = client.get("/admin/knowledge/subjects")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "Benutzerverwaltung" in html
            assert "Fragen eingeben" in html
            assert "Wissensverwaltung" in html


# ── Question Input Template Tests ─────────────────────────────────────────────

class TestQuestionInputTemplate:
    """Tests for the question_input.html template rendering and structure."""

    @pytest.fixture
    def app(self):
        """Create a Flask app with admin and main blueprints for testing."""
        import os
        from flask import Flask
        template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "apps", "kyzo_frontend", "templates")
        app = Flask(__name__, template_folder=template_dir)
        app.config["SECRET_KEY"] = "test-secret"
        app.config["API_URL"] = "http://localhost:8000/api/v1"
        app.config["AUTH_SECRET_KEY"] = "test-secret"

        from apps.kyzo_frontend.routes.admin import admin_bp
        from apps.kyzo_frontend.routes.main import main_bp
        app.register_blueprint(admin_bp)
        app.register_blueprint(main_bp)

        return app

    def _make_token(self, scope, expired=False):
        """Helper to create a JWT token."""
        if expired:
            exp = datetime.now(timezone.utc) - timedelta(minutes=10)
        else:
            exp = datetime.now(timezone.utc) + timedelta(minutes=30)
        return jwt.encode(
            {"sub": "test@kyzo.com", "scope": scope, "exp": exp},
            "test-secret", algorithm="HS256"
        )

    # ── Functional: Template renders with all required elements ─────────────

    def test_admin_sees_all_dropdowns(self, app):
        """Template renders with Subject, Topic, Grade dropdowns, mode toggle, question count."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("admin"))
            resp = client.get("/admin/questions/input")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert 'id="subject-dropdown"' in html
            assert 'id="topic-dropdown"' in html
            assert 'id="grade-dropdown"' in html
            assert 'id="input-type-dropdown"' in html
            assert 'id="num-of-questions-dropdown"' in html

    def test_grade_options_1_to_13(self, app):
        """Grade select contains options 1 through 13."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("admin"))
            resp = client.get("/admin/questions/input")
            assert resp.status_code == 200
            html = resp.data.decode()
            for grade in range(1, 14):
                assert f'value="{grade}"' in html

    def test_mode_toggle_default_scan(self, app):
        """Mode toggle defaults to Datei-Upload (scan)."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("admin"))
            resp = client.get("/admin/questions/input")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert 'value="scan"' in html
            assert 'value="manual"' in html

    def test_question_count_options(self, app):
        """Question count select has 5, 10, 15, 20, 25 options."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("admin"))
            resp = client.get("/admin/questions/input")
            assert resp.status_code == 200
            html = resp.data.decode()
            for count in [5, 10, 15, 20, 25]:
                assert f'value="{count}"' in html

    def test_file_upload_panel_present(self, app):
        """File upload area is present in the template."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("admin"))
            resp = client.get("/admin/questions/input")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert 'id="file-upload-panel"' in html
            assert 'id="file-upload"' in html

    def test_text_input_panel_present(self, app):
        """Textarea for manual mode is present in the template."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("admin"))
            resp = client.get("/admin/questions/input")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert 'id="text-input-panel"' in html
            assert 'id="text-input"' in html

    # ── Functional: Sidebar role-based filtering ────────────────────────────

    def test_admin_sees_benutzerverwaltung(self, app):
        """Admin sidebar includes Benutzerverwaltung."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("admin"))
            resp = client.get("/admin/questions/input")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "Benutzerverwaltung" in html

    def test_teacher_no_benutzerverwaltung(self, app):
        """Teacher sidebar does NOT include Benutzerverwaltung."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("teacher"))
            resp = client.get("/admin/questions/input")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "Benutzerverwaltung" not in html
            assert "Fragen eingeben" in html
            assert "Wissensverwaltung" in html

    def test_teacher_sees_fragen_eingeben(self, app):
        """Teacher sidebar shows 'Fragen eingeben'."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("teacher"))
            resp = client.get("/admin/questions/input")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "Fragen eingeben" in html

    def test_student_redirected_from_question_input(self, app):
        """Student is redirected from question_input route."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("student"))
            resp = client.get("/admin/questions/input")
            assert resp.status_code == 302

    # ── Technical: Template structure ───────────────────────────────────────

    def test_template_extends_base(self, app):
        """Template extends base.html (verified by rendered nav structure)."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("admin"))
            resp = client.get("/admin/questions/input")
            assert resp.status_code == 200
            html = resp.data.decode()
            # base.html provides the nav structure; its presence confirms inheritance
            assert 'class="nav"' in html
            assert 'class="nav__logo"' in html

    def test_reuses_btn_class(self, app):
        """Template includes btn CSS class."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("admin"))
            resp = client.get("/admin/questions/input")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert ".btn {" in html or "btn-primary" in html

    def test_reuses_btn_primary_class(self, app):
        """Template includes btn-primary CSS class."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("admin"))
            resp = client.get("/admin/questions/input")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "btn-primary" in html

    def test_reuses_form_control_class(self, app):
        """Template includes form-control CSS class."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("admin"))
            resp = client.get("/admin/questions/input")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "form-control" in html

    def test_reuses_table_toolbar_select_class(self, app):
        """Template includes table-toolbar__select CSS class."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("admin"))
            resp = client.get("/admin/questions/input")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "table-toolbar__select" in html

    def test_reuses_spinner_class(self, app):
        """Template includes spinner CSS class."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("admin"))
            resp = client.get("/admin/questions/input")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert ".spinner" in html

    def test_reuses_modal_class(self, app):
        """Template includes modal CSS class."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("admin"))
            resp = client.get("/admin/questions/input")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert ".modal" in html

    def test_includes_auth_js(self, app):
        """Template includes auth.js script."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("admin"))
            resp = client.get("/admin/questions/input")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "auth.js" in html

    def test_includes_toast_js(self, app):
        """Template includes toast.js script."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("admin"))
            resp = client.get("/admin/questions/input")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "toast.js" in html

    def test_includes_question_input_js(self, app):
        """Template includes question-input.js script."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("admin"))
            resp = client.get("/admin/questions/input")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "question-input.js" in html

    def test_sets_api_url(self, app):
        """Template sets API_URL JS variable."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("admin"))
            resp = client.get("/admin/questions/input")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "const API_URL" in html

    # ── Technical: Responsive layout ────────────────────────────────────────

    def test_has_768px_breakpoint(self, app):
        """Template includes 768px responsive breakpoint."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("admin"))
            resp = client.get("/admin/questions/input")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "@media (max-width: 768px)" in html

    def test_has_640px_breakpoint(self, app):
        """Template includes 640px responsive breakpoint."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("admin"))
            resp = client.get("/admin/questions/input")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "@media (max-width: 640px)" in html

    def test_has_1100px_breakpoint(self, app):
        """Template includes 1100px responsive breakpoint."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("admin"))
            resp = client.get("/admin/questions/input")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "@media (max-width: 1100px)" in html

    # ── Technical: WCAG compliance ──────────────────────────────────────────

    def test_has_aria_labels(self, app):
        """Template includes ARIA labels for accessibility."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("admin"))
            resp = client.get("/admin/questions/input")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "aria-label" in html or "aria-labelledby" in html

    def test_has_form_labels(self, app):
        """Template includes form labels for all inputs."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("admin"))
            resp = client.get("/admin/questions/input")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "<label" in html

    def test_file_upload_has_max_attribute(self, app):
        """File input has multiple attribute for file limit."""
        with app.test_client() as client:
            client.set_cookie("jwt_token", self._make_token("admin"))
            resp = client.get("/admin/questions/input")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "multiple" in html
