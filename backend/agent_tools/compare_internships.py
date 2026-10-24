from backend.models import CompareRequest
from backend.services.internship_service import InternshipService
from backend.services.matching import match_internship


def execute(repository, profile, arguments: CompareRequest):
    service = InternshipService(repository)
    matches = [match_internship(profile, service.get(identifier)) for identifier in arguments.internship_ids]
    eligible = [match for match in matches if match["eligible"]]
    best = sorted(eligible, key=lambda item: (-item["score"], item["internship"]["id"]))
    return {"comparisons": matches, "best_match_id": best[0]["internship"]["id"] if best else None,
            "note": "Best match is based on your profile and deterministic weights, not a placement guarantee."}
