from datetime import date, timedelta

import pytest

from backend.models import Internship, Profile
from backend.scripts.seed_demo_data import demo_internships
from backend.services.matching import WEIGHTS, match_internship, rank_internships


TODAY = date(2026, 10, 23)


def test_perfect_match_and_weight_sum(profile_data):
    item = demo_internships(TODAY)[0]
    result = match_internship(Profile(**profile_data), item, TODAY)
    assert WEIGHTS == {"skills": 35, "education": 25, "sector": 20, "location": 15, "mode": 5}
    assert result["score"] == sum(WEIGHTS.values()) == 100
    assert result["eligible"] is True
    assert result["missing_skills"] == []


def test_case_insensitive_skills_and_proportional_matching():
    result = match_internship(Profile(skills=["  PYTHON "], min_stipend=36000, max_duration_months=1),
                              demo_internships(TODAY)[0], TODAY)
    assert result["score_breakdown"] == {"skills": 33.33}
    assert result["missing_skills"] == ["FastAPI", "MongoDB"]
    assert result["score"] == 33.33


@pytest.mark.parametrize("deadline_offset,eligible", [(0, True), (-1, False), (1, True)])
def test_deadline_boundary(deadline_offset, eligible):
    item = demo_internships(TODAY)[0].model_copy(update={"application_deadline": TODAY + timedelta(days=deadline_offset)})
    assert match_internship(Profile(), item, TODAY)["eligible"] is eligible


def test_missing_eligibility_information_is_not_assumed_qualified():
    item = demo_internships(TODAY)[3]
    result = match_internship(Profile(), item, TODAY)
    assert result["eligible"] is False
    assert len(result["ineligibility_reasons"]) == 3
    qualified = Profile(degree="b.tech", year=3, cgpa=7)
    assert match_internship(qualified, item, TODAY)["eligible"] is True
    assert match_internship(qualified.model_copy(update={"cgpa": 6.9}), item, TODAY)["eligible"] is False


def test_availability_and_started_internships():
    item = demo_internships(TODAY)[0]
    late = Profile(available_from=item.start_date + timedelta(days=1))
    assert match_internship(late, item, TODAY)["eligible"] is False
    assert match_internship(Profile(), item.model_copy(update={"start_date": TODAY - timedelta(days=1)}), TODAY)["eligible"] is False


def test_work_mode_mismatch_loses_location_points(profile_data):
    profile_data["preferred_work_mode"] = "onsite"
    result = match_internship(Profile(**profile_data), demo_internships(TODAY)[0], TODAY)
    assert result["score"] == 95


def test_stable_ties_and_ineligible_filtering():
    base = demo_internships(TODAY)[0]
    items = [base.model_copy(update={"id": "z"}), base.model_copy(update={"id": "a"}),
             base.model_copy(update={"id": "expired", "application_deadline": TODAY - timedelta(days=1)})]
    ranked = rank_internships(Profile(), items, today=TODAY)
    assert [row["internship"]["id"] for row in ranked] == ["a", "z"]
    assert len(rank_internships(Profile(), items, today=TODAY, include_ineligible=True)) == 3


def test_missing_soft_preferences_are_not_penalized():
    item = demo_internships(TODAY)[0]
    result = match_internship(Profile(skills=item.skills_required), item, TODAY)
    assert result["score_breakdown"] == {"skills": 100.0}


def test_interest_words_do_not_match_inside_unrelated_words():
    item = demo_internships(TODAY)[0].model_copy(update={"domain": "Retail", "title": "Retail Intern"})
    result = match_internship(Profile(interests=["AI"]), item, TODAY)
    assert result["score_breakdown"]["sector"] == 0.0


def test_stored_internship_skills_are_normalized():
    document = demo_internships(TODAY)[0].model_dump(mode="json")
    document["skills_required"] = [" Python ", "python", "SQL"]
    item = Internship.model_validate(document)
    assert item.skills_required == ["Python", "SQL"]
