"""Read-only public GitHub repository evaluator."""
from urllib.parse import urlparse
import httpx


def parse_repo_url(value):
    parsed = urlparse(value.strip())
    if parsed.scheme not in {"http", "https"} or parsed.hostname != "github.com":
        raise ValueError("Use a public github.com repository URL")
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2:
        raise ValueError("Use a repository URL like https://github.com/owner/repository")
    return parts[0], parts[1].removesuffix(".git")


def evaluate_repository(url, transport=None):
    owner, repo = parse_repo_url(url)
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "Internpath-Project-Evaluator"}
    base = f"https://api.github.com/repos/{owner}/{repo}"
    try:
        with httpx.Client(timeout=15, transport=transport) as client:
            metadata = client.get(base, headers=headers)
            metadata.raise_for_status()
            root = client.get(base + "/contents", headers=headers)
            root.raise_for_status()
            metadata_json = metadata.json()
            entries = root.json() if isinstance(root.json(), list) else []
    except (httpx.HTTPError, ValueError, TypeError) as exc:
        raise ValueError("GitHub repository could not be read. Check that it is public and the URL is correct.") from exc
    names = {str(item.get("name", "")).casefold() for item in entries}
    checks = {"readme": any(name.startswith("readme") for name in names),
              "tests": any("test" in name for name in names),
              "license": any(name.startswith("license") for name in names),
              "documentation": any(name in {"docs", "documentation"} for name in names),
              "ci": any(name in {".github", ".gitlab-ci.yml", "azure-pipelines.yml"} for name in names),
              "source_code": bool(entries)}
    suggestions = []
    if not checks["readme"]: suggestions.append("Add a README with setup steps, screenshots, and a project explanation.")
    if not checks["tests"]: suggestions.append("Add tests or a testing section to show how the project is verified.")
    if not checks["documentation"]: suggestions.append("Add API or architecture documentation.")
    if not checks["ci"]: suggestions.append("Add a CI workflow that runs tests and builds the project.")
    return {"repository": f"{owner}/{repo}", "url": url, "name": metadata_json.get("name"),
            "description": metadata_json.get("description"), "stars": metadata_json.get("stargazers_count", 0),
            "checks": checks, "score": round(100 * sum(checks.values()) / len(checks)),
            "suggestions": suggestions, "message": "Read-only public-repository checks only; this is not a code-quality guarantee."}
