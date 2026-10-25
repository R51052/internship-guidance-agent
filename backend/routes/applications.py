from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from backend.database import serialize, utcnow
from backend.models import ApplicationCreate, ApplicationUpdate
from backend.services.internship_service import InternshipService
from backend.services.safety_service import safety_check
from backend.utils.security import current_user, get_repository

router = APIRouter(prefix="/applications", tags=["applications"])


def _with_internship(repo, item):
    internship = repo.get("internships", item["internship_id"])
    return {**serialize(item), "internship": serialize(internship),
            "safety": safety_check(InternshipService(repo).get(item["internship_id"])) if internship else None}


@router.get("")
def list_applications(user=Depends(current_user), repo=Depends(get_repository)):
    items = [_with_internship(repo, item) for item in repo.find("applications", {"user_id": user["id"]})]
    items.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    return {"applications": items, "total": len(items)}


@router.post("", status_code=201)
def create_application(data: ApplicationCreate, user=Depends(current_user), repo=Depends(get_repository)):
    internship = InternshipService(repo).get(data.internship_id)
    key = f"{user['id']}:{data.internship_id}"
    existing = repo.get("applications", key)
    if existing:
        raise HTTPException(409, "This internship is already in your application tracker")
    item = repo.upsert("applications", key, {**data.model_dump(mode="json"), "user_id": user["id"],
                                             "created_at": utcnow(), "updated_at": utcnow(),
                                             "company": internship.company, "role": internship.title,
                                             "apply_url": str(internship.apply_url) if internship.apply_url else ""})
    return _with_internship(repo, item)


@router.patch("/{application_id}")
def update_application(application_id: str, data: ApplicationUpdate,
                       user=Depends(current_user), repo=Depends(get_repository)):
    item = repo.get("applications", application_id)
    if not item or item.get("user_id") != user["id"]:
        raise HTTPException(404, "Application not found")
    changes = {key: value for key, value in data.model_dump(mode="json").items() if value is not None}
    changes["updated_at"] = utcnow()
    item.update(changes)
    repo.upsert("applications", application_id, item)
    return _with_internship(repo, item)


@router.delete("/{application_id}", status_code=204)
def delete_application(application_id: str, user=Depends(current_user), repo=Depends(get_repository)):
    item = repo.get("applications", application_id)
    if not item or item.get("user_id") != user["id"]:
        raise HTTPException(404, "Application not found")
    repo.delete("applications", application_id)


@router.get("/safety/{internship_id}")
def check_internship_safety(internship_id: str, user=Depends(current_user), repo=Depends(get_repository)):
    return safety_check(InternshipService(repo).get(internship_id))
