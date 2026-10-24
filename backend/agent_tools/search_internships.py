from typing import Literal

from pydantic import Field

from backend.models import StrictModel
from backend.services.internship_service import InternshipService


class SearchArguments(StrictModel):
    query: str = Field(default="", max_length=200)
    location: str = Field(default="", max_length=100)
    domain: str = Field(default="", max_length=100)
    work_mode: Literal["remote", "hybrid", "onsite"] | None = None
    min_stipend: int = Field(default=0, ge=0, le=1000000)
    limit: int = Field(default=10, ge=1, le=50)


def execute(repository, profile, arguments: SearchArguments):
    filters = arguments.model_dump(exclude={"limit"})
    items = InternshipService(repository).search(**filters)
    return {"total": len(items), "internships": [item.model_dump(mode="json") for item in items[:arguments.limit]]}
