"""Seed clearly labelled synthetic records; never scrapes or claims live openings."""
import argparse
from datetime import date, timedelta

from backend.config import Settings
from backend.database import create_repository
from backend.models import Internship


def demo_internships(today=None):
    today = today or date.today()
    rows = [
        ("demo-python", "Python Backend Intern", "Demo Northstar Labs", "Backend Development", ["Python", "FastAPI", "MongoDB"], "Bengaluru", "remote", 18000, 3),
        ("demo-data", "Data Analyst Intern", "Demo Insight Studio", "Data Science", ["Python", "SQL", "Excel"], "Mumbai", "hybrid", 15000, 3),
        ("demo-react", "Frontend Developer Intern", "Demo Pixel Works", "Web Development", ["JavaScript", "React", "CSS"], "Pune", "remote", 16000, 4),
        ("demo-ml", "Machine Learning Intern", "Demo Vector Research", "Machine Learning", ["Python", "Machine Learning", "Statistics"], "Hyderabad", "onsite", 25000, 6),
        ("demo-design", "Product Design Intern", "Demo Canvas Collective", "Design", ["Figma", "UI Design", "User Research"], "Delhi", "remote", 12000, 2),
        ("demo-devops", "Cloud Engineering Intern", "Demo Cloud Harbor", "Cloud Computing", ["Linux", "Docker", "Python"], "Bengaluru", "hybrid", 22000, 4),
        ("demo-marketing", "Digital Marketing Intern", "Demo Growth Garden", "Marketing", ["SEO", "Content Writing", "Analytics"], "Mumbai", "remote", 10000, 2),
        ("demo-fullstack", "Full Stack Intern", "Demo App Forge", "Web Development", ["JavaScript", "React", "Python", "SQL"], "Pune", "onsite", 20000, 6),
        ("demo-java", "Java Developer Intern", "Demo Code Orchard", "Backend Development", ["Java", "SQL", "Git"], "Chennai", "onsite", 14000, 3),
        ("demo-research", "Research Engineering Intern", "Demo Horizon Academy", "Machine Learning", ["Python", "Statistics", "Research"], "Delhi", "remote", 12000, 3),
    ]
    result = []
    for index, (identifier, title, company, domain, skills, location, mode, stipend, duration) in enumerate(rows):
        eligibility = {"min_cgpa": 7.0, "degrees": ["B.Tech", "B.E.", "B.Sc", "M.Tech", "M.Sc"], "years": [2, 3, 4]} if index in (3, 5, 9) else {}
        result.append(Internship(id=identifier, title=title, company=company, domain=domain,
                                 description=f"Synthetic demo opportunity to practice {', '.join(skills)}. This is not a real job opening.",
                                 skills_required=skills, location=location, work_mode=mode, stipend=stipend,
                                 duration_months=duration, application_deadline=today + timedelta(days=30 + index),
                                 start_date=today + timedelta(days=45 + index), eligibility=eligibility,
                                 is_demo=True, source="synthetic-demo"))
    return result


def seed_repository(repository, *, overwrite=False):
    count = 0
    for internship in demo_internships():
        if overwrite or repository.get("internships", internship.id) is None:
            repository.upsert("internships", internship.id, internship.model_dump(mode="json"))
            count += 1
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overwrite", action="store_true", help="Refresh only the known synthetic demo IDs")
    args = parser.parse_args()
    settings = Settings.from_env()
    settings.prepare()
    repository = create_repository(settings)
    try:
        count = seed_repository(repository, overwrite=args.overwrite)
        print(f"Seeded {count} clearly labelled synthetic internships into {repository.mode}.")
        if settings.demo_mode:
            print("In-memory data lasts only for this process; API demo startup seeds its own repository.")
    finally:
        repository.close()


if __name__ == "__main__":
    main()
