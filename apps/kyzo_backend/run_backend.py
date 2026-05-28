from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from apps.kyzo_backend.config import fastapi_settings, slowapi_limiter
from apps.kyzo_backend.core import create_database
from apps.kyzo_backend.api import (knowledge_router,
                                   question_router,
                                   test_router,
                                   user_router
                                   )


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
    - API Metadata: Sets the title, version, and description for OpenAPI docs.
    - Lifecycle Management: Hooks into the 'lifespan' context manager.
    - CORS Security: Mounts CORSMiddleware to allow secure cross-origin
      communication with the frontend.
    - Rate Limiting: Configures SlowAPI by binding the global limiter instance
      to the application state and registering the 'RateLimitExceeded' exception handler.
    - Routing Architecture: Aggregates specialized routers (e.g. Knowledge,
      Questions, Tests, Users) into a single unified API surface.

    Returns:
        FastAPI: A fully configured FastAPI instance, armed with global security guards
            and ready to be served by an ASGI server like Uvicorn.

    Note:
        The integrated routers provide the foundational CRUD, RBAC protection,
        and AI-driven business logic endpoints for the Kyzo adaptive learning platform.
    """
    backend_app = FastAPI(
        title="Kyzo Backend",
        description="AI-powered adaptive learning platform API",
        version="1.0.0",
        lifespan=lifespan
    )

    backend_app.add_middleware(
        CORSMiddleware,
        allow_origins=fastapi_settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    backend_app.state.limiter = slowapi_limiter
    backend_app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    backend_app.include_router(knowledge_router, prefix=fastapi_settings.API_PREFIX_V1)
    backend_app.include_router(question_router, prefix=fastapi_settings.API_PREFIX_V1)
    backend_app.include_router(test_router, prefix=fastapi_settings.API_PREFIX_V1)
    backend_app.include_router(user_router, prefix=fastapi_settings.API_PREFIX_V1)

    return backend_app




if __name__ == "__main__":
    uvicorn.run(
        "apps.kyzo_backend.run_backend:create_app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        factory=True
    )
else:
    app = create_app()
