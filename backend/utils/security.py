from datetime import timedelta
from uuid import uuid4

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash

from backend.database import utcnow

password_hasher = PasswordHash.recommended()
bearer = HTTPBearer(auto_error=False)
# A dummy hash prevents a fast missing-account path during login.
dummy_hash = password_hasher.hash("dummy-not-a-real-user-password")


def hash_password(password):
    return password_hasher.hash(password)


def verify_password(password, encoded):
    try:
        return password_hasher.verify(password, encoded)
    except (ValueError, TypeError):
        return False


def public_user(user):
    return {key: user[key] for key in ("id", "name", "email", "created_at")}


def issue_token(user, repository, settings):
    now = utcnow()
    expiry = now + timedelta(minutes=settings.jwt_expiry_minutes)
    identifier = str(uuid4())
    token = jwt.encode({"sub": user["id"], "jti": identifier, "iat": now,
                        "exp": expiry, "iss": "internship-guidance"}, settings.jwt_secret, algorithm="HS256")
    repository.insert("sessions", {"id": identifier, "user_id": user["id"], "expires_at": expiry})
    return {"access_token": token, "token_type": "bearer", "expires_in": settings.jwt_expiry_minutes * 60,
            "user": public_user(user)}


def get_repository(request: Request):
    return request.app.state.repository


def get_auth(request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    unauthorized = HTTPException(401, "Invalid or expired authentication token", headers={"WWW-Authenticate": "Bearer"})
    if credentials is None:
        raise unauthorized
    try:
        payload = jwt.decode(credentials.credentials, request.app.state.settings.jwt_secret,
                             algorithms=["HS256"], issuer="internship-guidance",
                             options={"require": ["sub", "jti", "exp", "iat"]})
    except jwt.InvalidTokenError:
        raise unauthorized from None
    repo = request.app.state.repository
    session = repo.get("sessions", payload["jti"])
    if not session or session["user_id"] != payload["sub"]:
        raise unauthorized
    user = repo.get("users", payload["sub"])
    if user is None:
        raise unauthorized
    return {"user": user, "session_id": payload["jti"]}


def current_user(auth=Depends(get_auth)):
    return auth["user"]
