"""Run from project root: uvicorn backend.main:app --reload."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo.errors import PyMongoError

from backend.config import Settings
from backend.database import create_repository
from backend.routes import agent, auth, favorites, health, profiles, recommendations


def create_app(settings: Settings | None = None, repository=None):
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(application):
        settings.prepare()
        repo = repository if repository is not None else create_repository(settings)
        application.state.repository = repo
        if settings.demo_mode and settings.seed_demo_data:
            from backend.scripts.seed_demo_data import seed_repository
            seed_repository(repo)
        try:
            yield
        finally:
            repo.close()

    app = FastAPI(title="Internship Guidance Agent API", version="1.0.0", lifespan=lifespan,
                  description="Authenticated internship matching with explicit offline demo and mock-AI modes.")
    app.state.settings = settings
    app.state.rate_limiter = agent.RateLimiter(settings.ai_rate_limit, settings.ai_rate_window_seconds)
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                       allow_origin_regex=settings.cors_origin_regex or None,
                       allow_credentials=False,
                       allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                       allow_headers=["Authorization", "Content-Type"])

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exception: RequestValidationError):
        # Pydantic error inputs may include passwords; only return safe metadata.
        return JSONResponse(status_code=422, content={"detail": [
            {"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]}
            for error in exception.errors()]})

    @app.exception_handler(PyMongoError)
    async def database_error(request: Request, exception: PyMongoError):
        return JSONResponse(status_code=503, content={"detail": "Database temporarily unavailable"})

    for route in (health.router, auth.router, profiles.router, recommendations.router, agent.router, favorites.router):
        app.include_router(route, prefix="/api")
    app.include_router(health.router, include_in_schema=False)
    return app


app = create_app()
