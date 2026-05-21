"""Main routes blueprint — Landingpage placeholder."""

from datetime import datetime

from flask import Blueprint, render_template, current_app

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Placeholder route for the landing page."""
    return render_template("index.html", now=datetime.utcnow())


@main_bp.route("/register")
def register():
    """Render the registration page."""
    api_url = current_app.config.get("API_URL", "/api/v1")
    return render_template("register.html", api_url=api_url)


@main_bp.route("/login")
def login():
    """Render the login page."""
    api_url = current_app.config.get("API_URL", "/api/v1")
    return render_template("login.html", api_url=api_url)
