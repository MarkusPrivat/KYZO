"""
database.py - Database session management and initialization for the Kyzo FastAPI application.

This module provides the core database connectivity and session management for the Kyzo
adaptive learning platform. It establishes a connection to the SQLite database using
SQLAlchemy and implements a session factory pattern with proper resource cleanup.

Key Features:
-------------
- **Database Engine Configuration**: Creates a SQLAlchemy engine with thread-safe
  connection settings (required for SQLite in multi-threaded environments like FastAPI).
- **Session Management**: Provides a session factory with disabled auto-commit and auto-flush
  for better transaction control.
- **Database Initialization**: Creates all database tables based on the SQLAlchemy models
  defined in the application.
- **Dependency Injection**: Implements a generator-based dependency for FastAPI that
  automatically handles session lifecycle (creation and cleanup).

Components:
-----------
- Engine: SQLAlchemy engine instance configured with the database URI from settings.
- SESSION_LOCAL: Thread-local session factory for creating database sessions.
- create_database(): Initializes the database schema by creating all tables.
- get_db(): FastAPI dependency that yields a database session for the request lifecycle.
"""
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from apps.kyzo_backend.config.config import fastapi_settings
from apps.kyzo_backend.data.models import Base


engine = create_engine(
    fastapi_settings.SQLALCHEMY_DATABASE_URI,
    connect_args={"check_same_thread": False}
)

SESSION_LOCAL = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_database() -> None:
    """
    Creates all database tables defined in the SQLAlchemy models.

    This function uses the metadata from the Base class to generate
    the schema. It is safe to call multiple times as it only creates
    tables that do not already exist in the database.
    """
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function that yields a database session and
    ensures it's closed after the request is finished.
    """
    database = SESSION_LOCAL()
    try:
        yield database
    finally:
        database.close()
