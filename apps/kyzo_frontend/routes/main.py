"""Main routes blueprint — Landingpage placeholder."""

from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Placeholder route for the landing page."""
    return "Hello World — Kyzo Frontend (Placeholder)"
