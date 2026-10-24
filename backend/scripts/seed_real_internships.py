"""Store three verified, official Amazon Jobs listings in MongoDB.

The listings intentionally leave deadline, stipend, duration, and work mode
empty when the official posting does not publish those facts. The assistant
must not infer or fabricate those values.
"""
from backend.config import Settings
from backend.database import create_repository
from backend.models import Internship


REAL_INTERNSHIPS = [
    Internship(
        id="amazon-10513277",
        title="Software Development Engineer Intern – May 2027",
        company="Amazon",
        description=(
            "Two-month software development internship with Amazon University "
            "Talent Acquisition in Bengaluru. The official posting describes "
            "building scalable systems, cloud services, and customer-facing products."
        ),
        domain="Software Development",
        skills_required=["Programming", "Data Structures", "Algorithms", "Object-Oriented Design"],
        location="Bengaluru, Karnataka, India",
        work_mode="onsite",
        stipend=None,
        currency=None,
        stipend_period=None,
        duration_months=2,
        application_deadline=None,
        start_date=None,
        eligibility={"years": [3, 4]},
        apply_url="https://www.amazon.jobs/en/jobs/10513277/software-development-engineer-intern-may-2027-2-month-amazon-university-talent-acquisition",
        source="Amazon Jobs",
        is_demo=False,
    ),
    Internship(
        id="amazon-10575661",
        title="Applied Scientist I Intern",
        company="Amazon",
        description=(
            "Applied science internship with Amazon University Talent Acquisition. "
            "The official posting describes applying machine learning and research "
            "methods to customer and business problems."
        ),
        domain="Machine Learning",
        skills_required=["Machine Learning", "Statistics", "Python", "Research"],
        location="India",
        work_mode=None,
        stipend=None,
        currency=None,
        stipend_period=None,
        duration_months=None,
        application_deadline=None,
        start_date=None,
        eligibility={},
        apply_url="https://www.amazon.jobs/en/jobs/10575661/applied-scientist-i-intern-amazon-university-talent-acquisition",
        source="Amazon Jobs",
        is_demo=False,
    ),
    Internship(
        id="amazon-10477346",
        title="Applied Scientist I Intern – Jan 2027 (6 months)",
        company="Amazon",
        description=(
            "Applied science internship with Amazon in India. The official "
            "posting describes applying machine learning and statistical methods "
            "to customer and business problems with research and engineering teams."
        ),
        domain="Machine Learning",
        skills_required=["Machine Learning", "Statistics", "Python", "Research"],
        location="Bengaluru, Karnataka, India",
        work_mode=None,
        stipend=None,
        currency=None,
        stipend_period=None,
        duration_months=6,
        application_deadline=None,
        start_date=None,
        eligibility={"degrees": ["B.Tech", "B.E.", "B.Sc", "M.Tech", "M.Sc", "PhD"]},
        apply_url="https://www.amazon.jobs/en/jobs/10477346/applied-scientist-i-intern-jan-2027-6-months",
        source="Amazon Jobs",
        is_demo=False,
    ),
]
LEGACY_IDS = {"amazon-10572995", "amazon-10496769", "amazon-10498165"}


def seed_real_internships(repository, *, overwrite=False):
    removed = 0
    for identifier in LEGACY_IDS:
        if repository.delete("internships", identifier):
            removed += 1
    count = 0
    for internship in REAL_INTERNSHIPS:
        if overwrite or repository.get("internships", internship.id) is None:
            repository.upsert("internships", internship.id, internship.model_dump(mode="json"))
            count += 1
    return count


def main():
    settings = Settings.from_env()
    settings.prepare()
    repository = create_repository(settings)
    try:
        count = seed_real_internships(repository, overwrite=True)
        print(f"Synchronized {count} verified real internships in {repository.mode}.")
    finally:
        repository.close()


if __name__ == "__main__":
    main()
