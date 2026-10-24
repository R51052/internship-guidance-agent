"""Environment configuration; persistent deployments never silently use demo data."""
import os
import secrets
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field


class Settings(BaseModel):
    demo_mode: bool = False
    seed_demo_data: bool = True
    mongodb_uri: str = ""
    mongodb_database: str = "internship_guidance"
    jwt_secret: str = ""
    jwt_expiry_minutes: int = Field(default=60, ge=1, le=1440)
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173", "http://localhost:3000", "http://localhost:5500"])
    cors_origin_regex: str = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
    ai_rate_limit: int = Field(default=20, ge=1, le=10000)
    ai_rate_window_seconds: int = Field(default=60, ge=1, le=3600)
    llm_mode: Literal["auto", "mock", "openai", "gemini", "groq"] = "auto"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    groq_base_url: str = "https://api.groq.com/openai/v1"

    @classmethod
    def from_env(cls):
        load_dotenv(Path(__file__).with_name(".env"), override=False)
        fields = {name: os.environ[name.upper()] for name in cls.model_fields if name.upper() in os.environ}
        if "cors_origins" in fields:
            fields["cors_origins"] = [value.strip() for value in fields["cors_origins"].split(",") if value.strip()]
        return cls(**fields)

    def prepare(self):
        if not self.demo_mode and not self.mongodb_uri:
            raise RuntimeError("Set MONGODB_URI, or explicitly enable DEMO_MODE=true for an offline demo.")
        if not self.jwt_secret and self.demo_mode:
            self.jwt_secret = secrets.token_urlsafe(48)
        if len(self.jwt_secret) < 32:
            raise RuntimeError("JWT_SECRET must contain at least 32 characters.")
        if "*" in self.cors_origins:
            raise RuntimeError("Configure explicit CORS origins; wildcard origins are not supported.")
        if self.llm_mode == "openai" and not self.openai_api_key:
            raise RuntimeError("LLM_MODE=openai requires OPENAI_API_KEY.")
        if self.llm_mode == "gemini" and not self.gemini_api_key:
            raise RuntimeError("LLM_MODE=gemini requires GEMINI_API_KEY.")
        if self.llm_mode == "groq" and not self.groq_api_key:
            raise RuntimeError("LLM_MODE=groq requires GROQ_API_KEY.")

    @property
    def resolved_llm_mode(self):
        if self.llm_mode == "mock":
            return "mock"
        if self.llm_mode == "openai":
            return "openai" if self.openai_api_key else "mock"
        if self.llm_mode == "gemini":
            return "gemini" if self.gemini_api_key else "mock"
        if self.llm_mode == "groq":
            return "groq" if self.groq_api_key else "mock"
        if self.openai_api_key:
            return "openai"
        if self.gemini_api_key:
            return "gemini"
        if self.groq_api_key:
            return "groq"
        return "mock"
