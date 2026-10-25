from typing import Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from backend.routes.profiles import load_profile
from backend.services.internship_service import InternshipService
from backend.services.matching import WEIGHTS, match_internship, rank_internships
from backend.services.freshness_service import freshness
from backend.utils.security import current_user, get_repository

router = APIRouter(tags=["internships", "recommendations"])


class RecommendationRequest(BaseModel):
    limit: int = Field(default=5, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    include_ineligible: bool = False


@router.get("/public/internships", tags=["public"])
def public_internships(q: str = Query(default="", max_length=200),
                       location: str = Query(default="", max_length=100),
                       domain: str = Query(default="", max_length=100),
                       work_mode: Literal["remote", "hybrid", "onsite"] | None = None,
                       limit: int = Query(default=20, ge=1, le=100),
                       offset: int = Query(default=0, ge=0),
                       repo=Depends(get_repository)):
    """Public read-only catalog for React discovery; recommendations remain private."""
    items = InternshipService(repo).search(query=q, location=location, domain=domain, work_mode=work_mode)
    result = [{**item.model_dump(mode="json"), "freshness": freshness(item)} for item in items[offset:offset + limit]]
    return {"internships": result, "total": len(items), "limit": limit, "offset": offset,
            "is_demo": repo.mode == "demo"}


@router.get("/internships")
def internships(q: str = Query(default="", max_length=200),
                location: str = Query(default="", max_length=100),
                domain: str = Query(default="", max_length=100),
                work_mode: Literal["remote", "hybrid", "onsite"] | None = None,
                min_stipend: int = Query(default=0, ge=0, le=1000000),
                include_expired: bool = False,
                limit: int = Query(default=20, ge=1, le=100),
                offset: int = Query(default=0, ge=0),
                user=Depends(current_user), repo=Depends(get_repository)):
    items = InternshipService(repo).search(query=q, location=location, domain=domain, work_mode=work_mode,
                                         min_stipend=min_stipend, include_expired=include_expired)
    result = [{**item.model_dump(mode="json"), "freshness": freshness(item)} for item in items[offset:offset + limit]]
    return {"internships": result, "total": len(items), "limit": limit, "offset": offset,
            "is_demo": repo.mode == "demo"}


@router.get("/internships/{internship_id}")
def internship_details(internship_id: str, user=Depends(current_user), repo=Depends(get_repository)):
    item = InternshipService(repo).get(internship_id)
    return {**item.model_dump(mode="json"), "match": match_internship(load_profile(repo, user), item)}


@router.get("/recommendations")
def recommendations(limit: int = Query(default=10, ge=1, le=100),
                    offset: int = Query(default=0, ge=0),
                    include_ineligible: bool = False,
                    user=Depends(current_user), repo=Depends(get_repository)):
    items = InternshipService(repo).search(include_expired=include_ineligible)
    ranked = rank_internships(load_profile(repo, user), items, include_ineligible=include_ineligible)
    return {"recommendations": ranked[offset:offset + limit], "total": len(ranked), "weights": WEIGHTS,
            "limit": limit, "offset": offset, "is_demo": repo.mode == "demo"}


@router.post("/recommendations")
def recommendations_post(data: RecommendationRequest,
                         user=Depends(current_user), repo=Depends(get_repository)):
    items = InternshipService(repo).search(include_expired=data.include_ineligible)
    ranked = rank_internships(load_profile(repo, user), items, include_ineligible=data.include_ineligible)
    return {"recommendations": ranked[data.offset:data.offset + data.limit], "total": len(ranked), "weights": WEIGHTS,
            "limit": data.limit, "offset": data.offset, "is_demo": repo.mode == "demo"}
