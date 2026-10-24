from pydantic import Field

from backend.models import StrictModel
from backend.services.internship_service import InternshipService


class DetailsArguments(StrictModel):
    internship_id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")


def execute(repository, profile, arguments: DetailsArguments):
    return InternshipService(repository).get(arguments.internship_id).model_dump(mode="json")
