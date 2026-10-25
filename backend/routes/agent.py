from collections import deque
from threading import Lock
from time import monotonic

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.agent_tools import execute_tool
from backend.models import ChatRequest, CoachRequest, CompareRequest, SkillGapRequest
from backend.routes.profiles import load_profile
from backend.services.agent_service import AgentService
from backend.services.coach_service import CoachService
from backend.utils.security import current_user, get_repository

router = APIRouter(prefix="/agent", tags=["agent"])


class RateLimiter:
    """Per-user sliding window shared by all AI routes in this process."""
    def __init__(self, limit, window):
        self.limit = limit
        self.window = window
        self.buckets = {}
        self.lock = Lock()

    def check(self, identifier):
        now = monotonic()
        with self.lock:
            for key in list(self.buckets):
                if not self.buckets[key] or self.buckets[key][-1] <= now - self.window:
                    del self.buckets[key]
            bucket = self.buckets.setdefault(identifier, deque())
            while bucket and bucket[0] <= now - self.window:
                bucket.popleft()
            if len(bucket) >= self.limit:
                retry = max(1, int(self.window - (now - bucket[0])) + 1)
                raise HTTPException(429, "AI request limit reached; try again shortly", headers={"Retry-After": str(retry)})
            bucket.append(now)


def rate_limited_user(request: Request, user=Depends(current_user)):
    request.app.state.rate_limiter.check(user["id"])
    return user


@router.post("/chat")
def chat(data: ChatRequest, request: Request, user=Depends(rate_limited_user), repo=Depends(get_repository)):
    return AgentService(repo, request.app.state.settings).chat(load_profile(repo, user), data)


@router.post("/coach")
def coach(data: CoachRequest, request: Request, user=Depends(rate_limited_user), repo=Depends(get_repository)):
    return CoachService(repo, request.app.state.settings).coach(load_profile(repo, user), data)


@router.post("/skill-gap")
def skill_gap(data: SkillGapRequest, user=Depends(rate_limited_user), repo=Depends(get_repository)):
    return execute_tool("skill_analysis", data.model_dump(), repo, load_profile(repo, user))


@router.post("/compare")
def compare(data: CompareRequest, user=Depends(rate_limited_user), repo=Depends(get_repository)):
    return execute_tool("compare_internships", data.model_dump(), repo, load_profile(repo, user))
