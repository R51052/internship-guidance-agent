"""Sync current internship listings from The Muse public jobs feed into MongoDB.

The source does not publish a universal application deadline or stipend field,
so those values remain null rather than being invented. Listings are source-
linked and should be verified on the employer page before applying.
"""
import argparse
import html
import re
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser

import httpx

from backend.config import Settings
from backend.database import create_repository
from backend.models import Internship


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        if data.strip():
            self.parts.append(data.strip())

    def text(self):
        return re.sub(r"\s+", " ", html.unescape(" ".join(self.parts))).strip()


SKILL_MAP = [
    "Python", "Java", "JavaScript", "TypeScript", "React", "SQL", "Excel", "AWS", "Azure",
    "Docker", "Kubernetes", "Linux", "Git", "Machine Learning", "Data Science", "Statistics",
    "Data Analysis", "Figma", "Marketing", "Analytics", "Research", "Communication",
]


def clean_text(value, limit):
    return re.sub(r"\s+", " ", html.unescape(value or "")).strip()[:limit]


def extract_skills(item, description):
    haystack = " ".join([
        description,
        " ".join(tag.get("name", "") for tag in item.get("tags", [])),
        " ".join(category.get("name", "") for category in item.get("categories", [])),
    ]).casefold()
    skills = [skill for skill in SKILL_MAP if skill.casefold() in haystack]
    return skills[:8] or ["Communication"]


def infer_work_mode(location, description):
    value = f"{location} {description}".casefold()
    if "remote" in value or "work from home" in value:
        return "remote"
    if "hybrid" in value:
        return "hybrid"
    return "onsite"


def infer_domain(item):
    categories = [category.get("name", "") for category in item.get("categories", [])]
    if categories:
        return clean_text(categories[0], 100)
    title = clean_text(item.get("name", "Internship"), 100)
    for keyword, domain in (("software", "Software Development"), ("developer", "Software Development"),
                            ("data", "Data"), ("machine learning", "Machine Learning"),
                            ("design", "Design"), ("marketing", "Marketing"), ("finance", "Finance") ):
        if keyword in title.casefold():
            return domain
    return "Internship"


def normalize(item):
    description = TextExtractor()
    description.feed(item.get("contents", ""))
    description_text = description.text()
    locations = [clean_text(value.get("name", ""), 100) for value in item.get("locations", []) if value.get("name")]
    location = (", ".join(locations) or "Location not published")[:100]
    company = clean_text((item.get("company") or {}).get("name", "Company not published"), 150)
    title = clean_text(item.get("name", "Internship"), 200)
    source_id = str(item.get("id"))
    published_at = None
    if item.get("publication_date"):
        try:
            published_at = datetime.fromisoformat(item["publication_date"].replace("Z", "+00:00"))
        except ValueError:
            published_at = None
    return Internship(
        id=f"themuse-{source_id}",
        title=title,
        company=company,
        description=description_text[:10000] or "Internship listing from The Muse.",
        domain=infer_domain(item),
        skills_required=extract_skills(item, description_text),
        location=location,
        work_mode=infer_work_mode(location, description_text),
        stipend=None,
        currency=None,
        stipend_period=None,
        duration_months=None,
        application_deadline=None,
        start_date=None,
        apply_url=item.get("refs", {}).get("landing_page"),
        source="The Muse",
        source_job_id=source_id,
        published_at=published_at,
        last_synced_at=datetime.now(timezone.utc),
        is_active_inferred=True,
        is_demo=False,
    )


def fetch_listings(pages, max_age_days):
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    results = []
    with httpx.Client(timeout=30, headers={"User-Agent": "Internpath internship sync/1.0"}) as client:
        for page in range(1, pages + 1):
            response = client.get("https://www.themuse.com/api/public/jobs", params={"page": page, "level": "Internship"})
            response.raise_for_status()
            payload = response.json()
            for item in payload.get("results", []):
                published = item.get("publication_date")
                if published:
                    try:
                        published_at = datetime.fromisoformat(published.replace("Z", "+00:00"))
                    except ValueError:
                        continue
                    if published_at < cutoff:
                        continue
                results.append(item)
    return results


def sync(repository, items):
    current_ids = set()
    for raw in items:
        internship = normalize(raw)
        current_ids.add(internship.id)
        repository.upsert("internships", internship.id, internship.model_dump(mode="json"))
    for record in repository.find("internships"):
        if record.get("id", "").startswith("themuse-") and record.get("id") not in current_ids:
            repository.delete("internships", record["id"])
    return len(current_ids)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pages", type=int, default=5, help="The Muse pages to fetch (20 records per page).")
    parser.add_argument("--max-age-days", type=int, default=365, help="Ignore records older than this many days.")
    args = parser.parse_args()
    settings = Settings.from_env()
    settings.prepare()
    repository = create_repository(settings)
    try:
        raw = fetch_listings(max(1, min(args.pages, 25)), max(1, args.max_age_days))
        count = sync(repository, raw)
        print(f"Synchronized {count} live internship listings from The Muse into {repository.mode}.")
    finally:
        repository.close()


if __name__ == "__main__":
    main()
