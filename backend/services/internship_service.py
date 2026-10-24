from datetime import date

from fastapi import HTTPException

from backend.models import Internship
from backend.services.matching import normalize


class InternshipService:
    def __init__(self, repository):
        self.repository = repository

    def get(self, internship_id):
        value = self.repository.get("internships", internship_id)
        if value is None:
            raise HTTPException(404, "Internship not found")
        return Internship.model_validate(value)

    def search(self, *, query="", location="", domain="", work_mode=None,
               min_stipend=0, include_expired=False):
        result = []
        for document in self.repository.find("internships"):
            item = Internship.model_validate(document)
            if not include_expired and ((item.application_deadline and item.application_deadline < date.today()) or
                                       (item.start_date and item.start_date < date.today())):
                continue
            searchable = " ".join([item.title, item.company, item.description, item.domain, *item.skills_required])
            if query and normalize(query) not in normalize(searchable):
                continue
            if location and normalize(location) not in normalize(item.location):
                continue
            if domain and normalize(domain) != normalize(item.domain):
                continue
            if work_mode and item.work_mode != work_mode:
                continue
            monthly = ((item.stipend or 0) /
                       (item.duration_months if item.stipend_period == "total" and item.duration_months else 1))
            if monthly < min_stipend:
                continue
            result.append(item)
        return sorted(result, key=lambda item: item.id)
