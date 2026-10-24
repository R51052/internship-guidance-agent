from backend.services.matching import normalize


def analyze_skill_gap(profile, internship):
    owned = {normalize(item) for item in profile.skills}
    matched = [skill for skill in internship.skills_required if normalize(skill) in owned]
    missing = [skill for skill in internship.skills_required if normalize(skill) not in owned]
    return {
        "internship_id": internship.id,
        "matched_skills": matched,
        "missing_skills": missing,
        "coverage_percent": round(100 * len(matched) / len(internship.skills_required), 1),
        "learning_plan": [
            {"skill": skill, "priority": index + 1,
             "steps": [f"Study the fundamentals of {skill}",
                       f"Build a small project using {skill}",
                       f"Add evidence of {skill} to your portfolio"],
             "estimated_hours": 12}
            for index, skill in enumerate(missing)
        ],
        "note": "Learning time is a planning estimate, not a guarantee of proficiency or selection.",
    }
