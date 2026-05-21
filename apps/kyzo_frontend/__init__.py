"""Kyzo Frontend — Flask application package."""

from flask import Flask


def create_app(config_name="development"):
    """Application factory for Kyzo Frontend.

    Args:
        config_name: Configuration class name ('development', 'production', etc.)

    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)

    # Load configuration
    if config_name == "production":
        from .config import ProductionConfig
        app.config.from_object(ProductionConfig)
    else:
        from .config import DevelopmentConfig
        app.config.from_object(DevelopmentConfig)

    # Register blueprints
    from .routes.main import main_bp
    app.register_blueprint(main_bp)

    return app
