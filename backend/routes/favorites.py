from fastapi import APIRouter, Depends, HTTPException, Response

from backend.database import serialize, utcnow
from backend.models import FavoriteRequest
from backend.services.internship_service import InternshipService
from backend.utils.security import current_user, get_repository

router = APIRouter(prefix="/favorites", tags=["favorites"])


def save_favorite(identifier, user, repo):
    InternshipService(repo).get(identifier)
    key = f"{user['id']}:{identifier}"
    favorite = repo.get("favorites", key)
    if favorite is None:
        favorite = repo.upsert("favorites", key, {"user_id": user["id"], "internship_id": identifier,
                                                  "created_at": utcnow()})
    return serialize(favorite)


@router.get("")
def list_favorites(user=Depends(current_user), repo=Depends(get_repository)):
    favorites = []
    for item in repo.find("favorites", {"user_id": user["id"]}):
        # Deleted records stay explicit instead of becoming fictional internships.
        internship = repo.get("internships", item["internship_id"])
        favorites.append({**serialize(item), "internship": serialize(internship), "unavailable": internship is None})
    return {"favorites": favorites, "total": len(favorites)}


@router.post("", status_code=201)
def add_favorite(data: FavoriteRequest, user=Depends(current_user), repo=Depends(get_repository)):
    return save_favorite(data.internship_id, user, repo)


@router.post("/{internship_id}", status_code=201)
def add_favorite_by_id(internship_id: str, user=Depends(current_user), repo=Depends(get_repository)):
    return save_favorite(internship_id, user, repo)


@router.delete("/{internship_id}", status_code=204)
def remove_favorite(internship_id: str, user=Depends(current_user), repo=Depends(get_repository)):
    if not repo.delete("favorites", f"{user['id']}:{internship_id}"):
        raise HTTPException(404, "Favorite not found")
    return Response(status_code=204)
