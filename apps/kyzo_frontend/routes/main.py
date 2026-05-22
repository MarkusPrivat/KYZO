"""Main routes blueprint — Landingpage placeholder."""

from datetime import datetime, timezone

import jwt
from flask import Blueprint, render_template, current_app, request, redirect

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Placeholder route for the landing page."""
    return render_template("index.html", now=datetime.utcnow())


@main_bp.route("/register")
def register():
    """Render the registration page.

    Server-side guard: if the user is already authenticated (valid JWT in cookie),
    redirect to the home page instead of showing the registration form.
    """
    api_url = current_app.config.get("API_URL", "/api/v1")
    auth_secret = current_app.config.get("AUTH_SECRET_KEY", "")

    token = request.cookies.get("jwt_token")
    if token:
        try:
            if auth_secret:
                jwt.decode(
                    token,
                    auth_secret,
                    algorithms=["HS256"],
                    options={"require": ["exp"]},
                )
            else:
                # Fallback: decode without verification (just check exp claim)
                jwt.decode(
                    token,
                    options={"verify_signature": False, "require": ["exp"]},
                    algorithms=["HS256"],
                )
            # Token is valid — user is already authenticated
            return redirect("/")
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            # Invalid or expired token — fall through to render the page
            pass

    return render_template("register.html", api_url=api_url)


@main_bp.route("/login")
def login():
    """Render the login page."""
    api_url = current_app.config.get("API_URL", "/api/v1")
    return render_template("login.html", api_url=api_url)


@main_bp.route("/profile")
def profile():
    """Render the profile page."""
    api_url = current_app.config.get("API_URL", "/api/v1")
    return render_template("profile.html", api_url=api_url)
