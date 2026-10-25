from fastapi import APIRouter, Depends, HTTPException

from backend.database import serialize, utcnow
from backend.models import GithubEvaluateRequest, ProgressUpdate
from backend.services.github_service import evaluate_repository
from backend.utils.security import current_user, get_repository

router = APIRouter(prefix="/student", tags=["student"])

@router.get("/interview-history")
def interview_history(user=Depends(current_user), repo=Depends(get_repository)):
    items = repo.find("interview_history", {"user_id": user["id"]})
    items.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    scores = [item["score"] for item in items if item.get("score") is not None]
    return {"history": serialize(items), "total": len(items), "average_score": round(sum(scores) / len(scores), 1) if scores else None}

@router.delete("/interview-history", status_code=204)
def clear_interview_history(user=Depends(current_user), repo=Depends(get_repository)):
    for item in repo.find("interview_history", {"user_id": user["id"]}):
        repo.delete("interview_history", item["id"])

@router.get("/progress")
def get_progress(user=Depends(current_user), repo=Depends(get_repository)):
    items = repo.find("progress", {"user_id": user["id"]})
    counts = {status: sum(1 for item in items if item.get("status") == status) for status in ("planned", "learning", "practiced", "completed")}
    return {"items": serialize(items), "counts": counts, "completed": counts["completed"], "total": len(items)}

@router.put("/progress")
def update_progress(data: ProgressUpdate, user=Depends(current_user), repo=Depends(get_repository)):
    key = f"{user['id']}:{data.skill.casefold()}"
    value = repo.upsert("progress", key, {**data.model_dump(mode="json"), "user_id": user["id"], "updated_at": utcnow()})
    return serialize(value)

@router.post("/github-evaluate")
def github_evaluate(data: GithubEvaluateRequest, user=Depends(current_user)):
    try:
        return evaluate_repository(data.url)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
