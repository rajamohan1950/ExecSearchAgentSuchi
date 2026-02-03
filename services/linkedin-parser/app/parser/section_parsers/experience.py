import re
import logging

from app.parser.models import ExperienceEntry

logger = logging.getLogger(__name__)

# Date range pattern: "May 2025 - Present" or "October 2017 - October 2021 (4 years 1 month)"
DATE_RANGE_PATTERN = re.compile(
    r"(\w{3,9}\s+\d{4})\s*[-–—]\s*(Present|\w{3,9}\s+\d{4})",
    re.IGNORECASE,
)

# Year-only date pattern for "Earlier Experience": "2000 - 2014 (14 years)"
YEAR_RANGE_PATTERN = re.compile(
    r"^(\d{4})\s*[-–—]\s*(\d{4}|Present)\s*(?:\(.+?\))?\s*$",
    re.IGNORECASE,
)

# Duration in parentheses: "(3 years 3 months)" or "(14 years)"
DURATION_PATTERN = re.compile(r"\([\d]+\s+years?\s*(?:\d+\s+months?)?\)")

# Page markers
PAGE_MARKER = re.compile(r"^Page\s+\d+\s+of\s+\d+\s*$", re.IGNORECASE)


def parse_experience(text: str) -> list[ExperienceEntry]:
    entries: list[ExperienceEntry] = []
    if not text.strip():
        return entries

    # Remove page markers
    lines = [l for l in text.split("\n") if not PAGE_MARKER.match(l.strip())]

    # Detect format by checking if company names appear on their own line before title
    # Format A (old LinkedIn): "Title\nCompany, Location DateRange\n• bullets"
    # Format B (new LinkedIn): "Company\nTitle\nDateRange (duration)\nLocation\n- bullets"
    format_b = _detect_format_b(lines)

    if format_b:
        entries = _parse_format_b(lines)
    else:
        entries = _parse_format_a(lines)

    logger.info(f"Parsed {len(entries)} experience entries (format={'B' if format_b else 'A'})")
    return entries


def _detect_format_b(lines: list[str]) -> bool:
    """Detect if experience uses Format B (Company on own line, date on separate line with duration)."""
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Format B: date line has duration in parens and is a standalone line
        if DATE_RANGE_PATTERN.search(stripped) and DURATION_PATTERN.search(stripped):
            # In Format B, the date line only contains the date range + duration
            cleaned = DATE_RANGE_PATTERN.sub("", stripped)
            cleaned = DURATION_PATTERN.sub("", cleaned).strip()
            if not cleaned or len(cleaned) < 3:
                return True
        if YEAR_RANGE_PATTERN.match(stripped):
            return True
    return False


def _parse_format_b(lines: list[str]) -> list[ExperienceEntry]:
    """Parse Format B: Company\\nTitle\\nDateRange (duration)\\nLocation\\n- bullets"""
    entries: list[ExperienceEntry] = []

    # Find date-range lines (these anchor each role)
    date_line_indices = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if DATE_RANGE_PATTERN.search(stripped) or YEAR_RANGE_PATTERN.match(stripped):
            date_line_indices.append(i)

    if not date_line_indices:
        return _fallback_parse(lines)

    # Track the current company name (persists for multiple roles at same company)
    current_company = None

    for idx, date_line_idx in enumerate(date_line_indices):
        date_line = lines[date_line_idx].strip()

        # Parse dates
        date_match = DATE_RANGE_PATTERN.search(date_line)
        year_match = YEAR_RANGE_PATTERN.match(date_line)
        if date_match:
            start_date = date_match.group(1)
            end_date = date_match.group(2)
        elif year_match:
            start_date = year_match.group(1)
            end_date = year_match.group(2)
        else:
            start_date = None
            end_date = None

        # Title is 1 line above date
        title = lines[date_line_idx - 1].strip() if date_line_idx > 0 else "Unknown Role"

        # Company: 2 lines above date, OR carried forward from previous entry
        # We need to check if the line 2-above is a company name or description text
        company_candidate = None
        if date_line_idx >= 2:
            candidate = lines[date_line_idx - 2].strip()
            # A company name is typically short, no bullets, not a description
            if (candidate
                    and not candidate.startswith("-")
                    and not candidate.startswith("•")
                    and len(candidate) < 80
                    and not DATE_RANGE_PATTERN.search(candidate)
                    and not YEAR_RANGE_PATTERN.match(candidate)
                    and not DURATION_PATTERN.search(candidate)):
                # Check if this is a new company or just a continuation of description
                # If prev entry exists and this candidate isn't after a blank line, it might be description
                if idx > 0:
                    prev_date_idx = date_line_indices[idx - 1]
                    # Lines between prev date line and this company candidate
                    between_start = prev_date_idx + 1
                    between_end = date_line_idx - 2
                    # Check if there's content between (descriptions) — if the candidate is
                    # immediately after descriptions without a gap, check if it looks like a company
                    if _looks_like_company(candidate):
                        company_candidate = candidate
                else:
                    # First entry — line 2-above should be company
                    company_candidate = candidate

        if company_candidate:
            current_company = company_candidate
        company = current_company or ""

        # Location: 1 line below date (if it looks like a location)
        location = None
        if date_line_idx + 1 < len(lines):
            loc_candidate = lines[date_line_idx + 1].strip()
            if _looks_like_location(loc_candidate):
                location = loc_candidate
                desc_start = date_line_idx + 2
            else:
                desc_start = date_line_idx + 1
        else:
            desc_start = date_line_idx + 1

        # Description: everything from desc_start until the next role's company line
        if idx + 1 < len(date_line_indices):
            next_date_idx = date_line_indices[idx + 1]
            # Description ends 2 lines before next date (title line and maybe company line)
            desc_end = next_date_idx - 1  # at minimum, the title line
            # Check if line at next_date_idx - 2 is a company name
            if next_date_idx >= 2 and _looks_like_company(lines[next_date_idx - 2].strip()):
                desc_end = next_date_idx - 2
        else:
            desc_end = len(lines)

        desc_lines = []
        for d in range(desc_start, desc_end):
            stripped = lines[d].strip()
            if stripped:
                desc_lines.append(stripped)

        description = "\n".join(desc_lines) if desc_lines else None

        entries.append(ExperienceEntry(
            title=title,
            company=company,
            location=location,
            start_date=start_date,
            end_date=end_date,
            description=description,
        ))

    return entries


