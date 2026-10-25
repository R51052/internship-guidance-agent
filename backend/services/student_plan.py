"""Deterministic student actions layered on top of canonical match results."""


def build_student_plan(profile, recommendations):
    """Return a practical four-week plan without inventing employer facts."""
    top = recommendations[0] if recommendations else None
    internship = top["internship"] if top else None
    missing = list(top.get("missing_skills", [])) if top else []
    focus = missing[:3] or ["programming fundamentals", "problem solving"]
    role = internship["title"] if internship else "your target internship"

    if profile.year in (1, 2):
        phase = "Build fundamentals and one small project"
    elif profile.year in (3, 4):
        phase = "Prepare for interviews and apply consistently"
    else:
        phase = "Build evidence of skills and clarify your target role"

    project_ideas = [
        f"Build a small {focus[0]} project with a clear README and demo.",
        f"Create a {focus[1] if len(focus) > 1 else 'problem-solving'} project that consumes a public API or dataset.",
        "Add tests, error handling, and a short architecture note to an existing project.",
    ]
    interview_questions = [
        f"Explain a project where you used {focus[0]}. What trade-offs did you make?",
        "Tell me about a bug or failed approach and how you debugged it.",
        "How would you break a new technical problem into smaller tasks?",
        "Which part of your project would you improve with more time, and why?",
        "What are you learning now, and how are you measuring progress?",
    ]

    return {
        "title": "Your next 30 days",
        "target_role": role,
        "phase": phase,
        "focus_skills": focus,
        "weeks": [
            {
                "week": 1,
                "title": "Close the first skill gap",
                "tasks": [
                    f"Study {focus[0]} for 30–45 minutes on five days.",
                    "Write down three concepts you can explain without notes.",
                    "Solve five small practice problems and keep the solutions in GitHub.",
                ],
            },
            {
                "week": 2,
                "title": "Build one proof-of-work project",
                "tasks": [
                    f"Create a small project that demonstrates {', '.join(focus[:2])}.",
                    "Add a README with setup steps, screenshots, and what you learned.",
                    "Ask one peer or mentor to review the project and record the feedback.",
                ],
            },
            {
                "week": 3,
                "title": "Practice explaining your work",
                "tasks": [
                    "Prepare a two-minute explanation of your project and one challenge you solved.",
                    "Practice data structures, debugging, and role-specific questions.",
                    "Update your resume bullets with measurable project outcomes.",
                ],
            },
            {
                "week": 4,
                "title": "Apply carefully and track progress",
                "tasks": [
                    "Verify eligibility, deadline, location, and work mode on each official source page.",
                    "Apply only to roles that fit your current profile or have a realistic skill gap.",
                    "Track company, source URL, date applied, follow-up date, and next action.",
                ],
            },
        ],
        "application_checklist": [
            "One-page resume tailored to the role",
            "Updated GitHub project with a clear README",
            "Profile skills kept honest and current",
            "Official listing checked before applying",
        ],
        "project_ideas": project_ideas,
        "interview_questions": interview_questions,
        "resume_actions": [
            "Lead each project bullet with an action verb and name the technology used.",
            "Describe the problem, your contribution, and a measurable result where possible.",
            "Keep the skills section aligned with what you can explain in an interview.",
        ],
        "application_tracker_fields": [
            "Company and role",
            "Official source URL",
            "Eligibility checked",
            "Date applied and current status",
            "Next follow-up date",
        ],
    }
