from backend.agent_tools.internship_details import DetailsArguments
from backend.services.internship_service import InternshipService
from backend.services.skill_gap_service import analyze_skill_gap


def execute(repository, profile, arguments: DetailsArguments):
    return analyze_skill_gap(profile, InternshipService(repository).get(arguments.internship_id))
