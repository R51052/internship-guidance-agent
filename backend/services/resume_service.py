"""Safe in-memory resume extraction, validation, and document generation."""
from io import BytesIO
import re
from pathlib import Path

from docx import Document
from pypdf import PdfReader
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


MAX_RESUME_BYTES = 5 * 1024 * 1024
SUPPORTED_FORMATS = {".pdf": "pdf", ".docx": "docx"}
SECTION_NAMES = ("education", "skills", "projects", "experience", "certifications", "summary")


def _format_validation(text, page_count=None):
    normalized = text.strip()
    lower = normalized.casefold()
    checks = []
    issues = []
    found = [name.title() for name in SECTION_NAMES if re.search(rf"\b{re.escape(name)}\b", lower)]
    missing = [name.title() for name in SECTION_NAMES[:4] if name not in found]
    if found:
        checks.append(f"Detected sections: {', '.join(found)}")
    if missing:
        issues.append(f"Add or clarify: {', '.join(missing)}")
    if not re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", normalized):
        issues.append("Add a professional email address")
    if len(normalized) < 250:
        issues.append("Resume text is short; add evidence from projects, coursework, or experience")
    if len(normalized) > 12000:
        issues.append("Resume text is long; keep the final version focused and concise")
    long_lines = sum(len(line) > 180 for line in normalized.splitlines())
    if long_lines:
        issues.append("Break long lines into readable bullets")
    if page_count and page_count > 2:
        issues.append("Keep an internship resume to one or two pages")
    if page_count:
        checks.append(f"Detected {page_count} page(s)")
    checks.append("No unsupported file type or executable content is accepted")
    score = max(0, min(100, 100 - len(issues) * 15))
    return {"score": score, "checks": checks, "issues": issues, "sections": found}


def extract_resume(filename, content_type, data):
    if len(data) > MAX_RESUME_BYTES:
        raise ValueError("Resume file must be 5 MB or smaller")
    suffix = Path(filename or "").suffix.casefold()
    if suffix not in SUPPORTED_FORMATS:
        raise ValueError("Only PDF and DOCX resume files are supported")
    format_name = SUPPORTED_FORMATS[suffix]
    if format_name == "pdf":
        reader = PdfReader(BytesIO(data))
        page_count = len(reader.pages)
        text = "\n".join((page.extract_text() or "") for page in reader.pages).strip()
    else:
        document = Document(BytesIO(data))
        paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
        text = "\n".join(paragraphs).strip()
        page_count = None
    if not text:
        raise ValueError("Could not extract readable text from this resume")
    return {"filename": Path(filename).name, "format": format_name, "content_type": content_type or "",
            "text": text[:20000], "page_count": page_count,
            "formatting": _format_validation(text, page_count)}


def _safe_filename(value):
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-")
    return cleaned[:60] or "internpath-resume"


def generate_document(content, format_name, filename):
    content = content.strip()
    if not content:
        raise ValueError("Resume content cannot be empty")
    output = BytesIO()
    if format_name == "docx":
        document = Document()
        document.add_heading("Resume", 0)
        for block in content.split("\n"):
            line = block.strip()
            if not line:
                continue
            if line.casefold().rstrip(":") in SECTION_NAMES:
                document.add_heading(line.rstrip(":"), level=1)
            else:
                document.add_paragraph(line)
        document.save(output)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        extension = "docx"
    elif format_name == "pdf":
        styles = getSampleStyleSheet()
        document = SimpleDocTemplate(output, pagesize=LETTER, rightMargin=.7 * inch,
                                     leftMargin=.7 * inch, topMargin=.65 * inch, bottomMargin=.65 * inch)
        story = [Paragraph("Resume", styles["Title"]), Spacer(1, 10)]
        for block in content.split("\n"):
            line = block.strip()
            if not line:
                story.append(Spacer(1, 6))
            elif line.casefold().rstrip(":") in SECTION_NAMES:
                story.append(Paragraph(line.rstrip(":"), styles["Heading2"]))
            else:
                story.append(Paragraph(line.replace("&", "&amp;"), styles["BodyText"]))
        document.build(story)
        media_type = "application/pdf"
        extension = "pdf"
    else:
        raise ValueError("Format must be pdf or docx")
    output.seek(0)
    return output, media_type, f"{_safe_filename(filename)}.{extension}"