def _looks_like_company(text: str) -> bool:
    """Heuristic: is this line likely a company name?"""
    if not text:
        return False
    # Company names: short, no bullets, no dates, typically Title Case or known patterns
    if text.startswith("-") or text.startswith("•"):
        return False
    if DATE_RANGE_PATTERN.search(text) or YEAR_RANGE_PATTERN.match(text):
        return False
    if len(text) > 60:
        return False
    # Skip section headers that got merged into experience
    section_headers = {"earlier experience", "additional experience", "other experience",
                       "previous experience", "prior experience"}
    if text.lower().strip() in section_headers:
        return False
    # Company names are usually short (1-5 words) and don't start with lowercase
    words = text.split()
    if len(words) > 8:
        return False
    # Avoid description-like lines that start with action verbs
    desc_starters = {"led", "built", "managed", "delivered", "achieved", "reduced",
                     "increased", "implemented", "designed", "developed", "created",
                     "launched", "scaled", "established", "generated", "enabled",
                     "optimized", "automated", "improved", "drove", "hired", "owned"}
    if words and words[0].lower().rstrip(",.:") in desc_starters:
        return False
    return True


def _looks_like_location(text: str) -> bool:
    """Heuristic: is this line a location?"""
    if not text:
        return False
    if text.startswith("-") or text.startswith("•"):
        return False
    if len(text) > 60:
        return False
    # Location patterns: "City", "City, State", "Greater City Area"
    location_patterns = [
        r"^[A-Z][a-z]+(?:\s[A-Z][a-z]+)*(?:,\s*\w+)*$",  # "Bengaluru" or "Seattle, WA"
        r"(?:Greater|Metro)\s+\w+",  # "Greater Bengaluru Area"
        r"\b(?:Area|Region|Metro)\b",
    ]
    for pat in location_patterns:
        if re.search(pat, text):
            return True
    # Short text with comma (City, State/Country pattern)
    if "," in text and len(text) < 40:
        return True
    return False


def _parse_format_a(lines: list[str]) -> list[ExperienceEntry]:
    """Parse Format A (original LinkedIn): Title\\nCompany, Location DateRange\\n• bullets"""
    entries: list[ExperienceEntry] = []

    # Find date-range lines
    date_line_indices = []
    for i, line in enumerate(lines):
        if DATE_RANGE_PATTERN.search(line):
            date_line_indices.append(i)

    if not date_line_indices:
        return _fallback_parse(lines)

    for idx, date_line_idx in enumerate(date_line_indices):
        # Title is the line(s) before the date line
        if idx > 0:
            min_title_start = date_line_indices[idx - 1] + 1
        else:
            min_title_start = 0

        title_lines = []
        for t in range(date_line_idx - 1, min_title_start - 1, -1):
            stripped = lines[t].strip()
            if stripped and not stripped.startswith("•") and not stripped.startswith("-"):
                title_lines.insert(0, stripped)
                break

        title = " ".join(title_lines) if title_lines else "Unknown Role"

        # Parse the date line
        date_line = lines[date_line_idx].strip()
        date_match = DATE_RANGE_PATTERN.search(date_line)
        start_date = date_match.group(1) if date_match else None
        end_date = date_match.group(2) if date_match else None

        company_location = DATE_RANGE_PATTERN.sub("", date_line).strip().rstrip(",").strip()
        company, location = _split_company_location(company_location)

        # Description
        if idx + 1 < len(date_line_indices):
            next_title_start = date_line_indices[idx + 1] - 1
            desc_end = next_title_start
        else:
            desc_end = len(lines)

        desc_lines = []
        for d in range(date_line_idx + 1, desc_end):
            stripped = lines[d].strip()
            if stripped:
                desc_lines.append(stripped)

        description = "\n".join(desc_lines) if desc_lines else None

        entries.append(ExperienceEntry(
            title=title,
            company=company,
            location=location,
            start_date=start_date,
            end_date=end_date,
            description=description,
        ))

    return entries


def _split_company_location(text: str) -> tuple[str, str | None]:
    """Split 'AlphaForge.ai, Bengaluru, India' into company and location."""
    if not text:
        return ("", None)

    parts = [p.strip() for p in text.split(",")]

    if len(parts) >= 3:
        company = parts[0]
        location = ", ".join(parts[1:])
        return (company, location)
    elif len(parts) == 2:
        company = parts[0]
        location = parts[1]
        return (company, location)
    else:
        return (text, None)


def _fallback_parse(lines: list[str]) -> list[ExperienceEntry]:
    """Fallback: split by empty lines into blocks."""
    entries = []
    blocks: list[list[str]] = []
    current: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current:
                blocks.append(current)
                current = []
        else:
            current.append(stripped)
    if current:
        blocks.append(current)

    for block in blocks:
        if block:
            entries.append(ExperienceEntry(
                title=block[0],
                company=block[1] if len(block) > 1 else "",
                description="\n".join(block[2:]) if len(block) > 2 else None,
            ))
    return entries
