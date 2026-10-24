from fastapi import APIRouter, Depends

from backend.models import Profile
from backend.utils.security import current_user, get_repository

router = APIRouter(tags=["profiles"])


def load_profile(repo, user):
    document = repo.get("profiles", user["id"])
    if document:
        document.pop("id", None)
        return Profile.model_validate(document)
    return Profile(full_name=user["name"])


@router.get("/profile")
@router.get("/profiles/me", include_in_schema=False)
def get_profile(user=Depends(current_user), repo=Depends(get_repository)):
    return load_profile(repo, user).model_dump(mode="json")


@router.put("/profile")
@router.post("/profile")
@router.put("/profiles/me", include_in_schema=False)
@router.post("/profiles/me", include_in_schema=False)
def update_profile(data: Profile, user=Depends(current_user), repo=Depends(get_repository)):
    repo.upsert("profiles", user["id"], data.model_dump(mode="json"))
    return data.model_dump(mode="json")
