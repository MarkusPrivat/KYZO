from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from apps.kyzo_backend.core import create_database
from apps.kyzo_backend.api import knowledge_router, question_router, user_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Asynchronous context manager for the FastAPI application lifecycle.

    This function coordinates the 'Startup' and 'Shutdown' phases of the
    Kyzo Backend. It ensures that critical infrastructure, such as the
    database schema, is fully initialized and verified before the
    application begins to accept incoming network traffic.

    Args:
        _app (FastAPI): The instance of the FastAPI application.

    Yields:
        None: Control is yielded back to the FastAPI framework to start
              the main request-processing loop.

    Lifecycle Flow:
    ---------------
    1. **Startup**: Calls `create_database()` to ensure all SQLAlchemy
       models are reflected as physical tables.
    2. **Execution**: The application remains in the 'yield' state while
       running.
    3. **Shutdown**: (Optional) Place logic here for closing database
       pools or clearing caches.
    """
    create_database()

    yield

    # Shutdown-Logic: (Placeholder for future cleanup)


def create_app() -> FastAPI:
    """
    Factory function to initialize and configure the FastAPI application.

    This 'Application Factory' pattern allows for flexible app creation,
    making it easier to maintain separate configurations for production,
    development, and testing environments.

    It centralizes the integration of:
    - **API Metadata**: Sets the title, version, and description for OpenAPI docs.
    - **Lifecycle Management**: Hooks into the 'lifespan' context manager.
    - **Routing Architecture**: Aggregates specialized routers (e.g. Knowledge,
      Questions, Users, ...) into a single API surface.

    Returns:
        FastAPI: A fully configured FastAPI instance ready to be served by Uvicorn.

    Note:
        The integrated routers provide the foundational CRUD and AI-logic
        endpoints for the Kyzo adaptive learning platform.
    """
    backend_app = FastAPI(
        title="Kyzo Backend",
        description="AI-powered adaptive learning platform API",
        version="1.0.0",
        lifespan=lifespan
    )

    backend_app.include_router(knowledge_router)
    backend_app.include_router(question_router)
    backend_app.include_router(user_router)

    return backend_app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("run_backend:app", host="127.0.0.1", port=8000, reload=True)
