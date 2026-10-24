"""Deterministic, explainable matching. Eligibility is a gate, not a score.

The public weights mirror the project specification exactly. When a student has
not supplied a soft preference, that criterion is excluded and the remaining
weights are re-normalized. This avoids both silently penalizing and silently
rewarding incomplete profiles.
"""
import re
from datetime import date

from backend.models import Internship, Profile

WEIGHTS = {"skills": 35, "education": 25, "sector": 20, "location": 15, "mode": 5}


def normalize(value):
    return " ".join(value.casefold().split())


def eligibility_reasons(profile: Profile, internship: Internship, today: date | None = None):
    today = today or date.today()
    reasons = []
    if internship.application_deadline and internship.application_deadline < today:
        reasons.append("Application deadline has passed")
    if internship.start_date and internship.start_date < today:
        reasons.append("Internship has already started")
    if profile.available_from and internship.start_date and profile.available_from > internship.start_date:
        reasons.append("Internship starts before your availability")
    requirements = internship.eligibility
    if requirements.min_cgpa is not None and (profile.cgpa is None or profile.cgpa < requirements.min_cgpa):
        reasons.append(f"Requires a CGPA of at least {requirements.min_cgpa:g}; update your profile if unknown")
    if requirements.degrees and normalize(profile.degree) not in {normalize(item) for item in requirements.degrees}:
        reasons.append("Degree requirement is not met or degree is missing")
    if requirements.years and profile.year not in requirements.years:
        reasons.append("Study year requirement is not met or year is missing")
    return reasons


def match_internship(profile: Profile, internship: Internship, today: date | None = None):
    owned = {normalize(skill) for skill in profile.skills}
    required = {normalize(skill) for skill in internship.skills_required}
    matched = [skill for skill in internship.skills_required if normalize(skill) in owned]
    missing = [skill for skill in internship.skills_required if normalize(skill) not in owned]
    interests = {normalize(item) for item in profile.interests}
    targets = {normalize(internship.domain), normalize(internship.title)}
    sector_fit = float(any(re.search(r"(?<!\w)" + re.escape(item) + r"(?!\w)", target)
                           for item in interests for target in targets))
    has_education_preference = bool(profile.degree or profile.education)
    education_fit = 1.0
    if internship.eligibility.degrees:
        education_fit = float(bool(profile.degree) and normalize(profile.degree) in {
            normalize(item) for item in internship.eligibility.degrees
        })
    elif not has_education_preference:
        education_fit = None
    location_fit = None
    if profile.preferred_locations:
        location_fit = float(normalize(internship.location) in {
            normalize(item) for item in profile.preferred_locations
        })
    mode_fit = None if profile.preferred_work_mode == "any" else float(
        profile.preferred_work_mode == internship.work_mode
    )
    active = {
        "skills": len(owned & required) / len(required) if required else 1.0,
        "education": education_fit,
        "sector": sector_fit if profile.interests else None,
        "location": location_fit,
        "mode": mode_fit,
    }
    active_weight = sum(WEIGHTS[key] for key, value in active.items() if value is not None)
    breakdown = {
        key: round(value * WEIGHTS[key] * 100 / active_weight, 2)
        for key, value in active.items() if value is not None
    }
    reasons = eligibility_reasons(profile, internship, today)
    score = round(sum(breakdown.values()), 2)
    return {
        "internship": internship.model_dump(mode="json"),
        "score": score,
        "match_score": score,
        "score_breakdown": breakdown,
        "eligible": not reasons,
        "ineligibility_reasons": reasons,
        "matched_skills": matched,
        "missing_skills": missing,
        "explanation": [f"{len(matched)} of {len(required)} required skills match your profile",
                         "Your preferred sector aligns with this role" if sector_fit else "No listed sector preference matches the role",
                         "Location matches" if location_fit == 1 else "Location preference is not a match" if location_fit == 0 else "Location preference not specified",
                         "Work mode matches" if mode_fit == 1 else "Work mode preference is not a match" if mode_fit == 0 else "Work mode preference not specified"] + reasons,
    }


def rank_internships(profile, internships, *, today=None, include_ineligible=False):
    matches = [match_internship(profile, item, today) for item in internships]
    return sorted((item for item in matches if include_ineligible or item["eligible"]),
                  key=lambda item: (-item["score"], item["internship"]["id"]))
