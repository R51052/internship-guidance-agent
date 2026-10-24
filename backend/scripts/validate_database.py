"""Validate stored internship schemas and report orphaned profile/favorite records."""
import json

from pydantic import ValidationError

from backend.config import Settings
from backend.database import create_repository
from backend.models import Internship, Profile
from backend.scripts.seed_demo_data import seed_repository


def validate_repository(repository):
    errors = []
    counts = {}
    for collection in ("users", "profiles", "internships", "favorites", "sessions"):
        counts[collection] = len(repository.find(collection))
    for item in repository.find("internships"):
        try:
            Internship.model_validate(item)
        except ValidationError:
            errors.append({"collection": "internships", "id": str(item.get("id")), "error": "Invalid internship schema"})
    for item in repository.find("profiles"):
        try:
            Profile.model_validate({key: value for key, value in item.items() if key != "id"})
        except ValidationError:
            errors.append({"collection": "profiles", "id": str(item.get("id")), "error": "Invalid profile schema"})
        if not repository.get("users", item.get("id")):
            errors.append({"collection": "profiles", "id": str(item.get("id")), "error": "Orphaned profile"})
    for item in repository.find("favorites"):
        if not repository.get("users", item.get("user_id")) or not repository.get("internships", item.get("internship_id")):
            errors.append({"collection": "favorites", "id": str(item.get("id")), "error": "Orphaned favorite"})
    return {"valid": not errors, "mode": repository.mode, "counts": counts, "errors": errors}


def main():
    settings = Settings.from_env()
    settings.prepare()
    repo = create_repository(settings)
    try:
        if settings.demo_mode and settings.seed_demo_data:
            seed_repository(repo)
        result = validate_repository(repo)
        print(json.dumps(result, indent=2))
        return 0 if result["valid"] else 1
    finally:
        repo.close()


if __name__ == "__main__":
    raise SystemExit(main())
