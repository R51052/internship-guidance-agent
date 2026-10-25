"""Conservative heuristic checks for internship listing safety signals."""
from urllib.parse import urlparse


OFFICIAL_HOST_SUFFIXES = ("amazon.jobs", "salesforce.com", "cargill.com", "redhat.com",
                          "walmart.com", "haier.com", "lever.co", "microsoft.com",
                          "oracle.com", "adobe.com")
SUSPICIOUS_TERMS = ("pay registration", "registration fee", "deposit", "buy course",
                    "whatsapp only", "telegram only", "send otp", "aadhaar", "pan card")


def safety_check(internship):
    url = str(internship.apply_url or "")
    host = (urlparse(url).hostname or "").casefold()
    flags = []
    checks = ["Application link is present" if url else "No application link is published"]
    if host and not any(host == suffix or host.endswith("." + suffix) for suffix in OFFICIAL_HOST_SUFFIXES):
        flags.append("The link is not on a recognized employer or recruiting-platform domain")
    else:
        checks.append("Application link uses a recognized employer or recruiting-platform domain")
    text = f"{internship.title} {internship.description}".casefold()
    for term in SUSPICIOUS_TERMS:
        if term in text:
            flags.append(f"Listing text contains a warning phrase: {term}")
    if not internship.source or internship.source.casefold() in {"curated", "unknown"}:
        flags.append("Source attribution is limited")
    if flags:
        level = "needs_verification" if len(flags) < 3 else "high_risk_signals"
    else:
        level = "lower_risk_signals"
    return {"risk_level": level, "flags": flags, "checks": checks,
            "message": "This is a heuristic, not a guarantee. Verify the role on the employer's official careers site and never pay to apply."}
