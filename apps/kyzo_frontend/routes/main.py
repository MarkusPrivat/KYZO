"""Main routes blueprint — Landingpage placeholder."""

from datetime import datetime

from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Placeholder route for the landing page."""
    return render_template("index.html", now=datetime.utcnow())
