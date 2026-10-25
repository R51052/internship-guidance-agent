"""Synchronize source-linked internship records focused on India.

The records below come from official employer career pages found during the
October 25, 2026 refresh. Unknown stipend, deadline, and duration values are
left empty instead of being invented. Users should verify every listing on its
source page before applying.
"""
from datetime import datetime, timezone

from backend.config import Settings
from backend.database import create_repository
from backend.models import Internship


def now():
    return datetime.now(timezone.utc)


INDIA_INTERNSHIPS = [
    Internship(
        id="india-amazon-10498157",
        title="Programmer Analyst 6M H1 Intern FY26",
        company="Amazon",
        description="Amazon India internship involving application support, automation, service integrations, troubleshooting, and mentoring.",
        domain="Software Development",
        skills_required=["Programming", "Python", "Java", "Automation", "Problem Solving"],
        location="India (including Hyderabad)",
        work_mode=None,
        apply_url="https://www.amazon.jobs/en/jobs/10498157/programmer-analyst-6m-h1-intern-fy26",
        source="Amazon Jobs India",
        source_job_id="10498157",
        last_synced_at=now(),
        is_demo=False,
    ),
    Internship(
        id="india-salesforce-jr337715",
        title="Summer 2027 Intern - Software Engineer",
        company="Salesforce",
        description="Software engineering internship for the Class of 2028 in Bangalore or Hyderabad, working on distributed systems, cloud services, testing, and product features.",
        domain="Software Development",
        skills_required=["Java", "C++", "Python", "JavaScript", "React", "SQL", "Data Structures", "Algorithms"],
        location="Bangalore or Hyderabad, India",
        work_mode=None,
        eligibility={"degrees": ["B.E", "B.Tech"], "years": [2, 3, 4]},
        apply_url="https://careers.salesforce.com/en/jobs/jr337715/summer-2027-intern-software-engineer/",
        source="Salesforce Careers India",
        source_job_id="JR337715",
        last_synced_at=now(),
        is_demo=False,
    ),
    Internship(
        id="india-cargill-332319",
        title="Software Engineer Intern - Digital Technology and Data",
        company="Cargill",
        description="Software engineering internship in Bengaluru focused on cloud platforms, big-data platforms, application development, mentorship, and real business projects.",
        domain="Software Development",
        skills_required=["Programming", "Cloud", "Data", "Software Engineering", "Problem Solving"],
        location="Bengaluru, India",
        work_mode="hybrid",
        duration_months=6,
        apply_url="https://careers.cargill.com/en/job/bengaluru/software-engineer-intern-digital-technology-and-data/23251/100079360032",
        source="Cargill Careers India",
        source_job_id="332319",
        last_synced_at=now(),
        is_demo=False,
    ),
    Internship(
        id="india-redhat-r058560",
        title="Software Engineering Intern",
        company="Red Hat",
        description="Software engineering internship in Pune or Bangalore with projects and mentoring across Ansible, RHEL, OpenShift, AI, Python, JavaScript, and Agile engineering.",
        domain="Software Development",
        skills_required=["Python", "Java", "JavaScript", "Git", "Linux", "AI", "Agile"],
        location="Pune or Bangalore, India",
        work_mode="onsite",
        apply_url="https://redhat.wd5.myworkdayjobs.com/en-US/Jobs/job/Software-Engineering-Intern_R-058560",
        source="Red Hat Careers India",
        source_job_id="R-058560",
        last_synced_at=now(),
        is_demo=False,
    ),
    Internship(
        id="india-walmart-r2580222",
        title="Grad Intern - No Work Experience",
        company="Walmart Global Tech India",
        description="Graduate software engineering internship in Bengaluru working on scalable software solutions with AI and ML integrations and real-world projects.",
        domain="Software Development",
        skills_required=["Software Engineering", "AI", "Machine Learning", "Problem Solving", "Programming"],
        location="Bengaluru, India",
        work_mode="onsite",
        apply_url="https://walmart.wd504.myworkdayjobs.com/en-US/WalmartExternal/job/IN-KA-BANGALORE-Home-Office-Building-10/Grad-Intern---No-Work-Experience_R-2580222",
        source="Walmart Global Tech India",
        source_job_id="R-2580222",
        last_synced_at=now(),
        is_demo=False,
    ),
    Internship(
        id="india-ge-req25264",
        title="Technology Intern",
        company="GE Appliances India",
        description="Technology internship in Hyderabad or Bangalore covering web, mobile, cloud, automation, application development, testing, and modern engineering tools.",
        domain="Technology",
        skills_required=["Python", "React", "Java", "Cloud", "Docker", "AWS", "GenAI", "Problem Solving"],
        location="Hyderabad or Bangalore, India",
        work_mode="onsite",
        duration_months=6,
        apply_url="https://haier.wd3.myworkdayjobs.com/en-US/GE_Appliances/job/Hyderabad-SAL-IN/Technology-Intern_REQ-25264",
        source="GE Appliances Careers India",
        source_job_id="REQ-25264",
        last_synced_at=now(),
        is_demo=False,
    ),
    Internship(
        id="india-amazon-10541345",
        title="SDE I Intern",
        company="Amazon",
        description="Six-month in-person software development internship for 2027 graduates, with project ownership, distributed systems, automation, AWS exposure, and mentorship.",
        domain="Software Development",
        skills_required=["C++", "Python", "Java", "Algorithms", "Data Structures", "AWS"],
        location="Bengaluru, Chennai, Hyderabad, Delhi, Mumbai, or Pune, India",
        work_mode="onsite",
        duration_months=6,
        eligibility={"years": [3, 4]},
        apply_url="https://www.amazon.jobs/en/jobs/10541345/sde-i-intern-amazon-university-talent-acquisition",
        source="Amazon Jobs India",
        source_job_id="10541345",
        last_synced_at=now(),
        is_demo=False,
    ),
    Internship(
        id="india-hevo-993a3ed3",
        title="Associate Software Development Engineer (SDE) Intern",
        company="Hevo Data",
        description="Bangalore software development internship involving SaaS connectors, REST APIs, data pipelines, debugging, testing, and internal AI tools.",
        domain="Software Development",
        skills_required=["Java", "TypeScript", "Python", "REST APIs", "Data Structures"],
        location="Bangalore, India",
        work_mode="onsite",
        apply_url="https://jobs.lever.co/hevodata/993a3ed3-3014-432f-b0f4-28d300d58d9a",
        source="Hevo Data / Lever",
        source_job_id="993a3ed3-3014-432f-b0f4-28d300d58d9a",
        last_synced_at=now(),
        is_demo=False,
    ),
    Internship(
        id="india-merkle-frontend-20675d00",
        title="Software Engineer - Intern (Frontend)",
        company="Merkle Science",
        description="Frontend engineering internship in Bangalore building responsive dashboards and investigation workflows with React, REST APIs, state management, testing, and Git.",
        domain="Frontend Development",
        skills_required=["JavaScript", "React", "HTML", "CSS", "REST APIs", "Git"],
        location="Bangalore, India",
        work_mode="hybrid",
        duration_months=12,
        apply_url="https://jobs.lever.co/merklescience/20675d00-156c-4f3f-a9bf-4cacee176bc2",
        source="Merkle Science / Lever",
        source_job_id="20675d00-156c-4f3f-a9bf-4cacee176bc2",
        last_synced_at=now(),
        is_demo=False,
    ),
    Internship(
        id="india-merkle-backend-intern",
        title="Software Engineer (Intern) - Backend",
        company="Merkle Science",
        description="Backend engineering internship in Bangalore listed on Merkle Science's official engineering jobs board. Verify the current detail page before applying.",
        domain="Backend Development",
        skills_required=["Python", "Java", "REST APIs", "Databases", "Git"],
        location="Bangalore, India",
        work_mode="hybrid",
        apply_url="https://jobs.lever.co/merklescience?team=Engineering",
        source="Merkle Science / Lever",
        source_job_id="backend-intern-engineering-board",
        last_synced_at=now(),
        is_demo=False,
    ),
    Internship(
        id="india-sprinto-ai-implementation",
        title="AI Implementation Intern",
        company="Sprinto",
        description="Remote Bengaluru AI implementation internship supporting AI infrastructure, model evaluation, data pipelines, document parsing, search tools, and LLM integrations.",
        domain="Artificial Intelligence",
        skills_required=["Python", "Machine Learning", "Data Processing", "LLMs", "AWS", "Problem Solving"],
        location="Bengaluru, India",
        work_mode="remote",
        apply_url="https://jobs.lever.co/Sprinto/6dfd5f41-57b6-40e8-9eab-ba4083c1a7c4",
        source="Sprinto / Lever",
        source_job_id="6dfd5f41-57b6-40e8-9eab-ba4083c1a7c4",
        last_synced_at=now(),
        is_demo=False,
    ),
    Internship(
        id="india-microsoft-explore",
        title="Explore Microsoft — India Program",
        company="Microsoft",
        description="Eight-week India-only Explore program for first- or second-year college students covering software development, design, build, quality, mentoring, and project ownership.",
        domain="Software Development",
        skills_required=["Programming", "Data Structures", "Problem Solving", "Product Thinking", "Collaboration"],
        location="Various Microsoft campuses in India",
        work_mode=None,
        duration_months=2,
        apply_url="https://careers.microsoft.com/v2/global/en/exploremicrosoft",
        source="Microsoft Careers India",
        source_job_id="explore-microsoft-india",
        last_synced_at=now(),
        is_demo=False,
    ),
    Internship(
        id="india-sprinto-talent-acquisition",
        title="Talent Acquisition Intern",
        company="Sprinto",
        description="Remote Bengaluru talent acquisition internship listed on Sprinto's official India jobs board. Verify the current detail page before applying.",
        domain="Human Resources",
        skills_required=["Communication", "Research", "Coordination", "Recruiting"],
        location="Bengaluru, India",
        work_mode="remote",
        apply_url="https://jobs.lever.co/Sprinto?location=Bengaluru",
        source="Sprinto / Lever",
        source_job_id="talent-acquisition-intern-board",
        last_synced_at=now(),
        is_demo=False,
    ),
    Internship(
        id="india-microsoft-university-internships",
        title="University Internships — India",
        company="Microsoft",
        description="Microsoft's official student careers portal for university internship opportunities in India. Use the portal to check the current role, team, eligibility, and application window before applying.",
        domain="Software Development",
        skills_required=["Programming", "Problem Solving", "Data Structures", "Communication", "Collaboration"],
        location="India",
        work_mode=None,
        eligibility={"degrees": ["B.E", "B.Tech", "B.Sc", "M.E", "M.Tech", "M.Sc"], "years": [3]},
        apply_url="https://careers.microsoft.com/students/us/en/india",
        source="Microsoft Student Careers India",
        source_job_id="microsoft-university-internships-india",
        last_synced_at=now(),
        is_demo=False,
    ),
    Internship(
        id="india-oracle-student-intern-search",
        title="Student and Intern Opportunities — India",
        company="Oracle",
        description="Oracle's official careers search for student and intern roles in India. Filter the live search for internship or student positions and confirm the exact team, city, and requirements on the role page.",
        domain="Technology",
        skills_required=["Programming", "SQL", "Cloud", "Problem Solving", "Communication"],
        location="India",
        work_mode=None,
        eligibility={"degrees": ["B.E", "B.Tech", "B.Sc", "M.E", "M.Tech", "M.Sc", "MBA"]},
        apply_url="https://careers.oracle.com/en/sites/jobsearch/requisitions?keyword=Intern&location=India",
        source="Oracle Careers India",
        source_job_id="oracle-student-intern-india-search",
        last_synced_at=now(),
        is_demo=False,
    ),
    Internship(
        id="india-adobe-student-careers",
        title="Student and New Graduate Opportunities — India",
        company="Adobe",
        description="Adobe's official student and new-graduate careers portal for India. Use the current search results to verify whether an internship is open and review the exact skills and graduation requirements.",
        domain="Technology",
        skills_required=["Programming", "Java", "Python", "JavaScript", "Data Structures", "Algorithms"],
        location="Noida or Bengaluru, India",
        work_mode=None,
        eligibility={"degrees": ["B.E", "B.Tech", "B.Sc", "M.E", "M.Tech", "M.Sc"]},
        apply_url="https://careers.adobe.com/us/en/university",
        source="Adobe Careers India",
        source_job_id="adobe-student-careers-india",
        last_synced_at=now(),
        is_demo=False,
    ),
]


def sync_india_internships(repository):
    for internship in INDIA_INTERNSHIPS:
        repository.upsert("internships", internship.id, internship.model_dump(mode="json"))
    for item in repository.find("internships"):
        if item.get("id", "").startswith(("themuse-", "india-", "amazon-")) and item.get("id") not in {x.id for x in INDIA_INTERNSHIPS}:
            repository.delete("internships", item["id"])
        if item.get("source") == "The Muse":
            repository.delete("internships", item["id"])
    return len(INDIA_INTERNSHIPS)


def main():
    settings = Settings.from_env()
    settings.prepare()
    repository = create_repository(settings)
    try:
        count = sync_india_internships(repository)
        print(f"Synchronized {count} India-focused internship records in {repository.mode}.")
    finally:
        repository.close()


if __name__ == "__main__":
    main()
