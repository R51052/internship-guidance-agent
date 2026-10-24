"""Allowlisted tools: model-supplied inputs are validated before any execution."""
from backend.agent_tools import compare_internships, explain_recommendations, internship_details, search_internships, skill_analysis
from backend.models import CompareRequest

TOOLS = {
    "search_internships": (search_internships.SearchArguments, search_internships.execute,
                           "Search stored internship records; never searches the web."),
    "internship_details": (internship_details.DetailsArguments, internship_details.execute,
                           "Read a stored internship by its exact ID."),
    "skill_analysis": (internship_details.DetailsArguments, skill_analysis.execute,
                       "Find missing skills for a stored internship using the current user's profile."),
    "compare_internships": (CompareRequest, compare_internships.execute,
                            "Compare two to five distinct stored internships against the current profile."),
    "explain_recommendations": (explain_recommendations.ExplainArguments, explain_recommendations.execute,
                                "Return deterministic, eligible recommendations with scoring explanations."),
}


def execute_tool(name, arguments, repository, profile):
    if name not in TOOLS:
        raise ValueError(f"Unknown tool: {name}")
    schema, handler, _ = TOOLS[name]
    parsed = schema.model_validate(arguments)
    return handler(repository, profile, parsed)


def tool_schemas():
    return [{"type": "function", "function": {"name": name, "description": description,
                                               "parameters": schema.model_json_schema()}}
            for name, (schema, _, description) in TOOLS.items()]
