"""Configuration classes for Kyzo Frontend."""

import os


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    HOST = "127.0.0.1"
    PORT = 5000


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False

    def __init__(self):
        secret = os.environ.get("SECRET_KEY")
        if not secret:
            raise ValueError("SECRET_KEY environment variable is required for production")
        self.SECRET_KEY = secret
