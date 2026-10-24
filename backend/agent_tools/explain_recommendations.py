from pydantic import Field

from backend.models import StrictModel
from backend.services.internship_service import InternshipService
from backend.services.matching import WEIGHTS, rank_internships


class ExplainArguments(StrictModel):
    limit: int = Field(default=5, ge=1, le=20)


def execute(repository, profile, arguments: ExplainArguments):
    ranked = rank_internships(profile, InternshipService(repository).search())
    return {"recommendations": ranked[:arguments.limit], "total": len(ranked), "weights": WEIGHTS}
