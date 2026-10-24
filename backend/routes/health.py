from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pymongo.errors import PyMongoError

router = APIRouter(tags=["health"])


@router.get("/health")
def health(request: Request):
    repository = request.app.state.repository
    try:
        ready = repository.ping()
    except PyMongoError:
        ready = False
    return JSONResponse(status_code=200 if ready else 503,
                        content={"status": "ok" if ready else "degraded", "database": repository.mode,
                                 "demo_mode": repository.mode == "demo",
                                 "llm_mode": request.app.state.settings.resolved_llm_mode})
