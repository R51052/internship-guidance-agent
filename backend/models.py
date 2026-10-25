"""Validated request and stored domain schemas."""
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, StringConstraints, field_validator, model_validator

InternshipID = Annotated[str, StringConstraints(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")]
Password = Annotated[str, StringConstraints(strip_whitespace=False, max_length=128)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class RegisterRequest(StrictModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: Password = Field(min_length=8)

    @field_validator("password", mode="before")
    @classmethod
    def password_not_trimmed(cls, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Password must not be blank")
        return value


class LoginRequest(StrictModel):
    email: EmailStr
    password: Password = Field(min_length=1)


class Profile(StrictModel):
    full_name: str = Field(default="", max_length=100)
    education: str = Field(default="", max_length=150)
    degree: str = Field(default="", max_length=100)
    year: int | None = Field(default=None, ge=1, le=6)
    cgpa: float | None = Field(default=None, ge=0, le=10)
    skills: list[str] = Field(default_factory=list, max_length=50)
    interests: list[str] = Field(default_factory=list, max_length=30)
    preferred_locations: list[str] = Field(default_factory=list, max_length=20)
    preferred_work_mode: Literal["any", "remote", "hybrid", "onsite"] = "any"
    min_stipend: int = Field(default=0, ge=0, le=1000000)
    max_duration_months: int | None = Field(default=None, ge=1, le=24)
    available_from: date | None = None
    bio: str = Field(default="", max_length=2000)

    @field_validator("skills", "interests", "preferred_locations")
    @classmethod
    def normalized_list(cls, values):
        result = []
        for value in values:
            value = value.strip()
            if not value or len(value) > 100:
                raise ValueError("List entries must contain 1–100 characters")
            if value.casefold() not in {entry.casefold() for entry in result}:
                result.append(value)
        return result


class Eligibility(StrictModel):
    min_cgpa: float | None = Field(default=None, ge=0, le=10)
    degrees: list[str] = Field(default_factory=list, max_length=20)
    years: list[int] = Field(default_factory=list, max_length=6)

    @field_validator("years")
    @classmethod
    def valid_years(cls, years):
        if any(year < 1 or year > 6 for year in years):
            raise ValueError("Eligible years must be between 1 and 6")
        return years


class Internship(StrictModel):
    id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    title: str = Field(min_length=2, max_length=200)
    company: str = Field(min_length=2, max_length=150)
    description: str = Field(min_length=10, max_length=10000)
    domain: str = Field(min_length=2, max_length=100)
    skills_required: list[str] = Field(min_length=1, max_length=50)
    location: str = Field(min_length=2, max_length=100)
    work_mode: Literal["remote", "hybrid", "onsite"] | None = None
    stipend: int | None = Field(default=None, ge=0, le=1000000)
    currency: str | None = "INR"
    stipend_period: Literal["month", "total"] | None = "month"
    duration_months: int | None = Field(default=None, ge=1, le=24)
    application_deadline: date | None = None
    start_date: date | None = None
    eligibility: Eligibility = Field(default_factory=Eligibility)
    apply_url: HttpUrl | None = None
    source: str = "curated"
    source_job_id: str | None = None
    published_at: datetime | None = None
    last_synced_at: datetime | None = None
    is_active_inferred: bool = True
    is_demo: bool = False

    @field_validator("skills_required")
    @classmethod
    def normalized_skills(cls, values):
        return Profile.normalized_list(values)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date and self.application_deadline and self.start_date < self.application_deadline:
            raise ValueError("Start date cannot precede the application deadline")
        return self


class ChatRequest(StrictModel):
    message: str = Field(min_length=1, max_length=4000)
    internship_ids: list[InternshipID] = Field(default_factory=list, max_length=5)

    @field_validator("internship_ids")
    @classmethod
    def unique_ids(cls, values):
        if len(set(values)) != len(values):
            raise ValueError("Select different internships")
        return values


class CoachRequest(StrictModel):
    mode: Literal["interview", "resume"]
    content: str = Field(min_length=1, max_length=10000)
    internship_id: InternshipID | None = None
    question_index: int = Field(default=0, ge=0, le=10)


class ResumeGenerateRequest(StrictModel):
    content: str = Field(default="", max_length=20000)
    format: Literal["pdf", "docx"] = "pdf"
    filename: str = Field(default="internpath-resume", min_length=1, max_length=80)


class CompareRequest(StrictModel):
    internship_ids: list[InternshipID] = Field(min_length=2, max_length=5)

    @field_validator("internship_ids")
    @classmethod
    def unique_ids(cls, values):
        if len(set(values)) != len(values):
            raise ValueError("Select different internships to compare")
        return values


class SkillGapRequest(StrictModel):
    internship_id: InternshipID


class FavoriteRequest(SkillGapRequest):
    pass
