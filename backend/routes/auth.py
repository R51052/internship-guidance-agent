from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from backend.database import ConflictError, serialize, utcnow
from backend.models import LoginRequest, Profile, RegisterRequest
from backend.utils.security import current_user, dummy_hash, get_auth, get_repository, hash_password, issue_token, public_user, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201)
def register(data: RegisterRequest, request: Request, repo=Depends(get_repository)):
    user = {"id": str(uuid4()), "name": data.name, "email": str(data.email).casefold(),
            "password_hash": hash_password(data.password), "created_at": utcnow()}
    try:
        repo.insert("users", user)
    except ConflictError:
        raise HTTPException(409, "An account with this email already exists") from None
    repo.upsert("profiles", user["id"], Profile(full_name=user["name"]).model_dump(mode="json"))
    return serialize(issue_token(user, repo, request.app.state.settings))


@router.post("/login")
def login(data: LoginRequest, request: Request, repo=Depends(get_repository)):
    user = repo.one("users", {"email": str(data.email).casefold()})
    valid = verify_password(data.password, user["password_hash"] if user else dummy_hash)
    if not user or not valid:
        raise HTTPException(401, "Incorrect email or password", headers={"WWW-Authenticate": "Bearer"})
    return serialize(issue_token(user, repo, request.app.state.settings))


@router.post("/logout", status_code=204)
def logout(auth=Depends(get_auth), repo=Depends(get_repository)):
    repo.delete("sessions", auth["session_id"])
    return Response(status_code=204)


@router.get("/me")
def me(user=Depends(current_user)):
    return serialize(public_user(user))
